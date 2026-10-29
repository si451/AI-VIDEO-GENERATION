import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import YOUTUBE_API_KEY, MEMORY_DIR

def analyze_competitors(query: str = "bedtime stories for kids cartoon", max_results: int = 8) -> dict:
    """
    Scrapes high-performing videos in the kids story niche using YouTube Data API v3.
    Extracts titles, view counts, tags, and common title formulas.
    Saves intelligence to memory/channel_insights.json for DeepSeek to learn from.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY is not configured in .env")

    # Step 1: Search for videos ordered by viewCount
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "maxResults": max_results,
        "videoDuration": "medium",  # 4-20 mins
        "key": YOUTUBE_API_KEY
    }
    search_url = f"https://www.googleapis.com/youtube/v3/search?{urllib.parse.urlencode(search_params)}"
    
    req = urllib.request.Request(search_url, headers={"User-Agent": "AIVideoHarness/1.0"})
    with urllib.request.urlopen(req) as resp:
        search_data = json.loads(resp.read().decode("utf-8"))

    items = search_data.get("items", [])
    video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]
    
    if not video_ids:
        return {"error": "No videos found"}

    # Step 2: Fetch detailed statistics (viewCount, likeCount, tags)
    stats_params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    }
    stats_url = f"https://www.googleapis.com/youtube/v3/videos?{urllib.parse.urlencode(stats_params)}"
    
    req2 = urllib.request.Request(stats_url, headers={"User-Agent": "AIVideoHarness/1.0"})
    with urllib.request.urlopen(req2) as resp2:
        stats_data = json.loads(resp2.read().decode("utf-8"))

    competitor_insights = []
    all_tags = []

    for item in stats_data.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        
        title = snippet.get("title", "")
        views = int(statistics.get("viewCount", 0))
        tags = snippet.get("tags", [])
        channel_title = snippet.get("channelTitle", "")
        
        all_tags.extend(tags[:5])
        competitor_insights.append({
            "title": title,
            "views": views,
            "channel": channel_title,
            "tags": tags[:8]
        })

    # Sort by views descending
    competitor_insights.sort(key=lambda x: x["views"], reverse=True)

    result = {
        "niche_query": query,
        "total_analyzed": len(competitor_insights),
        "top_videos": competitor_insights,
        "top_keywords": list(set(all_tags))[:15]
    }

    # Save to persistent memory
    memory_file = MEMORY_DIR / "channel_insights.json"
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result

if __name__ == "__main__":
    print("Testing Competitor Engine...")
    insights = analyze_competitors("bedtime stories for kids cartoon", max_results=5)
    print(f"Scraped {len(insights['top_videos'])} competitor videos:")
    for v in insights["top_videos"]:
        print(f" - [{v['views']:,} views] {v['title']} (by {v['channel']})")
