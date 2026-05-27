# Async Python

## 1. Coroutines and await

`async def` creates coroutine functions. Calling one returns a coroutine object that must be awaited or scheduled. `await` marks yield points where the coroutine pauses so the event loop can run other tasks.

## 2. Event Loop Scheduling Model

The event loop coordinates execution of asynchronous tasks. When a coroutine awaits I/O, control returns to the loop. This allows progress across many tasks in one thread while waiting operations complete.

## 3. Task Creation and gather

Use `asyncio.create_task` for fire-and-track task scheduling and `asyncio.gather` for awaiting multiple coroutines together. Structured orchestration avoids ad-hoc concurrency bugs and makes error behavior explicit.

## 4. Cancellation and Timeouts

Real systems need timeout and cancellation logic. Async tasks can be cancelled, and code should handle cancellation paths carefully to avoid partial state updates or hidden leaks.

## 5. Blocking Calls and Async Boundaries

Blocking calls inside async code paths pause the event loop for all tasks. Prefer async-capable clients and adapters, and isolate unavoidable blocking work away from latency-sensitive async flows.

## 6. Choosing Async vs Sync

Async is best for I/O-bound concurrency, not for heavy CPU workloads. Choose async when you need many overlapping waits. Choose sync when control flow is simple and throughput demands do not justify added complexity.
