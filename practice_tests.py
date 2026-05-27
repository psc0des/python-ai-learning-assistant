PRACTICE_TESTS = [
    {
        "topic_id": "python-basics",
        "questions": [
            {
                "question": "Which statement best explains Python assignment?",
                "options": [
                    "A name is bound to an object.",
                    "A variable permanently stores one fixed type.",
                    "Assignment copies every object by default.",
                    "A name can only point to strings or numbers.",
                ],
                "answer": 0,
                "explanation": "The official tutorial introduces assignment with `=`, which binds a name so it can be used later. The value has the type, not the name itself.",
            },
            {
                "question": "What does `17 // 3` return?",
                "options": [
                    "5",
                    "5.666666666666667",
                    "2",
                    "6",
                ],
                "answer": 0,
                "explanation": "`//` performs floor division, so it discards the fractional part. `/` would return a float, and `%` would return the remainder.",
            },
            {
                "question": "Why does `word[0] = 'J'` fail when `word` is a string?",
                "options": [
                    "Strings are immutable, so indexed characters cannot be assigned.",
                    "Strings cannot be indexed in Python.",
                    "The first index in Python is 1, not 0.",
                    "Single-letter strings are not allowed.",
                ],
                "answer": 0,
                "explanation": "Strings support indexing and slicing, but they cannot be changed in place. Create a new string when you need different text.",
            },
            {
                "question": "What does slicing a list usually return?",
                "options": [
                    "A new list containing the selected items.",
                    "The original list permanently shortened.",
                    "Only one item.",
                    "A dictionary of index positions.",
                ],
                "answer": 0,
                "explanation": "Lists are sequences, so indexing returns one item while slicing returns a new list with the selected range.",
            },
            {
                "question": "What does `for i in range(3)` produce?",
                "options": [
                    "0, 1, 2",
                    "1, 2, 3",
                    "0, 1, 2, 3",
                    "3, 2, 1",
                ],
                "answer": 0,
                "explanation": "range(3) produces integers from 0 up to (but not including) 3.",
            },
            {
                "question": "Which statement best describes `pass`?",
                "options": [
                    "It does nothing and can act as a placeholder where syntax requires a statement.",
                    "It exits the current loop immediately.",
                    "It skips the next loop iteration.",
                    "It returns None from every function.",
                ],
                "answer": 0,
                "explanation": "The Python Tutorial describes `pass` as a statement that does nothing, useful as a placeholder while sketching code.",
            },
            {
                "question": "What happens when a function reaches the end without a `return` statement?",
                "options": [
                    "It returns None.",
                    "It returns the last variable assigned.",
                    "It prints the last expression.",
                    "It raises NameError.",
                ],
                "answer": 0,
                "explanation": "A function without a return value returns None. This is why labs usually ask you to return values rather than only print them.",
            },
            {
                "question": "What error do you expect from reading a name before assigning it?",
                "options": [
                    "NameError",
                    "IndexError",
                    "TypeError",
                    "ZeroDivisionError",
                ],
                "answer": 0,
                "explanation": "The tutorial shows that trying to access an undefined variable raises NameError.",
            },
        ],
    },
    {
        "topic_id": "data-structures",
        "questions": [
            {
                "question": "Which container is usually best for checking whether an item was already seen?",
                "options": ["set", "list", "tuple", "string"],
                "answer": 0,
                "explanation": "A set is designed for uniqueness and fast O(1) membership checks.",
            },
            {
                "question": "What happens if you use a list as a dictionary key?",
                "options": [
                    "Python raises a TypeError because lists are not hashable.",
                    "The list is automatically converted to a tuple.",
                    "It works fine.",
                    "Python silently ignores the entry.",
                ],
                "answer": 0,
                "explanation": "Dictionary keys must be hashable. Lists are mutable and therefore not hashable.",
            },
            {
                "question": "Which method safely gets a value from a dict without raising KeyError?",
                "options": [
                    "dict.get(key, default)",
                    "dict[key]",
                    "dict.find(key)",
                    "dict.fetch(key)",
                ],
                "answer": 0,
                "explanation": "dict.get() returns the default value (or None) if the key doesn't exist, instead of raising KeyError.",
            },
            {
                "question": "What is the main advantage of a tuple over a list?",
                "options": [
                    "Tuples are immutable, making them safe as dict keys and for fixed data.",
                    "Tuples are always faster than lists.",
                    "Tuples can hold more elements.",
                    "Tuples support more methods.",
                ],
                "answer": 0,
                "explanation": "Immutability means tuples can be used as dict keys and in sets. They also signal that the data should not change.",
            },
            {
                "question": "What does `{1, 2, 3} & {2, 3, 4}` return?",
                "options": [
                    "{2, 3} — the intersection of both sets.",
                    "{1, 2, 3, 4} — the union.",
                    "{1, 4} — elements in only one set.",
                    "An error because & doesn't work on sets.",
                ],
                "answer": 0,
                "explanation": "The & operator returns the intersection — elements present in both sets.",
            },
        ],
    },
    {
        "topic_id": "functions",
        "questions": [
            {
                "question": "Why should functions usually return values instead of only printing?",
                "options": [
                    "Returned values are easier to test and reuse.",
                    "Printing is not allowed in Python.",
                    "Return statements make code run in parallel.",
                    "Printing changes the type of the value.",
                ],
                "answer": 0,
                "explanation": "A returned value can be asserted in tests and used by other code. Print only displays text.",
            },
            {
                "question": "What problem can `def add_item(item, items=[])` cause?",
                "options": [
                    "The default list is shared across all calls, accumulating items unexpectedly.",
                    "Python does not allow lists as defaults.",
                    "The function will always return an empty list.",
                    "The function cannot accept more than one argument.",
                ],
                "answer": 0,
                "explanation": "Mutable default arguments (like []) are created once and shared between calls. Use None as default and create a new list inside the function.",
            },
            {
                "question": "What is the difference between a parameter and an argument?",
                "options": [
                    "A parameter is the name in the function definition; an argument is the actual value passed.",
                    "They are the same thing.",
                    "A parameter is always a string; an argument is always a number.",
                    "An argument is in the definition; a parameter is the value passed.",
                ],
                "answer": 0,
                "explanation": "Parameters are defined in the function signature. Arguments are the actual values supplied when calling the function.",
            },
            {
                "question": "What does `*args` do in a function definition?",
                "options": [
                    "Collects extra positional arguments into a tuple.",
                    "Makes all arguments required.",
                    "Multiplies all arguments together.",
                    "Collects keyword arguments into a dictionary.",
                ],
                "answer": 0,
                "explanation": "*args collects additional positional arguments into a tuple. **kwargs collects keyword arguments into a dictionary.",
            },
            {
                "question": "What does a function return if there is no return statement?",
                "options": [
                    "None",
                    "0",
                    "An empty string",
                    "It raises an error.",
                ],
                "answer": 0,
                "explanation": "A function without a return statement (or with a bare return) implicitly returns None.",
            },
        ],
    },
    {
        "topic_id": "oop",
        "questions": [
            {
                "question": "What does `self` refer to inside an instance method?",
                "options": [
                    "The current instance.",
                    "The parent class only.",
                    "The Python interpreter.",
                    "A global variable created automatically.",
                ],
                "answer": 0,
                "explanation": "`self` is the instance whose method is currently running.",
            },
            {
                "question": "When should you prefer composition over inheritance?",
                "options": [
                    "When you want to combine behaviors from multiple sources without deep hierarchies.",
                    "Never — inheritance is always better.",
                    "Only when you have exactly two classes.",
                    "Composition is not a real design pattern.",
                ],
                "answer": 0,
                "explanation": "Composition ('has-a') is often simpler and more flexible than inheritance ('is-a'). It avoids deep class hierarchies.",
            },
            {
                "question": "What is a dataclass useful for?",
                "options": [
                    "Classes that mainly hold data with auto-generated __init__ and __repr__.",
                    "Classes that never have any attributes.",
                    "Replacing all functions with objects.",
                    "Making code run faster automatically.",
                ],
                "answer": 0,
                "explanation": "Dataclasses reduce boilerplate when a class is primarily a container for structured data.",
            },
            {
                "question": "What happens if you forget `self` in a method definition?",
                "options": [
                    "Calling the method raises a TypeError about unexpected arguments.",
                    "Python automatically adds self.",
                    "The method works but cannot access instance data.",
                    "Python raises a SyntaxError.",
                ],
                "answer": 0,
                "explanation": "Python passes the instance as the first argument. Without self in the signature, the call fails with a TypeError.",
            },
            {
                "question": "What does `__init__` do?",
                "options": [
                    "Initializes a new instance by setting up its attributes.",
                    "Destroys the instance.",
                    "Creates the class itself.",
                    "Defines class-level constants.",
                ],
                "answer": 0,
                "explanation": "__init__ is called when a new instance is created. It sets up the instance's initial state.",
            },
        ],
    },
    {
        "topic_id": "errors-testing",
        "questions": [
            {
                "question": "What is the safest first step when Python raises a traceback?",
                "options": [
                    "Read the exception type and failing line.",
                    "Delete the function and start again.",
                    "Catch all exceptions with bare `except`.",
                    "Ignore the traceback if the code sometimes works.",
                ],
                "answer": 0,
                "explanation": "The exception type and line number usually tell you where to begin debugging.",
            },
            {
                "question": "Why is bare `except:` considered bad practice?",
                "options": [
                    "It catches all exceptions, hiding real bugs and making debugging harder.",
                    "It is slower than catching specific exceptions.",
                    "It only catches SyntaxErrors.",
                    "Python does not allow bare except blocks.",
                ],
                "answer": 0,
                "explanation": "Bare except catches everything — including KeyboardInterrupt and SystemExit — hiding real bugs.",
            },
            {
                "question": "Which inputs should you test beyond the 'happy path'?",
                "options": [
                    "Empty input, None, zero, duplicates, negative numbers, and boundary values.",
                    "Only the example from the problem statement.",
                    "Only very large numbers.",
                    "No extra cases — if the main case works, it's fine.",
                ],
                "answer": 0,
                "explanation": "Edge cases reveal bugs that normal inputs miss. Good tests cover empty, zero, negative, duplicate, and boundary values.",
            },
            {
                "question": "What does `assert x > 0` do?",
                "options": [
                    "Raises AssertionError if x is not greater than 0.",
                    "Prints whether x is greater than 0.",
                    "Sets x to a positive value.",
                    "Does nothing — assert is a comment.",
                ],
                "answer": 0,
                "explanation": "assert evaluates the condition and raises AssertionError if it is False. It documents and enforces expected behavior.",
            },
            {
                "question": "What is the recommended debugging approach?",
                "options": [
                    "Change one thing at a time, reproduce, hypothesize, test.",
                    "Change many things at once and hope it works.",
                    "Delete all code and start from scratch.",
                    "Ignore errors and add more features.",
                ],
                "answer": 0,
                "explanation": "Systematic debugging — isolate, hypothesize, test one change — finds bugs faster than random changes.",
            },
        ],
    },
    {
        "topic_id": "fastapi",
        "questions": [
            {
                "question": "What does FastAPI commonly use Pydantic models for?",
                "options": [
                    "Request and response validation.",
                    "Replacing the web server.",
                    "Creating Git commits.",
                    "Running shell commands.",
                ],
                "answer": 0,
                "explanation": "FastAPI uses Pydantic models to validate and document structured data at API boundaries.",
            },
            {
                "question": "What HTTP method should a 'create new resource' endpoint use?",
                "options": [
                    "POST",
                    "GET",
                    "DELETE",
                    "HEAD",
                ],
                "answer": 0,
                "explanation": "POST is the standard method for creating new resources. GET reads, PUT/PATCH updates, DELETE removes.",
            },
            {
                "question": "What does a 422 status code typically mean in FastAPI?",
                "options": [
                    "The request body failed validation (unprocessable entity).",
                    "The server is down.",
                    "The resource was successfully created.",
                    "The user is not authenticated.",
                ],
                "answer": 0,
                "explanation": "FastAPI returns 422 when Pydantic validation fails on the request data.",
            },
            {
                "question": "Why should you keep route handler functions thin?",
                "options": [
                    "So business logic can be tested independently without starting the server.",
                    "FastAPI crashes if handlers are too long.",
                    "Python functions have a line limit.",
                    "Thin handlers run faster.",
                ],
                "answer": 0,
                "explanation": "Separating business logic from route handlers makes the logic testable and reusable.",
            },
            {
                "question": "When does an async route handler help performance?",
                "options": [
                    "When the handler awaits I/O like database queries or HTTP calls.",
                    "Always — async is always faster.",
                    "When doing heavy math calculations.",
                    "Only when using GET requests.",
                ],
                "answer": 0,
                "explanation": "Async routes help when the handler awaits I/O. CPU-bound work needs a different approach (e.g., run_in_executor).",
            },
        ],
    },
    {
        "topic_id": "pydantic",
        "questions": [
            {
                "question": "Which phrase best describes Pydantic?",
                "options": [
                    "A data validation and serialization library.",
                    "A database engine.",
                    "A frontend rendering framework.",
                    "A shell scripting language.",
                ],
                "answer": 0,
                "explanation": "Pydantic validates input data into typed Python objects and serializes models back to data formats.",
            },
            {
                "question": "Where should you apply Pydantic validation?",
                "options": [
                    "At trust boundaries: HTTP requests, config files, API responses, queue messages.",
                    "Only inside private helper functions.",
                    "Never — Python types are enough.",
                    "Only for database schemas.",
                ],
                "answer": 0,
                "explanation": "Validation at boundaries catches bad data early, before it reaches business logic.",
            },
            {
                "question": "What does `Field(ge=1, le=5)` do in a Pydantic model?",
                "options": [
                    "Constrains the field to values between 1 and 5, inclusive.",
                    "Sets the field to always equal 1 or 5.",
                    "Makes the field optional.",
                    "Creates a list of 5 elements.",
                ],
                "answer": 0,
                "explanation": "ge (greater-or-equal) and le (less-or-equal) define numeric range constraints.",
            },
            {
                "question": "What is the difference between Optional[str] and a field with a default?",
                "options": [
                    "Optional[str] allows None; a default provides a value when the field is omitted.",
                    "They are the same thing.",
                    "Optional makes the field required.",
                    "Defaults cannot be used with Pydantic.",
                ],
                "answer": 0,
                "explanation": "Optional[str] means the value can be None. A default means the field can be omitted from input. They solve different problems.",
            },
            {
                "question": "What does model.model_dump() return?",
                "options": [
                    "A dictionary representation of the model's data.",
                    "A JSON string.",
                    "A new Pydantic model.",
                    "The model's class name.",
                ],
                "answer": 0,
                "explanation": "model_dump() serializes the model to a Python dictionary. Use model_dump_json() for a JSON string.",
            },
        ],
    },
    {
        "topic_id": "async",
        "questions": [
            {
                "question": "When does async Python usually help most?",
                "options": [
                    "When code waits on I/O like APIs or databases.",
                    "When multiplying large matrices in pure Python.",
                    "When removing all functions.",
                    "When avoiding error handling.",
                ],
                "answer": 0,
                "explanation": "Async shines for I/O-bound concurrency, not automatic CPU parallelism.",
            },
            {
                "question": "What happens if you call an async function without await?",
                "options": [
                    "You get a coroutine object instead of the actual result.",
                    "Python raises a SyntaxError.",
                    "The function runs normally.",
                    "The function runs but returns None.",
                ],
                "answer": 0,
                "explanation": "Calling an async function without await creates a coroutine but doesn't execute it. Python will warn about unawaited coroutines.",
            },
            {
                "question": "Why is `time.sleep(5)` bad inside an async function?",
                "options": [
                    "It blocks the event loop, freezing all other async tasks.",
                    "It doesn't work in Python 3.",
                    "It makes the function synchronous permanently.",
                    "It raises an ImportError.",
                ],
                "answer": 0,
                "explanation": "time.sleep() blocks the thread. Use asyncio.sleep() inside async code so the event loop can run other tasks.",
            },
            {
                "question": "What does the event loop do?",
                "options": [
                    "Coordinates async tasks, switching between them when one awaits I/O.",
                    "Runs code on multiple CPU cores.",
                    "Compiles Python to machine code.",
                    "Manages memory garbage collection.",
                ],
                "answer": 0,
                "explanation": "The event loop schedules coroutines and switches between them at await points.",
            },
            {
                "question": "What is concurrency vs parallelism?",
                "options": [
                    "Concurrency handles multiple tasks with overlapping progress; parallelism runs them simultaneously on different cores.",
                    "They are the same thing.",
                    "Concurrency is faster than parallelism.",
                    "Parallelism only works in JavaScript.",
                ],
                "answer": 0,
                "explanation": "Concurrency is about structure (managing multiple tasks). Parallelism is about execution (running them at the same time on multiple cores).",
            },
        ],
    },
    {
        "topic_id": "langchain",
        "questions": [
            {
                "question": "What is a common reason to use LangChain?",
                "options": [
                    "To compose models, prompts, tools, retrievers, and parsers.",
                    "To replace Python syntax.",
                    "To store files in Git.",
                    "To create HTML without JavaScript.",
                ],
                "answer": 0,
                "explanation": "LangChain provides building blocks for LLM applications and agent workflows.",
            },
            {
                "question": "What is an output parser used for in LangChain?",
                "options": [
                    "Converting unstructured model text into structured data like JSON or typed objects.",
                    "Parsing Python source code.",
                    "Formatting HTML output.",
                    "Compressing model responses.",
                ],
                "answer": 0,
                "explanation": "Output parsers extract structured data from model responses, making them programmatically usable.",
            },
            {
                "question": "Why is observability important for LLM applications?",
                "options": [
                    "LLM behavior can drift — tracing helps debug quality issues in prompts, retrieval, and tool use.",
                    "It makes the model respond faster.",
                    "It is only needed for regulatory compliance.",
                    "Observability replaces testing.",
                ],
                "answer": 0,
                "explanation": "LLM outputs are non-deterministic. Tracing prompts, context, and outputs is essential for debugging and improving quality.",
            },
            {
                "question": "What is the difference between a tool and a retriever in LangChain?",
                "options": [
                    "A tool performs an action; a retriever fetches relevant documents for context.",
                    "They are the same thing.",
                    "A retriever performs actions; a tool fetches documents.",
                    "Neither is used in LangChain.",
                ],
                "answer": 0,
                "explanation": "Tools execute actions (search, create, delete). Retrievers fetch relevant documents to provide context for the model.",
            },
            {
                "question": "What can cause a RAG system to give wrong answers?",
                "options": [
                    "Poor retrieval quality, stale data, bad chunking, or hallucination.",
                    "Using too many documents.",
                    "Having too fast an internet connection.",
                    "Using Python instead of JavaScript.",
                ],
                "answer": 0,
                "explanation": "RAG failures often stem from retrieval problems. If the wrong chunks are retrieved, the model generates answers from irrelevant context.",
            },
        ],
    },
    {
        "topic_id": "langgraph",
        "questions": [
            {
                "question": "What is the core idea behind LangGraph?",
                "options": [
                    "Stateful workflows made of nodes and edges.",
                    "A vector database format.",
                    "A CSS layout library.",
                    "A Python package manager.",
                ],
                "answer": 0,
                "explanation": "LangGraph models workflows as state, nodes, edges, and conditional transitions.",
            },
            {
                "question": "What is a 'node' in a LangGraph workflow?",
                "options": [
                    "A unit of work — a function that reads and updates state.",
                    "A database table.",
                    "A CSS selector.",
                    "A Git branch.",
                ],
                "answer": 0,
                "explanation": "Nodes are functions that perform one step of the workflow, reading from and writing to shared state.",
            },
            {
                "question": "When is a LangGraph workflow better than a simple chain?",
                "options": [
                    "When the workflow needs branching, retries, human approval, or complex control flow.",
                    "Always — graphs are superior to chains.",
                    "Only when processing images.",
                    "Never — chains handle everything.",
                ],
                "answer": 0,
                "explanation": "Graphs add value when workflows need conditional routing, loops, human review, or checkpoints — things simple chains can't do.",
            },
            {
                "question": "What are checkpoints used for in LangGraph?",
                "options": [
                    "Saving workflow state so it can be paused, resumed, and inspected.",
                    "Marking code as complete.",
                    "Creating database backups.",
                    "Compiling Python to bytecode.",
                ],
                "answer": 0,
                "explanation": "Checkpoints persist the graph's state, enabling pause/resume, debugging, and human-in-the-loop patterns.",
            },
            {
                "question": "Why is human-in-the-loop important for AI workflows?",
                "options": [
                    "Some actions have real-world impact and need human approval before executing.",
                    "Humans are faster than AI at all tasks.",
                    "It is required by Python syntax.",
                    "It reduces compute costs.",
                ],
                "answer": 0,
                "explanation": "Actions like deleting data, sending emails, or modifying infrastructure should require human approval to prevent harm.",
            },
        ],
    },
    {
        "topic_id": "mcp",
        "questions": [
            {
                "question": "What does MCP standardize?",
                "options": [
                    "How AI clients connect to tools and resources.",
                    "How Python stores integers.",
                    "How browsers render CSS.",
                    "How SQL joins are optimized.",
                ],
                "answer": 0,
                "explanation": "MCP defines a client-server pattern for exposing tools, resources, and prompts to AI applications.",
            },
            {
                "question": "What is the difference between an MCP tool and an MCP resource?",
                "options": [
                    "A tool performs an action; a resource provides data to read.",
                    "They are the same thing.",
                    "A resource performs actions; a tool provides data.",
                    "Neither exists in MCP.",
                ],
                "answer": 0,
                "explanation": "Tools are callable actions (search, create). Resources are readable data objects (files, documents, schemas).",
            },
            {
                "question": "What does 'least privilege' mean for MCP servers?",
                "options": [
                    "Expose only the minimum capabilities needed — no more.",
                    "Give the AI model full access to everything.",
                    "Use the smallest possible model.",
                    "Run on the cheapest hardware.",
                ],
                "answer": 0,
                "explanation": "Least privilege limits what the model can do, reducing risk from misuse or errors.",
            },
            {
                "question": "Why should MCP servers log tool calls?",
                "options": [
                    "To audit what the AI requested and detect unexpected behavior.",
                    "Logging is required by Python.",
                    "To make the server slower.",
                    "Logs are only for error messages.",
                ],
                "answer": 0,
                "explanation": "Logging tool calls creates an audit trail and helps detect misuse or unexpected model behavior.",
            },
            {
                "question": "What is an MCP prompt?",
                "options": [
                    "A reusable template exposed by the server for common tasks.",
                    "A Python function decorator.",
                    "A database query.",
                    "A CSS animation.",
                ],
                "answer": 0,
                "explanation": "MCP prompts are templates the server exposes so clients can use well-structured instructions for common tasks.",
            },
        ],
    },
    {
        "topic_id": "rag-vectors",
        "questions": [
            {
                "question": "What is the main purpose of embeddings in RAG?",
                "options": [
                    "Represent text meaning as vectors for semantic search.",
                    "Encrypt API keys.",
                    "Run Python code faster.",
                    "Replace all source documents.",
                ],
                "answer": 0,
                "explanation": "Embeddings let the system compare meaning and retrieve relevant chunks for a question.",
            },
            {
                "question": "Why does chunk size matter in RAG?",
                "options": [
                    "Too small loses context; too large adds noise and costs more tokens.",
                    "Chunk size has no effect on quality.",
                    "Smaller chunks are always better.",
                    "Larger chunks are always better.",
                ],
                "answer": 0,
                "explanation": "Chunk size is a tradeoff. Small chunks may lose meaning. Large chunks may include irrelevant text and use more context window.",
            },
            {
                "question": "Does RAG eliminate hallucination?",
                "options": [
                    "No — it reduces hallucination but does not eliminate it.",
                    "Yes — RAG completely prevents hallucination.",
                    "RAG increases hallucination.",
                    "Hallucination only happens without embeddings.",
                ],
                "answer": 0,
                "explanation": "RAG reduces hallucination by providing relevant context, but the model can still generate incorrect information.",
            },
            {
                "question": "What should be stored alongside vector embeddings?",
                "options": [
                    "Source metadata (file name, page, date, section) for citations and filtering.",
                    "Only the embedding vector — metadata is unnecessary.",
                    "The entire original document.",
                    "User passwords.",
                ],
                "answer": 0,
                "explanation": "Metadata enables source citations, date filtering, and debugging retrieval problems.",
            },
            {
                "question": "How should you evaluate a RAG system?",
                "options": [
                    "Test with known questions, expected sources, and answer quality checks.",
                    "Only test with random questions.",
                    "Trust that embeddings always find the right answer.",
                    "RAG systems don't need evaluation.",
                ],
                "answer": 0,
                "explanation": "Systematic evaluation with known question-answer-source triples reveals retrieval and generation failures.",
            },
        ],
    },
    {
        "topic_id": "python-devops",
        "questions": [
            {
                "question": "Which DevOps automation habit is most important before changing real systems?",
                "options": [
                    "Support dry runs and clear failure handling.",
                    "Hardcode all paths.",
                    "Ignore command return codes.",
                    "Concatenate shell commands with user input.",
                ],
                "answer": 0,
                "explanation": "Safe automation should show what it will do, handle failures clearly, and avoid surprising side effects.",
            },
            {
                "question": "Why use `subprocess.run()` with a list instead of a shell string?",
                "options": [
                    "Lists avoid shell injection vulnerabilities and handle arguments correctly.",
                    "Lists are slower but more readable.",
                    "Shell strings don't work on Windows.",
                    "There is no difference.",
                ],
                "answer": 0,
                "explanation": "Passing arguments as a list bypasses shell interpretation, preventing injection attacks from untrusted input.",
            },
            {
                "question": "What does 'idempotent' mean for a script?",
                "options": [
                    "Running it multiple times produces the same result as running it once.",
                    "The script can only run once.",
                    "The script deletes itself after running.",
                    "The script requires root access.",
                ],
                "answer": 0,
                "explanation": "Idempotent scripts are safe to re-run. They check current state before making changes, avoiding duplicate actions.",
            },
            {
                "question": "When is Python better than Bash for automation?",
                "options": [
                    "When you need complex JSON/YAML parsing, error handling, testing, or cross-platform support.",
                    "Never — Bash is always better.",
                    "Only for web development.",
                    "Python is always better than Bash.",
                ],
                "answer": 0,
                "explanation": "Python excels when scripts need structured data handling, proper error management, and testability.",
            },
            {
                "question": "Why should DevOps scripts use `pathlib` instead of string concatenation for paths?",
                "options": [
                    "pathlib handles OS differences and prevents fragile path construction.",
                    "pathlib is faster.",
                    "String paths don't work in Python 3.",
                    "pathlib automatically creates directories.",
                ],
                "answer": 0,
                "explanation": "pathlib provides an object-oriented API for paths that works correctly across operating systems.",
            },
        ],
    },
    {
        "topic_id": "sql-http-git",
        "questions": [
            {
                "question": "Which HTTP status code commonly means the request body failed validation in FastAPI?",
                "options": ["422", "201", "301", "101"],
                "answer": 0,
                "explanation": "FastAPI commonly returns 422 Unprocessable Entity for validation errors.",
            },
            {
                "question": "What is the difference between HTTP 401 and 403?",
                "options": [
                    "401 means 'not authenticated'; 403 means 'authenticated but not authorized'.",
                    "They are the same thing.",
                    "401 means 'not found'; 403 means 'server error'.",
                    "401 is for GET; 403 is for POST.",
                ],
                "answer": 0,
                "explanation": "401 Unauthorized means identity is not verified. 403 Forbidden means identity is known but lacks permission.",
            },
            {
                "question": "What does `git diff` show?",
                "options": [
                    "Changes between the working directory and the last commit (or staging area).",
                    "The full commit history.",
                    "Remote repository URLs.",
                    "Branch names only.",
                ],
                "answer": 0,
                "explanation": "git diff shows line-by-line changes that haven't been staged or committed yet.",
            },
            {
                "question": "What does `SELECT * FROM users WHERE active = true` do?",
                "options": [
                    "Returns all columns from the users table for rows where active is true.",
                    "Deletes inactive users.",
                    "Creates a new table called users.",
                    "Updates all users to be active.",
                ],
                "answer": 0,
                "explanation": "SELECT reads data. The WHERE clause filters which rows are returned.",
            },
            {
                "question": "Why is committing API keys to Git dangerous?",
                "options": [
                    "Keys in Git history are visible forever, even if removed in a later commit.",
                    "Git encrypts all committed files.",
                    "API keys don't work if committed.",
                    "It only matters for public repositories.",
                ],
                "answer": 0,
                "explanation": "Git history is permanent. Even after removing a key, it remains in old commits and can be extracted.",
            },
        ],
    },
]
