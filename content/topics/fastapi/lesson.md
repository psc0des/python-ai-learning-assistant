# FastAPI

FastAPI is a Python framework for building web APIs — the backend services that power mobile apps, web frontends, and integrations between systems. You describe each API endpoint in Python code, and FastAPI handles the heavy lifting: parsing incoming data, validating it, routing requests to the right handler, and sending back structured responses. As a bonus, it auto-generates interactive documentation from your code.

Think of a FastAPI app like a post office counter. A customer walks in (HTTP request) with a specific request form filled out (path, query params, JSON body). The counter staff (FastAPI) read the form, check it is filled correctly (validation), then hand the request to the right department (route handler). That department does the work and sends back a response slip (JSON response with a status code). Dependencies are like specialist consultants the department can call in — authentication, database sessions, shared settings.

## 1. Your First FastAPI App — Routes and Decorators

A FastAPI route is a Python function with a decorator that tells FastAPI which URL and HTTP method should trigger it. When a matching request arrives, FastAPI calls your function and converts its return value to a JSON response.

```python
# The minimal FastAPI app
from fastapi import FastAPI

app = FastAPI()

@app.get('/')                    # GET request to /
def read_root():
    return {'message': 'Hello!'} # FastAPI converts this dict to JSON

@app.get('/items/{item_id}')     # {} means a path variable
def read_item(item_id: int):     # type hint → FastAPI validates the value
    return {'item_id': item_id}
```

To run: `uvicorn main:app --reload`. Then visit `http://localhost:8000` and `http://localhost:8000/docs` (free interactive documentation!).

```python

@app.get('/health', status_code=200)
def health_check():
    return {'status': 'ok', 'service': 'billing-api', 'version': '1.2.0'}
```

**The decorator tells FastAPI everything:** `@app.get` means 'respond to GET requests', `@app.post` means 'respond to POST requests', and so on. The function name is just Python — it does not affect the URL.

## 2. Path, Query, and Body Parameters — Where Data Lives

Every HTTP request can carry data in three places, and each has a different purpose:

- **Path parameters** — identify a specific resource: `/users/42` → `user_id = 42`
- **Query parameters** — filter or paginate: `/users?limit=10&active=true`
- **Request body** — send structured data for create/update operations

FastAPI figures out which is which from the function signature:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):  # body model
    name: str
    email: str

@app.get('/users/{user_id}')          # {user_id} is a path param
def get_user(
    user_id: int,                     # <- from path (matches the URL pattern)
    include_deleted: bool = False,    # <- from query (?include_deleted=true)
):
    return {'id': user_id, 'include_deleted': include_deleted}

@app.post('/users', status_code=201)
def create_user(user: UserCreate):    # <- from request body (JSON)
    return {'id': 99, 'name': user.name, 'email': user.email}
```

**Layman rule:** path identifies *which* thing, query modifies *how* you see it, body carries *what* you are creating or updating. This separation makes APIs predictable and easy to document.

## 3. Request Validation with Pydantic

When users submit data to your API, it might be wrong — a missing field, a number where text was expected, a value out of range. FastAPI uses Pydantic models to validate this automatically, rejecting bad data with a clear `422 Unprocessable Entity` error before it ever reaches your logic.

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=100, description='Must be 1-100')  # range constraint
    notes: str = ''   # optional field with a default

@app.post('/orders', status_code=201)
def create_order(order: OrderCreate):
    return {
        'order_id': 'ORD-001',
        'product_id': order.product_id,
        'quantity': order.quantity,
    }
```

If you POST `{'product_id': 'abc', 'quantity': 200}`, FastAPI automatically responds:

```
422 Unprocessable Entity
{
  "detail": [
    {"field": "product_id", "msg": "value is not a valid integer"},
    {"field": "quantity",   "msg": "ensure this value is less than or equal to 100"}
  ]
}
```

Your handler function is only called with **valid, type-correct data**. This eliminates an entire category of defensive checks from your business logic.

## 4. HTTP Status Codes — Communicating Outcomes

HTTP status codes tell clients what happened. Using the right code makes APIs intuitive and self-documenting. Using 200 for everything (including errors) is a common mistake that forces clients to parse response bodies just to know if it worked.

```
200 OK           — request succeeded, data returned
201 Created      — new resource was created successfully
204 No Content   — success, nothing to return (e.g. DELETE)
400 Bad Request  — malformed request syntax
401 Unauthorized — not authenticated (need to log in)
403 Forbidden    — authenticated but not allowed
404 Not Found    — resource does not exist
422 Unprocessable Entity — valid syntax but invalid data (FastAPI validation errors)
500 Internal Server Error — something broke on the server
```

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()
fake_db = {1: {'name': 'Widget'}, 2: {'name': 'Gadget'}}

@app.get('/products/{product_id}')
def get_product(product_id: int):
    if product_id not in fake_db:
        raise HTTPException(status_code=404, detail=f'Product {product_id} not found')
    return fake_db[product_id]

@app.delete('/products/{product_id}', status_code=204)
def delete_product(product_id: int):
    if product_id not in fake_db:
        raise HTTPException(status_code=404, detail=f'Product {product_id} not found')
    del fake_db[product_id]
```

`HTTPException` is FastAPI's way to send an error response immediately and stop the handler from continuing.

## 5. Dependencies — Reuse Without Repetition

Most real API endpoints need the same things: check the user is logged in, get a database connection, load app settings. Without a pattern for this, you end up copying the same code into every handler.

FastAPI's `Depends` system lets you declare shared logic once and inject it into any route that needs it.

```python
from fastapi import Depends, FastAPI, HTTPException, Header

app = FastAPI()

# Dependency: verify a simple API key header
def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != 'secret-key-123':
        raise HTTPException(status_code=401, detail='Invalid API key')
    return x_api_key

# Any route can use it by adding: current_key=Depends(require_api_key)
@app.get('/protected-data')
def get_data(current_key: str = Depends(require_api_key)):
    return {'data': 'This is protected content', 'key': current_key}

@app.get('/protected-stats')
def get_stats(current_key: str = Depends(require_api_key)):
    return {'stats': {'users': 42}, 'key': current_key}
```

Both routes require authentication. If the key check is wrong, both fail in the same way. If you need to change the check logic, you only change it in one place — the dependency function.

## 6. Error Handling and Auto-Generated API Docs

FastAPI generates interactive API documentation automatically from your code. Visit `/docs` (Swagger UI) or `/redoc` while your app is running and you get a clickable interface that lets you test every endpoint directly in the browser.

To make those docs truly useful, write clear error responses and add descriptions to your models and routes:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title='Order Service',
    description='Manages customer orders',
    version='2.1.0',
)

class OrderCreate(BaseModel):
    product_id: int = Field(description='ID of the product to order')
    quantity: int = Field(ge=1, description='Number of units to order (minimum 1)')

@app.post(
    '/orders',
    status_code=201,
    summary='Create a new order',
    responses={422: {'description': 'Validation error in request body'}},
)
def create_order(order: OrderCreate):
    """Create a new order for an authenticated customer."""
    if order.product_id > 9999:
        raise HTTPException(status_code=404, detail=f'Product {order.product_id} not found')
    return {'order_id': 'ORD-001', **order.model_dump()}
```

The docstring, `summary`, `responses`, and `Field(description=...)` all appear in `/docs`. Good documentation is not extra work — it emerges naturally from writing clean, type-hinted FastAPI code.

## 7. Try The Real Library

The labs in this topic build API concepts in pure Python so you understand routing, validation, status codes, and dependency boundaries before a framework hides them. When you are ready to use the real framework, try the official FastAPI path in a throwaway folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "fastapi[standard]"
fastapi dev main.py
```

Save this as `main.py` before running the command:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Ticket(BaseModel):
    title: str
    priority: int

@app.post('/tickets')
def create_ticket(ticket: Ticket):
    return {'accepted': True, 'ticket': ticket.model_dump()}
```

Open `http://127.0.0.1:8000/docs`, send a valid ticket, then send a bad one like `{"title": "oops", "priority": "high"}`. Connect what you see back to the pure-Python labs: route matching, schema validation, and structured error responses are the same ideas with production tooling around them.
