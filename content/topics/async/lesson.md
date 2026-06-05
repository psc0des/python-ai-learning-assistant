# Async Python

Imagine a single waiter serving 20 tables. If the waiter stood at one table waiting for the kitchen to finish a dish before walking to the next table, most customers would wait forever. Instead, a smart waiter takes an order, submits it to the kitchen, serves the next table while the kitchen works, and comes back when the dish is ready. Async Python works the same way — one process can juggle many waiting operations (network calls, database queries, file reads) by doing other work while waiting, instead of sitting idle.

Async Python is cooperative concurrency. Your code runs until it hits an `await` point — a place where it has to wait for something external. At that moment, control returns to the event loop, which can run other ready coroutines while the first one waits. When the awaited thing finishes, your coroutine resumes where it paused. This overlaps waiting time across many operations — it does NOT run things simultaneously in parallel, and it does NOT speed up CPU-heavy calculations.

## 1. async def and await — The Building Blocks

`async def` defines a **coroutine function**. Unlike a regular function that runs to completion when called, calling an async function just creates a coroutine object — it does not execute yet. You need to `await` it (or schedule it) to actually run it.

`await` is where a coroutine pauses and says 'I am waiting for something — event loop, feel free to run other tasks while I wait.'

```python run
import asyncio

# Regular function — runs immediately when called
def fetch_sync(name):
    print(f'Fetching {name}...')
    return f'data from {name}'

# Coroutine function — calling it returns a coroutine object, does not run
async def fetch_async(name):
    print(f'Fetching {name}...')
    await asyncio.sleep(1)   # simulate a 1-second network wait
    return f'data from {name}'

# To run a coroutine from normal (non-async) code, use asyncio.run():
async def main():
    result = await fetch_async('users-api')
    print(result)

asyncio.run(main())
```

**Key point:** if you call an async function without `await`, nothing happens — you just get a coroutine object sitting there. Python will even warn you: `RuntimeWarning: coroutine 'fetch_async' was never awaited`.

## 2. How the Event Loop Works

The event loop is the engine that runs async code. Think of it as an air traffic controller — it decides which plane (task) can use the runway (CPU) at each moment. When a task hits an `await`, it parks and waits. The event loop immediately picks up another task that is ready to run.

```python run
import asyncio

async def task(name, delay):
    print(f'{name} started')
    await asyncio.sleep(delay)   # 'park' for 'delay' seconds
    print(f'{name} finished after {delay}s')
    return name

async def main():
    # Run tasks ONE AT A TIME (sequential) — total time ~3 seconds:
    await task('A', 1)
    await task('B', 2)

asyncio.run(main())
# A started → A finished → B started → B finished  (3 seconds total)
```

Compare that with running them concurrently:

```python
async def main_concurrent():
    # Run tasks CONCURRENTLY — total time ~2 seconds (the longest one):
    results = await asyncio.gather(
        task('A', 1),
        task('B', 2),
    )
    print(results)   # ['A', 'B']

asyncio.run(main_concurrent())
# A started → B started → A finished (1s) → B finished (2s)  — only 2s total!
```

The savings come from overlapping the waiting time. Both tasks are 'in flight' simultaneously — the event loop interleaves them.

## 3. Running Tasks Concurrently — gather and create_task

`asyncio.gather()` is the most common way to run multiple coroutines concurrently and wait for all of them to finish. It is perfect when you need results from several independent operations before moving on.

`asyncio.create_task()` schedules a coroutine to run in the background immediately, so it can run while your current coroutine keeps going.

```python
import asyncio

async def fetch_user(user_id):
    await asyncio.sleep(0.5)   # simulated DB query
    return {'id': user_id, 'name': f'User {user_id}'}

async def fetch_orders(user_id):
    await asyncio.sleep(0.8)   # simulated API call
    return [f'Order-{user_id}-1', f'Order-{user_id}-2']

# gather: run both at the same time, wait for both
async def get_user_dashboard(user_id):
    user, orders = await asyncio.gather(
        fetch_user(user_id),
        fetch_orders(user_id),
    )
    return {'user': user, 'orders': orders}

result = asyncio.run(get_user_dashboard(42))
print(result)
# Takes ~0.8s (the longer one), not 1.3s (sequential sum)
```

```python
# create_task: fire and continue — check result later
async def background_work():
    task = asyncio.create_task(fetch_user(99))  # starts immediately
    # ... do other work here ...
    user = await task   # wait for it when you need the result
    return user
```

## 4. Timeouts and Cancellation

In real applications, external services can hang — a slow database, an unresponsive API, a dropped network connection. Without timeouts, your async code can wait forever.

`asyncio.wait_for()` wraps a coroutine with a timeout. If the coroutine does not finish in time, it raises `asyncio.TimeoutError`.

```python run
import asyncio

async def slow_api_call():
    await asyncio.sleep(10)   # simulates a very slow response
    return 'result'

async def main():
    try:
        # Only wait 2 seconds — then give up
        result = await asyncio.wait_for(slow_api_call(), timeout=2.0)
        print(result)
    except asyncio.TimeoutError:
        print('API call timed out — using cached data instead')
        result = 'cached_fallback'
    return result

asyncio.run(main())
# API call timed out — using cached data instead
```

**Task cancellation** happens when you explicitly stop a running task:

```python
async def main():
    task = asyncio.create_task(slow_api_call())
    await asyncio.sleep(1)
    task.cancel()           # request cancellation
    try:
        await task
    except asyncio.CancelledError:
        print('Task was cancelled')   # handle the cancellation
```

Always handle `CancelledError` — if you catch it but do not re-raise, you may leave resources in a dirty state.

## 5. The Blocking Trap — What Breaks Async

The biggest mistake beginners make with async code is calling **blocking (synchronous) functions** inside an async function. When a blocking call runs, it freezes the entire event loop — all other tasks stop until it finishes. This completely defeats the purpose of async.

```python
import asyncio
import time

async def bad_example():
    print('Starting...')
    time.sleep(3)   # BLOCKS THE ENTIRE EVENT LOOP for 3 seconds!
    print('Done')

async def good_example():
    print('Starting...')
    await asyncio.sleep(3)   # yields control — other tasks can run
    print('Done')
```

**Common blocking calls to avoid in async code:**
- `time.sleep()` → use `asyncio.sleep()` instead
- `requests.get()` → use `httpx` or `aiohttp` (async HTTP clients)
- Regular file I/O → use `aiofiles` or run in a thread pool
- Synchronous DB drivers → use async DB libraries (asyncpg, motor, etc.)

```python
# Professional pattern: run blocking code in a thread pool
import asyncio
import time

def slow_file_read(path):
    time.sleep(2)   # blocking file operation
    return 'file contents'

async def main():
    # Run blocking function without freezing the event loop:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, slow_file_read, 'data.txt')
    print(result)
```

## 6. When to Use Async — and When Not To

Async is a powerful tool, but it adds complexity. Use it deliberately, not by default.

**Use async when:**
- Your code makes many network requests, database queries, or file reads that have significant wait times
- You need to handle many simultaneous connections or users
- You are building APIs or web services where latency matters

**Do NOT use async when:**
- Your work is CPU-heavy (image processing, number crunching, ML inference) — async does not help; use multiprocessing instead
- Your flow is simple and sequential — async adds mental overhead for no benefit
- You only make one external call at a time — sequential awaits are just slower sync code with extra syntax

```python
# WRONG use of async — no concurrent I/O, just added complexity:
async def process_report():    # pointless async here
    data = load_from_disk()    # blocking call — but only one, no benefit
    summary = summarize(data)  # CPU work — async does not help
    return summary

# RIGHT use of async — multiple concurrent I/O operations:
async def build_dashboard(user_id):
    metrics, alerts, profile = await asyncio.gather(
        fetch_metrics(user_id),   # network call 1
        fetch_alerts(user_id),    # network call 2
        fetch_profile(user_id),   # network call 3
    )
    return {'metrics': metrics, 'alerts': alerts, 'profile': profile}
    # ~3x faster than doing these three calls sequentially
```

**In FastAPI and other async frameworks**, you often write `async def` route handlers even when you only await one thing — that is fine because the framework's event loop still benefits from the cooperative yield points.
