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
