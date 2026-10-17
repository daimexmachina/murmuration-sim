
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import os

SR = 44100
BPM = 174.0
SPB = 60.0 / BPM          # seconds per beat
BARS = 8
BEATS = BARS * 4
N = int(SR * SPB * BEATS)
rng = np.random.default_rng(1997)
buf = np.zeros(N + SR)

def t_axis(dur):
    return np.arange(int(SR * dur)) / SR

def kick(dur=0.40):
    t = t_axis(dur)
    f = 52 + 110 * np.exp(-t / 0.028)          # pitch envelope
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.115)
    click = rng.standard_normal(t.size) * np.exp(-t / 0.0018) * 0.35
    return body + click

def snare(dur=0.30, tone=185.0, decay=0.11, bright=1.0):
    t = t_axis(dur)
    noise = rng.standard_normal(t.size)
    sos = butter(2, [1100, 7500], btype="band", fs=SR, output="sos")
    noise = sosfilt(sos, noise) * bright
    shell = (np.sin(2 * np.pi * tone * t) + 0.6 * np.sin(2 * np.pi * tone * 1.6 * t))
    return (noise * 0.9 + shell * 0.35) * np.exp(-t / decay)

def hat(dur=0.06, decay=0.017):
    t = t_axis(dur)
    n = rng.standard_normal(t.size)
    sos = butter(4, 6500, btype="high", fs=SR, output="sos")
    return sosfilt(sos, n) * np.exp(-t / decay) * 0.5

def saw(t, f):
    return 2.0 * ((t * f) % 1.0) - 1.0

def reese(dur, f0, detune_cents=14.0, cutoff=340.0, reso=0.85, wobble=True):
    """Two detuned saws + sub, lowpassed with a slow LFO on the cutoff."""
    t = t_axis(dur)
    d = 2 ** (detune_cents / 1200.0)
    x = saw(t, f0 / d) + saw(t, f0 * d) + 0.5 * np.sin(2 * np.pi * f0 * t)
    x /= 2.5
    if wobble:
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t)
        mod = 0.55 + 0.45 * lfo
        sos = butter(2, min(cutoff * 1.8, SR * 0.45), btype="low", fs=SR, output="sos")
        out = sosfilt(sos, x) * mod
    else:
        sos = butter(2, cutoff, btype="low", fs=SR, output="sos")
        out = sosfilt(sos, x)
    # gentle resonance flavour
    sos2 = butter(2, cutoff * 2.2, btype="low", fs=SR, output="sos")
    out = out * reso + sosfilt(sos2, x) * (1 - reso)
    return out * np.exp(-t / (dur * 1.6))

def place(sig, at_beat, gain=1.0):
    start = int(at_beat * SPB * SR)
    end = min(start + sig.size, buf.size)
    if start < buf.size:
        buf[start:end] += sig[: end - start] * gain

K, S, H = kick(), snare(), hat()

# --- two-step DnB skeleton over 8 bars -------------------------------
for bar in range(BARS):
    b = bar * 4
    place(K, b + 0.0, 1.0)          # one
    place(K, b + 2.5, 0.92)         # the "3-and" push
    place(S, b + 1.0, 0.85)         # two
    place(S, b + 3.0, 0.90)         # four
    # 16th hats, accented on the offbeat
    for i in range(8):
        g = 0.55 if i % 2 else 0.32
        place(H, b + i * 0.5, g)

# --- break chopping: ghost snares / rolls ----------------------------
for bar in range(BARS):
    b = bar * 4
    place(snare(0.10, 320, 0.035, 1.2), b + 3.25, 0.42)
    place(snare(0.08, 300, 0.03, 1.1), b + 3.5, 0.30)
    if bar % 2 == 1:
        place(snare(0.06, 360, 0.022, 1.4), b + 3.75, 0.24)
    if bar % 4 == 3:
        for k in range(6):                      # 32nd roll into the drop
            place(snare(0.05, 340 - k * 8, 0.02, 1.4), b + 3.5 + k * 0.125, 0.20 + k * 0.035)

# --- reese bass riff -------------------------------------------------
F1 = 43.65      # F1
RIFF = [(F1, 0.0, 1.5), (F1, 1.5, 0.5), (F1 * 2 ** (3 / 12), 2.0, 1.0),
        (F1 * 2 ** (7 / 12), 3.0, 1.0)]
for bar in range(BARS):
    b = bar * 4
    if bar == 4 or bar == 5:                    # let the drums breathe
        continue
    for note, off, dur in RIFF:
        place(reese(dur * SPB, note, 18 if bar % 2 else 10), b + off, 0.55)

# --- FX: downward noise sweep + riser --------------------------------
sweep_len = 2.0
t = t_axis(sweep_len)
f = np.linspace(6000, 300, t.size)
sw = rng.standard_normal(t.size) * np.sin(2 * np.pi * np.cumsum(f) / SR)
place(sw * np.exp(-t / 0.7) * 0.18, 0.0)

# --- mix -------------------------------------------------------------
mix = buf[:N]
mix /= np.max(np.abs(mix)) / 0.92
mix = np.tanh(mix * 1.15) / np.tanh(1.15)      # tape-ish soft clip
mix *= 0.95

outdir = "/home/daim/workspace/dnb_taste"
os.makedirs(outdir, exist_ok=True)
wav_path = os.path.join(outdir, "taste_174bpm_8bars.wav")
wavfile.write(wav_path, SR, (mix * 32767).astype(np.int16))

dur = mix.size / SR
peak = float(np.max(np.abs(mix)))
rms = float(np.sqrt(np.mean(mix ** 2)))
print(f"WAV: {wav_path}")
print(f"duration={dur:.2f}s  peak={peak:.3f}  rms={rms:.4f}  dBFS(rms)={20*np.log10(rms):.1f}")
