import os
import sys
import gc
import time
import torch
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    SCENES_DIR,
    HF_TOKEN,
    SHORTS_IMG_WIDTH,
    SHORTS_IMG_HEIGHT,
    LONG_IMG_WIDTH,
    LONG_IMG_HEIGHT
)

# Enable high-speed downloads if needed
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

MODEL_ID = "Yntec/DisneyPixarCartoon768"

QUALITY_BOOSTER = (
    "3D Disney Pixar animation style, cute character design, volumetric studio lighting, vibrant colors, clean render, 8k"
)

NEGATIVE_PROMPT = (
    "ugly, deformed, bad anatomy, bad limbs, blurry, low quality, photorealistic, realistic, noisy, cropped"
)

_global_pipe = None

def get_pipeline():
    """Loads and caches the DisneyPixarCartoon768 pipeline in VRAM (fp16) with ultra-safe memory management."""
    global _global_pipe
    if _global_pipe is not None:
        return _global_pipe

    print(f"\n[Visual Engine] Loading local model '{MODEL_ID}' onto {torch.cuda.get_device_name(0)}...")
    start_load = time.time()
    
    from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
        safety_checker=None,
        token=HF_TOKEN
    )
    # Euler scheduler is robust, fast, and eliminates all off-by-one boundary index bugs
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.enable_attention_slicing()  # Keeps VRAM well within 4GB limit (~2.1 GB)
    pipe.enable_vae_slicing()
    pipe.to("cuda")

    print(f"[Visual Engine] Model loaded in {time.time() - start_load:.2f}s! (VRAM: {torch.cuda.memory_allocated() / 1024**2:.2f} MB)")
    _global_pipe = pipe
    return _global_pipe

def free_gpu():
    """Completely releases model from GPU memory to free all VRAM for downstream modules."""
    global _global_pipe
    if _global_pipe is not None:
        del _global_pipe
        _global_pipe = None
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        try:
            torch.cuda.ipc_collect()
        except Exception:
            pass
    print(f"[Visual Engine] GPU Memory freed! Current VRAM: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")

def generate_frame_image(
    frame_id: int,
    prompt: str,
    aspect_ratio: str = "9:16",
    seed: int = 42,
    output_dir: Path = None
) -> Path:
    """
    Renders a high quality 3D Disney Pixar illustration.
    - 9:16 Vertical Shorts: 512x896
    - 16:9 Widescreen Long: 768x512
    Saves as frame_01.jpg, frame_02.jpg, etc.
    """
    if output_dir is None:
        output_dir = SCENES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as frame_01.jpg (and also create scene_X.jpg alias if needed)
    output_path = output_dir / f"frame_{frame_id:02d}.jpg"

    if aspect_ratio == "9:16":
        width, height = SHORTS_IMG_WIDTH, SHORTS_IMG_HEIGHT  # 512x896
    else:
        width, height = LONG_IMG_WIDTH, LONG_IMG_HEIGHT      # 768x512

    pipe = get_pipeline()
    # CRITICAL FIX: CPU generator avoids float32/fp16 mismatch on Windows CUDA
    generator = torch.Generator(device="cpu").manual_seed(seed)

    # Enhance prompt with Pixar aesthetic boosters
    enhanced_prompt = f"{prompt}, {QUALITY_BOOSTER}"

    print(f" -> Rendering Frame {frame_id:02d} [{width}x{height} {aspect_ratio}] (seed={seed})...")
    start_gen = time.time()
    
    image = pipe(
        prompt=enhanced_prompt,
        negative_prompt=NEGATIVE_PROMPT,
        width=width,
        height=height,
        num_inference_steps=20,
        guidance_scale=7.5,
        generator=generator
    ).images[0]

    gen_duration = time.time() - start_gen
    image.save(output_path, quality=98)
    
    # Also save scene_X.jpg for backward-compatibility with older inspection tools
    alias_path = output_dir / f"scene_{frame_id}.jpg"
    if alias_path != output_path:
        image.save(alias_path, quality=98)

    print(f" -> Frame {frame_id:02d} rendered in {gen_duration:.2f}s! Saved to: {output_path.name}")
    return output_path

# Alias for backward compatibility
generate_scene_image = generate_frame_image

def generate_all_frame_images(
    frames: list,
    aspect_ratio: str = "9:16",
    master_seed: int = 42,
    auto_free_vram: bool = True,
    output_dir: Path = None
) -> list:
    """
    Renders all frames in a story (~3 seconds each), then wipes VRAM.
    """
    if output_dir is None:
        output_dir = SCENES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered_paths = []
    print(f"\n[Visual Engine] Generating {len(frames)} high quality frames ({aspect_ratio}) with Yntec/DisneyPixarCartoon768...")

    try:
        for idx, frame in enumerate(frames):
            fid = frame.get("frame_id", frame.get("scene_id", idx + 1))
            prompt = frame.get("visual_prompt", "")
            # Increment seed deterministically per frame to get situational diversity while keeping characters consistent
            frame_seed = master_seed + (fid * 17)
            path = generate_frame_image(fid, prompt, aspect_ratio=aspect_ratio, seed=frame_seed, output_dir=output_dir)
            rendered_paths.append(path)
    finally:
        if auto_free_vram:
            free_gpu()

    return rendered_paths

# Alias for backward compatibility
generate_all_scene_images = generate_all_frame_images

if __name__ == "__main__":
    print("Testing Visual Engine (9:16 vertical test)...")
    test_dir = BASE_DIR / "output" / "evaluations"
    test_prompt = "Barnaby Bear smiling happily in a sunny forest clearing, holding a glowing golden acorn"
    out = generate_frame_image(1, test_prompt, aspect_ratio="9:16", seed=42, output_dir=test_dir)
    print(f"SUCCESS! Rendered vertical frame at: {out}")
    free_gpu()
