import os
import sys
import json
import asyncio
from pathlib import Path
from langchain_core.tools import tool

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from modules.competitor_engine import analyze_competitors
from modules.story_engine import generate_story
from modules.visual_engine import generate_frame_image, free_gpu
from modules.tts_engine import generate_scene_voice
from modules.assembler import stitch_runs_into_omnibus
from config import OUTPUT_DIR, MEMORY_DIR, VOICE_MAP
import harness

@tool
def inspect_my_channel_tool() -> str:
    """
    Retrieves the complete profile of our YouTube channel 'WhimsyWand Tales' (@WhimsyWandTales).
    Includes our mascots (Pip the Baby Dragon, Fern the Fairy, Barnaby Bear), tagline, published videos,
    and viral growth strategy.
    """
    channel_file = MEMORY_DIR / "my_channel.json"
    if not channel_file.exists():
        return "Channel memory file not found."
    try:
        with open(channel_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        chars = [c.get("name") for c in data.get("core_characters", [])]
        published = [v.get("title") for v in data.get("published_video_audit", [])]
        out = (
            f"### Channel Profile: {data.get('channel_name')} ({data.get('handle')})\n"
            f"**Tagline**: {data.get('tagline')}\n"
            f"**Audience**: {data.get('target_audience')}\n"
            f"**Core Characters**: {', '.join(chars)}\n"
            f"**Voice Rule**: {data.get('voice_rules')}\n\n"
            f"**Published Videos (Do not repeat these)**:\n" + "\n".join(f"- {p}" for p in published) + "\n\n"
            f"**Growth Goal**: Model competitor viral hits (>1M views), use ~3-second situational frames, child voices only, and curiosity-gap titles."
        )
        return out
    except Exception as e:
        return f"Error reading channel profile: {str(e)}"

@tool
def analyze_competitors_tool(query: str = "bedtime stories for kids cartoon") -> str:
    """
    Scrapes high-performing competitor videos on YouTube in the children's story niche.
    Returns top ranking titles, view counts, viral patterns, and tags.
    """
    try:
        insights = analyze_competitors(query=query, max_results=6)
        top_vids = insights.get("top_videos", [])
        summary = f"Scraped {len(top_vids)} top-performing competitor videos for '{query}':\n\n"
        for idx, v in enumerate(top_vids, 1):
            summary += f"{idx}. '{v['title']}' ({v['views']:,} views, by {v['channel']})\n"
        summary += f"\nTop viral keywords/tags: {', '.join(insights.get('top_keywords', [])[:10])}\n"
        return summary
    except Exception as e:
        return f"Error analyzing competitors: {str(e)}"

@tool
def draft_story_script_tool(topic: str = "", num_frames: int = 10, aspect_ratio: str = "9:16") -> str:
    """
    Drafts an episodic story script broken into ~3-second situational frames.
    For a 30s Short, use num_frames=10, aspect_ratio='9:16'.
    For a Long episode chapter, use num_frames=15, aspect_ratio='16:9'.
    Includes persistent Disney/Pixar visual anchors, child dialogues, and camera motions.
    """
    try:
        # Normalize and cap frame count safely (max 25 frames per chapter to ensure reliability)
        clean_frames = 10 if aspect_ratio == "9:16" else 15
        if num_frames:
            try:
                clean_frames = min(max(int(num_frames), 3), 25)
            except Exception:
                pass

        clean_topic = topic.strip() if topic and isinstance(topic, str) and topic.strip() else None
        story = generate_story(prompt_or_topic=clean_topic, num_frames=clean_frames, aspect_ratio=aspect_ratio)
        title = story.get("title", "Untitled Episode")
        moral = story.get("moral_lesson", "")
        chars = story.get("character_bible", {}).get("characters", [])
        frames = story.get("frames", story.get("scenes", []))
        
        out = f"### Drafted Story: {title} ({aspect_ratio})\n"
        out += f"**Moral Lesson**: {moral}\n"
        out += f"**Target Age**: {story.get('target_age', '3-7')}\n"
        out += f"**Total Frames**: {len(frames)} (~{len(frames)*3} seconds total)\n\n"
        out += "#### Characters:\n"
        for c in chars:
            out += f"- **{c.get('name')}** ({c.get('role')}): Voice={c.get('voice_type')}, Anchor={c.get('visual_anchor')}\n"
        out += f"\n#### Frames (~3s each):\n"
        for f in frames:
            fid = f.get("frame_id", f.get("scene_id", 1))
            out += f"**Frame {fid:02d}** [{f.get('speaker')}]: \"{f.get('dialogue')}\" | Motion: `{f.get('camera_motion')}`\n"
        
        # Save active draft
        active_draft_file = MEMORY_DIR / "active_story_draft.json"
        with open(active_draft_file, "w", encoding="utf-8") as file:
            json.dump(story, file, indent=2, ensure_ascii=False)
            
        return out
    except Exception as e:
        return f"Error drafting story script: {str(e)}"

@tool
def preview_character_image_tool(prompt: str, aspect_ratio: str = "9:16") -> str:
    """
    Renders a test 3D Disney/Pixar cartoon character or scene image locally on RTX 2050.
    Supports 9:16 vertical (512x896) or 16:9 widescreen (768x512).
    Returns the file path of the saved evaluation image.
    """
    try:
        eval_dir = OUTPUT_DIR / "evaluations"
        eval_dir.mkdir(parents=True, exist_ok=True)
        out_path = eval_dir / "preview_agent_image.jpg"
        
        full_prompt = f"{prompt}, 3D Disney Pixar animation style, volumetric studio lighting, vibrant colors, 8k render"
        generate_frame_image(1, full_prompt, aspect_ratio=aspect_ratio, seed=42, output_dir=eval_dir)
        free_gpu()
        return f"Image successfully rendered locally ({aspect_ratio}) at: {out_path}"
    except Exception as e:
        return f"Error rendering preview image: {str(e)}"

@tool
def preview_voice_sample_tool(text: str, role: str = "child_male") -> str:
    """
    Generates a spoken voice sample using Edge-TTS.
    STRICT REQUIREMENT: Only child voices are permitted ('child_female', 'child_male', 'narrator').
    """
    try:
        eval_dir = OUTPUT_DIR / "evaluations"
        eval_dir.mkdir(parents=True, exist_ok=True)
        out_path = eval_dir / f"voice_preview_{role}.mp3"
        
        voice_id = VOICE_MAP.get(role, VOICE_MAP["narrator"])
        asyncio.run(generate_scene_voice(0, text, voice_id, "+0%", "+2Hz", out_path))
        return f"Child voice sample generated for role '{role}' ({voice_id}) at: {out_path}"
    except Exception as e:
        return f"Error generating voice sample: {str(e)}"

@tool
def render_full_video_tool(topic: str = "", num_frames: int = 10, aspect_ratio: str = "9:16") -> str:
    """
    Executes the entire end-to-end production harness pipeline:
    1. Writes script with 3-second frame pacing
    2. Generates local Disney/Pixar illustrations per frame (no repetitions, frame_01.jpg, frame_02.jpg...)
    3. Synthesizes child-only dialogue
    4. Generates animated ASS karaoke subtitles
    5. Renders butter-smooth slow zoom/pan camera motion (NVENC 30fps)
    6. Mixes audio with dynamic BGM ducking
    7. Assembles final 1080p MP4 and YouTube chapter metadata in an isolated run folder.
    """
    try:
        result = harness.run_production_pipeline(
            topic=topic if topic else None,
            num_frames=num_frames,
            aspect_ratio=aspect_ratio,
            use_local_images=True
        )
        final_video = result.get("final_video")
        run_dir = result.get("run_dir")
        duration = result.get("duration", 0)
        metadata = result.get("metadata", {})
        
        return (
            f"🎉 Full Video Production Complete!\n"
            f"- **Format**: {aspect_ratio} ({'YouTube Short' if aspect_ratio == '9:16' else 'Long Episode'})\n"
            f"- **Run Directory**: {run_dir}\n"
            f"- **Final Video File**: {final_video}\n"
            f"- **Total Duration**: {duration:.2f} seconds ({num_frames} frames @ ~3s each)\n"
            f"- **YouTube Title**: {metadata.get('youtube_title')}\n"
            f"- **Chapters**: {len(metadata.get('chapters', []))} marked"
        )
    except Exception as e:
        return f"Error rendering full video: {str(e)}"

@tool
def list_completed_runs_tool() -> str:
    """
    Lists all previously produced video runs with their folder names, titles, durations, and file paths.
    """
    runs_dir = OUTPUT_DIR / "runs"
    if not runs_dir.exists():
        return "No production runs found yet."
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    if not runs:
        return "No production runs found yet."
    
    summary = f"Found {len(runs)} production runs:\n\n"
    for r in runs:
        meta_file = r / "final_video_metadata.json"
        video_file = r / "final_video.mp4"
        title = r.name
        dur = "Unknown"
        aspect = "16:9"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title = data.get("youtube_title", data.get("title", r.name))
                    dur_val = data.get("total_duration_sec", data.get("duration_seconds", 0))
                    dur = f"{dur_val:.1f}s"
                    aspect = data.get("aspect_ratio", "16:9")
            except Exception:
                pass
        summary += f"- **{r.name}** [{aspect}]\n  Title: {title}\n  Duration: {dur}\n  Video: {video_file} ({'EXISTS' if video_file.exists() else 'MISSING'})\n\n"
    return summary

@tool
def get_viral_seo_package_tool(title: str, moral: str, aspect_ratio: str = "9:16") -> str:
    """
    Generates high-CTR title formulas, keyword-stuffed YouTube descriptions, hashtags, and viral tags.
    """
    tag_prefix = "#Shorts " if aspect_ratio == "9:16" else ""
    format_label = "Short" if aspect_ratio == "9:16" else "Bedtime Story"

    formulas = [
        f"{title} | {format_label} For Kids | Cartoon Animation",
        f"🌟 Can Barnaby Help? {title} | Moral Bedtime Story",
        f"{title} 🐻 {tag_prefix}Kids Animation"
    ]
    tags = [
        "bedtime stories for kids", "cartoon for kids", "disney animation story", "children bedtime story",
        "kids cartoon", "moral stories for kids", "teamwork for kids", "toddler stories", "shorts", "animation shorts"
    ]
    
    package = (
        f"### Viral YouTube Publishing Package ({aspect_ratio})\n\n"
        f"**Top 3 High-CTR Title Formulas**:\n"
        + "\n".join(f"{i+1}. {f}" for i, f in enumerate(formulas))
        + f"\n\n**Viral Tags (Copy & Paste to YouTube Studio)**:\n"
        + ", ".join(tags)
        + f"\n\n**Description Template**:\n"
        + f"Welcome to our magical storyland! In this {format_label}, join our beloved friends as they discover that: {moral}.\n\n"
        + "🔔 Subscribe for daily wholesome children's cartoon stories!\n"
        + f"{tag_prefix}#KidsStories #BedtimeStory #CartoonAnimation #ChildrensBooks #KidsAnimation"
    )
    return package

@tool
def compile_omnibus_tool(title: str = "WhimsyWand Tales Bedtime Stories 30-Minute Omnibus") -> str:
    """
    Compiles all previously generated episode runs into a single continuous 16:9 Master Omnibus video
    with automatic continuous chapter markers and timestamps for YouTube.
    """
    try:
        runs_dir = OUTPUT_DIR / "runs"
        completed = sorted([d for d in runs_dir.iterdir() if d.is_dir() and (d / "final_video.mp4").exists()])
        if not completed:
            return "No completed video runs found to compile."

        out_run_dir = harness.get_next_run_dir("WhimsyWand_Bedtime_Omnibus")
        metadata = stitch_runs_into_omnibus(completed, out_run_dir, title=title)
        
        return (
            f"🎉 Master Bedtime Story Omnibus Successfully Compiled!\n\n"
            f"- **Master File**: {metadata.get('final_video_path')}\n"
            f"- **Total Duration**: {metadata.get('total_duration_sec', 0):.2f}s (~{metadata.get('total_duration_sec', 0)/60:.1f} minutes)\n"
            f"- **Chapters Included**:\n" + "\n".join(metadata.get('chapters', [])) + "\n\n"
            f"- **YouTube SEO Title**: {metadata.get('youtube_title')}"
        )
    except Exception as e:
        return f"Error compiling master omnibus: {str(e)}"


@tool
def produce_bedtime_omnibus_tool(topic: str = "WhimsyWand Bedtime Stories 30-Minute Omnibus") -> str:
    """
    Produces the complete 30-minute Bedtime Story Omnibus compilation inside a SINGLE self-contained run folder.
    Generates all 5 chapters, all 3D Disney/Pixar illustrations, sweet child voiceovers, subtitles,
    and stitches the master 1080p 16:9 MP4 with continuous YouTube timestamps (0:00, 6:00, 12:00, 18:00, 24:00)
    ALL within ONE isolated run directory. Zero clutter, zero extra folders.
    """
    try:
        result = harness.run_omnibus_pipeline(topic=topic, num_chapters=5, frames_per_chapter=15, aspect_ratio="16:9")
        final_video = result.get("final_video")
        run_dir = result.get("run_dir")
        metadata = result.get("metadata", {})
        return (
            f"🎉 30-Minute Master Bedtime Story Omnibus Successfully Produced in ONE Single Folder!\n\n"
            f"- **Run Directory**: `{run_dir}`\n"
            f"- **Master Video File**: `{final_video}`\n"
            f"- **Total Duration**: {metadata.get('total_duration_sec', 0):.2f}s (~{metadata.get('total_duration_sec', 0)/60:.1f} minutes)\n"
            f"- **Chapters Included**:\n" + "\n".join(metadata.get('chapters', [])) + "\n\n"
            f"- **YouTube SEO Title**: {metadata.get('youtube_title')}"
        )
    except Exception as e:
        return f"Error producing bedtime omnibus: {str(e)}"


@tool
def generate_thumbnail_tool(run_id: str = "") -> str:
    """
    Synthesizes a bespoke 1280x720 high-CTR YouTube Thumbnail for an existing production run.
    Creates both clean cinematic 3D poster art and a branded title-stamped version.
    """
    try:
        from modules.thumbnail_engine import generate_video_thumbnail
        runs_dir = OUTPUT_DIR / "runs"
        if run_id and (runs_dir / run_id).exists():
            target_dir = runs_dir / run_id
        else:
            completed = sorted([d for d in runs_dir.iterdir() if d.is_dir() and (d / "final_video.mp4").exists()], reverse=True)
            if not completed:
                return "No completed video runs found to generate thumbnail for."
            target_dir = completed[0]

        meta_file = target_dir / "final_video_metadata.json"
        title = target_dir.name
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    title = json.load(f).get("youtube_title", title)
            except Exception:
                pass

        thumb_path = generate_video_thumbnail(target_dir, title=title)
        return (
            f"🎉 High-CTR YouTube Thumbnail Successfully Generated!\n\n"
            f"- **Clean 1280x720 Thumbnail**: `{thumb_path}`\n"
            f"- **Branded Version with Title**: `{target_dir / 'thumbnail_with_title.jpg'}`\n"
            f"- Ready for 1-click download in WhimsyWand Tales Studio!"
        )
    except Exception as e:
        return f"Error generating thumbnail: {str(e)}"
