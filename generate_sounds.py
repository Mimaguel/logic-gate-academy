#!/usr/bin/env python3
"""
Generates short, original UI sound effects as .wav files using plain sine
synthesis (numpy) - no external audio samples, so no licensing concerns.
Run once; the output .wav files are what actually ship with the game.
"""
import numpy as np
import wave
import struct
from pathlib import Path

SR = 44100
OUT_DIR = str(Path(__file__).resolve().parent / "assets" / "sounds")


def envelope(n, attack=0.02, release=0.35):
    """Simple fast-attack / exponential-release amplitude envelope."""
    t = np.linspace(0, 1, n)
    a_samples = max(1, int(n * attack))
    env = np.ones(n)
    env[:a_samples] = np.linspace(0, 1, a_samples)
    decay_start = n - int(n * release)
    if decay_start < n:
        decay_len = n - decay_start
        env[decay_start:] *= np.exp(-np.linspace(0, 6, decay_len))
    return env


def tone(freq, duration, amp=0.3, wave_shape="sine", fm_to=None):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if fm_to is not None:
        freq_curve = np.linspace(freq, fm_to, n)
        phase = 2 * np.pi * np.cumsum(freq_curve) / SR
    else:
        phase = 2 * np.pi * freq * t
    if wave_shape == "sine":
        wav = np.sin(phase)
    elif wave_shape == "square":
        wav = np.sign(np.sin(phase))
    elif wave_shape == "triangle":
        wav = 2 * np.abs(2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))) - 1
    else:
        wav = np.sin(phase)
    return wav * amp


def save_wav(path, samples):
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())
    print(f"wrote {path} ({len(samples) / SR:.2f}s)")


# --- click: crisp short digital tick ---
n = int(SR * 0.06)
s = tone(1400, 0.06, amp=0.25, wave_shape="square") * envelope(n, attack=0.01, release=0.85)
save_wav(f"{OUT_DIR}/click.wav", s)

# --- nav: soft short whoosh/tick for page transitions ---
n = int(SR * 0.09)
s = tone(900, 0.09, amp=0.15, wave_shape="sine", fm_to=500) * envelope(n, attack=0.02, release=0.8)
save_wav(f"{OUT_DIR}/nav.wav", s)

# --- correct: bright ascending two-note chime ---
n1 = int(SR * 0.11)
n2 = int(SR * 0.20)
part1 = tone(660, 0.11, amp=0.28) * envelope(n1, attack=0.01, release=0.6)
part2 = tone(990, 0.20, amp=0.30) * envelope(n2, attack=0.01, release=0.7)
s = np.concatenate([part1, part2])
save_wav(f"{OUT_DIR}/correct.wav", s)

# --- wrong: short descending buzz ---
n = int(SR * 0.28)
s = tone(260, 0.28, amp=0.28, wave_shape="triangle", fm_to=110) * envelope(n, attack=0.01, release=0.55)
save_wav(f"{OUT_DIR}/wrong.wav", s)

# --- victory: triumphant 4-note major arpeggio ---
notes = [523.25, 659.25, 783.99, 1046.50]  # C5 E5 G5 C6
parts = []
for i, freq in enumerate(notes):
    dur = 0.16 if i < 3 else 0.35
    n = int(SR * dur)
    parts.append(tone(freq, dur, amp=0.30) * envelope(n, attack=0.01, release=0.6))
s = np.concatenate(parts)
save_wav(f"{OUT_DIR}/victory.wav", s)

# --- fail: low descending two-note "run over" tone ---
n1 = int(SR * 0.18)
n2 = int(SR * 0.30)
part1 = tone(220, 0.18, amp=0.28, wave_shape="triangle") * envelope(n1, attack=0.01, release=0.5)
part2 = tone(140, 0.30, amp=0.28, wave_shape="triangle") * envelope(n2, attack=0.01, release=0.7)
s = np.concatenate([part1, part2])
save_wav(f"{OUT_DIR}/fail.wav", s)

print("done")
