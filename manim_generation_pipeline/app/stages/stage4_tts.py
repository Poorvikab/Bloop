from pathlib import Path
import os
import azure.cognitiveservices.speech as speechsdk


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
AUDIO_DIR = OUTPUTS_DIR / "audio"


def normalize_scene_id(sid):
    sid = str(sid).strip().lower()
    if not sid.startswith("scene_"):
        sid = f"scene_{sid}"
    return sid


def tts_generate(script, video_id: str, scene_ids: list[str]):
    output_dir = AUDIO_DIR / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    speech_key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not region:
        raise RuntimeError("Azure Speech key or region not set")

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=region
    )
    speech_config.speech_synthesis_voice_name = "en-IN-NeerjaNeural"

    # ✅ Normalize script into map
    script_map = {}
    for s in script:
        if "scene_id" not in s or "script" not in s:
            print(f"[!] Skipping invalid script entry: {s}")
            continue

        sid = normalize_scene_id(s["scene_id"])
        script_map[sid] = s["script"]

    # Normalize input scene_ids
    scene_ids = [normalize_scene_id(sid) for sid in scene_ids]

    print("Scene IDs:", scene_ids)
    print("Available scripts:", list(script_map.keys()))

    # Generate audio
    for scene_id in scene_ids:
        if scene_id not in script_map:
            print(f"[!] Missing script for {scene_id}, skipping...")
            continue  # ✅ no hard crash

        text = script_map[scene_id]
        audio_path = output_dir / f"{scene_id}.wav"

        audio_config = speechsdk.audio.AudioOutputConfig(
            filename=str(audio_path)
        )

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        result = synthesizer.speak_text_async(text).get()

        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"TTS failed for {scene_id}")

        print(f"[✓] Generated audio for {scene_id}")