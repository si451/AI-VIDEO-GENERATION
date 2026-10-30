"""
WhimsyWand Tales - Production Runner for Today's 30-Minute Bedtime Story Omnibus
Applies the 4-Phase Wave & Descent framework from skills/viral-kids-bedtime-storyteller/SKILL.md:
1. Phase 1: 15-second Sensory-Curiosity Hooks (soft ambient questions at second 0).
2. Phase 2: Relatable Toddler Emotions (restless thoughts, fear of dark, feeling small, need for comfort).
3. Phase 3: Interactive Somatic Cues (pillow hugs, blowing gentle breaths, pointing, 3-second deep breaths).
4. Phase 4: The Sleep Slide (heavy eyelids, yawns, warm blankets, soothing lullaby cadence).

Strict Rules Enforced:
- Single Self-Contained Folder in output/runs/ (zero duplicate runs).
- Strict Sweet Child Voices Only (en-US-AnaNeural & en-US-ChristopherNeural).
- Local 3D Disney/Pixar Illustrations rendered on RTX 2050 (zero API fees).
- High-CTR 1280x720 HD Thumbnail generation with branded & clean art options.
"""

import sys
import json
import logging
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import harness
from modules.progress_tracker import tracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("produce_today_30min")

TODAY_CHAPTER_CONCEPTS = [
    {
        "title": "Barnaby Bear & The Moon's Lost Lullaby",
        "theme": (
            "Hook: Shh... listen closely. Tonight the Whispering Woods went completely silent because the moon forgot its bedtime lullaby. "
            "Barnaby Bear feels a flutter of worry in his tummy because the little forest babies cannot sleep. "
            "Interactive Somatic Cues: Give your pillow a big gentle hug with Barnaby, and hum a soft 'mmm' melody to help. "
            "Sleep Slide: The moon begins to glow silver, and Barnaby snuggles into sweet honey moss, yawning into deep peaceful sleep."
        )
    },
    {
        "title": "Pip the Baby Dragon & The Sleepy Starlight Spark",
        "theme": (
            "Hook: Have you ever wondered what little baby dragons dream of when the stars come out? "
            "Pip the tiny dragon feels small and frustrated because his warm spark breath won't light the bedtime lantern. "
            "Interactive Somatic Cues: Blow a gentle, soft breath at the screen to help Pip's spark... and take a slow breath in together. "
            "Sleep Slide: A warm violet glow lights the lantern, and Pip curls his indigo wings into a cozy bedtime nest."
        )
    },
    {
        "title": "Fern the Fairy & The Whispering Starlight Flower",
        "theme": (
            "Hook: High on Moonberry Hill, one tiny shy bluebell was waiting for a gentle touch before closing its petals. "
            "Fern feels shy because her wings are small, but learns that the gentlest fairy dust creates the sweetest dreams. "
            "Interactive Somatic Cues: Point your finger at the glowing bluebell star on screen to help Fern find it! "
            "Sleep Slide: Starlight dust floats down like soft warm snow, tucking every flower into quiet slumber."
        )
    },
    {
        "title": "Benny Bunny & The Soft Cloud Blanket",
        "theme": (
            "Hook: As twilight turns into deep indigo, Benny Bunny's paws were chilly and he couldn't find his bedtime blanket. "
            "Benny feels nervous about sleeping alone in the wide meadow until Luna the Cloud drifts down to keep him company. "
            "Interactive Somatic Cues: Pull your blanket up over your shoulders with Benny Bunny... doesn't that feel warm and safe? "
            "Sleep Slide: A soft pastel cloud blanket settles over Benny's floppy ears as he lets out a quiet, sleepy bunny yawn."
        )
    },
    {
        "title": "The Grand Sleepy Symphony of Whispering Woods",
        "theme": (
            "Hook: Tonight, under the ancient glowing willow tree, all our tiny heroes come together for the grand bedtime rest. "
            "Emotional Arc: Pure warmth, unconditional friendship, safety, and deep gratitude for a wonderful day. "
            "Interactive Somatic Cues: Take a big, slow, deep breath in with all our friends... 1... 2... 3... and let it out slow. "
            "Sleep Slide: Heavy eyelids, glowing starlight lullaby, and the peaceful fade into uninterrupted restorative dreams."
        )
    }
]

def produce_todays_30min_omnibus(target_minutes: float = 30.0, dry_run_visuals: bool = False):
    """
    Executes the full master 30-minute Bedtime Story Omnibus pipeline.
    """
    print("\n" + "="*80)
    print("   WHIMSYWAND TALES - OFFICIAL 30-MINUTE BEDTIME STORY OMNIBUS PRODUCTION")
    print(f"   Target Runtime: {target_minutes:.1f} Minutes (1,800 Seconds)")
    print("   Architecture: 5 Emotional Bedtime Chapters with 15s Hooks & Somatic Interactivity")
    print("   Voice Model: Strict Sweet Child Voices Only (en-US-AnaNeural & en-US-ChristopherNeural)")
    print("   Visual Engine: Disney/Pixar 3D Diffusion on NVIDIA RTX 2050")
    print("="*80 + "\n")

    # Format chapter topics as comma-separated string for harness
    chapter_topics_list = [c["title"] for c in TODAY_CHAPTER_CONCEPTS]
    chapter_topics_str = ", ".join(chapter_topics_list)

    result = harness.run_omnibus_pipeline(
        topic="WhimsyWand Bedtime Stories 30-Minute Omnibus",
        chapter_topics=chapter_topics_str,
        num_chapters=5,
        frames_per_chapter=25,
        target_duration_minutes=target_minutes,
        aspect_ratio="16:9",
        use_local_images=not dry_run_visuals
    )

    print("\n" + "="*80)
    print("   PRODUCTION SUCCESSFUL!")
    print(f"   Master Run Directory: {result.get('run_dir')}")
    print(f"   Master Video Path: {result.get('final_video')}")
    print(f"   Actual Runtime: {result.get('duration'):.1f} seconds (~{result.get('duration')/60:.1f} minutes)")
    print("="*80 + "\n")
    return result

if __name__ == "__main__":
    # Check if user specified dry run or minutes
    target_m = 30.0
    if len(sys.argv) > 1:
        try:
            target_m = float(sys.argv[1])
        except ValueError:
            pass

    dry_run = "--dry-run" in sys.argv
    produce_todays_30min_omnibus(target_minutes=target_m, dry_run_visuals=dry_run)
