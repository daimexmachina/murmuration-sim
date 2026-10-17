
"""Reese v2: aggressive, filthy, growling. v1 rendered over the identical riff for A/B."""
import numpy as np
from scipy.signal import butter, sosfilt, lfilter, welch
from scipy.io import wavfile
import os, json

SR = 44100
BPM = 174.0
SPB = 60.0 / BPM
OUT = "/home/daim/workspace/dnb_taste"
os.makedirs(OUT, exist_ok=True)

F1, GS1, AS1, C2, DS2, F2 = 43.65, 51.91, 58.27, 65.41, 77.78, 87.31
BARS = 8
BEATS = BARS * 4
N = int(SR * SPB * BEATS)

# ---------------------------------------------------------------- helpers
def sat(x, drive, mode="tanh"):
    if mode == "tanh":
        return np.tanh(x * drive) / np.tanh(drive)
    if mode == "hard":
        return np.clip(x * drive, -1.0, 1.0)
    if mode == "fold":
        return np.sin(x * drive)
    if mode == "asym":
        y = x * drive
        return np.where(y > 0, np.tanh(y), np.tanh(y * 1.9) * 0.88)
    raise ValueError(mode)

def bitcrush(x, bits=7, down=3):
    q = 2 ** (bits - 1)
    y = np.round(np.clip(x, -1, 1) * q) / q
    if down > 1:
        y = y[(np.arange(y.size) // down) * down]
    return y

def rbj_low(fc, Q):
    fc = float(np.clip(fc, 25.0, SR * 0.45))
    w0 = 2 * np.pi * fc / SR
    al = np.sin(w0) / (2 * Q)
    cw = np.cos(w0)
    b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
    a = np.array([1 + al, -2 * cw, 1 - al])
    return b / a[0], a / a[0]

def sweep_lowpass(x, cutoffs, Q=11.0, block=256):
    """Resonant lowpass whose cutoff moves per block - this is the growl engine."""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    x = np.ascontiguousarray(x)
    for i in range(0, x.size, block):
        seg = x[i:i + block]
        b, a = rbj_low(cutoffs[min(i + block // 2, cutoffs.size - 1)], Q)
        out, zi = lfilter(b, a, seg, zi=zi)
        y[i:i + block] = out
    return y

def formant_bank(x, fs_, gains=(1.0, 0.62, 0.34)):
    out = np.zeros_like(x)
    for f, g in zip(fs_, gains):
        sos = butter(2, [f * 0.86, f * 1.16], "band", fs=SR, output="sos")
        out += sosfilt(sos, x) * g
    return out

VOW = {"ah": (730, 1090, 2440), "ee": (270, 2290, 3010),
       "oh": (570, 840, 2410), "oo": (300, 870, 2240)}

def norm(x, target=1.0):
    p = np.max(np.abs(x))
    return x * (target / p) if p > 1e-12 else x

def gate_env(n, dur, atk=0.004, rel=0.045, drop=0.22):
    t = np.arange(n) / SR
    e = np.clip(t / atk, 0, 1) * np.clip((dur - t) / rel, 0, 1)
    return e * (1.0 - drop * np.clip(t / max(dur, 1e-6), 0, 1))

def multiband_filth(x):
    lo  = sosfilt(butter(4, 100, "low",  fs=SR, output="sos"), x)
    mid = sosfilt(butter(4, [100, 1400], "band", fs=SR, output="sos"), x)
    hi  = sosfilt(butter(4, 1400, "high", fs=SR, output="sos"), x)
    lo  = sat(lo, 3.5)
    mid = sat(mid, 7.0, "hard") * 0.72 + sat(mid, 4.2, "fold") * 0.48
    hi  = bitcrush(sat(hi, 6.5, "asym"), bits=7, down=3) * 0.80
    return lo + mid + hi

# ---------------------------------------------------------------- the bass
def reese_filthy(dur, f0, t0, seed=7):
    n = int(SR * dur)
    t = t0 + np.arange(n) / SR
    fmid = f0 * 2.0
    # pitch drop at onset ("yow"), then settle
    fenv = f0 * (1.0 + 0.055 * np.exp(-(np.arange(n) / SR) / 0.045))
    phase = np.cumsum(fenv) / SR                      # cycles at nominal f0
    fmid_env = phase * 2.0

    o = np.zeros(n)
    for cents in (-31, -16, -6, 6, 16, 31):           # 6-voice detuned bank
        o += 2.0 * ((phase * 2.0 * 2 ** (cents / 1200.0)) % 1.0) - 1.0
    o += 0.55 * (2.0 * (phase % 1.0) - 1.0)           # centre octave-down body
    # hard sync 1.5x -> metallic snarl
    m = np.floor(phase * 1.5)
    o += 0.62 * (2.0 * ((phase * 1.003 - (1.003 / 1.5) * m) % 1.0) - 1.0)
    # inharmonic FM -> scream
    o += 0.42 * (2.0 * ((fmid_env + 1.4 * np.sin(2 * np.pi * fmid * 3.07 * t)) % 1.0) - 1.0)
    o = norm(o / 6.5)

    o = sat(o, 2.0)
    a = 0.5 + 0.5 * np.sin(2 * np.pi * 2.9 * t)       # quarter-note vowel morph
    o = norm(formant_bank(o, VOW["oh"]) * a + formant_bank(o, VOW["ee"]) * (1 - a))
    o = sat(o, 1.6)

    # resonant growl sweep: 8th-note yoy under a slow shape
    cut = 220.0 * np.exp(1.9 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.8 * t - 1.0)))
    cut *= 0.72 + 0.48 * np.sin(2 * np.pi * 0.45 * t)
    o = sweep_lowpass(o, np.clip(cut, 120, 3200), Q=11.0)

    D = int(SR / fmid)                                # resonant comb
    b = np.zeros(D + 1); b[0] = 1.0
    aa = np.zeros(D + 1); aa[0] = 1.0; aa[-1] = -0.55
    o = lfilter(b, aa, o)
    o = norm(o)

    o = o * 0.78 + (o * np.sin(2 * np.pi * fmid * 1.414 * t)) * 0.22   # ring mod
    o = multiband_filth(o)
    o = sosfilt(butter(2, 95, "high", fs=SR, output="sos"), o)         # clear the sub
    o = norm(o)

    sub = np.tanh(np.sin(2 * np.pi * np.cumsum(fenv) / SR) * 1.9) / np.tanh(1.9)
    sub = sosfilt(butter(4, 155, "low", fs=SR, output="sos"), sub)
    sub = norm(sub)

    return (sub * 0.92 + o * 1.06) * gate_env(n, dur), sub, o

def reese_v1(dur, f0, t0):
    """The original: two detuned saws + sub, LP 340. Kept for honest A/B."""
    n = int(SR * dur)
    t = t0 + np.arange(n) / SR
    ph = np.cumsum(np.full(n, f0)) / SR
    d = 2 ** (10.0 / 1200.0)
    x = (2.0 * ((ph * 2.0 * d) % 1.0) - 1.0) + (2.0 * ((ph * 2.0 / d) % 1.0) - 1.0)
    x += 0.5 * np.sin(2 * np.pi * f0 * t)
    x = norm(x / 2.5)
    x = sosfilt(butter(2, 340, "low", fs=SR, output="sos"), x)
    return norm(x) * gate_env(n, dur)

RIFF = []                                              # (beat, dur_beats, freq)
pairs = [
    [(0.0, 3.0, F1), (3.5, 0.5, F1), (4.0, 2.0, GS1), (6.0, 2.0, C2)],
    [(0.0, 3.0, F1), (3.5, 0.5, F1), (4.0, 2.0, GS1), (6.0, 2.0, C2)],
    [(0.0, 3.0, F1), (3.5, 0.5, F1), (4.0, 2.0, GS1), (6.0, 2.0, DS2)],
    [(0.0, 3.5, F1), (4.0, 1.0, GS1), (5.0, 1.0, AS1), (6.0, 2.0, F2)],
]
for pi, p in enumerate(pairs):
    for off, dur, f in p:
        RIFF.append((pi * 8 + off, dur, f))

def render_bass(which):
    buf = np.zeros(N)
    for start_beat, dur_beats, f in RIFF:
        dur = dur_beats * SPB
        t0 = start_beat * SPB
        if which == "v2":
            sig, _, _ = reese_filthy(dur, f, t0)
        else:
            sig = reese_v1(dur, f, t0)
        i = int(start_beat * SPB * SR)
        e = min(i + sig.size, N)
        buf[i:e] += sig[: e - i]
    return norm(buf, 0.98)

# ---------------------------------------------------------------- drums
rng = np.random.default_rng(1997)
def t_axis(d): return np.arange(int(SR * d)) / SR
def kick(dur=0.40):
    t = t_axis(dur); f = 52 + 110 * np.exp(-t / 0.028)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.115) \
           + rng.standard_normal(t.size) * np.exp(-t / 0.0018) * 0.35
def snare(dur=0.30, tone=185.0, decay=0.11, bright=1.0):
    t = t_axis(dur)
    nz = sosfilt(butter(2, [1100, 7500], "band", fs=SR, output="sos"), rng.standard_normal(t.size)) * bright
    sh = np.sin(2 * np.pi * tone * t) + 0.6 * np.sin(2 * np.pi * tone * 1.6 * t)
    return (nz * 0.9 + sh * 0.35) * np.exp(-t / decay)
def hat(dur=0.06, decay=0.017):
    t = t_axis(dur)
    return sosfilt(butter(4, 6500, "high", fs=SR, output="sos"),
                   rng.standard_normal(t.size)) * np.exp(-t / decay) * 0.5

def render_drums():
    buf = np.zeros(N + SR)
    K, S, H = kick(), snare(), hat()
    def put(sig, beat, g):
        i = int(beat * SPB * SR); e = min(i + sig.size, buf.size)
        if i < buf.size: buf[i:e] += sig[: e - i] * g
    for bar in range(BARS):
        b = bar * 4
        put(K, b, 1.0); put(K, b + 2.5, 0.92)
        put(S, b + 1, 0.85); put(S, b + 3, 0.90)
        for i in range(8):
            put(H, b + i * 0.5, 0.55 if i % 2 else 0.32)
        put(snare(0.10, 320, 0.035, 1.2), b + 3.25, 0.42)
        put(snare(0.08, 300, 0.03, 1.1), b + 3.5, 0.30)
        if bar % 2 == 1:
            put(snare(0.06, 360, 0.022, 1.4), b + 3.75, 0.24)
        if bar % 4 == 3:
            for k in range(6):
                put(snare(0.05, 340 - k * 8, 0.02, 1.4), b + 3.5 + k * 0.125, 0.20 + k * 0.035)
    return norm(buf[:N], 0.95)

def master(x):
    x = sosfilt(butter(2, 30, "high", fs=SR, output="sos"), x)
    x = np.tanh(x * 1.25) / np.tanh(1.25)
    return norm(x, 0.95)

def metrics(x):
    f, P = welch(x, fs=SR, nperseg=8192)
    P = P + 1e-20
    cen = float(np.sum(f * P) / np.sum(P))
    flat = float(np.exp(np.mean(np.log(P))) / np.mean(P))
    c = np.cumsum(P) / np.sum(P)
    roll = float(f[np.searchsorted(c, 0.95)])
    crest = float(np.max(np.abs(x)) / np.sqrt(np.mean(x ** 2)))
    def band(a, b):
        s = (f >= a) & (f < b); return float(np.sum(P[s]))
    tot = float(np.sum(P))
    return {"centroid_hz": round(cen, 1), "rolloff95_hz": round(roll, 1),
            "flatness": round(flat, 5), "crest": round(crest, 2),
            "sub_30_90_pct": round(100 * band(30, 90) / tot, 1),
            "mid_300_1500_pct": round(100 * band(300, 1500) / tot, 1),
            "high_1500_8000_pct": round(100 * band(1500, 8000) / tot, 1),
            "rms_dbfs": round(20 * np.log10(np.sqrt(np.mean(x ** 2))), 1)}

rep = {}
for which, name in (("v1", "reese_solo_v1"), ("v2", "reese_solo_v2")):
    bass = render_bass(which)
    wavfile.write(f"{OUT}/{name}.wav", SR, (bass * 32767).astype(np.int16))
    rep[name] = metrics(bass)

drums = render_drums()
drop = master(drums * 0.85 + render_bass("v2") * 0.95)
wavfile.write(f"{OUT}/drop_v2_full.wav", SR, (drop * 32767).astype(np.int16))
rep["drop_v2_full"] = metrics(drop)

with open(f"{OUT}/metrics.json", "w") as fh:
    json.dump(rep, fh, indent=2)
print(json.dumps(rep, indent=2))
