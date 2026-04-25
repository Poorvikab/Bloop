import json
from utils.llm import call_llm
from pathlib import Path
from paths import PROMPTS_DIR


def normalize_scene_id(sid):
    sid = str(sid).strip().lower()
    if not sid.startswith("scene_"):
        sid = f"scene_{sid}"
    return sid


def extract_scene_id(s):
    if isinstance(s, dict):
        return s.get("scene_id")
    return s


def generate_script(scenes, timestamps, persona, level):
    prompt = (PROMPTS_DIR / "script_writer.txt").read_text(encoding="utf-8")

    prompt = prompt.format(
        scenes=json.dumps(scenes),
        timestamps=json.dumps(timestamps),
        persona=persona,
        level=level
    )

    output = call_llm(prompt)

    try:
        script = json.loads(output)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON:\n{output}") from e

    if not isinstance(script, list):
        raise RuntimeError("LLM output must be a list")

    # ✅ FIX: unwrap scenes correctly
    if isinstance(scenes, dict):
        scene_list = scenes.get("scenes", [])
    else:
        scene_list = scenes

    print("Scene list:", scene_list[:2])  # debug
    print("Script output:", script[:2])

    expected_scene_ids = {
        normalize_scene_id(extract_scene_id(s)) for s in scene_list
    }

    actual_scene_ids = set()
    for s in script:
        if "scene_id" not in s or "script" not in s:
            raise RuntimeError(f"Invalid scene object from LLM: {s}")

        actual_scene_ids.add(normalize_scene_id(s["scene_id"]))

    missing = expected_scene_ids - actual_scene_ids
    extra = actual_scene_ids - expected_scene_ids

    if missing:
        raise RuntimeError(f"LLM missing scripts for scenes: {missing}")

    if extra:
        print(f"[!] Warning: extra scenes from LLM: {extra}")

    Path("outputs/script.json").write_text(
        json.dumps(script, indent=2),
        encoding="utf-8"
    )

    print(f"[✓] Script generated for {len(script)} scenes")

    return script