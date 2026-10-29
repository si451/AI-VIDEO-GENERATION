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
    compile_omnibus_tool
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

Autonomous Production Directives:
- When asked to analyze or make a video: ALWAYS first use `inspect_my_channel_tool` to check channel history, then use `analyze_competitors_tool` to find viral trends and keywords.
- When asked for a 30-Minute Video / Bedtime Story Compilation:
  * YouTube best practice: Format as a 5-Chapter Bedtime Story Omnibus (e.g. Chapter 1: Pip's Lost Star, Chapter 2: Fern's Glowing Garden, Chapter 3: Barnaby's Gentle Honey Quest, Chapter 4: Luna's Raindrop Lullaby, Chapter 5: Benny's Starlight Scarf).
  * Provide chapter timestamps (`0:00`, `6:00`, `12:00`, `18:00`, `24:00`), high-CTR title formulas, and tags.
  * Trigger production with `render_full_video_tool` or compile finished runs with `compile_omnibus_tool`.
- When asked to produce a Short: Use aspect_ratio="9:16", ~10 frames (30 seconds).
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
        compile_omnibus_tool
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

