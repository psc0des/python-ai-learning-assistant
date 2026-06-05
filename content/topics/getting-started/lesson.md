# Getting Started: Coding From Zero

This topic assumes you have never written a line of code. By the end you will have run real Python, made the computer do small useful things, and understood the handful of ideas everything else is built on. Go slowly, type every example yourself, and let yourself make mistakes — that is how you learn.

## 1. What Is Code, and How Do You Run It?

Think of a recipe card. It is a list of steps, written in order, that anyone can follow to make a dish. Code is exactly that — a list of steps written for a computer to follow. The computer reads your steps from top to bottom and does each one, in order, extremely fast.

The program that reads and runs your Python steps is called the **interpreter**. You write code, you press Run, and the interpreter does what you wrote. In this app you do not need to install anything — the editor and a Run button are built in. You write a line, run it, and see the result immediately. That instant feedback is the best way to learn.

The simplest possible instruction is to show something on the screen. We use `print()` for that:

```python run
print('I just ran my first line of code!')
```

When you run that, the words inside the quotes appear as output. That is it — you have run a program. Everything else in programming is just learning more kinds of instructions to put on the list.

**Try this:** change the words inside the quotes to your own name and run it again. Changing examples and re-running is how you learn fastest.

## 2. Showing Output with print()

`print()` is how your program talks to you. Whatever you put inside the brackets, Python shows on the screen. This is your window into what your code is doing — you will use it constantly to check your work.

You can print text (always wrapped in quotes), numbers (no quotes), or several things separated by commas:

```python run
print('Hello!')          # text in quotes
print(42)                # a number, no quotes
print('Score:', 95)      # two things — Python adds a space: Score: 95
```

Anything inside quotes is treated as plain text and printed exactly as written. Anything without quotes, Python tries to understand as a value or calculation:

```python run
print('2 + 2')   # shows: 2 + 2   (it is just text)
print(2 + 2)     # shows: 4       (Python does the maths)
```

That difference — quotes mean 'literal text', no quotes mean 'work this out' — is one of the first big 'aha' moments in coding.

**Try this:** print your favourite number, then print it with `+ 10` after it (no quotes) and watch Python do the maths.

## 3. Variables: Naming Your Values

Imagine sticking a labelled note onto a box so you can find it again later. A **variable** is that label. You pick a name, attach it to a value with `=`, and from then on you can use the name instead of repeating the value.

```python run
name = 'Sam'
age = 20

print(name)        # Sam
print(age)         # 20
print(age + 1)     # 21
```

Read `=` as 'gets' or 'is set to', not as the equals sign from maths. `age = 20` means 'the name age now points to the value 20'. You can change it later, and the newest value wins:

```python run
score = 10
score = score + 5    # take the current score (10), add 5, store it back
print(score)         # 15
```

Good names make code readable. `total_price` tells a future reader (including you tomorrow) what the value means; `x` does not.

**Common trap:** using a name before you have created it. If you `print(city)` before writing `city = 'Paris'`, Python stops with a `NameError` — it has no note with that label yet.

## 4. The Three Values You Meet First: Text, Numbers, True/False

Every value in Python has a **type** — a kind. As a beginner you meet three kinds first:

- **Text** (called a *string*): letters and symbols wrapped in quotes, like `'hello'` or `'order #42'`.
- **Numbers**: whole numbers like `7` (an *int*) and decimals like `3.5` (a *float*). No quotes.
- **True/False** (called a *boolean*): the answer to a yes/no question — exactly `True` or `False`.

```python run
city = 'Tokyo'      # text
temperature = 18.5  # number
is_raining = False  # True/False

print(type(city))         # <class 'str'>
print(type(temperature))  # <class 'float'>
print(type(is_raining))   # <class 'bool'>
```

The type matters because it decides what you can do. You can add two numbers to get a sum; you can 'add' two strings to join them together; but adding a number to text directly causes an error.

```python run
print('Sea' + 'shell')   # Seashell  (joining text)
print(3 + 4)             # 7         (adding numbers)
```

Booleans appear whenever you ask a question, like `5 > 3`, which Python answers with `True`. They are the foundation of decisions, which come next.

**Try this:** run `print(type(your_value))` on a few different values to see what Python calls them.

## 5. Making Decisions with if / else

Real programs need to choose what to do based on the situation — like a doorman who lets you in only if you are on the list. In Python, `if` and `else` make that choice.

You give `if` a yes/no question (something that is True or False). If it is True, Python runs the indented lines underneath. If it is False, it runs the `else` block instead.

```python run
age = 15

if age >= 18:
    print('You can vote.')
else:
    print('Too young to vote.')
# shows: Too young to vote.
```

Two details that catch every beginner:

- Use `==` (two equals signs) to **check** if things are equal, and `=` (one) to **store** a value. `if name == 'Sam':` asks a question; `name = 'Sam'` sets a value.
- The lines that belong to the `if` must be **indented** (pushed to the right, usually four spaces). The indentation is how Python knows which lines are 'inside' the decision.

The comparison questions you will use most: `==` (equal), `!=` (not equal), `>` `<` `>=` `<=` (greater/less than).

```python run
score = 72
if score >= 50:
    result = 'pass'
else:
    result = 'fail'
print(result)   # pass
```

**Try this:** change `score` to a number below 50 and run it again to see the other branch.

## 6. Your First Function (and Reading Errors)

When you find yourself wanting to reuse the same steps, you wrap them in a **function** — a named instruction you can run again and again. You met `print()` already; that is a function someone else wrote. Now you write your own with `def`.

```python run
def greet(person):
    return 'Hello, ' + person + '!'

print(greet('Sam'))   # Hello, Sam!
print(greet('Mia'))   # Hello, Mia!
```

The word in brackets (`person`) is a placeholder for whatever you pass in when you call it. `return` is the function's way of handing a result back so the rest of your program can use it. This is different from `print()`: `print` only shows text on screen, while `return` gives a value back to your code. In this app, the labs check the value you **return**, so returning (not just printing) matters.

**Reading errors — the most important beginner skill.** When Python cannot follow an instruction, it stops and prints an error. Do not panic and do not ignore it — read the **last line**, which names the problem:

```python
print(total)
# NameError: name 'total' is not defined
```

That last line is Python telling you, in its own words, exactly what confused it — here, you used `total` before creating it. Errors are normal. Professional programmers read them all day. Learning to read the last line calmly is what turns a frustrating wall into a simple fix.

**Try this:** write a function `double(n)` that returns `n * 2`, then call it with a few numbers.
