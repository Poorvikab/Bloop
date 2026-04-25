import subprocess
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MEDIA_DIR = PROJECT_ROOT / "media"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

SCENES_DIR = OUTPUTS_DIR / "scenes"
AUDIO_DIR = OUTPUTS_DIR / "audio"
VIDEOS_DIR = OUTPUTS_DIR / "videos"


def get_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


# ============================================================
# ✅ FIXED MUX AUDIO (scene_id-based, NOT index-based)
# ============================================================

def mux_audio(video_id: str, scene_ids: list[str]):
    base_audio = AUDIO_DIR / video_id
    base_out = VIDEOS_DIR / video_id / "scenes_with_audio"
    base_out.mkdir(parents=True, exist_ok=True)

    for scene_id in scene_ids:

        # 🔥 Find video by scene_id (robust to skipped scenes)
        candidates = list(SCENES_DIR.glob(f"*_{scene_id}.mp4"))

        if len(candidates) == 0:
            raise RuntimeError(f"No video found for {scene_id}")

        if len(candidates) > 1:
            raise RuntimeError(f"Multiple videos found for {scene_id}: {candidates}")

        video = candidates[0]

        # 🔥 Audio must match scene_id
        audio = base_audio / f"{scene_id}.wav"

        if not audio.exists():
            raise RuntimeError(f"No audio found for {scene_id}")

        # Output keeps original ordering visually but doesn't rely on idx
        out = base_out / f"{video.stem}.mp4"

        # Durations
        V = get_duration(video)
        A = get_duration(audio)

        print(f"🔍 {scene_id}: video={V:.2f}s audio={A:.2f}s")

        if A > V:
            vf = f"tpad=stop_mode=clone:stop_duration={A - V}"
            af = "anull"
        elif V > A:
            vf = "null"
            af = f"apad=pad_dur={V - A}"
        else:
            vf = "null"
            af = "anull"

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(video),
                "-i", str(audio),
                "-filter_complex", f"[0:v]{vf}[v];[1:a]{af}[a]",
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-c:a", "aac",
                str(out),
            ],
            check=True,
        )

        print(f"🔊 Muxed {scene_id}")

    print(f"✅ Audio muxed for {len(scene_ids)} scenes")


# ============================================================
# STITCH FINAL VIDEO
# ============================================================

def stitch(video_id: str):
    base = VIDEOS_DIR / video_id
    scenes_dir = base / "scenes_with_audio"
    final_out = base / "final.mp4"

    video_files = sorted(scenes_dir.glob("*.mp4"))

    if not video_files:
        raise RuntimeError("No scene videos found to stitch")

    list_file = base / "concat_list.txt"

    with open(list_file, "w") as f:
        for v in video_files:
            f.write(f"file '{v.resolve()}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(final_out),
        ],
        check=True,
    )

    list_file.unlink()

    print(f"🎞 Final video → {final_out}")
    return final_out


# ============================================================
# EXTRACT AUDIO FROM FINAL VIDEO
# ============================================================

def extract_audio_from_final(video_id: str):
    input_video = VIDEOS_DIR / video_id / "final.mp4"
    output_audio = AUDIO_DIR / video_id / "final_audio.wav"

    if not input_video.exists():
        raise FileNotFoundError("final.mp4 not found")

    output_audio.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_audio),
        ],
        check=True,
    )

    print(f"🔊 Extracted audio → {output_audio}")
    return output_audio


# ============================================================
# SADTALKER
# ============================================================

def send_to_sadtalker(
    audio_path: Path,
    image_path: Path = Path("D:/bloop/data/avatars/sir-isaac-newton.webp"),
):
    url = "http://127.0.0.1:8000/video/generate"

    with open(audio_path, "rb") as a, open(image_path, "rb") as i:
        files = {
            "audio": ("audio.wav", a, "audio/wav"),
            "image": ("avatar.jpg", i, "image/jpeg"),
        }
        response = requests.post(url, files=files)

    response.raise_for_status()
    data = response.json()
    print("🧠 SadTalker job started:", data)
    return data["job_id"]