import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from modules.visual_engine import generate_frame_image, free_gpu

def generate_video_thumbnail(
    run_dir: Path,
    title: str = "Bedtime Stories for Kids",
    mascots_text: str = "Pip the tiny baby dragon and Benny the fluffy baby bunny",
    seed: int = 777
) -> Path:
    """
    Synthesizes a bespoke, high-CTR 1280x720 YouTube Thumbnail directly inside run_dir.
    Creates:
    - thumbnail.jpg: Clean cinematic 3D Disney Pixar poster.
    - thumbnail_with_title.jpg: Stamped with high-CTR bedtime badge and subtitle.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    
    prompt = (
        f"{mascots_text}, snuggled peacefully together under a giant glowing crescent moon in an enchanted bedtime fairy tale forest, "
        "floating golden starlight sparkles, glowing fireflies, cozy dreamland atmosphere, 3D Disney Pixar animation style, "
        "volumetric studio moonlight, vibrant colors, clean render, 8k"
    )

    print(f"\n[Thumbnail Engine] Generating 1280x720 High-CTR Thumbnail for '{title}'...")
    raw_path = generate_frame_image(999, prompt, aspect_ratio="16:9", seed=seed, output_dir=run_dir)
    free_gpu()

    # Load and resize to exact YouTube 1280x720 HD dimensions
    img = Image.open(raw_path)
    img_hd = img.resize((1280, 720), Image.Resampling.LANCZOS)
    
    # Clean thumbnail
    clean_thumb_path = run_dir / "thumbnail.jpg"
    img_hd.save(clean_thumb_path, quality=98)
    
    # Remove temporary raw frame if named frame_999.jpg
    temp_frame = run_dir / "frame_999.jpg"
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
        for y in range(480, 720):
            alpha = int(180 * ((y - 480) / 240)**1.5)
            draw.line([(0, y), (1280, y)], fill=(10, 15, 30, alpha))

        font_title = None
        font_sub = None
        for fpath in ["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]:
            if Path(fpath).exists():
                try:
                    font_title = ImageFont.truetype(fpath, 64)
                    font_sub = ImageFont.truetype(fpath, 34)
                    break
                except Exception:
                    pass

        if font_title is None:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Pillowed golden badge
        badge_text = "🌙 BEDTIME STORIES"
        sub_text = "✨ 5 MAGICAL TALES • SOOTHING SLEEP COMPILATION"

        box_x, box_y, box_w, box_h = 50, 520, 680, 80
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=18,
            fill=(255, 185, 30, 240),
            outline=(255, 255, 255, 220),
            width=3
        )
        draw.text((box_x + 30, box_y + 10), badge_text, fill=(40, 20, 5, 255), font=font_title)

        # Subtitle with drop shadow
        draw.text((52, 622), sub_text, fill=(0, 0, 0, 220), font=font_sub)
        draw.text((50, 620), sub_text, fill=(255, 250, 220, 255), font=font_sub)

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

