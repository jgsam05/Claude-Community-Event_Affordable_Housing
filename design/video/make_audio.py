#!/usr/bin/env python3
"""Synthesizes the sound effects for the OCA demo video and writes oca-sfx.wav.

Every sound is timed to the animation in oca-demo.html. Needs only numpy.
Usage: python3 make_audio.py out.wav
Then mux with: ffmpeg -i oca-demo.mp4 -i out.wav -c:v copy -c:a aac -b:a 192k -shortest oca-demo-sfx.mp4
"""
import sys
import wave
import numpy as np

SR = 44100
DUR = 30.0
rng = np.random.default_rng(7)
mix = np.zeros((int(SR * DUR) + SR, 2))


def env_exp(n, decay):
    t = np.arange(n) / SR
    return np.exp(-t / decay)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    prev = 0.0
    for i in range(len(x)):
        prev = (1 - a) * x[i] + a * prev
        y[i] = prev
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def add(sound, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    n = min(len(sound), mix.shape[0] - i)
    if n <= 0:
        return
    l = gain * (1 - max(0, pan))
    r = gain * (1 + min(0, pan))
    mix[i:i + n, 0] += sound[:n] * l
    mix[i:i + n, 1] += sound[:n] * r


def key_tick(pitch=1.0):
    """Soft mechanical keystroke: a click on top of a short low thump."""
    n = int(SR * 0.06)
    noise = rng.standard_normal(n)
    click = highpass(noise, 1800 * pitch) * env_exp(n, 0.004)
    tt = np.arange(n) / SR
    thump = np.sin(2 * np.pi * 150 * pitch * tt) * env_exp(n, 0.012)
    return 0.55 * click + 0.45 * thump


def mouse_down():
    n = int(SR * 0.05)
    noise = rng.standard_normal(n)
    tt = np.arange(n) / SR
    return 0.5 * highpass(noise, 1200) * env_exp(n, 0.005) + 0.6 * np.sin(2 * np.pi * 220 * tt) * env_exp(n, 0.014)


def mouse_up():
    n = int(SR * 0.04)
    noise = rng.standard_normal(n)
    tt = np.arange(n) / SR
    return 0.4 * highpass(noise, 2500) * env_exp(n, 0.004) + 0.3 * np.sin(2 * np.pi * 340 * tt) * env_exp(n, 0.01)


def tab_click():
    """Clean UI click used when the view changes."""
    n = int(SR * 0.09)
    tt = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 880 * tt) * env_exp(n, 0.018) + 0.5 * np.sin(2 * np.pi * 1760 * tt) * env_exp(n, 0.01)
    noise = highpass(rng.standard_normal(n), 2000) * env_exp(n, 0.004)
    return 0.45 * tone + 0.5 * noise


def pop(freq=520):
    n = int(SR * 0.16)
    tt = np.arange(n) / SR
    f = freq * (1 + 0.8 * np.exp(-tt / 0.03))
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) * env_exp(n, 0.045)


def whoosh(length, rising=True, peak=0.5):
    n = int(SR * length)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # sweep a simple lowpass across the noise
    chunks = 24
    size = n // chunks
    for c in range(chunks):
        frac = c / (chunks - 1)
        cutoff = 400 + (3200 * frac if rising else 3200 * (1 - frac))
        seg = noise[c * size:(c + 1) * size if c < chunks - 1 else n]
        out[c * size:c * size + len(seg)] = lowpass(seg, cutoff)
    x = np.linspace(0, 1, n)
    shape = np.sin(np.pi * x) ** 2 if peak == 0.5 else np.where(x < peak, (x / peak) ** 2, ((1 - x) / (1 - peak)) ** 2)
    return out * shape * 2.2


def swell(length):
    n = int(SR * length)
    tt = np.arange(n) / SR
    x = np.linspace(0, 1, n)
    tone = np.sin(2 * np.pi * (220 + 220 * x) * tt) * 0.5 + np.sin(2 * np.pi * (330 + 330 * x) * tt) * 0.3
    return tone * (np.sin(np.pi * x) ** 2)


def chime():
    n = int(SR * 1.8)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for f, g in [(784, 1.0), (1175, 0.55), (1568, 0.35)]:
        out += g * np.sin(2 * np.pi * f * tt) * env_exp(n, 0.55)
    return out


# ---------- timeline (matches oca-demo.html) ----------
# Scene A: paper swishes as documents land
for i in range(7):
    add(whoosh(0.35, True) * 0.12, 0.2 + i * 0.2 + 0.7, 1.0, pan=(i - 3) / 6)

# Scene change clicks (A to B, B to C, C to results)
for t in (4.0, 9.0, 15.0):
    add(tab_click(), t, 0.9)

# Scene B: a pop as each group appears
for i, f in enumerate((440, 520, 620, 740)):
    add(pop(f), 4.7 + i * 0.8 + 0.12, 0.55)

# Scene C: typing "92701", one tick per character
for k in range(1, 6):
    t = 9.9 + (k / 5.0) * 1.2
    add(key_tick(pitch=rng.uniform(0.9, 1.12)), t, rng.uniform(0.6, 0.85))
# click on "Find sites" (down then up)
add(mouse_down(), 11.7, 0.95)
add(mouse_up(), 11.88, 0.8)
# loading bar: soft rising whoosh
add(whoosh(1.9, True) * 0.10, 12.6, 1.0)

# Scene D: cards slide in, pins pop
for i in range(4):
    add(whoosh(0.3, True) * 0.10, 15.5 + i * 0.3 + 0.25, 1.0, pan=-0.4)
for i, f in enumerate((660, 590, 520, 460)):
    add(pop(f), 16.5 + i * 0.3 + 0.2, 0.5, pan=0.4)

# Scene E: select the first site, panel opens, bars fill
add(mouse_down(), 19.2, 0.9)
add(mouse_up(), 19.34, 0.7)
add(tab_click(), 20.1, 0.8)
for i in range(3):
    add(pop(480 + i * 90), 21.2 + i * 0.6 + 0.3, 0.38)
add(tab_click(), 23.2, 0.5)
add(tab_click(), 23.9, 0.5)

# Scene F: map opens, parcels converge, logo moves, letters arrive
add(whoosh(1.0, True) * 0.22, 25.1, 1.0)
add(swell(1.6) * 0.18, 26.2, 1.0)
add(pop(300) * 0.9, 27.6, 0.7)           # parcels meet
add(whoosh(0.9, False) * 0.2, 27.9, 1.0)  # logo slides left
for i in range(3):
    add(pop(560 + i * 110), 28.3 + i * 0.18 + 0.1, 0.55)
add(chime(), 29.15, 0.35)

# ---------- master ----------
peak = np.max(np.abs(mix))
mix = mix / peak * 0.85
mix = mix[: int(SR * DUR)]
out = (mix * 32767).astype("<i2")
path = sys.argv[1] if len(sys.argv) > 1 else "oca-sfx.wav"
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print("wrote", path)
