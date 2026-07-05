# Security Policy

## Supported Use

Python Skill Lab is a local, single-user learning tool. It binds to
`127.0.0.1` by default and runs learner code on the same machine as the person
using the app.

Most learner code executes inside a real WASM/WASI sandbox (`wasmtime` plus a
vendored WASI CPython build) with no filesystem, network, or process-spawn
access from inside it — this is a genuine isolation boundary, not just
pattern-matching. One narrow exception: code that imports `asyncio` falls back
to a subprocess sandbox instead, since WASI has no socket support (which
asyncio's event loop requires) — that fallback is defense-in-depth only (an
AST safety scan, restricted runtime builtins), not a hard guarantee. The app
also includes origin checks and request limits at the HTTP layer. See
`CLAUDE.md`'s "Code runner" section for the full model.

Do not expose this app to a public network, shared server, classroom server, or
multi-user environment without a separate security review and real isolation
boundary.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately through GitHub Security
Advisories for this repository. If advisories are unavailable, open a minimal
public issue asking for a private contact path without disclosing exploit
details.

When reporting, include:

- The affected file, endpoint, or feature.
- Steps to reproduce.
- The expected and actual behavior.
- Any relevant logs or screenshots with secrets removed.

Please do not publish proof-of-concept exploit details before the maintainer has
had time to investigate.

## Out of Scope

The following are known properties of the local learning model, not security
vulnerabilities by themselves:

- A local user can run arbitrary code in their own terminal outside the app.
- The learner-code runner is not intended for hostile third-party code.
- API keys entered into the browser session are the user's responsibility and
  should not be shared or committed.
