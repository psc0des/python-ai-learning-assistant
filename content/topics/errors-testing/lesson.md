# Errors, Debugging, and Testing

## 1. Reading Tracebacks Effectively

Tracebacks list call frames leading to failure. Start at the exception type and message, then locate the first line in your own code. This habit helps you avoid random changes and move directly to root-cause analysis.

## 2. Handling Expected Exceptions

Use try/except for failures you expect and can recover from. Catch specific exception classes, not everything. This keeps normal failure paths safe while preserving visibility for unexpected bugs.

## 3. Raising Exceptions with Clear Messages

When input or state violates a function contract, raise an appropriate exception with a useful message. Good error messages shorten debugging time and improve API behavior for callers.

## 4. Cleanup Paths: finally and Context Managers

Some resources must be cleaned up even when errors happen. Use finally blocks or context managers (`with`) to ensure cleanup runs consistently. This prevents hidden leaks and inconsistent state.

## 5. Assertions and Test Structure

Assertions encode expected behavior. A useful test suite includes normal cases, edge cases, invalid input, and boundary values. Prefer deterministic tests with clear failure messages over ad-hoc prints.

## 6. Debugging Workflow You Can Repeat

A reliable debugging loop is: reproduce the bug, narrow input, inspect state, form a hypothesis, apply one change, rerun tests, and confirm outcome. This process scales better than random edits under pressure.
