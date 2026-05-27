# SQL, HTTP, Git, and Linux Basics

This module combines four practical foundations because real debugging rarely stays inside one tool. Production issues often require switching quickly between HTTP behavior, SQL state, Git history, and Linux runtime inspection.

## 1) HTTP Behavior

Know request intent (method), response meaning (status code), and payload expectations (headers/body). Misreading HTTP outcomes leads to wrong fixes.

## 2) SQL State Verification

Use SQL to verify facts directly in data storage. Query before changing data. Prefer explicit WHERE filters and sanity checks before updates/deletes.

## 3) Git Traceability

Use `git status` and `git diff` to inspect local changes, then commit in focused units. Git history should tell the story of behavior changes clearly.

## 4) Linux Runtime Inspection

Command-line basics help you inspect logs, files, and running processes quickly. Always confirm current directory and target environment before running commands.

## 5) Cross-Layer Investigation Pattern

A robust investigation sequence is:
1. Reproduce request/response behavior.
2. Inspect logs around failure time.
3. Verify SQL state.
4. Review recent Git changes.
5. Validate fix with the same evidence path.

## 6) Safety Habits

Small discipline prevents big mistakes: no unfiltered SQL writes, no secret commits, no blind command execution, and no assumptions without evidence.

## Real-World Implementation Pattern

Strong engineers build a habit loop:
- Gather evidence from all layers.
- Form one hypothesis at a time.
- Verify quickly.
- Commit minimal, reversible fixes.
