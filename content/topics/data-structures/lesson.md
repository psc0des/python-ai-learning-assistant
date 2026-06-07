# Lists, Dicts, Sets, Tuples

Every Python program needs to store collections of data — a list of names, a lookup table of prices, a set of unique visitors. Python gives you four built-in containers for this: lists (ordered, changeable), dictionaries (key-value lookup), sets (unique items only), and tuples (fixed, unchangeable records). Picking the right container for the job makes code shorter, faster, and much easier to understand.

Think of it like organising your kitchen. A list is like a numbered shelf — everything has a position, you can add or remove items, and order matters. A dictionary is like labelled jars — you look things up by name (the key), not by position. A set is like a guest list that automatically removes duplicates. A tuple is like a sealed package — the contents are fixed and cannot be changed. Choose the container based on how you need to access the data.

## 1. Lists — Ordered, Changeable Sequences

A list is the most versatile Python container. Think of it as a numbered queue — every item has a position (index), and you can add, remove, or replace items at any point.

Indexes start at **0**, not 1 — so the first item is at index `[0]`, the second at `[1]`, and so on. Negative indexes count from the end: `[-1]` is always the last item.

```python run

tasks = ['buy groceries', 'call dentist', 'pay bills']
tasks.append('walk dog')       # add to end
tasks.insert(0, 'wake up')     # insert at position 0
tasks.remove('call dentist')   # remove by value
print(tasks)
# ['wake up', 'buy groceries', 'pay bills', 'walk dog']
print(tasks[0])    # 'wake up'  — first item
print(tasks[-1])   # 'walk dog' — last item
print(tasks[1:3])  # ['buy groceries', 'pay bills'] — slice
```

```python

error_codes = []
for response in api_responses:
    if response['status'] >= 400:
        error_codes.append(response['status'])

error_codes.sort()        # sort in place
unique_errors = sorted(set(error_codes))  # deduplicate then sort
print(unique_errors)
```

**Key distinction:** methods like `sort()` and `reverse()` modify the list **in place** and return `None`. Functions like `sorted()` and `reversed()` return a **new** value and leave the original alone. Mixing these up is a very common mistake.

## 2. List Comprehensions — Concise Transforms

A list comprehension is a shorthand way to create a new list by transforming or filtering another list — all in one readable line. It replaces a multi-line `for` loop with a single expression.

The pattern is: `[expression for item in iterable if condition]`. The `if condition` part is optional.

```python run

names = ['alice', 'bob', 'carol']
upper_names = [name.upper() for name in names]
print(upper_names)  # ['ALICE', 'BOB', 'CAROL']

# Filter: keep only names longer than 3 characters
long_names = [name for name in names if len(name) > 3]
print(long_names)   # ['alice', 'carol']
```

```python run

scores = [72, 44, 91, 58, 88, 36]

passing = [
    {'score': s, 'grade': 'A' if s >= 90 else 'B'}
    for s in scores
    if s >= 60
]
print(passing)
# [{'score': 72, 'grade': 'B'}, {'score': 91, 'grade': 'A'}, {'score': 88, 'grade': 'B'}]
```

**Readability rule:** the `if` at the end of a comprehension is a *filter* (which items to include). The `if/else` inside the expression is a *transform* (how to label each item). They serve different purposes and can coexist. If you need a *second filter* condition or a nested loop, write a regular `for` loop instead — comprehensions only help when they fit on one readable line.

## 3. Tuples — Fixed Records

A tuple is like a list, but **immutable** — once you create it, you cannot add, remove, or replace items. Think of it like a coordinate pair on a map: (latitude, longitude). It always has exactly two values, and swapping them would mean something completely different.

Tuples are great for representing fixed-shape records: coordinates, RGB colours, database rows, function return values with multiple parts.

```python run

location = (51.5074, -0.1278)  # London, (latitude, longitude)
print(location[0])    # 51.5074 — latitude
print(location[1])    # -0.1278 — longitude

# Unpacking: assign tuple values to multiple variables at once
lat, lon = location
print(f'Lat: {lat}, Lon: {lon}')
```

```python run

def get_name_parts(full_name):
    parts = full_name.strip().split()
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ''
    return first, last   # Python packages this as a tuple

first, last = get_name_parts('Ada Byron Lovelace')
print(first, last)   # Ada Lovelace
```

Tuples can also be used as **dictionary keys** (unlike lists), because their immutability guarantees they will not change after being used as a key.

## 4. Sets — Unique Items and Fast Membership Checks

A set is a collection with **no duplicates** and **no guaranteed order**. Think of it like a bag you can only put unique marbles into — try to add a colour you already have and nothing happens.

Sets are optimised for two things: (1) checking whether an item exists (`in` operator is very fast), and (2) removing duplicates from a collection.

```python run

visited = {'London', 'Paris', 'Tokyo'}
visited.add('New York')
visited.add('Paris')    # already there — silently ignored
print(visited)          # order may vary, but no duplicates
print('Tokyo' in visited)   # True — instant check
print('Berlin' in visited)  # False
```

```python run

service_a_users = {'alice', 'bob', 'carol', 'dave'}
service_b_users = {'carol', 'dave', 'eve', 'frank'}

both_services = service_a_users & service_b_users   # intersection
only_a = service_a_users - service_b_users           # difference
all_users = service_a_users | service_b_users        # union

print('Both:', both_services)    # {'carol', 'dave'}
print('Only A:', only_a)         # {'alice', 'bob'}
print('Total:', len(all_users))  # 6
```

**Performance tip:** checking `item in my_set` is nearly instantaneous regardless of set size. Checking `item in my_list` slows down as the list grows. Use sets when membership checks are the primary operation.

## 5. Dictionaries — Key-Value Lookup

A dictionary maps **keys** to **values** — like a real dictionary where you look up a word (key) to find its definition (value). The key can be any immutable value (string, number, tuple), and the lookup is very fast regardless of how many entries there are.

```python run

grades = {
    'Alice': 88,
    'Bob': 72,
    'Carol': 95,
}
print(grades['Alice'])          # 88
grades['Dave'] = 61             # add a new entry
grades['Bob'] = 75              # update an existing entry
print(grades.get('Eve', 0))     # 0 — safe default when key missing

for name, score in grades.items():
    print(f'{name}: {score}')
```

```python run

log_levels = ['INFO', 'ERROR', 'INFO', 'WARNING', 'ERROR', 'ERROR']

counts = {}
for level in log_levels:
    counts[level] = counts.get(level, 0) + 1

print(counts)  # {'INFO': 2, 'ERROR': 3, 'WARNING': 1}
```

**Safe access rule:** use `dict.get(key, default)` instead of `dict[key]` when a key might not exist. Direct bracket access raises a `KeyError` if the key is missing; `.get()` returns your default value instead.

## 6. Looping Techniques — enumerate, zip, and Beyond

Python has several built-in tools that make loops cleaner and more expressive than a manual index counter.

**`enumerate`** gives you both the index and the item at the same time — no need for `range(len(...))`.

**`zip`** combines two or more lists element-by-element, stopping when the shortest runs out.

```python run
# enumerate: loop with position and value
fruits = ['apple', 'banana', 'cherry']
for i, fruit in enumerate(fruits, start=1):
    print(f'{i}. {fruit}')
# 1. apple  2. banana  3. cherry

# zip: pair up two lists
names = ['Alice', 'Bob', 'Carol']
scores = [88, 72, 95]
for name, score in zip(names, scores):
    print(f'{name} scored {score}')
```

```python run

def build_report(employee_ids, salaries):
    return [
        {'employee': eid, 'salary': sal, 'band': 'senior' if sal > 80000 else 'standard'}
        for eid, sal in zip(employee_ids, salaries)
    ]

report = build_report(['E-001', 'E-002', 'E-003'], [75000, 92000, 68000])
for row in report:
    print(row)
```

These tools make intent clear: `enumerate` says 'I need position', `zip` says 'I am pairing two sequences'. Code that uses them is easier to read than equivalent index-based loops.
