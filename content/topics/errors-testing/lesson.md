# Errors, Debugging, and Testing

Every program encounters unexpected situations: a file that does not exist, a number where text was expected, a network connection that times out. Python uses exceptions to signal these problems, and how you handle them determines whether your program crashes helpfully or silently corrupts data.

Think of exceptions like a smoke alarm. When something goes wrong, Python sounds an alarm (raises an exception) with information about what happened and where. You can choose to handle the alarm for expected problems (try/except), set up cleanup actions that always run (finally), or let the alarm propagate upward so the caller deals with it. Tests are like fire drills — they practice the alarm scenarios repeatedly so you know your code behaves correctly before real users encounter it.

## 1. Reading Tracebacks — Python's Error Messages

A traceback is Python telling you exactly what went wrong and where. Most beginners see a traceback and panic — but it is actually a detailed roadmap to the bug.

**Reading strategy:** always start at the **bottom** of the traceback. The last line tells you the exception type and a description. Work your way up to find the first line of *your own code* that caused the problem.

```
Traceback (most recent call last):
  File "app.py", line 12, in process_order
    total = calculate_tax(price)          <- your code — start here
  File "app.py", line 5, in calculate_tax
    return amount * rate                  <- and follow up
TypeError: can't multiply sequence by non-int of type 'NoneType'
```

Reading this bottom-up: `TypeError` on `amount * rate` means `rate` is `None`. Go look at what is passed to `calculate_tax` on line 12.

```python
# Common exception types and what they mean
# NameError      — you used a variable that does not exist yet
# TypeError      — wrong type for an operation (str + int)
# ValueError     — right type but bad value (int('abc'))
# IndexError     — list index out of range
# KeyError       — dictionary key does not exist
# AttributeError — object does not have that attribute/method
```

**Habit to build:** before changing anything, read the full traceback and say out loud what you think it means. Guessing wastes time; understanding saves it.

## 2. Handling Exceptions — try, except, else

Some failures are predictable: a user types text when you expect a number, a file does not exist, a network call times out. For these, wrap the risky code in a `try` block and handle the failure in `except`.

**Critical rule:** catch specific exception types, not everything. Catching all exceptions hides bugs — you might swallow a programming error that should be fixed.

```python

def ask_for_age():
    raw = input('Enter your age: ')
    try:
        age = int(raw)         # this might raise ValueError
    except ValueError:
        print('Please enter a whole number.')
        return None
    return age
```

```python

import json
from pathlib import Path

def load_config(path):
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        raise FileNotFoundError(f'Config file not found: {path}')

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON in {path}: {exc}') from exc
```

**BAD — do not do this:**

```python
try:
    risky_operation()
except:            # catches EVERYTHING including KeyboardInterrupt!
    pass           # silently hides ALL errors — debugging nightmare
```

**GOOD — catch only what you expect:**

```python
try:
    risky_operation()
except (ValueError, KeyError) as exc:
    logger.warning('Expected failure: %s', exc)
```

## 3. Raising Exceptions with Clear Messages

When your code detects a problem — bad input, invalid state — you should raise an exception with a message that helps the caller understand exactly what went wrong and how to fix it.

Think of it like a form validation message: 'Password must be at least 8 characters' is useful; 'Error' is not.

```python

def set_age(age):
    if not isinstance(age, int):
        raise TypeError(f'Age must be an integer, got {type(age).__name__}')
    if age < 0 or age > 150:
        raise ValueError(f'Age {age} is not a realistic human age (0-150)')
    return age

set_age(25)      # fine
set_age(-5)      # ValueError: Age -5 is not a realistic human age (0-150)
set_age('old')   # TypeError: Age must be an integer, got str
```

```python

def process_order(order_data):
    if 'items' not in order_data:
        raise KeyError("Order must contain 'items' field")
    if not order_data['items']:
        raise ValueError('Order must have at least one item')
    total = sum(item['price'] for item in order_data['items'])
    if total <= 0:
        raise ValueError(f'Order total must be positive, got {total}')
    return {'total': total, 'item_count': len(order_data['items'])}
```

**Good error messages answer:** what went wrong, what the actual value was, and ideally what a valid value looks like.

## 4. Cleanup with finally and Context Managers

Some resources must always be cleaned up — even if an error occurs. Files need to be closed. Database connections need to be released. Network sockets need to be shut down. If an exception skips your cleanup code, you get **resource leaks**.

**`finally`** always runs, whether or not an exception occurred.
**`with`** (context managers) do cleanup automatically — this is the preferred approach for files and connections.

```python
# Without cleanup — the file stays open if an error occurs:
# f = open('data.txt')
# data = f.read()   # if this fails, f.close() is never called!
# f.close()

# With 'with' — file closes automatically, even on error:
with open('data.txt') as f:
    data = f.read()   # if this fails, file still closes
```

```python

class DatabaseConnection:
    def __enter__(self):
        print('Opening connection')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Closing connection')   # always runs
        return False   # do not suppress exceptions

    def query(self, sql):
        return f'Results for: {sql}'

with DatabaseConnection() as db:
    results = db.query('SELECT * FROM users')
    print(results)
# Opening connection
# Results for: SELECT * FROM users
# Closing connection  <- even if query raised an exception
```

Context managers are everywhere in professional Python: `open()`, database sessions, HTTP clients, locks. Learn to recognise and use the `with` pattern.

## 5. Writing Tests — Prevent Bugs from Coming Back

A test is a piece of code that checks whether your code does what you expect. Tests are valuable because they run automatically, catch regressions (old bugs that come back), and give you confidence to change code without fear.

The simplest tests use `assert` — if the condition is false, the test fails with an `AssertionError`.

```python

def apply_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# Tests
assert apply_discount(100, 10) == 90.0,   'Basic 10% discount'
assert apply_discount(50.00, 0) == 50.00, 'Zero discount unchanged'
assert apply_discount(10.00, 100) == 0.0, '100% discount is free'
print('All tests passed!')
```

```python

def safe_divide(a, b):
    if b == 0:
        return None
    return a / b

def test_safe_divide():
    assert safe_divide(10, 2) == 5.0      # normal case
    assert safe_divide(10, 0) is None      # division by zero
    assert safe_divide(0, 5) == 0.0       # zero numerator
    assert safe_divide(-6, 2) == -3.0     # negative numbers

test_safe_divide()
print('safe_divide tests passed!')
```

**What to test:** normal cases (happy path), boundary values (0, -1, empty string), invalid input, and known past bugs. A test suite that only tests the easy path is not much protection.

## 6. Debugging Systematically — A Repeatable Workflow

When something breaks, beginners tend to make random changes and hope one sticks. Professionals follow a repeatable process that finds bugs faster and without breaking other things.

**The debugging loop:**
1. **Reproduce** — find the simplest input that causes the bug
2. **Isolate** — narrow down to the exact line or function that fails
3. **Inspect** — print or examine the values at that point
4. **Hypothesise** — form a specific theory: 'I think X is None when it should be 5'
5. **Change one thing** — test your theory with a minimal fix
6. **Verify** — run tests again to confirm the fix and check nothing else broke

```python
# Debugging example: add print statements to inspect state
def process_orders(orders):
    results = []
    for i, order in enumerate(orders):
        print(f'[DEBUG] Processing order {i}: {order}')   # inspect
        try:
            total = order['quantity'] * order['price']
            print(f'[DEBUG] Total: {total}')               # inspect
            results.append({'id': order['id'], 'total': total})
        except (KeyError, TypeError) as exc:
            print(f'[DEBUG] Failed on order {i}: {exc}')  # diagnose
            results.append({'id': order.get('id'), 'error': str(exc)})
    return results
```

**Key discipline:** change **one thing at a time**. If you change three things and the bug disappears, you do not know which change fixed it — and you might have introduced new problems. The one-change rule makes debugging predictable.
