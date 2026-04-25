from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
BACKEND_URL = os.getenv("BLOOP_BACKEND_URL", "http://127.0.0.1:8000")
MANIM_URL = os.getenv("BLOOP_MANIM_URL", "http://127.0.0.1:8001")
DEFAULT_CHAT_ID = "29541568-2a5e-41c4-b313-6a9b6fcd80e2"
DEFAULT_DOC_ID = "2927e234-a070-40f0-bf22-fc607c479af7"


def wait_for(url: str, timeout: int = 120) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for {url}")


def main() -> None:
    print("Checking services...")
    wait_for(f"{MANIM_URL}/docs")
    wait_for(f"{BACKEND_URL}/docs")

    if not DEFAULT_CHAT_ID:
        raise RuntimeError("Set BLOOP_SMOKE_CHAT_ID to an existing chat_id")

    question = "Explain photosynthesis in simple terms."
    params = {
        "chat_id": DEFAULT_CHAT_ID,
        "question": question,
        "video_enabled": True,
        "face_enabled": False,
    }
    if DEFAULT_DOC_ID:
        params["document_id"] = DEFAULT_DOC_ID

    print("Sending smoke request to backend /qa/ask...")
    response = requests.post(f"{BACKEND_URL}/qa/ask", params=params, timeout=600)
    response.raise_for_status()
    data = response.json()
    print(json.dumps(data, indent=2))

    video_id = data.get("video_id")
    if not video_id:
        raise RuntimeError("Backend did not return video_id")

    pipeline_roots = [
        ROOT / "manim_generation_pipeline" / "outputs",
        ROOT / "manim_generation_pipeline" / "app" / "outputs",
    ]
    for base in pipeline_roots:
        if (base / "scenes.json").exists() and (base / "script.json").exists() and (base / "timestamps.json").exists():
            print(f"Found pipeline outputs at {base}")
            final_video = base / "videos" / video_id / "final.mp4"
            if not final_video.exists():
                raise RuntimeError(f"Missing final video: {final_video}")
            print(f"Found final video: {final_video}")
            break
    else:
        raise RuntimeError("Could not find manim pipeline outputs")

    print("Smoke test passed")


if __name__ == "__main__":
    main()
