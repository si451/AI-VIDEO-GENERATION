"""
WhimsyWand Studio - Conversation History & Session Manager
Persists multi-thread chat history across browser reloads and server restarts.
Enables starting new conversations or switching between past production chats.
"""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("conversation_manager")
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
CONVERSATIONS_DIR = MEMORY_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WELCOME_MESSAGE = {
    "role": "assistant",
    "content": (
        "👋 **Welcome to WhimsyWand Tales Studio!** (@WhimsyWandTales)\n\n"
        "I am your AI Showrunner and YouTube Growth Director with full autonomous control of video production.\n\n"
        "Whenever you want to produce a video, simply tell me in chat or pick a prompt below! I will:\n"
        "1. 🔍 **Audit our Channel**: Inspect `@WhimsyWandTales` published history and core mascots (Pip the Dragon, Fern the Fairy, Barnaby Bear, Benny Bunny, Luna the Cloud).\n"
        "2. 📈 **Research Competitors**: Find viral videos with millions of views to adapt winning hooks and emotional story arcs.\n"
        "3. ✍️ **Draft Emotional Bedtime Scripts**: Hook young listeners in the first 15 seconds, weave in interactive somatic actions, and guide them through a soothing sleep slide.\n"
        "4. 🎨 **Render 3D Pixar Visuals**: Locally generate high-res artwork on your RTX 2050 (zero API cost).\n"
        "5. 🎙️ **Voiceover & Subtitles**: Strictly sweet child voices with ASS karaoke animations & NVENC master rendering!\n\n"
        "Tell me what you'd like to create, or ask for a **30-minute Bedtime Story Omnibus**!"
    )
}

def _get_conv_path(conv_id: str) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", conv_id)
    return CONVERSATIONS_DIR / f"{safe_id}.json"

def list_conversations() -> List[Dict[str, Any]]:
    """Returns metadata list of all saved conversations, sorted newest first."""
    convs = []
    for f in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            convs.append({
                "id": data.get("id", f.stem),
                "title": data.get("title", "Untitled Chat"),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(data.get("messages", []))
            })
        except Exception as e:
            logger.warning(f"Error reading conversation {f}: {e}")

    # Sort descending by updated_at
    convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    # If empty, create initial default conversation
    if not convs:
        new_conv = create_conversation(title="WhimsyWand Bedtime Production")
        convs.append({
            "id": new_conv["id"],
            "title": new_conv["title"],
            "created_at": new_conv["created_at"],
            "updated_at": new_conv["updated_at"],
            "message_count": len(new_conv["messages"])
        })

    return convs

def get_conversation(conv_id: str) -> Dict[str, Any]:
    """Retrieves full conversation with messages. If not found, creates it."""
    path = _get_conv_path(conv_id)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception as e:
            logger.error(f"Failed to read conversation {conv_id}: {e}")

    return create_conversation(conv_id=conv_id)

def create_conversation(conv_id: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new conversation session with welcome greeting."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cid = conv_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
    conv_data = {
        "id": cid,
        "title": title or "New Production Chat",
        "created_at": now,
        "updated_at": now,
        "messages": [DEFAULT_WELCOME_MESSAGE]
    }
    path = _get_conv_path(cid)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(conv_data, fp, indent=2, ensure_ascii=False)
    return conv_data

def append_message(conv_id: str, role: str, content: str) -> Dict[str, Any]:
    """Appends a user or assistant message and updates conversation timestamp & title."""
    conv = get_conversation(conv_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # If first user message and default title, update title based on prompt
    if role == "user" and (conv.get("title") in ["New Production Chat", "Untitled Chat"] or len(conv.get("messages", [])) <= 1):
        clean_prompt = content.strip().replace("\n", " ")
        if len(clean_prompt) > 35:
            clean_prompt = clean_prompt[:32].rstrip() + "..."
        conv["title"] = clean_prompt

    conv["updated_at"] = now
    conv.setdefault("messages", []).append({
        "role": role,
        "content": content,
        "timestamp": now
    })

    path = _get_conv_path(conv_id)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(conv, fp, indent=2, ensure_ascii=False)
    return conv

def delete_conversation(conv_id: str) -> bool:
    """Deletes conversation from disk."""
    path = _get_conv_path(conv_id)
    if path.exists():
        try:
            path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conv_id}: {e}")
    return False
