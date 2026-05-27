# Python Basics

Python basics are execution basics. If you understand how Python evaluates values, binds names, chooses branches, repeats loops, and returns function output, everything else in backend and AI programming becomes easier.

## 1. Why Python and How to Approach This Tutorial

Think of learning to cook. You could read every cookbook in the library, or you could just make a simple omelette today. Python rewards the same hands-on approach — the fastest way to learn is to type code and see what happens immediately.

Python is popular because it reads almost like plain English, runs on any platform without complex setup, and has a huge library of ready-made tools. Companies use it for web APIs, automation scripts, data analysis, and AI — all built on the same basics you are about to learn.

The best way to work through this topic is to keep Python open and try every example yourself. When something surprises you, that surprise is the lesson.

```python
# This is a comment — Python ignores it.
# Try typing these lines in a Python shell:
print('Hello, world!')   # prints text
2 + 3                     # evaluates to 5
type(42)                  # tells you what kind of value this is
```

**Key habit to build:** after reading each concept, type a small variation yourself. Do not just read — run it.

## 2. Numbers, Operators, and Variables

Think of a variable like a sticky note. You write a name on the sticky note and stick it to a value so you can find it later. In Python, `=` is how you attach a name to a value — it is not the same as the equals sign in maths.

Arithmetic mostly works as you expect, but a few details trip up beginners:

- `/` always gives a decimal (float): `7 / 2` gives `3.5`, not `3`
- `//` does floor division (rounds down): `7 // 2` gives `3`
- `%` gives the remainder: `7 % 2` gives `1`
- `**` is the power operator: `2 ** 8` gives `256`

```python

guests = 4
total_bill = 87.50
per_person = total_bill / guests
print(per_person)   # 21.875
```

```python

def calculate_order_total(unit_price, quantity, tax_rate=0.08):
    subtotal = unit_price * quantity
    tax = round(subtotal * tax_rate, 2)
    return subtotal + tax

print(calculate_order_total(19.99, 3))  # 64.77
```

**Common trap:** reading a variable before you have assigned it causes a `NameError`. Always assign before you use.

## 3. Strings: Working with Text

A string is just a sequence of characters — letters, spaces, punctuation, or anything you can type. Think of it like a word in a crossword puzzle: each letter has a numbered position starting from 0.

You can read individual characters with square brackets (`name[0]`), or grab a slice of characters (`name[0:3]`). One important rule: **strings are immutable**, meaning once you create a string you cannot change individual letters inside it — you have to build a new string.

```python

full_name = 'Ada Lovelace'
print(full_name[0])       # 'A' — first character
print(full_name[4:12])    # 'Lovelace' — slice
print(full_name.upper())  # 'ADA LOVELACE'
print(len(full_name))     # 12 — number of characters
```

```python

def normalize_email(raw_email):
    cleaned = raw_email.strip().lower()
    if '@' not in cleaned:
        return None
    username, domain = cleaned.split('@', 1)
    return f'{username}@{domain}'

print(normalize_email('  Alice@Example.COM  '))  # alice@example.com
```

**f-strings** (f'Hello {name}') are the modern way to insert variable values into text — much cleaner than joining strings together with `+`.

## 4. Lists: Storing Collections of Things

A list is like a numbered shopping trolley. You can put things in, take things out, change what is in each slot, and the order is always preserved.

Unlike strings, lists are **mutable** — you can modify them in place by adding items (`append`), removing items (`remove`), or replacing items by position.

```python

shopping = ['apples', 'bread', 'milk']
shopping.append('eggs')          # add to the end
shopping[1] = 'sourdough'        # replace 'bread'
shopping.remove('milk')          # remove by value
print(shopping)                  # ['apples', 'sourdough', 'eggs']
print(len(shopping))             # 3 — how many items
print(shopping[0])               # 'apples' — first item
```

```python

def get_passing_scores(scores, cutoff=60):
    return [s for s in scores if s >= cutoff]

results = get_passing_scores([72, 44, 91, 58, 88])
print(results)  # [72, 91, 88]
```

**Important:** if you pass a list into a function and the function modifies it, the original list changes too — because lists are mutable objects, not copies.

## 5. Control Flow: Making Decisions and Repeating Work

Control flow is how your program decides what to do next. `if`, `elif`, and `else` give your Python code decision-making ability. `for` loops repeat a block of code for each item in a sequence. `range(n)` produces the numbers 0, 1, 2, ... n-1 (note: it stops **before** n).

```python

score = 75

if score >= 90:
    grade = 'A'
elif score >= 75:
    grade = 'B'
elif score >= 60:
    grade = 'C'
else:
    grade = 'F'

print(f'Grade: {grade}')  # Grade: B
```

```python

temperatures = [21.3, 19.8, 23.1, 18.5, 22.0]
high_count = 0

for temp in temperatures:
    if temp > 22.0:
        high_count += 1

print(f'{high_count} readings above threshold')
```

**Common trap:** `range(5)` gives 0, 1, 2, 3, 4 — not 1 through 5. The stop value is always excluded.

## 6. Functions: Reusable Building Blocks

A function is like a kitchen appliance — plug it in once, use it as many times as you like. `def` creates a function. The names in the parentheses are parameters — placeholders for the values passed in when calling. `return` sends a result back to the caller.

```python

def greet(name):
    return 'Hello, ' + name + '!'

print(greet('Alice'))   # Hello, Alice!
print(greet('Bob'))     # Hello, Bob!
```

```python

def validate_port(text):
    try:
        port = int(text)
    except ValueError:
        return None
    if port < 1 or port > 65535:
        return None
    return port

print(validate_port('8080'))   # 8080
print(validate_port('99999'))  # None
print(validate_port('abc'))    # None
```

**Key rule:** use `return` to give data back, not `print()`. If you only `print()` inside a function, tests and other code cannot use the result.

## 7. Putting It All Together

The real power of Python basics is combining these pieces into small programs that solve real problems.

```python
# A mini cart calculator — uses variables, lists, loops, conditions, and a function
def summarise_cart(prices, tax_rate=0.08):
    subtotal = sum(prices)
    tax = round(subtotal * tax_rate, 2)
    total = subtotal + tax

    if total >= 100:
        status = 'manager_review'
    else:
        status = 'approved'

    return {
        'item_count': len(prices),
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'status': status,
    }

result = summarise_cart([19.99, 35.50, 12.00])
print(result)
# {'item_count': 3, 'subtotal': 67.49, 'tax': 5.4, 'total': 72.89, 'status': 'approved'}
```

Trace through this function line by line: the list goes in, `sum` adds the prices, conditionals choose the status, and a dictionary comes back. This pattern — input → process → structured output — is the core of most real Python functions.
