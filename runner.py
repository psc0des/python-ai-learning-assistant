"""Sandboxed code runner for Python Skill Lab.

Executes learner code in a restricted subprocess with:
- AST-based import allowlisting and built-in/attribute blocking before execution
- input() blocked before execution — labs use parameters or sample variables
- open() blocked via AST scan — no file I/O from learner code
- Strict timeout with process kill
- Size limits on submitted code

IMPORTANT — this is defense-in-depth against accidental misuse, not a hard
security boundary. Learner code runs as real bytecode in the same interpreter
as this runner, so a determined learner who wants to reach the host machine
(e.g. by walking `.f_back`/`.f_builtins`/`gi_frame` on a live frame object)
can still find a path to it. The allowlist + frame-attribute + dunder blocks
below close every escape found during a security audit, but no in-process
denylist/allowlist can close this class of attack completely — only OS-level
isolation (a container, a locked-down account, or a WASM interpreter such as
Pyodide) is a real boundary. Do not expose this app to a network or
multi-user environment.
"""

from __future__ import annotations

import ast
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

MAX_CODE_BYTES = 20_000
RUN_TIMEOUT_SECONDS = 6

# Each run/trace request starts a fresh isolated Python subprocess on purpose.
# Reusing an interpreter would be faster, but it would also keep learner state
# alive between runs and weaken the local safety boundary.

# ---------------------------------------------------------------------------
# Dangerous construct detection
# ---------------------------------------------------------------------------

# Allowlist, not a denylist. A security audit proved that any module not
# explicitly blocked (gc, inspect, codecs, platform, sysconfig, io, ...) can
# be used to pivot back to the real os module or the interpreter's real
# builtins, so the only defensible policy is "nothing runs unless it is on
# this list." Every module here is pure-computation/formatting with no
# filesystem, network, process, or introspection capability. Extend this
# list deliberately when new lesson/lab content needs a module — do not add
# anything that can access the filesystem, network, processes, or live
# interpreter objects (no os, sys, io, gc, inspect, ctypes, socket, etc.).
ALLOWED_MODULES = frozenset({
    "math", "random", "string", "re",
    "datetime", "collections", "itertools", "functools",
    "typing", "dataclasses", "enum", "decimal", "fractions",
    "statistics", "copy", "heapq", "bisect", "textwrap",
    "uuid", "abc", "operator", "contextlib", "asyncio",
    "json", "numbers", "cmath",
})

BLOCKED_BUILTINS = frozenset({
    "exec", "eval", "compile", "__import__",
    "breakpoint", "exit", "quit",
    "globals", "locals", "vars",
    "getattr", "setattr", "delattr",
})

# Non-dunder attributes that hand back a live frame object. A frame's
# f_builtins/f_globals are the REAL, unrestricted interpreter builtins (the
# stripped USER_GLOBALS builtins only apply to the frame learner code runs
# in) — so any of these is a one-hop pivot to os/eval/exec/open regardless
# of what is stripped from USER_GLOBALS. Blocking the dunder-style names
# alone is not enough because these are ordinary attribute names, not dunders.
BLOCKED_FRAME_ATTRS = frozenset({
    "f_back", "f_builtins", "f_globals", "f_locals", "f_code", "f_trace",
    "gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame", "ag_code",
    "tb_frame", "tb_next",
})

# Dunders a beginner legitimately needs for OOP/operator-overloading lessons.
# __class__, __subclasses__, __bases__, __mro__, __globals__ etc. are
# deliberately excluded — each is a step on the classic
# ().__class__.__base__.__subclasses__() style object-graph walk back to a
# dangerous class or module.
_ALLOWED_DUNDERS = frozenset({
    "__init__", "__str__", "__repr__", "__len__",
    "__getitem__", "__setitem__", "__contains__",
    "__iter__", "__next__", "__enter__", "__exit__",
    "__eq__", "__ne__", "__lt__", "__gt__",
    "__le__", "__ge__", "__hash__", "__bool__",
    "__add__", "__sub__", "__mul__", "__truediv__",
    "__floordiv__", "__mod__", "__pow__",
    "__name__", "__doc__",
})

# str.format's dotted mini-language (e.g. "{0.__globals__}".format(fn)) reaches
# dunder attributes from INSIDE a string constant, where the AST Attribute/Name
# checks below never look. Flag these markers wherever they appear in a string
# literal — a beginner's own code has no legitimate reason to reference them.
DANGEROUS_STRING_MARKERS = (
    "__globals__", "__builtins__", "__subclasses__", "__import__",
    "__reduce__", "__loader__", "__base__", "__bases__", "__mro__",
    "f_builtins", "f_back", "f_globals", "f_locals",
    "gi_frame", "cr_frame", "ag_frame", "tb_frame",
)


class CodeSecurityError(Exception):
    """Raised when submitted code contains blocked constructs."""
    pass


def scan_for_dangerous_code(code: str) -> list[str]:
    """Parse code as AST and check for dangerous imports, builtins, and constructs.

    Returns a list of human-readable violation descriptions.
    """
    violations: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Syntax errors are fine — the runner will report them naturally
        return []

    for node in ast.walk(tree):
        # --- Import checks (allowlist — deny anything not explicitly safe) ---
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module not in ALLOWED_MODULES:
                    violations.append(
                        f"Line {node.lineno}: import '{alias.name}' is not allowed in the practice sandbox. "
                        f"This sandbox only permits a safe set of standard-library modules for learning exercises."
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                if root_module not in ALLOWED_MODULES:
                    violations.append(
                        f"Line {node.lineno}: import from '{node.module}' is not allowed in the practice sandbox."
                    )

        # --- Dangerous built-in calls ---
        elif isinstance(node, ast.Call):
            func = node.func
            func_name = None
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr

            if func_name in BLOCKED_BUILTINS:
                violations.append(
                    f"Line {node.lineno}: '{func_name}()' is not allowed in the practice sandbox."
                )

            # Block open() entirely — labs use input parameters, not files
            if func_name == "input":
                violations.append(
                    f"Line {node.lineno}: input() is not available in this practice runner. "
                    f"Use a function parameter or a sample variable instead."
                )

            # Bare help() (no arguments) opens pydoc's interactive console,
            # which reads from stdin — the subprocess is non-interactive, so
            # this hangs until the run timeout, exactly like an unblocked
            # input() call would. help(some_object) is fine: it prints
            # immediately and returns, so only the zero-argument form is
            # blocked here.
            if func_name == "help" and not node.args and not node.keywords:
                violations.append(
                    f"Line {node.lineno}: help() with no arguments opens an interactive prompt "
                    f"this non-interactive runner can't respond to. Try help(str) or "
                    f"help(some_function) instead — those print immediately."
                )

            if func_name == "open":
                violations.append(
                    f"Line {node.lineno}: open() is not available in this sandbox. "
                    f"Use variables and function parameters to work with data in your solution."
                )

        # --- Direct __builtins__ access (guards subscript bypass: __builtins__['__import__']('os')) ---
        elif isinstance(node, ast.Name):
            if node.id == "__builtins__":
                violations.append(
                    f"Line {node.lineno}: access to '__builtins__' is not allowed in the sandbox."
                )

        # --- Attribute access: dunders, and non-dunder frame-walking pivots ---
        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_FRAME_ATTRS:
                violations.append(
                    f"Line {node.lineno}: access to '{node.attr}' is restricted in the sandbox."
                )
            elif node.attr.startswith("__") and node.attr.endswith("__"):
                if node.attr not in _ALLOWED_DUNDERS:
                    violations.append(
                        f"Line {node.lineno}: access to '{node.attr}' is restricted in the sandbox."
                    )

        # --- String literals referencing frame/builtins internals (format-string bypass) ---
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            matched = next((m for m in DANGEROUS_STRING_MARKERS if m in node.value), None)
            if matched:
                violations.append(
                    f"Line {node.lineno}: this string references the restricted internal name "
                    f"'{matched}' and is not allowed in the sandbox."
                )

    return violations


# ---------------------------------------------------------------------------
# Coach feedback (built-in, no AI required)
# ---------------------------------------------------------------------------

def coach_feedback(
    code: str,
    stdout: str,
    stderr: str,
    tests: list[dict[str, Any]],
    exercise: dict[str, Any] | None = None,
) -> list[str]:
    """Generate built-in feedback based on code analysis and test results.

    This provides immediate help even when no AI provider is configured.
    """
    feedback: list[str] = []
    passed = sum(1 for test in tests if test.get("passed"))
    total = len(tests)

    if total and passed == total:
        feedback.append("All tests passed — your solution is correct. Try explaining your approach in three sentences.")
    elif total:
        feedback.append(f"{passed}/{total} tests passed. Focus on the first failing test and compare expected vs actual output.")

    if stderr:
        # Provide targeted error guidance
        if "NameError" in stderr:
            feedback.append("NameError means Python can't find a name you used. Check spelling and make sure the variable or function is defined before you use it.")
        elif "TypeError" in stderr:
            feedback.append("TypeError means you used a value in a way its type doesn't support. Check argument counts and data types.")
        elif "IndentationError" in stderr or "unexpected indent" in stderr:
            feedback.append("IndentationError means your code blocks aren't aligned correctly. Python uses indentation to define blocks.")
        elif "SyntaxError" in stderr:
            feedback.append("SyntaxError means Python couldn't understand your code. Check for missing colons, unmatched brackets, or unclosed quotes.")
        elif "IndexError" in stderr:
            feedback.append("IndexError means you tried to access a position that doesn't exist. Check your list length and index values.")
        elif "KeyError" in stderr:
            feedback.append("KeyError means the dictionary key you used doesn't exist. Try using .get() with a default value.")
        elif "AttributeError" in stderr:
            feedback.append("AttributeError means you tried to use a method or property that doesn't exist on that object. Check the object's type.")
        elif "ValueError" in stderr:
            feedback.append("ValueError means the value has the right type but wrong content. Check your input data and conversions.")
        else:
            feedback.append("Python raised an error. Read the last line of the traceback first to understand the exception type, then look at the line number.")

    try:
        tree = ast.parse(code or "\n")
    except SyntaxError as exc:
        feedback.append(f"Syntax issue near line {exc.lineno}: {exc.msg}. Check brackets, quotes, colons, and indentation.")
        return feedback

    function_defs = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not function_defs and total:
        feedback.append("This exercise expects a function. Make sure you've defined a function with 'def' and the correct name.")

    if "print(" in code and total and not all(t.get("passed") for t in tests):
        feedback.append("Tip: Make sure your function returns the value, not just prints it. Tests check the return value.")

    if any(isinstance(node, ast.ExceptHandler) and node.type is None for node in ast.walk(tree)):
        feedback.append("Avoid bare 'except:' blocks — catch a specific exception type so you don't hide real bugs.")

    if len(code.splitlines()) > 60:
        feedback.append("Your solution is getting long. See if you can extract a helper function to keep it readable.")

    # Exercise-specific hint
    if exercise and not all(t.get("passed") for t in tests):
        hint = exercise.get("hint", "")
        if hint and total and passed == 0:
            feedback.append(f"Stuck? Here's a nudge: {hint}")

    if not feedback:
        feedback.append("Run the code, inspect the output, then try explaining your approach aloud.")

    return feedback


# ---------------------------------------------------------------------------
# Test harness builder
# ---------------------------------------------------------------------------

def build_test_code(user_code: str, tests: list[dict[str, Any]]) -> str:
    """Build the Python script that runs user code + test assertions."""
    # Encode tests as a JSON string that gets parsed inside the subprocess.
    # This avoids the JSON/Python literal mismatch (true vs True, null vs None).
    encoded_tests_json = json.dumps(json.dumps(tests))
    return f"""
import builtins as _bi
import contextlib
import io
import json
import sys
import traceback

_BLOCKED = frozenset({{'eval', 'exec', 'compile', 'breakpoint', 'open', 'input', 'globals', 'locals', 'vars', 'getattr', 'setattr', 'delattr'}})
# NOTE: '__import__' is deliberately NOT in this set — Python's own `import`
# statement calls __builtins__.__import__ internally, so removing it would
# break every legitimate `import json`/`import math`/etc. Direct calls to
# __import__(...) as a function, and __builtins__ name/subscript access, are
# already blocked by the AST scan (BLOCKED_BUILTINS / the __builtins__ Name
# check), which is the correct layer to stop that specific bypass.
TESTS = json.loads({encoded_tests_json})
USER_GLOBALS = {{"__name__": "__main__", "__builtins__": {{k: v for k, v in vars(_bi).items() if k not in _BLOCKED}}}}

def _safe(value):
    # Keep JSON-serializable values as-is; fall back to a truncated repr so an
    # exotic return value (set, custom object, etc.) can never crash json.dumps.
    try:
        json.dumps(value)
        return value
    except Exception:
        try:
            text = repr(value)
        except Exception:
            text = "<unrepresentable>"
        return text if len(text) <= 200 else text[:197] + "..."

def _norm(value):
    # Tuples cannot be expressed in JSON, so an 'expected' value loaded from a
    # lab file is always a list. Normalize tuples<->lists (recursively) before
    # comparing so a correct tuple return is not marked wrong.
    if isinstance(value, (list, tuple)):
        return [_norm(item) for item in value]
    if isinstance(value, dict):
        return {{key: _norm(val) for key, val in value.items()}}
    return value

def _run_user_code():
    # Compile with a learner-facing filename so syntax errors and tracebacks
    # point at the learner's own line, never the runner's wrapper script.
    code_obj = compile({user_code!r}, "<your code>", "exec")
    exec(code_obj, USER_GLOBALS)

_top_level_failed = False

try:
    _run_user_code()
except SyntaxError as _exc:
    _top_level_failed = True
    _where = (" on line " + str(_exc.lineno)) if _exc.lineno else ""
    print("Your code has a syntax error" + _where + ": " + str(_exc.msg), file=sys.stderr)
except Exception as _exc:
    _top_level_failed = True
    # Show only the learner's frames, not the runner's internal wrapper frames.
    _frames = [fr for fr in traceback.extract_tb(sys.exc_info()[2]) if fr.filename == "<your code>"]
    if _frames:
        traceback.print_list(_frames, file=sys.stderr)
    print(type(_exc).__name__ + ": " + str(_exc), file=sys.stderr)

results = []
for test in TESTS:
    expression = test.get("call", "")
    expected = test.get("expected")
    label = test.get("label", expression)
    capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(capture):
            actual = eval(expression, USER_GLOBALS)
        try:
            passed = bool(_norm(actual) == _norm(expected))
        except Exception:
            passed = False
        results.append({{
            "label": label,
            "call": expression,
            "expected": expected,
            "actual": _safe(actual),
            "printed": capture.getvalue(),
            "passed": passed,
        }})
    except Exception as exc:
        results.append({{
            "label": label,
            "call": expression,
            "expected": expected,
            "actual": "could not run - see error above" if _top_level_failed else repr(exc),
            "printed": capture.getvalue(),
            "passed": False,
        }})

print("\\n__PY_SKILL_LAB_RESULTS__" + json.dumps(results))
"""


def parse_test_results(stdout: str) -> list[dict[str, Any]]:
    """Extract structured test results from runner stdout."""
    marker = "__PY_SKILL_LAB_RESULTS__"
    if marker not in stdout:
        return []
    raw = stdout.rsplit(marker, 1)[-1].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def strip_test_marker(stdout: str) -> str:
    """Remove the test result marker from user-visible output."""
    marker = "__PY_SKILL_LAB_RESULTS__"
    if marker not in stdout:
        return stdout
    return stdout.rsplit(marker, 1)[0].strip()


MAX_STDOUT_BYTES = 300_000  # cap captured stdout so a tight print loop can't return an unbounded HTTP body


def _cap_stdout(stdout: str, limit: int = MAX_STDOUT_BYTES) -> str:
    """Truncate oversized stdout, keeping the tail.

    The 6s RUN_TIMEOUT_SECONDS already bounds how long a print loop can run,
    but nothing previously bounded how much of its output was captured and
    returned — `print('A'*500000)` produced a ~500 KB response with no cap
    to match the 100 KB request-body cap. The results marker (__PY_SKILL_LAB_
    RESULTS__) is always printed last, so keeping the tail rather than the
    head preserves it whenever possible.
    """
    data = stdout.encode("utf-8", errors="ignore")
    if len(data) <= limit:
        return stdout
    return "... (earlier output truncated — you printed too much)\n" + data[-limit:].decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_user_code(payload: dict[str, Any], exercises: list[dict[str, Any]]) -> dict[str, Any]:
    """Execute learner code safely and return structured results."""
    code = str(payload.get("code", ""))
    exercise_id = str(payload.get("exercise_id", ""))
    exercise = next((item for item in exercises if item["id"] == exercise_id), None)

    if exercise_id and exercise is None:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Unknown exercise_id: '{exercise_id}'.",
            "tests": [],
            "feedback": ["The exercise ID was not recognised. Please reload the page."],
        }

    # --- Size check ---
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "Code is too large for this sandbox.",
            "tests": [],
            "feedback": ["Keep practice snippets small and focused."],
        }

    # --- Security scan ---
    violations = scan_for_dangerous_code(code)
    if violations:
        feedback = ["Your code uses constructs that are blocked in this practice sandbox."]
        violation_text = "\n".join(violations)
        if "input()" in violation_text:
            feedback.append("Rewrite interactive prompts as a function parameter or a sample variable, then run the code again.")
        if "open()" in violation_text:
            feedback.append("File reading and writing are blocked here; use variables, lists, dictionaries, or function parameters instead.")
        if "help() with no arguments" in violation_text:
            feedback.append("Pass something to help(), like help(str) or help(len), instead of calling it with no arguments.")
        if not any(name in violation_text for name in ("input()", "open()", "help() with no arguments")):
            feedback.append("System access is restricted so practice code stays focused on the exercise logic.")
        feedback.append("Focus on Python's built-in data types, functions, control flow, and return values.")
        return {
            "ok": False,
            "stdout": "",
            "stderr": violation_text,
            "tests": [],
            "feedback": feedback,
        }

    # --- Build and run ---
    tests = exercise.get("tests", []) if exercise else []
    test_code = build_test_code(code, tests)

    try:
        # Create isolated temp directory for execution.
        # NOTE: We use mkdtemp() instead of TemporaryDirectory() because on Windows
        # the TemporaryDirectory.__exit__ cleanup races with the OS releasing the
        # subprocess's directory handle, causing WinError 5 'Access is denied'.
        # shutil.rmtree(ignore_errors=True) silently skips any files still locked.
        tmpdir = tempfile.mkdtemp(prefix="pyskilllab_")
        try:
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            # Remove potentially dangerous env vars from child process
            for key in ("PYTHONSTARTUP", "PYTHONPATH"):
                env.pop(key, None)

            proc = subprocess.run(
                [sys.executable, "-I", "-B", "-c", test_code],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT_SECONDS,
                cwd=tmpdir,
                env=env,
            )
            stdout = _cap_stdout(proc.stdout)
            stderr = proc.stderr
        finally:
            # ignore_errors=True: if Windows still holds a handle, the dir stays
            # in %TEMP% until the OS cleans it up — not a correctness problem.
            shutil.rmtree(tmpdir, ignore_errors=True)
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = "Execution timed out. Check for infinite loops or very slow code."
    except Exception as exc:
        logger.exception("Code runner failed unexpectedly")
        stdout = ""
        stderr = f"Runner error: {exc}"

    parsed_tests = parse_test_results(stdout)
    clean_stdout = strip_test_marker(stdout)
    return {
        "ok": not stderr and all(test.get("passed") for test in parsed_tests),
        "stdout": clean_stdout,
        "stderr": stderr,
        "tests": parsed_tests,
        "feedback": coach_feedback(code, clean_stdout, stderr, parsed_tests, exercise),
    }


# ---------------------------------------------------------------------------
# Execution visualizer (step-through trace)
# ---------------------------------------------------------------------------

MAX_TRACE_STEPS = 300
TRACE_MARKER = "__PY_TRACE__"


def build_trace_code(user_code: str) -> str:
    """Build a subprocess script that runs user code under sys.settrace.

    It records one step per executed line — the line number plus a snapshot of
    the data variables in scope — so the frontend can replay execution. Values
    are serialized safely (non-JSON values fall back to a truncated repr) so an
    exotic value can never crash the recorder.
    """
    return f"""
import builtins as _bi
import sys, json, io, contextlib, types

_BLOCKED = frozenset({{'eval', 'exec', 'compile', 'breakpoint', 'open', 'input', 'globals', 'locals', 'vars', 'getattr', 'setattr', 'delattr'}})
# NOTE: '__import__' is deliberately NOT in this set — Python's own `import`
# statement calls __builtins__.__import__ internally, so removing it would
# break every legitimate `import json`/`import math`/etc. Direct calls to
# __import__(...) as a function, and __builtins__ name/subscript access, are
# already blocked by the AST scan (BLOCKED_BUILTINS / the __builtins__ Name
# check), which is the correct layer to stop that specific bypass.
MAX_STEPS = {MAX_TRACE_STEPS}
USER_FILE = "<user>"
steps = []
state = {{"last_line": 0}}

def _safe(value):
    try:
        json.dumps(value)
        return value
    except Exception:
        try:
            text = repr(value)
        except Exception:
            text = "<unrepresentable>"
        return text if len(text) <= 120 else text[:117] + "..."

def _skip(value):
    return isinstance(value, (
        types.FunctionType, types.LambdaType, types.ModuleType, type,
        types.BuiltinFunctionType, types.MethodType,
    ))

def _snapshot(namespace):
    out = {{}}
    for key, value in list(namespace.items()):
        if key.startswith("__") or _skip(value):
            continue
        out[key] = _safe(value)
    return out

class _StepLimit(Exception):
    pass

def _tracer(frame, event, arg):
    if frame.f_code.co_filename != USER_FILE:
        return _tracer
    if event == "line":
        if len(steps) >= MAX_STEPS:
            raise _StepLimit()
        state["last_line"] = frame.f_lineno
        steps.append({{"line": frame.f_lineno, "vars": _snapshot(frame.f_locals), "out": capture.getvalue()}})
    return _tracer

result = {{"steps": steps, "stdout": "", "truncated": False, "error": "", "error_line": 0}}
user_globals = {{"__name__": "__main__", "__file__": USER_FILE, "__builtins__": {{k: v for k, v in vars(_bi).items() if k not in _BLOCKED}}}}
capture = io.StringIO()
try:
    compiled = compile({user_code!r}, USER_FILE, "exec")
    sys.settrace(_tracer)
    with contextlib.redirect_stdout(capture):
        exec(compiled, user_globals)
except _StepLimit:
    result["truncated"] = True
except SyntaxError as exc:
    result["error"] = "SyntaxError: " + str(exc.msg)
    if exc.lineno:
        result["error_line"] = exc.lineno
except Exception as exc:
    result["error"] = type(exc).__name__ + ": " + str(exc)
finally:
    sys.settrace(None)

# A final snapshot captures assignments made on the last executed line,
# which produces no further 'line' event of its own.
# Skip when last_line==0 (no lines ran, e.g. a compile-time SyntaxError) so
# a beginner does not see a misleading "Step 1 of 1" with phantom execution.
result["stdout"] = capture.getvalue()
if state["last_line"] > 0:
    steps.append({{"line": state["last_line"], "vars": _snapshot(user_globals), "final": True, "out": result["stdout"]}})
print("{TRACE_MARKER}" + json.dumps(result))
"""


def parse_trace_result(stdout: str) -> dict[str, Any] | None:
    """Extract the structured trace payload from subprocess stdout."""
    if TRACE_MARKER not in stdout:
        return None
    raw = stdout.rsplit(TRACE_MARKER, 1)[-1].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def trace_user_code(payload: dict[str, Any]) -> dict[str, Any]:
    """Run learner code and return a step-by-step execution trace."""
    code = str(payload.get("code", ""))

    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return {"ok": False, "steps": [], "stdout": "", "error": "Code is too large to visualize."}

    violations = scan_for_dangerous_code(code)
    if violations:
        return {
            "ok": False,
            "steps": [],
            "stdout": "",
            "error": "\n".join(violations),
        }

    trace_code = build_trace_code(code)
    try:
        tmpdir = tempfile.mkdtemp(prefix="pyskilllab_trace_")
        try:
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            for key in ("PYTHONSTARTUP", "PYTHONPATH"):
                env.pop(key, None)
            proc = subprocess.run(
                [sys.executable, "-I", "-B", "-c", trace_code],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT_SECONDS,
                cwd=tmpdir,
                env=env,
            )
            stdout = _cap_stdout(proc.stdout)
            stderr = proc.stderr
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except subprocess.TimeoutExpired:
        return {"ok": False, "steps": [], "stdout": "",
                "error": "Execution timed out. Check for infinite loops or very slow code."}
    except Exception as exc:
        logger.exception("Trace runner failed unexpectedly")
        return {"ok": False, "steps": [], "stdout": "", "error": f"Visualizer error: {exc}"}

    parsed = parse_trace_result(stdout)
    if parsed is None:
        return {"ok": False, "steps": [], "stdout": "",
                "error": stderr or "Could not produce an execution trace."}

    return {
        "ok": not parsed.get("error"),
        "steps": parsed.get("steps", []),
        "stdout": parsed.get("stdout", ""),
        "truncated": parsed.get("truncated", False),
        "error": parsed.get("error", ""),
        "error_line": parsed.get("error_line", 0),
    }
