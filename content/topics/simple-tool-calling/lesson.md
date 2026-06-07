# Tool Calling and Function Use

LLMs are good at reasoning and generating text, but they cannot run code, check a database, or fetch live data on their own. Tool calling solves this: you give the LLM a list of functions it is allowed to call, and when the LLM decides one is needed, it returns a structured signal instead of a text answer. Your Python code reads that signal, runs the function, sends the result back, and the LLM produces a final answer that uses real data.

Think of tool calling like a manager delegating to specialists. The manager (LLM) understands the problem and knows which specialist to call — but the specialist (your Python function) does the actual work. The manager cannot fetch a weather report themselves; they ask the weather specialist, get the answer, and incorporate it into their response. Your code coordinates that handoff in both directions.

## 1. What Tool Calling Is

The LLM API supports an optional `tools` field in the request payload. Each tool is a dict describing a Python function — its name, what it does, and what parameters it expects. If the LLM decides a tool should be called, it returns a response with `tool_calls` instead of (or alongside) `content`. Your code then runs the function and sends the result back.

```python run
# A mock tool call response — what the LLM sends when it wants to call a function
response = {
    "choices": [{
        "message": {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "London"}'
                }
            }]
        },
        "finish_reason": "tool_calls"
    }]
}

message = response["choices"][0]["message"]
if message.get("tool_calls"):
    call = message["tool_calls"][0]
    print("Tool requested:", call["function"]["name"])
    print("Arguments string:", call["function"]["arguments"])
    print("Finish reason:", response["choices"][0]["finish_reason"])
```

`finish_reason: "tool_calls"` signals that the model stopped because it wants to invoke a tool, not because it finished answering. Your code must check for this and run the dispatch step before asking the model to continue.

## 2. Writing a Tool Schema

A tool schema is a dict that describes one function to the LLM. It has three parts: the function name (used to dispatch the call), a plain-English description (how the model decides when to use it), and a parameters object in JSON Schema format.

```python run
def make_tool_schema(name, description, properties, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            }
        }
    }

weather_tool = make_tool_schema(
    name="get_weather",
    description="Get the current weather for a city",
    properties={"city": {"type": "string", "description": "The city name"}},
    required=["city"],
)

print(weather_tool["function"]["name"])
print(weather_tool["function"]["description"])
print(weather_tool["function"]["parameters"]["required"])
```

The description is read by the LLM — write it for the model, not for other developers. Be specific: "Get the current temperature and conditions for a city" is better than "weather tool" because the model uses it to decide when to call the function.

## 3. Parsing a Tool Call Response

When the LLM decides to call a tool, `tool_calls` in the response message contains a list of call objects. Each call has a function name and an `arguments` string. The arguments are a JSON-encoded string — not a dict — so you must parse them with `json.loads` before passing them to your function.

```python run
import json

def parse_tool_call(tool_call):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    return {"name": name, "args": args}

tc = {
    "id": "call_abc",
    "function": {
        "name": "get_weather",
        "arguments": '{"city": "London", "units": "metric"}'
    }
}

parsed = parse_tool_call(tc)
print(parsed["name"])           # get_weather
print(parsed["args"]["city"])   # London
print(type(parsed["args"]))     # <class 'dict'>
```

```python run
import json

def is_tool_call(response_message):
    return bool(response_message.get("tool_calls"))

msg_with_tool = {"role": "assistant", "content": None, "tool_calls": [{"id": "x"}]}
msg_with_text = {"role": "assistant", "content": "Hello there!"}

print(is_tool_call(msg_with_tool))  # True
print(is_tool_call(msg_with_text))  # False
```

## 4. Dispatching to Python Functions

A dispatcher maps tool names to actual Python functions and calls the right one with the extracted arguments. The result must be converted to a string — the LLM API requires all message content to be strings.

```python run
import json

def dispatch(tool_call, registry):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    func = registry[name]
    return str(func(**args))

def add(a, b):
    return a + b

def greet(name):
    return f"Hello, {name}!"

registry = {"add": add, "greet": greet}

tc_add = {"function": {"name": "add", "arguments": '{"a": 3, "b": 4}'}}
tc_greet = {"function": {"name": "greet", "arguments": '{"name": "Alice"}'}}

print(dispatch(tc_add, registry))    # 7
print(dispatch(tc_greet, registry))  # Hello, Alice!
```

The dispatcher uses `**args` to unpack the parsed dict as keyword arguments. This means the LLM's argument names must exactly match your function's parameter names — another reason the schema description matters.

## 5. Returning Tool Results to the LLM

After running the function, you send the result back as a `"tool"` role message. This message must include the `tool_call_id` from the original request so the LLM can match it to the tool call it made.

```python run
def make_tool_result_message(tool_call_id, result):
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": str(result),
    }

tool_call_id = "call_abc123"
result_message = make_tool_result_message(tool_call_id, "72F, partly cloudy")
print(result_message)

# The full history you send back to the LLM
history = [
    {"role": "user", "content": "What is the weather in London?"},
    {"role": "assistant", "content": None, "tool_calls": [{"id": tool_call_id, "function": {"name": "get_weather", "arguments": '{"city": "London"}'}}]},
    result_message,
]

print(f"\nHistory length: {len(history)}")
print(f"Last role: {history[-1]['role']}")
```

The LLM then reads the conversation history — including the tool result — and generates a final natural language answer. The full loop is: user message → LLM decides to call tool → your code runs tool → tool result sent back → LLM generates final answer.

## 6. Multi-Tool Registries

Most real applications expose several tools. A registry object lets you register tools by name, dispatch any call, and list what is available — all in one place.

```python run
import json

class SimpleRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, func):
        self._tools[name] = func

    def dispatch(self, tool_call):
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        return str(self._tools[name](**args))

    def list_tools(self):
        return list(self._tools.keys())

reg = SimpleRegistry()
reg.register("add", lambda a, b: a + b)
reg.register("upper", lambda text: text.upper())

print(reg.list_tools())

tc1 = {"function": {"name": "add", "arguments": '{"a": 10, "b": 5}'}}
tc2 = {"function": {"name": "upper", "arguments": '{"text": "hello"}'}}

print(reg.dispatch(tc1))   # 15
print(reg.dispatch(tc2))   # HELLO
```

In production, registries also store tool schemas so they can be passed directly into the `tools` field of every API request. The capstone lab extends this pattern with schema storage alongside the function.
