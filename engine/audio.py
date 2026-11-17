"""Voice (Kokoro TTS, local), original procedural synthwave music, and SFX."""
import os, re, hashlib
import numpy as np
import soundfile as sf

SR = 24000
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "..", "build", "tts_cache")

# pronunciation fixes for the Spanish voice (display text stays untouched)
PRON = [
    (r"\bGTA\s*(6|VI)\b", "ge te a seis"), (r"\bGTA\s*(5|V)\b", "ge te a cinco"), (r"\bGTA\s*(4|IV)\b", "ge te a cuatro"),
    (r"\bGTA Online\b", "ge te a onlain"), (r"\bGTA\+", "ge te a plus"), (r"\bGTA\b", "ge te a"),
    (r"\bPS5 Pro\b", "PlayStation cinco Pro"), (r"\bPS5\b", "PlayStation cinco"), (r"\bPS4\b", "PlayStation cuatro"),
    (r"Xbox Series X\|S", "Xbox Series equis y ese"), (r"Series X", "Series equis"), (r"Series S", "Series ese"),
    (r"\bXbox One\b", "equis box uan"), (r"\bXbox\b", "equis box"), (r"\bPlayStation\b", "pléisteishon"),
    (r"\bPC\b", "pe ce"), (r"(\d+)\s*GB\b", r"\1 gigas"), (r"\bGB\b", "gigas"), (r"\bSSD\b", "ese ese de"), (r"\bHDR\b", "ache de erre"),
    (r"\bM\.2\b", "eme punto dos"), (r"\bUTC\b", "u te ce"),
    (r"Rockstar", "Rocstar"), (r"Vice City", "Vais Siti"), (r"\bJason\b", "Yéison"), (r"Cal Hampton", "Cal Jámpton"),
    (r"Boobie Ike", "Bubi Aik"), (r"Dre'Quan Priest", "Dricuán Prist"), (r"Dre'Quan", "Dricuán"), (r"Real Dimez", "Ril Daims"),
    (r"Bae-Luxe", "Bei Lux"), (r"Roxy", "Roxi"), (r"Brian Heder", "Bráian Jéder"), (r"\bBrian\b", "Bráian"),
    (r"Grassrivers", "Gras Rívers"), (r"Port Gellhorn", "Port Guéljorn"), (r"Mount Kalaga", "Maunt Kalaga"),
    (r"Leonida Keys", "Leonida Kis"), (r"Ultimate", "Áltimeit"), (r"Standard", "Estándar"),
    (r"Vintage Vice City Pack", "Vintach Vais Siti Pak"), (r"Stanier", "Estanier"), (r"Cheetah", "Chíta"),
    (r"Take-Two", "Teik Tu"), (r"Tommy Vercetti", "Tomi Verchéti"), (r"Pointer Sisters", "Póinter Sísters"),
    (r"Tom Petty", "Tom Péti"), (r"Bank of America", "Bank of América"), (r"Red Dead Redemption 2", "Red Ded Ridémshon dos"),
    (r"Red Dead", "Red Ded"), (r"Rideout Customs", "Ráidaut Cástoms"), (r"Only Raw", "Onli Ro"), (r"Jack of Hearts", "Yak of Jarts"),
    (r"\bonline\b", "onlain"), (r"\bYouTube\b", "Yutub"), (r"\blike\b", "laik"), (r"streaming", "estríming"),
    (r"\bcloud\b", "claud"), (r"Cloud Gaming", "Claud Guéiming"), (r"\bspoilers?\b", "espóilers"), (r"\bspoiler\b", "espóiler"),
    (r"day one", "dei uan"), (r"Game Pass", "Guéim Pas"), (r"Pro\b", "Pro"), (r"Los Santos", "Los Santos"),
    (r"Lucia", "Lucía"), (r"Miami", "Maiami"), (r"Florida", "Flórida"), (r"Everglades", "Évergleids"), (r"Keys\b", "Kis"),
    (r"Hawk & Little", "Jok an Lítel"), (r"Leonida", "Leónida"), (r"Duval", "Duval"), (r"\bNZ\b", "Nueva Zelanda"),
    (r"(\d+)\s*%", r"\1 por ciento"), (r"\$(\d+)\.99", r"\1 dólares con noventa y nueve"), (r"\$(\d+)", r"\1 dólares"),
    (r"€", " euros"), (r"\bvs\.?\b", "contra"), (r"\bh\b", "horas"), (r"\bTikTok\b", "Tiktok"), (r"\bmods?\b", "mods"),
    (r"\bFPS\b", "efe pe ese"), (r"(\d+)\s*fps", r"\1 efe pe ese"), (r"\bRPG\b", "erre pe ge"), (r"\bIA\b", "i a"),
]


def to_voice(text):
    s = text
    for a, b in PRON:
        s = re.sub(a, b, s)
    s = s.replace("«", "").replace("»", "").replace("\"", "")
    return s


_k = None


def kokoro():
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(os.path.join(HERE, "models", "kokoro.onnx"), os.path.join(HERE, "models", "voices.bin"))
    return _k


def tts(text, voice="em_alex", speed=1.08):
    os.makedirs(CACHE, exist_ok=True)
    vt = to_voice(text)
    h = hashlib.md5(f"{voice}|{speed}|{vt}".encode()).hexdigest()
    p = os.path.join(CACHE, h + ".wav")
    if os.path.exists(p):
        a, _ = sf.read(p, dtype="float32")
        return a
    a, sr = kokoro().create(vt, voice=voice, speed=speed, lang="es")
    a = np.asarray(a, np.float32)
    # trim silence
    thr = 0.01
    nz = np.where(np.abs(a) > thr)[0]
    if len(nz):
        a = a[max(0, nz[0] - 600): nz[-1] + 1200]
    sf.write(p, a, SR)
    return a


# ---------------------------------------------------------------- music
def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e


def _saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0, detune) if detune else (0,):
        ph = (t * f * (1 + d)) % 1.0
        out += 2 * ph - 1
    return out / (3 if detune else 1)


def _lp(x, alpha):
    # one-pole lowpass
    y = np.empty_like(x)
    acc = 0.0
    # vectorised approx via cumulative filter using scipy-less loop on downsampled? keep simple loop in chunks
    from numpy.lib.stride_tricks import sliding_window_view  # noqa
    for i in range(len(x)):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return y


def lowpass(x, cutoff):
    # FFT brickwall-ish smooth lowpass (fast)
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, n)


PROGS = {
    "Am": [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])],
    "Fm": [(53, [53, 56, 60]), (49, [49, 53, 56]), (51, [51, 55, 58]), (48, [48, 52, 55])],
    "Dm": [(50, [50, 53, 57]), (46, [46, 50, 53]), (48, [48, 52, 55]), (45, [45, 49, 52])],
    "Em": [(52, [52, 55, 59]), (48, [48, 52, 55]), (50, [50, 54, 57]), (47, [47, 51, 54])],
}


def music(seconds, key="Am", bpm=100, seed=0):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    prog = PROGS[key]
    loop_n = int(bar * 4 * SR)
    loop = np.zeros(loop_n)
    # pad
    for i, (root, ch) in enumerate(prog):
        n = int(bar * SR)
        s = i * n
        pad = np.zeros(n)
        for m in ch:
            pad += _saw(_note(m), n, 0.004)
        env = np.minimum(1, np.arange(n) / (0.3 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.2 * SR))
        loop[s:s + n] += lowpass(pad, 1400) * env * 0.10
        # bass 8ths
        en = int(beat / 2 * SR)
        for k in range(8):
            f = _note(root - 24 + (12 if k % 2 else 0))
            b = _saw(f, en) * _env(en, 0.003, 0.12)
            loop[s + k * en: s + k * en + en] += lowpass(b, 500) * 0.28
        # arp 16ths
        sn = int(beat / 4 * SR)
        arp = ch + [ch[0] + 12]
        for k in range(16):
            m = arp[k % 4] + 12
            tone = np.sign(np.sin(2 * np.pi * _note(m) * np.arange(sn) / SR)) * _env(sn, 0.002, 0.06)
            loop[s + k * sn: s + k * sn + sn] += lowpass(tone, 3000) * 0.045
    # drums
    bn = int(beat * SR)
    t = np.arange(bn) / SR
    kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-t * 30)) * t) * np.exp(-t * 9) * 0.6
    snare = (rng.standard_normal(bn) * np.exp(-t * 16) * 0.22 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 20) * 0.15)
    hn = int(beat / 2 * SR)
    hat = rng.standard_normal(hn) * np.exp(-np.arange(hn) / SR * 60) * 0.06
    hat = hat - lowpass(hat, 6000)
    for b in range(16):
        s = b * bn
        if s + bn > loop_n:
            break
        loop[s:s + bn] += kick
        if b % 2 == 1:
            loop[s:s + bn] += snare
        loop[s + hn: s + hn + hn] += hat
        loop[s: s + hn] += hat * 0.5
    loop /= np.max(np.abs(loop)) + 1e-6
    reps = int(np.ceil(seconds * SR / loop_n)) + 1
    out = np.tile(loop, reps)[: int(seconds * SR)]
    # fade in/out
    fi = int(1.5 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    fo = int(3 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out.astype(np.float32)


def whoosh(dur=0.45, seed=1):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 2
    # sweep via mixing two filtered versions
    lo = lowpass(x, 900)
    hi = lowpass(x, 5000)
    y = (lo * (1 - t) + hi * t) * env
    return (y / (np.max(np.abs(y)) + 1e-6) * 0.35).astype(np.float32)


def boom(dur=0.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (40 + 80 * np.exp(-t * 12)) * t) * np.exp(-t * 4)
    return (y * 0.7).astype(np.float32)
