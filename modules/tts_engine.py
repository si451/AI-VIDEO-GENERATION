import os
import sys
import json
import asyncio
from pathlib import Path
import edge_tts

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import AUDIO_DIR, VOICE_MAP

def get_voice_for_speaker(speaker: str, character_bible: dict = None) -> tuple:
    """
    Resolves the designated CHILD-ONLY voice and pitch/rate modulation.
    STRICT USER REQUIREMENT: Only child voices allowed (en-US-AnaNeural or en-US-ChristopherNeural).
    """
    speaker_clean = speaker.strip().lower()

    # Default child narrator
    if speaker_clean in ("narrator", "storyteller", "narrative"):
        return VOICE_MAP.get("narrator", "en-US-AnaNeural"), "+0%", "+2Hz"

    # Check character bible mapping
    if character_bible and "characters" in character_bible:
        for char in character_bible["characters"]:
            if char.get("name", "").lower() == speaker_clean:
                vtype = char.get("voice_type", "child_male")
                if vtype in ("child_female", "animal_cute"):
                    return VOICE_MAP.get("child_female", "en-US-AnaNeural"), "+5%", "+6Hz"
                elif vtype == "child_male":
                    return VOICE_MAP.get("child_male", "en-US-ChristopherNeural"), "+0%", "+3Hz"
                else:
                    return VOICE_MAP.get("narrator", "en-US-AnaNeural"), "+0%", "+0Hz"

    # Smart fallback to child voices
    if any(k in speaker_clean for k in ("pip", "dragon", "barnaby", "bear", "boy", "cub", "christopher", "jack", "benny")):
        return VOICE_MAP.get("child_male", "en-US-ChristopherNeural"), "+0%", "+3Hz"
    else:
        return VOICE_MAP.get("child_female", "en-US-AnaNeural"), "+5%", "+6Hz"

async def generate_scene_voice(scene_id: int, text: str, voice: str, rate: str, pitch: str, output_path: Path) -> dict:
    """
    Generates high quality neural speech with exact word-level timing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    
    word_timestamps = []
    audio_data = bytearray()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            start_sec = chunk["offset"] / 10_000_000.0
            dur_sec = chunk["duration"] / 10_000_000.0
            word_timestamps.append({
                "word": chunk["text"],
                "start": round(start_sec, 3),
                "end": round(start_sec + dur_sec, 3)
            })
            
    with open(output_path, "wb") as f:
        f.write(audio_data)

    # Probe exact file duration using ffprobe for mathematically perfect sync
    import subprocess
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)]
        total_duration = float(subprocess.check_output(cmd).decode().strip())
    except Exception:
        total_duration = word_timestamps[-1]["end"] + 0.3 if word_timestamps else 3.0

    return {
        "scene_id": scene_id,
        "audio_path": str(output_path),
        "duration": round(total_duration, 3),
        "word_timestamps": word_timestamps
    }

def generate_all_scene_voices(scenes: list, character_bible: dict = None, output_audio_dir: Path = None) -> list:
    """
    Generates consistent voice tracks and word timestamps for all scenes.
    """
    if output_audio_dir is None:
        output_audio_dir = AUDIO_DIR
    output_audio_dir.mkdir(parents=True, exist_ok=True)
    results = []

    async def _run_all():
        for idx, scene in enumerate(scenes):
            scene_id = scene.get("frame_id", scene.get("scene_id", idx + 1))
            dialogue = scene["dialogue"]
            speaker = scene.get("speaker", "narrator")
            
            voice, rate, pitch = get_voice_for_speaker(speaker, character_bible)
            audio_file = output_audio_dir / f"frame_{scene_id:02d}_voice.mp3"
            
            print(f" -> Frame {scene_id:02d} [{speaker} -> {voice.split('-')[-1]}]: \"{dialogue[:40]}...\"")
            res = await generate_scene_voice(scene_id, dialogue, voice, rate, pitch, audio_file)
            res["frame_id"] = scene_id

            # Also create scene_X alias for backward compatibility
            alias_file = output_audio_dir / f"scene_{scene_id}_voice.mp3"
            if alias_file != audio_file and not alias_file.exists():
                import shutil
                shutil.copy(audio_file, alias_file)

            results.append(res)

    asyncio.run(_run_all())
    
    # Save metadata
    metadata_file = output_audio_dir / "voice_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results

if __name__ == "__main__":
    print("Testing Voice Consistency Engine...")
    bible = {
        "characters": [
            {"name": "Barnaby", "voice_type": "child_male"},
            {"name": "Squeaky", "voice_type": "animal_cute"},
            {"name": "Oliver", "voice_type": "old_wise"}
        ]
    }
    test_scenes = [
        {"scene_id": 1, "speaker": "narrator", "dialogue": "Once upon a time in the woods."},
        {"scene_id": 2, "speaker": "Barnaby", "dialogue": "I found a big jar of sweet honey!"},
        {"scene_id": 3, "speaker": "Squeaky", "dialogue": "Can you share some honey with me, Barnaby?"},
        {"scene_id": 4, "speaker": "Oliver", "dialogue": "Sharing with friends makes everyone happy."}
    ]
    voices = generate_all_scene_voices(test_scenes, character_bible=bible)
    print(f"SUCCESS: Generated {len(voices)} voice tracks with persistent character voices.")
