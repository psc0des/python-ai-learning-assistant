# MCP

Every AI assistant needs to connect to the outside world — to search documentation, query a database, call an API, or read files. Without a standard, every team builds its own custom integration for every assistant and every data source — a combinatorial explosion of brittle glue code. Model Context Protocol (MCP) is the standard that solves this: a common language for AI applications to discover and use external capabilities in a controlled, auditable way.

Think of MCP like a USB standard for AI capabilities. Before USB, every device needed a proprietary cable — printers, cameras, keyboards each had their own connectors. USB standardised the interface so any device could connect to any computer. MCP does the same for AI: any assistant (host) can connect to any capability provider (MCP server) using a standard protocol, without custom integration code.

## 1. The Three Roles — Host, Client, Server

MCP separates concerns across three roles. Understanding who does what is the foundation for designing correct MCP integrations.

**Host** — the AI application the user interacts with. Examples: Claude Desktop, a coding assistant, a support chatbot. The host manages user experience and decides which MCP servers to connect to.

**Client** — the MCP protocol layer running inside the host. It speaks the MCP message format, handles connection lifecycle, and routes requests to the appropriate server.

**Server** — a separate process or service that exposes capabilities (tools, resources, prompts) through the MCP protocol.

```
User
  ↓
Host App (e.g. Claude Desktop)
  ↓ (via MCP Client)
MCP Server A: repository-search
MCP Server B: ticket-system
MCP Server C: documentation-db
```

The key insight: the host does not directly call the repository search API. It goes through the MCP Client, which contacts the MCP Server, which calls the API. This indirection enables standardised discovery, logging, and permission boundaries.

**Why separate servers?** You can give different servers different permission levels. Your documentation server might be read-only. Your ticket server might allow creating tickets but not deleting them. Your deployment server might require human approval before any action runs.

## 2. Capability Types — Tools, Resources, Prompts

An MCP server exposes three types of capabilities. Each has a distinct purpose and appropriate security posture.

**Tool** — a callable action with a defined input schema. The model can invoke a tool to do something: search, create, update, delete. Tools are the most powerful and most risky capability type.

**Resource** — read-only access to a data object: a document, a file, a database query result. Resources are safer than tools because they cannot modify state.

**Prompt** — a reusable template the model can load and use. Prompts help standardise how the model approaches recurring tasks.

```
Example server capability surface:

Tool:     search_tickets(query: str, limit: int) → list of tickets
Tool:     create_ticket(title: str, priority: int) → ticket ID
Resource: /docs/onboarding-guide → text content of the document
Resource: /runbooks/incident-response → text content
Prompt:   'bug-report-template' → structured prompt for filing bugs
```

**Design principle:** always start with the least powerful capability type. If a resource provides what the model needs, do not create a tool. If a read tool is enough, do not add write access.

```python
# Conceptual tool definition (using MCP Python SDK):
from mcp.server import Server
from mcp.types import Tool

server = Server('ticket-server')

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name='search_tickets',
            description='Search open support tickets by keyword',
            inputSchema={
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'limit': {'type': 'integer', 'default': 10, 'maximum': 50}
                },
                'required': ['query']
            }
        )
    ]
```

## 3. Capability Discovery — Explicit, Not Assumed

When an MCP client first connects to a server, it does not assume what capabilities exist. It **discovers** them through a standardised handshake.

This is important because:
- Different environments may have different servers with different capability sets
- A host can adapt its behaviour based on what is actually available
- Capability discovery creates an audit trail: you know what was offered and what was used

**The connection lifecycle:**

```
1. initialize       → client tells server its capabilities and protocol version
2. initialized      → server confirms, shares its own capabilities
3. tools/list       → client discovers available tools
4. resources/list   → client discovers available resources
5. tools/call       → client invokes a specific tool with arguments
6. resources/read   → client reads a specific resource
7. [work happens]
8. connection ends  → clean shutdown
```

Because discovery is explicit, a host can gracefully handle 'this server does not have a search tool' rather than crashing. It can also present the user with a meaningful message: 'I do not have access to the ticket system in this environment.'

## 4. Tool Contracts — Input Schema and Safe Execution

Every MCP tool must have a clear input schema that defines what arguments it accepts, their types, and which are required. This schema is what the model sees when deciding how to call the tool — a good schema prevents the model from sending malformed requests.

**What makes a good tool contract:**

```python
# GOOD tool definition — clear, constrained, defensive:
{
    'name': 'create_ticket',
    'description': 'Create a new support ticket. Use only when the user explicitly asks to create a ticket.',
    'inputSchema': {
        'type': 'object',
        'properties': {
            'title':    {'type': 'string', 'minLength': 5, 'maxLength': 200},
            'priority': {'type': 'integer', 'minimum': 1, 'maximum': 5},
            'category': {'type': 'string', 'enum': ['billing', 'technical', 'account']},
        },
        'required': ['title', 'priority', 'category']
    }
}

# BAD tool definition — too broad, no constraints:
{
    'name': 'do_thing',
    'description': 'Does stuff',
    'inputSchema': {'type': 'object'}  # accepts anything — dangerous
}
```

**On the server side, always validate inputs even if they passed schema checking** — never trust that the client validated correctly. Treat tool arguments the same way you treat user input in a web API.

## 5. Security — Least Privilege by Design

MCP servers run with real access to real systems. A server connected to your ticket system, repository, or deployment pipeline can cause real damage if compromised or misused. Security is not an add-on — it must be designed in from the start.

**The least-privilege principle in practice:**

```
WRONG — one monolithic server with all permissions:
super-server:
  - read all files
  - write all files
  - delete any record
  - deploy to production
  - send emails

RIGHT — separate servers with minimal scopes:
docs-server:       read docs and runbooks only
ticket-server:     create/read tickets, no delete
deployment-server: read deploy status, no execute without human approval
```

**Rules for safe MCP server design:**
1. **Read before write** — if read-only access is enough, do not add write tools
2. **Validate every argument** — check types, lengths, allowed values server-side
3. **Require approval for high-impact actions** — any action that cannot be easily undone needs a human gate
4. **No tool should accept arbitrary code or shell commands** — this is a critical injection risk
5. **Scope secrets tightly** — the deployment server's API key should not be accessible to the documentation server

```python
# Example approval gate pattern:
async def deploy_service(service: str, environment: str):
    if environment == 'production':
        # Return an approval-needed response instead of executing
        return {'status': 'pending_approval', 'action': f'deploy {service} to production'}
    # staging is safe to proceed without approval
    return await do_deploy(service, environment)
```

## 6. Observability — Logging and Auditing Tool Use

When an AI model calls a tool and produces an unexpected result, how do you debug it? Without logs, you only have the final answer. With proper observability, you can trace every decision.

**What to log for every tool call:**

```python
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger('mcp.tool-calls')

async def handle_tool_call(tool_name: str, arguments: dict, session_id: str):
    start_time = datetime.now(timezone.utc)
    log_entry = {
        'session_id': session_id,
        'tool': tool_name,
        'arguments': arguments,     # what the model sent
        'timestamp': start_time.isoformat(),
    }
    try:
        result = await execute_tool(tool_name, arguments)
        log_entry['result_summary'] = str(result)[:200]  # abbreviated
        log_entry['status'] = 'success'
        return result
    except Exception as exc:
        log_entry['status'] = 'error'
        log_entry['error'] = str(exc)
        raise
    finally:
        log_entry['duration_ms'] = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.info(json.dumps(log_entry))
```

**Why this matters:** if an AI system takes an unintended action, your logs let you reconstruct: which session called it, with what arguments, at what time, and what result was returned. This is the difference between 'the assistant did something strange' and 'the assistant called create_ticket with these exact args at 14:32, here is the evidence.'
