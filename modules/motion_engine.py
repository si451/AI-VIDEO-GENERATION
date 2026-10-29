import os
import sys
import subprocess
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    SCENES_DIR,
    VIDEO_FPS,
    SHORTS_WIDTH,
    SHORTS_HEIGHT,
    LONG_WIDTH,
    LONG_HEIGHT
)

def build_smooth_motion_filter(
    motion_type: str,
    duration_sec: float,
    aspect_ratio: str = "9:16",
    fps: int = 30
) -> str:
    """
    Constructs butter-smooth, jitter-free FFmpeg camera motion filters.
    Eliminates sub-pixel shaking by using incremental zoom steps with high-resolution pre-scaling.
    Supports both 9:16 vertical shorts and 16:9 widescreen.
    """
    total_frames = max(int(duration_sec * fps), 30)
    
    if aspect_ratio == "9:16":
        out_w, out_h = SHORTS_WIDTH, SHORTS_HEIGHT      # 720x1280
        scale_w, scale_h = 1080, 1920                   # Pre-scale for zero jitter
    else:
        out_w, out_h = LONG_WIDTH, LONG_HEIGHT          # 1280x720
        scale_w, scale_h = 1920, 1080

    # Gentle zoom rate: over ~3 seconds (90 frames), zoom from 1.00 to ~1.08
    # Rate per frame = 0.08 / total_frames
    zoom_step = round(0.08 / max(total_frames, 1), 6)

    if motion_type == "zoom_in_slow":
        # Ultra smooth slow push-in towards center
        filter_str = (
            f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
            f"crop={scale_w}:{scale_h},"
            f"zoompan=z='min(zoom+{zoom_step},1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps={fps}"
        )
    elif motion_type == "zoom_out_slow":
        # Ultra smooth pull-back
        filter_str = (
            f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
            f"crop={scale_w}:{scale_h},"
            f"zoompan=z='if(lte(zoom,1.0),1.10,max(1.001,zoom-{zoom_step}))':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps={fps}"
        )
    elif motion_type == "pan_right":
        # Smooth gentle drift right
        pan_step = round(40.0 / max(total_frames, 1), 3)
        filter_str = (
            f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
            f"crop={scale_w}:{scale_h},"
            f"zoompan=z='1.08':d=1:x='min(x+{pan_step},iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps={fps}"
        )
    elif motion_type == "pan_left":
        # Smooth gentle drift left
        pan_step = round(40.0 / max(total_frames, 1), 3)
        filter_str = (
            f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
            f"crop={scale_w}:{scale_h},"
            f"zoompan=z='1.08':d=1:x='max(x-{pan_step},0)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps={fps}"
        )
    else:  # default gentle zoom in
        filter_str = (
            f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=increase,"
            f"crop={scale_w}:{scale_h},"
            f"zoompan=z='min(zoom+{zoom_step},1.08)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps={fps}"
        )

    return filter_str

# Alias for backward compatibility
build_zoompan_filter = build_smooth_motion_filter

def animate_frame_image(
    image_path: Path,
    output_path: Path,
    duration_sec: float,
    motion_type: str = "zoom_in_slow",
    aspect_ratio: str = "9:16"
) -> Path:
    """
    Converts a static illustration into a dynamic 30fps clip using GPU-accelerated NVENC.
    Guarantees exact audio duration lock and butter-smooth motion.
    """
    filter_expr = build_smooth_motion_filter(motion_type, duration_sec, aspect_ratio=aspect_ratio, fps=VIDEO_FPS)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", filter_expr,
        "-t", f"{duration_sec:.3f}",
        "-c:v", "h264_nvenc",
        "-preset", "p6",      # Higher quality preset
        "-cq", "18",          # High fidelity, low compression artifacts
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        # Fallback to libx264 if NVENC busy
        cmd[cmd.index("h264_nvenc")] = "libx264"
        cmd[cmd.index("-preset") + 1] = "medium"
        cmd[cmd.index("-cq")] = "-crf"
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg motion generation failed: {proc.stderr}")

    return output_path

# Alias for backward compatibility
animate_scene_image = animate_frame_image

def animate_all_frames(
    frames: list,
    voice_metadata: list,
    aspect_ratio: str = "9:16",
    scenes_dir: Path = None,
    min_duration_sec: float = 0.0
) -> list:
    """
    Animates all frame images matching each frame's exact spoken audio duration.
    """
    if scenes_dir is None:
        scenes_dir = SCENES_DIR
    animated_clips = []
    print(f"\n[Motion Engine] Animating {len(frames)} frames ({aspect_ratio}, smooth slow zoom/pan, NVENC 30fps)...")

    # Map durations from voice metadata
    dur_map = {}
    for v in voice_metadata:
        fid = v.get("frame_id", v.get("scene_id", 1))
        dur_map[fid] = max(v["duration"], 1.5)

    for idx, frame in enumerate(frames):
        fid = frame.get("frame_id", frame.get("scene_id", idx + 1))
        motion = frame.get("camera_motion", "zoom_in_slow")
        voice_dur = dur_map.get(fid, 3.0)
        dur = max(voice_dur + 0.5, min_duration_sec) if min_duration_sec > 0 else voice_dur

        # Look for frame_01.jpg or scene_1.jpg
        img_path = scenes_dir / f"frame_{fid:02d}.jpg"
        if not img_path.exists():
            img_path = scenes_dir / f"scene_{fid}.jpg"

        clip_path = scenes_dir / f"frame_{fid:02d}_clip.mp4"

        print(f" -> Animating Frame {fid:02d} ({motion}, {dur:.2f}s, {aspect_ratio})...")
        animate_frame_image(img_path, clip_path, duration_sec=dur, motion_type=motion, aspect_ratio=aspect_ratio)
        animated_clips.append(clip_path)

    return animated_clips

# Alias for backward compatibility
animate_all_scenes = animate_all_frames

if __name__ == "__main__":
    print("Testing upgraded Motion Engine...")
    test_img = BASE_DIR / "output" / "evaluations" / "preview_agent_image.jpg"
    if not test_img.exists():
        test_img = list(SCENES_DIR.glob("*.jpg"))[0] if list(SCENES_DIR.glob("*.jpg")) else None
    
    if test_img and test_img.exists():
        test_out = BASE_DIR / "output" / "evaluations" / "test_smooth_motion.mp4"
        animate_frame_image(test_img, test_out, duration_sec=3.0, motion_type="zoom_in_slow", aspect_ratio="9:16")
        print(f"SUCCESS: Generated test smooth clip at {test_out}")
