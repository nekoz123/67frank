"""Original procedural graphics: synthwave Leonida backgrounds, neon text, cards, map, portraits.
Everything here is drawn from scratch (no third-party / Rockstar artwork)."""
import math, random, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

PINK = (255, 45, 149)
CYAN = (34, 228, 255)
ORANGE = (255, 138, 61)
PURPLE = (123, 44, 255)
YELLOW = (255, 210, 63)
GREEN = (60, 255, 150)
WHITE = (255, 255, 255)
NAVY = (11, 6, 32)
RED = (255, 60, 70)

THEMES = {
    "sunset": dict(sky=[(18, 6, 48), (92, 20, 110), (255, 70, 120), (255, 160, 70)], a=PINK, b=CYAN, sun=[(255, 230, 90), (255, 60, 140)]),
    "night": dict(sky=[(4, 4, 20), (20, 10, 60), (70, 20, 120), (180, 40, 140)], a=CYAN, b=PINK, sun=[(255, 120, 220), (120, 40, 255)]),
    "ocean": dict(sky=[(6, 20, 50), (10, 70, 120), (40, 180, 200), (255, 190, 120)], a=CYAN, b=ORANGE, sun=[(255, 240, 160), (255, 120, 80)]),
    "toxic": dict(sky=[(6, 10, 20), (20, 50, 60), (40, 140, 110), (230, 230, 90)], a=GREEN, b=PINK, sun=[(240, 255, 140), (60, 200, 140)]),
    "fire": dict(sky=[(20, 4, 10), (90, 10, 30), (220, 50, 40), (255, 170, 60)], a=ORANGE, b=YELLOW, sun=[(255, 240, 120), (255, 70, 40)]),
}


@lru_cache(maxsize=64)
def font(name, size):
    files = {
        "bebas": "BebasNeue-Bold.otf", "black": "Montserrat-Black.otf", "xbold": "Montserrat-ExtraBold.otf",
        "bold": "Montserrat-Bold.otf", "semi": "Montserrat-SemiBold.otf", "script": "KaushanScript-Regular.otf",
    }
    return ImageFont.truetype(os.path.join(FONTS, files[name]), size)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_back(t):
    t = clamp(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_io(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def vgrad(w, h, stops):
    """vertical gradient with N evenly spaced color stops -> RGB image"""
    ys = np.linspace(0, 1, h)[:, None]
    n = len(stops) - 1
    arr = np.zeros((h, 1, 3), np.float32)
    for c in range(3):
        xs = np.linspace(0, 1, n + 1)
        arr[:, 0, c] = np.interp(ys[:, 0], xs, [s[c] for s in stops])
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")


def with_alpha(img, f):
    if f >= 0.999:
        return img
    img = img.copy()
    a = img.getchannel("A").point(lambda v: int(v * f))
    img.putalpha(a)
    return img


def paste(base, el, x, y, alpha=1.0):
    """alpha-composite el onto base at (x,y) (top-left), with clipping"""
    if el is None or alpha <= 0.01:
        return
    el = with_alpha(el, alpha)
    x, y = int(round(x)), int(round(y))
    bw, bh = base.size
    ew, eh = el.size
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(ew, bw - x), min(eh, bh - y)
    if ex <= sx or ey <= sy:
        return
    crop = el.crop((sx, sy, ex, ey)) if (sx or sy or ex != ew or ey != eh) else el
    base.alpha_composite(crop, (x + sx, y + sy))


def paste_c(base, el, cx, cy, alpha=1.0, scale=1.0):
    if el is None:
        return
    if abs(scale - 1) > 0.01 and scale > 0.02:
        el = el.resize((max(1, int(el.width * scale)), max(1, int(el.height * scale))), Image.BILINEAR)
    paste(base, el, cx - el.width / 2, cy - el.height / 2, alpha)


# ---------------------------------------------------------------- text
def text_img(text, fnt, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0), glow=None, glow_r=18, spacing=0, shadow=False):
    """Render text (single line) -> tight RGBA with optional neon glow."""
    if spacing:
        # manual letter spacing
        widths = [fnt.getbbox(ch)[2] for ch in text]
        tw = sum(widths) + spacing * (len(text) - 1)
    else:
        bb = fnt.getbbox(text, stroke_width=stroke)
        tw = bb[2] - bb[0]
    asc, desc = fnt.getmetrics()
    th = asc + desc
    pad = (glow_r * 3 if glow else 10) + stroke
    im = Image.new("RGBA", (int(tw) + pad * 2 + 10, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if spacing:
        x = pad
        for ch, wch in zip(text, widths):
            d.text((x, pad), ch, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            x += wch + spacing
    else:
        bb = fnt.getbbox(text, stroke_width=stroke)
        d.text((pad - bb[0], pad), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if glow or shadow:
        a = im.getchannel("A")
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        if shadow:
            sh = Image.new("RGBA", im.size, (0, 0, 0, 255))
            sh.putalpha(a.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.9)))
            out.alpha_composite(sh, (6, 8)) if False else out.alpha_composite(sh.crop((0, 0, im.width - 6, im.height - 8)), (6, 8))
        if glow:
            g = Image.new("RGBA", im.size, glow + (255,))
            ga = a.filter(ImageFilter.GaussianBlur(glow_r))
            g.putalpha(ga.point(lambda v: min(255, int(v * 2.2))))
            out.alpha_composite(g)
            g2 = Image.new("RGBA", im.size, glow + (255,))
            g2.putalpha(a.filter(ImageFilter.GaussianBlur(glow_r / 3)))
            out.alpha_composite(g2)
        out.alpha_composite(im)
        im = out
    bbox = im.getchannel("A").point(lambda v: 255 if v > 6 else 0).getbbox()
    return im.crop(bbox) if bbox else im


def wrap(text, fnt, maxw):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if fnt.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def para_img(text, fnt, maxw, fill=WHITE, line_gap=1.18, align="left", stroke=0):
    lines = wrap(text, fnt, maxw)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    wmax = max(int(fnt.getlength(l)) for l in lines) if lines else 1
    im = Image.new("RGBA", (wmax + 8 + stroke * 2, lh * len(lines) + 8 + stroke * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = 4 + stroke
        if align == "center":
            x = (im.width - fnt.getlength(l)) / 2
        d.text((x, 4 + stroke + i * lh), l, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return im


def rrect(w, h, r, fill, outline=None, width=0, glow=None):
    pad = 40 if glow else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if glow:
        g = Image.new("L", im.size, 0)
        ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + w, pad + h), r, outline=255, width=max(4, width * 2))
        g = g.filter(ImageFilter.GaussianBlur(14))
        gl = Image.new("RGBA", im.size, glow + (255,))
        gl.putalpha(g.point(lambda v: min(255, v * 2)))
        im.alpha_composite(gl)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill, outline=outline, width=width)
    return im


# ---------------------------------------------------------------- scenery
def palm(h, color=(10, 4, 24), seed=0):
    """procedural palm tree silhouette RGBA"""
    rnd = random.Random(seed)
    w = int(h * 0.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bx = w * 0.5 + rnd.uniform(-0.05, 0.05) * w
    lean = rnd.uniform(-0.18, 0.18) * h
    top = (bx + lean, h * 0.22)
    pts = []
    n = 40
    for i in range(n + 1):
        t = i / n
        x = bx + lean * (t ** 1.6)
        y = h - t * (h - top[1])
        pts.append((x, y))
    for i in range(n):
        t = i / n
        wdt = lerp(h * 0.035, h * 0.016, t)
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        d.polygon([(x0 - wdt, y0), (x0 + wdt, y0), (x1 + wdt * 0.95, y1), (x1 - wdt * 0.95, y1)], fill=color)
    tx, ty = pts[-1]
    nf = rnd.randint(7, 9)
    for k in range(nf):
        ang = -math.pi / 2 + (k / (nf - 1) - 0.5) * math.pi * 1.5 + rnd.uniform(-0.15, 0.15)
        L = h * rnd.uniform(0.28, 0.38)
        droop = rnd.uniform(0.35, 0.6)
        prev = (tx, ty)
        segs = 14
        for s in range(1, segs + 1):
            u = s / segs
            x = tx + math.cos(ang) * L * u
            y = ty + math.sin(ang) * L * u + droop * L * u * u
            thick = h * 0.03 * math.sin(math.pi * min(0.999, u * 0.9 + 0.08))
            d.line([prev, (x, y)], fill=color, width=max(2, int(thick)))
            # leaflets
            if s % 1 == 0 and u > 0.1:
                nx, ny = -(y - prev[1]), (x - prev[0])
                ln = math.hypot(nx, ny) or 1
                for sg in (-1, 1):
                    ll = h * 0.05 * (1 - u * 0.6)
                    d.line([(x, y), (x + sg * nx / ln * ll + (x - prev[0]) * 0.6, y + sg * ny / ln * ll + ll * 0.5)], fill=color, width=max(1, int(h * 0.006)))
            prev = (x, y)
    d.ellipse((tx - h * 0.025, ty - h * 0.02, tx + h * 0.025, ty + h * 0.03), fill=color)
    return im


def skyline(w, h, seed=1, color=(14, 6, 34), lit=(255, 200, 120)):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 0
    while x < w:
        bw = rnd.randint(40, 120)
        bh = int(h * rnd.uniform(0.25, 0.95) * (1.0 if abs(x - w * 0.5) < w * 0.25 else 0.7))
        d.rectangle((x, h - bh, x + bw, h), fill=color)
        if rnd.random() < 0.3:
            d.rectangle((x + bw * 0.4, h - bh - rnd.randint(20, 60), x + bw * 0.45, h - bh), fill=color)
        for wy in range(h - bh + 10, h - 8, 16):
            for wx in range(x + 6, x + bw - 8, 14):
                if rnd.random() < 0.28:
                    c = lit if rnd.random() < 0.7 else (120, 230, 255)
                    d.rectangle((wx, wy, wx + 5, wy + 7), fill=c + (rnd.randint(120, 230),))
        x += bw + rnd.randint(0, 10)
    return im


class Backdrop:
    """Animated synthwave Leonida scene. Precomputes layers; frame(t) cheap."""

    def __init__(self, theme="sunset", seed=0):
        th = THEMES[theme]
        self.th = th
        self.horizon = int(H * 0.62)
        sky = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        sky.paste(vgrad(W, self.horizon, th["sky"]), (0, 0))
        # stars
        rnd = random.Random(seed)
        d = ImageDraw.Draw(sky)
        for _ in range(220):
            x, y = rnd.randrange(W), rnd.randrange(int(self.horizon * 0.6))
            b = rnd.randint(120, 255)
            d.point((x, y), fill=(b, b, b, 255))
        # sun
        R = 260
        sun = vgrad(R * 2, R * 2, th["sun"]).convert("RGBA")
        m = Image.new("L", (R * 2, R * 2), 0)
        md = ImageDraw.Draw(m)
        md.ellipse((0, 0, R * 2, R * 2), fill=255)
        for i in range(8):
            y0 = int(R * 1.0 + i * i * 2.2 + i * 14)
            md.rectangle((0, y0, R * 2, y0 + 4 + i * 2), fill=0)
        sun.putalpha(m)
        glow = Image.new("RGBA", (R * 4, R * 4), (0, 0, 0, 0))
        gm = Image.new("L", glow.size, 0)
        ImageDraw.Draw(gm).ellipse((R * 0.8, R * 0.8, R * 3.2, R * 3.2), fill=150)
        gm = gm.filter(ImageFilter.GaussianBlur(70))
        glow = Image.new("RGBA", glow.size, th["sun"][1] + (255,))
        glow.putalpha(gm)
        sky.alpha_composite(glow, (W // 2 - R * 2, self.horizon - R * 2 - 40))
        sky.alpha_composite(sun, (W // 2 - R, self.horizon - R * 2 + 120))
        self.sky = sky
        # skyline (wider for parallax)
        self.city = skyline(W + 400, 230, seed=seed + 3, color=(12, 5, 30))
        # floor
        self.floor_frames = []
        fh = H - self.horizon
        base_floor = vgrad(W, fh, [(30, 6, 50), (8, 2, 20)]).convert("RGBA")
        # reflection of sun on water/floor
        refl = Image.new("RGBA", (W, fh), (0, 0, 0, 0))
        rd = ImageDraw.Draw(refl)
        for i in range(0, fh, 9):
            ww = int(240 * (1 - i / fh) + 40)
            rd.rectangle((W // 2 - ww, i, W // 2 + ww, i + 3), fill=th["sun"][1] + (int(140 * (1 - i / fh)),))
        base_floor.alpha_composite(refl)
        nfr = 30
        col = th["a"]
        for k in range(nfr):
            f = base_floor.copy()
            lay = Image.new("RGBA", (W, fh), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            vx = W / 2
            for i in range(-24, 25):
                x1 = vx + i * 160
                ld.line([(vx + i * 8, 0), (x1 + (x1 - vx) * 2.5, fh)], fill=col + (150,), width=2)
            off = k / nfr
            for j in range(14):
                z = (j + 1 - off)
                y = fh * (1.0 / (z * 0.55 + 0.0001)) ** 1.0 * 0.12
                if 0 < y < fh:
                    ld.line([(0, y), (W, y)], fill=col + (int(60 + 140 * y / fh),), width=2)
            gl = lay.filter(ImageFilter.GaussianBlur(4))
            f.alpha_composite(gl)
            f.alpha_composite(lay)
            self.floor_frames.append(f)
        # palms
        self.palms = []
        prnd = random.Random(seed + 9)
        for i, (px, ph) in enumerate([(-60, 820), (190, 640), (1560, 700), (1760, 900), (1380, 520)]):
            self.palms.append((px, ph, palm(ph, seed=seed * 7 + i)))

    def frame(self, t, dim=0.0):
        im = self.sky.copy()
        cx = int(-200 + 30 * math.sin(t * 0.15))
        paste(im, self.city, cx, self.horizon - 230 + 2)
        im.alpha_composite(self.floor_frames[int(t * 30) % len(self.floor_frames)], (0, self.horizon))
        im.alpha_composite(self.sunmask_cache, (0, 0)) if False else None
        for i, (px, ph, p) in enumerate(self.palms):
            sway = 14 * math.sin(t * 0.5 + i)
            paste(im, p, px + sway, H - ph + 30)
        if dim > 0:
            im.alpha_composite(Image.new("RGBA", (W, H), (6, 2, 18, int(255 * dim))))
        return im


class SoftBG:
    """darkened blurred backdrop with slow pan for content scenes"""

    def __init__(self, backdrop, dim=0.55):
        big = backdrop.frame(3.0).resize((W + 160, H + 90), Image.BILINEAR)
        big = big.filter(ImageFilter.GaussianBlur(10))
        big.alpha_composite(Image.new("RGBA", big.size, (8, 3, 22, int(255 * dim))))
        # vignette
        v = Image.new("L", big.size, 0)
        ImageDraw.Draw(v).ellipse((-300, -250, big.width + 300, big.height + 250), fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160))
        dark = Image.new("RGBA", big.size, (0, 0, 0, 255))
        dark.putalpha(ImageChops.invert(v).point(lambda x: int(x * 0.8)))
        big.alpha_composite(dark)
        # scanline / particles
        self.big = big
        rnd = random.Random(5)
        self.parts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 30), rnd.uniform(1.5, 4)) for _ in range(40)]
        self.col = backdrop.th["a"]

    def frame(self, t):
        ox = 80 + 80 * math.sin(t * 0.07)
        oy = 45 + 40 * math.cos(t * 0.05)
        im = self.big.crop((int(ox), int(oy), int(ox) + W, int(oy) + H))
        d = ImageDraw.Draw(im)
        for (x, y, sp, r) in self.parts:
            yy = (y - t * sp) % H
            d.ellipse((x - r, yy - r, x + r, yy + r), fill=self.col + (90,))
        return im


# ---------------------------------------------------------------- portraits
def portrait(w, h, kind="m", rim=PINK, rim2=CYAN, seed=0):
    """stylized original silhouette bust with neon rim lights"""
    if kind == "duo":
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        a = portrait(int(w * 0.62), int(h * 0.92), "f", rim, rim2, seed)
        b = portrait(int(w * 0.62), int(h * 0.92), "f2", rim2, rim, seed + 1)
        out.alpha_composite(b, (int(w * 0.38), int(h * 0.08)))
        out.alpha_composite(a, (0, int(h * 0.08)))
        return out
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    cx = w / 2
    hr = w * 0.16
    hy = h * 0.42
    # shoulders (rounded, sloped)
    d.rounded_rectangle((cx - w * 0.46, h * 0.66, cx + w * 0.46, h * 1.4), radius=int(w * 0.24), fill=255)
    d.polygon([(cx - hr * 0.7, h * 0.6), (cx + hr * 0.7, h * 0.6), (cx + w * 0.3, h * 0.69), (cx - w * 0.3, h * 0.69)], fill=255)
    # neck
    d.polygon([(cx - hr * 0.62, hy + hr * 0.6), (cx + hr * 0.62, hy + hr * 0.6), (cx + hr * 0.8, h * 0.68), (cx - hr * 0.8, h * 0.68)], fill=255)
    # head
    d.ellipse((cx - hr, hy - hr * 1.25, cx + hr, hy + hr * 1.2), fill=255)
    # ears
    d.ellipse((cx - hr * 1.12, hy - hr * 0.2, cx - hr * 0.8, hy + hr * 0.35), fill=255)
    d.ellipse((cx + hr * 0.8, hy - hr * 0.2, cx + hr * 1.12, hy + hr * 0.35), fill=255)
    if kind in ("f", "f2"):
        d.ellipse((cx - hr * 1.3, hy - hr * 1.5, cx + hr * 1.3, hy + hr * 0.6), fill=255)
        if kind == "f":
            d.rounded_rectangle((cx - hr * 1.32, hy - hr * 0.4, cx + hr * 1.32, h * 0.8), radius=int(hr * 0.8), fill=255)
        else:  # high bun / ponytail
            d.ellipse((cx - hr * 0.6, hy - hr * 2.1, cx + hr * 0.6, hy - hr * 1.0), fill=255)
    elif kind == "m":
        d.ellipse((cx - hr * 1.06, hy - hr * 1.4, cx + hr * 1.06, hy + hr * 0.0), fill=255)
    elif kind == "cap":
        d.chord((cx - hr * 1.1, hy - hr * 1.5, cx + hr * 1.1, hy + hr * 0.3), 180, 360, fill=255)
        d.rounded_rectangle((cx - hr * 0.3, hy - hr * 0.72, cx + hr * 1.9, hy - hr * 0.5), radius=6, fill=255)
    grad = vgrad(w, h, [(34, 16, 66), (8, 4, 20)]).convert("RGBA")
    grad.putalpha(m)

    def rimlayer(dx, col):
        sh = ImageChops.offset(m, dx, -abs(dx) // 3)
        edge = ImageChops.subtract(m, sh).filter(ImageFilter.GaussianBlur(3))
        l = Image.new("RGBA", (w, h), col + (255,))
        l.putalpha(edge.point(lambda v: min(255, v * 2)))
        return l
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gl = Image.new("RGBA", (w, h), rim + (255,))
    gl.putalpha(m.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.55)))
    out.alpha_composite(gl)
    out.alpha_composite(grad)
    out.alpha_composite(rimlayer(int(w * 0.025), rim))
    out.alpha_composite(rimlayer(-int(w * 0.025), rim2))
    # fade bottom
    fade = Image.new("L", (w, h), 255)
    fd = ImageDraw.Draw(fade)
    for y in range(int(h * 0.85), h):
        fd.line([(0, y), (w, y)], fill=int(255 * (h - y) / (h * 0.15)))
    edge = Image.new("L", (w, h), 0)
    ImageDraw.Draw(edge).rectangle((30, 30, w - 30, h + 60), fill=255)
    edge = edge.filter(ImageFilter.GaussianBlur(18))
    out.putalpha(ImageChops.multiply(ImageChops.multiply(out.getchannel("A"), fade), edge))
    return out


# ---------------------------------------------------------------- map
MAP_OUTLINE = [(80, 130), (300, 110), (430, 120), (560, 105), (700, 120), (770, 170), (775, 280), (750, 380), (780, 500),
               (810, 620), (800, 740), (760, 800), (705, 790), (660, 720), (600, 640), (540, 580), (505, 480), (470, 400),
               (420, 330), (330, 285), (230, 265), (140, 270), (85, 230)]
MAP_REGIONS = {
    "Port Gellhorn": [(0, 0), (330, 0), (330, 330), (0, 330)],
    "Ambrosia": [(330, 0), (560, 0), (560, 430), (330, 330)],
    "Mount Kalaga": [(560, 0), (900, 0), (900, 400), (560, 430)],
    "Grassrivers": [(330, 330), (560, 430), (690, 410), (700, 900), (330, 900)],
    "Vice City": [(690, 410), (900, 400), (900, 900), (700, 900)],
}
KEYS = [(735, 835, 22), (690, 865, 18), (640, 885, 16), (590, 898, 13), (545, 905, 11), (505, 908, 9)]
REGION_COL = {"Port Gellhorn": ORANGE, "Ambrosia": YELLOW, "Mount Kalaga": GREEN, "Grassrivers": (90, 200, 120),
              "Vice City": PINK, "Leonida Keys": CYAN}
REGION_PIN = {"Port Gellhorn": (190, 200), "Ambrosia": (420, 200), "Mount Kalaga": (660, 230), "Grassrivers": (580, 560),
              "Vice City": (750, 640), "Leonida Keys": (640, 885)}


def leonida_map(size=900, highlight=None, dim_others=True):
    s = size / 900
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    outline = Image.new("L", (size, size), 0)
    ImageDraw.Draw(outline).polygon([(x * s, y * s) for x, y in MAP_OUTLINE], fill=255)
    regions = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(regions)
    for name, poly in MAP_REGIONS.items():
        c = REGION_COL[name]
        a = 235 if (highlight in (None, name)) else (70 if dim_others else 200)
        rd.polygon([(x * s, y * s) for x, y in poly], fill=tuple(int(v * 0.55) for v in c) + (a,))
    # texture: noise dots
    arr = np.array(regions)
    rnd = np.random.default_rng(3)
    noise = rnd.integers(-18, 18, arr.shape[:2])
    arr[..., :3] = np.clip(arr[..., :3].astype(int) + noise[..., None], 0, 255)
    regions = Image.fromarray(arr.astype(np.uint8), "RGBA")
    ra = ImageChops.multiply(regions.getchannel("A"), outline)
    regions.putalpha(ra)
    # glow outline
    edge = outline.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
    g = Image.new("RGBA", (size, size), CYAN + (255,))
    g.putalpha(edge.filter(ImageFilter.GaussianBlur(10)))
    im.alpha_composite(g)
    im.alpha_composite(regions)
    e2 = Image.new("RGBA", (size, size), (200, 250, 255, 255))
    e2.putalpha(edge)
    im.alpha_composite(e2)
    d = ImageDraw.Draw(im)
    # region borders
    for name, poly in MAP_REGIONS.items():
        pass
    for (x, y, r) in KEYS:
        c = REGION_COL["Leonida Keys"]
        a = 255 if highlight in (None, "Leonida Keys") else 90
        d.ellipse(((x - r) * s, (y - r * 0.6) * s, (x + r) * s, (y + r * 0.6) * s), fill=tuple(int(v * 0.6) for v in c) + (a,), outline=(200, 250, 255, a), width=2)
    return im


# ---------------------------------------------------------------- icons
def icon(kind, size=120, col=CYAN):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size
    lw = max(3, s // 14)
    c = col + (255,)
    if kind == "check":
        d.ellipse((4, 4, s - 4, s - 4), outline=c, width=lw)
        d.line([(s * .28, s * .52), (s * .44, s * .68), (s * .74, s * .34)], fill=c, width=lw + 2, joint="curve")
    elif kind == "x":
        d.ellipse((4, 4, s - 4, s - 4), outline=c, width=lw)
        d.line([(s * .32, s * .32), (s * .68, s * .68)], fill=c, width=lw + 2)
        d.line([(s * .68, s * .32), (s * .32, s * .68)], fill=c, width=lw + 2)
    elif kind == "clock":
        d.ellipse((4, 4, s - 4, s - 4), outline=c, width=lw)
        d.line([(s / 2, s / 2), (s / 2, s * .22)], fill=c, width=lw)
        d.line([(s / 2, s / 2), (s * .7, s * .6)], fill=c, width=lw)
    elif kind == "download":
        d.line([(s / 2, s * .12), (s / 2, s * .62)], fill=c, width=lw + 2)
        d.line([(s * .28, s * .42), (s / 2, s * .64), (s * .72, s * .42)], fill=c, width=lw + 2, joint="curve")
        d.line([(s * .15, s * .72), (s * .15, s * .86), (s * .85, s * .86), (s * .85, s * .72)], fill=c, width=lw, joint="curve")
    elif kind == "warn":
        d.polygon([(s / 2, s * .08), (s * .95, s * .9), (s * .05, s * .9)], outline=c, width=lw)
        d.line([(s / 2, s * .36), (s / 2, s * .64)], fill=c, width=lw + 2)
        d.ellipse((s / 2 - lw, s * .74 - lw, s / 2 + lw, s * .74 + lw), fill=c)
    elif kind == "star":
        pts = []
        for i in range(10):
            r = s * .46 if i % 2 == 0 else s * .2
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((s / 2 + r * math.cos(a), s / 2 + r * math.sin(a)))
        d.polygon(pts, outline=c, width=lw)
    elif kind == "pin":
        d.ellipse((s * .22, s * .06, s * .78, s * .62), outline=c, width=lw)
        d.polygon([(s * .27, s * .45), (s / 2, s * .94), (s * .73, s * .45)], fill=c)
        d.ellipse((s * .4, s * .24, s * .6, s * .44), fill=c)
    elif kind == "money":
        d.rounded_rectangle((s * .06, s * .24, s * .94, s * .76), radius=s // 10, outline=c, width=lw)
        d.ellipse((s * .36, s * .34, s * .64, s * .66), outline=c, width=lw)
    elif kind == "gamepad":
        d.rounded_rectangle((s * .06, s * .3, s * .94, s * .74), radius=s // 5, outline=c, width=lw)
        d.line([(s * .22, s * .52), (s * .38, s * .52)], fill=c, width=lw)
        d.line([(s * .3, s * .44), (s * .3, s * .6)], fill=c, width=lw)
        d.ellipse((s * .64, s * .42, s * .72, s * .5), fill=c)
        d.ellipse((s * .74, s * .52, s * .82, s * .6), fill=c)
    elif kind == "pc":
        d.rounded_rectangle((s * .08, s * .14, s * .92, s * .68), radius=8, outline=c, width=lw)
        d.line([(s / 2, s * .68), (s / 2, s * .84)], fill=c, width=lw)
        d.line([(s * .3, s * .86), (s * .7, s * .86)], fill=c, width=lw)
    elif kind == "cloud":
        d.ellipse((s * .1, s * .4, s * .45, s * .75), outline=c, width=lw)
        d.ellipse((s * .3, s * .22, s * .72, s * .64), outline=c, width=lw)
        d.ellipse((s * .55, s * .4, s * .9, s * .75), outline=c, width=lw)
    elif kind == "film":
        d.rounded_rectangle((s * .08, s * .2, s * .92, s * .8), radius=8, outline=c, width=lw)
        d.polygon([(s * .42, s * .36), (s * .66, s * .5), (s * .42, s * .64)], fill=c)
    elif kind == "user":
        d.ellipse((s * .32, s * .1, s * .68, s * .46), outline=c, width=lw)
        d.pieslice((s * .14, s * .52, s * .86, s * 1.2), 180, 360, outline=c, width=lw)
    elif kind == "fire":
        d.polygon([(s / 2, s * .06), (s * .8, s * .5), (s * .74, s * .82), (s / 2, s * .94), (s * .26, s * .82), (s * .2, s * .5), (s * .36, s * .32), (s * .42, s * .5)], outline=c, width=lw)
    else:
        d.ellipse((4, 4, s - 4, s - 4), outline=c, width=lw)
    g = im.filter(ImageFilter.GaussianBlur(6))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(g)
    out.alpha_composite(im)
    return out
