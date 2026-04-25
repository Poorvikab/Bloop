from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.multimodal_store_service import MultimodalRecord, MultimodalVectorStoreService


class VideoArtifactService:
    def __init__(self, pipeline_root: str | Path):
        self.pipeline_root = Path(pipeline_root)
        self.output_dir = self.pipeline_root / "outputs"
        self.vector_store = MultimodalVectorStoreService()

    def ingest_video_outputs(self, video_id: str) -> int:
        scenes_path = self._resolve_output_file("scenes.json")
        script_path = self._resolve_output_file("script.json")
        timestamps_path = self._resolve_output_file("timestamps.json")

        if not scenes_path.exists() or not script_path.exists():
            raise FileNotFoundError("Missing manim pipeline outputs for scenes or script")

        scenes_data = json.loads(scenes_path.read_text(encoding="utf-8"))
        script_data = json.loads(script_path.read_text(encoding="utf-8"))
        timestamps_data = (
            json.loads(timestamps_path.read_text(encoding="utf-8"))
            if timestamps_path.exists()
            else []
        )

        timestamps_by_scene = {
            int(item.get("scene")): item
            for item in timestamps_data
            if isinstance(item, dict) and item.get("scene") is not None
        }
        script_by_scene = {
            int(item.get("scene_id")): item.get("script", "")
            for item in script_data
            if isinstance(item, dict) and item.get("scene_id") is not None
        }

        category = str(scenes_data.get("category") or "video")
        scenes = scenes_data.get("scenes") or []

        records: list[MultimodalRecord] = []

        summary_text = self._build_summary(video_id, category, scenes, script_data)
        if summary_text:
            records.append(
                MultimodalRecord(
                    id=f"video:{video_id}:summary",
                    text=summary_text,
                    image=None,
                    payload={
                        "record_type": "video_summary",
                        "scope": "document",
                        "user_id": "legacy-user",
                        "chat_id": None,
                        "document_id": None,
                        "artifact_id": video_id,
                        "artifact_type": "video",
                        "video_id": video_id,
                        "category": category,
                        "text": summary_text,
                        "source": "manim_generation_pipeline",
                    },
                )
            )

        for idx, scene in enumerate(scenes, start=1):
            scene_id = str(scene.get("scene_id") or idx)
            script = script_by_scene.get(int(scene_id)) or ""
            timestamp = timestamps_by_scene.get(int(scene_id), {})
            text = self._build_scene_text(scene, script, timestamp)
            if not text.strip():
                continue

            records.append(
                MultimodalRecord(
                    id=f"video:{video_id}:scene:{scene_id}",
                    text=text,
                    image=scene.get("visual"),
                    payload={
                        "record_type": "video_chunk",
                        "scope": "document",
                        "user_id": "legacy-user",
                        "chat_id": None,
                        "document_id": None,
                        "artifact_id": video_id,
                        "artifact_type": "video",
                        "video_id": video_id,
                        "scene_id": scene_id,
                        "scene_index": idx,
                        "category": category,
                        "concept": scene.get("concept"),
                        "visual": scene.get("visual"),
                        "script": script,
                        "start": timestamp.get("start"),
                        "end": timestamp.get("end"),
                        "duration": timestamp.get("duration"),
                        "text": text,
                        "source": "manim_generation_pipeline",
                    },
                )
            )

        return self.vector_store.upsert(records)

    def _resolve_output_file(self, name: str) -> Path:
        primary = self.pipeline_root / "outputs" / name
        fallback = self.pipeline_root / "app" / "outputs" / name
        candidates = [p for p in (primary, fallback) if p.exists()]
        if not candidates:
            return primary
        if len(candidates) == 1:
            return candidates[0]
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def _build_summary(
        self,
        video_id: str,
        category: str,
        scenes: list[dict[str, Any]],
        script_data: list[dict[str, Any]],
    ) -> str:
        concepts = [str(scene.get("concept") or "") for scene in scenes if scene.get("concept")]
        scripts = [str(item.get("script") or "") for item in script_data if item.get("script")]
        if not concepts and not scripts:
            return ""

        return " ".join(
            [
                f"Video {video_id} about {category}.",
                "Scenes: " + "; ".join(concepts[:8]),
                "Narration: " + " ".join(scripts[:2]),
            ]
        ).strip()

    def _build_scene_text(
        self,
        scene: dict[str, Any],
        script: str,
        timestamp: dict[str, Any],
    ) -> str:
        parts = [
            f"Concept: {scene.get('concept') or ''}",
            f"Visual: {scene.get('visual') or ''}",
            f"Narration: {script}",
        ]
        if timestamp:
            parts.append(
                f"Timing: start={timestamp.get('start')} end={timestamp.get('end')} duration={timestamp.get('duration')}"
            )
        return "\n".join(part for part in parts if part.strip())
