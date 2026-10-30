"""
WhimsyWand Tales - Bedtime Acoustic Lullaby & Music Box Generator
Generates authentic acoustic music-box and sleepy piano lullabies with bell harmonics,
gentle arpeggios, and warm decaying envelopes. Completely eliminates robotic sine beeps!
"""

import numpy as np
import scipy.io.wavfile
import subprocess
from pathlib import Path

# Note frequencies (Hz)
NOTES = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "C6": 1046.50
}

def synthesize_music_box_note(freq: float, duration: float, sr: int = 44100) -> np.ndarray:
    """Synthesizes a realistic bell-like music box chime with natural acoustic decay."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Fundamental + classic music box strike harmonics (1x, 2.76x, 5.4x)
    envelope1 = np.exp(-1.8 * t)  # Long warm body
    envelope2 = np.exp(-4.5 * t)  # Shimmering chime
    envelope3 = np.exp(-9.0 * t)  # Initial delicate strike tap

    tone = (
        0.60 * np.sin(2 * np.pi * freq * t) * envelope1 +
        0.25 * np.sin(2 * np.pi * freq * 2.76 * t) * envelope2 +
        0.15 * np.sin(2 * np.pi * freq * 5.40 * t) * envelope3
    )
    return tone

def create_soothing_bedtime_lullaby(output_mp3: Path, duration_sec: float = 360.0, track_theme: str = "starlight"):
    """
    Synthesizes a continuous, calming music box lullaby with gentle chord progressions.
    """
    sr = 44100
    bpm = 64.0  # Slow relaxing bedtime tempo
    beat_dur = 60.0 / bpm

    # 8-measure gentle lullaby sequence (repeats continuously)
    # Each entry: (note_name, beat_offset, note_duration)
    melody_patterns = {
        "starlight": [
            # Measure 1: C major starlight
            ("C4", 0.0, 3.0), ("E4", 0.5, 2.5), ("G4", 1.0, 2.0), ("C5", 1.5, 2.5), ("G4", 2.0, 2.0), ("E4", 2.5, 2.0),
            # Measure 2: G major gentle
            ("G3", 3.0, 3.0), ("D4", 3.5, 2.5), ("G4", 4.0, 2.0), ("B4", 4.5, 2.5), ("G4", 5.0, 2.0), ("D4", 5.5, 2.0),
            # Measure 3: A minor sweet
            ("A3", 6.0, 3.0), ("C4", 6.5, 2.5), ("E4", 7.0, 2.0), ("A4", 7.5, 2.5), ("E4", 8.0, 2.0), ("C4", 8.5, 2.0),
            # Measure 4: F major soft hug
            ("F3", 9.0, 3.0), ("A3", 9.5, 2.5), ("C4", 10.0, 2.0), ("F4", 10.5, 2.5), ("C4", 11.0, 2.0), ("A3", 11.5, 2.0),
            # Measure 5: C major peaceful
            ("C4", 12.0, 3.0), ("G4", 12.5, 2.5), ("E5", 13.0, 2.5), ("D5", 13.5, 2.0), ("C5", 14.0, 2.5), ("G4", 14.5, 2.0),
            # Measure 6: F to G transition
            ("F4", 15.0, 2.5), ("A4", 15.5, 2.0), ("G4", 16.0, 3.0), ("B4", 16.5, 2.5), ("D5", 17.0, 2.0), ("B4", 17.5, 2.0),
            # Measure 7: Sleepy descent
            ("C5", 18.0, 3.5), ("G4", 19.0, 3.0), ("E4", 20.0, 3.0), ("C4", 21.0, 4.0),
            # Measure 8: Warm rest
            ("G3", 22.0, 3.0), ("C4", 23.0, 4.0)
        ]
    }

    pattern = melody_patterns.get(track_theme, melody_patterns["starlight"])
    cycle_duration = 24.0 * beat_dur  # ~22.5s per cycle

    total_samples = int(sr * (duration_sec + 4.0))
    audio_buffer = np.zeros(total_samples, dtype=np.float32)

    current_time = 0.0
    while current_time < duration_sec:
        for note, beat_off, note_len in pattern:
            start_sec = current_time + (beat_off * beat_dur)
            if start_sec >= duration_sec:
                break
            freq = NOTES.get(note, 440.0)
            note_audio = synthesize_music_box_note(freq, note_len, sr=sr)
            
            start_idx = int(start_sec * sr)
            end_idx = min(start_idx + len(note_audio), total_samples)
            samples_to_add = end_idx - start_idx
            if samples_to_add > 0:
                audio_buffer[start_idx:end_idx] += note_audio[:samples_to_add] * 0.18

        current_time += cycle_duration

    # Gentle soft master fade in and fade out
    fade_in_samples = int(sr * 2.0)
    fade_out_samples = int(sr * 3.5)
    audio_buffer[:fade_in_samples] *= np.linspace(0, 1, fade_in_samples)
    audio_buffer[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples)

    # Normalize volume
    peak = np.max(np.abs(audio_buffer))
    if peak > 0:
        audio_buffer = (audio_buffer / peak) * 0.45

    # Write WAV and encode with FFmpeg to high-quality MP3
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    temp_wav = output_mp3.with_suffix(".temp.wav")
    int16_audio = (audio_buffer * 32767).astype(np.int16)
    scipy.io.wavfile.write(str(temp_wav), sr, int16_audio)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_wav),
        "-t", f"{duration_sec:.2f}",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_mp3)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if temp_wav.exists():
        temp_wav.unlink()

    return output_mp3

if __name__ == "__main__":
    test_out = Path("assets/bgm/bedtime_music_box_lullaby.mp3")
    create_soothing_bedtime_lullaby(test_out, duration_sec=60.0)
    print("Generated real music box lullaby:", test_out)

