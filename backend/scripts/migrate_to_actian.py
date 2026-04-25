from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "backend" / "app"
LEGACY_CHROMA_DB = ROOT / "backend" / "app" / "vectorstore" / "chroma_db" / "chroma.sqlite3"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.config import DEFAULT_USER_ID
from services.vector_store_service import VectorRecord, VectorStoreService


def _load_env() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    load_dotenv(ROOT / ".env")


def _connect_neon():
    neon_url = os.getenv("NEON_DB_URL")
    if not neon_url:
        raise RuntimeError("NEON_DB_URL is not set")
    engine = create_engine(neon_url)
    return sessionmaker(bind=engine)()


def _normalize_path(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("\\", "/").strip().lower()


def _load_documents(db) -> dict[str, str]:
    rows = db.execute(text("select document_id::text, file_name from documents")).fetchall()
    by_name: dict[str, str] = {}
    for document_id, file_name in rows:
        by_name[_normalize_path(str(file_name))] = str(document_id)
    return by_name


def _load_sources(conn: sqlite3.Connection) -> dict[str, str]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    collection_rows = cur.execute("select id, name from collections").fetchall()
    collection_by_id = {row["id"]: row["name"] for row in collection_rows}

    sources: dict[str, str] = {}
    for row in cur.execute("select distinct topic, json_extract(metadata, '$.source') as source from embeddings_queue where metadata is not null"):
        topic = row[0]
        source = row[1]
        if source:
            sources[topic] = source

    for row in cur.execute("select id, source from embeddings_queue where metadata is null and source is not null"):
        sources[row[0]] = row[1]

    return {topic: _normalize_path(source) for topic, source in sources.items()}


def _document_id_for_source(source: str, documents_by_name: dict[str, str]) -> str | None:
    base = Path(source).name
    if base in documents_by_name:
        return documents_by_name[base]
    normalized = _normalize_path(source)
    for name, document_id in documents_by_name.items():
        if name and name in normalized:
            return document_id
    return None


def _load_queue_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = []
    for row in cur.execute("select id, topic, vector, encoding, metadata from embeddings_queue where operation = 2 order by seq_id"):
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        rows.append({
            "id": row["id"],
            "topic": row["topic"],
            "vector": row["vector"],
            "encoding": row["encoding"],
            "metadata": metadata,
        })
    return rows


def _vector_from_blob(blob: bytes, encoding: str | None) -> list[float]:
    if encoding and encoding.upper() != "FLOAT32":
        raise RuntimeError(f"Unsupported vector encoding: {encoding}")
    import array

    values = array.array("f")
    values.frombytes(blob)
    return list(values)


def backfill(dry_run: bool = False, limit: int | None = None) -> None:
    _load_env()
    db = _connect_neon()
    try:
        documents_by_name = _load_documents(db)
    finally:
        db.close()

    if not LEGACY_CHROMA_DB.exists():
        raise FileNotFoundError(f"Legacy Chroma DB not found: {LEGACY_CHROMA_DB}")

    conn = sqlite3.connect(LEGACY_CHROMA_DB)
    try:
        rows = _load_queue_rows(conn)
    finally:
        conn.close()

    if limit is not None:
        rows = rows[:limit]

    vector_store = VectorStoreService()
    grouped: dict[str, list[VectorRecord]] = defaultdict(list)
    skipped = 0

    for row in rows:
        metadata = row["metadata"] or {}
        source = metadata.get("source") or ""
        document_id = _document_id_for_source(source, documents_by_name)
        if not document_id:
            skipped += 1
            continue

        text_value = metadata.get("chroma:document") or ""
        if not text_value.strip():
            skipped += 1
            continue

        payload: dict[str, Any] = {
            "record_type": "document_chunk",
            "scope": "document",
            "user_id": DEFAULT_USER_ID,
            "chat_id": None,
            "document_id": document_id,
            "artifact_id": None,
            "text": text_value,
            "source": source,
            "legacy_collection": row["topic"],
            "legacy_metadata": metadata,
        }

        for key in ("page", "page_label", "author", "creator", "producer", "creationdate", "moddate", "total_pages"):
            if key in metadata:
                payload[key] = metadata[key]

        grouped[document_id].append(
            VectorRecord(
                id=row["id"],
                vector=_vector_from_blob(row["vector"], row["encoding"]),
                payload=payload,
            )
        )

    total = sum(len(values) for values in grouped.values())
    print(json.dumps({"candidates": len(rows), "records": total, "skipped": skipped, "documents": len(grouped), "dry_run": dry_run}, indent=2))

    if dry_run or not total:
        return

    for document_id, records in grouped.items():
        vector_store.upsert(records)
        print(f"upserted {len(records)} chunks for {document_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    backfill(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
