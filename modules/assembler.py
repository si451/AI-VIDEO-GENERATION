import os
import sys
import json
import subprocess
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def format_chapter_time(seconds: float) -> str:
    """Formats seconds to YouTube chapter timestamp: M:SS or H:MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

def assemble_final_video(
    story_data: dict,
    animated_clips: list,
    master_audio_path: Path,
    subtitles_ass_path: Path,
    output_video_path: Path,
    scenes_dir: Path = None,
    aspect_ratio: str = "9:16"
) -> dict:
    """
    Stitches video clips, mastered audio, and burned styled subtitles
    into the final YouTube-ready MP4 using hardware-accelerated NVENC.
    Supports both 9:16 vertical shorts and 16:9 widescreen.
    """
    if scenes_dir is None:
        scenes_dir = output_video_path.parent / "scenes"
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create clip concat list
    concat_list_file = scenes_dir / "clips_concat_list.txt"
    lines = []
    current_time = 0.0
    chapters = []

    frame_list = story_data.get("frames", story_data.get("scenes", []))

    for i, clip_info in enumerate(animated_clips):
        clip_path = Path(clip_info["clip_path"])
        duration = clip_info["duration"]
        fid = clip_info.get("frame_id", clip_info.get("scene_id", i + 1))
        
        # Build descriptive chapter timestamp
        if i < len(frame_list):
            diag = frame_list[i].get("dialogue", "")
            words = diag.split()[:4]
            desc = " ".join(words) if words else f"Frame {fid}"
        else:
            desc = f"Part {fid}"

        # Only add chapter markers every ~15 seconds to avoid cluttering YouTube player
        if i == 0 or current_time >= (len(chapters) * 15.0):
            chapters.append(f"{format_chapter_time(current_time)} - {desc}...")

        current_time += duration

        safe_path = str(clip_path.resolve()).replace("\\", "/")
        lines.append(f"file '{safe_path}'")

    with open(concat_list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Intermediate joined video
    raw_joined_video = scenes_dir / "raw_joined_video.mp4"
    join_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(raw_joined_video)
    ]
    subprocess.run(join_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 2. Master Render: Video + Audio + Burned Subtitles via NVENC
    print(f"\n[Assembler] Rendering Final Master Video ({aspect_ratio}) with RTX 2050 NVENC...")
    safe_sub_path = str(subtitles_ass_path.resolve()).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_joined_video),
        "-i", str(master_audio_path),
        "-vf", f"ass='{safe_sub_path}'",
        "-c:v", "h264_nvenc",
        "-preset", "p6",      # Pristine video quality
        "-cq", "18",          # High fidelity, zero compression blocks
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_video_path)
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        # Fallback to software encoding if NVENC busy
        cmd[cmd.index("h264_nvenc")] = "libx264"
        cmd[cmd.index("-preset") + 1] = "medium"
        cmd[cmd.index("-cq")] = "-crf"
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Master assembly failed: {proc.stderr}")

    # 3. Generate YouTube Metadata
    title = story_data.get("title", "Magical Bedtime Story for Children")
    moral = story_data.get("moral_lesson", "Kindness and teamwork make magic happen.")
    tags = story_data.get("seo_tags", ["bedtime stories", "fairy tales", "kids cartoon", "3D animation"])
    
    tag_prefix = "#Shorts " if aspect_ratio == "9:16" else ""
    format_label = "YouTube Short" if aspect_ratio == "9:16" else "Bedtime Story For Kids"

    description = (
        f"{title} | {format_label}\n\n"
        f"📖 Moral of the Story: {moral}\n\n"
        f"Welcome to our wholesome world of 3D Pixar-style children stories! Join Barnaby Bear and friends on cute bedtime adventures.\n\n"
        f"⏱️ Chapters:\n" + "\n".join(chapters) + "\n\n"
        f"🔔 Subscribe for daily animated adventures & bedtime stories for kids!\n\n"
        f"{tag_prefix}#KidsStories #BedtimeStories #CartoonAnimation #PixarStyle #ToddlerStories"
    )

    metadata = {
        "youtube_title": f"{title} | {format_label} | Cartoon Animation",
        "youtube_description": description,
        "youtube_tags": tags + ["bedtime story", "kids stories", "shorts", "3d cartoon", "toddler animation", "sleep story"],
        "chapters": chapters,
        "aspect_ratio": aspect_ratio,
        "final_video_path": str(output_video_path),
        "total_duration_sec": round(current_time, 3)
    }

    meta_file = output_video_path.parent / f"{output_video_path.stem}_metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[Assembler] SUCCESS! Final Video Rendered: {output_video_path.name}")
    print(f"[Assembler] YouTube Metadata Generated: {meta_file.name}")
    return metadata

def stitch_runs_into_omnibus(run_dirs: list, output_run_dir: Path, title: str = "WhimsyWand Bedtime Stories Compilation") -> dict:
    """
    Concatenates multiple completed episode runs into a single continuous YouTube compilation MP4.
    Automatically calculates continuous chapter markers with timestamps.
    """
    output_run_dir.mkdir(parents=True, exist_ok=True)
    concat_list = output_run_dir / "omnibus_concat.txt"
    lines = []
    chapters = []
    total_time = 0.0
    all_tags = set([
        "bedtime stories for kids", "cartoon for kids", "30 minutes bedtime story",
        "whimsywand tales", "disney pixar animation", "sleep story for toddlers",
        "kids animation", "soothing bedtime stories"
    ])

    for idx, r_path in enumerate(run_dirs):
        r_path = Path(r_path)
        v_path = r_path / "final_video.mp4"
        meta_file = r_path / "final_video_metadata.json"
        if not v_path.exists():
            continue

        run_title = r_path.name
        run_dur = 0.0
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    m = json.load(f)
                    run_title = m.get("youtube_title", run_title)
                    run_dur = m.get("total_duration_sec", 0.0)
                    for t in m.get("youtube_tags", []):
                        all_tags.add(t)
            except Exception:
                pass

        chapters.append(f"{format_chapter_time(total_time)} - Chapter {idx + 1}: {run_title.split('|')[0].strip()}")
        safe_path = str(v_path.resolve()).replace("\\", "/")
        lines.append(f"file '{safe_path}'")
        total_time += run_dur

    if not lines:
        raise ValueError("No valid final_video.mp4 found in the provided run directories.")

    with open(concat_list, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    final_video = output_run_dir / "final_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(final_video)
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Omnibus concatenation failed: {proc.stderr}")

    description = (
        f"{title}\n\n"
        f"🌙 A soothing Bedtime Story compilation for toddlers and kids by WhimsyWand Tales (@WhimsyWandTales)!\n"
        f"Relax and drift off to magical sleep with Pip the Dragon, Fern the Fairy, Barnaby Bear, Luna the Cloud, and Benny Bunny.\n\n"
        f"⏱️ Chapters & Timestamps:\n" + "\n".join(chapters) + "\n\n"
        f"🔔 Subscribe to WhimsyWand Tales for weekly magical bedtime stories!\n\n"
        f"#BedtimeStory #KidsStories #BedtimeCompilation #ToddlerStories #CartoonForKids #WhimsyWandTales"
    )

    metadata = {
        "youtube_title": f"{title} | Bedtime Stories For Kids | Cartoon Animation",
        "youtube_description": description,
        "youtube_tags": list(all_tags),
        "chapters": chapters,
        "aspect_ratio": "16:9",
        "final_video_path": str(final_video),
        "total_duration_sec": round(total_time, 2)
    }

    with open(output_run_dir / "final_video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata
