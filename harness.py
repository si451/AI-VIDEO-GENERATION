import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure robust UTF-8 printing on Windows PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import OUTPUT_DIR, MEMORY_DIR
from modules.competitor_engine import analyze_competitors
from modules.story_engine import generate_story
from modules.tts_engine import generate_all_scene_voices
from modules.visual_engine import generate_all_frame_images, free_gpu
from modules.motion_engine import animate_all_frames
from modules.subtitle_engine import generate_styled_ass
from modules.audio_mixer import mix_story_audio
from modules.assembler import assemble_final_video

RUNS_DIR = OUTPUT_DIR / "runs"

def get_next_run_dir(title: str) -> Path:
    """
    Creates an isolated run directory: output/runs/run_{id:03d}_{timestamp}_{title_slug}/
    Guarantees every video run is completely self-contained with no file collisions.
    """
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    existing_runs = [d for d in RUNS_DIR.iterdir() if d.is_dir() and d.name.startswith("run_")]
    run_num = len(existing_runs) + 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title_slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_")[:30]
    run_name = f"run_{run_num:03d}_{timestamp}_{title_slug}"
    
    run_dir = RUNS_DIR / run_name
    (run_dir / "scenes").mkdir(parents=True, exist_ok=True)
    (run_dir / "audio").mkdir(parents=True, exist_ok=True)
    return run_dir

def run_production_pipeline(
    topic: str = None,
    num_frames: int = 10,
    aspect_ratio: str = "9:16",
    use_competitor_trends: bool = False,
    use_local_images: bool = True
) -> dict:
    """
    Executes the complete high-retention Children's YouTube Harness.
    - Pacing: ~3 seconds per visual frame.
    - Voices: Strict sweet child voices only.
    - Aspect Ratio: 9:16 (Shorts: 720x1280) or 16:9 (Long: 1280x720).
    - Camera Motion: Butter-smooth slow zoom / pan with zero jitter.
    """
    print("\n" + "="*75)
    print(f"   AI CHILDREN'S STUDIO: PRODUCTION PIPELINE [{aspect_ratio}]")
    print("="*75)

    # STEP 0: Competitor Research (Optional)
    if use_competitor_trends:
        print("\n[Step 0/6] Researching Trending Competitor Formats on YouTube...")
        try:
            insights = analyze_competitors("bedtime stories for kids cartoon", max_results=5)
            print(f" -> Analyzed {insights.get('total_analyzed', 0)} top competitor videos.")
        except Exception as e:
            print(f" -> [Notice] Competitor scrape skipped: {e}")

    # STEP 1: Story & Character Memory Bible (DeepSeek)
    target_sec = num_frames * 3
    print(f"\n[Step 1/6] Writing Script & 3-Second Frame Storyboard ({num_frames} frames, ~{target_sec}s total)...")
    story_data = generate_story(prompt_or_topic=topic, num_frames=num_frames, aspect_ratio=aspect_ratio)
    
    frames = story_data.get("frames", story_data.get("scenes", []))
    title = story_data.get("title", "Barnaby Bear Adventure")
    char_bible = story_data.get("character_bible", {})

    print(f" -> Title: {title}")
    print(f" -> Frames: {len(frames)} situational shots (~3s each)")
    print(f" -> Characters: {[c.get('name') for c in char_bible.get('characters', [])]}")

    # Setup isolated Run Directory
    run_dir = get_next_run_dir(title)
    scenes_dir = run_dir / "scenes"
    audio_dir = run_dir / "audio"
    print(f" -> Isolated Run Directory: {run_dir.resolve()}")

    # Save complete story package in the run folder
    with open(run_dir / "story_package.json", "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=2, ensure_ascii=False)

    # STEP 2: Multi-Character Voiceover with Word Timestamps (STRICT CHILD VOICES ONLY)
    print("\n[Step 2/6] Generating Child-Only Dialogue & Narration (Edge-TTS)...")
    voice_metadata = generate_all_scene_voices(frames, character_bible=char_bible, output_audio_dir=audio_dir)
    print(f" -> Generated {len(voice_metadata)} child voice tracks.")

    # STEP 3: Generate Local 3D Disney/Pixar Illustrations (No Repetitions)
    if use_local_images:
        print(f"\n[Step 3/6] Generating {len(frames)} Disney/Pixar Frames locally on RTX 2050 ({aspect_ratio})...")
        generate_all_frame_images(frames, aspect_ratio=aspect_ratio, master_seed=42, auto_free_vram=True, output_dir=scenes_dir)
    else:
        print("\n[Step 3/6] Skipping image generation (using placeholders)...")
        from PIL import Image, ImageDraw
        w, h = (512, 896) if aspect_ratio == "9:16" else (768, 512)
        for idx, fr in enumerate(frames):
            fid = fr.get("frame_id", idx + 1)
            img = Image.new("RGB", (w, h), color=((30 + fid*20) % 180, (40 + fid*25) % 200, (70 + fid*30) % 230))
            draw = ImageDraw.Draw(img)
            draw.text((20, h//2 - 20), f"Frame {fid:02d}: {fr.get('dialogue', '')[:35]}...", fill=(255, 255, 255))
            img.save(scenes_dir / f"frame_{fid:02d}.jpg")
            img.save(scenes_dir / f"scene_{fid}.jpg")

    free_gpu()

    # STEP 4: Butter-Smooth 2.5D Camera Motion (NVENC 30fps)
    print(f"\n[Step 4/6] Animating Frames with Smooth Slow Zoom/Pan (NVENC 30fps)...")
    clip_paths = animate_all_frames(frames, voice_metadata, aspect_ratio=aspect_ratio, scenes_dir=scenes_dir)

    animated_clips = []
    dur_map = {v.get("frame_id", v.get("scene_id", i+1)): v["duration"] for i, v in enumerate(voice_metadata)}
    for idx, cp in enumerate(clip_paths):
        fid = frames[idx].get("frame_id", idx + 1)
        animated_clips.append({
            "frame_id": fid,
            "scene_id": fid,
            "clip_path": str(cp),
            "duration": dur_map.get(fid, 3.0)
        })

    # STEP 5: Subtitles & Background Music Mixing
    print(f"\n[Step 5/6] Styling Subtitles ({aspect_ratio}) & Mixing Ducked Audio...")
    subtitles_ass = run_dir / "subtitles.ass"
    generate_styled_ass(frames, voice_metadata, subtitles_ass, aspect_ratio=aspect_ratio)

    master_audio = audio_dir / "master_audio.mp3"
    mix_story_audio(frames, voice_metadata, master_audio, audio_dir=audio_dir)

    # STEP 6: Master Assembly (NVENC GPU Stitching & YouTube Metadata)
    print(f"\n[Step 6/6] Assembling Master Final Video ({aspect_ratio})...")
    final_video = run_dir / "final_video.mp4"

    metadata = assemble_final_video(
        story_data=story_data,
        animated_clips=animated_clips,
        master_audio_path=master_audio,
        subtitles_ass_path=subtitles_ass,
        output_video_path=final_video,
        scenes_dir=scenes_dir,
        aspect_ratio=aspect_ratio
    )

    print("\n" + "="*75)
    print(f"      PRODUCTION COMPLETE! {aspect_ratio} READY FOR PUBLISHING")
    print("="*75)
    print(f" -> Master Video: {final_video.resolve()}")
    print(f" -> YouTube Title: {metadata.get('youtube_title')}")
    print(f" -> Total Duration: {metadata.get('total_duration_sec', 0):.2f} seconds")
    print(f" -> Run Package: {run_dir.resolve()}")

    return {
        "run_dir": str(run_dir),
        "final_video": str(final_video),
        "duration": metadata.get("total_duration_sec", 0),
        "metadata": metadata
    }

# Backward-compatibility alias
run_pipeline = run_production_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Children's YouTube Channel Harness")
    parser.add_argument("--topic", type=str, default=None, help="Story topic or character idea")
    parser.add_argument("--frames", type=int, default=10, help="Number of 3-second frames (~30s for 10 frames)")
    parser.add_argument("--aspect", type=str, default="9:16", choices=["9:16", "16:9"], help="Video aspect ratio: 9:16 (Shorts) or 16:9 (Long)")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation for quick testing")
    args = parser.parse_args()

    run_production_pipeline(
        topic=args.topic,
        num_frames=args.frames,
        aspect_ratio=args.aspect,
        use_local_images=not args.skip_images
    )
