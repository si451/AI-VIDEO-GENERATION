"""
WhimsyWand Studio - YouTube Channel Live Sync Engine
Syncs real-time video performance, views, durations, and uploads directly
from @WhimsyWandTales on YouTube without requiring paid API quota keys.
"""

import json
import logging
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("channel_syncer")
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
CHANNEL_FILE = MEMORY_DIR / "my_channel.json"
CHANNEL_URL = "https://www.youtube.com/@WhimsyWandTales"

def _find_keys(obj, key_name):
    """Recursively yield all instances of key_name in a nested dict/list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key_name:
                yield v
            else:
                yield from _find_keys(v, key_name)
    elif isinstance(obj, list):
        for item in obj:
            yield from _find_keys(item, key_name)

def _fetch_html_with_retry(url: str, retries: int = 3, delay: float = 1.0) -> str:
    """Fetch URL contents with browser headers and retry logic."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception as e:
            last_err = e
            time.sleep(delay * (attempt + 1))
    raise last_err

def extract_long_videos() -> List[Dict[str, Any]]:
    """Extract all long-form videos published to the channel."""
    url = f"{CHANNEL_URL}/videos"
    videos = []
    try:
        html = _fetch_html_with_retry(url)
        m = re.search(r"var ytInitialData = ({.*?});</script>", html)
        if not m:
            return videos
        
        data = json.loads(m.group(1))
        for l in _find_keys(data, "lockupViewModel"):
            meta_vm = l.get("metadata", {}).get("lockupMetadataViewModel", {})
            title = meta_vm.get("title", {}).get("content")
            rows = meta_vm.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", [])
            parts = rows[0].get("metadataParts", []) if rows else []
            views = parts[0].get("text", {}).get("content", "0 views") if len(parts) > 0 else "0 views"
            time_ago = parts[1].get("text", {}).get("content", "") if len(parts) > 1 else ""
            
            # Duration & Video ID extraction
            badges = l.get("contentImage", {}).get("thumbnailViewModel", {}).get("overlays", [])
            duration = "0:00"
            vid_id = None
            for b in badges:
                b_vm = b.get("thumbnailBottomOverlayViewModel", {})
                for badge in b_vm.get("badges", []):
                    tb = badge.get("thumbnailBadgeViewModel", {})
                    if "text" in tb:
                        duration = tb["text"]
                    if "animationActivationTargetId" in tb:
                        vid_id = tb["animationActivationTargetId"]
            
            if not vid_id:
                on_tap = l.get("rendererContext", {}).get("commandContext", {}).get("onTap", {})
                vid_id = on_tap.get("innertubeCommand", {}).get("watchEndpoint", {}).get("videoId")
            
            if vid_id and title:
                # Avoid duplicates
                if not any(v["id"] == vid_id for v in videos):
                    videos.append({
                        "id": vid_id,
                        "title": title,
                        "views": views if "view" in views.lower() else f"{views} views",
                        "published_time": time_ago,
                        "duration": duration,
                        "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "type": "long"
                    })
    except Exception as e:
        logger.warning(f"Error extracting long videos: {e}")
    return videos

def extract_shorts() -> List[Dict[str, Any]]:
    """Extract all YouTube Shorts published to the channel."""
    url = f"{CHANNEL_URL}/shorts"
    shorts = []
    try:
        html = _fetch_html_with_retry(url)
        m = re.search(r"var ytInitialData = ({.*?});</script>", html)
        if not m:
            return shorts
        
        data = json.loads(m.group(1))
        for s in _find_keys(data, "shortsLockupViewModel"):
            entity = s.get("entityId", "")
            vid_id = entity.replace("shorts-shelf-item-", "")
            
            overlay_meta = s.get("overlayMetadata", {})
            title = overlay_meta.get("primaryText", {}).get("content", "")
            views = overlay_meta.get("secondaryText", {}).get("content", "0 views")
            
            if not title:
                acc_text = s.get("accessibilityText", "")
                title = acc_text.split(",")[0] if acc_text else f"Short {vid_id}"
            
            if vid_id and title:
                if not any(sh["id"] == vid_id for sh in shorts):
                    shorts.append({
                        "id": vid_id,
                        "title": title,
                        "views": views,
                        "published_time": "Shorts Feed",
                        "duration": "< 60s",
                        "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        "url": f"https://www.youtube.com/shorts/{vid_id}",
                        "type": "short"
                    })
    except Exception as e:
        logger.warning(f"Error extracting shorts: {e}")
    return shorts

def sync_channel_metrics(force: bool = False) -> Dict[str, Any]:
    """
    Syncs the latest uploaded videos and view counts from YouTube into memory/my_channel.json.
    Returns the enriched channel data.
    """
    channel_data = {}
    if CHANNEL_FILE.exists():
        try:
            with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
                channel_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read channel json: {e}")

    try:
        long_videos = extract_long_videos()
        shorts = extract_shorts()
        
        if long_videos or shorts:
            channel_data["live_videos"] = long_videos
            channel_data["live_shorts"] = shorts
            channel_data["total_long_videos"] = len(long_videos)
            channel_data["total_shorts"] = len(shorts)
            channel_data["total_uploaded_videos"] = len(long_videos) + len(shorts)
            channel_data["last_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            channel_data["sync_status"] = "synced_live"

            # Auto-update published_video_audit for Agent Showrunner memory
            existing_audit = {v.get("video_id") for v in channel_data.get("published_video_audit", [])}
            new_audit = list(channel_data.get("published_video_audit", []))
            
            for lv in long_videos:
                if lv["id"] not in existing_audit:
                    # Guess character
                    t_lower = lv["title"].lower()
                    char = "Bedtime Stories"
                    if "pip" in t_lower: char = "Pip the Dragon"
                    elif "fern" in t_lower: char = "Fern the Fairy"
                    elif "barnaby" in t_lower: char = "Barnaby Bear"
                    elif "luna" in t_lower: char = "Luna the Cloud"
                    elif "benny" in t_lower: char = "Benny Bunny"
                    
                    new_audit.insert(0, {
                        "title": lv["title"],
                        "video_id": lv["id"],
                        "character": char,
                        "duration": lv["duration"],
                        "views": lv["views"],
                        "published_time": lv["published_time"]
                    })
                    existing_audit.add(lv["id"])
                    
            for sh in shorts:
                if sh["id"] not in existing_audit:
                    t_lower = sh["title"].lower()
                    char = "Shorts"
                    if "pip" in t_lower: char = "Pip the Dragon"
                    elif "fern" in t_lower: char = "Fern the Fairy"
                    elif "barnaby" in t_lower: char = "Barnaby Bear"
                    elif "luna" in t_lower: char = "Luna the Cloud"
                    elif "benny" in t_lower: char = "Benny Bunny"
                    
                    new_audit.append({
                        "title": sh["title"],
                        "video_id": sh["id"],
                        "character": char,
                        "duration": sh["duration"],
                        "views": sh["views"],
                        "published_time": "Shorts"
                    })
                    existing_audit.add(sh["id"])

            channel_data["published_video_audit"] = new_audit

            # Save back to disk
            with open(CHANNEL_FILE, "w", encoding="utf-8") as f:
                json.dump(channel_data, f, indent=2, ensure_ascii=False)
            logger.info("Successfully updated memory/my_channel.json with live YouTube performance.")
        else:
            channel_data["sync_status"] = "cached_fallback"

    except Exception as e:
        logger.error(f"Channel sync failed: {e}")
        channel_data["sync_status"] = "error"
        channel_data["sync_error"] = str(e)

    return channel_data

if __name__ == "__main__":
    result = sync_channel_metrics()
    print(f"Sync complete! Total videos: {result.get('total_uploaded_videos')}")
    print(f"Live Long Videos: {len(result.get('live_videos', []))}")
    print(f"Live Shorts: {len(result.get('live_shorts', []))}")
