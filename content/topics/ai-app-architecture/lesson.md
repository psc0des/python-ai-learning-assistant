# Basic AI App Architecture

## The Three-Layer Structure

An AI app is just regular Python code with three moving parts: something that takes user input, something that talks to the LLM, and something that handles the response. Understanding how those parts connect — and where to add RAG, tool calling, or validation — is the foundation of building real AI applications.

```python run
def build_request(config, messages):
    return {**config, 'messages': messages}

def parse_response(response):
    return response['choices'][0]['message']['content']

config = {'model': 'gpt-4o-mini', 'temperature': 0.7}
messages = [{'role': 'user', 'content': 'What is 2 + 2?'}]
payload = build_request(config, messages)
print(payload['model'])           # gpt-4o-mini
print(len(payload['messages']))   # 1
```

Each layer has one job. The input layer formats the user's words into the messages array. The LLM client sends the payload and receives the raw response. The output handler extracts the reply text and passes it on. Keep these layers separate — it makes each one independently testable and swappable.

```python run
def format_user_message(text):
    return {'role': 'user', 'content': text}

def extract_reply(response):
    return response['choices'][0]['message']['content']

msg = format_user_message('Hello')
fake_response = {'choices': [{'message': {'content': 'Hi there!'}}]}
print(extract_reply(fake_response))  # Hi there!
```

## Config and the Client Layer

Config is the set of values that control how the LLM responds — model name, temperature, max_tokens. These values are separate from the conversation content. Putting them in a dict or dataclass means you can change the model in one place without touching the code that builds messages.

```python run
def build_config(model, temperature=0.7, max_tokens=512):
    return {'model': model, 'temperature': temperature, 'max_tokens': max_tokens}

def build_request(config, messages):
    payload = dict(config)
    payload['messages'] = messages
    return payload

cfg = build_config('gpt-4o-mini', temperature=0.3)
payload = build_request(cfg, [{'role': 'user', 'content': 'Hello'}])
print(payload['temperature'])   # 0.3
print(payload['model'])         # gpt-4o-mini
```

The client layer is the boundary where Python meets the network. In a minimal implementation it is just a function that takes a payload and returns a response dict. Abstracting it this way means you can swap OpenAI for Anthropic or Ollama by changing one function, not the entire app.

```python run
def make_fake_client(fixed_reply):
    def client(payload):
        return {'choices': [{'message': {'content': fixed_reply}}]}
    return client

client = make_fake_client('Four.')
response = client({'model': 'gpt-4o-mini', 'messages': []})
print(response['choices'][0]['message']['content'])  # Four.
```

## Managing Conversation State

A stateless app sends only the current user message to the LLM and gets one reply. A stateful app keeps the full history of messages and sends the whole thread each turn. History is what makes multi-turn conversation possible — without it, the model forgets every previous message.

```python run
def add_message(history, role, content):
    history.append({'role': role, 'content': content})
    return history

history = []
add_message(history, 'system', 'You are a helpful assistant.')
add_message(history, 'user', 'What is 2 + 2?')
add_message(history, 'assistant', 'Four.')
add_message(history, 'user', 'Multiply that by three.')

print(len(history))           # 4
print(history[-1]['content']) # Multiply that by three.
```

The history list is just the `messages` array from the API spec. Pass it directly as the messages field in your payload. Each new user turn appends to the list; each assistant reply appends to the list. The LLM reads the full list every time.

```python run
def build_stateful_request(config, history, user_text):
    history.append({'role': 'user', 'content': user_text})
    return {**config, 'messages': history}

config = {'model': 'gpt-4o-mini', 'temperature': 0.7}
history = [{'role': 'system', 'content': 'You are helpful.'}]
payload = build_stateful_request(config, history, 'Hello!')
print(len(payload['messages']))    # 2 — system + user
print(payload['messages'][1]['role'])  # user
```

## Adding RAG and Tools

RAG (Retrieval-Augmented Generation) and tool calling are both ways of giving the LLM information it does not have in its weights. RAG prepends retrieved text to the system prompt before the request. Tool calling lets the model request your functions and read the results mid-conversation.

```python run
def add_rag_context(messages, chunks):
    context = '\n'.join(f'- {c}' for c in chunks)
    system = {'role': 'system', 'content': f'Use this context:\n{context}'}
    return [system] + messages

chunks = ['Paris is in France.', 'France is in Western Europe.']
messages = [{'role': 'user', 'content': 'Where is Paris?'}]
enriched = add_rag_context(messages, chunks)
print(enriched[0]['role'])   # system
print(len(enriched))         # 2
```

Tool dispatch works the same way regardless of which tool is called: read the function name and JSON arguments from the model's response, call the matching function in your registry, convert the result to a string, and send it back as a tool-role message.

```python run
import json

def dispatch(name, args_json, registry):
    args = json.loads(args_json)
    return str(registry[name](**args))

registry = {
    'greet': lambda name: f'Hello, {name}!',
    'add':   lambda a, b: a + b,
}
print(dispatch('greet', '{"name": "Alice"}', registry))  # Hello, Alice!
print(dispatch('add', '{"a": 3, "b": 4}', registry))     # 7
```

## Error Handling and Fallbacks

LLM API calls can fail: network timeouts, rate limits, malformed responses, or the model returning something you did not expect. A fallback is a default value your app returns when something goes wrong, so the user sees a helpful message instead of a Python traceback.

```python run
def with_fallback(fn, default):
    try:
        return fn()
    except Exception:
        return default

result = with_fallback(lambda: 42, 0)
print(result)    # 42

bad = with_fallback(lambda: 1 / 0, -1)
print(bad)       # -1

text = with_fallback(lambda: int('not a number'), 'parse error')
print(text)      # parse error
```

Wrap your client call in a fallback so the output handler always receives something it can display. Log the real error separately for debugging — the fallback message is for the user, the exception is for you.

```python run
def safe_extract(response, fallback='Sorry, something went wrong.'):
    try:
        return response['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        return fallback

good = {'choices': [{'message': {'content': 'Four.'}}]}
bad  = {'error': 'rate_limit_exceeded'}

print(safe_extract(good))  # Four.
print(safe_extract(bad))   # Sorry, something went wrong.
```

## Putting It All Together

A complete AI app class wraps config, history, request building, and response parsing into one object. Each method does one job, and the class holds the shared state — model name and conversation history — so you do not pass it everywhere.

```python run
class SimpleAIApp:
    def __init__(self, model, system_prompt=None):
        self.model = model
        self.history = []
        if system_prompt:
            self.history.append({'role': 'system', 'content': system_prompt})

    def add_message(self, role, content):
        self.history.append({'role': role, 'content': content})
        return self

    def build_request(self, temperature=0.7):
        return {'model': self.model, 'messages': self.history, 'temperature': temperature}

    def parse_response(self, response):
        return response['choices'][0]['message']['content']

    def message_count(self):
        return len(self.history)

app = SimpleAIApp('gpt-4o-mini', system_prompt='You are helpful.')
app.add_message('user', 'What is 2 + 2?')
print(app.message_count())         # 2 — system + user
payload = app.build_request()
print(payload['model'])            # gpt-4o-mini
print(len(payload['messages']))    # 2
```

To actually call the LLM, pass the payload from `build_request()` to your HTTP client and feed the response back through `parse_response()`. Then call `add_message('assistant', reply)` so the exchange becomes part of the history for the next turn.

```python run
class SimpleAIApp:
    def __init__(self, model, system_prompt=None):
        self.model = model
        self.history = []
        if system_prompt:
            self.history.append({'role': 'system', 'content': system_prompt})

    def add_message(self, role, content):
        self.history.append({'role': role, 'content': content})
        return self

    def build_request(self, temperature=0.7):
        return {'model': self.model, 'messages': self.history, 'temperature': temperature}

    def parse_response(self, response):
        return response['choices'][0]['message']['content']

    def message_count(self):
        return len(self.history)

# Simulate a two-turn conversation without a real API
app = SimpleAIApp('gpt-4o-mini')
app.add_message('user', 'Hello')
app.add_message('assistant', 'Hi!')
app.add_message('user', 'How are you?')
print(app.message_count())  # 3
print(app.build_request()['messages'][-1]['content'])  # How are you?
```
