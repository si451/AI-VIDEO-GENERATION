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
from modules.thumbnail_engine import generate_video_thumbnail
from modules.progress_tracker import tracker

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
    use_local_images: bool = True,
    run_dir: Path = None,
    min_duration_sec: float = 0.0
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
        tracker.update_stage("competitors", "📈 Scanning Viral Competitors", "Scraping high-retention competitor videos (>1M views)...", 10)
        print("\n[Step 0/6] Researching Trending Competitor Formats on YouTube...")
        try:
            insights = analyze_competitors("bedtime stories for kids cartoon", max_results=5)
            print(f" -> Analyzed {insights.get('total_analyzed', 0)} top competitor videos.")
        except Exception as e:
            print(f" -> [Notice] Competitor scrape skipped: {e}")

    # STEP 1: Story & Character Memory Bible (DeepSeek)
    tracker.update_stage("script", "✍️ Drafting Script & Storyboard", f"Writing {num_frames} situational frames (~3s each)...", 20)
    target_sec = num_frames * 3
    print(f"\n[Step 1/6] Writing Script & 3-Second Frame Storyboard ({num_frames} frames, ~{target_sec}s total)...")
    story_data = generate_story(prompt_or_topic=topic, num_frames=num_frames, aspect_ratio=aspect_ratio)
    
    frames = story_data.get("frames", story_data.get("scenes", []))
    title = story_data.get("title", "Barnaby Bear Adventure")
    tracker.title = title
    char_bible = story_data.get("character_bible", {})

    print(f" -> Title: {title}")
    print(f" -> Frames: {len(frames)} situational shots (~3s each)")
    print(f" -> Characters: {[c.get('name') for c in char_bible.get('characters', [])]}")

    # Setup isolated Run Directory (use passed run_dir if provided to keep everything in ONE single folder)
    if run_dir is None:
        run_dir = get_next_run_dir(title)
    else:
        run_dir = Path(run_dir)
        (run_dir / "scenes").mkdir(parents=True, exist_ok=True)
        (run_dir / "audio").mkdir(parents=True, exist_ok=True)
    scenes_dir = run_dir / "scenes"
    audio_dir = run_dir / "audio"
    print(f" -> Isolated Run Directory: {run_dir.resolve()}")

    # Save complete story package in the run folder
    with open(run_dir / "story_package.json", "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=2, ensure_ascii=False)

    # STEP 2: Multi-Character Voiceover with Word Timestamps (STRICT CHILD VOICES ONLY)
    tracker.update_stage("voice", "🎙️ Child Voiceover & Dialogue", f"Synthesizing {len(frames)} child voices (AnaNeural & ChristopherNeural)...", 35)
    print("\n[Step 2/6] Generating Child-Only Dialogue & Narration (Edge-TTS)...")
    voice_metadata = generate_all_scene_voices(frames, character_bible=char_bible, output_audio_dir=audio_dir)
    print(f" -> Generated {len(voice_metadata)} child voice tracks.")

    # STEP 3: Generate Local 3D Disney/Pixar Illustrations (No Repetitions)
    tracker.update_stage("visuals", "🎨 Rendering 3D Disney/Pixar Frames", f"Generating {len(frames)} frames locally on RTX 2050 ({aspect_ratio})...", 45)
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
    tracker.update_stage("motion", "🎥 Animating Camera Motion", "Applying smooth slow zoom/pan motion (NVENC 30fps)...", 80)
    print(f"\n[Step 4/6] Animating Frames with Smooth Slow Zoom/Pan (NVENC 30fps)...")
    clip_paths = animate_all_frames(frames, voice_metadata, aspect_ratio=aspect_ratio, scenes_dir=scenes_dir, min_duration_sec=min_duration_sec)

    animated_clips = []
    dur_map = {v.get("frame_id", v.get("scene_id", i+1)): max(v["duration"] + 0.8, min_duration_sec) if min_duration_sec > 0 else (v["duration"] + 0.8) for i, v in enumerate(voice_metadata)}
    for idx, cp in enumerate(clip_paths):
        fid = frames[idx].get("frame_id", idx + 1)
        animated_clips.append({
            "frame_id": fid,
            "scene_id": fid,
            "clip_path": str(cp),
            "duration": dur_map.get(fid, 3.8)
        })

    # STEP 5: Subtitles & Background Music Mixing
    tracker.update_stage("motion", "📝 Karaoke Subtitles & Ducked BGM", "Styling ASS subtitles and mixing background music...", 88)
    print(f"\n[Step 5/6] Styling Subtitles ({aspect_ratio}) & Mixing Ducked Audio...")
    subtitles_ass = run_dir / "subtitles.ass"
    generate_styled_ass(frames, voice_metadata, subtitles_ass, aspect_ratio=aspect_ratio, min_duration_sec=min_duration_sec)

    master_audio = audio_dir / "master_audio.mp3"
    mix_story_audio(frames, voice_metadata, master_audio, audio_dir=audio_dir, min_duration_sec=min_duration_sec)

    # STEP 6: Master Assembly (NVENC GPU Stitching & YouTube Metadata)
    tracker.update_stage("assembly", "🎞️ NVENC Master Video Assembly", "Encoding final 1080p MP4 via NVIDIA hardware...", 94)
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
    # Generate High-CTR YouTube Thumbnail
    try:
        generate_video_thumbnail(run_dir, title=metadata.get("youtube_title", "Bedtime Stories for Kids"))
    except Exception as e:
        print(f" -> [Notice] Thumbnail generation skipped: {e}")

    print(f" -> Master Video: {final_video.resolve()}")
    print(f" -> YouTube Title: {metadata.get('youtube_title')}")
    print(f" -> Total Duration: {metadata.get('total_duration_sec', 0):.2f} seconds")
    print(f" -> Run Package: {run_dir.resolve()}")

    tracker.complete_job(
        reply=f"🎉 Full Video Production Complete!\n- Title: {metadata.get('youtube_title')}\n- Duration: {metadata.get('total_duration_sec', 0):.1f}s\n- Video: {final_video.name}",
        video_url=f"/media/runs/{run_dir.name}/final_video.mp4",
        run_dir=str(run_dir)
    )

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


def run_omnibus_pipeline(
    topic: str = "WhimsyWand Bedtime Stories Omnibus",
    chapter_topics: list = None,
    num_chapters: int = 5,
    frames_per_chapter: int = 25,
    target_duration_minutes: float = 30.0,
    seconds_per_scene: float = 8.0,
    aspect_ratio: str = "16:9",
    use_local_images: bool = True,
    run_dir: Path = None
) -> dict:
    """
    Executes a complete Bedtime Story Omnibus compilation inside ONE single run directory.
    - Scales dynamically to any requested duration (5 minutes, 15 minutes, or 30 minutes).
    - Accepts custom chapter topics so the agent can pass its own non-repeating stories!
    - Guarantees: EXACTLY ONE folder created in output/runs/ (e.g. output/runs/run_001_..._30Min_Omnibus/)
    - All scenes, voices, chapter clips, thumbnail, and final_video.mp4 live inside this single folder.
    """
    from modules.assembler import stitch_chapter_files
    import json
    
    # Calculate accurate title slug
    dur_label = f"{int(round(target_duration_minutes))}Min" if target_duration_minutes >= 2 else "Short"
    safe_topic = re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_")[:25]
    folder_title = f"WhimsyWand_{safe_topic}_{dur_label}_Omnibus" if safe_topic else f"WhimsyWand_Bedtime_{dur_label}_Omnibus"

    if run_dir is None:
        run_dir = get_next_run_dir(folder_title)
    else:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

    scenes_dir = run_dir / "scenes"
    audio_dir = run_dir / "audio"
    chapters_dir = run_dir / "chapters"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    chapters_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse or dynamically construct chapter topics
    parsed_chapters = []
    if chapter_topics:
        if isinstance(chapter_topics, str):
            if chapter_topics.strip().startswith("[") and chapter_topics.strip().endswith("]"):
                try:
                    parsed_chapters = json.loads(chapter_topics)
                except Exception:
                    parsed_chapters = [c.strip() for c in chapter_topics.split(",") if c.strip()]
            else:
                parsed_chapters = [c.strip() for c in chapter_topics.split(",") if c.strip()]
        elif isinstance(chapter_topics, list):
            parsed_chapters = chapter_topics

    # Mascot roster for fallback chapter generation (never repeating published videos!)
    DEFAULT_MASCOT_CONCEPTS = [
        {"mascot": "Pip the Baby Dragon", "title": "Pip and the Starlight Compass", "theme": "Pip uses his tiny warm spark to help a lost baby owl find its nest under the glowing moon"},
        {"mascot": "Fern the Forest Fairy", "title": "Fern and the Whispering Moss", "theme": "Fern sprinkles starlight dew on sleepy forest flowers so they bloom sweet bedtime dreams"},
        {"mascot": "Barnaby Bear", "title": "Barnaby Bear's Blanket of Pine", "theme": "Barnaby gently shares his cozy pine needle blanket with tired little forest creatures"},
        {"mascot": "Squeaky Squirrel", "title": "Squeaky and the Golden Acorn Lantern", "theme": "Squeaky hangs glowing golden acorn lanterns high in the oak tree to light the bedtime path"},
        {"mascot": "Benny Bunny", "title": "Benny Bunny's Moonbeam Voyage", "theme": "Benny Bunny follows gentle silver moonbeams across the meadow into cozy bedtime sleep"}
    ]

    final_chapter_configs = []
    for i in range(num_chapters):
        if i < len(parsed_chapters) and parsed_chapters[i]:
            c_name = parsed_chapters[i]
            final_chapter_configs.append({
                "title": c_name,
                "theme": f"{c_name} starring our WhimsyWand mascots, cozy soothing bedtime moral story"
            })
        else:
            def_idx = i % len(DEFAULT_MASCOT_CONCEPTS)
            final_chapter_configs.append(DEFAULT_MASCOT_CONCEPTS[def_idx])

    # 2. Mathematical Target Scaling
    # Target seconds per chapter
    target_total_sec = target_duration_minutes * 60.0
    target_sec_per_chapter = target_total_sec / num_chapters
    effective_seconds_per_scene = max(3.5, target_sec_per_chapter / max(1, frames_per_chapter))
    total_frames = num_chapters * frames_per_chapter

    tracker.start_job(
        job_id=run_dir.name[:12],
        title=f"{topic} ({target_duration_minutes:.0f} Min)",
        total_frames=total_frames,
        aspect_ratio=aspect_ratio
    )

    chapter_video_paths = []
    chapter_titles = []
    all_story_packages = []

    print("\n" + "="*75)
    print(f"   AI BEDTIME OMNIBUS PRODUCTION: SINGLE FOLDER SCALABLE PIPELINE")
    print(f"   Target Runtime: {target_duration_minutes:.1f} Minutes (~{target_total_sec:.0f}s total)")
    print(f"   Target Directory: {run_dir.name}")
    print(f"   Chapters: {num_chapters} (~{target_sec_per_chapter/60:.1f} mins each) • Frames: {total_frames} (~{effective_seconds_per_scene:.1f}s/frame)")
    print("="*75)

    for ch_idx, cfg in enumerate(final_chapter_configs):
        ch_num = ch_idx + 1
        ch_title = cfg["title"]
        ch_theme = cfg["theme"]
        chapter_titles.append(ch_title)

        tracker.update_stage(
            "script",
            f"✍️ Scripting Chapter {ch_num}/{num_chapters}: {ch_title}",
            f"Writing {frames_per_chapter} frames (~{effective_seconds_per_scene:.1f}s scene pacing)...",
            10 + int((ch_idx / num_chapters) * 20)
        )

        print(f"\n[Omnibus Chapter {ch_num}/{num_chapters}] Writing Script: {ch_title} ({frames_per_chapter} frames)...")
        ch_story = generate_story(prompt_or_topic=ch_theme, num_frames=frames_per_chapter, aspect_ratio=aspect_ratio)
        ch_frames = ch_story.get("frames", ch_story.get("scenes", []))
        ch_bible = ch_story.get("character_bible", {})
        all_story_packages.append(ch_story)

        # 1. Voiceover for this chapter
        tracker.update_stage(
            "voice",
            f"🎙️ Voices for Chapter {ch_num}/{num_chapters}",
            f"Synthesizing sweet child voices ({ch_title})...",
            30 + int((ch_idx / num_chapters) * 15)
        )
        print(f"[Omnibus Chapter {ch_num}/{num_chapters}] Generating Child Voices...")
        ch_voice_metadata = generate_all_scene_voices(ch_frames, character_bible=ch_bible, output_audio_dir=audio_dir)

        # 2. Local 3D Disney/Pixar illustrations into scenes_dir
        tracker.update_stage(
            "visuals",
            f"🎨 Rendering 3D Visuals: Chapter {ch_num}/{num_chapters}",
            f"Synthesizing {len(ch_frames)} frames on RTX 2050...",
            45 + int((ch_idx / num_chapters) * 35)
        )
        print(f"[Omnibus Chapter {ch_num}/{num_chapters}] Rendering 3D Pixar Visuals on RTX 2050...")
        if use_local_images:
            generate_all_frame_images(ch_frames, aspect_ratio=aspect_ratio, master_seed=42 + (ch_num * 100), auto_free_vram=True, output_dir=scenes_dir)
        else:
            from PIL import Image, ImageDraw
            w, h = (768, 512)
            for idx, fr in enumerate(ch_frames):
                fid = fr.get("frame_id", idx + 1)
                img = Image.new("RGB", (w, h), color=((40 + ch_num*30) % 255, (50 + fid*20) % 255, (80 + fid*15) % 255))
                draw = ImageDraw.Draw(img)
                draw.text((30, h//2), f"Ch{ch_num} Frame {fid:02d}", fill=(255, 255, 255))
                img.save(scenes_dir / f"frame_{fid:02d}.jpg")

        free_gpu()

        # 3. Motion & audio assembly for this chapter with effective scene pacing
        tracker.update_stage(
            "motion",
            f"🎥 Animating Chapter {ch_num}/{num_chapters}",
            f"Applying 30fps slow zoom/pan ({effective_seconds_per_scene:.1f}s per scene)...",
            80 + int((ch_idx / num_chapters) * 10)
        )
        clip_paths = animate_all_frames(
            ch_frames,
            ch_voice_metadata,
            aspect_ratio=aspect_ratio,
            scenes_dir=scenes_dir,
            min_duration_sec=effective_seconds_per_scene
        )

        animated_clips = []
        dur_map = {v.get("frame_id", v.get("scene_id", i+1)): max(v["duration"] + 0.8, effective_seconds_per_scene) for i, v in enumerate(ch_voice_metadata)}
        for idx, cp in enumerate(clip_paths):
            fid = ch_frames[idx].get("frame_id", idx + 1)
            animated_clips.append({
                "frame_id": fid,
                "scene_id": fid,
                "clip_path": str(cp),
                "duration": dur_map.get(fid, effective_seconds_per_scene)
            })

        ch_subtitles = run_dir / f"chapter_{ch_num:02d}_subtitles.ass"
        generate_styled_ass(ch_frames, ch_voice_metadata, ch_subtitles, aspect_ratio=aspect_ratio, min_duration_sec=effective_seconds_per_scene)

        ch_master_audio = audio_dir / f"chapter_{ch_num:02d}_audio.mp3"
        mix_story_audio(
            ch_frames,
            ch_voice_metadata,
            ch_master_audio,
            audio_dir=audio_dir,
            min_duration_sec=effective_seconds_per_scene
        )

        ch_video_path = chapters_dir / f"chapter_{ch_num:02d}.mp4"
        assemble_final_video(
            story_data=ch_story,
            animated_clips=animated_clips,
            master_audio_path=ch_master_audio,
            subtitles_ass_path=ch_subtitles,
            output_video_path=ch_video_path,
            scenes_dir=scenes_dir,
            aspect_ratio=aspect_ratio
        )
        chapter_video_paths.append(ch_video_path)
        print(f" -> Chapter {ch_num:02d} rendered: {ch_video_path.name}")

    # 4. Final Omnibus Stitching inside THIS SINGLE RUN FOLDER
    tracker.update_stage(
        "assembly",
        "🎞️ Assembling Final Master Video",
        "Concatenating all chapters with continuous YouTube timestamps...",
        95
    )
    print("\n[Master Omnibus Stitching] Concatenating chapters into final_video.mp4...")
    actual_title = f"{topic} | Bedtime Stories For Kids | Cartoon Animation"
    metadata = stitch_chapter_files(
        chapter_video_paths=chapter_video_paths,
        output_run_dir=run_dir,
        chapter_titles=chapter_titles,
        title=actual_title
    )

    # Calculate actual runtime
    actual_sec = metadata.get("total_duration_sec", 0.0)
    actual_min = actual_sec / 60.0

    # Save omnibus manifest package
    with open(run_dir / "story_package.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": topic,
            "target_duration_minutes": target_duration_minutes,
            "actual_duration_seconds": actual_sec,
            "actual_duration_minutes": round(actual_min, 2),
            "chapters": all_story_packages,
            "metadata": metadata
        }, f, indent=2, ensure_ascii=False)

    # 5. Automatically Generate High-CTR 1280x720 YouTube Thumbnail
    try:
        generate_video_thumbnail(run_dir, title=actual_title)
    except Exception as e:
        print(f" -> [Notice] Thumbnail generation skipped: {e}")

    final_video = run_dir / "final_video.mp4"
    tracker.complete_job(
        reply=(
            f"🎉 **Master Bedtime Story Omnibus Production Complete!**\n\n"
            f"- **Single Self-Contained Folder**: `{run_dir.name}` (Zero duplicate folders)\n"
            f"- **Master Video**: `{final_video.name}`\n"
            f"- **Actual Duration**: {actual_min:.1f} minutes ({actual_sec:.1f} seconds)\n"
            f"- **Chapters Included**:\n" + "\n".join(metadata.get('chapters', [])) + "\n\n"
            f"- **YouTube SEO Title**: {metadata.get('youtube_title')}\n"
            f"- **1280×720 Thumbnail**: Saved inside run folder (`thumbnail.jpg` and `thumbnail_with_title.jpg`)"
        ),
        video_url=f"/media/runs/{run_dir.name}/final_video.mp4",
        run_dir=str(run_dir)
    )

    return {
        "run_dir": str(run_dir),
        "final_video": str(final_video),
        "duration": actual_sec,
        "metadata": metadata
    }
