# RAG, Embeddings, and Vector DBs

LLMs know a lot from their training data, but they do not know about your company's internal documentation, last week's incident report, or the custom runbook your team wrote in 2024. RAG (Retrieval-Augmented Generation) solves this by searching your own documents at query time and feeding the most relevant excerpts to the model as context before it answers. The result: answers grounded in your actual data, with sources you can verify.

Think of RAG like an open-book exam. Without RAG, the model answers purely from memory (training data) — impressive, but limited and potentially wrong. With RAG, the model gets to 'look things up' in your document library before answering. The quality of the exam answer now depends on both the model's reasoning ability AND the quality of the lookup — finding the wrong passage (bad retrieval) leads to a wrong answer even with a brilliant model.

## 1. What RAG Is and Why It Matters

LLMs have a knowledge cutoff date and no access to your private data. When you ask an LLM about your company's Q3 financial report or last month's incident runbook, it either hallucinates an answer or admits it does not know.

RAG fixes this by inserting a retrieval step before generation:

```
Without RAG:
User question → Model (trained knowledge only) → Answer

With RAG:
User question → Search your documents → Retrieve relevant chunks
              → Inject chunks into prompt → Model answers using retrieved context → Answer
```

**When RAG helps:**
- Answering questions about internal documents, policies, or recent events
- Customer support over a knowledge base or product documentation
- Technical assistants with access to code documentation or runbooks

**When RAG does NOT help:**
- The question requires reasoning the model cannot do (RAG adds context, not intelligence)
- Your documents do not contain the answer (RAG cannot retrieve what is not indexed)
- You need real-time data (embeddings are static until you re-index)

RAG reduces hallucination risk because the model has real evidence to cite — but it does not eliminate it. A model can still misinterpret good context, or ignore it entirely.

## 2. Embeddings — How Semantic Search Works

Traditional keyword search looks for exact word matches. Semantic search using embeddings finds documents that mean the same thing, even if they use different words.

An embedding model converts a piece of text into a list of numbers (a vector) that captures its meaning. Similar meanings produce vectors that are close together in space. This is how the search finds "how do I cancel my subscription?" even if the document says "to terminate your plan, follow these steps."

```python
# Conceptual example of what embeddings do:
# (In practice you call an embedding API)

# These two phrases have very similar embeddings (close in vector space):
# 'Cancel my account'   → [0.23, -0.11, 0.89, ...]
# 'Delete my profile'   → [0.21, -0.13, 0.91, ...]

# These two phrases have different embeddings (far apart in vector space):
# 'Cancel my account'   → [0.23, -0.11, 0.89, ...]
# 'How to cook pasta'   → [-0.55, 0.72, -0.34, ...]
```

```python
# Using OpenAI embeddings API:
from openai import OpenAI
client = OpenAI()

def embed(text: str) -> list[float]:
    response = client.embeddings.create(
        model='text-embedding-3-small',
        input=text,
    )
    return response.data[0].embedding  # a list of ~1536 floats

# Store this vector alongside the document chunk in a vector database
# At query time, embed the question and find the nearest stored vectors
```

**Key fact:** you must embed documents and queries using the same model. Different models produce incompatible vector spaces — mixing them gives nonsensical results.

## 3. Chunking — Splitting Documents the Right Way

You cannot embed an entire 50-page document at once — embedding models have token limits, and large chunks dilute meaning. You must split documents into smaller chunks before embedding them.

Chunking strategy is one of the most impactful decisions in a RAG system. It depends on your documents and query patterns.

**Common chunking approaches:**

```
Fixed-size chunking: split every N tokens, with overlap
  Pro: simple, predictable
  Con: can split mid-sentence, breaking context

Sentence/paragraph chunking: split at natural boundaries
  Pro: preserves semantic units
  Con: chunk sizes are variable

Document-structure chunking: split at headers, sections
  Pro: chunks map to meaningful topics
  Con: requires parsing document structure
```

**Chunk overlap** is important: if a key fact spans the boundary between chunks, including some overlap ensures it appears in at least one complete chunk.

```python
# Example: fixed-size chunking with overlap
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks
```

**Metadata is as important as the chunk text.** Store `source`, `section`, `date`, `product`, `author` alongside each chunk so you can filter by them at retrieval time and cite them in answers.

## 4. Retrieval, Filtering, and Reranking

Vector similarity search gives you a candidate set — the top-k chunks that are most semantically similar to your query. But 'similar' is not the same as 'useful for this specific question.'

**Step 1 — Vector search:** embed the query, find the top-k nearest chunks (k is typically 5–20).

**Step 2 — Metadata filtering:** narrow the candidate set using structured filters. This prevents irrelevant results from sneaking in based on surface-level similarity.

```python
# Example: retrieve only from a specific product and date range
results = vector_store.similarity_search(
    query='How do I reset my password?',
    k=10,
    filter={
        'product': 'billing-portal',
        'date': {'$gte': '2024-01-01'},    # only recent docs
    }
)
```

**Step 3 — Reranking:** a reranker model scores each retrieved chunk against the specific query and reorders them by relevance. This catches cases where a chunk was semantically close but not actually useful.

```
Vector search top-5 (by similarity):
  #1: 'Reset your password in account settings'  ← actually useful
  #2: 'Password must be 8+ characters'           ← useful
  #3: 'Forgot your username? ...'                ← tangentially related
  #4: 'Security policy overview'                 ← not directly useful
  #5: 'Login troubleshooting guide'              ← might be useful

After reranking (by actual query relevance):
  #1: 'Reset your password in account settings'  ← same top pick
  #2: 'Login troubleshooting guide'              ← moved up — more directly useful
  #3: ...
```

Reranking adds latency but meaningfully improves answer quality when your initial retrieval is noisy.

## 5. Grounded Generation and Citations

Once you have retrieved relevant chunks, you build a prompt that includes them as context and instructs the model to answer using only that evidence.

```python
from langchain_core.prompts import ChatPromptTemplate

rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful support assistant.
Answer the user's question using ONLY the provided context.
If the answer is not in the context, say 'I don't have that information.'
Always cite the source document for any claim you make.

Context:
{context}

Question: {question}

Answer (with source citations):
""")

def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(f"[Source {i+1}: {chunk['metadata']['source']}]\n{chunk['text']}")
    return '\n\n'.join(parts)

# Usage:
chunks = retrieve_chunks('How do I reset my password?')
context = build_context(chunks)
prompt_value = rag_prompt.invoke({'context': context, 'question': 'How do I reset my password?'})
answer = model.invoke(prompt_value)
```

**Citation discipline matters because:** fluent, well-structured prose from a model can be completely wrong. "The policy says X" is only trustworthy if you can click through to the source and verify X is actually there. Prompt the model to always cite, and check that citations actually support the claims.

## 6. Evaluation — Measuring What Actually Works

Many RAG systems ship without systematic evaluation. When the system gives a wrong answer, nobody knows whether the problem was retrieval (wrong chunks), context (right chunks but too much noise), or generation (model misinterpreted good context). Good evaluation tells you which.

```python
# A simple evaluation benchmark
benchmark = [
    {
        'question': 'What is the password reset process?',
        'expected_source': 'account-settings-guide',
        'expected_keywords': ['settings', 'reset', 'email link'],
    },
    {
        'question': 'How do I cancel my subscription?',
        'expected_source': 'billing-faq',
        'expected_keywords': ['cancel', 'account', 'end of billing period'],
    },
]

def evaluate_rag(benchmark, retrieve_fn, generate_fn):
    results = []
    for item in benchmark:
        chunks = retrieve_fn(item['question'])
        sources_retrieved = [c['metadata']['source'] for c in chunks]
        answer = generate_fn(item['question'], chunks)

        retrieval_hit = item['expected_source'] in sources_retrieved
        keyword_hit = all(kw in answer.lower() for kw in item['expected_keywords'])

        results.append({
            'question': item['question'],
            'retrieval_correct': retrieval_hit,
            'answer_keywords_present': keyword_hit,
        })
    return results
```

**Debugging workflow when answers are wrong:**
1. Check retrieval first — did the right chunks come back?
2. If yes, check the prompt — is the context being used correctly?
3. If yes, the model may be misinterpreting — try a clearer instruction
4. If retrieval was wrong — adjust chunk size, overlap, metadata filters, or reranking

Change one thing at a time. A RAG system has many moving parts, and changing several at once makes it impossible to know what helped.

## 7. Try A Real Vector Store

The labs in this topic build the RAG pipeline in pure Python so chunking, embeddings, retrieval, and evaluation are visible. To try a real local vector store without hiding the idea, use Chroma with explicit toy vectors:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install chromadb
python chroma_demo.py
```

Save this as `chroma_demo.py`:

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection('support_docs')

collection.add(
    ids=['refund', 'password'],
    documents=[
        'Refunds are available for 30 days after purchase.',
        'Password resets are sent by email from account settings.',
    ],
    embeddings=[
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ],
)

results = collection.query(query_embeddings=[[1.0, 0.1, 0.0]], n_results=1)
print(results['documents'][0][0])
```

Real systems usually generate embeddings with a model API and store metadata for citations, but this starter keeps the moving parts small: add documents, store vectors, query nearest vectors, then inspect whether the retrieved text actually answers the question.
