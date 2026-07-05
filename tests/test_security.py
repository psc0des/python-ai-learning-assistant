"""Tests for security scanning.

Verifies that the AST-based scanner catches dangerous code constructs
and that safe code is allowed.
"""

import pytest
from runner import scan_for_dangerous_code


class TestBlockedImports:
    def test_blocks_os_import(self):
        violations = scan_for_dangerous_code("import os")
        assert len(violations) >= 1
        assert "os" in violations[0]

    def test_blocks_subprocess(self):
        violations = scan_for_dangerous_code("import subprocess")
        assert len(violations) >= 1

    def test_blocks_from_os(self):
        violations = scan_for_dangerous_code("from os import remove")
        assert len(violations) >= 1

    def test_blocks_socket(self):
        violations = scan_for_dangerous_code("import socket")
        assert len(violations) >= 1

    def test_blocks_shutil(self):
        violations = scan_for_dangerous_code("import shutil")
        assert len(violations) >= 1

    def test_blocks_urllib(self):
        violations = scan_for_dangerous_code("import urllib")
        assert len(violations) >= 1

    def test_blocks_pathlib(self):
        violations = scan_for_dangerous_code("import pathlib")
        assert len(violations) >= 1

    def test_blocks_nested_import(self):
        violations = scan_for_dangerous_code("import os.path")
        assert len(violations) >= 1


class TestBlockedBuiltins:
    def test_blocks_exec(self):
        violations = scan_for_dangerous_code("exec('print(1)')")
        assert len(violations) >= 1

    def test_blocks_eval(self):
        violations = scan_for_dangerous_code("eval('1+1')")
        assert len(violations) >= 1

    def test_blocks_compile(self):
        violations = scan_for_dangerous_code("compile('pass', '', 'exec')")
        assert len(violations) >= 1

    def test_allows_re_compile_attribute_call(self):
        # Regression test: re.compile(...) is a method/attribute call named
        # "compile" on the `re` module, not the dangerous bare compile()
        # builtin — the two must not be conflated. Found via content
        # authoring: this previously false-positive-blocked the extremely
        # common, safe re.compile().
        violations = scan_for_dangerous_code("import re\npattern = re.compile(r'\\\\d+')\n")
        assert violations == []

    def test_still_blocks_builtins_attribute_eval_bypass(self):
        # Confirms narrowing the BLOCKED_BUILTINS check to ast.Name calls
        # did not reopen the __builtins__.eval(...) style bypass — it's
        # still caught by the separate __builtins__ Name-access check.
        violations = scan_for_dangerous_code("__builtins__.eval('1+1')")
        assert violations
        assert any("__builtins__" in v for v in violations)

    def test_blocks_dunder_import(self):
        violations = scan_for_dangerous_code("__import__('os')")
        assert len(violations) >= 1

    def test_blocks_breakpoint(self):
        violations = scan_for_dangerous_code("breakpoint()")
        assert len(violations) >= 1


class TestBlockedFileAccess:
    def test_blocks_open_write(self):
        violations = scan_for_dangerous_code("f = open('x.txt', 'w')")
        assert len(violations) >= 1

    def test_blocks_open_append(self):
        violations = scan_for_dangerous_code("f = open('x.txt', 'a')")
        assert len(violations) >= 1

    def test_blocks_open_read(self):
        violations = scan_for_dangerous_code("f = open('x.txt', 'r')")
        assert len(violations) >= 1

    def test_blocks_open_bare(self):
        violations = scan_for_dangerous_code("f = open('secret.txt')")
        assert len(violations) >= 1


class TestSafeCode:
    def test_allows_basic_function(self):
        code = "def add(a, b):\n    return a + b"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_list_operations(self):
        code = "items = [1, 2, 3]\nitems.append(4)\nprint(items)"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_dict_operations(self):
        code = "d = {'a': 1}\nd['b'] = 2"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_string_operations(self):
        code = "text = 'hello world'\nwords = text.split()\nresult = ' '.join(reversed(words))"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_class_definition(self):
        code = "class Counter:\n    def __init__(self):\n        self.count = 0\n    def increment(self):\n        self.count += 1"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_math_import(self):
        code = "import math\nprint(math.sqrt(16))"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_json_import(self):
        code = "import json\ndata = json.loads('{}')"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_blocks_open_read_in_safe_class(self):
        # open() is blocked entirely — even read mode
        code = "f = open('x.txt', 'r')"
        violations = scan_for_dangerous_code(code)
        assert len(violations) >= 1

    def test_handles_syntax_error_gracefully(self):
        code = "def f(\n"
        violations = scan_for_dangerous_code(code)
        assert violations == []  # Syntax errors are OK — runner will report them

    def test_allows_try_except(self):
        code = "try:\n    int('x')\nexcept ValueError:\n    pass"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_allowed_dunders(self):
        code = "class Foo:\n    def __init__(self):\n        pass\n    def __str__(self):\n        return 'foo'\n    def __len__(self):\n        return 0"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_contextlib_import(self):
        # Needed for the context-managers curriculum content
        code = "import contextlib\n@contextlib.contextmanager\ndef cm():\n    yield 1"
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_itertools_functools_collections_typing(self):
        code = (
            "import itertools\nimport functools\nimport collections\nimport typing\n"
            "import dataclasses\nimport enum\n"
        )
        violations = scan_for_dangerous_code(code)
        assert violations == []

    def test_allows_time_import(self):
        # time.perf_counter()/time.sleep() are pure — no filesystem, network,
        # or process access — and are needed for the decorator-timing example
        # in the intermediate-python-patterns lesson content.
        code = "import time\nstart = time.perf_counter()\nprint(time.perf_counter() - start)"
        violations = scan_for_dangerous_code(code)
        assert violations == []


class TestModuleAllowlist:
    """Regression tests for the CRITICAL sandbox-escape finding: the old module
    policy was a denylist, so any module not explicitly named (gc, inspect,
    codecs, platform, sysconfig, io, ...) passed straight through and could be
    used to reach the real os module or the interpreter's real builtins. The
    policy is now an allowlist — anything not explicitly safe is rejected."""

    def test_blocks_gc_import(self):
        # The original proven escape: gc.get_objects() walk to the os module
        violations = scan_for_dangerous_code("import gc")
        assert len(violations) >= 1

    def test_blocks_inspect_import(self):
        violations = scan_for_dangerous_code("import inspect")
        assert len(violations) >= 1

    def test_blocks_codecs_import(self):
        violations = scan_for_dangerous_code("import codecs")
        assert len(violations) >= 1

    def test_blocks_platform_import(self):
        violations = scan_for_dangerous_code("import platform")
        assert len(violations) >= 1

    def test_blocks_sysconfig_import(self):
        violations = scan_for_dangerous_code("import sysconfig")
        assert len(violations) >= 1

    def test_blocks_io_import(self):
        violations = scan_for_dangerous_code("import io")
        assert len(violations) >= 1


class TestFrameWalkingBlocked:
    """Regression tests for the CRITICAL root-cause finding: any live frame or
    generator object hands back f_builtins/f_globals, which are the REAL,
    unstripped interpreter builtins — a one-hop pivot to eval/exec/open that
    does not require importing anything at all."""

    def test_blocks_generator_gi_frame(self):
        code = "def g():\n    yield 1\ng().gi_frame\n"
        violations = scan_for_dangerous_code(code)
        assert len(violations) >= 1
        assert any("gi_frame" in v for v in violations)

    def test_blocks_f_back(self):
        code = "some_frame.f_back\n"
        violations = scan_for_dangerous_code(code)
        assert any("f_back" in v for v in violations)

    def test_blocks_globals_attribute(self):
        code = "def f():\n    pass\nf.__globals__\n"
        violations = scan_for_dangerous_code(code)
        assert any("__globals__" in v for v in violations)

    def test_blocks_f_builtins_attr(self):
        code = "frame_holder.f_builtins\n"
        violations = scan_for_dangerous_code(code)
        assert any("f_builtins" in v for v in violations)

    def test_blocks_tb_frame(self):
        code = "try:\n    1 / 0\nexcept Exception as e:\n    e.__traceback__.tb_frame\n"
        violations = scan_for_dangerous_code(code)
        assert violations, "Expected violation for __traceback__ and/or tb_frame access"

    def test_blocks_class_attribute(self):
        # __class__ used to be allowlisted; it is the first hop of
        # ().__class__.__base__.__subclasses__() and is no longer permitted.
        violations = scan_for_dangerous_code("x = []\nx.__class__\n")
        assert any("__class__" in v for v in violations)


class TestFormatStringBypassBlocked:
    """Regression test for the leak found during audit: '{0.__globals__}'.format(fn)
    reaches dunder attributes from inside a string literal, where the AST
    Attribute/Name checks never look because the dunder is text, not a node."""

    def test_blocks_format_string_globals_leak(self):
        code = "def f():\n    pass\nprint('{0.__globals__}'.format(f))\n"
        violations = scan_for_dangerous_code(code)
        assert any("__globals__" in v for v in violations)

    def test_blocks_format_string_builtins_leak(self):
        code = "print('{0.__builtins__}'.format(object()))\n"
        violations = scan_for_dangerous_code(code)
        assert violations
