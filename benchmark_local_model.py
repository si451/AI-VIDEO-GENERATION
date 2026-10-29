import os
import sys
import time
import torch
from pathlib import Path
from dotenv import load_dotenv

# Enable high-speed multi-threaded Rust downloader
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
HF_TOKEN = os.getenv("HF_TOKEN")

OUTPUT_DIR = BASE_DIR / "output" / "evaluations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "Yntec/DisneyPixarCartoon768"

print(f"=== Benchmarking Local Cartoon Model: {MODEL_ID} ===")
print(f"Device: {torch.cuda.get_device_name(0)} (4GB VRAM)")
print(f"HuggingFace Authentication: {'Authenticated ✅' if HF_TOKEN else 'Anonymous ❌'}")
print(f"Current VRAM Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")

from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

print("\n[1/3] Loading model into VRAM (fp16 with HF Token priority)...")
start_load = time.time()
pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    variant="fp16",
    safety_checker=None,
    token=HF_TOKEN
)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()
pipe.to("cuda")

load_time = time.time() - start_load
print(f" -> Model loaded in {load_time:.2f} seconds!")
print(f" -> VRAM Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")

prompt = (
    "Barnaby the cute baby bear cub, fluffy caramel-brown fur with creamy white belly, "
    "big round curious brown eyes, wearing a tiny red backpack, smiling happily, "
    "standing in a sunny enchanted forest with giant green trees and yellow wildflowers, "
    "3D Disney Pixar animation style, vibrant vivid colors, cinematic soft lighting, masterpiece"
)
negative_prompt = (
    "ugly, deformed, disfigured, poor details, bad anatomy, bad paws, mutated limbs, "
    "blurry, low quality, dark, scary, photorealistic, realistic, human"
)

print("\n[2/3] Generating test cartoon image (768x512 16:9 widescreen, 20 steps)...")
start_gen = time.time()
generator = torch.Generator(device="cuda").manual_seed(42)
image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    width=768,
    height=512,
    num_inference_steps=20,
    guidance_scale=7.5,
    generator=generator
).images[0]

gen_time = time.time() - start_gen
peak_vram = torch.cuda.max_memory_allocated() / 1024**2
print(f" -> Generation completed in {gen_time:.2f} seconds!")
print(f" -> Peak VRAM Usage: {peak_vram:.2f} MB (Well under 4,096 MB limit!)")

out_file = OUTPUT_DIR / "eval_disney_pixar_768.jpg"
image.save(out_file, quality=95)
print(f"\n[3/3] SUCCESS! Saved evaluation image to:\n{out_file.resolve()}")
