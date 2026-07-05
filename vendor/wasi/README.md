# Vendored WASI Python runtime

`python-3.12.0.wasm` is a prebuilt, WASI-target (`wasm32-wasi`) CPython 3.12.0
interpreter, used by `runner.py` as a **real** sandbox boundary for learner
code (see `CLAUDE.md`'s "Code runner" section for the full security
rationale). It is executed via the `wasmtime` Python package — no Node.js,
browser, or Emscripten/JS glue layer is involved; this is a standalone WASI
binary run directly through `wasmtime`'s embedding API.

## Provenance

- **Source:** [vmware-labs/webassembly-language-runtimes](https://github.com/vmware-labs/webassembly-language-runtimes), release tag `python/3.12.0+20231211-040d5a6`
- **Direct download:** `https://github.com/vmware-labs/webassembly-language-runtimes/releases/download/python%2F3.12.0%2B20231211-040d5a6/python-3.12.0.wasm`
- **SHA-256:** `e5dc5a398b07b54ea8fdb503bf68fb583d533f10ec3f930963e02b9505f7a763`
- **License:** Python Software Foundation License (same as upstream CPython); the `webassembly-language-runtimes` build scripts are Apache-2.0.
- **Size:** ~26 MB. This is a real, meaningful addition to repo size — it is the full CPython interpreter plus standard library compiled to a single WASM module. If a future CPython WASI release becomes available, replace this file and update the checksum above; do not keep multiple versions vendored.

## Why this file, not Pyodide

Pyodide targets `wasm32-unknown-emscripten` and expects a browser/JS host with
its own glue layer — it is the right choice for *client-side, in-browser*
execution, but this app's execution currently happens server-side (learner
code is POSTed to `/api/run`). A plain WASI build is the correct target for
*server-side* WASM sandboxing via `wasmtime`, with no browser or Node.js
dependency. Moving execution into the browser (a genuine Pyodide-in-a-
Web-Worker architecture) remains a valid, larger future direction — see the
note in `CLAUDE.md` — but was out of scope for this change.

## Known limitation: no `asyncio` event loop

This WASI Preview 1 build has no `socket` support (`OSError: Not supported`),
and `asyncio`'s event loop requires a self-pipe (`socket.socketpair()`) to
wake itself up — so any learner code that actually **runs** an asyncio event
loop (not just `import asyncio`) cannot execute inside this sandbox. `os`
also has no `system`/`fork`/`exec` capability at all (WASI has no process
model), which is a deliberate, structural security property, not a bug.
`runner.py` detects `asyncio` imports via AST and routes that code through
the existing hardened subprocess sandbox instead — see `CLAUDE.md`.
