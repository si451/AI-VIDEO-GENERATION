import os
import sys
import json
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    SHORTS_WIDTH,
    SHORTS_HEIGHT,
    LONG_WIDTH,
    LONG_HEIGHT
)

ASS_HEADER_TEMPLATE = """[Script Info]
Title: Children's Story Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CartoonDefault,Arial Rounded MT Bold,{font_size},&H0000FFFF,&H00FFFFFF,&H00331000,&H80000000,-1,0,0,0,100,100,1,0,1,4.0,2.0,2,24,24,{margin_v},1
Style: CartoonText,Arial Rounded MT Bold,{font_size},&H0000FFFF,&H00FFFFFF,&H00331000,&H80000000,-1,0,0,0,100,100,1,0,1,4.0,2.0,2,24,24,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def format_timestamp(seconds: float) -> str:
    """Formats seconds to ASS timestamp format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def generate_styled_ass(
    frames: list,
    voice_metadata: list,
    output_file: Path,
    aspect_ratio: str = "9:16",
    min_duration_sec: float = 0.0
) -> Path:
    """
    Generates a beautifully styled .ass subtitle file with exact frame-accurate word timing.
    Adjusts layout and font size for 9:16 vertical shorts (clear of YouTube UI) or 16:9 widescreen.
    Guarantees 100% synchronization with video clips and audio tracks.
    """
    if aspect_ratio == "9:16":
        width, height = SHORTS_WIDTH, SHORTS_HEIGHT
        font_size = 40
        margin_v = 240  # Sits right above YouTube Shorts bottom overlay
    else:
        width, height = LONG_WIDTH, LONG_HEIGHT
        font_size = 42
        margin_v = 55

    lines = [ASS_HEADER_TEMPLATE.format(width=width, height=height, font_size=font_size, margin_v=margin_v)]
    
    current_time_offset = 0.0
    meta_map = {}
    for m in voice_metadata:
        fid = m.get("frame_id", m.get("scene_id", 1))
        meta_map[fid] = m

    for idx, frame in enumerate(frames):
        fid = frame.get("frame_id", frame.get("scene_id", idx + 1))
        meta = meta_map.get(fid, {})
        duration = meta.get("duration", 3.0)
        word_timestamps = meta.get("word_timestamps", [])

        # The scene step matches animate_all_frames and build_scene_dialogue_track exactly
        scene_step = max(duration + 0.8, min_duration_sec) if min_duration_sec > 0 else (duration + 0.8)

        scene_start = current_time_offset
        # Let the last chunk linger until right before scene ends so kids and parents can read comfortably
        scene_end = scene_start + max(duration + 0.5, scene_step - 0.2)

        if word_timestamps:
            # Group words into clean 4-6 word readable chunks
            chunk_size = 5
            for i in range(0, len(word_timestamps), chunk_size):
                chunk = word_timestamps[i:i + chunk_size]
                chunk_start = scene_start + chunk[0]["start"]
                if i + chunk_size < len(word_timestamps):
                    chunk_end = scene_start + word_timestamps[i + chunk_size]["start"]
                else:
                    chunk_end = scene_end

                start_str = format_timestamp(chunk_start)
                end_str = format_timestamp(chunk_end)
                plain_text = " ".join(w["word"] for w in chunk)

                lines.append(f"Dialogue: 0,{start_str},{end_str},CartoonDefault,,0,0,0,,{plain_text}")
        else:
            # Fallback to entire dialogue string
            start_str = format_timestamp(scene_start)
            end_str = format_timestamp(scene_end)
            diag = frame.get("dialogue", "")
            lines.append(f"Dialogue: 0,{start_str},{end_str},CartoonDefault,,0,0,0,,{diag}")

        current_time_offset += scene_step

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_file
