# LLM API Calls in Python

Every AI product you have used — ChatGPT, Claude, Copilot — runs on a simple loop: a Python program sends a structured request to a language model API and parses the structured response. This topic teaches you that plumbing. No AI framework required — just Python dictionaries, strings, and functions.

Think of an LLM API like a very smart mail-order service. You write a letter (your prompt), seal it in a structured envelope (a JSON payload), and send it to an address (the API endpoint). The service reads your letter, writes a reply, and sends it back in a structured format. Every AI application follows this same request-response cycle.

## 1. What Is an LLM API?

An API (Application Programming Interface) is how programs talk to each other. You send a request, the other service does work, and you get a response. An LLM API applies this to language models: your Python code sends a text-based request, a language model runs on the server, and you get a text-based response.

Every request is a POST to a URL, with a JSON body. Every response is a JSON object. You never need to understand how the model works internally — only the shape of the input and output.

```python run
# The request: a Python dict you serialize to JSON
payload = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is Python?"}],
    "temperature": 0.7,
}

# The response: a Python dict you get back (shown as a mock)
mock_response = {
    "choices": [
        {"message": {"role": "assistant", "content": "Python is a programming language."}}
    ],
    "usage": {"total_tokens": 18}
}

print(payload["model"])                                   # gpt-4o-mini
print(mock_response["choices"][0]["message"]["content"])  # Python is a programming language.
```

The same message format works across providers — OpenAI, Anthropic (via compatibility layer), Groq, Ollama, and others all support the same messages array structure.

## 2. The Messages Array

The `messages` field is the heart of every LLM API call. It is a list of dictionaries, each with two keys: `role` and `content`. The model reads every message in the list, in order, before generating a reply.

Three roles exist:

- `"system"` — instructions to the model: how it should behave, what constraints to follow. Usually the first message in the list.
- `"user"` — what the human typed.
- `"assistant"` — what the model said in a previous turn. You include past assistant messages so the model understands the conversation so far.

```python run
messages = [
    {"role": "system", "content": "You are a concise Python tutor. Keep answers to two sentences."},
    {"role": "user", "content": "What is a list?"},
    {"role": "assistant", "content": "A list is an ordered, mutable sequence. You create one with square brackets: [1, 2, 3]."},
    {"role": "user", "content": "What about a tuple?"},
]

for msg in messages:
    label = msg["role"].upper()
    print(f"{label}: {msg['content'][:60]}")
```

The model sees the full conversation thread — both what you said and what it said before — which is how it maintains context across multiple turns.

## 3. Building a Request Payload

The request body has three common fields: `model`, `messages`, and `temperature`. Build it as a Python dictionary — your HTTP library or SDK will serialize it to JSON.

- `model` — which model to call. The exact string depends on your provider: `"gpt-4o-mini"`, `"claude-3-haiku-20240307"`, `"llama3"` for Ollama, etc.
- `messages` — the conversation array from the previous section.
- `temperature` — a float from `0.0` to `2.0`. Lower = more predictable output. Higher = more creative. `0.7` is a sensible default for most tasks.

```python run
def build_payload(messages, model="gpt-4o-mini", temperature=0.7):
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

msgs = [{"role": "user", "content": "Explain list comprehensions in one sentence."}]
payload = build_payload(msgs, model="gpt-4o")

print(payload["model"])          # gpt-4o
print(payload["temperature"])    # 0.7
print(len(payload["messages"]))  # 1
```

Wrapping this in a function immediately makes it testable and easy to update. If your provider changes the required fields, you update the function once.

## 4. Reading the Response

The response is a nested dictionary. The generated text lives at `response["choices"][0]["message"]["content"]`. The path looks long but follows a clear structure: `choices` is a list (usually with one item), each choice has a `message`, and the message has `content`.

Token usage — how many tokens were consumed — is at `response["usage"]["total_tokens"]`. Providers bill by token, so tracking this matters once you move beyond experimenting.

```python run
mock_response = {
    "id": "chatcmpl-abc123",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "A list comprehension builds a list from another iterable in one compact line."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 14,
        "completion_tokens": 17,
        "total_tokens": 31
    }
}

reply = mock_response["choices"][0]["message"]["content"]
tokens = mock_response["usage"]["total_tokens"]
finish = mock_response["choices"][0]["finish_reason"]

print(reply)
print(f"Tokens used: {tokens}")
print(f"Stopped because: {finish}")
```

`finish_reason` tells you why the model stopped. `"stop"` means it finished naturally. `"length"` means it hit the `max_tokens` limit and the response may be cut off.

## 5. Prompt Templates as Functions

A prompt template is a string with placeholders. Instead of writing slightly different versions of the same prompt each time, write a function that takes parameters and returns the fully assembled string. This makes prompts reusable, testable, and easy to improve independently of the rest of your code.

```python run
def explain_prompt(concept, audience="a beginner"):
    return f"Explain {concept} to {audience} in plain English. Keep it to two sentences."

def compare_prompt(thing_a, thing_b):
    return f"What is the difference between {thing_a} and {thing_b}? One sentence only."

print(explain_prompt("recursion"))
print(explain_prompt("async/await", audience="someone who knows JavaScript"))
print(compare_prompt("list", "tuple"))
```

For templates where the structure itself comes from configuration or user input, use `str.format()` with keyword arguments:

```python run
def make_prompt(template, **kwargs):
    return template.format(**kwargs)

tmpl = "Summarize the following {doc_type} in {word_count} words:\n\n{text}"
result = make_prompt(
    tmpl,
    doc_type="email",
    word_count=30,
    text="Dear team, the meeting is moved to Thursday."
)
print(result)
```

Keep each template function focused on one task. A function that assembles 10 different prompts based on flags is a signal those prompts should be separate functions.

## 6. Conversation History

LLMs have no memory between separate API calls. To simulate a multi-turn conversation, you maintain the full list of messages yourself and send it with every request.

The loop: append the user message → call the API → extract the reply → append it as an `"assistant"` message → repeat.

```python run
history = []

def add_message(role, content):
    history.append({"role": role, "content": content})

def show_history():
    for msg in history:
        print(f'  {msg["role"].upper()}: {msg["content"]}')

# Turn 1
add_message("system", "You are a Python tutor.")
add_message("user", "What is a list?")
add_message("assistant", "An ordered, mutable sequence. Example: [1, 2, 3].")

# Turn 2
add_message("user", "How do I add an item?")
add_message("assistant", "Use list.append(item). Example: mylist.append(4).")

print(f"{len(history)} messages in history:")
show_history()
```

One important constraint: every model has a context window — the maximum number of tokens it can process in one request. A long conversation eventually fills this limit. In production, you truncate old messages, keep only the system message and the most recent turns, or summarize earlier history before it overflows.
