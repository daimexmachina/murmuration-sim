
"""Reese v3: two-stage distortion + resonant peak sweep + scream layer."""
import numpy as np
from scipy.signal import butter, sosfilt, lfilter, welch
from scipy.io import wavfile
import os, json

SR, BPM = 44100, 174.0
SPB = 60.0 / BPM
OUT = "/home/daim/workspace/dnb_taste"
F1, GS1, AS1, C2, DS2, F2 = 43.65, 51.91, 58.27, 65.41, 77.78, 87.31
BARS, BEATS = 8, 32
N = int(SR * SPB * BEATS)

def sat(x, drive, mode="tanh"):
    if mode == "tanh":  return np.tanh(x * drive) / np.tanh(drive)
    if mode == "hard":  return np.clip(x * drive, -1.0, 1.0)
    if mode == "fold":  return np.sin(x * drive)
    if mode == "asym":
        y = x * drive
        return np.where(y > 0, np.tanh(y), np.tanh(y * 1.9) * 0.88)
    raise ValueError(mode)

def bitcrush(x, bits=6, down=4):
    q = 2 ** (bits - 1)
    y = np.round(np.clip(x, -1, 1) * q) / q
    return y[(np.arange(y.size) // down) * down] if down > 1 else y

def rbj_low(fc, Q):
    fc = float(np.clip(fc, 25.0, SR * 0.45)); w0 = 2 * np.pi * fc / SR
    al = np.sin(w0) / (2 * Q); cw = np.cos(w0)
    b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2]); a = np.array([1 + al, -2 * cw, 1 - al])
    return b / a[0], a / a[0]

def rbj_peak(fc, Q, gain_db):
    fc = float(np.clip(fc, 25.0, SR * 0.45)); A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * fc / SR; al = np.sin(w0) / (2 * Q); cw = np.cos(w0)
    b = np.array([1 + al * A, -2 * cw, 1 - al * A]); a = np.array([1 + al / A, -2 * cw, 1 - al / A])
    return b / a[0], a / a[0]

def sweep(x, param, coeff_fn, block=256):
    """Block-wise biquad whose coefficients follow a control signal."""
    y = np.zeros_like(x); zi = np.zeros(2); x = np.ascontiguousarray(x)
    for i in range(0, x.size, block):
        b, a = coeff_fn(param[min(i + block // 2, param.size - 1)])
        out, zi = lfilter(b, a, x[i:i + block], zi=zi)
        y[i:i + block] = out
    return y

def formant_bank(x, fs_, gains=(1.0, 0.62, 0.34)):
    out = np.zeros_like(x)
    for f, g in zip(fs_, gains):
        out += sosfilt(butter(2, [f * 0.86, f * 1.16], "band", fs=SR, output="sos"), x) * g
    return out
VOW = {"ah": (730, 1090, 2440), "ee": (270, 2290, 3010), "oh": (570, 840, 2410)}

def norm(x, t=1.0):
    p = np.max(np.abs(x)); return x * (t / p) if p > 1e-12 else x

def gate_env(n, dur, atk=0.004, rel=0.045, drop=0.20):
    t = np.arange(n) / SR
    return (np.clip(t / atk, 0, 1) * np.clip((dur - t) / rel, 0, 1)
            * (1.0 - drop * np.clip(t / max(dur, 1e-6), 0, 1)))

def tri(t, rate):                      # snappier than a sine
    return (2.0 / np.pi) * np.arcsin(np.sin(2 * np.pi * rate * t))

# ------------------------------------------------------------- v3 bass
def reese_v3(dur, f0, t0):
    n = int(SR * dur); t = t0 + np.arange(n) / SR
    fmid = f0 * 2.0
    fenv = f0 * (1.0 + 0.055 * np.exp(-(np.arange(n) / SR) / 0.045))
    phase = np.cumsum(fenv) / SR

    o = np.zeros(n)
    for c in (-31, -16, -6, 6, 16, 31):                       # detuned saws
        o += 2.0 * ((phase * 2.0 * 2 ** (c / 1200.0)) % 1.0) - 1.0
    o += 0.6 * np.sign(np.sin(2 * np.pi * phase * 2.0))        # square voice (odd harmonics)
    o += 0.55 * (2.0 * (phase % 1.0) - 1.0)                    # octave-down body
    m = np.floor(phase * 1.5)                                  # hard sync snarl
    o += 0.62 * (2.0 * ((phase * 1.003 - (1.003 / 1.5) * m) % 1.0) - 1.0)
    o += 0.45 * (2.0 * ((phase * 2.0 + 1.4 * np.sin(2 * np.pi * fmid * 3.07 * t)) % 1.0) - 1.0)
    o = norm(o / 7.0)

    # stage 1: destroy, then sweep, then destroy again
    o = sat(o, 4.5, "fold")
    a = 0.5 + 0.5 * np.sin(2 * np.pi * 2.9 * t)
    o = norm(formant_bank(o, VOW["oh"]) * a + formant_bank(o, VOW["ee"]) * (1 - a))

    cut1 = 900.0 * np.exp(1.05 * tri(t, 5.8)) * (0.75 + 0.35 * tri(t, 0.45))
    cut1 = np.clip(cut1, 260.0, 2600.0)
    o = sweep(o, cut1, lambda f: rbj_low(f, 9.0))
    o = norm(o)
    o = sweep(o, cut1 * 1.25, lambda f: rbj_peak(f, 6.0, 12.0))   # growl formant
    o = norm(o)

    o = sat(o, 6.0, "hard") * 0.62 + sat(o, 3.5, "asym") * 0.55
    o = norm(o)
    cut2 = 1200.0 * np.exp(0.95 * tri(t, 8.7)) * (0.8 + 0.3 * tri(t, 0.30))
    o = sweep(o, np.clip(cut2, 420.0, 3600.0), lambda f: rbj_low(f, 6.0))
    o = norm(o)

    D = int(SR / fmid)                                          # resonant comb
    b = np.zeros(D + 1); b[0] = 1.0
    aa = np.zeros(D + 1); aa[0] = 1.0; aa[-1] = -0.52
    o = norm(lfilter(b, aa, o))
    o = o * 0.80 + (o * np.sin(2 * np.pi * fmid * 1.414 * t)) * 0.20

    lo  = sat(sosfilt(butter(4, 140, "low", fs=SR, output="sos"), o), 3.0)
    mdp = sosfilt(butter(4, [140, 1600], "band", fs=SR, output="sos"), o)
    mid = sat(mdp, 9.0, "hard") * 0.7 + sat(mdp, 5.0, "fold") * 0.55
    hi  = bitcrush(sat(sosfilt(butter(4, 1600, "high", fs=SR, output="sos"), o), 7.0, "asym"),
                   bits=6, down=4) * 0.85
    growl = norm(lo * 0.5 + mid * 1.0 + hi * 0.55)

    scream = sosfilt(butter(4, [2000, 6500], "band", fs=SR, output="sos"),
                     sat(norm(o), 8.0, "fold")) * 0.22
    growl = norm(growl + scream)
    growl = norm(sosfilt(butter(2, 90, "high", fs=SR, output="sos"), growl))

    sub = np.tanh(np.sin(2 * np.pi * np.cumsum(fenv) / SR) * 1.9) / np.tanh(1.9)
    sub = norm(sosfilt(butter(4, 140, "low", fs=SR, output="sos"), sub))
    return (sub * 0.62 + growl * 1.35) * gate_env(n, dur)

def reese_v1(dur, f0, t0):
    n = int(SR * dur); t = t0 + np.arange(n) / SR
    ph = np.cumsum(np.full(n, f0)) / SR; d = 2 ** (10.0 / 1200.0)
    x = (2.0 * ((ph * 2.0 * d) % 1.0) - 1.0) + (2.0 * ((ph * 2.0 / d) % 1.0) - 1.0)
    x += 0.5 * np.sin(2 * np.pi * f0 * t)
    x = norm(sosfilt(butter(2, 340, "low", fs=SR, output="sos"), norm(x / 2.5)))
    return x * gate_env(n, dur)

RIFF = []
pairs = [
    [(0.0, 3.0, F1), (3.5, 0.5, F1), (4.0, 2.0, GS1), (6.0, 2.0, C2)],
    [(0.0, 3.0, F1), (3.5, 0.5, F1), (4.0, 2.0, GS1), (6.0, 2.0, C2)],
    [(0.0, 3.0, F1), (3.5, 0.5, F1), (4.0, 2.0, GS1), (6.0, 2.0, DS2)],
    [(0.0, 3.5, F1), (4.0, 1.0, GS1), (5.0, 1.0, AS1), (6.0, 2.0, F2)],
]
for pi, p in enumerate(pairs):
    RIFF += [(pi * 8 + off, dur, f) for off, dur, f in p]

def render_bass(fn):
    buf = np.zeros(N)
    for sb, db, f in RIFF:
        sig = fn(db * SPB, f, sb * SPB)
        i = int(sb * SPB * SR); e = min(i + sig.size, N)
        buf[i:e] += sig[: e - i]
    return norm(buf, 0.98)

rng = np.random.default_rng(1997)
def t_axis(d): return np.arange(int(SR * d)) / SR
def kick(dur=0.40):
    t = t_axis(dur); f = 52 + 110 * np.exp(-t / 0.028)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.115) \
           + rng.standard_normal(t.size) * np.exp(-t / 0.0018) * 0.35
def snare(dur=0.30, tone=185.0, decay=0.11, bright=1.0):
    t = t_axis(dur)
    nz = sosfilt(butter(2, [1100, 7500], "band", fs=SR, output="sos"), rng.standard_normal(t.size)) * bright
    return (nz * 0.9 + (np.sin(2 * np.pi * tone * t) + 0.6 * np.sin(2 * np.pi * tone * 1.6 * t)) * 0.35) * np.exp(-t / decay)
def hat(dur=0.06, decay=0.017):
    t = t_axis(dur)
    return sosfilt(butter(4, 6500, "high", fs=SR, output="sos"), rng.standard_normal(t.size)) * np.exp(-t / decay) * 0.5
def render_drums():
    buf = np.zeros(N + SR); K, S, H = kick(), snare(), hat()
    def put(s, beat, g):
        i = int(beat * SPB * SR); e = min(i + s.size, buf.size)
        if i < buf.size: buf[i:e] += s[: e - i] * g
    for bar in range(BARS):
        b = bar * 4
        put(K, b, 1.0); put(K, b + 2.5, 0.92); put(S, b + 1, 0.85); put(S, b + 3, 0.90)
        for i in range(8): put(H, b + i * 0.5, 0.55 if i % 2 else 0.32)
        put(snare(0.10, 320, 0.035, 1.2), b + 3.25, 0.42); put(snare(0.08, 300, 0.03, 1.1), b + 3.5, 0.30)
        if bar % 2 == 1: put(snare(0.06, 360, 0.022, 1.4), b + 3.75, 0.24)
        if bar % 4 == 3:
            for k in range(6): put(snare(0.05, 340 - k * 8, 0.02, 1.4), b + 3.5 + k * 0.125, 0.20 + k * 0.035)
    return norm(buf[:N], 0.95)

def master(x):
    x = sosfilt(butter(2, 30, "high", fs=SR, output="sos"), x)
    return norm(np.tanh(x * 1.25) / np.tanh(1.25), 0.95)

def pitch_clarity(x, fmin=35, fmax=120):
    x = x - x.mean(); n = x.size
    ac = np.fft.irfft(np.abs(np.fft.rfft(x, 2 * n)) ** 2)[:n]; ac /= ac[0]
    lo, hi = int(SR / fmax), int(SR / fmin)
    seg = ac[lo:hi]; k = int(np.argmax(seg))
    return round(float(seg[k]), 3), round(float(SR / (lo + k)), 1)

def metrics(x):
    f, P = welch(x, fs=SR, nperseg=8192); P = P + 1e-20
    tot = float(np.sum(P)); c = np.cumsum(P) / tot
    def band(a, b):
        s = (f >= a) & (f < b); return round(100 * float(np.sum(P[s])) / tot, 1)
    pc, pf = pitch_clarity(x)
    return {"centroid_hz": round(float(np.sum(f * P) / tot), 1),
            "rolloff95_hz": round(float(f[np.searchsorted(c, 0.95)]), 1),
            "flatness": round(float(np.exp(np.mean(np.log(P))) / np.mean(P)), 5),
            "crest": round(float(np.max(np.abs(x)) / np.sqrt(np.mean(x ** 2))), 2),
            "sub_30_90_pct": band(30, 90), "low_90_300_pct": band(90, 300),
            "mid_300_1500_pct": band(300, 1500), "high_1500_8000_pct": band(1500, 8000),
            "pitch_clarity": pc, "pitch_hz": pf,
            "rms_dbfs": round(20 * np.log10(np.sqrt(np.mean(x ** 2))), 1)}

rep = {}
for tag, fn, name in (("v1", reese_v1, "reese_solo_v1"),
                      ("v3", reese_v3, "reese_solo_v3")):
    b = render_bass(fn)
    wavfile.write(f"{OUT}/{name}.wav", SR, (b * 32767).astype(np.int16))
    rep[name] = metrics(b)

drop = master(render_drums() * 0.85 + render_bass(reese_v3) * 0.98)
wavfile.write(f"{OUT}/drop_v3_full.wav", SR, (drop * 32767).astype(np.int16))
rep["drop_v3_full"] = metrics(drop)

with open(f"{OUT}/metrics_v3.json", "w") as fh: json.dump(rep, fh, indent=2)
print(json.dumps(rep, indent=2))
