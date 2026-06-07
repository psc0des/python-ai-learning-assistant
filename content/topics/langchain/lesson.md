# LangChain

LangChain is a framework for building applications powered by large language models (LLMs) like GPT or Claude. Without a framework, you quickly end up with tangled custom code for calling models, formatting prompts, handling tools, and parsing outputs — code that breaks every time a provider changes their API. LangChain gives you well-tested, interchangeable building blocks: models, prompts, tools, retrieval, and output parsers.

Think of LangChain like a professional kitchen with stations. The model is the chef. The prompt template is the recipe card. Tools are specialist stations (the grill, the fryer, a search engine). Retrieval brings fresh ingredients from the larder (your document store). Structured output ensures the dish arrives in the right container (a JSON object, not free prose). You, as the developer, design the kitchen layout — which stations exist, how data flows between them, and what happens when something goes wrong.

## 1. What LangChain Solves — The Problem First

Without LangChain, building an LLM application looks like this: call the OpenAI API directly, format a prompt manually, parse the response text, then redo all of this differently for Anthropic, add retry logic, add logging, add tool calling... every project reinvents the same glue code.

LangChain gives you standard building blocks so you can focus on the interesting part — what the application does — rather than re-implementing model integrations.

```python
# Without LangChain — direct API call, lots of manual work:
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Summarise this: ...' + document}]
)
summary = response.choices[0].message.content

# With LangChain — swappable, composable, observable:
from langchain.chat_models import init_chat_model
model = init_chat_model('openai:gpt-4o-mini')  # or 'anthropic:claude-3-5-haiku'
response = model.invoke('Summarise this: ' + document)
print(response.content)
```

The key benefit: if you want to switch from OpenAI to Anthropic, you change one line. The rest of your code stays the same because both implement the same interface.

## 2. Models and Prompt Templates

A **prompt template** is a reusable text pattern with variable slots — like a form with blanks to fill in. Instead of building prompt strings with messy string concatenation, templates keep your prompts clean, readable, and testable.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

model = init_chat_model('openai:gpt-4o-mini')

# Define a reusable template with {variables}
prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a helpful assistant specialising in {domain}.'),
    ('user', 'Explain {topic} in simple terms for a beginner.'),
])

# Fill in the variables and call the model
chain = prompt | model   # '|' composes prompt → model into a pipeline
result = chain.invoke({'domain': 'Python', 'topic': 'decorators'})
print(result.content)
```

**Why templates matter:**
- Prompts are code — they should be version-controlled, not scattered as f-strings
- Templates make it easy to test prompts independently from the model
- The `|` operator chains components: `prompt | model | output_parser` is a full pipeline

**Good prompt design** is often more impactful than model choice. Clear instructions, relevant examples, and specific output format guidance all improve quality significantly.

## 3. Tools — Giving the Model Capabilities

By default, an LLM can only generate text. **Tools** extend the model with real capabilities: searching the web, querying a database, calling an internal API, reading a file. The model decides which tool to call based on the user's request.

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Return current weather for a city. Use when the user asks about weather."""
    # In real code, this would call a weather API
    return f'Sunny, 22 degrees in {city}'

@tool
def calculator(expression: str) -> str:
    """Add, subtract, multiply, or divide two numbers: '15 * 7', '100 / 4'."""
    for sym, fn in [('+', float.__add__), ('-', float.__sub__),
                    ('*', float.__mul__), ('/', float.__truediv__)]:
        if sym in expression:
            left, right = expression.split(sym, 1)
            try:
                return str(fn(float(left), float(right)))
            except (ValueError, ZeroDivisionError) as e:
                return f'Error: {e}'
    return 'Error: use format like "15 * 7"'

# Bind tools to a model:
model_with_tools = model.bind_tools([get_weather, calculator])
response = model_with_tools.invoke('What is the weather in Tokyo and what is 15 * 7?')
```

**Safety rules for tools:**
1. Give every tool the **minimum permissions** it needs — read-only where possible
2. **Log every tool call** — what was called, what args, what result
3. For destructive actions (delete, update, send), add a **human approval step**
4. Never expose a tool that can run arbitrary code or access sensitive systems without guardrails

## 4. Agents vs Chains — Choose Deliberately

This is one of the most important design decisions in LangChain apps, and many developers default to agents when a simple chain would do the job better.

**A chain** is a fixed pipeline: step A → step B → step C, always in that order. Predictable, fast, easy to test and debug.

**An agent** lets the model decide what to do next at each step — which tool to call, whether to loop, when to finish. Flexible, but harder to predict, debug, and control.

```python
# Chain — fixed, deterministic pipeline:
from langchain_core.output_parsers import StrOutputParser

chain = prompt | model | StrOutputParser()
result = chain.invoke({'topic': 'Python lists', 'domain': 'programming'})
# Runs exactly: prompt → model → parse output. Always.

# Agent — model decides what to do (current approach via LangGraph's prebuilt harness):
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model, tools=[get_weather, calculator])
result = agent.invoke({'messages': [('user', 'What is 15*7 and is it hot in London?')]})
# Model might call calculator, then get_weather, then respond. Or in different order.
```

**Decision guide:**
- Is the flow always the same steps in the same order? → **Use a chain**
- Does the model need to choose between multiple tools or retry dynamically? → **Use an agent**
- Start simple. Add agent complexity only when chains genuinely cannot solve the problem.

## 5. Retrieval-Augmented Generation (RAG) Basics

LLMs have a knowledge cutoff — they cannot answer questions about your company's internal documents, recent events, or private data. **RAG** (Retrieval-Augmented Generation) solves this by fetching relevant documents at query time and including them in the prompt as context.

**The RAG pipeline:**
1. **Index**: convert your documents into embeddings and store them in a vector database
2. **Retrieve**: when a question arrives, find the most relevant document chunks
3. **Generate**: send the question + retrieved chunks to the model to get a grounded answer

```python
# Simplified RAG conceptual example
from langchain_core.prompts import ChatPromptTemplate

rag_prompt = ChatPromptTemplate.from_template("""
Answer the question using ONLY the provided context.
If the answer is not in the context, say 'I don't know.'

Context:
{context}

Question: {question}
""")

# In a real app:
# 1. retrieved_docs = vector_store.similarity_search(question, k=4)
# 2. context = '\n\n'.join([doc.page_content for doc in retrieved_docs])
# 3. answer = (rag_prompt | model).invoke({'context': context, 'question': question})
```

**Why retrieval quality matters as much as the model:** if you retrieve the wrong chunks, the model will either give a wrong answer or say 'I don't know' — even if the answer exists somewhere in your database. Good chunking strategy and metadata filtering are just as important as the model you choose.

## 6. Structured Output — Machine-Readable Responses

Free-form LLM text output is great for humans but terrible for code. If you need to extract specific fields — a sentiment label, a list of extracted names, a confidence score — you either parse unreliable text or use structured output.

LangChain's `with_structured_output()` forces the model to return data that matches a Pydantic schema instead of freeform prose.

```python
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

model = init_chat_model('openai:gpt-4o-mini')

# Define what you want back
class SupportTicketClassification(BaseModel):
    category: str = Field(description='One of: billing, technical, account, general')
    urgency: int = Field(ge=1, le=5, description='1=low, 5=critical')
    summary: str = Field(description='One sentence summary of the issue')
    needs_human: bool = Field(description='True if this requires a human agent')

# Model returns a validated Pydantic object, not a string:
classifier = model.with_structured_output(SupportTicketClassification)

ticket_text = 'My payment failed 3 times and my account is locked. Urgent!'
result = classifier.invoke(f'Classify this support ticket: {ticket_text}')

print(result.category)      # 'billing'
print(result.urgency)       # 5
print(result.needs_human)   # True
```

Structured output eliminates brittle regex parsing, gives you validated field types, and makes your LLM pipeline as reliable as any other typed API.
