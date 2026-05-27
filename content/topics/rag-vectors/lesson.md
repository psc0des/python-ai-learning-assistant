# RAG, Embeddings, and Vector DBs

RAG quality is mostly a retrieval quality problem, not just a model problem. If evidence selection is weak, final answers will be weak even with a strong LLM.

## 1) Retrieval-First Thinking

Treat RAG as a retrieval pipeline plus generation, not generation alone. The model should answer from selected evidence, not from unsupported guesswork.

## 2) Embeddings as Search Representation

Embeddings convert text into vectors where semantic similarity can be computed. This enables retrieval of relevant chunks even when wording differs.

## 3) Chunking and Metadata

Chunk size and boundaries matter. Overly small chunks lose context. Overly large chunks add irrelevant text and token cost. Attach metadata so results can be filtered and cited.

## 4) Candidate Retrieval and Reranking

Top-k vector search is a candidate stage. Add metadata filters and optional reranking to improve final relevance. Many production failures happen here, not in model decoding.

## 5) Grounded Answers and Citations

Require responses to reference retrieved evidence. Citation-aware outputs improve trust and make debugging possible when claims are incorrect.

## 6) Evaluation and Iteration

Use test sets with expected answers and expected sources. Track retrieval precision, citation correctness, and unsupported claims. Improve chunking, filtering, and reranking before changing prompts blindly.

## Real-World Implementation Pattern

Strong teams usually:
1. Build ingestion with metadata from day one.
2. Evaluate retrieval separately from generation.
3. Add reranking and fallback behavior for low-confidence retrieval.
4. Ship citation-aware responses and monitor drift over time.
