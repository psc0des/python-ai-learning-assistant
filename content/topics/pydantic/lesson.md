# Pydantic

Pydantic is one of the most important Python tools for backend and AI systems because it protects boundaries. Instead of trusting raw dictionaries from users, APIs, files, or queues, you parse input into models and only pass validated output deeper into your system.

## 1) Models as Boundary Contracts

Create classes that inherit from `BaseModel` and define fields with type hints. This model becomes the accepted shape of input. If incoming data doesn't fit, validation fails early instead of failing later in business logic.

## 2) Validation Output Guarantee

The official docs call out an important nuance: "validation" in Pydantic means the resulting model output conforms to your schema. It does not mean the raw input was already correct. Pydantic may parse or coerce inputs before producing valid output. This is why your app should use model output, not raw payloads.

## 3) Field Constraints and Domain Rules

Use `Field()` for constraints like `ge=1`, `le=5`, `min_length`, and `max_length`. Put rules where data enters the system. This avoids scattered checks and makes behavior predictable across endpoints and services.

## 4) Optional vs Default vs Required

These are different:
- `Optional[str]` means `None` is allowed.
- A default means the field can be omitted.
- No default means required.

Being explicit here prevents subtle bugs when requests omit fields or send null values.

## 5) Coercion vs Strict Mode

Default mode is helpful for many boundaries (e.g., `"3"` becoming `3`). But strict mode is better when type correctness must be enforced exactly. Choose based on risk:
- Use coercion-friendly behavior where developer convenience is acceptable.
- Use strict behavior for sensitive settings, identity fields, or high-impact operations.

## 6) Validation Errors, Custom Validators, and Serialization

`ValidationError` contains structured details that can be returned by APIs or logged with context. For custom rules (for example, two fields must agree), use field or model validators. Once data is valid, serialize with `model_dump()` or `model_dump_json()`.

## Real-World Implementation Pattern

In production APIs, teams often:
1. Parse request payload into a Pydantic model.
2. Return structured field errors immediately on failure.
3. Pass validated model data to service/business logic.
4. Serialize response models consistently.

This pattern improves reliability, testing, and maintainability.
