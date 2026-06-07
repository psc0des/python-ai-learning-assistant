"""Tests for the sandboxed code runner.

Verifies that:
- Valid code runs and returns correct results
- Test harness parses results correctly
- Timeouts are handled
- Coach feedback is generated
"""

import pytest
from content_loader import load_content
from runner import (
    run_user_code,
    build_test_code,
    parse_test_results,
    strip_test_marker,
    coach_feedback,
    scan_for_dangerous_code,
)

EXERCISES = load_content().exercises


class TestBuildTestCode:
    def test_builds_valid_python(self):
        code = build_test_code("x = 1", [{"call": "x", "expected": 1, "label": "check x"}])
        assert "__PY_SKILL_LAB_RESULTS__" in code
        assert "x = 1" in code

    def test_empty_tests(self):
        code = build_test_code("pass", [])
        assert "__PY_SKILL_LAB_RESULTS__" in code


class TestNonSerializableReturn:
    def test_set_return_does_not_crash_harness(self):
        # Regression for P1.1: a non-JSON-serializable return value must degrade
        # to a readable repr and a failed test, never crash the result harness.
        exercises = [{"id": "p1", "tests": [
            {"call": "f()", "expected": [1, 2, 3], "label": "set-vs-list"}
        ]}]
        result = run_user_code({"code": "def f():\n    return {1, 2, 3}\n", "exercise_id": "p1"}, exercises)
        assert len(result["tests"]) == 1
        test = result["tests"][0]
        assert test["passed"] is False
        assert isinstance(test["actual"], str) and "1" in test["actual"]


class TestTupleListComparison:
    def test_tuple_return_matches_list_expected(self):
        # Regression for P1.2: JSON has no tuples, so 'expected' is always a list.
        # A correct tuple return must compare equal, not be marked wrong.
        exercises = [{"id": "tp", "tests": [
            {"call": "f()", "expected": [1, 2], "label": "tuple"}
        ]}]
        result = run_user_code({"code": "def f():\n    return (1, 2)\n", "exercise_id": "tp"}, exercises)
        assert result["tests"][0]["passed"] is True

    def test_genuine_mismatch_still_fails(self):
        exercises = [{"id": "tp2", "tests": [
            {"call": "f()", "expected": [1, 2, 3], "label": "mismatch"}
        ]}]
        result = run_user_code({"code": "def f():\n    return [1, 2]\n", "exercise_id": "tp2"}, exercises)
        assert result["tests"][0]["passed"] is False


class TestParseTestResults:
    def test_parses_valid_results(self):
        stdout = 'hello\n__PY_SKILL_LAB_RESULTS__[{"label":"a","passed":true}]'
        results = parse_test_results(stdout)
        assert len(results) == 1
        assert results[0]["passed"] is True

    def test_no_marker(self):
        assert parse_test_results("just output") == []

    def test_bad_json(self):
        assert parse_test_results("__PY_SKILL_LAB_RESULTS__{invalid}") == []


class TestStripTestMarker:
    def test_strips_marker(self):
        stdout = "hello\n__PY_SKILL_LAB_RESULTS__[...]"
        assert strip_test_marker(stdout) == "hello"

    def test_no_marker(self):
        assert strip_test_marker("just output") == "just output"


class TestCoachFeedback:
    def test_all_tests_passed(self):
        feedback = coach_feedback("def f(): return 1", "", "", [{"passed": True}])
        assert any("correct" in f.lower() or "passed" in f.lower() for f in feedback)

    def test_partial_pass(self):
        tests = [{"passed": True}, {"passed": False}]
        feedback = coach_feedback("def f(): return 1", "", "", tests)
        assert any("1/2" in f for f in feedback)

    def test_name_error_guidance(self):
        feedback = coach_feedback("x = y", "", "NameError: name 'y' is not defined", [])
        assert any("NameError" in f for f in feedback)

    def test_type_error_guidance(self):
        feedback = coach_feedback("x = 1 + 'a'", "", "TypeError: ...", [])
        assert any("TypeError" in f for f in feedback)

    def test_syntax_error(self):
        feedback = coach_feedback("def f(\n", "", "", [])
        assert any("syntax" in f.lower() for f in feedback)

    def test_bare_except_warning(self):
        code = "try:\n    pass\nexcept:\n    pass"
        feedback = coach_feedback(code, "", "", [])
        assert any("except" in f.lower() for f in feedback)

    def test_no_function_warning(self):
        feedback = coach_feedback("x = 1", "", "", [{"passed": False}])
        assert any("function" in f.lower() for f in feedback)


class TestRunUserCode:
    def test_passing_exercise(self):
        result = run_user_code(
            {
                "code": "def reverse_words(text):\n    return ' '.join(text.split()[::-1])\n",
                "exercise_id": "reverse-words",
            },
            EXERCISES,
        )
        assert result["ok"] is True
        assert all(t["passed"] for t in result["tests"])

    def test_failing_exercise(self):
        result = run_user_code(
            {
                "code": "def reverse_words(text):\n    return text\n",
                "exercise_id": "reverse-words",
            },
            EXERCISES,
        )
        assert result["ok"] is False

    def test_unknown_exercise(self):
        result = run_user_code(
            {"code": "print('hello')", "exercise_id": "nonexistent"},
            EXERCISES,
        )
        assert result["ok"] is False
        assert "nonexistent" in result["stderr"]

    def test_empty_exercise_id_runs_as_scratchpad(self):
        result = run_user_code(
            {"code": "print('hello')", "exercise_id": ""},
            EXERCISES,
        )
        assert "stdout" in result

    def test_oversized_code(self):
        result = run_user_code(
            {"code": "x = 1\n" * 20001, "exercise_id": "reverse-words"},
            EXERCISES,
        )
        assert result["ok"] is False
        assert "too large" in result["stderr"].lower()

    def test_timeout_code(self):
        result = run_user_code(
            {"code": "while True: pass", "exercise_id": "reverse-words"},
            EXERCISES,
        )
        assert result["ok"] is False
        assert "timed out" in result["stderr"].lower()

    def test_input_is_blocked_before_timeout(self):
        result = run_user_code(
            {"code": "word = input('Enter a word: ')\nprint(word)", "exercise_id": ""},
            EXERCISES,
        )
        assert result["ok"] is False
        assert "input()" in result["stderr"]
        assert "timed out" not in result["stderr"].lower()


class TestOpenBlocking:
    def test_scan_blocks_open_bare(self):
        violations = scan_for_dangerous_code("f = open('secret.txt')")
        assert any("open()" in v for v in violations)

    def test_scan_blocks_open_with_read_mode(self):
        violations = scan_for_dangerous_code("open('secret.txt', 'r')")
        assert any("open()" in v for v in violations)

    def test_scan_blocks_open_with_write_mode(self):
        violations = scan_for_dangerous_code("open('out.txt', 'w')")
        assert any("open()" in v for v in violations)

    def test_run_blocks_open_read(self):
        result = run_user_code(
            {"code": "open('secret.txt', 'r')", "exercise_id": ""},
            EXERCISES,
        )
        assert result["ok"] is False
        assert "open()" in result["stderr"]

    def test_run_blocks_open_bare(self):
        result = run_user_code(
            {"code": "f = open('any_file')", "exercise_id": ""},
            EXERCISES,
        )
        assert result["ok"] is False
        assert "open()" in result["stderr"]


class TestInputBlocking:
    def test_scan_blocks_input(self):
        violations = scan_for_dangerous_code("word = input('Enter a word: ')")
        assert any("input()" in v for v in violations)


class TestSandboxBypassBlocking:
    def test_scan_blocks_builtins_name_access(self):
        violations = scan_for_dangerous_code("__builtins__['__import__']('os')")
        assert violations, "Expected violation for direct __builtins__ access"
        assert any("__builtins__" in v for v in violations)

    def test_run_blocks_builtins_subscript_import(self):
        result = run_user_code(
            {"code": "os = __builtins__['__import__']('os')\nos.system('echo bypass')\n", "exercise_id": ""},
            EXERCISES,
        )
        assert result["ok"] is False

    def test_scan_blocks_builtins_attribute_access(self):
        violations = scan_for_dangerous_code("__builtins__.__dict__['__import__']('os')")
        assert violations, "Expected violation for __builtins__.__dict__ access"

    def test_run_getattr_import_is_blocked(self):
        result = run_user_code(
            {"code": "f = getattr(__builtins__, '__import__')\nf('os')\n", "exercise_id": ""},
            EXERCISES,
        )
        assert result["ok"] is False
