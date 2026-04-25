# Memory Model

## Goal

We want the assistant to keep useful long-term memory about a user and reuse it during future chats.

The intended behavior is:
- store only durable, high-signal memories
- avoid saving low-value turns like acknowledgements
- keep memory retrieval tied to the same Actian-backed vector store as document RAG
- let the LLM decide what is worth storing

## What We Have Built

### Storage

Memory is stored in Actian VectorAI through `backend/app/services/vector_store_service.py`.

Each memory record includes:
- `record_type`: semantic, episodic, preference, artifact, or mastery
- `scope`: user, chat, document, or global
- `user_id`: fixed to `legacy-user` for now
- `document_id`: optional document scope
- `content`: distilled memory text
- `tags`: optional tags
- `importance`: low, medium, or high
- `source`: `chat_memory`

### Writing Memories

Memory writing happens in `backend/app/services/memory_service.py`.

Flow:
1. `backend/app/services/qa_service.py` generates an answer.
2. `maybe_store_chat_memory(...)` sends the exchange to Groq.
3. The LLM returns JSON saying whether the turn is worth storing.
4. If yes, a distilled memory is embedded and upserted into Actian.

The current rules are:
- ignore low-signal replies like thanks, yes, okay, lol
- only store when the LLM thinks the exchange is durable
- store the cleaned-up memory text, not the full chat transcript

### Retrieving Memories

Memory retrieval happens in `backend/app/services/qa_service.py` through `build_memory_context(...)`.

Current retrieval behavior:
- searches Actian using the query text
- filters by `user_id`
- filters by `record_type="semantic"`
- optionally filters by `document_id`
- injects the top memory hits into the RAG prompt as `Relevant memory`

### RAG

Document retrieval also uses the same Actian service.

Current document RAG behavior:
- PDF ingestion chunks the document with overlap
- chunks are embedded and stored in Actian
- `/qa/ask` retrieves `document_chunk` records from Actian
- summary questions use a separate summary prompt branch
- chapter/outline/table-of-contents queries are treated as summary-style queries

## Current LLM Setup

The main chat and memory paths currently use Groq Llama:
- `backend/app/services/qa_service.py`
- `backend/app/services/memory_service.py`

The current model is `llama-3.3-70b-versatile` in code at the moment of writing.

## What This Means Today

We already have:
- one retrieval layer for docs and memory
- durable memory writes
- memory-aware prompts
- fixed guest identity via `legacy-user`
- prompt routing for summary-style document questions

So the memory model is working as a real system, but it is still simple.

## What Is Still Left

### Memory Retrieval Quality

We are only using part of the memory schema during retrieval right now.

Current retrieval mostly uses:
- `user_id`
- `record_type="semantic"`
- optional `document_id`

Not yet used much for retrieval:
- `scope`
- `tags`
- `importance`

### Memory Taxonomy Tuning

The schema supports:
- semantic
- episodic
- preference
- artifact
- mastery

We have not yet validated whether these categories are the best fit or whether the prompt should produce them more consistently.

### Better Prompting

The prompt can still be improved so it:
- chooses cleaner memories
- avoids noisy or repetitive memories
- writes better distilled summaries
- avoids awkward chapter/outline output formatting

### Better Retrieval Logic

Future improvements could include:
- weighting `importance`
- using `scope` to prioritize the right memories
- retrieving by `tags`
- separating personal preferences from document-specific facts more clearly

### Model Upgrade

The current Groq model is good enough to work, but we may still want a stronger or better-tuned model for:
- cleaner summaries
- better memory extraction
- less noisy chapter/TOC answers

## Practical Summary

What we wanted:
- Actian-backed RAG
- long-term memory
- LLM-driven memory selection
- minimal guest-mode setup

What we have:
- all of the above, in a working basic form

What remains:
- better memory retrieval using the schema we already store
- better memory prompts
- better LLM quality for structured answers
