# Standard Library Fluency

Python's standard library ships with tools that replace common hand-rolled patterns: counting, grouping, combining and slicing sequences, memoizing, and building structured records without boilerplate. This topic builds fluency with the tools you will see everywhere in intermediate and professional Python code — including in this very app's own source.

Each tool matches a specific shape of problem. Learning to recognize that shape — "I am counting things", "I am grouping things", "I am memoizing a slow call" — is what turns a working loop into idiomatic, readable Python.

## 1. itertools — Combining and Slicing Iterables Without Loops

`itertools` is a toolbox of small, fast building blocks for working with sequences and iterators without writing manual loops. Two of the most useful: `chain`, which lazily strings several iterables together into one, and `islice`, which takes a slice of an iterator without consuming the whole thing first.

```python run
import itertools

a = [1, 2, 3]
b = [4, 5, 6]
combined = list(itertools.chain(a, b))
print(combined)

first_three = list(itertools.islice(range(100), 3))
print(first_three)
```

`itertools.groupby` groups **consecutive** items that share a key — it does not scan ahead to collect every match, so you must sort the input by that key first, or you'll silently get multiple small groups instead of one group per key.

```python run
import itertools

people = [
    {'name': 'Ada', 'dept': 'Eng'},
    {'name': 'Grace', 'dept': 'Eng'},
    {'name': 'Alan', 'dept': 'Math'},
]
people_sorted = sorted(people, key=lambda p: p['dept'])
for dept, group in itertools.groupby(people_sorted, key=lambda p: p['dept']):
    names = [p['name'] for p in group]
    print(dept, names)
```

**Common trap:** forgetting to sort before `groupby` — if the Math entry came *between* the two Eng entries in the original list, you'd get three separate one-item groups instead of two.

## 2. collections — Counter, defaultdict, and namedtuple

`collections.Counter` is a dict built for counting: hand it any iterable and it tallies how many times each item appears, with a `most_common()` method for ranking the results.

```python run
from collections import Counter

votes = ['red', 'blue', 'red', 'green', 'blue', 'red']
tally = Counter(votes)
print(tally)
print(tally.most_common(2))
```

`collections.defaultdict` removes the need to check whether a key already exists before appending to it — it calls a factory function (like `list` or `int`) to create a default value the first time a key is touched. `collections.namedtuple` gives you a lightweight, immutable record with named fields — cheaper than a class when you just need a labeled tuple.

```python run
from collections import defaultdict, namedtuple

groups = defaultdict(list)
for word in ['apple', 'banana', 'avocado', 'blueberry']:
    groups[word[0]].append(word)
print(dict(groups))

Point = namedtuple('Point', ['x', 'y'])
p = Point(3, 4)
print(p.x, p.y)
print(p)
```

Without `defaultdict`, the grouping loop above would need `if word[0] not in groups: groups[word[0]] = []` before every append — `defaultdict` makes that check disappear entirely.

## 3. functools — reduce, lru_cache, and partial

`functools.reduce` collapses a sequence into a single value by repeatedly applying a two-argument function, carrying an accumulator forward. `functools.partial` pre-fills some of a function's arguments, returning a new callable that only needs the rest.

```python run
import functools

total = functools.reduce(lambda acc, x: acc + x, [1, 2, 3, 4], 0)
print(total)

def power(base, exponent):
    return base ** exponent

square = functools.partial(power, exponent=2)
print(square(5))
```

`functools.lru_cache` memoizes a function's results, keyed by its arguments — calling it again with the same arguments returns the cached value instead of recomputing it.

```python run
import functools

calls = []

@functools.lru_cache(maxsize=None)
def slow_square(n):
    calls.append(n)
    return n * n

print(slow_square(4))
print(slow_square(4))
print(slow_square(5))
print('actual calls made:', calls)
```

Notice `calls` only ever records `[4, 5]`, even though `slow_square(4)` was called twice — the second call was served entirely from the cache. **Common trap:** an unbounded `lru_cache` (`maxsize=None`) on a function called with many distinct arguments over a long-running process can grow memory usage indefinitely — set a real `maxsize` outside of small scripts.

## 4. dataclasses — Structured Data Without Boilerplate

Before dataclasses, a simple data-holding class meant hand-writing `__init__`, `__repr__`, and `__eq__` yourself. `@dataclass` generates all three from your field declarations.

```python run
from dataclasses import dataclass, field

@dataclass
class Product:
    name: str
    price: float
    tags: list = field(default_factory=list)

p1 = Product('Widget', 9.99)
p2 = Product('Gadget', 19.99, tags=['new'])
print(p1)
print(p2)
print(p1 == Product('Widget', 9.99))
```

**Common trap:** writing `tags: list = []` instead of `field(default_factory=list)`. A plain `= []` default is the exact same mutable-default-argument bug from function parameters — every instance that doesn't pass its own `tags` would share **one** list object. `default_factory` calls `list()` fresh for each new instance instead.

`__post_init__` runs automatically right after the generated `__init__` assigns all the declared fields — the right place to compute a derived value from them.

```python run
from dataclasses import dataclass

@dataclass
class Rectangle:
    width: float
    height: float
    area: float = 0.0

    def __post_init__(self):
        self.area = self.width * self.height

r = Rectangle(3, 4)
print(r)
print(r.area)
```

Note that type annotations like `width: float` are hints, not runtime enforcement — passing `3` (an int) works fine and Python will not convert or reject it; a type checker like mypy is what catches a mismatch, not the dataclass itself.

## 5. Chaining It Together — A Real Data-Processing Pipeline

These tools are most valuable combined. A small log-analysis pipeline: a list of structured log records (as dataclasses), tallied by level and filtered by message with `Counter`.

```python run
from collections import Counter
from dataclasses import dataclass

@dataclass
class LogEntry:
    level: str
    message: str

logs = [
    LogEntry('INFO', 'started'),
    LogEntry('ERROR', 'failed to connect'),
    LogEntry('INFO', 'retrying'),
    LogEntry('ERROR', 'timeout'),
    LogEntry('ERROR', 'timeout'),
]

level_counts = Counter(log.level for log in logs)
print(level_counts)

message_counts = Counter(log.message for log in logs if log.level == 'ERROR')
print(message_counts.most_common(1))
```

Notice `Counter` accepts any iterable directly — including a generator expression filtering `logs` in place — so no intermediate list is ever built just to count things. This is the same shape as a real monitoring dashboard: structured records in, aggregated counts out, using three or four stdlib tools instead of a hand-rolled nested-loop-and-dict implementation.

## 6. When to Reach for the Standard Library vs. Writing It Yourself

These tools are popular because they are fast, well-tested, and communicate intent clearly to another reader — `Counter(items)` says "I am counting things" more clearly than a manual `for`/`if`/`+= 1` loop does. But reaching for them without understanding their exact behavior causes real bugs:

- **`groupby` without sorting first** silently produces multiple small groups instead of one full group per key — one of the most common stdlib-related bugs in real code.
- **An unbounded `lru_cache`** on a function called with many distinct arguments over a long-running process (like this app's own server) can grow memory usage indefinitely.
- **A mutable `default_factory`-free default** on a dataclass field (or a function argument) shares one object across every instance — surprising and hard to trace back to its source.

**Reach for the standard library when:** the exact tool matches your problem shape (counting → `Counter`, grouping → `groupby` or `defaultdict`, memoizing → `lru_cache`, structured records → `dataclass`) and you understand its edge cases. **Write your own loop when:** the stdlib tool's specific behavior would be less clear or more error-prone than 3-4 lines of plain, obvious code — clarity for the next reader (including future you) always outranks looking clever.
