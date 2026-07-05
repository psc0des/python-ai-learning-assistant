# Intermediate Python Patterns

Once you're comfortable writing functions and classes, three patterns show up everywhere in real Python code: decorators (like `@app.get` in FastAPI or `@tool` in LangChain), generators (lazy iteration with `yield`), and context managers (the `with` statement). Frameworks and libraries use all three constantly — and until now, this course has only used them, never taught them. This topic closes that gap.

Each pattern solves a different shape of problem: a decorator changes behavior *around* a function without touching its code; a generator produces values lazily, one at a time; a context manager guarantees setup and cleanup around a block of code, no matter how it exits.

## 1. Decorators — Wrapping a Function Without Rewriting It

A decorator is gift wrapping for a function — the function underneath doesn't change, but everything about how you receive and use it does. Technically, a decorator is just a function that takes a function and returns a (usually different) function.

`@loud` above `def greet(name):` is exactly the same as writing `greet = loud(greet)` right after the definition. The `@` syntax is convenient sugar for that reassignment — nothing more.

```python run
def loud(func):
    def wrapper(*args, **kwargs):
        print(f'Calling {func.__name__}')
        result = func(*args, **kwargs)
        print(f'{func.__name__} returned {result!r}')
        return result
    return wrapper

def add(a, b):
    return a + b

# Manually apply the decorator — this is exactly what @loud does:
add = loud(add)
print(add(2, 3))
```

In real code you almost never write it manually — you use `@` directly above the function it decorates:

```python run
def loud(func):
    def wrapper(*args, **kwargs):
        print(f'Calling {func.__name__}')
        return func(*args, **kwargs)
    return wrapper

@loud
def greet(name):
    return f'Hello, {name}!'

print(greet('Ada'))
```

**One catch:** the wrapper replaces the original function, so tools that inspect `func.__name__` or `func.__doc__` now see the wrapper's, not the original's. `functools.wraps(func)` fixes this by copying that metadata across — always use it in production decorators:

```python run
import time
import functools

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f'{func.__name__} took {elapsed:.6f}s')
        return result
    return wrapper

@timed
def add(a, b):
    return a + b

print(add(2, 3))
```

This is exactly the pattern you'll meet again later as `@app.get(...)` in FastAPI and `@tool` in LangChain — both are ordinary decorators wrapping your function with extra behavior (routing, tool registration) around it.

## 2. Decorators with Arguments — Building a Decorator Factory

Sometimes a decorator itself needs configuration — `@repeat(times=3)` or `@retry(attempts=5)`. That requires one more layer of nesting: a **decorator factory**, a function that takes your configuration arguments and returns the actual decorator.

Think of it as three nested boxes: the factory takes settings and hands back a decorator; the decorator takes your function and hands back a wrapper; the wrapper is what actually runs when your function is called.

```python run
import functools

def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator

@repeat(times=3)
def roll_die_face():
    return 6   # deterministic stand-in for a real random roll

print(roll_die_face())
```

A more realistic example — validating an argument before the real function ever runs, configured per use:

```python run
import functools

def validate_range(low, high):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(value):
            if not (low <= value <= high):
                raise ValueError(f'{value} is out of range [{low}, {high}]')
            return func(value)
        return wrapper
    return decorator

@validate_range(0, 100)
def set_volume(level):
    return f'Volume set to {level}'

print(set_volume(50))
try:
    set_volume(150)
except ValueError as exc:
    print(f'Rejected: {exc}')
```

**Common trap:** forgetting the extra nesting layer and writing `def repeat(times, func):` directly — that can't be used with `@repeat(times=3)` syntax at all, because `@` only ever passes the decorated function as the *single* argument to whatever the expression above it evaluates to.

## 3. Generators and yield — Lazy, One-at-a-Time Iteration

A generator is a vending machine, not a delivery truck: it hands you one item at a time, on request, instead of showing up with everything already loaded in memory. Any function containing `yield` is a **generator function** — calling it does not run its body at all. It immediately returns a generator object, and the body only runs up to the next `yield` each time you call `next()` on it (which is exactly what a `for` loop does under the hood).

```python run
def count_up_to(limit):
    n = 1
    while n <= limit:
        yield n
        n += 1

counter = count_up_to(5)
print(next(counter))
print(next(counter))

for remaining in counter:
    print(remaining)
```

Notice the `for` loop picks up exactly where the two `next()` calls left off — a generator remembers its own paused state between calls. Once it runs off the end of its code, it is **exhausted**: iterating it again produces nothing, you'd need to call the generator function again for a fresh one.

The real payoff is memory: a generator never holds a full sequence in memory at once.

```python run
def first_n_squares_list(n):
    return [i * i for i in range(n)]   # builds the whole list in memory immediately

def first_n_squares_gen(n):
    for i in range(n):
        yield i * i   # computes one value at a time, on demand

print(first_n_squares_list(5))
gen = first_n_squares_gen(5)
print(list(gen))
print(sum(first_n_squares_gen(1000)))   # never builds a 1000-item list in memory
```

That last line sums a thousand values without ever materializing a thousand-item list — `sum()` pulls one value at a time from the generator and discards it immediately. This is exactly how you'd stream a huge file or a paginated API response without running out of memory.

## 4. Custom Iterators — __iter__ and __next__

A generator function is the easy way to get an iterator. The full **iterator protocol** underneath it is just two dunder methods, and you can implement them yourself on any class: `__iter__(self)` (usually just `return self`) and `__next__(self)`, which returns the next value or raises `StopIteration` once there is nothing left.

```python run
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value

for number in Countdown(3):
    print(number)
```

A `for` loop is really just repeatedly calling `iter()` once and then `next()` until `StopIteration` is raised — you can do exactly that by hand:

```python run
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value

it = iter(Countdown(2))   # what 'for' does automatically
print(next(it))
print(next(it))
try:
    next(it)
except StopIteration:
    print('Exhausted — this is exactly what ends a for-loop')
```

**When to write a class instead of a generator function:** when the iterator needs extra public methods or state that outside code inspects (like `.current` or a `.reset()` method) — a plain generator function has no way to expose that. Otherwise, a generator function is almost always simpler.

## 5. Context Managers — with, __enter__/__exit__, and @contextmanager

A context manager is a chaperone for a block of code: it shows up before your code runs (`__enter__`), stays out of the way while you work, and always steps back in to clean up (`__exit__`) — even if your code raises an exception. That guarantee is exactly what `with` is for, and it's why `with open(...) as f:` always closes the file, no matter what happens inside the block.

This sandbox blocks real file access, but the same protocol applies to any resource that needs guaranteed cleanup — a database transaction is a perfect stand-in:

```python run
class Transaction:
    def __init__(self, name):
        self.name = name
        self.committed = False

    def __enter__(self):
        print(f'BEGIN {self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.committed = True
            print(f'COMMIT {self.name}')
        else:
            print(f'ROLLBACK {self.name} (due to {exc_type.__name__})')
        return False   # do not suppress the exception

with Transaction('update_balance') as txn:
    print('...doing work...')
print('committed:', txn.committed)

try:
    with Transaction('risky_update') as txn2:
        raise ValueError('insufficient funds')
except ValueError as exc:
    print(f'caught outside the with-block: {exc}')
```

**Returning `True` from `__exit__` suppresses the exception** — the caller never sees it. That's occasionally useful, but doing it by accident is a common bug that silently hides real errors, which is why the example above deliberately returns `False`.

Writing a full class is verbose for simple cases. `@contextlib.contextmanager` turns a generator function with exactly one `yield` into a context manager: code before `yield` becomes `__enter__`, the yielded value becomes the `as` target, and code after `yield` (in a `finally`) becomes `__exit__`.

```python run
import contextlib

@contextlib.contextmanager
def indent_log(label):
    print(f'-> entering {label}')
    try:
        yield label.upper()
    finally:
        print(f'<- leaving {label}')

with indent_log('setup') as tag:
    print(f'working inside {tag}')
```

## 6. Choosing the Right Pattern

All three patterns solve a different shape of problem, and real code often combines them:

- **Decorator** — you want to change or add behavior *around* a callable without touching its own code (logging, timing, validation, registration).
- **Generator** — you want to produce a sequence of values lazily, one at a time, especially when the sequence is large, unbounded, or expensive to fully build up front.
- **Context manager** — you want guaranteed setup/teardown around a block, regardless of whether it succeeds or raises.

They compose naturally — a decorator can wrap a function that's called inside a generator expression, all inside a context manager:

```python run
import contextlib
import functools

def logged(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'[log] calling {func.__name__}')
        return func(*args, **kwargs)
    return wrapper

@contextlib.contextmanager
def batch(label):
    print(f'[batch] start {label}')
    yield
    print(f'[batch] end {label}')

@logged
def double(n):
    return n * 2

with batch('demo'):
    for value in (double(x) for x in range(3)):
        print(value)
```

**Where you'll meet these again:** Flask and FastAPI register every route with a decorator (`@app.get('/users')`); LangChain registers callable tools with `@tool`; data pipelines and RAG chunking use generators to stream large inputs; and database sessions, HTTP clients, and test fixtures almost universally use context managers for guaranteed cleanup. Recognizing these three shapes is what makes that later code readable instead of magical.
