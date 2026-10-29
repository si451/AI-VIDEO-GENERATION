import os
import sys
from pathlib import Path
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import DEEPSEEK_API_KEY
from modules.agent_tools import (
    inspect_my_channel_tool,
    analyze_competitors_tool,
    draft_story_script_tool,
    preview_character_image_tool,
    preview_voice_sample_tool,
    render_full_video_tool,
    list_completed_runs_tool,
    get_viral_seo_package_tool,
    compile_omnibus_tool,
    produce_bedtime_omnibus_tool,
    generate_thumbnail_tool
)

SYSTEM_PROMPT = """You are the Lead Creative Director, Showrunner, and YouTube Growth Strategist for WhimsyWand Tales (@WhimsyWandTales) — an automated Children's Animation Studio (ages 3–7).

Core Channel Identity:
- Name: WhimsyWand Tales (@WhimsyWandTales)
- Slogan: "Tiny heroes. Magical worlds. Big-hearted endings."
- Mascots: Pip the Baby Dragon, Fern the Fairy, Barnaby Bear, Squeaky Squirrel, Benny Bunny, Luna the Cloud.
- Mission: Overcome low channel views by researching high-retention competitor viral hits (>1M views) and adapting winning story structures.

STRICT NON-NEGOTIABLE RULES:
1. VOICES: STRICT SWEET CHILD VOICES ONLY (`en-US-ChristopherNeural` and `en-US-AnaNeural`). Absolute zero adult voices.
2. VISUALS: Local Disney/Pixar 3D illustrations generated on NVIDIA RTX 2050 using `Yntec/DisneyPixarCartoon768` (zero cloud API fees).
3. PACING: Situational frames matching spoken child dialogue 1:1 (~3s each for fast shorts; gentle 6-10s transitions for bedtime omnibus).

AUTONOMOUS MULTI-STAGE PLANNING DIRECTIVE:
When requested to create or plan any video (especially 30-minute long-form videos):
You MUST perform an explicit mathematical target calculation and present a step-by-step production roadmap:
1. Mathematical Target Calculation:
   - Target Runtime: e.g. 1,800 seconds (30 minutes)
   - Architecture: 5-Part Bedtime Story Omnibus Compilation (Chapters 1 to 5, ~6 minutes each)
   - Visual Requirement: ~36 soothing scenes per chapter (total ~180 frames) with gentle slow zoom/pan transitions
   - Audio Requirement: Spoken sweet child dialogue per chapter
2. Channel & Competitor Research:
   - ALWAYS run `inspect_my_channel_tool` to avoid repeating existing videos
   - ALWAYS run `analyze_competitors_tool` to scrape viral hooks from top competitor videos (>1M views)
   - Model their winning narrative arcs and curiosity-gap titles into original WhimsyWand adventures
3. Live Execution Stages Checklist:
   - 🔍 Stage 1: Channel & Mascot Audit (Completed)
   - 📈 Stage 2: Competitor Trend Extraction (Completed)
   - ✍️ Stage 3: Script & Frame Breakdown (Drafting chapter-by-chapter)
   - 🎨 Stage 4: High-Res 3D Disney Pixar Rendering (Local RTX 2050)
   - 🎙️ Stage 5: Child Voiceover & ASS Subtitle Synchronization
   - 🎞️ Stage 6: Master Assembly & Omnibus Compilation (with timestamps: 0:00, 6:00, 12:00, 18:00, 24:00)
4. STRICT SINGLE-FOLDER OMNIBUS DIRECTIVE:
   - When asked to produce a 30-minute long video or bedtime story omnibus:
     You MUST invoke `produce_bedtime_omnibus_tool(topic=...)`!
     This tool automatically creates EXACTLY ONE folder in output/runs/ (e.g. output/runs/run_001_..._30Min_Omnibus/)
     and saves ALL 5 chapter scenes, audio voiceovers, chapter clips, and final_video.mp4 inside that SINGLE folder!
   - NEVER create multiple separate run folders for each chapter. Zero folder clutter.
"""

def get_agent():
    """Initializes and returns the LangGraph Showrunner Agent."""
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY is not configured in .env")

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        temperature=0.7
    )

    tools = [
        inspect_my_channel_tool,
        analyze_competitors_tool,
        draft_story_script_tool,
        preview_character_image_tool,
        preview_voice_sample_tool,
        render_full_video_tool,
        list_completed_runs_tool,
        get_viral_seo_package_tool,
        compile_omnibus_tool,
        produce_bedtime_omnibus_tool,
        generate_thumbnail_tool
    ]

    checkpointer = MemorySaver()
    agent = create_react_agent(
        llm,
        tools=tools,
        checkpointer=checkpointer,
        prompt=SYSTEM_PROMPT
    )
    return agent

# Singleton instance
_agent_instance = None

def run_agent_message(user_message: str, thread_id: str = "default_user") -> str:
    """Runs a message through the LangGraph agent and returns the final answer."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = get_agent()

    config = {"configurable": {"thread_id": thread_id}}
    result = _agent_instance.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config
    )
    
    last_message = result["messages"][-1]
    return last_message.content

if __name__ == "__main__":
    print("=== Testing LangGraph Showrunner Agent ===")
    test_query = "What are the latest completed video runs and what tools do you have?"
    print(f"\nUser: {test_query}\n")
    response = run_agent_message(test_query)
    print(f"Agent:\n{response}")
