from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from services.multimodal_store_service import MultimodalRecord, MultimodalVectorStoreService
from services.vision_service import extract_image_caption


class ImageArtifactService:
    def __init__(self):
        self.vector_store = MultimodalVectorStoreService()

    def ingest_image(self, image_path: str, *, image_id: str, user_id: str, chat_id: str | None = None) -> int:
        caption = self._caption_image(image_path)
        text = f"Image caption: {caption}" if caption else f"Image artifact at {Path(image_path).name}"

        record = MultimodalRecord(
            id=f"image:{image_id}",
            text=text,
            image=image_path,
            payload={
                "record_type": "image_chunk",
                "scope": "document",
                "user_id": user_id,
                "chat_id": chat_id,
                "document_id": None,
                "artifact_id": image_id,
                "artifact_type": "image",
                "image_path": image_path,
                "caption": caption,
                "text": text,
                "source": "vision_service",
            },
        )
        return self.vector_store.upsert([record])

    def _caption_image(self, image_path: str) -> str:
        try:
            return extract_image_caption(image_path)
        except Exception:
            return ""
