# BLOOP Context

This is the teammate-facing context doc for BLOOP. Use it to understand what we built, why Actian VectorAI DB matters, and how the RAG + memory + multimodal pieces fit together.

## What BLOOP Is

BLOOP is an AI learning assistant built around Actian VectorAI DB. The core idea is simple:

- users upload documents or ask questions
- the app retrieves relevant chunks from Actian VectorAI DB
- the assistant answers with RAG
- useful chat memories are stored back into the same vector layer
- video generation is wired in as a separate manim pipeline

The product direction comes from the wider educational app idea, but the part that matters here is the Actian-backed retrieval system.

## Main Story

The story for the project is:

1. A student uploads content or asks a question.
2. BLOOP chunks and stores the document in Actian VectorAI DB.
3. BLOOP retrieves the best chunks using Actian filters + semantic search + lexical reranking.
4. BLOOP answers the question with the retrieved context.
5. BLOOP decides whether the exchange is worth saving as durable memory.
6. BLOOP can also generate video artifacts through a separate manim service.
7. Images and video outputs are indexed as additional searchable artifacts.

## Why Actian VectorAI DB Is Central

Actian is doing real work in three places:

- document RAG storage and retrieval
- chat memory storage and retrieval
- multimodal artifact storage and retrieval

This is not just a vector store for embeddings. It is the main retrieval layer for the app.

## Current Architecture

### Backend

Main backend lives in `backend/app/`.

Important services:

- `backend/app/services/vector_store_service.py`
  - Actian wrapper
  - vector upsert/search
  - hybrid search helper
  - filter support
  - deterministic fallback embeddings when needed
- `backend/app/services/document_service.py`
  - PDF ingestion
  - chunking with overlap
  - embedding and upsert into Actian
- `backend/app/services/qa_service.py`
  - RAG answer generation
  - summary/outline routing
  - memory injection into prompts
- `backend/app/services/memory_service.py`
  - LLM-driven memory selection
  - writes durable memories into Actian
- `backend/app/services/multimodal_store_service.py`
  - named vectors for text and image
  - multimodal artifact records
- `backend/app/services/video_artifact_service.py`
  - ingests manim outputs (`scenes.json`, `script.json`, `timestamps.json`)
  - stores scene-level and summary-level text artifacts
- `backend/app/services/image_artifact_service.py`
  - captions/indexes images

### API Routes

Key route file:

- `backend/app/api/qa.py`

Important endpoints:

- `POST /qa/upload-doc`
  - uploads a document
  - stores chunks in Actian
  - optionally ties the doc to a chat
- `POST /qa/ask`
  - main RAG endpoint
  - retrieves from Actian
  - generates answer
  - optionally calls the manim service for video generation
- `POST /qa/ask-from-image`
  - image-based question flow
  - indexes image artifact
  - can also drive avatar/video generation paths
- `GET /qa/debug/memory-search`
  - debug endpoint for Actian memory retrieval

### Manim Service

The video pipeline is a separate service under `manim_generation_pipeline/`.

It runs in its own venv and process.

Important files:

- `manim_generation_pipeline/app/main.py`
- `manim_generation_pipeline/app/stages/stage1_scenes.py`
- `manim_generation_pipeline/app/stages/stage2_manim.py`
- `manim_generation_pipeline/app/stages/stage3_script.py`
- `manim_generation_pipeline/app/stages/stage4_tts.py`
- `manim_generation_pipeline/app/stages/stage5_stitch.py`

The backend calls it over HTTP on `127.0.0.1:8001`.

## RAG Flow

### Ingestion

Document ingestion does this:

1. load PDF with `PyPDFLoader`
2. split into chunks with overlap
3. embed chunks
4. upsert each chunk into Actian
5. save document metadata in Postgres

Chunking details:

- chunk size: 700
- overlap: 150

### Retrieval

The RAG path uses Actian in a filtered search setup:

- `user_id` is always used
- `document_id` is used when a specific document is selected
- `record_type="document_chunk"` is used for document retrieval
- summary-style questions get a different retrieval bias

The retrieval stack currently supports:

- semantic search
- hybrid search
- structured filters

### Answering

`backend/app/services/qa_service.py`:

- detects summary/outline/chapter questions
- pulls context from Actian
- adds memory context if available
- prompts Groq Llama (`llama-3.3-70b-versatile`)
- writes useful memory back through `maybe_store_chat_memory(...)`

## Memory Model

Memory is one of the main parts of BLOOP. The goal is not to save every chat turn, but to preserve useful, durable context that helps the assistant behave consistently over time.

### Why Memory Exists

Memory lets BLOOP remember things like:

- a user prefers simple explanations
- a user is studying a particular topic repeatedly
- a previous answer or clarification is relevant later
- a document-specific detail should survive across turns

The memory system is meant to improve continuity, not to act like a raw chat log.

### What Gets Stored

The memory writer only saves high-signal exchanges. Typical examples:

- stable user preferences
- recurring learning goals
- important facts the assistant should reuse
- distilled summaries of useful context

### What Does Not Get Stored

We avoid storing low-value turns such as:

- thanks
- okay
- yes
- no
- short acknowledgements
- filler responses

This keeps the vector store cleaner and makes retrieval more useful.

### Where Memory Lives

Memory is stored in Actian VectorAI DB through `backend/app/services/vector_store_service.py`.

Each memory record carries metadata so we can filter and rank it later.

Common fields:

- `record_type`
- `scope`
- `user_id`
- `document_id`
- `content`
- `tags`
- `importance`
- `source`

### Memory Types

The schema supports these categories:

- `semantic`
- `episodic`
- `preference`
- `artifact`
- `mastery`

Right now the system mostly uses `semantic`, but the schema is already ready for richer memory taxonomies.

### Memory Write Flow

The write path is:

1. `backend/app/services/qa_service.py` generates the answer.
2. `maybe_store_chat_memory(...)` is called.
3. The LLM decides whether the exchange is worth remembering.
4. If yes, it returns a distilled memory object.
5. The memory is embedded and upserted into Actian.

This means the LLM is acting as a memory filter, not just a responder.

### Memory Retrieval Flow

When answering a question, `qa_service.py` calls `build_memory_context(...)`.

Retrieval currently uses:

- `user_id`
- `record_type="semantic"`
- optional `document_id`

The top matching memories are added to the prompt under `Relevant memory`.

This gives the model a small, filtered slice of past context instead of flooding it with the full history.

### How Memory Interacts With RAG

Memory and document RAG use the same Actian-backed retrieval layer, but they serve different purposes:

- RAG retrieves facts from the current document
- memory retrieves useful long-term context about the user or prior exchanges

The answer prompt can include both at once.

That is important because the assistant can then answer with:

- document truth
- user preference awareness
- prior conversation continuity

### Current Memory Behavior

The memory system is working, but it is still simple:

- it stores distilled text, not full transcripts
- it mostly retrieves semantic memories
- it does not yet heavily use `tags` or `importance`
- it could still get better at selecting and ranking memories

### Why This Matters For BLOOP

Memory is what makes BLOOP feel like more than a one-off RAG chatbot.

It gives the app a persistent identity and lets it behave like a learning companion that remembers the student, the topic, and the style that works best.

## Multimodal / Named Vectors

We also added multimodal support on top of Actian.

### Text + Image

The multimodal store uses named vectors so text and image live in the same logical collection but can be searched independently.

This is our named-vectors approach for multimodal search.

### Video as Text Artifacts

We are not embedding raw video directly.

Instead, we index text artifacts from the video pipeline:

- scene concepts
- scene visual descriptions
- narration/script text
- timestamps
- summary records

That makes the generated video content searchable in a vector DB-friendly way.

## Manim Pipeline

The manim service is intentionally separate from the backend.

Flow:

1. backend sends a request to `8001`
2. manim service plans scenes
3. manim service generates manim code
4. manim service renders scenes
5. script/TTS/stitch steps produce the final video
6. backend ingests the generated outputs into Actian

Important output files:

- `outputs/scenes.json`
- `outputs/script.json`
- `outputs/timestamps.json`
- `outputs/videos/<video_id>/final.mp4`

## Current State

### Done

- Actian-backed document ingestion
- Actian-backed document retrieval
- hybrid retrieval support
- filtered search support
- LLM-driven memory writes
- memory retrieval injected into answers
- multimodal text/image store
- video artifact ingestion
- backend-to-manim HTTP wiring
- smoke script for end-to-end validation

### Still Rough

- the manim generation path is still brittle
- some LLM outputs can still break scene generation
- the current end-to-end smoke path can fail on video generation depending on the current manim output

## Relevant Files

### Backend

- `backend/app/api/qa.py`
- `backend/app/services/vector_store_service.py`
- `backend/app/services/document_service.py`
- `backend/app/services/document_content_service.py`
- `backend/app/services/qa_service.py`
- `backend/app/services/memory_service.py`
- `backend/app/services/multimodal_store_service.py`
- `backend/app/services/video_artifact_service.py`
- `backend/app/services/image_artifact_service.py`
- `backend/app/core/config.py`

### Manim pipeline

- `manim_generation_pipeline/app/main.py`
- `manim_generation_pipeline/app/stages/stage1_scenes.py`
- `manim_generation_pipeline/app/stages/stage2_manim.py`
- `manim_generation_pipeline/app/stages/stage3_script.py`
- `manim_generation_pipeline/app/stages/stage4_tts.py`
- `manim_generation_pipeline/app/stages/stage5_stitch.py`
- `manim_generation_pipeline/app/utils/json_safe.py`

### Validation

- `scripts/smoke_manim_backend.py`
- `backend/app/testing/test_db.py`

### Docs

- `docs/memory-model.md`
- `docs/design.md`
- `docs/requirements.md`

## Short Version

BLOOP is an Actian VectorAI DB-powered educational RAG assistant with long-term memory, hybrid/filtered retrieval, and multimodal artifact indexing. The current focus is document understanding plus memory, with a separate manim video pipeline wired in for generated explanations.
