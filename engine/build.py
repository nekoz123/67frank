"""Build a finished video (mp4 + srt + thumbnail) from a script spec.
Usage: python3 build.py <video_id> [--preview]"""
import os, sys, json, math, subprocess, time, re
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw
import gfx
from gfx import W, H, font, text_img, paste, paste_c, rrect, ease_out, clamp, PINK, CYAN, YELLOW, WHITE, NAVY
import audio
from scenes import SCENES

FPS = 30
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "videos")
BUILD = os.path.join(ROOT, "build")
CHANNEL = "Zona Leonida"


def sentences(seg):
    v = seg["v"]
    return v if isinstance(v, list) else [v]


def chunk_caption(text, maxc=34):
    words = text.split()
    out, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) > maxc and cur:
            out.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


def fmt_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def plan_audio(spec):
    voice = spec.get("voice", "em_alex")
    speed = spec.get("speed", 1.03)
    t = 0.0
    timeline = []  # (start, dur, seg, marks)
    voice_track = []
    caps = []  # (start, end, text)
    GAP, TAIL = 0.22, 0.42
    for i, seg in enumerate(spec["segments"]):
        lead = 0.35 if i == 0 else 0.18
        marks = []
        cur = lead
        clips = []
        for s in sentences(seg):
            a = audio.tts(s, voice, speed)
            marks.append(cur)
            clips.append((cur, a))
            d = len(a) / audio.SR
            # captions proportional to characters
            chunks = chunk_caption(s)
            tot = sum(len(c) for c in chunks)
            cc = cur
            for c in chunks:
                cd = d * len(c) / tot
                caps.append((t + cc, t + cc + cd, c))
                cc += cd
            cur += d + GAP
        dur = cur - GAP + TAIL + seg.get("hold", 0)
        timeline.append((t, dur, seg, marks))
        for (o, a) in clips:
            voice_track.append((t + o, a))
        t += dur
    return timeline, voice_track, caps, t


def mix(spec, timeline, voice_track, total, path):
    n = int((total + 0.5) * audio.SR)
    v = np.zeros(n, np.float32)
    for (st, a) in voice_track:
        s = int(st * audio.SR)
        v[s:s + len(a)] += a[: max(0, n - s)]
    v = v / (np.max(np.abs(v)) + 1e-6) * 0.92
    m = audio.music(n / audio.SR, spec.get("key", "Am"), spec.get("bpm", 100), seed=hash(spec["id"]) % 1000)
    # ducking envelope
    env = np.abs(v)
    k = int(0.25 * audio.SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = np.where(env > 0.01, 0.075, 0.16).astype(np.float32)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    out = v + m * duck
    wh = audio.whoosh()
    for i, (st, dur, seg, marks) in enumerate(timeline):
        if i == 0:
            b = audio.boom()
            s = int(0.1 * audio.SR)
            out[s:s + len(b)] += b[: n - s]
        else:
            s = max(0, int((st - 0.15) * audio.SR))
            out[s:s + len(wh)] += wh[: max(0, n - s)] * 0.6
    out = out / (np.max(np.abs(out)) + 1e-6) * 0.95
    sf.write(path, out, audio.SR)


class Overlay:
    def __init__(self, ctx):
        self.logo = text_img(CHANNEL.upper(), font("bebas", 54), fill=WHITE, glow=ctx["a"], glow_r=8)
        self.cap_cache = {}
        self.a, self.b = ctx["a"], ctx["b"]

    def cap(self, text):
        if text not in self.cap_cache:
            ti = text_img(text, font("black", 58), fill=WHITE, stroke=7, stroke_fill=(0, 0, 0))
            bg = rrect(ti.width + 40, ti.height + 24, 16, (0, 0, 0, 120))
            bg.alpha_composite(ti, (20, 12))
            self.cap_cache[text] = bg
        return self.cap_cache[text]

    def draw(self, im, gt, total, caps, seg_t):
        paste(im, self.logo, W - self.logo.width - 36, 26, 0.85)
        # captions
        for (s, e, c) in caps:
            if s - 0.02 <= gt < e + 0.05:
                ci = self.cap(c)
                k = ease_out((gt - s) / 0.12)
                paste_c(im, ci, W / 2, 965 + 12 * (1 - k), 1, 0.96 + 0.04 * k)
                break
        # progress line
        d = ImageDraw.Draw(im)
        d.rectangle((0, H - 6, int(W * gt / total), H), fill=self.a)
        # wipe transition
        if seg_t < 0.35 and gt > 0.5:
            k = seg_t / 0.35
            x = -600 + (W + 1200) * k
            d.polygon([(x - 300, 0), (x + 100, 0), (x - 200, H), (x - 600, H)], fill=self.a)
            d.polygon([(x + 120, 0), (x + 220, 0), (x - 80, H), (x - 180, H)], fill=self.b)


def render(spec, preview=False):
    vid = spec["id"]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    t0 = time.time()
    timeline, vtrack, caps, total = plan_audio(spec)
    wav = os.path.join(BUILD, f"{vid}.wav")
    mix(spec, timeline, vtrack, total, wav)
    # srt
    with open(os.path.join(OUT, f"{vid}.srt"), "w") as f:
        for i, (s, e, c) in enumerate(caps, 1):
            f.write(f"{i}\n{fmt_srt(s)} --> {fmt_srt(e)}\n{c}\n\n")
    th = gfx.THEMES[spec.get("theme", "sunset")]
    backdrop = gfx.Backdrop(spec.get("theme", "sunset"), seed=hash(vid) % 50)
    ctx = dict(a=th["a"], b=th["b"], backdrop=backdrop, soft=gfx.SoftBG(backdrop), channel=CHANNEL)
    ov = Overlay(ctx)
    scenes = [SCENES[seg["s"]](seg, dur, ctx, marks) for (st, dur, seg, marks) in timeline]
    out_mp4 = os.path.join(OUT, f"{vid}.mp4") if not preview else os.path.join(BUILD, f"{vid}_preview.mp4")
    nframes = int(total * FPS)
    if preview:
        nframes = min(nframes, int(spec.get("preview_s", 25) * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    si = 0
    for fi in range(nframes):
        gt = fi / FPS
        while si + 1 < len(timeline) and gt >= timeline[si + 1][0]:
            si += 1
        st, dur, seg, marks = timeline[si]
        lt = gt - st
        sc = scenes[si]
        im = sc.bg(lt, gt)
        sc.draw(im, lt, gt)
        ov.draw(im, gt, total, caps, lt)
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()
    print(f"[{vid}] {total:.1f}s video, {nframes} frames, built in {time.time() - t0:.0f}s -> {out_mp4}", flush=True)
    return total


def thumbnail(spec):
    tspec = spec["thumb"]
    th = gfx.THEMES[spec.get("theme", "sunset")]
    bd = gfx.Backdrop(spec.get("theme", "sunset"), seed=hash(spec["id"]) % 50)
    im = bd.frame(2.0, dim=0.15)
    kind = tspec.get("art")
    if kind == "map":
        m = gfx.leonida_map(900, tspec.get("region"))
        paste_c(im, m, 1440, 560, 1, 1.05)
    elif kind in ("f", "m", "duo", "cap", "pair"):
        if kind == "pair":
            paste(im, gfx.portrait(620, 780, "f", PINK, CYAN, 1), 1000, 300)
            paste(im, gfx.portrait(620, 780, "m", CYAN, gfx.ORANGE, 2), 1330, 300)
        else:
            paste(im, gfx.portrait(700, 880, kind, th["a"], th["b"], 3), 1150, 200)
    elif kind:
        paste_c(im, gfx.icon(kind, 520, tspec.get("icon_col", YELLOW)), 1450, 520)
    # dark left gradient for legibility
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for x in range(0, 1300, 10):
        gd.rectangle((x, 0, x + 10, H), fill=(5, 0, 15, int(200 * (1 - x / 1300))))
    im.alpha_composite(g)
    y = 120
    cols = tspec.get("colors", ["white", "yellow", "a"])
    cmap = {"white": WHITE, "yellow": YELLOW, "a": th["a"], "b": th["b"], "red": gfx.RED, "pink": PINK, "cyan": CYAN}
    for i, line in enumerate(tspec["lines"]):
        c = cmap[cols[i % len(cols)]]
        size = tspec.get("sizes", [240] * 5)[i]
        ti = text_img(line.upper(), font("bebas", size), fill=c, stroke=10, stroke_fill=(0, 0, 0), shadow=True)
        paste(im, ti, 70, y)
        y += ti.height - 10
    if tspec.get("badge"):
        bt = text_img(tspec["badge"].upper(), font("black", 70), fill=WHITE)
        box = rrect(bt.width + 60, bt.height + 40, 18, (230, 30, 50, 255))
        box.alpha_composite(bt, (30, 20))
        rb = box.rotate(-6, expand=True, resample=Image.BICUBIC)
        paste(im, rb, W - rb.width - 50, 50)
    out = os.path.join(OUT, f"{spec['id']}_miniatura.jpg")
    im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=92)
    return out


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    from scripts import VIDEOS
    want = sys.argv[1]
    preview = "--preview" in sys.argv
    for spec in VIDEOS:
        if spec["id"] == want or want == "all":
            os.makedirs(OUT, exist_ok=True)
            thumbnail(spec)
            render(spec, preview)
