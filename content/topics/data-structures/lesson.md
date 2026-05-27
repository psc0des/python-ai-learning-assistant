# Lists, Dicts, Sets, Tuples

## 1. Lists and Common List Methods

Lists are ordered and mutable. Use them when item order matters or when you need to append, remove, or reorder values. Learn the most common methods first: append, extend, insert, remove, pop, clear, index, count, sort, reverse, and copy. Also learn which methods mutate the list versus return new values.

## 2. List Comprehensions and Nested Comprehensions

List comprehensions let you transform or filter data in one readable expression. They are great for simple conversions, but readability still matters. Keep each comprehension short and explicit. For complex logic, write a normal loop with clear names.

## 3. Tuples, Sequence Packing, and Unpacking

Tuples are immutable sequences and often represent fixed-shape records. Python also supports packing and unpacking, which makes multiple assignments and returning grouped values clean. Use tuples when data should be stable and self-contained.

## 4. Sets for Uniqueness and Membership

Sets are built for uniqueness and fast membership tests. They also support math-like operations such as union, intersection, difference, and symmetric difference. When duplicate removal or membership checks dominate your logic, sets are usually the cleanest choice.

## 5. Dictionaries for Keyed Data

Dictionaries map keys to values and are the default structure for structured records, counters, and grouped data. Learn key access, updates, safe reads with get, and iteration through keys, values, and key-value pairs. Dict comprehensions help for predictable transforms.

## 6. Looping Techniques and Comparison Behavior

Python provides readable looping tools like enumerate, zip, sorted, and reversed. You should know when each helps clarity. You should also understand sequence comparison behavior, because comparing lists or tuples can be useful but surprising when types or order differ.
