#!/usr/bin/env python3
"""Synthesizes the sound design for the OCA demo video and writes a stereo WAV.

Direction: minimal, warm and spacious. A soft pad moves through one chord progression
(dark at the start, bright at the logo reveal). Soft piano-like notes in the same key mark
what happens on screen. Typing sounds like a keyboard, clicks stay clean, and a very quiet
room tone keeps everything from feeling pasted on. No noise whooshes.

Every event is timed to oca-demo.html. Needs only numpy.
Usage: python3 make_audio.py out.wav
Then mux with: ffmpeg -i oca-demo.mp4 -i out.wav -c:v copy -c:a aac -b:a 192k -shortest oca-demo-sfx.mp4
"""
import sys
import wave
import numpy as np

SR = 44100
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
music = np.zeros((N + SR * 3, 2))
sfx = np.zeros((N + SR * 3, 2))
room = np.zeros(N)


def tvec(n):
    return np.arange(n) / SR


def fft_shape(x, lo=None, hi=None):
    """Smooth band limiting with FFT (no ringing from brick-wall edges)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + np.exp(-(f - lo) / (lo * 0.18)))
    if hi:
        m *= 1 / (1 + np.exp((f - hi) / (hi * 0.18)))
    return np.fft.irfft(X * m, len(x))


def place(buf, sound, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0:
        return
    n = min(len(sound), buf.shape[0] - i)
    if n <= 0:
        return
    l = gain * (1 - max(0.0, pan))
    r = gain * (1 + min(0.0, pan))
    buf[i:i + n, 0] += sound[:n] * l
    buf[i:i + n, 1] += sound[:n] * r


# ---------------- instruments ----------------
def piano(freq, dur=2.2, vel=1.0):
    """Soft electric-piano / mallet tone: gentle FM, quick bloom, long warm decay."""
    n = int(SR * dur)
    tt = tvec(n)
    idx = 1.1 * np.exp(-tt / 0.10)
    s = np.sin(2 * np.pi * freq * tt + idx * np.sin(2 * np.pi * freq * tt))
    s += 0.28 * np.sin(2 * np.pi * 2 * freq * tt) * np.exp(-tt / 0.35)
    s += 0.10 * np.sin(2 * np.pi * 3 * freq * tt) * np.exp(-tt / 0.2)
    env = (1 - np.exp(-tt / 0.006)) * np.exp(-tt / 0.9)
    out = s * env * vel
    fade = np.clip((dur - tt) / 0.3, 0, 1)
    return out * fade


def sub_thump(freq=58, dur=0.9, vel=1.0):
    n = int(SR * dur)
    tt = tvec(n)
    f = freq * (1 + 0.6 * np.exp(-tt / 0.05))
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-tt / 0.004)) * np.exp(-tt / 0.22)
    return np.sin(ph) * env * vel


def soft_tap(freq=170, vel=1.0):
    """Muted wooden tap, like a fingertip on a desk."""
    n = int(SR * 0.12)
    tt = tvec(n)
    return np.sin(2 * np.pi * freq * tt) * np.exp(-tt / 0.02) * vel


def key_thock(pitch=1.0, vel=1.0):
    """Keyboard keystroke: body thock, small bottom-out tick, light key release."""
    n = int(SR * 0.16)
    tt = tvec(n)
    body = np.sin(2 * np.pi * 190 * pitch * tt) * np.exp(-tt / 0.020)
    body += 0.45 * np.sin(2 * np.pi * 420 * pitch * tt) * np.exp(-tt / 0.012)
    tick1 = fft_shape(rng.standard_normal(n), 1800, 6500) * np.exp(-tt / 0.0028)
    tick2 = np.roll(fft_shape(rng.standard_normal(n), 1500, 5000) * np.exp(-tt / 0.0025), int(SR * 0.006))
    release = np.roll(fft_shape(rng.standard_normal(n), 2500, 7000) * np.exp(-tt / 0.0022), int(SR * 0.085)) * 0.22
    return (0.55 * body + 0.28 * tick1 + 0.18 * tick2 + release) * vel


def mouse_down():
    n = int(SR * 0.05)
    tt = tvec(n)
    noise = fft_shape(rng.standard_normal(n), 1200, 8000)
    return 0.5 * noise * np.exp(-tt / 0.005) + 0.6 * np.sin(2 * np.pi * 220 * tt) * np.exp(-tt / 0.014)


def mouse_up():
    n = int(SR * 0.04)
    tt = tvec(n)
    noise = fft_shape(rng.standard_normal(n), 2500, 9000)
    return 0.4 * noise * np.exp(-tt / 0.004) + 0.3 * np.sin(2 * np.pi * 340 * tt) * np.exp(-tt / 0.01)


def tab_click():
    n = int(SR * 0.09)
    tt = tvec(n)
    tone = np.sin(2 * np.pi * 880 * tt) * np.exp(-tt / 0.018) + 0.5 * np.sin(2 * np.pi * 1760 * tt) * np.exp(-tt / 0.01)
    noise = fft_shape(rng.standard_normal(n), 2000, 9000) * np.exp(-tt / 0.004)
    return 0.45 * tone + 0.5 * noise


def riser(length, f0, f1, vel=1.0):
    """Smooth pitched swell, no noise."""
    n = int(SR * length)
    tt = tvec(n)
    x = np.linspace(0, 1, n)
    f = f0 * (f1 / f0) ** x
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    return s * (x ** 2.2) * np.minimum(1, (1 - x) / 0.06 + 0.0) * vel


# ---------------- music: warm pad ----------------
def pad_voice(freq, length, t_attack, t_release):
    n = int(SR * length)
    tt = tvec(n)
    s = np.zeros(n)
    for det in (0.997, 1.0, 1.003):
        ph = 2 * np.pi * freq * det * tt
        s += np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    s /= 3
    a = np.clip(tt / t_attack, 0, 1)
    r = np.clip((length - tt) / t_release, 0, 1)
    env = (a * a * (3 - 2 * a)) * (r * r * (3 - 2 * r))
    lfo = 1 + 0.12 * np.sin(2 * np.pi * 0.17 * tt + freq)
    return s * env * lfo


AM7 = [110.0, 220.0, 329.63, 392.0, 523.25]
FMAJ7 = [87.31, 174.61, 261.63, 329.63, 440.0]
CMAJ7 = [65.41, 130.81, 196.0, 329.63, 493.88]
G6 = [98.0, 196.0, 246.94, 293.66, 329.63]
CMAJ9 = [65.41, 130.81, 196.0, 329.63, 493.88, 587.33]
prog = [(0.0, 4.0, AM7), (4.0, 9.0, FMAJ7), (9.0, 15.0, CMAJ7), (15.0, 20.0, G6),
        (20.0, 25.0, AM7), (25.0, 27.6, FMAJ7), (27.6, 30.0, CMAJ9)]
for t0, t1, chord in prog:
    start = max(0.0, t0 - 0.9)
    length = (t1 + 1.1) - start
    for f in chord:
        v = pad_voice(f, length, 1.1 if t0 > 0 else 0.9, 1.3)
        place(music, v, start, 0.030, pan=0.0)

# ---------------- melody notes (C major pentatonic) ----------------
C4, D4, E4, G4, A4 = 261.63, 293.66, 329.63, 392.0, 440.0
C5, D5, E5, G5, A5 = 523.25, 587.33, 659.25, 783.99, 880.0
C6, D6, E6, G6n, A6 = 1046.5, 1174.66, 1318.5, 1568.0, 1760.0
B5 = 987.77


def n(freq, t, vel=0.5, dur=2.0, pan=0.0):
    place(music, piano(freq, dur), t, vel * 0.5, pan)


# A: pensive opening, two sparse notes
n(A4, 0.6, 0.55, 2.4)
n(E4, 2.0, 0.45, 2.4)

# B: four groups arrive, rising line
for i, f in enumerate((E5, G5, A5, C6)):
    n(f, 4.75 + i * 0.8, 0.5, 2.0, pan=-0.3 + i * 0.2)

# C: typing is quiet underneath, confirm after the click, loading arpeggio
for i, f in enumerate((C5, E5, G5, A5, C6, A5, G5, E5)):
    n(f, 12.65 + i * 0.22, 0.28, 1.4)
n(G5, 14.45, 0.45, 1.8)
n(C6, 14.6, 0.45, 2.2)

# D: cards land with soft low notes, pins add bright ones
for i, f in enumerate((E5, D5, C5, A4)):
    n(f, 15.6 + i * 0.3, 0.38, 1.6, pan=-0.35)
for i, f in enumerate((G5, A5, C6, D6)):
    n(f, 16.6 + i * 0.3, 0.34, 1.6, pan=0.35)

# E: panel opens on a soft chord, three bars fill with rising notes
for f in (C5, E5, G5):
    n(f, 20.15, 0.32, 2.2)
for i, f in enumerate((E5, G5, A5)):
    n(f, 21.45 + i * 0.6, 0.42, 1.8, pan=0.1 * i)
n(C6, 23.25, 0.25, 1.8)
n(E6, 23.95, 0.25, 1.8)

# F: building arpeggio, then reveal
for i, f in enumerate((C5, E5, G5, B5, C6, E6)):
    n(f, 26.2 + i * 0.22, 0.30 + 0.05 * i, 1.6, pan=-0.3 + i * 0.12)
# reveal chord when the parcels meet
for f in (C5, E5, G5, C6):
    n(f, 27.62, 0.5, 3.0)
# letters arrive
for i, f in enumerate((G5, C6, E6)):
    n(f, 28.35 + i * 0.18, 0.4, 2.2, pan=-0.2 + i * 0.2)
# final resolved chord with the tagline
for f in (C5, E5, G5, B5, D6):
    n(f, 29.2, 0.45, 3.0)

# ---------------- sound effects ----------------
# soft low hit on each scene change, with a clean click
for t in (4.0, 9.0, 15.0):
    place(sfx, tab_click(), t, 0.55)
    place(sfx, sub_thump(70, 0.35, 1.0), t, 0.28)

# typing 92701: five keys, each a little different
for k in range(1, 6):
    t = 9.9 + (k / 5.0) * 1.2
    place(sfx, key_thock(pitch=rng.uniform(0.88, 1.15), vel=1.0), t, rng.uniform(0.7, 0.95),
          pan=rng.uniform(-0.08, 0.08))

# Find sites click
place(sfx, mouse_down(), 11.7, 0.9)
place(sfx, mouse_up(), 11.88, 0.7)

# select first site, then panel details
place(sfx, mouse_down(), 19.2, 0.85)
place(sfx, mouse_up(), 19.34, 0.65)
place(sfx, tab_click(), 20.1, 0.45)
place(sfx, tab_click(), 23.2, 0.30)
place(sfx, tab_click(), 23.9, 0.30)

# map opens, parcels move together, impact on meeting
place(sfx, riser(1.4, 160, 640, 1.0), 25.15, 0.07)
place(sfx, riser(1.5, 130, 520, 1.0), 26.2, 0.08)
place(sfx, sub_thump(52, 1.4, 1.0), 27.6, 0.38)

# ---------------- room tone ----------------
noise = rng.standard_normal(N)
room = fft_shape(noise, 70, 900)
room *= 1 + 0.25 * np.sin(2 * np.pi * 0.11 * tvec(N))
room /= np.max(np.abs(room))
fade = np.clip(tvec(N) / 0.8, 0, 1) * np.clip((DUR - tvec(N)) / 0.8, 0, 1)
room *= fade

# ---------------- master ----------------
mus = music[:N]
fx = sfx[:N]
mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.42
fx = fx / (np.max(np.abs(fx)) + 1e-9) * 0.55
bed = np.stack([room, np.roll(room, 331)], axis=1) * 0.018
mix = mus + fx + bed
mix *= np.clip(tvec(N) / 0.4, 0, 1)[:, None] * np.clip((DUR - tvec(N)) / 0.7, 0, 1)[:, None]
mix = np.tanh(mix * 1.4) / np.tanh(1.4)  # gentle soft limiting
mix = mix / np.max(np.abs(mix)) * 0.89
out = (mix * 32767).astype("<i2")
path = sys.argv[1] if len(sys.argv) > 1 else "oca-sfx.wav"
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print("wrote", path)
