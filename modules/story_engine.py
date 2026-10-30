import os
import sys
import json
import urllib.request
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import DEEPSEEK_API_KEY, MEMORY_DIR, VOICE_MAP

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """You are the Lead Creative Showrunner and YouTube Growth Strategist for "WhimsyWand Tales" (https://www.youtube.com/@WhimsyWandTales).
Tagline: "Tiny heroes. Magical worlds. Big-hearted endings."
Target Audience: Toddlers & Young Kids (Ages 3 to 7) and Families.

CORE CHANNEL MASCOTS & CHARACTERS:
1. Pip the Baby Dragon (main mascot) - tiny purple and orange baby dragon, glossy indigo wings, big violet eyes, learns to fly and control his warm spark breath.
2. Fern the Forest Fairy - flower petal dress, gossamer dragonfly wings with sparkle dust, emerald eyes, plants glowing flowers.
3. Barnaby Bear - honey-brown grizzly cub with tiny red adventurer backpack, big friendly green eyes.
4. Squeaky Squirrel - copper fur, fluffy white chest, knitted acorn cap, brave and energetic.
5. Luna the Little Cloud - fluffy white baby cloud with rosy cheeks, creates mini rainbows when giggling.
6. Benny Bunny - fluffy white baby bunny, long floppy pink ears, sky-blue scarf.

CRITICAL VIRAL STORYTELLING & BEDTIME PSYCHOLOGY RULES:
1. 4-PHASE WAVE & DESCENT STRUCTURE (MANDATORY FOR HIGH RETENTION):
   - Phase 1 (Frames 1-3) THE SENSORY-CURIOSITY HOOK: Start with an ambient cozy visual and a soft whispered question to spike retention in the first 15 seconds! (e.g. "Shh... if you listen very closely, the sleepy stars have a bedtime secret..."). Introduce the mascot, setting, and cozy mystery immediately.
   - Phase 2 (Frames 4-8) RELATABLE TODDLER TENSION & EMOTION: The character feels a real bedtime emotion (fear of dark shadows, a restless buzzing mind, or missing a soft blanket). Create deep vulnerability and sweet friend support.
   - Phase 3 (Frames 9-18) SOMATIC INTERACTION & WONDER: Include at least TWO interactive child participation cues!
     * Somatic Breath: "Can you help Pip? Blow a gentle, soft breath at the screen... Look! His warm spark glowed purple!"
     * Somatic Pointing: "Point your finger at the brightest little star... you showed Barnaby the way!"
     * Somatic Hug: "Give your cozy pillow a big, warm squeeze just like Benny Bunny."
     * Deep Breathing: "Let's take a slow, deep breath in together... 1... 2... 3... and let it all out slow."
   - Phase 4 (Frames 19-End) THE SLEEP SLIDE: Lower heart rates with heavy eyelids, warm blankets, soft yawns, starlight fading to lavender, and whispering sweet goodnights. NO LOUD OUTROS!
2. PACING & SCENE TIMING: Each frame has exactly ONE spoken sentence (5 to 10 words, ~2.5 to 3.5 seconds).
3. 1-TO-1 AUDIO/VISUAL MATCH: The visual prompt MUST depict the EXACT situational action described in that sentence!
4. VISUAL CONSISTENCY: In "character_bible", define a precise "visual_anchor" for each character. In every frame's "visual_prompt", ALWAYS reuse that exact visual anchor combined with situational action, camera angle, and 3D Disney Pixar render style.
5. STRICT CHILD VOICES ONLY: All characters and the narrator MUST use sweet, lively child voices ("child_male" or "child_female"). NEVER use adult voices.

Output MUST be valid raw JSON matching this schema:
{
  "episode_id": "ep_001",
  "title": "string",
  "target_age": "3-7",
  "aspect_ratio": "9:16",
  "moral_lesson": "string",
  "seo_tags": ["tag1", "tag2"],
  "character_bible": {
    "characters": [
      {
        "name": "Pip the Baby Dragon",
        "role": "main_character",
        "voice_type": "child_male",
        "visual_anchor": "Pip the tiny purple and orange baby dragon, oversized glossy indigo wings, big sparkling violet eyes, gentle friendly snout, tiny soft horns, 3D Disney Pixar animation style, warm golden rim lighting, adorable miniature proportions",
        "personality": "Curious, kind, adventurous"
      }
    ]
  },
  "frames": [
    {
      "frame_id": 1,
      "speaker": "Pip the Baby Dragon",
      "voice_type": "child_male",
      "dialogue": "Pip the baby dragon found a magical glowing acorn in the forest!",
      "visual_prompt": "Pip the tiny purple and orange baby dragon, oversized glossy indigo wings, big sparkling violet eyes, looking down in wonder at a shiny glowing acorn on mossy ground, 3D Disney Pixar animation, enchanted forest sunlight, 8k",
      "camera_motion": "zoom_in_slow",
      "sfx_cue": "magic_twinkle",
      "bgm_mood": "playful_cheerful"
    }
  ]
}
Do NOT include markdown formatting (no ```json code blocks). Output ONLY the raw JSON object."""

def load_my_channel_context() -> str:
    """Loads WhimsyWand Tales channel intelligence and published video history."""
    channel_file = MEMORY_DIR / "my_channel.json"
    if not channel_file.exists():
        return ""
    try:
        with open(channel_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        published = [v.get("title") for v in data.get("published_video_audit", [])]
        return (
            f"\nOUR CHANNEL: {data.get('channel_name')} ({data.get('handle')})\n"
            f"Tagline: {data.get('tagline')}\n"
            f"Core Concept: {data.get('description')}\n"
            f"Already Published Videos (DO NOT REPEAT THESE TOPICS):\n" + "\n".join(f"- {p}" for p in published) + "\n"
        )
    except Exception:
        return ""

def load_competitor_context() -> str:
    """Loads trending competitor viral hits from memory/channel_insights.json."""
    insights_file = MEMORY_DIR / "channel_insights.json"
    if not insights_file.exists():
        return ""
    try:
        with open(insights_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        top_vids = data.get("top_videos", [])[:4]
        lines = [f"- '{v.get('title')}' ({v.get('views', 0):,} views)" for v in top_vids]
        return f"\nCOMPETITOR VIRAL HITS (>1M views to model after):\n" + "\n".join(lines) + "\n"
    except Exception:
        return ""

def generate_story(
    prompt_or_topic: str = None,
    num_frames: int = None,
    aspect_ratio: str = "9:16"
) -> dict:
    """
    Autonomous Story Generator for WhimsyWand Tales.
    If prompt_or_topic is None or empty:
      - Reads our channel history (my_channel.json)
      - Inspects competitor viral formulas
      - Automatically creates a brand-new winning story concept!
    Auto-calculates frames if not specified:
      - 9:16 Shorts: 10 frames (~30 seconds)
      - 16:9 Long: 20 frames (~60 seconds)
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY is not configured in .env")

    # Auto-calculate frame count if not provided
    if num_frames is None:
        num_frames = 10 if aspect_ratio == "9:16" else 20

    channel_context = load_my_channel_context()
    competitor_context = load_competitor_context()

    if prompt_or_topic and prompt_or_topic.strip():
        user_goal = f"Topic / Direction: {prompt_or_topic.strip()}"
    else:
        user_goal = (
            "AUTONOMOUS VIRAL CREATION TASK:\n"
            "1. Analyze our channel 'WhimsyWand Tales' and our tiny heroes (Pip the Dragon, Fern the Fairy, Barnaby Bear, Luna the Cloud, Benny Bunny).\n"
            "2. Analyze competitor viral hits to identify high-view fairy tale conflicts (e.g. lost star, magic seeds, facing fears, helping friends).\n"
            "3. Create a BRAND NEW, captivating story for WhimsyWand Tales that has NOT been published yet.\n"
            "4. Formulate an irresistible curiosity-gap title formula that kids and parents will click!"
        )

    user_instructions = f"""{user_goal}

Format: {aspect_ratio} {'Vertical YouTube Short' if aspect_ratio == '9:16' else 'Widescreen Story Episode'}.
Exact Number of Frames: {num_frames}.
Estimated Duration: {num_frames * 3} seconds (~3.0 seconds per frame).
Target Audience: Toddlers & Young Kids (Ages 3-7).

{channel_context}
{competitor_context}

CRITICAL RULES:
- Generate EXACTLY {num_frames} frames in the "frames" list.
- Each frame's dialogue MUST be 1 short sentence (5 to 9 words, ~2.5 to 3.5 seconds).
- Every single frame must have a unique situational visual prompt matching the exact spoken action.
- STRICT SWEET CHILD VOICES ONLY ("child_male" or "child_female").
- Keep visuals in 3D Disney Pixar animation style with rich fairy-tale lighting."""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_instructions}
        ],
        "temperature": 0.8,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"}
    }

    req = urllib.request.Request(
        DEEPSEEK_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        },
        data=json.dumps(payload).encode("utf-8")
    )

    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))

    content = res_json["choices"][0]["message"]["content"].strip()

    # Extract JSON between braces
    start_brace = content.find('{')
    end_brace = content.rfind('}')
    raw_json = content[start_brace:end_brace + 1] if (start_brace != -1 and end_brace != -1 and end_brace > start_brace) else content

    try:
        parsed = json.loads(raw_json)
    except Exception:
        import json_repair
        parsed = json_repair.loads(content)

    if not isinstance(parsed, dict):
        import json_repair
        parsed = json_repair.loads(content)
        if not isinstance(parsed, dict):
            parsed = {"title": "WhimsyWand Adventure", "frames": []}
    
    # Standardize 'scenes' / 'frames' keys
    if "frames" in parsed and "scenes" not in parsed:
        parsed["scenes"] = parsed["frames"]
    elif "scenes" in parsed and "frames" not in parsed:
        parsed["frames"] = parsed["scenes"]

    return parsed

if __name__ == "__main__":
    print("Testing Autonomous WhimsyWand Story Engine...")
    story = generate_story(prompt_or_topic=None, num_frames=3, aspect_ratio="9:16")
    print(f"Autonomous Story Title: '{story.get('title')}'")
    print(f"Moral: '{story.get('moral_lesson')}'")
    for f in story.get("frames", []):
        print(f" - Frame {f.get('frame_id')}: \"{f.get('dialogue')}\" [{f.get('speaker')}]")
