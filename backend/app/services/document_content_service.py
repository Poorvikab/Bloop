from __future__ import annotations

from services.vector_store_service import VectorStoreService
from core.config import DEFAULT_USER_ID


vector_store = VectorStoreService()


def get_document_chunks(document_id: str, k: int = 15) -> list[str]:
    query_vector = vector_store.embed_text("core concepts and key ideas of the document")
    results = vector_store.search(
        query_vector,
        limit=k,
        filters={"user_id": DEFAULT_USER_ID, "document_id": document_id, "record_type": "document_chunk"},
    )
    return [item["payload"].get("text", "") for item in results]
