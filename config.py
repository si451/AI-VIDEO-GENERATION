import os
from pathlib import Path
from dotenv import load_dotenv
import torch

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Paths
MODULES_DIR = BASE_DIR / "modules"
MEMORY_DIR = BASE_DIR / "memory"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
SCENES_DIR = OUTPUT_DIR / "scenes"
AUDIO_DIR = OUTPUT_DIR / "audio"
FINAL_DIR = OUTPUT_DIR / "final"

# Device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Video Dimensions & Aspect Ratios
# 9:16 Vertical for YouTube Shorts / Reels / TikTok
SHORTS_WIDTH = 720
SHORTS_HEIGHT = 1280
SHORTS_IMG_WIDTH = 512
SHORTS_IMG_HEIGHT = 896

# 16:9 Widescreen for Standard YouTube Videos
LONG_WIDTH = 1280
LONG_HEIGHT = 720
LONG_IMG_WIDTH = 768
LONG_IMG_HEIGHT = 512

VIDEO_FPS = 30

# STRICT CHILD VOICES ONLY (No Adult Voices)
# en-US-AnaNeural: Sweet, expressive, cute young child
# en-US-ChristopherNeural: Enthusiastic, bright, adventurous young boy
VOICE_MAP = {
    "narrator": "en-US-AnaNeural",         # Sweet child narrator
    "child_female": "en-US-AnaNeural",       # Cute little girl child
    "child_male": "en-US-ChristopherNeural", # Playful little boy child
    "animal_cute": "en-US-AnaNeural",        # Cute small baby animal
    "default": "en-US-AnaNeural"             # Default fallback child
}
