# LangGraph

LangChain handles single calls to a model. LangGraph handles multi-step workflows where an AI system needs to make decisions, take actions, check results, and loop back — all while remembering what it has done so far. Think of it as the difference between a single chess move and an entire chess game. LangGraph is the tool that lets you build AI agents that can pause for human approval, resume after an interruption, branch in different directions based on conditions, and keep an auditable record of every step.

Picture a flowchart that can remember its state. A LangGraph workflow is a directed graph: each box is a node (a unit of work like 'classify the alert' or 'draft a response'), each arrow is an edge (the path to the next node), and a shared state dictionary carries all the data between nodes. Unlike a simple chain which always goes A→B→C, LangGraph supports conditional routing (if severity is high, go to node X; otherwise go to node Y), loops, and pause points where a human can review before the workflow continues.

## 1. Why LangGraph? — Beyond Simple Chains

A simple LangChain chain is like a one-way street: input flows through steps A → B → C and you get an output. That is fine for many tasks. But real-world AI workflows need more:

- **Branching** — if the model is uncertain, escalate to a human; if confident, proceed
- **Loops** — retry if a tool call failed; gather more data if context is insufficient
- **State** — remember what happened 5 steps ago to inform the decision at step 10
- **Pause and resume** — stop for human approval, then continue when approved

**When to use LangGraph vs a simple chain:**

```
Simple Q&A answer           → LangChain chain
Fixed-step data pipeline    → LangChain chain
Multi-step triage workflow  → LangGraph
Agent with retry + approval → LangGraph
Long-running background job → LangGraph
```

LangGraph is not a replacement for chains — it is the tool you reach for when workflows need state, branching, or persistence that chains cannot express cleanly.

## 2. State, Nodes, and Edges — The Core Model

Every LangGraph workflow has three fundamental parts:

**State** — a shared dictionary (or typed dataclass) that all nodes can read from and write to. It carries the evolving data across the entire workflow.

**Nodes** — Python functions. Each node receives the current state, does work (calls a model, runs a tool, applies logic), and returns a partial state update.

**Edges** — connections between nodes that define what runs next.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# Define the shared state — everything the workflow needs to track
class TicketState(TypedDict):
    ticket_text: str
    category: str        # filled in by 'classify' node
    urgency: int         # filled in by 'classify' node
    response_draft: str  # filled in by 'draft_response' node
    approved: bool       # set by human approval step

# Nodes are plain functions that return partial state updates
def classify(state: TicketState) -> dict:
    # In real code, call an LLM here
    return {'category': 'billing', 'urgency': 3}

def draft_response(state: TicketState) -> dict:
    # In real code, call an LLM with state['category'] and state['ticket_text']
    return {'response_draft': 'Thank you for contacting billing support...'}

# Build the graph
graph_builder = StateGraph(TicketState)
graph_builder.add_node('classify', classify)
graph_builder.add_node('draft_response', draft_response)
graph_builder.add_edge('classify', 'draft_response')  # classify always leads to draft
graph_builder.add_edge('draft_response', END)
graph_builder.set_entry_point('classify')

graph = graph_builder.compile()
```

The state design is the most important architectural decision — it becomes the contract that every node works with.

## 3. Conditional Routing — Making Decisions

Conditional edges let the workflow choose its next step based on the current state. This is how you express 'if urgency is high, escalate; otherwise, auto-reply.'

```python
from langgraph.graph import StateGraph, END

# A routing function looks at state and returns the name of the next node
def route_by_urgency(state: TicketState) -> str:
    if state['urgency'] >= 4:
        return 'escalate_to_human'   # high urgency → human
    else:
        return 'auto_reply'          # low urgency → automated response

# Add nodes for each possible path
graph_builder.add_node('escalate_to_human', escalate_fn)
graph_builder.add_node('auto_reply', auto_reply_fn)

# Add a conditional edge — the routing function decides which node runs next
graph_builder.add_conditional_edges(
    'classify',              # FROM this node
    route_by_urgency,        # CALL this function to decide
    {
        'escalate_to_human': 'escalate_to_human',  # map return value → node name
        'auto_reply': 'auto_reply',
    }
)
```

**Why this matters:** the decision logic is explicit, testable Python code — not buried inside a large prompt. You can unit-test `route_by_urgency` independently, and you can trace exactly why the workflow took a particular path in any given run.

## 4. Persistence and Thread IDs — Remembering Runs

A regular function forgets everything when it returns. A LangGraph workflow with persistence saves its state at every checkpoint, so a long-running job can be paused, resumed days later, or replayed for debugging.

**Thread IDs** are the key: each run gets a unique thread ID, and you use the same ID to resume that specific run later.

```python
from langgraph.checkpoint.memory import MemorySaver

# Add a checkpointer when compiling the graph
checkpointer = MemorySaver()  # in production, use a database-backed checkpointer
graph = graph_builder.compile(checkpointer=checkpointer)

# Start a run with a thread ID
config = {'configurable': {'thread_id': 'ticket-run-001'}}
initial_input = {'ticket_text': 'My invoice is wrong and I need help urgently'}

result = graph.invoke(initial_input, config=config)

# Later — resume the SAME run after a crash or restart (it loads from checkpoint):
resume_result = graph.invoke(None, config=config)  # same thread_id — picks up where it left off
```

**Practical value:** if a long workflow crashes halfway through (a network error, a timeout), you do not start from scratch. You resume from the last checkpoint. For expensive LLM pipelines, this saves both time and cost.

## 5. Human-in-the-Loop — Safe Pausing

AI agents can make mistakes. For high-impact actions — deleting records, sending emails, restarting services, charging customers — you want a human to review and approve before the action executes.

LangGraph's **interrupt** mechanism pauses the workflow at a specific node, surfaces the current state to a human, waits for their decision, then resumes.

```python
from langgraph.types import interrupt, Command

def review_and_approve(state: TicketState) -> dict:
    # This pauses the workflow and returns control to the caller
    # The caller (your API, your UI) sees the current state and waits
    decision = interrupt({
        'message': 'Please review this response before sending',
        'draft': state['response_draft'],
        'ticket': state['ticket_text'],
    })
    # When the human resumes the run, 'decision' contains their input
    return {'approved': decision.get('approve', False)}

# After adding this node and its edges:
# 1. graph.invoke(input, config)    → runs until interrupt, returns current state
# 2. human reviews state in your UI
# 3. graph.invoke(Command(resume={'approve': True}), config) → resumes the paused interrupt()
```

**Safety principle:** any action that cannot be easily undone (send, delete, deploy, charge) should have a human-in-the-loop interrupt before it runs. This is not a limitation — it is a design choice that makes AI systems trustworthy enough to use in production.

## 6. Streaming and Observability

A multi-step workflow that silently runs for 30 seconds and then returns an answer is a poor user experience — and a debugging nightmare. Streaming lets you see what is happening at each node in real time.

```python
# Stream node-by-node updates as the graph runs
for event in graph.stream(initial_input, config=config):
    for node_name, output in event.items():
        print(f'[{node_name}] produced:', output)

# Example output:
# [classify] produced: {'category': 'billing', 'urgency': 4}
# [escalate_to_human] produced: {'response_draft': 'Escalating to billing team...'}
# [review_and_approve] produced: INTERRUPT (waiting for human)
```

**Why observability matters for AI workflows:**
- A wrong final answer could have come from a bad classification, weak retrieval, a failed tool call, or poor prompt. Without step-by-step visibility, you cannot tell which.
- Checkpoints + streaming = full audit trail: every input, every state transition, every decision
- When a run fails or produces a bad result, replay the exact run from its checkpoint to debug step by step

**Production habit:** log the full state at each node. The cost of storing this data is tiny compared to the debugging time saved when something goes wrong.

## 7. Try The Real Library

The labs in this topic build graph workflow ideas in pure Python so state, nodes, edges, and history are visible. The real LangGraph library gives you a production graph runtime for those same concepts:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U langgraph
python graph_demo.py
```

Save this as `graph_demo.py`:

```python
from typing import TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    question: str
    route: str
    answer: str

def classify(state: State):
    route = 'policy' if 'policy' in state['question'].lower() else 'general'
    return {'route': route}

def answer(state: State):
    return {'answer': f"Handled by {state['route']} route"}

graph = StateGraph(State)
graph.add_node('classify', classify)
graph.add_node('answer', answer)
graph.add_edge(START, 'classify')
graph.add_edge('classify', 'answer')
graph.add_edge('answer', END)
app = graph.compile()

result = app.invoke({'question': 'What is the refund policy?', 'route': '', 'answer': ''})
print(result['answer'])
```

Compare this with the pure-Python graph lab: the names changed, but the mental model did not. You still define state, register nodes, connect edges, compile the graph, and invoke it with input.
