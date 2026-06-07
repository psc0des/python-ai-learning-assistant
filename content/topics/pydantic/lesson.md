# Pydantic

Every real Python application receives data from the outside world — form submissions, API requests, config files, database results. That data is almost never perfectly formatted. Pydantic is the tool Python developers use to convert messy, untrusted external input into clean, validated Python objects with the types and constraints you specified. Once data passes through Pydantic, you can trust it — no more defensive `if 'key' in data` checks scattered through your business logic.

Think of Pydantic like a customs officer at an airport border. Raw data arrives (like travellers with passports). The customs officer checks each piece against the rules (type hints and Field constraints). If everything checks out, the traveller is let through as a validated, trustworthy object. If something is wrong, they get a clear rejection with the specific problem listed — not a vague 'rejected'. Your business logic is the city on the other side — it only ever sees validated, correctly-typed people.

## 1. Your First Pydantic Model

A Pydantic model is a Python class that inherits from `BaseModel`. You declare the fields and their types using Python type hints, and Pydantic does the rest — parsing, converting, and validating input automatically.

```python
from pydantic import BaseModel

# Define the shape of the data you expect
class User(BaseModel):
    name: str
    age: int
    email: str

# Create an instance from a dictionary (like JSON from an API)
raw_data = {'name': 'Alice', 'age': '28', 'email': 'alice@example.com'}
user = User.model_validate(raw_data)

print(user.name)   # 'Alice' — a string
print(user.age)    # 28 — an int (Pydantic converted '28' from string!)
print(user)        # name='Alice' age=28 email='alice@example.com'
```

**What just happened?** The raw data had `age` as a string `'28'`. Pydantic automatically converted it to `int 28` because the field is declared as `int`. This is called **coercion**.

```python

class CreateTicketRequest(BaseModel):
    title: str
    priority: int
    assignee_id: str
    tags: list[str] = []   # optional — defaults to empty list

request = CreateTicketRequest.model_validate({
    'title': 'Server is down',
    'priority': '1',    # string → int coerced
    'assignee_id': 'u-42',
})
print(request.priority)   # 1 (int, not '1')
print(request.tags)       # [] — default applied
```

## 2. Validation Errors — When Bad Data Arrives

When input does not match your model, Pydantic raises a `ValidationError` with a detailed list of every field that failed and exactly why. This is far more useful than a generic 'something went wrong' message.

```python
from pydantic import BaseModel, ValidationError

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

# Test with bad data
try:
    p = Product.model_validate({
        'name': 123,          # wrong type — should be str
        # 'price' is missing entirely
        'in_stock': 'maybe',  # 'maybe' is not a recognised bool value
    })
except ValidationError as e:
    print(e)
# ValidationError: 3 validation errors for Product
#   name: Input should be a valid string
#   price: Field required
#   in_stock: Input should be a valid boolean
```

**In FastAPI**, this `ValidationError` is automatically converted into a `422 Unprocessable Entity` HTTP response with the full error details — so API clients know exactly what they need to fix.

**Important distinction:** validation is about the **output** being correct, not the input being clean. Pydantic takes messy input, applies rules, and guarantees the resulting object satisfies your model. If it cannot, it tells you why with precision.

## 3. Field Constraints — Encoding Business Rules

Type hints alone cannot express rules like 'must be positive' or 'cannot be an empty string'. `Field()` lets you add those constraints directly in the model, so they are enforced automatically every time.

```python
from pydantic import BaseModel, Field

class DeployRequest(BaseModel):
    service: str = Field(min_length=1, description='Service name cannot be empty')
    replicas: int = Field(ge=1, le=50, description='Must be between 1 and 50')
    environment: str = Field(pattern=r'^(staging|production)$')
    dry_run: bool = False

# This will pass:
req = DeployRequest.model_validate({
    'service': 'billing-api',
    'replicas': '3',
    'environment': 'staging',
})
print(req)

# This will fail (replicas=200 violates le=50):
try:
    DeployRequest.model_validate({'service': 'x', 'replicas': 200, 'environment': 'staging'})
except Exception as e:
    print(e)  # replicas: Input should be less than or equal to 50
```

**Common Field constraints:**
- `ge=1` — greater than or equal to 1
- `le=100` — less than or equal to 100
- `min_length=1` — string must not be empty
- `max_length=255` — string length cap
- `pattern=r'...'` — must match a regex
- `description='...'` — appears in FastAPI's auto-generated docs

## 4. Optional Fields and Default Values

Not every field is required. Pydantic lets you declare optional fields (where `None` is allowed) and fields with default values (which can be omitted). These are **two separate concepts** that are often confused.

```python
from pydantic import BaseModel
from typing import Optional

class UserProfile(BaseModel):
    username: str                  # REQUIRED — must be provided
    bio: str = ''                  # has a default — can be omitted
    avatar_url: Optional[str] = None  # optional — can be None or omitted
    age: int | None = None         # modern syntax (Python 3.10+)

# All of these are valid:
UserProfile(username='alice')                              # minimal
UserProfile(username='bob', bio='I love Python')          # with bio
UserProfile(username='carol', avatar_url='https://...')   # with avatar
UserProfile(username='dave', age=None)                    # explicitly None
```

**The critical distinction:**
- `bio: str = ''` → the field has a *default value*; it can be omitted from input
- `avatar_url: Optional[str] = None` → the field *allows None* as a value; it can also be omitted
- `username: str` → *required*; omitting it raises a ValidationError

Mixing these up causes bugs where required data silently gets a default, or nullable data unexpectedly rejects `None`.

## 5. Coercion vs Strict Mode

By default, Pydantic is helpful and converts compatible types automatically. This is called **coercion**: `'3'` becomes `3` for an `int` field, `'true'` becomes `True` for a `bool` field, and so on.

Sometimes this is too lenient — you want to be sure the caller is sending the exact right type, not relying on Pydantic to fix it for them.

```python
from pydantic import BaseModel

# Default (coercive) mode
class LenientModel(BaseModel):
    count: int
    active: bool

m = LenientModel(count='5', active='yes')
print(m.count, m.active)   # 5 True — silently coerced

# Strict mode — no coercion allowed
class StrictModel(BaseModel):
    model_config = {'strict': True}
    count: int
    active: bool

try:
    StrictModel(count='5', active=True)   # '5' is NOT an int → fails
except Exception as e:
    print(e)  # count: Input should be a valid integer
```

**When to use strict mode:**
- High-trust internal APIs where callers should know the exact contract
- Financial or safety-critical data where silent type promotion could mask a serious bug

**When to leave coercion on:**
- External-facing APIs where data may arrive from forms, URL params, or legacy systems that send everything as strings

## 6. Serialization — Getting Data Back Out

After validation, you need to get data back out of the model — to send as a JSON response, write to a database, or log for debugging. Pydantic provides `model_dump()` (returns a Python dict) and `model_dump_json()` (returns a JSON string).

```python
from pydantic import BaseModel, Field
from datetime import datetime

class OrderSummary(BaseModel):
    order_id: str
    total: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    internal_note: str = Field(default='', exclude=True)  # hide from output

order = OrderSummary(
    order_id='ORD-789',
    total=149.99,
    internal_note='flagged for review',  # this is excluded from output
)

# Get as dict (for further processing)
data = order.model_dump()
print(data)
# {'order_id': 'ORD-789', 'total': 149.99, 'created_at': datetime(...)}
# Note: 'internal_note' is excluded!

# Get as JSON string (for API responses or logging)
print(order.model_dump_json(indent=2))
```

**`exclude=True`** on a field means it will never appear in serialized output — perfect for internal flags, sensitive data, or fields that are only used for processing. This is cleaner than manually filtering dicts everywhere.
