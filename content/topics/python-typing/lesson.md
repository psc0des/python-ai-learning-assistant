# Python Typing in Depth

Basic type hints only scratch the surface. Real intermediate and professional Python code uses Optional/Union to model values that might be absent or one of several types, TypeVar/Generic to type containers and functions generically, Protocol for structural typing without inheritance, and TypedDict for dict shapes.

The single most important fact in this whole topic: none of it is enforced by Python itself. Every tool here is a blueprint for a separate static checker (mypy, pyright) to verify — Python the language runs your code exactly the same whether the hints are right, wrong, or absent entirely.

## 1. Why Type Hints — Documentation, Not Enforcement

Type hints like `def add(a: int, b: int) -> int:` describe what a function *expects* and *returns* — for readers, IDEs, and static checkers like mypy. Python itself does **not** enforce them at runtime; they are documentation with tooling superpowers, not a guarantee.

```python run
def add(a: int, b: int) -> int:
    return a + b

print(add(2, 3))
print(add('x', 'y'))   # Python does NOT stop this -- hints are not enforced at runtime
```

Both calls run without error — `add('x', 'y')` even "succeeds" because `+` happens to work on strings too, just not in the way the hint promised. A static type checker (mypy, pyright) would flag the second call as an error *before* you ever run the code; Python the language will not.

## 2. Optional and Union — Modeling 'Might Not Have a Value'

`Optional[str]` means "a `str`, or `None`" — it is shorthand for `Union[str, None]`. `Union[int, float, str]` means the value could be any one of those types.

```python run
from typing import Optional, Union

def find_user(user_id: int, users: dict) -> Optional[str]:
    return users.get(user_id)

def normalize(value: Union[int, float, str]) -> str:
    return str(value)

users = {1: 'Ada', 2: 'Grace'}
print(find_user(1, users))
print(find_user(99, users))
print(normalize(42))
print(normalize(3.14))
```

Python 3.10 introduced a shorter syntax using `|`: `int | str` instead of `Union[int, str]`, and `int | None` instead of `Optional[int]`.

```python run
def describe(value: int | str | None) -> str:
    if value is None:
        return 'nothing'
    return f'{type(value).__name__}: {value}'

print(describe(5))
print(describe('hi'))
print(describe(None))
```

**Common trap:** returning `Optional[str]` from a function and then forgetting to handle the `None` case at the call site — the annotation is a promise the *caller* must also respect, which is exactly what a static checker verifies for you.

## 3. Generics — TypeVar and Generic Containers

A plain `list` hint says "a list of something," but doesn't say what. `TypeVar` lets you link an input type to an output type — "whatever type goes in a list of T, a T comes back out."

```python run
from typing import TypeVar, List

T = TypeVar('T')

def first(items: List[T]) -> T:
    return items[0]

print(first([1, 2, 3]))
print(first(['a', 'b']))
```

A type checker uses this to verify that `first([1, 2, 3])` is known to return an `int`, and `first(['a', 'b'])` a `str` — without you writing two separate functions. `Generic[T]` extends the same idea to classes, so a container class can be typed for whatever it holds.

```python run
from typing import Generic, TypeVar

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self):
        self.items: list[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

s: Stack[int] = Stack()
s.push(1)
s.push(2)
print(s.pop())
print(s.pop())
```

`Stack[int]` tells a checker this particular stack only ever holds `int`s — pushing a string onto it would be a static type error, even though nothing stops it at runtime.

## 4. Protocol — Structural Typing Made Explicit

Python has always supported "duck typing" — if an object has the right methods, it works, regardless of its class hierarchy. `Protocol` lets you describe that shape explicitly, so a type checker can verify it *without requiring inheritance*.

```python run
from typing import Protocol

class Named(Protocol):
    name: str

    def greet(self) -> str:
        ...

class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f'Hello, I am {self.name}'

def introduce(entity: Named) -> str:
    return entity.greet()

print(introduce(Person('Ada')))
```

`Person` never inherits from `Named` — it just happens to have a `.name` attribute and a `.greet()` method, which is all `introduce()` actually needs. This is **structural typing**: 'if it looks like a duck and quacks like a duck, it satisfies the Duck protocol' — a checker verifies the shape matches, not the class ancestry.

## 5. TypedDict — Typing Dictionary Shapes

Plain `dict` hints (like `dict[str, int]`) describe uniform key/value types, but many dicts in real code have a *fixed, specific* shape — `{'title': ..., 'year': ...}`, always those two keys. `TypedDict` documents exactly that shape.

```python run
from typing import TypedDict

class Movie(TypedDict):
    title: str
    year: int

def summarize(movie: Movie) -> str:
    return f"{movie['title']} ({movie['year']})"

m: Movie = {'title': 'Arrival', 'year': 2016}
print(summarize(m))
```

**Common trap:** a `TypedDict` is still just a regular `dict` at runtime — it adds no validation of its own. Nothing stops you from constructing one with a missing key; only a static checker catches it.

```python run
from typing import TypedDict

class Movie(TypedDict):
    title: str
    year: int

bad_movie = {'title': 'Oops'}   # missing 'year' -- but this is just a dict, so it's allowed
print(bad_movie)
print(type(bad_movie).__name__)
```

If you need the missing-key case to be an actual runtime error, a `dataclass` (which has a real `__init__` requiring its declared fields) is a better fit than `TypedDict`.

## 6. Static Checking in Practice — mypy and the Limits of Type Hints

Everything in this topic — `Optional`, `Union`, `TypeVar`, `Protocol`, `TypedDict` — is inert at runtime. The tool that actually *enforces* these promises is a separate static type checker, most commonly `mypy`, run as its own step (`mypy your_file.py`), not by the Python interpreter.

This means Python's typing is **gradual and optional** by design: you can add hints to one function at a time, run mypy in CI to catch mismatches before they reach production, and still run completely unhinted code right alongside fully-typed code. `Any` is the deliberate escape hatch — a value typed `Any` opts out of checking entirely, useful for gradually typing an untyped codebase but easy to overuse as a way of silencing the checker instead of fixing the actual type mismatch.

**The honest scope of Python's type system:** it improves documentation, catches real bugs *before* runtime when checked by a separate tool, and helps IDEs autocomplete and refactor correctly — but it adds **zero enforcement on its own**. A function annotated `-> int` can still return a string at runtime, and Python will happily let it. Treat type hints as a contract you and your tooling agree to honor, not a guarantee the language backs up.
