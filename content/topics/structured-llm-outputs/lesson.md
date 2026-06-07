# Structured Outputs From LLMs

A language model that returns plain text is like a colleague who answers every question with a paragraph. Useful in conversation — a nightmare in code. When your application needs to extract a name, a status, or a number from a model response, free-form text forces you to write fragile parsing logic that breaks the moment the model changes its phrasing. Structured output solves this by making the model return data in a predictable shape your code can read directly.

Think of a structured output schema like a form instead of a blank page. When you hand someone a blank page, they might write an essay, a list, or a doodle. When you hand them a form with labelled fields, you get exactly the data you asked for in exactly the shape you expected. LLMs respond to structured prompting the same way — the right instructions produce JSON you can parse without guesswork.

## 1. The Problem With Free-Text Output

When an LLM replies in natural language, extracting specific values becomes fragile. The model might say "Alice is 30" one time and "The user's name is Alice, age 30" the next. Any code that splits on commas or searches for patterns will break as soon as the phrasing changes.

Structured data is different. A dictionary is a dictionary — you access `data["name"]` and it is always there, always a string, in a predictable position.

```python run
# Accessing structured data is reliable and readable
structured = {"name": "Alice", "age": 30, "role": "engineer", "active": True}

name = structured["name"]
next_birthday = structured["age"] + 1
status = "active" if structured["active"] else "inactive"

print(f"{name} turns {next_birthday} next year — {status}")
```

```python
# Without structure, you write fragile string parsing
unstructured_responses = [
    "Alice is 30 years old and currently active.",
    "The user named Alice (age: 30) is active.",
    "Name: Alice, Age 30. Status: active user.",
]

for text in unstructured_responses:
    # Every variation breaks a different assumption
    print(repr(text.split("is")[1].split("years")[0].strip()))
```

The solution is not smarter parsing — it is asking the model to return structured data in the first place.

## 2. Asking for JSON in Your Prompt

The simplest way to get structured output is to instruct the model in the system prompt. Tell it to reply only with valid JSON, describe the fields you expect, and give an example of the shape.

```python run
def json_system_prompt(fields_description):
    return (
        "You are a data extraction assistant. "
        "Reply only with a valid JSON object — no explanation, no markdown, no code fences. "
        f"The JSON must contain these fields: {fields_description}"
    )

prompt = json_system_prompt(
    '"name" (string), "age" (integer), "active" (boolean)'
)
print(prompt)
```

```python run
def structured_payload(user_text, required_fields):
    system = (
        "Extract the requested information and return only a JSON object. "
        "Do not include any text outside the JSON. "
        f"Required fields: {', '.join(required_fields)}"
    )
    return {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.0,
    }

payload = structured_payload("Alice is 30 and works as an engineer.", ["name", "age", "role"])
print(payload["messages"][0]["content"])
print(payload["temperature"])  # 0.0 — deterministic for extraction tasks
```

Use `temperature=0.0` for extraction tasks. You want the most predictable output, not creativity.

## 3. Validating With Pydantic

Pydantic lets you define the exact shape you expect from LLM output as a Python class. When you call `model_validate()`, it parses the dict and raises a `ValidationError` if any field is missing, the wrong type, or fails a constraint. This turns vague "something went wrong" failures into specific, readable errors.

```python
# Production pattern — Pydantic validation (requires: pip install pydantic)
from pydantic import BaseModel

class PersonRecord(BaseModel):
    name: str
    age: int
    active: bool

# Valid input — works
record = PersonRecord.model_validate({"name": "Alice", "age": 30, "active": True})
print(record.name)   # Alice
print(record.age)    # 30

# Invalid input — raises ValidationError with clear message
try:
    PersonRecord.model_validate({"name": "Alice", "age": "thirty"})
except Exception as e:
    print(e)   # age: Input should be a valid integer...
```

The same validation logic — check required fields, check types, report errors clearly — can be written in pure Python. The labs in this topic practice that pattern so you understand what Pydantic is doing under the hood:

```python run
def validate_person(data):
    errors = []
    if "name" not in data:
        errors.append("missing required field: name")
    elif not isinstance(data["name"], str):
        errors.append("name must be a string")
    if "age" not in data:
        errors.append("missing required field: age")
    elif not isinstance(data["age"], int):
        errors.append("age must be an integer")
    return errors

print(validate_person({"name": "Alice", "age": 30}))        # []
print(validate_person({"name": "Alice", "age": "thirty"}))  # ['age must be an integer']
print(validate_person({"name": "Alice"}))                    # ['missing required field: age']
```

## 4. Handling Parse Failures

Even with the best system prompt, an LLM can return text that is not valid JSON. A model might add an explanation before the JSON, wrap it in markdown code fences, or return a refusal. Your code must handle this gracefully.

The pattern is always the same: wrap `json.loads()` in a try/except and return a sentinel value (`None`, an empty dict, or a typed error) on failure.

```python run
import json

def safe_parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

# Valid JSON
print(safe_parse('{"name": "Alice", "age": 30}'))

# Invalid — LLM added explanation text
print(safe_parse('Here is the data: {"name": "Alice"}'))

# Empty or completely wrong
print(safe_parse("I cannot extract that information."))
```

```python run
import json

def parse_with_fallback(text, default=None):
    try:
        data = json.loads(text)
        return data, []
    except json.JSONDecodeError as e:
        return default, [f"JSON parse error: {e.msg}"]

data, errors = parse_with_fallback('{"name": "Alice"}')
print(data, errors)   # {'name': 'Alice'} []

data, errors = parse_with_fallback("Sorry, no data.", default={})
print(data, errors)   # {} ['JSON parse error: Expecting value']
```

In production, a parse failure usually triggers a retry: send the same request again, or send a follow-up message asking the model to fix its output.

## 5. Nested Schemas and Lists

LLM output is often more complex than a flat key-value object. You might ask for a list of items, or an object with nested sub-objects. Validation needs to handle each layer.

```python run
import json

# Nested object with a list field
raw = '{"title": "Deploy v2", "tags": ["backend", "infra"], "assignee": {"name": "Sam", "team": "ops"}}'
data = json.loads(raw)

print(data["title"])
print(data["tags"][1])              # infra
print(data["assignee"]["team"])     # ops
```

```python run
import json

def validate_items_list(data, item_required_fields):
    errors = []
    items = data.get("items", [])
    if not isinstance(items, list):
        return ["'items' must be a list"]
    for i, item in enumerate(items):
        for field in item_required_fields:
            if field not in item:
                errors.append(f"item[{i}] missing field: {field}")
    return errors

payload = json.loads('{"items": [{"id": 1, "label": "A"}, {"id": 2}]}')
print(validate_items_list(payload, ["id", "label"]))
# ['item[1] missing field: label']
```

Validate lists by iterating and applying the same field-check logic to each element. Report the index with each error so you know which item failed.

## 6. Schema Design Tips

Not all schemas are equally reliable. LLMs handle simple, flat schemas well. They struggle with deeply nested structures, ambiguous types, and large numbers of required fields. A schema that looks reasonable to a developer can produce inconsistent output from a model.

```python run
# Simple schema — reliable, easy for the model to follow
simple = {
    "name": "string",
    "priority": "integer between 1 and 5",
    "status": "one of: open, in_progress, closed",
}

for field, hint in simple.items():
    print(f"  {field}: {hint}")
```

```python run
# Rules that improve reliability
tips = [
    "Use flat structures — avoid nesting beyond two levels.",
    "Use string enums ('one of: A, B, C') instead of open strings when possible.",
    "Avoid nullable fields — prefer a sentinel value like empty string or -1.",
    "Name fields unambiguously — 'start_date' not 'date'.",
    "Keep the total field count under 10 per object.",
]

for i, tip in enumerate(tips, 1):
    print(f"{i}. {tip}")
```

When a model consistently returns an unexpected shape, the first fix is usually simplifying or clarifying the schema description in the system prompt — not patching the parsing code.
