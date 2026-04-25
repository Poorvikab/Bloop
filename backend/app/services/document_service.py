from __future__ import annotations

import uuid
from uuid import UUID

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from core.models import Document
from core.config import DEFAULT_USER_ID
from services.vector_store_service import VectorRecord, VectorStoreService


vector_store = VectorStoreService()


def ingest_document(file_path: str, chat_id: UUID, db: Session, user_id: str | None = None) -> str:
    """
    Ingest a PDF document: chunk, embed, store in vector DB and metadata in Neon DB
    
    Args:
        file_path: Path to the PDF file
        chat_id: UUID of the chat session
        db: SQLAlchemy database session
    
    Returns:
        document_id as string
    """
    # Load and chunk document
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(docs)

    # Create embeddings
    # Generate document ID
    doc_id = str(uuid.uuid4())

    resolved_user_id = user_id or DEFAULT_USER_ID
    embeddings = vector_store.embed_texts([chunk.page_content for chunk in chunks])
    records = []
    for index, chunk in enumerate(chunks):
        records.append(
            VectorRecord(
                id=f"{doc_id}:{index}",
                vector=embeddings[index],
                payload={
                    "record_type": "document_chunk",
                    "scope": "document",
                    "user_id": resolved_user_id,
                    "chat_id": str(chat_id) if chat_id else None,
                    "document_id": doc_id,
                    "chunk_index": index,
                    "text": chunk.page_content,
                    "source": file_path,
                },
            )
        )

    vector_store.upsert(records)

    # Extract file metadata
    file_name = file_path.split("/")[-1].replace("\\", "/").split("/")[-1]
    file_type = file_name.split(".")[-1] if "." in file_name else "pdf"

    # Store metadata in Neon DB
    document = Document(
        document_id=UUID(doc_id),
        chat_id=chat_id,
        file_name=file_name,
        file_type=file_type,
        file_path=file_path,
        storage_url=None  # Can add S3/cloud storage URL if needed
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)

    return doc_id


def get_vector_db_for_document(doc_id: str):
    return vector_store, doc_id
