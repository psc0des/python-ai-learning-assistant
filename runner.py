"""Sandboxed code runner for Python Skill Lab.

Executes learner code in a restricted subprocess with:
- AST-based import and built-in blocking before execution
- open() blocked via AST scan — no file I/O from learner code
- Strict timeout with process kill
- Size limits on submitted code
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

# ---------------------------------------------------------------------------
# Dangerous construct detection
# ---------------------------------------------------------------------------

BLOCKED_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "socket", "http",
    "urllib", "requests", "pathlib", "ctypes", "signal",
    "multiprocessing", "threading", "pickle", "shelve",
    "importlib", "runpy", "code", "codeop", "compileall",
    "webbrowser", "ftplib", "smtplib", "telnetlib",
    "xmlrpc", "tkinter", "turtle", "antigravity",
    "_thread", "concurrent",
})

BLOCKED_BUILTINS = frozenset({
    "exec", "eval", "compile", "__import__",
    "breakpoint", "exit", "quit",
    "globals", "locals", "vars",
    "getattr", "setattr", "delattr",
})



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
        # --- Import checks ---
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module in BLOCKED_MODULES:
                    violations.append(
                        f"Line {node.lineno}: import '{alias.name}' is not allowed in the practice sandbox. "
                        f"This sandbox is for learning exercises — system access modules are blocked for safety."
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                if root_module in BLOCKED_MODULES:
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
            if func_name == "open":
                violations.append(
                    f"Line {node.lineno}: open() is not available in this sandbox. "
                    f"Use variables and function parameters to work with data in your solution."
                )

        # --- Dunder attribute access (e.g. __class__, __subclasses__) ---
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                if node.attr not in {"__init__", "__str__", "__repr__", "__len__",
                                      "__getitem__", "__setitem__", "__contains__",
                                      "__iter__", "__next__", "__enter__", "__exit__",
                                      "__eq__", "__ne__", "__lt__", "__gt__",
                                      "__le__", "__ge__", "__hash__", "__bool__",
                                      "__add__", "__sub__", "__mul__", "__truediv__",
                                      "__floordiv__", "__mod__", "__pow__",
                                      "__name__", "__doc__", "__class__"}:
                    violations.append(
                        f"Line {node.lineno}: access to '{node.attr}' is restricted in the sandbox."
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
import contextlib
import io
import json
import traceback

TESTS = json.loads({encoded_tests_json})
USER_GLOBALS = {{"__name__": "__main__"}}

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

try:
    exec({user_code!r}, USER_GLOBALS)
except Exception:
    traceback.print_exc()

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
            "actual": repr(exc),
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
        return {
            "ok": False,
            "stdout": "",
            "stderr": "\n".join(violations),
            "tests": [],
            "feedback": [
                "Your code uses constructs that are blocked in this practice sandbox.",
                "This sandbox is designed for learning exercises — system access is restricted for safety.",
                "Focus on the exercise logic using Python's built-in data types and standard operations.",
            ],
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
            stdout = proc.stdout
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
import sys, json, io, contextlib, types

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
user_globals = {{"__name__": "__main__", "__file__": USER_FILE}}
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
            stdout = proc.stdout
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
