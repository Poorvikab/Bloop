from __future__ import annotations

import json
import uuid
from typing import Any

from langchain_groq import ChatGroq
from core.config import DEFAULT_USER_ID
from services.vector_store_service import VectorRecord, VectorStoreService


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=512,
    timeout=30,
    max_retries=2,
)

vector_store = VectorStoreService()


def _parse_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def maybe_store_chat_memory(
    *,
    user_id: str | None,
    document_id: str | None,
    question: str | None,
    answer: str,
    context: list[dict],
) -> None:
    user_id = user_id or DEFAULT_USER_ID

    prompt = f"""
You are a memory curator for a learning assistant.

Decide whether the exchange contains a durable memory worth storing.
Ignore low-signal turns like okay, thanks, yes, lol, or pure acknowledgements.

Return ONLY JSON with this shape:
{{
  "should_store": true|false,
  "memory": {{
    "record_type": "semantic|episodic|preference|artifact|mastery",
    "scope": "user|chat|document|global",
    "content": "clean distilled memory text",
    "tags": ["tag1", "tag2"],
    "importance": "low|medium|high"
  }}
}}

Conversation context:
{json.dumps(context[-6:] if context else [], ensure_ascii=True)}

User question:
{question or ""}

Assistant answer:
{answer}

Document id:
{document_id or ""}
"""

    response = llm.invoke(prompt)
    payload = _parse_json(response.content)
    if not payload or not payload.get("should_store"):
        return

    memory = payload.get("memory") or {}
    content = str(memory.get("content") or "").strip()
    if not content:
        return

    record_type = memory.get("record_type") or "episodic"
    scope = memory.get("scope") or ("document" if document_id else "user")
    tags = memory.get("tags") or []
    importance = memory.get("importance") or "medium"

    embedding = vector_store.embed_text(content)
    vector_store.upsert(
        [
            VectorRecord(
                id=f"memory:{uuid.uuid4()}",
                vector=embedding,
                payload={
                    "record_type": record_type,
                    "scope": scope,
                    "user_id": user_id,
                    "chat_id": None,
                    "document_id": document_id,
                    "artifact_id": None,
                    "content": content,
                    "tags": tags,
                    "importance": importance,
                    "source": "chat_memory",
                },
            )
        ]
    )
