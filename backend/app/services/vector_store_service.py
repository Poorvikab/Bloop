from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
import hashlib
import math
import re
import uuid

from actian_vectorai import Distance, Field, FilterBuilder, PointStruct, VectorAIClient, VectorParams
from langchain_nomic import NomicEmbeddings

from core.config import DEFAULT_USER_ID


ACTIAN_VECTORAI_URL = os.getenv("ACTIAN_VECTORAI_URL", "localhost:50051")
ACTIAN_COLLECTION_NAME = os.getenv("ACTIAN_COLLECTION_NAME", "bloop_memory")
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))
NOMIC_MODEL = os.getenv("NOMIC_MODEL", "nomic-embed-text-v1.5")


@dataclass(frozen=True)
class VectorRecord:
    id: str
    vector: list[float]
    payload: dict[str, Any]


class VectorStoreService:
    def __init__(self, url: str | None = None, collection_name: str | None = None):
        self.url = url or ACTIAN_VECTORAI_URL
        self.collection_name = collection_name or ACTIAN_COLLECTION_NAME
        self._nomic_embeddings: NomicEmbeddings | None = None

    def _client(self) -> VectorAIClient:
        return VectorAIClient(self.url)

    def embed_text(self, text: str) -> list[float]:
        try:
            return self._nomic().embed_query(text)
        except Exception:
            return self._fallback_embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            return self._nomic().embed_documents(texts)
        except Exception:
            return [self._fallback_embed(text) for text in texts]

    def _nomic(self) -> NomicEmbeddings:
        if self._nomic_embeddings is None:
            self._nomic_embeddings = NomicEmbeddings(model=NOMIC_MODEL)
        return self._nomic_embeddings

    def _fallback_embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        seed = digest
        while len(values) < VECTOR_DIMENSION:
            seed = hashlib.sha256(seed).digest()
            for i in range(0, len(seed), 4):
                if len(values) >= VECTOR_DIMENSION:
                    break
                chunk = seed[i : i + 4]
                num = int.from_bytes(chunk, "big", signed=False)
                values.append(((num % 2000) / 1000.0) - 1.0)

        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def ensure_collection(self, vector_size: int) -> None:
        with self._client() as client:
            self._ensure_collection(client, vector_size)

    def _ensure_collection(self, client: VectorAIClient, vector_size: int) -> None:
        if not client.collections.exists(self.collection_name):
            client.collections.create(
                self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.Cosine),
            )

        for field_name in ("record_type", "scope", "user_id", "chat_id", "document_id", "artifact_id", "created_at"):
            try:
                client.points.create_field_index(self.collection_name, field_name)
            except Exception:
                pass

    def upsert(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0

        with self._client() as client:
            self._ensure_collection(client, len(records[0].vector))
            points = [
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, record.id)),
                    vector=record.vector,
                    payload={**record.payload, "source_id": record.id},
                )
                for record in records
            ]
            client.points.upsert(self.collection_name, points)
            return len(points)

    def search(
        self,
        query_vector: list[float],
        *,
        limit: int = 15,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        with self._client() as client:
            filter_obj = self._build_filter(filters)
            results = client.points.search(
                self.collection_name,
                vector=query_vector,
                limit=limit,
                filter=filter_obj,
                with_payload=True,
            )
            return [
                {"id": result.id, "score": result.score, "payload": result.payload or {}}
                for result in results
            ]

    def search_text(
        self,
        query_text: str,
        *,
        limit: int = 15,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self.search(self.embed_text(query_text), limit=limit, filters=filters)

    def hybrid_search(
        self,
        query_text: str,
        *,
        limit: int = 15,
        filters: dict[str, Any] | None = None,
        candidate_limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not query_text.strip():
            return []

        semantic_results = self.search_text(query_text, limit=candidate_limit, filters=filters)
        lexical_results = self._lexical_rank(query_text, semantic_results)
        return self._reciprocal_rank_fusion([semantic_results, lexical_results], limit=limit)

    def _lexical_rank(
        self,
        query_text: str,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        query_terms = self._tokenize(query_text)
        if not query_terms:
            return []

        ranked: list[dict[str, Any]] = []
        for item in candidates:
            payload = item.get("payload") or {}
            text = str(payload.get("text") or payload.get("content") or "")
            if not text:
                continue

            text_terms = self._tokenize(text)
            if not text_terms:
                continue

            overlap = query_terms & text_terms
            if not overlap:
                continue

            heading_boost = 0.0
            if self._looks_like_heading(text):
                heading_boost = 0.25

            score = (len(overlap) / len(query_terms)) + heading_boost
            ranked.append({"id": item["id"], "score": score, "payload": payload})

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked

    def _tokenize(self, text: str) -> set[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "of",
            "in",
            "on",
            "for",
            "is",
            "are",
            "this",
            "that",
            "what",
            "which",
            "with",
            "by",
            "be",
            "from",
            "as",
            "at",
            "it",
            "i",
            "we",
            "you",
            "me",
            "my",
            "our",
            "these",
            "those",
            "how",
            "when",
            "where",
            "why",
            "who",
        }
        return {token for token in tokens if token not in stopwords and len(token) > 1}

    def _looks_like_heading(self, text: str) -> bool:
        stripped = text.strip().lower()
        return (
            stripped.startswith("chapter")
            or stripped.startswith("section")
            or stripped.startswith("unit")
            or stripped.startswith("module")
            or stripped.startswith("table of contents")
            or stripped.startswith("contents")
        )

    def _reciprocal_rank_fusion(
        self,
        result_sets: list[list[dict[str, Any]]],
        *,
        limit: int = 15,
        ranking_constant_k: int = 60,
    ) -> list[dict[str, Any]]:
        scores: dict[str, dict[str, Any]] = {}

        for results in result_sets:
            for rank, item in enumerate(results, start=1):
                item_id = str(item["id"])
                entry = scores.setdefault(item_id, {"id": item_id, "score": 0.0, "payload": item.get("payload") or {}})
                entry["score"] += 1.0 / (ranking_constant_k + rank)
                if not entry["payload"]:
                    entry["payload"] = item.get("payload") or {}

        fused = list(scores.values())
        fused.sort(key=lambda item: item["score"], reverse=True)
        return fused[:limit]

    def delete_by_filter(self, filters: dict[str, Any]) -> None:
        with self._client() as client:
            filter_obj = self._build_filter(filters)
            if filter_obj is None:
                return
            client.points.delete(self.collection_name, filter=filter_obj)

    def _build_filter(self, filters: dict[str, Any] | None):
        if not filters:
            return None

        builder = FilterBuilder()

        for field_name, field_value in filters.items():
            if field_value is None:
                continue
            if field_name == "user_id" and not field_value:
                field_value = DEFAULT_USER_ID
            builder.must(Field(field_name).eq(field_value))

        return builder.build()
