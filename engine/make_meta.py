"""Genera la ficha de subida (título, descripción con capítulos, etiquetas) de cada vídeo + kit del canal."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scripts import VIDEOS, COMMON_TAGS, DISCLAIMER
import build, gfx
from gfx import W, H, font, text_img, paste, paste_c, PINK, CYAN, YELLOW, WHITE
from PIL import Image, ImageDraw

OUT = build.OUT


def mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def label(seg):
    s = seg["s"]
    if seg.get("chap"):
        return seg["chap"]
    if s == "hook":
        return "Intro"
    if s == "title":
        return " ".join(seg["lines"]).capitalize()
    if s == "map":
        return seg.get("region") or seg.get("name")
    if s == "char":
        return seg["name"]
    if s == "cta":
        return "Final"
    if seg.get("title"):
        return seg["title"]
    if s == "stat":
        return seg["label"]
    return None


def chapters(spec):
    tl, _, _, total = build.plan_audio(spec)
    out = []
    for (st, dur, seg, marks) in tl:
        lab = label(seg)
        if not lab:
            continue
        if out and st - out[-1][0] < 10:
            continue
        if out and lab == out[-1][1]:
            continue
        out.append((st if out else 0, lab))
    if out and total - out[-1][0] < 10:
        out.pop()
    return out, total


def description(spec, chaps):
    first = spec["segments"][0]["v"]
    first = first if isinstance(first, str) else " ".join(first)
    lines = [first, ""]
    if len(chaps) >= 3:
        lines.append("⏱️ Capítulos")
        lines += [f"{mmss(t)} {l}" for t, l in chaps]
        lines.append("")
    lines += ["🔔 Suscríbete a Zona Leonida para guías, noticias y secretos de GTA 6 en español.",
              "💬 Déjanos tu opinión en los comentarios.", "", "ℹ️ " + DISCLAIMER, "",
              "#GTA6 #GTAVI #Leonida #ViceCity #GTA6Español"]
    return "\n".join(lines)


def main():
    guide = []
    for spec in VIDEOS:
        chaps, total = chapters(spec)
        desc = description(spec, chaps)
        tags = spec["tags"] + COMMON_TAGS
        # YouTube: tags field max 500 chars
        tl, acc = [], 0
        for t in tags:
            if acc + len(t) + 1 > 480:
                break
            tl.append(t)
            acc += len(t) + 1
        txt = (f"TÍTULO:\n{spec['title']}\n\nDESCRIPCIÓN:\n{desc}\n\nETIQUETAS:\n{', '.join(tl)}\n\n"
               f"MINIATURA: {spec['id']}_miniatura.jpg\nSUBTÍTULOS: {spec['id']}.srt (idioma: Español)\n"
               f"CATEGORÍA: Videojuegos · Juego: Grand Theft Auto VI\nDURACIÓN: {mmss(total)}\n")
        with open(os.path.join(OUT, f"{spec['id']}_ficha.txt"), "w") as f:
            f.write(txt)
        guide.append((spec, total))
        print(spec["id"], mmss(total), len(chaps), "capítulos")
    # channel kit
    kit = os.path.join(OUT, "..", "canal")
    os.makedirs(kit, exist_ok=True)
    bd = gfx.Backdrop("sunset", seed=7)
    big = bd.frame(1.5).resize((2560, 1440), Image.LANCZOS)
    t1 = text_img("ZONA LEONIDA", font("bebas", 250), fill=WHITE, stroke=5, stroke_fill=PINK, glow=PINK, glow_r=20)
    t2 = text_img("TODO GTA 6 EN ESPAÑOL · GUÍAS · NOTICIAS · SECRETOS", font("black", 52), fill=YELLOW, stroke=4, stroke_fill=(0, 0, 0))
    paste_c(big, t1, 1280, 640)
    paste_c(big, t2, 1280, 800)
    big.convert("RGB").save(os.path.join(kit, "banner_2560x1440.jpg"), quality=92)
    av = gfx.Backdrop("night", seed=3).frame(2).crop((W // 2 - 540, 0, W // 2 + 540, 1080)).resize((800, 800))
    zl = text_img("ZL", font("bebas", 520), fill=WHITE, stroke=8, stroke_fill=CYAN, glow=CYAN, glow_r=24)
    paste_c(av, zl, 400, 420)
    m = Image.new("L", (800, 800), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 800, 800), fill=255)
    av.putalpha(m)
    av.save(os.path.join(kit, "avatar_800x800.png"))
    wm = text_img("ZL", font("bebas", 140), fill=WHITE, stroke=4, stroke_fill=PINK)
    w2 = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    paste_c(w2, wm, 75, 75)
    w2.save(os.path.join(kit, "marca_de_agua_150x150.png"))


if __name__ == "__main__":
    main()
