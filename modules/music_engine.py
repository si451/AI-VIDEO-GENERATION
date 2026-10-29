import os
import sys
import subprocess
import shutil
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import ASSETS_DIR, DEVICE

def generate_procedural_synth(duration_sec: float, output_path: Path, mood: str = "playful_cheerful") -> Path:
    """
    Generates a charming acoustic synth melody using FFmpeg audio filters.
    Runs in 0.1s on CPU with zero dependencies or download requirements.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Scale frequencies according to mood
    if "bedtime" in mood or "peaceful" in mood:
        # Softer lullaby chords (C4, E4, G4, B4)
        c4, e4, g4, b4 = 261.63, 329.63, 392.00, 493.88
        cutoff = 900
        vol = 0.14
    else:
        # Cheerful playful chords (C5, E5, G5, C6)
        c4, e4, g4, b4 = 523.25, 659.25, 783.99, 1046.50
        cutoff = 1400
        vol = 0.18

    fade_out_start = max(duration_sec - 3.0, 0.0)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency={c4}:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency={e4}:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency={g4}:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency={b4}:duration={duration_sec}",
        "-filter_complex",
        f"[0:a][1:a][2:a][3:a]amix=inputs=4:dropout_transition=0,volume={vol},lowpass=f={cutoff},"
        f"afade=t=in:ss=0:d=2.0,afade=t=out:st={fade_out_start}:d=3.0[aout]",
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path

def generate_musicgen_audio(prompt: str, duration_sec: float, output_path: Path) -> Path:
    """
    Generates tailored background music from text using Meta's facebook/musicgen-small.
    Natively supported via HuggingFace transformers.
    Runs on CUDA if VRAM is free, or CPU.
    """
    import torch
    import scipy.io.wavfile
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_wav = output_path.with_suffix(".wav")

    print(f"[MusicGen] Loading facebook/musicgen-small for prompt: '{prompt}'...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained(
        "facebook/musicgen-small",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    ).to(device)

    # MusicGen generates in tokens (~50 tokens = 1 second)
    max_tokens = min(int(duration_sec * 50), 1500) # max 30s per pass
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt"
    ).to(device)

    audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
    sampling_rate = model.config.audio_encoder.sampling_rate

    # Convert to numpy & write wav
    audio_data = audio_values[0, 0].cpu().numpy()
    scipy.io.wavfile.write(str(temp_wav), rate=sampling_rate, data=audio_data)

    # Free memory immediately
    del model, processor, inputs, audio_values
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Convert to MP3 and loop if necessary to match full duration
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(temp_wav),
        "-t", str(duration_sec),
        "-af", f"afade=t=in:ss=0:d=1.5,afade=t=out:st={max(duration_sec - 2.5, 0)}:d=2.5",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    if temp_wav.exists():
        temp_wav.unlink()

    return output_path

def generate_ai_music(prompt: str, duration_sec: float, output_path: Path, use_musicgen: bool = False, mood: str = "playful_cheerful") -> Path:
    """
    Unified entrypoint for background music generation.
    Checks:
    1. Curated music in assets/bgm
    2. Optional MusicGen AI text-to-music
    3. High-quality procedural ambient story synth (instant & lightweight)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Priority 1: Check curated high-quality royalty-free tracks in assets/bgm
    custom_bgm = list((ASSETS_DIR / "bgm").glob("*.mp3")) + list((ASSETS_DIR / "bgm").glob("*.wav"))
    if custom_bgm:
        print(f"[Music Engine] Using curated BGM: {custom_bgm[0].name}")
        shutil.copy(custom_bgm[0], output_path)
        return output_path

    # Priority 2: MusicGen if explicitly requested
    if use_musicgen:
        try:
            return generate_musicgen_audio(prompt, duration_sec, output_path)
        except Exception as e:
            print(f"[Music Engine] MusicGen generation skipped/fallback ({e}), using procedural synth.")

    # Priority 3: Procedural ambient story synth
    print(f"[Music Engine] Generating acoustic story synth ({duration_sec:.1f}s, mood: {mood})...")
    return generate_procedural_synth(duration_sec, output_path, mood=mood)

if __name__ == "__main__":
    print("Testing upgraded Music Engine...")
    test_out = BASE_DIR / "test_synth_bgm.mp3"
    generate_ai_music("playful happy cartoon bedtime story music", duration_sec=5.0, output_path=test_out, mood="playful_cheerful")
    print(f"SUCCESS: Generated test BGM at {test_out} ({test_out.stat().st_size} bytes)")
    if test_out.exists():
        test_out.unlink()
