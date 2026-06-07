# Build a Simple RAG Pipeline

RAG stands for Retrieval-Augmented Generation. The idea is simple: instead of asking an LLM to answer from memory alone, you first find the most relevant pieces of your own documents and include them in the prompt. The model reads your documents, not its training data, to answer the question. This topic builds every piece of that pipeline from scratch using plain Python — no framework, no embeddings library, no vector database.

Think of a RAG pipeline like a research assistant who has a filing cabinet full of notes. When you ask a question, they do not guess from memory — they flip through the files, pull out the two or three most relevant pages, read them, and then answer based on what they found. Your code plays the role of that filing-cabinet search; the LLM plays the role of the reader.

## 1. What a RAG Pipeline Actually Does

A RAG pipeline has four steps that always run in the same order: split documents into chunks, represent each chunk numerically, score chunks against the query, and build a prompt from the best matches.

```python run
# The 4-step RAG pipeline in miniature
docs = [
    "Python functions let you reuse code. Define them with the def keyword.",
    "Lists store items in order. Access items by index.",
    "Dicts map keys to values. Use curly braces to create them.",
]

# Step 1: chunk (already one sentence each here)
chunks = docs

# Step 2: represent as word-frequency vectors
def make_vec(text):
    words = text.lower().split()
    return {w: words.count(w) for w in set(words)}

# Step 3: score each chunk against the query
query = "how do I reuse code with functions"
q_vec = make_vec(query)
scores = []
for chunk in chunks:
    c_vec = make_vec(chunk)
    score = sum(q_vec.get(w, 0) * c_vec.get(w, 0) for w in c_vec)
    scores.append((score, chunk))

# Step 4: retrieve top match and build a prompt
scores.sort(reverse=True)
top = scores[0][1]
print("Best match:", top)
print("Prompt context:", top[:50] + "...")
```

Step 2 uses bag-of-words vectors instead of real embeddings — the structure is identical, just less powerful. You will replace this step with a real embedding model when you move to production.

## 2. Chunking Text

A chunk is the atomic unit of your document store — the smallest piece of text you retrieve as a unit. Chunking too coarsely means retrieved context is noisy; chunking too finely means it loses meaning.

The simplest strategy is splitting on sentence boundaries. In English text, a period followed by a space reliably separates sentences without splitting decimal numbers like `3.14`.

```python run
def chunk_by_sentences(text):
    parts = text.split(". ")
    return [p.strip() for p in parts if p.strip()]

doc = "Python is a language. Functions are reusable. Lists store sequences. Dicts map keys to values."
chunks = chunk_by_sentences(doc)

for i, chunk in enumerate(chunks):
    print(f"[{i}] {chunk}")
```

```python run
def chunk_by_size(text, max_chars=100):
    words = text.split()
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(" ".join(current)) >= max_chars:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks

long_text = "This is a longer document that needs to be split into smaller pieces for retrieval. Each piece should be short enough to fit comfortably in an LLM context window."
for chunk in chunk_by_size(long_text, max_chars=60):
    print(repr(chunk))
```

In production, overlapping chunks (where each chunk shares a few words with the next) reduce the chance of splitting a relevant sentence across chunk boundaries.

## 3. Representing Text as Vectors

To compare chunks against a query mathematically, you need to represent text as numbers. The simplest representation is a bag-of-words vector: a dictionary where each key is a word and each value is how many times that word appears.

```python run
def make_word_vector(text):
    words = text.lower().split()
    vector = {}
    for word in words:
        vector[word] = vector.get(word, 0) + 1
    return vector

v1 = make_word_vector("python is great and python is fast")
v2 = make_word_vector("python and java are languages")

print("v1:", v1)
print("v2:", v2)
print("shared words:", set(v1) & set(v2))
```

A bag-of-words vector treats every word as an independent dimension. "python" and "programming" have zero overlap even though they are semantically related. Real embedding models — which you use with the `rag-vectors` topic — fix this by mapping words to dense float vectors where semantic neighbours are close together. The retrieval math is the same either way.

## 4. Finding Similar Chunks

The dot product of two word vectors measures how much vocabulary they share, weighted by frequency. Two vectors that share many high-frequency words produce a high score; two vectors with nothing in common produce zero.

```python run
def make_word_vector(text):
    words = text.lower().split()
    return {w: words.count(w) for w in set(words)}

def dot_product(vec_a, vec_b):
    return sum(vec_a.get(w, 0) * vec_b.get(w, 0) for w in vec_b)

query = "how do python functions work"
chunk_a = "python functions let you reuse code and call them anywhere"
chunk_b = "cats and dogs are the most common household pets"

q_vec = make_word_vector(query)
score_a = dot_product(q_vec, make_word_vector(chunk_a))
score_b = dot_product(q_vec, make_word_vector(chunk_b))

print(f"chunk_a score: {score_a}")  # higher — shares python, functions
print(f"chunk_b score: {score_b}")  # zero — no shared words
```

For a more rigorous comparison that accounts for document length, divide the dot product by the product of the two vector magnitudes — that is cosine similarity. Bag-of-words dot product is good enough for a small document store where chunk lengths are similar.

## 5. Retrieval and Context Building

Retrieval is sorting all chunks by their score against the query and taking the top-k. Context building is assembling those chunks into a formatted string you can include in an LLM prompt.

```python run
def make_word_vector(text):
    words = text.lower().split()
    return {w: words.count(w) for w in set(words)}

def score_chunks(query, chunks):
    query_words = set(query.lower().split())
    results = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        score = len(query_words & chunk_words)
        results.append((score, chunk))
    results.sort(reverse=True)
    return results

chunks = [
    "Python lists store ordered sequences of items.",
    "Dictionaries map string keys to any value.",
    "Functions take arguments and return results.",
    "Python is widely used for data and AI work.",
]

query = "how do python functions take arguments"
ranked = score_chunks(query, chunks)

print("Top 2 results:")
for score, chunk in ranked[:2]:
    print(f"  [{score}] {chunk}")
```

```python run
def build_prompt(query, top_chunks):
    context = "\n".join(f"- {chunk}" for chunk in top_chunks)
    return (
        f"Answer the question using only the context below.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )

top = ["Functions take arguments and return results.", "Python is widely used for data and AI work."]
print(build_prompt("what do functions do", top))
```

## 6. The Full Pipeline

All five pieces — chunk, vectorize, score, retrieve, prompt — compose into a single pipeline function. Each step is a pure function, making the whole pipeline easy to test and easy to swap components in later.

```python run
def chunk_by_sentences(text):
    return [p.strip() for p in text.split(". ") if p.strip()]

def score_chunks(query, chunks):
    query_words = set(query.lower().split())
    results = [(len(query_words & set(c.lower().split())), c) for c in chunks]
    results.sort(reverse=True)
    return results

def build_prompt(query, top_chunks):
    context = "\n".join(f"- {c}" for c in top_chunks)
    return f"Context:\n{context}\n\nQuestion: {query}"

def rag(query, documents, k=2):
    chunks = []
    for doc in documents:
        chunks.extend(chunk_by_sentences(doc))
    ranked = score_chunks(query, chunks)
    top = [chunk for _, chunk in ranked[:k]]
    return build_prompt(query, top)

documents = [
    "Python functions let you reuse code. Define with def and a name.",
    "Lists store items in order. Access elements by index starting at zero.",
    "Dictionaries map keys to values. Create with curly braces.",
]

result = rag("how do I define a reusable block of code", documents)
print(result)
```

To move this pipeline to production: replace `chunk_by_sentences` with an overlap-aware chunker, replace word-overlap scoring with real embedding vectors and cosine similarity, and add a vector store for fast nearest-neighbour search. The structure stays identical — only the implementations of each step change.
