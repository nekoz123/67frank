"""Scene types. Each scene: Scene(seg, dur, ctx, marks) with draw(im, t).
`marks` = start times (s, relative to segment) of each narration sentence."""
import math
from PIL import Image, ImageDraw, ImageFilter
from gfx import *

SAFE_BOTTOM = 860  # keep content above captions


def col(name, ctx):
    return {"a": ctx["a"], "b": ctx["b"], "pink": PINK, "cyan": CYAN, "orange": ORANGE, "yellow": YELLOW,
            "green": GREEN, "white": WHITE, "red": RED, "purple": PURPLE}.get(name, ctx["a"])


class Base:
    full_bg = False
    dim = 0.0

    def __init__(self, seg, dur, ctx, marks):
        self.seg, self.dur, self.ctx, self.marks = seg, dur, ctx, marks
        self.a, self.b = ctx["a"], ctx["b"]
        self.setup()

    def setup(self):
        pass

    def bg(self, t, gt):
        if self.full_bg:
            return self.ctx["backdrop"].frame(gt, dim=self.dim)
        return self.ctx["soft"].frame(gt)

    def mark(self, i, default=None):
        if i < len(self.marks):
            return self.marks[i]
        return default if default is not None else self.dur * 0.8

    def heading(self, im, t, text, y=60):
        if not hasattr(self, "_head"):
            self._head = text_img(text.upper(), font("bebas", 110), glow=self.a, glow_r=14)
            bar = Image.new("RGBA", (min(self._head.width, 1700), 8), self.b + (255,))
            self._bar = bar
        k = ease_out(t / 0.5)
        paste(im, self._head, 100 - 60 * (1 - k), y, k)
        bw = int(self._bar.width * ease_out((t - 0.2) / 0.6))
        if bw > 2:
            paste(im, self._bar.crop((0, 0, bw, 8)), 112, y + self._head.height + 6)


class Hook(Base):
    full_bg = True
    dim = 0.35

    def setup(self):
        self.dim = self.seg.get("dim", 0.35)
        cols = [WHITE, self.a, self.b, YELLOW]
        size = self.seg.get("size", 210 if len(self.seg["lines"]) < 3 else 175)
        self.lines = []
        for i, l in enumerate(self.seg["lines"]):
            c = col(self.seg["colors"][i], self.ctx) if "colors" in self.seg else cols[i % len(cols)]
            fill = WHITE if c == WHITE else tuple(int(v * 0.35 + 255 * 0.65) for v in c)
            self.lines.append(text_img(l.upper(), font("bebas", size), fill=fill, stroke=4, stroke_fill=c if c != WHITE else self.a,
                                       glow=(self.a if c == WHITE else c), glow_r=12, shadow=True))
        self.tag = text_img(self.seg["tag"].upper(), font("black", 46), fill=NAVY) if self.seg.get("tag") else None

    def draw(self, im, t, gt):
        n = len(self.lines)
        total_h = sum(l.height for l in self.lines) + 10 * (n - 1)
        y = (H - total_h) / 2 - 70 + (40 if self.seg.get("tag") else 0)
        for i, l in enumerate(self.lines):
            st = i * 0.32 if not self.seg.get("sync") else self.mark(i, i * 0.32)
            k = (t - st) / 0.45
            if k <= 0:
                y += l.height + 10
                continue
            sc = lerp(1.6, 1.0, ease_back(k)) if k < 1 else 1.0 + 0.012 * math.sin((t - st) * 2.0)
            shake = 6 * max(0, 1 - k) * math.sin(t * 70)
            paste_c(im, l, W / 2 + shake, y + l.height / 2, clamp(k * 2), sc)
            y += l.height + 10
        if self.tag:
            k = ease_out((t - 0.1) / 0.4)
            box = rrect(self.tag.width + 50, self.tag.height + 26, 12, YELLOW + (255,))
            box.alpha_composite(self.tag, (25, 13))
            paste_c(im, box, W / 2, 130 - 80 * (1 - k), k)


class Title(Base):
    full_bg = True
    dim = 0.55

    def setup(self):
        self.num = text_img(self.seg.get("num", ""), font("bebas", 360), fill=(0, 0, 0, 0), stroke=6, stroke_fill=self.a, glow=self.a, glow_r=20) if self.seg.get("num") else None
        self.lines = [text_img(l.upper(), font("bebas", 150), glow=self.b, glow_r=14, shadow=True) for l in self.seg["lines"]]
        self.sub = para_img(self.seg["sub"], font("bold", 44), 1000, fill=(235, 225, 255)) if self.seg.get("sub") else None

    def draw(self, im, t, gt):
        x0 = 140
        if self.num:
            k = ease_out(t / 0.5)
            paste(im, self.num, x0 - 100 * (1 - k), H / 2 - self.num.height / 2 - 60, k)
            x0 += self.num.width + 40
        y = H / 2 - sum(l.height for l in self.lines) / 2 - 80
        for i, l in enumerate(self.lines):
            k = ease_out((t - 0.15 - i * 0.15) / 0.5)
            paste(im, l, x0 + 120 * (1 - k), y, k)
            y += l.height + 6
        if self.sub:
            k = ease_out((t - 0.5) / 0.5)
            paste(im, self.sub, x0 + 6, y + 20, k)


class Bullets(Base):
    def setup(self):
        items = self.seg["items"]
        self.off = self.seg.get("offset", 1 if self.seg.get("intro", True) else 0)
        n = len(items)
        fsize = 54 if n <= 4 else (46 if n <= 5 else 40)
        gap = 22 if n <= 4 else 16
        icons = self.seg.get("icons") or ["check"] * n
        self.rows = []
        for i, it in enumerate(items):
            c = self.a if i % 2 == 0 else self.b
            ic = icon(icons[i] if i < len(icons) else icons[-1], 84, c)
            txt = para_img(it, font("xbold", fsize), 1380, fill=WHITE)
            ch = max(118, txt.height + 40)
            card = rrect(1640, ch, 22, (20, 10, 45, 215), outline=c + (160,), width=3)
            card.alpha_composite(ic, (50, (card.height - ic.height) // 2))
            card.alpha_composite(txt, (50 + 40 + ic.width, (card.height - txt.height) // 2))
            self.rows.append(card)
        total = sum(r.height for r in self.rows) + gap * (n - 1)
        avail = SAFE_BOTTOM - 240
        self.scale = min(1.0, avail / total)
        if self.scale < 1:
            self.rows = [r.resize((int(r.width * self.scale), int(r.height * self.scale)), Image.LANCZOS) for r in self.rows]
        self.gap = gap
        self.y0 = 240 + max(0, (avail - sum(r.height for r in self.rows) - gap * (n - 1)) / 2)

    def draw(self, im, t, gt):
        self.heading(im, t, self.seg["title"])
        n = len(self.rows)
        y = self.y0
        for i, r in enumerate(self.rows):
            st = self.mark(i + self.off, 0.4 + i * (self.dur * 0.7 / max(1, n)))
            k = ease_out((t - st) / 0.45)
            if k > 0:
                paste(im, r, 100 + 140 * (1 - k), y, k)
            y += r.height + self.gap


class Stat(Base):
    def setup(self):
        self.label = para_img(self.seg["label"], font("black", 64), 1500, fill=WHITE, align="center")
        self.sub = para_img(self.seg["sub"], font("semi", 42), 1400, fill=(220, 210, 245), align="center") if self.seg.get("sub") else None
        self.cache = {}

    def num_img(self, s):
        if s not in self.cache:
            self.cache[s] = text_img(s, font("bebas", self.seg.get("size", 330)), fill=WHITE, glow=self.a, glow_r=24)
        return self.cache[s]

    def draw(self, im, t, gt):
        if self.seg.get("title"):
            self.heading(im, t, self.seg["title"])
        val = self.seg["value"]
        if isinstance(val, (int, float)):
            k = ease_out(t / 1.4)
            v = val * k
            dec = self.seg.get("dec", 0)
            txt = f"{v:,.{dec}f}".replace(",", " ")
            s = self.seg.get("prefix", "") + txt + self.seg.get("suffix", "")
        else:
            s = val
        ni = self.num_img(s)
        sc = lerp(0.6, 1.0, ease_back(t / 0.5))
        paste_c(im, ni, W / 2, 400, clamp(t / 0.3), sc)
        k = ease_out((t - 0.4) / 0.5)
        paste_c(im, self.label, W / 2, 640 + 30 * (1 - k), k)
        if self.sub:
            k = ease_out((t - 0.8) / 0.5)
            paste_c(im, self.sub, W / 2, 640 + self.label.height / 2 + 40 + self.sub.height / 2, k)


class Compare(Base):
    def setup(self):
        for fs in (44, 40, 36, 33, 30):
            parts = []
            for j, side in enumerate(self.seg["sides"]):
                cc = col(side.get("color", "a" if j == 0 else "b"), self.ctx)
                els = [text_img(side["title"].upper(), font("bebas", 92), glow=cc, glow_r=10)]
                if side.get("big"):
                    els.append(text_img(side["big"], font("bebas", 140), fill=cc))
                rows = [para_img("• " + row, font("semi", fs), 640, fill=WHITE) for row in side["rows"]]
                parts.append((cc, els, rows))
            hmax = max(sum(e.height + 10 for e in els) + 40 + sum(r.height + 14 for r in rows) for (_, els, rows) in parts)
            if hmax + 90 <= 650:
                break
        ch = int(min(650, max(420, hmax + 90)))
        self.cards = []
        for (cc, els, rows) in parts:
            card = rrect(780, ch, 30, (16, 8, 40, 225), outline=cc + (255,), width=4, glow=cc)
            yy = 75
            for e in els:
                card.alpha_composite(e, ((card.width - e.width) // 2, yy))
                yy += e.height + 10
            yy += 30
            for r in rows:
                card.alpha_composite(r, (85, yy))
                yy += r.height + 14
            self.cards.append(card)
        self.ch = ch
        self.vs = text_img(self.seg.get("vs", "VS"), font("bebas", 150), fill=YELLOW, glow=ORANGE, glow_r=18)

    def draw(self, im, t, gt):
        if self.seg.get("title"):
            self.heading(im, t, self.seg["title"], y=40)
        for j, c in enumerate(self.cards):
            st = self.mark(j + self.seg.get("offset", 0), 0.2 + j * 0.6)
            k = ease_out((t - st) / 0.5)
            x = 120 if j == 0 else W - 120 - c.width + 80
            paste(im, c, x + (-150 if j == 0 else 150) * (1 - k), 200 + (650 - self.ch) / 2, k)
        k = ease_back((t - 0.5) / 0.5)
        if k > 0:
            paste_c(im, self.vs, W / 2, 240 + 325, clamp(k), 0.5 + 0.5 * k)


class Map(Base):
    def setup(self):
        hl = self.seg.get("region")
        self.map = leonida_map(820, hl)
        self.hl = hl
        self.name = text_img((self.seg.get("name") or hl or "LEONIDA").upper(), font("bebas", 130), glow=REGION_COL.get(hl, self.a), glow_r=14)
        self.desc = para_img(self.seg.get("desc", ""), font("semi", 48), 840, fill=(235, 230, 255))
        self.tag = text_img(self.seg["tag"].upper(), font("black", 34), fill=NAVY) if self.seg.get("tag") else None
        self.pin = icon("pin", 90, REGION_COL.get(hl, YELLOW)) if hl else None
        self.note = text_img("Mapa ilustrativo · ubicaciones aproximadas", font("semi", 24), fill=(200, 190, 230))

    def draw(self, im, t, gt):
        mx, my = 80, 70
        k = ease_out(t / 0.6)
        sc = lerp(0.92, 1.0, k) + 0.01 * math.sin(gt * 0.6)
        paste_c(im, self.map, mx + 410, my + 410, k, sc)
        if self.pin:
            px, py = REGION_PIN[self.hl]
            px, py = mx + px * 820 / 900, my + py * 820 / 900
            bounce = abs(math.sin(t * 3)) * 18
            kk = ease_back((t - 0.4) / 0.4)
            if kk > 0:
                r = (t * 60) % 80
                ring = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
                ImageDraw.Draw(ring).ellipse((100 - r, 100 - r * 0.5, 100 + r, 100 + r * 0.5), outline=REGION_COL[self.hl] + (int(255 * (1 - r / 80)),), width=4)
                paste_c(im, ring, px, py)
                paste_c(im, self.pin, px, py - 45 - bounce, 1, clamp(kk))
        x = 1000
        y = 150
        if self.tag:
            kt = ease_out((t - 0.2) / 0.4)
            box = rrect(self.tag.width + 36, self.tag.height + 20, 10, YELLOW + (255,))
            box.alpha_composite(self.tag, (18, 10))
            paste(im, box, x, y, kt)
            y += box.height + 20
        k2 = ease_out((t - 0.3) / 0.5)
        paste(im, self.name, x + 80 * (1 - k2), y, k2)
        k3 = ease_out((t - 0.7) / 0.5)
        paste(im, self.desc, x + 6, y + self.name.height + 25, k3)
        paste(im, self.note, 90, 905, 0.8)


class Char(Base):
    def setup(self):
        c1 = col(self.seg.get("color", "a"), self.ctx)
        c2 = col(self.seg.get("color2", "b"), self.ctx)
        self.c1 = c1
        self.por = portrait(560, 700, self.seg.get("kind", "m"), c1, c2, seed=hash(self.seg["name"]) % 100)
        self.name = text_img(self.seg["name"].upper(), font("bebas", 150), glow=c1, glow_r=16, shadow=True)
        self.role = text_img(self.seg["role"].upper(), font("black", 38), fill=NAVY)
        self.traits = [para_img("› " + tr, font("semi", 40), 900, fill=WHITE) for tr in self.seg.get("traits", [])]
        self.q = text_img("SILUETA ILUSTRATIVA", font("semi", 22), fill=(200, 190, 230))

    def draw(self, im, t, gt):
        k = ease_out(t / 0.6)
        paste(im, self.por, 140 - 120 * (1 - k), 140 + 4 * math.sin(gt), k)
        paste(im, self.q, 300, 850, 0.7 * k)
        x = 820
        k2 = ease_out((t - 0.2) / 0.5)
        paste(im, self.name, x + 100 * (1 - k2), 170, k2)
        box = rrect(self.role.width + 40, self.role.height + 22, 10, self.c1 + (255,))
        box.alpha_composite(self.role, (20, 11))
        paste(im, box, x + 8, 175 + self.name.height + 10, ease_out((t - 0.4) / 0.4))
        y = 175 + self.name.height + box.height + 50
        for i, tr in enumerate(self.traits):
            st = self.mark(i + self.seg.get("offset", 1), 0.8 + i * 0.7)
            kk = ease_out((t - st) / 0.45)
            if kk > 0:
                paste(im, tr, x + 10 + 60 * (1 - kk), y, kk)
            y += tr.height + 18


class Clock(Base):
    def setup(self):
        self.face = Image.new("RGBA", (620, 620), (0, 0, 0, 0))  # clock face
        d = ImageDraw.Draw(self.face)
        d.ellipse((10, 10, 610, 610), fill=(16, 8, 40, 230), outline=self.a + (255,), width=10)
        for i in range(12):
            a = i * math.pi / 6
            r1, r2 = 250, 285
            d.line([(310 + r1 * math.sin(a), 310 - r1 * math.cos(a)), (310 + r2 * math.sin(a), 310 - r2 * math.cos(a))], fill=WHITE, width=8 if i % 3 == 0 else 4)
        g = self.face.filter(ImageFilter.GaussianBlur(12))
        f2 = Image.new("RGBA", self.face.size, (0, 0, 0, 0))
        f2.alpha_composite(g)
        f2.alpha_composite(self.face)
        self.face = f2
        self.rows = []
        for (l, r) in self.seg.get("rows", []):
            card = rrect(900, 84, 16, (20, 10, 45, 220), outline=self.b + (140,), width=2)
            a_ = text_img(l, font("xbold", 40))
            b_ = text_img(r, font("bebas", 58), fill=YELLOW)
            card.alpha_composite(a_, (30, (84 - a_.height) // 2))
            card.alpha_composite(b_, (900 - 30 - b_.width, (84 - b_.height) // 2))
            self.rows.append(card)
        self.big = text_img(self.seg.get("big", "00:00"), font("bebas", 120), glow=self.b)

    def draw(self, im, t, gt):
        if self.seg.get("title"):
            self.heading(im, t, self.seg["title"], y=40)
        cx, cy = 480, 500
        paste_c(im, self.face, cx, cy, ease_out(t / 0.4))
        d = ImageDraw.Draw(im)
        k = ease_io(t / 2.2)
        mins = lerp(self.seg.get("from_min", -45), 0, k)
        ma = mins / 60 * 2 * math.pi
        ha = (mins / 60 / 12) * 2 * math.pi
        d.line([(cx, cy), (cx + 200 * math.sin(ma), cy - 200 * math.cos(ma))], fill=self.b, width=12)
        d.line([(cx, cy), (cx + 140 * math.sin(ha), cy - 140 * math.cos(ha))], fill=WHITE, width=16)
        d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=self.a)
        if t > 2.2:
            paste_c(im, self.big, cx, cy + 360, ease_out((t - 2.2) / 0.3))
        for i, r in enumerate(self.rows):
            st = self.mark(i + self.seg.get("offset", 1), 0.6 + i * 0.5)
            kk = ease_out((t - st) / 0.4)
            if kk > 0:
                paste(im, r, 900 + 100 * (1 - kk), 200 + i * 100, kk)


class Timeline(Base):
    def setup(self):
        self.pts = []
        for i, (date, lab) in enumerate(self.seg["points"]):
            c = self.a if i % 2 == 0 else self.b
            di = text_img(date.upper(), font("bebas", 96), glow=c, glow_r=10)
            li = para_img(lab, font("bold", 40), 380, fill=WHITE, align="center")
            self.pts.append((di, li, c))

    def draw(self, im, t, gt):
        self.heading(im, t, self.seg["title"])
        n = len(self.pts)
        x0, x1, y = 280, W - 280, 540
        d = ImageDraw.Draw(im)
        prog = ease_io(t / max(1.5, self.dur * 0.8))
        d.line([(x0, y), (x1, y)], fill=(80, 60, 120), width=6)
        d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=self.a, width=8)
        for i, (di, li, c) in enumerate(self.pts):
            x = x0 + (x1 - x0) * (i / max(1, n - 1))
            st = self.mark(i + self.seg.get("offset", 1), i * self.dur * 0.8 / max(1, n))
            kk = ease_back((t - st) / 0.4)
            if kk > 0:
                r = 22 * clamp(kk)
                d.ellipse((x - r, y - r, x + r, y + r), fill=c, outline=WHITE, width=4)
                up = i % 2 == 0
                paste_c(im, di, x, y - 110 if up else y + 90, clamp(kk))
                paste_c(im, li, x, (y - 110 - di.height / 2 - li.height / 2 - 10) if up else (y + 90 + di.height / 2 + li.height / 2 + 10), clamp(kk))


class Progress(Base):
    def setup(self):
        self.lab = text_img(self.seg.get("label", "").upper(), font("bebas", 90), glow=self.a)
        self.sub = para_img(self.seg.get("sub", ""), font("semi", 42), 1500, fill=(230, 220, 250), align="center")
        self.ic = icon("download", 160, self.b)
        self.cache = {}

    def draw(self, im, t, gt):
        if self.seg.get("title"):
            self.heading(im, t, self.seg["title"])
        paste_c(im, self.ic, W / 2, 330 + 10 * math.sin(gt * 3))
        paste_c(im, self.lab, W / 2, 470)
        bx, by, bw, bh = 260, 560, W - 520, 70
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((bx, by, bx + bw, by + bh), 35, fill=(20, 10, 45), outline=self.b, width=4)
        p = ease_io(t / max(1.0, self.dur * 0.85)) * self.seg.get("to", 1.0)
        if p > 0.03:
            d.rounded_rectangle((bx + 8, by + 8, bx + 8 + (bw - 16) * p, by + bh - 8), 28, fill=self.a)
        tot = self.seg.get("total", 212)
        s = f"{p * tot:.0f} / {tot} GB"
        if s not in self.cache:
            self.cache[s] = text_img(s, font("bebas", 80), fill=WHITE)
        paste_c(im, self.cache[s], W / 2, by + bh + 70)
        paste_c(im, self.sub, W / 2, by + bh + 170, ease_out((t - 0.5) / 0.5))


class Quote(Base):
    full_bg = False

    def setup(self):
        self.txt = para_img(self.seg["text"], font("black", self.seg.get("size", 72)), 1500, fill=WHITE, align="center", line_gap=1.15)
        g = Image.new("RGBA", self.txt.size, self.a + (255,))
        g.putalpha(self.txt.getchannel("A").filter(ImageFilter.GaussianBlur(14)))
        out = Image.new("RGBA", (self.txt.width + 60, self.txt.height + 60), (0, 0, 0, 0))
        out.alpha_composite(g, (30, 30))
        out.alpha_composite(self.txt, (30, 30))
        self.txt = out
        self.ic = icon(self.seg.get("icon", "warn"), 150, YELLOW) if self.seg.get("icon") else None

    def draw(self, im, t, gt):
        k = ease_out(t / 0.5)
        y = 470
        if self.ic:
            paste_c(im, self.ic, W / 2, 210, k, lerp(0.5, 1, ease_back(t / 0.5)))
            y = 540
        paste_c(im, self.txt, W / 2, y, k, lerp(0.92, 1, k))


class CTA(Base):
    full_bg = True
    dim = 0.5

    def setup(self):
        self.btn = rrect(700, 150, 26, (230, 30, 50, 255))
        tx = text_img("SUSCRÍBETE", font("black", 72), fill=WHITE)
        self.btn.alpha_composite(tx, ((700 - tx.width) // 2, (150 - tx.height) // 2))
        self.btn2 = rrect(700, 150, 26, (70, 70, 80, 255))
        tx2 = text_img("SUSCRITO ✓" if False else "SUSCRITO", font("black", 72), fill=(220, 220, 220))
        self.btn2.alpha_composite(tx2, ((700 - tx2.width) // 2, (150 - tx2.height) // 2))
        self.bell = icon("star", 130, YELLOW)
        self.line = text_img(self.seg.get("text", "ACTIVA LA CAMPANA").upper(), font("bebas", 110), glow=self.a)
        self.ch = text_img(self.ctx["channel"].upper(), font("bebas", 90), fill=YELLOW, glow=ORANGE)

    def draw(self, im, t, gt):
        paste_c(im, self.line, W / 2, 220, ease_out(t / 0.4))
        b = self.btn if t < 1.6 else self.btn2
        sc = 1.0 if t < 1.4 else (0.9 if t < 1.6 else 1.0)
        paste_c(im, b, W / 2, 470, ease_out((t - 0.2) / 0.3), sc * lerp(0.6, 1, ease_back((t - 0.2) / 0.4)))
        if t > 1.7:
            paste_c(im, self.bell, W / 2 + 470, 470, 1, 1 + 0.1 * math.sin(t * 20) * max(0, 1 - (t - 1.7)))
        paste_c(im, self.ch, W / 2, 700, ease_out((t - 0.6) / 0.4))
        # cursor
        if 0.8 < t < 1.8:
            k = ease_io((t - 0.8) / 0.6)
            cx, cy = lerp(W / 2 + 500, W / 2 + 120, k), lerp(820, 500, k)
            d = ImageDraw.Draw(im)
            d.polygon([(cx, cy), (cx + 40, cy + 95), (cx + 55, cy + 55), (cx + 95, cy + 45)], fill=WHITE, outline=(0, 0, 0), width=3)


SCENES = {"hook": Hook, "title": Title, "bullets": Bullets, "stat": Stat, "compare": Compare, "map": Map,
          "char": Char, "clock": Clock, "timeline": Timeline, "progress": Progress, "quote": Quote, "cta": CTA}
