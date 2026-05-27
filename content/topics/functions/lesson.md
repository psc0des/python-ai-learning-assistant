# Functions and Clean Code

Functions are how you stop writing the same code over and over. Instead of repeating the same ten lines every time you need to calculate a discount, you write it once as a function and call it wherever you need it. This topic goes deeper than just 'how to write a function' — you will learn how arguments flow in, how results flow out, how to set sensible defaults, and how to avoid sneaky bugs that trip up even experienced developers.

Think of a function like a vending machine. You put money in (arguments), select your item (the function name), the machine does its work inside (function body), and a snack comes out (return value). The machine does not care who is using it or why — it just takes input, does work, and produces output. Great functions work the same way: one clear job, predictable output, no hidden surprises.

## 1. Function Signatures and Basic Calls

A function signature is the promise your function makes to the world: 'give me these inputs and I will give you this output.' The name tells callers what the function does, and the parameter list tells them what they need to provide.

`def` creates the function, parentheses hold the parameter names, and the indented block is where the work happens. When you call the function, you provide arguments — the actual values that fill in those parameter slots.

```python

def greet(first_name, last_name):
    return f'Hello, {first_name} {last_name}!'

print(greet('Ada', 'Lovelace'))   # Hello, Ada Lovelace!
```

```python

def normalize_name(raw: str) -> str:
    """Strip whitespace and title-case a name."""
    return raw.strip().title()

print(normalize_name('  ada lovelace  '))  # Ada Lovelace
```

**Naming tip:** a good function name almost always contains a verb — `calculate_total`, `validate_email`, `load_config`. If you struggle to name it, the function might be doing too many things.

## 2. Default Arguments and the Mutable Default Trap

Default argument values let you make some parameters optional. Callers who do not provide that argument get the default value automatically — great for settings that have sensible common values.

```python

def order_pizza(topping, size='medium'):
    return f'Ordered: {size} pizza with {topping}'

print(order_pizza('mushrooms'))            # Ordered: medium pizza with mushrooms
print(order_pizza('peppers', 'large'))     # Ordered: large pizza with peppers
```

**The mutable default trap** is one of Python's most notorious beginner bugs. Default values are evaluated **once when the function is defined** — not every time it is called. So if you use a list or dict as a default, every call shares the same list object:

```python
# BUG — do NOT do this:
def add_item(item, cart=[]):
    cart.append(item)
    return cart

print(add_item('apple'))   # ['apple']
print(add_item('bread'))   # ['apple', 'bread']  <- the list leaked!

# CORRECT — use None as the sentinel:
def add_item_safe(item, cart=None):
    if cart is None:
        cart = []
    cart.append(item)
    return cart
```

This pattern (`if cart is None: cart = []`) is the standard fix used in every professional Python codebase.

## 3. Keyword Arguments and Readable Call Sites

When a function has several parameters, remembering the exact order can be hard and error-prone. Keyword arguments solve this by letting you name each argument at the call site, so the order does not matter.

```python
def book_flight(destination, date, seat_class='economy', window=False):
    return f'{seat_class} to {destination} on {date} (window={window})'

# Hard to read — what does True mean here?
book_flight('London', '2025-06-01', 'business', True)

# Much clearer with keyword arguments:
book_flight('London', date='2025-06-01', seat_class='business', window=True)
```

```python

def send_notification(user_id, message, channel='email', priority='normal'):
    return {'user': user_id, 'msg': message, 'via': channel, 'prio': priority}

# Caller can skip defaults they do not need:
result = send_notification('u-42', 'Your report is ready', priority='high')
print(result)
# {'user': 'u-42', 'msg': 'Your report is ready', 'via': 'email', 'prio': 'high'}
```

**Rule of thumb:** if a function call has three or more arguments and some are booleans or similar-looking values, use keyword arguments for all of them to make the intent obvious.

## 4. *args and **kwargs — Flexible Signatures

Sometimes you want a function that can accept any number of values — like a `sum()` that works on 2 numbers or 20. `*args` collects any extra positional arguments into a tuple. `**kwargs` collects any extra keyword arguments into a dictionary.

```python

def add_all(*numbers):
    return sum(numbers)

print(add_all(1, 2, 3))          # 6
print(add_all(10, 20, 30, 40))   # 100
```

```python

def log_and_call(func, *args, **kwargs):
    print(f'Calling {func.__name__} with args={args} kwargs={kwargs}')
    result = func(*args, **kwargs)
    print(f'Result: {result}')
    return result

def multiply(a, b):
    return a * b

log_and_call(multiply, 6, b=7)
# Calling multiply with args=(6,) kwargs={'b': 7}
# Result: 42
```

You will encounter `*args` and `**kwargs` constantly when reading library code. Even if you rarely write them yourself, understanding what they mean helps you read and use Python libraries confidently.

## 5. Return Values, Scope, and Side Effects

A function communicates its result through `return`. Without a `return` statement, Python returns `None` automatically — which is a frequent source of bugs when you forget to return something.

**Scope** means that variables created inside a function are local to that function. They do not exist outside it, and they do not interfere with variables of the same name elsewhere.

```python
# Scope example
x = 100  # outer variable

def compute():
    x = 42  # this is a DIFFERENT x, local to compute()
    return x

print(compute())  # 42
print(x)          # 100 — the outer x is unchanged
```

**Side effects** happen when a function changes something outside its own scope — modifying a list it received, writing to a file, or updating a global variable. Side effects are sometimes necessary but should be intentional and documented.

```python

# PURE — takes input, returns output, changes nothing else
def apply_discount(price, pct):
    return round(price * (1 - pct / 100), 2)

# SIDE EFFECT — modifies the list it receives
def apply_discounts_inplace(prices, pct):
    for i in range(len(prices)):
        prices[i] = round(prices[i] * (1 - pct / 100), 2)
```

Pure functions are easier to test, easier to reason about, and less likely to cause bugs. Prefer them when possible.

## 6. Docstrings and Type Hints — Self-Documenting Functions

A docstring is a short description written as the first line inside a function. It explains what the function does, what it expects, and what it returns. Type hints add type information to parameters and return values.

Neither replaces tests, but together they make your code much easier for others (and future-you) to use correctly.

```python
# Minimal docstring + type hints
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit."""
    return celsius * 9 / 5 + 32

print(celsius_to_fahrenheit(100))  # 212.0
```

```python

def summarize_scores(scores: list[int], passing: int = 60) -> dict:
    """
    Categorise a list of numeric scores.

    Args:
        scores:  List of integer scores.
        passing: Minimum score to pass (default 60).

    Returns:
        Dict with keys: total, passed_count, failed_count, pass_rate.
    """
    passed = [s for s in scores if s >= passing]
    return {
        'total': len(scores),
        'passed_count': len(passed),
        'failed_count': len(scores) - len(passed),
        'pass_rate': round(len(passed) / len(scores) * 100, 1) if scores else 0,
    }

print(summarize_scores([72, 44, 91, 58, 88]))
# {'total': 5, 'passed_count': 3, 'failed_count': 2, 'pass_rate': 60.0}
```

In professional codebases, type hints also enable static analysis tools (like mypy) to catch type errors before your code even runs.
