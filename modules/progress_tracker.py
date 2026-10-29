import time
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = MEMORY_DIR / "current_job.json"

_lock = threading.Lock()

DEFAULT_STAGES = [
    {"key": "audit", "title": "🔍 Audit Channel & Mascots", "status": "pending"},
    {"key": "competitors", "title": "📈 Scan Viral Competitors (>1M views)", "status": "pending"},
    {"key": "script", "title": "✍️ Draft Script & 3s Frame Storyboard", "status": "pending"},
    {"key": "visuals", "title": "🎨 Render 3D Disney/Pixar Visuals (RTX 2050)", "status": "pending"},
    {"key": "voice", "title": "🎙️ Synthesize Child Voices & Timestamps", "status": "pending"},
    {"key": "motion", "title": "🎥 Animate Smooth 2.5D Camera Motion", "status": "pending"},
    {"key": "assembly", "title": "🎞️ NVENC Master Video Assembly", "status": "pending"}
]

class ProgressTracker:
    def __init__(self):
        self.is_active: bool = False
        self.job_id: Optional[str] = None
        self.title: str = "Production Run"
        self.aspect_ratio: str = "16:9"
        self.current_stage: str = "idle"
        self.stage_title: str = "Idle"
        self.detail: str = "Ready for next production"
        self.progress_percent: int = 0
        self.current_frame: int = 0
        self.total_frames: int = 0
        self.start_time: float = 0.0
        self.stages: List[Dict[str, str]] = [dict(s) for s in DEFAULT_STAGES]
        self.error: Optional[str] = None
        self.latest_reply: Optional[str] = None
        self.final_video_url: Optional[str] = None
        self.run_dir: Optional[str] = None
        self._load_persisted_state()

    def _persist(self):
        try:
            data = self.to_dict()
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_persisted_state(self):
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # If loaded from disk and was active long ago (> 30 mins), mark finished/idle
                    if data.get("is_active") and time.time() - data.get("start_time", 0) > 1800:
                        data["is_active"] = False
                    self.is_active = data.get("is_active", False)
                    self.job_id = data.get("job_id")
                    self.title = data.get("title", "Production Run")
                    self.aspect_ratio = data.get("aspect_ratio", "16:9")
                    self.current_stage = data.get("current_stage", "idle")
                    self.stage_title = data.get("stage_title", "Idle")
                    self.detail = data.get("detail", "")
                    self.progress_percent = data.get("progress_percent", 0)
                    self.current_frame = data.get("current_frame", 0)
                    self.total_frames = data.get("total_frames", 0)
                    self.start_time = data.get("start_time", time.time())
                    self.stages = data.get("stages", [dict(s) for s in DEFAULT_STAGES])
                    self.error = data.get("error")
                    self.latest_reply = data.get("latest_reply")
                    self.final_video_url = data.get("final_video_url")
                    self.run_dir = data.get("run_dir")
            except Exception:
                pass

    def start_job(self, job_id: str, title: str = "Production Run", total_frames: int = 15, aspect_ratio: str = "16:9"):
        with _lock:
            self.is_active = True
            self.job_id = job_id
            self.title = title
            self.aspect_ratio = aspect_ratio
            self.current_stage = "audit"
            self.stage_title = "🔍 Channel & Competitor Research"
            self.detail = "Auditing @WhimsyWandTales and researching top viral hits..."
            self.progress_percent = 5
            self.current_frame = 0
            self.total_frames = total_frames
            self.start_time = time.time()
            self.error = None
            self.latest_reply = None
            self.final_video_url = None
            self.run_dir = None
            self.stages = [dict(s) for s in DEFAULT_STAGES]
            self.stages[0]["status"] = "in_progress"
            self._persist()

    def update_stage(self, stage_key: str, stage_title: str, detail: str, progress_percent: int):
        with _lock:
            self.current_stage = stage_key
            self.stage_title = stage_title
            self.detail = detail
            self.progress_percent = max(0, min(100, progress_percent))
            found = False
            for s in self.stages:
                if s["key"] == stage_key:
                    s["status"] = "in_progress"
                    found = True
                elif not found:
                    s["status"] = "completed"
                else:
                    if s["status"] != "completed":
                        s["status"] = "pending"
            self._persist()

    def update_frame(self, current_frame: int, total_frames: int):
        with _lock:
            self.current_frame = current_frame
            self.total_frames = total_frames
            # Visuals stage spans progress from 35% to 75%
            pct = 35 + int((current_frame / max(1, total_frames)) * 40)
            self.progress_percent = min(75, pct)
            self.detail = f"Synthesizing 3D Disney/Pixar Frame {current_frame} of {total_frames} on RTX 2050..."
            self._persist()

    def complete_job(self, reply: str = "", video_url: Optional[str] = None, run_dir: Optional[str] = None):
        with _lock:
            self.is_active = False
            self.current_stage = "completed"
            self.stage_title = "✅ Production Complete!"
            self.detail = "All frames rendered, voiced, and assembled into final video."
            self.progress_percent = 100
            for s in self.stages:
                s["status"] = "completed"
            self.latest_reply = reply
            self.final_video_url = video_url
            self.run_dir = run_dir
            self.error = None
            self._persist()

    def fail_job(self, error_message: str):
        with _lock:
            self.is_active = False
            self.current_stage = "failed"
            self.stage_title = "❌ Production Error"
            self.detail = error_message
            self.error = error_message
            for s in self.stages:
                if s["status"] == "in_progress":
                    s["status"] = "failed"
            self._persist()

    def reset(self):
        with _lock:
            self.is_active = False
            self.current_stage = "idle"
            self.stage_title = "Idle"
            self.detail = "Studio ready."
            self.progress_percent = 0
            self.error = None
            self.stages = [dict(s) for s in DEFAULT_STAGES]
            self._persist()

    def to_dict(self) -> Dict[str, Any]:
        elapsed = round(time.time() - self.start_time, 1) if self.start_time > 0 and (self.is_active or self.progress_percent > 0) else 0.0
        
        # Estimate remaining time based on current percent & elapsed
        estimated_remaining = 0.0
        if self.is_active and self.progress_percent > 5 and elapsed > 2:
            remaining_pct = 100 - self.progress_percent
            time_per_pct = elapsed / self.progress_percent
            estimated_remaining = round(remaining_pct * time_per_pct, 1)
        
        return {
            "is_active": self.is_active,
            "job_id": self.job_id,
            "title": self.title,
            "aspect_ratio": self.aspect_ratio,
            "current_stage": self.current_stage,
            "stage_title": self.stage_title,
            "detail": self.detail,
            "progress_percent": self.progress_percent,
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "elapsed_seconds": elapsed,
            "estimated_remaining_seconds": estimated_remaining,
            "stages": self.stages,
            "error": self.error,
            "latest_reply": self.latest_reply,
            "final_video_url": self.final_video_url,
            "run_dir": self.run_dir
        }

tracker = ProgressTracker()
