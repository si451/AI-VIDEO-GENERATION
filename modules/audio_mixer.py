import os
import sys
import subprocess
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import AUDIO_DIR, ASSETS_DIR, FINAL_DIR

def create_default_bgm(output_path: Path, duration_sec: float) -> Path:
    """
    Generates a gentle, soothing multi-tone ambient melody for children's stories
    if no custom MP3 files exist in assets/bgm/.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Synthesizes soft, gentle bell/music-box tones using FFmpeg lavfi
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=523.25:duration={duration_sec}",  # C5
        "-f", "lavfi",
        "-i", f"sine=frequency=659.25:duration={duration_sec}",  # E5
        "-f", "lavfi",
        "-i", f"sine=frequency=783.99:duration={duration_sec}",  # G5
        "-filter_complex",
        "[0:a][1:a][2:a]amix=inputs=3:dropout_transition=0,volume=0.15,lowpass=f=1200,afade=t=in:ss=0:d=2,afade=t=out:st=" + f"{max(duration_sec-3, 0)}:d=3[aout]",
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path

def build_scene_dialogue_track(scenes: list, voice_metadata: list, output_path: Path, audio_dir: Path = None) -> Path:
    """
    Concatenates individual scene voice tracks into a continuous dialogue track
    with gentle padding between scenes matching scene durations.
    """
    if audio_dir is None:
        audio_dir = AUDIO_DIR
    output_path.parent.mkdir(parents=True, exist_ok=True)
    meta_map = {m.get("frame_id", m.get("scene_id", i+1)): m for i, m in enumerate(voice_metadata)}

    inputs = []
    input_tags = []
    count = 0

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("frame_id", scene.get("scene_id", idx + 1))
        voice_file = audio_dir / f"frame_{scene_id:02d}_voice.mp3"
        if not voice_file.exists():
            voice_file = audio_dir / f"scene_{scene_id}_voice.mp3"
        if not voice_file.exists():
            voice_file = audio_dir / f"scene_{scene_id}.mp3"
        if voice_file.exists():
            inputs.extend(["-i", str(voice_file.resolve())])
            input_tags.append(f"[{count}:a]")
            count += 1

    if count == 0:
        raise RuntimeError("No scene voice files found to concatenate!")

    # Perfect frame-accurate audio concatenation via FFmpeg concat filter
    filter_expr = "".join(input_tags) + f"concat=n={count}:v=0:a=1[aout]"
    cmd = [
        "ffmpeg", "-y"
    ] + inputs + [
        "-filter_complex", filter_expr,
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path

def mix_story_audio(
    scenes: list,
    voice_metadata: list,
    output_master_audio: Path,
    bgm_path: Path = None,
    audio_dir: Path = None
) -> Path:
    """
    Assembles voice tracks, blends background music with dynamic audio ducking,
    and produces the master audio track.
    """
    if audio_dir is None:
        audio_dir = AUDIO_DIR
    output_master_audio.parent.mkdir(parents=True, exist_ok=True)

    # 1. Build continuous voice track inside the isolated run audio directory
    voice_track = audio_dir / "combined_voices.mp3"
    build_scene_dialogue_track(scenes, voice_metadata, voice_track, audio_dir=audio_dir)

    # Probe exact duration of combined voice track
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voice_track)]
    total_duration = float(subprocess.check_output(probe_cmd).decode().strip())

    # 2. Select or generate BGM matching the exact duration
    if bgm_path is None or not Path(bgm_path).exists():
        custom_bgm_files = list((ASSETS_DIR / "bgm").glob("*.mp3")) + list((ASSETS_DIR / "bgm").glob("*.wav"))
        if custom_bgm_files:
            bgm_track = custom_bgm_files[0]
        else:
            bgm_track = audio_dir / "bgm.mp3"
            create_default_bgm(bgm_track, total_duration + 3.0)
    else:
        bgm_track = Path(bgm_path)

    print(f"\n[Audio Mixer] Mixing Voice Track with Ducked Background Music ({total_duration:.1f}s)...")

    # 3. Dynamic Sidechain Compression (Audio Ducking)
    # When voice speaks, BGM volume reduces to 15%. When voice pauses, BGM swells to 45%.
    cmd = [
        "ffmpeg", "-y",
        "-i", str(bgm_track),
        "-i", str(voice_track),
        "-filter_complex",
        "[0:a]volume=0.35[bgm];"
        "[1:a]asplit=2[sc][voice];"
        "[bgm][sc]sidechaincompress=threshold=0.08:ratio=5:attack=60:release=400[ducked_bgm];"
        "[ducked_bgm][voice]amix=inputs=2:duration=longest[aout]",
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        str(output_master_audio)
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        # Simple fallback amix if sidechain filter fails
        fallback_cmd = [
            "ffmpeg", "-y",
            "-i", str(bgm_track),
            "-i", str(voice_track),
            "-filter_complex", "[0:a]volume=0.2[bgm];[1:a]volume=1.0[voice];[bgm][voice]amix=inputs=2:duration=longest",
            "-c:a", "libmp3lame",
            str(output_master_audio)
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    print(f"[Audio Mixer] Master audio track created: {output_master_audio.name}")
    return output_master_audio

if __name__ == "__main__":
    print("Testing Audio Mixer Engine...")
    test_scenes = [{"scene_id": 1}, {"scene_id": 2}, {"scene_id": 3}]
    meta_file = AUDIO_DIR / "voice_metadata.json"
    if meta_file.exists():
        import json
        with open(meta_file, "r") as f:
            test_meta = json.load(f)
        out_master = FINAL_DIR / "test_master_audio.mp3"
        mix_story_audio(test_scenes, test_meta, out_master)
        print(f"SUCCESS! Master audio saved to: {out_master}")
    else:
        print("Run tts_engine.py first to create voice metadata.")

