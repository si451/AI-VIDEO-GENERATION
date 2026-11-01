import os
import sys
import json
import random
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from modules.visual_engine import generate_frame_image, free_gpu

def _derive_thumbnail_prompt_and_badge(run_dir: Path, title: str = None):
    """
    Intelligently extracts the story theme, characters, and settings
    from story_package.json or final_video_metadata.json to ensure
    every single video gets a completely bespoke, high-CTR YouTube thumbnail.
    """
    clean_title = title or ""
    story_pkg_path = run_dir / "story_package.json"
    meta_path = run_dir / "final_video_metadata.json"
    
    mascots = "Pip the tiny baby dragon, Barnaby the fluffy bear cub, and Benny Bunny"
    duration_min = 30
    
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                if not clean_title:
                    clean_title = meta.get("youtube_title", "")
                dur_sec = meta.get("total_duration_sec", 1800)
                duration_min = max(5, round(dur_sec / 60))
        except Exception:
            pass

    if story_pkg_path.exists():
        try:
            with open(story_pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                if not clean_title:
                    clean_title = pkg.get("title", "")
        except Exception:
            pass

    # Clean up title for badge
    short_title = clean_title.split("|")[0].split("—")[0].split("–")[0].strip()
    short_title = re.sub(r"[\U00010000-\U0010ffff]", "", short_title)  # Remove emojis
    short_title = re.sub(r"\d+-Min.*", "", short_title, flags=re.IGNORECASE).strip()
    
    lower_title = clean_title.lower()
    
    # Context-aware thumbnail visuals
    if "whispering door" in lower_title or "door" in lower_title:
        prompt = (
            "Pip the tiny cute baby dragon, Barnaby the fuzzy little bear cub, and Benny the fluffy baby bunny standing together amazed "
            "before an ancient magical glowing wooden door carved with glowing starlight runes inside an enchanted moonlit forest, "
            "warm golden light beaming from keyhole, glowing fireflies, giant luminous crescent moon, floating sparkles, "
            "cozy dreamland bedtime fairy tale, 3D Disney Pixar animation style, volumetric studio lighting, rich vibrant colors, clean render, 8k"
        )
        badge_text = "THE WHISPERING DOOR"
    elif "train" in lower_title or "starlight" in lower_title:
        prompt = (
            "Pip the adorable baby dragon and Barnaby Bear happily waving from the window of a magical glowing steam train "
            "flying across a dreamy starry night sky towards a giant glowing golden crescent moon, floating fluffy clouds, "
            "starlight sparkles, cozy dreamland atmosphere, 3D Disney Pixar animation style, volumetric studio lighting, rich colors, clean render, 8k"
        )
        badge_text = "STARLIGHT SLEEPY TRAIN"
    elif "cloud" in lower_title:
        prompt = (
            "A cute little pastel lavender smiling baby cloud named Pippa, glowing softly in a twilight sky above a peaceful flower meadow, "
            "tiny baby dragon and fairy waving from below, giant glowing crescent moon, gentle starlight, "
            "cozy bedtime atmosphere, 3D Disney Pixar animation style, volumetric studio lighting, clean render, 8k"
        )
        badge_text = "THE SLEEPY LITTLE CLOUD"
    elif "fairy" in lower_title or "flower" in lower_title:
        prompt = (
            "Fern the delicate forest fairy with gossamer glowing wings sprinkling golden slumber dust over Barnaby Bear and Pip the baby dragon, "
            "nestled in a giant glowing blossom under a giant crescent moon, magical glowing enchanted forest, "
            "cozy dreamland atmosphere, 3D Disney Pixar animation style, volumetric studio lighting, clean render, 8k"
        )
        badge_text = "FERN'S FAIRY LULLABY"
    elif "barnaby" in lower_title or "bear" in lower_title:
        prompt = (
            "Barnaby Bear the adorable little bear cub holding a warm glowing lantern, walking along a gentle moonlit starlight path with Pip the baby dragon, "
            "giant glowing crescent moon, sleepy woodland friends watching, floating golden fireflies, cozy dreamland bedtime, "
            "3D Disney Pixar animation style, volumetric studio lighting, rich vibrant colors, clean render, 8k"
        )
        badge_text = "BARNABY'S BEDTIME LULLABY"
    else:
        prompt = (
            f"{mascots}, snuggled peacefully together under a giant glowing crescent moon in an enchanted bedtime fairy tale forest, "
            "floating golden starlight sparkles, glowing fireflies, cozy dreamland atmosphere, 3D Disney Pixar animation style, "
            "volumetric studio moonlight, vibrant colors, clean render, 8k"
        )
        badge_text = short_title[:24].upper() if short_title else "BEDTIME STORIES"

    sub_text = f"5 MAGICAL TALES • {duration_min}-MIN SOOTHING SLEEP COMPILATION"
    return prompt, badge_text, sub_text

def generate_video_thumbnail(
    run_dir: Path,
    title: str = None,
    prompt: str = None,
    mascots_text: str = None,
    seed: int = None,
    badge_text: str = None,
    sub_text: str = None
) -> Path:
    """
    Synthesizes a bespoke, high-CTR 1280x720 YouTube Thumbnail directly inside run_dir.
    Features:
    - Truly unique 3D Disney/Pixar visuals matching the actual episode.
    - Randomized seed on each run to prevent duplicate thumbnail penalties.
    - Creates 'thumbnail.jpg' (Clean Art) and 'thumbnail_with_title.jpg' (Branded Poster).
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Derive bespoke prompt and badge text if not explicitly supplied
    auto_prompt, auto_badge, auto_sub = _derive_thumbnail_prompt_and_badge(run_dir, title=title)
    final_prompt = prompt or auto_prompt
    final_badge = badge_text or auto_badge
    final_sub = sub_text or auto_sub

    # 2. Randomize seed if None to guarantee a fresh, non-duplicate generation
    if seed is None:
        seed = random.randint(10000, 999999)

    safe_badge = final_badge.encode('ascii', 'ignore').decode('ascii')
    safe_sub = final_sub.encode('ascii', 'ignore').decode('ascii')

    print(f"\n[Thumbnail Engine] Generating bespoke 1280x720 High-CTR Thumbnail...")
    print(f" -> Badge: {safe_badge}")
    print(f" -> Seed: {seed}")
    print(f" -> Prompt: {final_prompt[:80]}...")

    raw_path = generate_frame_image(999, final_prompt, aspect_ratio="16:9", seed=seed, output_dir=run_dir)
    free_gpu()

    # Load and resize to exact YouTube 1280x720 HD dimensions
    img = Image.open(raw_path)
    img_hd = img.resize((1280, 720), Image.Resampling.LANCZOS)
    
    # Clean thumbnail
    clean_thumb_path = run_dir / "thumbnail.jpg"
    img_hd.save(clean_thumb_path, quality=98)
    
    # Remove temporary raw frame if named frame_999.jpg or scene_999.jpg
    for temp_name in ["frame_999.jpg", "scene_999.jpg"]:
        temp_frame = run_dir / temp_name
        if temp_frame.exists() and temp_frame != clean_thumb_path:
            try:
                temp_frame.unlink()
            except Exception:
                pass

    # Create branded version with high-contrast text overlay
    try:
        rgba_img = img_hd.convert("RGBA")
        overlay = Image.new("RGBA", rgba_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Soft dark gradient at bottom for readability
        for y in range(460, 720):
            alpha = int(190 * ((y - 460) / 260)**1.4)
            draw.line([(0, y), (1280, y)], fill=(10, 15, 30, alpha))

        font_title = None
        font_sub = None
        for fpath in ["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]:
            if Path(fpath).exists():
                try:
                    font_title = ImageFont.truetype(fpath, 60)
                    font_sub = ImageFont.truetype(fpath, 32)
                    break
                except Exception:
                    pass

        if font_title is None:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Dynamic pillowed golden badge sized to text
        try:
            badge_width = int(draw.textlength(final_badge, font=font_title))
        except Exception:
            badge_width = 650

        box_x, box_y = 50, 520
        box_w = max(680, min(1150, badge_width + 60))
        box_h = 78

        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=18,
            fill=(255, 185, 30, 240),
            outline=(255, 255, 255, 230),
            width=3
        )
        draw.text((box_x + 25, box_y + 8), final_badge, fill=(40, 20, 5, 255), font=font_title)

        # Subtitle with drop shadow
        draw.text((52, 622), final_sub, fill=(0, 0, 0, 220), font=font_sub)
        draw.text((50, 620), final_sub, fill=(255, 250, 220, 255), font=font_sub)

        branded_img = Image.alpha_composite(rgba_img, overlay).convert("RGB")
        branded_path = run_dir / "thumbnail_with_title.jpg"
        branded_img.save(branded_path, quality=98)
        print(f"[Thumbnail Engine] Branded Thumbnail saved: {branded_path.name}")
    except Exception as e:
        print(f"[Thumbnail Engine] Notice: Branded text overlay skipped: {e}")

    print(f"[Thumbnail Engine] Clean Thumbnail saved: {clean_thumb_path.name}")
    return clean_thumb_path

if __name__ == "__main__":
    test_run = BASE_DIR / "output" / "evaluations"
    generate_video_thumbnail(test_run, title="Pip's Bedtime Story")

