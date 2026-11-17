import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scripts import VIDEOS
import build, gfx
from scenes import SCENES
from PIL import Image
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/claude-0/prev/sheets"
os.makedirs(out, exist_ok=True)
for spec in VIDEOS:
    if sys.argv[1] not in ("all", spec["id"]): continue
    tl, vt, caps, total = build.plan_audio(spec)
    th = gfx.THEMES[spec["theme"]]
    bd = gfx.Backdrop(spec["theme"], seed=hash(spec["id"]) % 50)
    ctx = dict(a=th["a"], b=th["b"], backdrop=bd, soft=gfx.SoftBG(bd), channel=build.CHANNEL)
    ov = build.Overlay(ctx)
    tiles = []
    for (st, dur, seg, marks) in tl:
        sc = SCENES[seg["s"]](seg, dur, ctx, marks)
        lt = dur - 0.6
        im = sc.bg(lt, st + lt); sc.draw(im, lt, st + lt); ov.draw(im, st + lt, total, caps, lt)
        tiles.append(im.convert("RGB").resize((640, 360)))
    cols = 3; rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (640 * cols, 360 * rows))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(f"{out}/{spec['id']}.jpg", quality=80)
    print(spec["id"], f"{total:.0f}s", len(tl), "segs", flush=True)
