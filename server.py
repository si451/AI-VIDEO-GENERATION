import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import OUTPUT_DIR, MEMORY_DIR, VOICE_MAP
from modules.competitor_engine import analyze_competitors
from modules.story_engine import generate_story
from modules.visual_engine import generate_frame_image, free_gpu
from modules.tts_engine import generate_scene_voice
from agent import run_agent_message
import harness
from modules.progress_tracker import tracker
import threading
import uuid

app = FastAPI(title="AI Kids Cartoon Video Harness API", version="2.0")

# CORS middleware for Next.js (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure output directories exist
(OUTPUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "evaluations").mkdir(parents=True, exist_ok=True)

# Mount static media directories
app.mount("/media/runs", StaticFiles(directory=str(OUTPUT_DIR / "runs")), name="runs")
app.mount("/media/evaluations", StaticFiles(directory=str(OUTPUT_DIR / "evaluations")), name="evaluations")

# Data Models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default_user"

class GenerateRequest(BaseModel):
    topic: Optional[str] = None
    num_frames: Optional[int] = None
    aspect_ratio: Optional[str] = "9:16"

class CharacterModel(BaseModel):
    name: str
    role: str
    voice_type: str
    visual_anchor: str
    personality: Optional[str] = ""

# In-memory generation status tracking
generation_jobs = {}

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "vram_allocated_mb": round(torch.cuda.memory_allocated() / (1024**2), 2) if torch.cuda.is_available() else 0
    }

@app.get("/api/stats")
def get_stats():
    runs_dir = OUTPUT_DIR / "runs"
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")], reverse=True)
    
    total_duration = 0.0
    for r in runs:
        meta_file = r / "final_video_metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_duration += data.get("total_duration_sec", 0.0)
            except Exception:
                pass

    return {
        "total_videos": len(runs),
        "total_runtime_seconds": round(total_duration, 2),
        "gpu_model": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "active_model": "Yntec/DisneyPixarCartoon768 (Local SD 1.5)",
        "voice_engine": "Edge-TTS Neural Child Voices"
    }

@app.get("/api/runs")
def get_runs():
    runs_dir = OUTPUT_DIR / "runs"
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")], reverse=True)
    
    results = []
    for r in runs:
        meta_file = r / "final_video_metadata.json"
        story_file = r / "story_package.json"
        video_file = r / "final_video.mp4"
        scenes_dir = r / "scenes"

        title = r.name
        dur = 0.0
        aspect = "16:9"
        tags = []
        chapters = []

        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    title = meta.get("youtube_title", r.name)
                    dur = meta.get("total_duration_sec", 0.0)
                    aspect = meta.get("aspect_ratio", "16:9")
                    tags = meta.get("youtube_tags", [])
                    chapters = meta.get("chapters", [])
            except Exception:
                pass

        # Find thumbnail (first frame or scene image)
        thumbnail_url = None
        first_frame = scenes_dir / "frame_01.jpg"
        if not first_frame.exists():
            first_frame = scenes_dir / "scene_1.jpg"
        if first_frame.exists():
            thumbnail_url = f"/media/runs/{r.name}/scenes/{first_frame.name}"

        # Frame count
        frames_found = len(list(scenes_dir.glob("frame_*.jpg"))) or len(list(scenes_dir.glob("scene_*.jpg")))

        results.append({
            "id": r.name,
            "title": title,
            "duration": round(dur, 2),
            "aspect_ratio": aspect,
            "video_url": f"/media/runs/{r.name}/final_video.mp4" if video_file.exists() else None,
            "thumbnail_url": thumbnail_url,
            "tags": tags,
            "chapters": chapters,
            "frame_count": frames_found
        })

    return results

@app.get("/api/runs/{run_id}")
def get_run_details(run_id: str):
    run_dir = OUTPUT_DIR / "runs" / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    meta_file = run_dir / "final_video_metadata.json"
    story_file = run_dir / "story_package.json"
    video_file = run_dir / "final_video.mp4"
    scenes_dir = run_dir / "scenes"
    audio_dir = run_dir / "audio"

    metadata = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            pass

    story_data = {}
    if story_file.exists():
        try:
            with open(story_file, "r", encoding="utf-8") as f:
                story_data = json.load(f)
        except Exception:
            pass

    raw_frames = story_data.get("frames", story_data.get("scenes", []))
    frames = []

    for idx, rf in enumerate(raw_frames):
        fid = rf.get("frame_id", rf.get("scene_id", idx + 1))
        img_name = f"frame_{fid:02d}.jpg"
        if not (scenes_dir / img_name).exists():
            img_name = f"scene_{fid}.jpg"

        audio_name = f"frame_{fid:02d}_voice.mp3"
        if not (audio_dir / audio_name).exists():
            audio_name = f"scene_{fid}_voice.mp3"

        frames.append({
            "frame_id": fid,
            "speaker": rf.get("speaker", "Child Narrator"),
            "dialogue": rf.get("dialogue", ""),
            "camera_motion": rf.get("camera_motion", "zoom_in_slow"),
            "visual_prompt": rf.get("visual_prompt", ""),
            "image_url": f"/media/runs/{run_id}/scenes/{img_name}" if (scenes_dir / img_name).exists() else None,
            "audio_url": f"/media/runs/{run_id}/audio/{audio_name}" if (audio_dir / audio_name).exists() else None,
        })

    return {
        "id": run_id,
        "title": metadata.get("youtube_title", run_id),
        "description": metadata.get("youtube_description", ""),
        "tags": metadata.get("youtube_tags", []),
        "chapters": metadata.get("chapters", []),
        "duration": metadata.get("total_duration_sec", 0.0),
        "aspect_ratio": metadata.get("aspect_ratio", "16:9"),
        "video_url": f"/media/runs/{run_id}/final_video.mp4" if video_file.exists() else None,
        "master_audio_url": f"/media/runs/{run_id}/audio/master_audio.mp3" if (audio_dir / "master_audio.mp3").exists() else None,
        "frames": frames,
        "character_bible": story_data.get("character_bible", {})
    }

def _run_agent_worker(job_id: str, message: str, thread_id: str):
    tracker.start_job(job_id=job_id, title=message[:50], total_frames=15, aspect_ratio="16:9")
    try:
        reply = run_agent_message(message, thread_id=thread_id)
        if tracker.is_active:
            tracker.complete_job(reply=reply)
        else:
            tracker.latest_reply = reply
    except Exception as e:
        import traceback
        traceback.print_exc()
        tracker.fail_job(str(e))

@app.post("/api/agent/chat")
def chat_with_agent(req: ChatRequest):
    job_id = str(uuid.uuid4())[:8]
    if tracker.is_active:
        return {
            "status": "busy",
            "job_id": tracker.job_id,
            "message": f"A production task is already running: {tracker.detail}"
        }
    
    t = threading.Thread(
        target=_run_agent_worker,
        args=(job_id, req.message, req.thread_id or "default_user"),
        daemon=True
    )
    t.start()
    return {"status": "started", "job_id": job_id}

@app.get("/api/agent/status")
@app.get("/api/production/status")
def get_production_status():
    return tracker.to_dict()

@app.post("/api/production/stop")
def stop_production():
    from modules.visual_engine import free_gpu
    free_gpu()
    tracker.fail_job("Production cancelled by user.")
    return {"status": "stopped", "message": "Production halted and GPU memory released."}

@app.post("/api/production/clean")
def clean_production_runs():
    runs_dir = OUTPUT_DIR / "runs"
    deleted = 0
    if runs_dir.exists():
        import shutil
        for r in runs_dir.iterdir():
            if r.is_dir():
                try:
                    shutil.rmtree(r)
                    deleted += 1
                except Exception:
                    pass
    tracker.reset()
    return {"status": "cleaned", "deleted_runs": deleted}

def _run_production_task(job_id: str, topic: Optional[str], num_frames: int, aspect_ratio: str):
    tracker.start_job(job_id, title=topic or "One-Click Production", total_frames=num_frames, aspect_ratio=aspect_ratio)
    generation_jobs[job_id] = {"status": "processing", "progress": 10, "step": "Auditing channel & researching competitors..."}
    try:
        result = harness.run_production_pipeline(
            topic=topic,
            num_frames=num_frames,
            aspect_ratio=aspect_ratio,
            use_competitor_trends=True,
            use_local_images=True
        )
        generation_jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "step": "Finished",
            "run_dir": result.get("run_dir"),
            "final_video": result.get("final_video"),
            "duration": result.get("duration"),
            "metadata": result.get("metadata")
        }
    except Exception as e:
        generation_jobs[job_id] = {"status": "failed", "error": str(e)}

@app.get("/api/my_channel")
def get_my_channel():
    channel_file = MEMORY_DIR / "my_channel.json"
    if channel_file.exists():
        try:
            with open(channel_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {}

@app.post("/api/generate")
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    import uuid
    job_id = str(uuid.uuid4())[:8]
    topic_clean = req.topic.strip() if req.topic and req.topic.strip() else None
    aspect_ratio = req.aspect_ratio or "9:16"
    num_frames = req.num_frames or (10 if aspect_ratio == "9:16" else 20)

    background_tasks.add_task(
        _run_production_task,
        job_id,
        topic_clean,
        num_frames,
        aspect_ratio
    )
    return {"job_id": job_id, "status": "started", "aspect_ratio": aspect_ratio, "frames": num_frames}

@app.get("/api/generate/{job_id}")
def check_generation_status(job_id: str):
    job = generation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return job

@app.get("/api/competitors")
def get_competitor_insights(query: str = "bedtime stories for kids cartoon", max_results: int = 6):
    insights = analyze_competitors(query=query, max_results=max_results)
    title_formulas = [
        "🌟 Can [Character Name] [Overcome the Challenge]? | Heartwarming Moral Story For Kids",
        "[Character Name] & The [Magical Object] | Bedtime Stories For Kids | Cartoon Animation",
        "Bedtime Story For Kids (Ages 3-7) | Calming Sleep Cartoon for Toddlers #Shorts"
    ]
    return {
        "niche_query": query,
        "top_videos": insights.get("top_videos", []),
        "top_keywords": insights.get("top_keywords", []),
        "title_formulas": title_formulas
    }

@app.get("/api/character_bible")
def get_character_bible():
    cb_path = MEMORY_DIR / "character_bible.json"
    if cb_path.exists():
        try:
            with open(cb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "characters": [
            {
                "name": "Barnaby Bear",
                "role": "main_character",
                "voice_type": "child_male",
                "visual_anchor": "Barnaby the baby grizzly cub bear, ultra-soft honey-brown fur, light beige muzzle, chubby rounded ears, wearing a cozy tiny red adventurer backpack, big friendly warm green eyes, playful smile, 3D Disney Pixar character design, soft rim lighting, octane 3d render",
                "personality": "Kind, curious, loyal friend"
            },
            {
                "name": "Squeaky Squirrel",
                "role": "sidekick",
                "voice_type": "child_female",
                "visual_anchor": "Squeaky the red bushy-tailed baby squirrel, copper fur, fluffy white chest, wearing a miniature knitted acorn cap, giant curious dark eyes, twitchy nose, expressive 3D Disney Pixar animation style, adorable miniature proportions",
                "personality": "Brave, energetic, loves sharing acorns"
            }
        ]
    }

@app.post("/api/character_bible")
def save_character_bible(data: dict):
    cb_path = MEMORY_DIR / "character_bible.json"
    cb_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cb_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"status": "saved"}

if __name__ == "__main__":
    import uvicorn
    print("Starting AI Video Harness FastAPI Server on http://localhost:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

