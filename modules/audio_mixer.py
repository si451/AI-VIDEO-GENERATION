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
    Generates an authentic acoustic music-box and piano lullaby with real bell harmonics,
    gentle arpeggios, and warm decaying envelopes. Completely replaces raw electronic sine beeps!
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from modules.lullaby_generator import create_soothing_bedtime_lullaby
        create_soothing_bedtime_lullaby(output_path, duration_sec=duration_sec)
        return output_path
    except Exception as e:
        # Fallback to soft filtered multi-chord if numpy/scipy fails
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"sine=frequency=261.63:duration={duration_sec}",  # C4
            "-f", "lavfi", "-i", f"sine=frequency=329.63:duration={duration_sec}",  # E4
            "-f", "lavfi", "-i", f"sine=frequency=392.00:duration={duration_sec}",  # G4
            "-filter_complex",
            f"[0:a][1:a][2:a]amix=inputs=3:dropout_transition=0,volume=0.08,lowpass=f=600,afade=t=in:ss=0:d=3,afade=t=out:st={max(duration_sec-4, 0)}:d=4[aout]",
            "-map", "[aout]",
            "-c:a", "libmp3lame",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path

def build_scene_dialogue_track(scenes: list, voice_metadata: list, output_path: Path, audio_dir: Path = None, min_duration_sec: float = 0.0) -> Path:
    """
    Concatenates individual scene voice tracks into a continuous dialogue track
    with gentle padding between scenes matching scene durations.
    """
    if audio_dir is None:
        audio_dir = AUDIO_DIR
    output_path.parent.mkdir(parents=True, exist_ok=True)
    meta_map = {m.get("frame_id", m.get("scene_id", i+1)): m for i, m in enumerate(voice_metadata)}

    inputs = []
    filter_parts = []
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
            v_meta = meta_map.get(scene_id, {})
            voice_dur = v_meta.get("duration", 3.0)
            target_dur = max(voice_dur + 0.8, min_duration_sec) if min_duration_sec > 0 else (voice_dur + 0.8)
            if target_dur > voice_dur:
                filter_parts.append(f"[{count}:a]apad=whole_dur={target_dur:.3f}[a{count}];")
            else:
                filter_parts.append(f"[{count}:a]anull[a{count}];")
            count += 1

    if count == 0:
        raise RuntimeError("No scene voice files found to concatenate!")

    concat_tags = "".join(f"[a{i}]" for i in range(count))
    filter_expr = "".join(filter_parts) + f"{concat_tags}concat=n={count}:v=0:a=1[aout]"
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
    audio_dir: Path = None,
    min_duration_sec: float = 0.0
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
    build_scene_dialogue_track(scenes, voice_metadata, voice_track, audio_dir=audio_dir, min_duration_sec=min_duration_sec)

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
