# OOP

Object-oriented programming (OOP) is a way of organising code around real-world concepts. Instead of writing loose functions that operate on raw data, you bundle the data and the functions that belong together into a single unit called a class. Think of a bank account: it has a balance (data) and actions like deposit, withdraw, and check_balance (behaviour). OOP lets you model this naturally in code.

A class is a blueprint — like an architectural drawing for a house. The drawing itself is not a house; it describes what a house looks like and what rooms it has. When you build a house from that drawing, you get an instance (an actual object). Each instance has its own state (its own address, its own furniture) but follows the same blueprint. In Python, `__init__` sets up each new instance's starting state, and `self` is how methods refer to the specific instance they are working on.

## 1. What Is a Class? Blueprint vs Instance

Imagine you are designing a dog shelter. Every dog has a name, a breed, and an age — but each dog is different. Instead of creating separate variables for every dog, you create a **class** called `Dog` that describes what every dog has. Then you create individual dogs (instances) from that blueprint.

```python

class Dog:
    def __init__(self, name, breed):
        self.name = name    # each dog has its OWN name
        self.breed = breed  # each dog has its OWN breed

    def speak(self):
        return f'{self.name} says: Woof!'

# Create two different dog instances
dog1 = Dog('Rex', 'Labrador')
dog2 = Dog('Bella', 'Poodle')

print(dog1.speak())   # Rex says: Woof!
print(dog2.speak())   # Bella says: Woof!
print(dog1.name)      # Rex
print(dog2.name)      # Bella — completely separate from dog1
```

Each call to `Dog(...)` creates a brand new, independent instance. Changing `dog1.name` has absolutely no effect on `dog2`.

```python

class ServiceMonitor:
    def __init__(self, service_name, threshold_ms=200):
        self.service_name = service_name
        self.threshold_ms = threshold_ms
        self.recent_latencies = []

    def record(self, latency_ms):
        self.recent_latencies.append(latency_ms)

    def is_healthy(self):
        if not self.recent_latencies:
            return True
        avg = sum(self.recent_latencies) / len(self.recent_latencies)
        return avg < self.threshold_ms
```

## 2. __init__ and self — Setting Up Each Instance

`__init__` is a special method (called a **dunder** — short for double underscore) that Python calls automatically whenever you create a new instance. Its job is to set up the starting state for that specific object.

`self` is how an instance refers to itself. Inside any instance method, `self` is the first parameter and Python fills it in automatically — you never pass it manually when calling methods.

```python
class BankAccount:
    def __init__(self, owner, initial_balance=0):
        self.owner = owner              # set on THIS specific account
        self.balance = initial_balance  # each account tracks its own balance
        self.transactions = []          # each account has its own history

    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(('deposit', amount))

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError('Insufficient funds')
        self.balance -= amount
        self.transactions.append(('withdrawal', amount))

    def statement(self):
        return f'{self.owner}: £{self.balance:.2f} ({len(self.transactions)} txns)'

alice_account = BankAccount('Alice', 1000)
alice_account.deposit(500)
alice_account.withdraw(200)
print(alice_account.statement())  # Alice: £1300.00 (2 txns)

bob_account = BankAccount('Bob', 250)
print(bob_account.statement())    # Bob: £250.00 (0 txns) — separate!
```

Notice how `alice_account` and `bob_account` are completely independent — they each have their own `balance` and `transactions`.

## 3. Class Variables vs Instance Variables

This is one of the most important distinctions in OOP — and one of the most common sources of bugs.

- **Instance variables** (set via `self.name = ...`) belong to each individual object
- **Class variables** (set at class level, outside any method) are **shared by all instances**

```python
# Layman analogy: all employees share the same company name,
# but each has their own personal name and salary
class Employee:
    company = 'Acme Corp'   # CLASS variable — shared by everyone

    def __init__(self, name, salary):
        self.name = name       # INSTANCE variable — per employee
        self.salary = salary   # INSTANCE variable — per employee

emp1 = Employee('Alice', 75000)
emp2 = Employee('Bob', 82000)

print(emp1.company)   # Acme Corp
print(emp2.company)   # Acme Corp — same shared value
print(emp1.name)      # Alice
print(emp2.name)      # Bob — each has their own
```

**The dangerous trap:** if your class variable is a **mutable** object (a list or dict), all instances will share and accidentally modify the same object.

```python
# BUG: all instances share the same list!
class BadQueue:
    items = []             # WRONG — this is a class variable!

    def add(self, item):
        self.items.append(item)

q1 = BadQueue()
q2 = BadQueue()
q1.add('task-1')
print(q2.items)   # ['task-1'] — contaminated!

# CORRECT: create a new list in __init__ for each instance:
class GoodQueue:
    def __init__(self):
        self.items = []    # CORRECT — fresh list per instance
```

## 4. Methods — Behaviour That Belongs to Data

A method is a function defined inside a class. The key difference from a regular function: methods have access to the object's own data through `self`, so they can read and update the object's state.

Good methods have a **single clear responsibility**. If a method name requires 'and' to describe it, it probably does too much.

```python

class Counter:
    def __init__(self, start=0):
        self.count = start

    def increment(self, amount=1):
        self.count += amount

    def reset(self):
        self.count = 0

    def value(self):
        return self.count

c = Counter()
c.increment()
c.increment(5)
print(c.value())   # 6
c.reset()
print(c.value())   # 0
```

```python

class RetryPolicy:
    def __init__(self, max_attempts, backoff_seconds=1.0):
        self.max_attempts = max_attempts
        self.backoff = backoff_seconds

    def should_retry(self, attempt_number):
        return attempt_number < self.max_attempts

    def delay_for(self, attempt_number):
        return self.backoff * (2 ** attempt_number)  # exponential backoff

policy = RetryPolicy(max_attempts=3)
for attempt in range(5):
    if policy.should_retry(attempt):
        print(f'Attempt {attempt}, wait {policy.delay_for(attempt)}s')
```

Note how the retry logic and its configuration live together in one place. If you needed to change the retry strategy, you only change this one class.

## 5. Inheritance vs Composition — Which to Choose

**Inheritance** lets one class extend another: the child class gets all the parent's methods plus adds or overrides its own. Use it when the relationship is genuinely 'is-a': a `Dog` **is an** `Animal`.

**Composition** means a class *contains* another class as an attribute. Use it when the relationship is 'has-a': a `Car` **has a** `Engine`.

```python
# Inheritance: Animal → Dog is a true 'is-a' relationship
class Animal:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return f'{self.name} is an animal'

class Dog(Animal):          # Dog inherits from Animal
    def speak(self):
        return f'{self.name} barks'

rex = Dog('Rex')
print(rex.describe())   # Rex is an animal  — inherited
print(rex.speak())      # Rex barks          — own method
```

```python
# Composition: Router 'has-a' Logger — not 'is-a' Logger
class Logger:
    def log(self, message):
        print(f'[LOG] {message}')

class Router:
    def __init__(self):
        self.logger = Logger()    # composition — Router uses a Logger

    def route(self, path):
        self.logger.log(f'Routing: {path}')
        return f'Handled {path}'

r = Router()
r.route('/api/users')
# [LOG] Routing: /api/users
```

**Prefer composition in most cases.** Deep inheritance trees are hard to understand and modify. Composition keeps each class focused and independently testable.

## 6. Dataclasses — Less Boilerplate for Data Objects

When a class mostly exists to **hold data** (configuration, records, API responses), writing `__init__` with repeated `self.x = x` for every field gets tedious. The `@dataclass` decorator generates this automatically from field type annotations.

```python
# Without dataclass — lots of repetition
class Config:
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
```

```python
# With dataclass — much cleaner
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str
    port: int
    debug: bool = False
    tags: list = field(default_factory=list)  # safe mutable default

cfg = Config(host='localhost', port=8080)
print(cfg)          # Config(host='localhost', port=8080, debug=False, tags=[])
print(cfg.host)     # localhost
```

```python

@dataclass
class DeployRequest:
    service: str
    environment: str
    replicas: int = 1
    dry_run: bool = False

    def validate(self):
        if self.replicas < 1:
            raise ValueError('replicas must be at least 1')
        if self.environment not in ('staging', 'production'):
            raise ValueError(f'Unknown environment: {self.environment}')

req = DeployRequest(service='api', environment='staging', replicas=3)
req.validate()
print(req)
```

Dataclasses also auto-generate `__repr__` (nice print output) and `__eq__` (comparison). Use them whenever a class is primarily a structured data container.
