# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2", "imageio-ffmpeg>=0.5,<1", "pillow>=10,<13", "opencv-python-headless>=4.9,<5", "numpy<3"]
# ///
"""Packaging Pick: best face frames from the video, then 1280x720 YouTube thumbnails.

  uv run thumbs.py frames VIDEO [--count 8] [--out DIR]
      → thumbs/frame 1..N.jpg + thumbs/frames sheet.jpg (numbered, to pick from)
  uv run thumbs.py make FRAME --text "I QUIT MY *JOB*" [--style punch|box|clean]
                       [--accent FFD400] [--side auto|left|right] [--name "option 1"]
      → thumbs/<name>.jpg   (*word* = accent colour)
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import er_lib as er

TW, TH = 1280, 720


# ---------- frames ----------
def score_frames(video, info, n_samples=60):
    import cv2
    fc = er.cascade("haarcascade_frontalface_default.xml")
    ec = er.cascade("haarcascade_eye.xml")
    dur = info["duration"]
    times = [dur * (0.03 + 0.94 * i / (n_samples - 1)) for i in range(n_samples)]
    rows = []
    with tempfile.TemporaryDirectory() as td:
        step = max(dur * 0.94 / n_samples, 0.2)
        er.run(["-ss", f"{dur * 0.03:.2f}", "-i", str(video), "-vf",
                f"{er.tonemap_chain(info)}fps=1/{step:.3f},scale=640:-2", "-frames:v", str(n_samples), "-q:v", "3",
                str(Path(td) / "s%03d.jpg")])
        for i, f in enumerate(sorted(Path(td).glob("*.jpg"))):
            t = dur * 0.03 + i * step
            im = er.imread(f); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            faces = fc.detectMultiScale(g, 1.1, 6, minSize=(g.shape[0] // 8, g.shape[0] // 8))
            if not len(faces):
                continue
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            roi = g[y:y + h, x:x + w]
            sharp = cv2.Laplacian(roi, cv2.CV_64F).var()
            eyes = ec.detectMultiScale(roi[: h // 2 + h // 6], 1.1, 5, minSize=(w // 10, w // 10))
            bright = roi.mean()
            s = (min(h / g.shape[0], 0.45) * 100 + min(sharp, 400) / 8 + (25 if len(eyes) >= 2 else 0)
                 - abs(bright - 140) / 4)
            rows.append((s, t))
    return rows


def frames(a):
    video = er.check_video(a.video)
    d = er.workdir(video, a.out); td = d / "thumbs"; td.mkdir(exist_ok=True)
    info = er.probe(video)
    rows = sorted(score_frames(video, info), reverse=True)
    if not rows:
        sys.exit("No face found in the sampled frames. Pick a moment yourself and run `make` on a still from it.")
    picked, gap = [], info["duration"] * 0.04
    for s, t in rows:
        if all(abs(t - p) > gap for p in picked):
            picked.append(t)
        if len(picked) == a.count:
            break
    picked.sort()
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(er.FONTS / "Anton-Regular.ttf"), 44)
    cells = []
    for i, t in enumerate(picked, 1):
        p = td / f"frame {i}.jpg"
        er.run(["-ss", f"{t:.2f}", "-i", str(video), "-vf", f"{er.tonemap_chain(info)}null", "-frames:v", "1", "-q:v", "2", str(p)])
        im = Image.open(p).convert("RGB"); im.thumbnail((480, 480))
        ImageDraw.Draw(im).text((12, 6), str(i), font=font, fill="#FFD400", stroke_width=4, stroke_fill="black")
        cells.append(im)
        print(f"frame {i}: {p}  (at {er.ts(t)})")
    cw = max(c.width for c in cells); ch = max(c.height for c in cells); cols = 4
    sheet = Image.new("RGB", (cw * cols, ch * ((len(cells) + cols - 1) // cols)), "black")
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(td / "frames sheet.jpg", quality=85)
    print(f"Sheet: {td / 'frames sheet.jpg'}")


# ---------- make ----------
def face_box(im):
    import cv2, numpy as np
    g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    fc = er.cascade("haarcascade_frontalface_default.xml")
    f = fc.detectMultiScale(g, 1.1, 6, minSize=(g.shape[0] // 10, g.shape[0] // 10))
    return tuple(max(f, key=lambda r: r[2] * r[3])) if len(f) else None


def base_canvas(im, side):
    """16:9 canvas with the person on the side away from the text."""
    from PIL import Image, ImageFilter, ImageEnhance
    W, H = im.size
    fb = face_box(im)
    fx = (fb[0] + fb[2] / 2) / W if fb else 0.5
    if side == "auto":
        side = "right" if fx < 0.5 else "left"     # text goes where the face is not
    if W / H >= 1.6:                               # horizontal frame: fill, nudge face away from text
        scale = max(TW / W, TH / H) * 1.12
        im2 = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
        cx = fx * im2.width
        target = TW * (0.72 if side == "left" else 0.28)
        x = int(min(max(cx - target, 0), im2.width - TW))
        fy = (fb[1] + fb[3] * 0.4) / H if fb else 0.4
        y = int(min(max(fy * im2.height - TH * 0.42, 0), im2.height - TH))
        canvas = im2.crop((x, y, x + TW, y + TH))
    else:                                          # vertical/phone frame: person panel + blurred fill
        bg = im.resize((TW, int(TW * H / W)), Image.LANCZOS)
        bg = bg.crop((0, (bg.height - TH) // 2, TW, (bg.height - TH) // 2 + TH)).filter(ImageFilter.GaussianBlur(40))
        canvas = ImageEnhance.Brightness(bg).enhance(0.55)
        ph = TH; pw = int(W * ph / H)
        panel = im.resize((pw, ph), Image.LANCZOS)
        if pw > TW * 0.5:                          # crop panel around the face
            cxp = fx * pw; cw = int(TW * 0.5)
            x = int(min(max(cxp - cw / 2, 0), pw - cw)); panel = panel.crop((x, 0, x + cw, ph)); pw = cw
        canvas.paste(panel, (TW - pw - 20 if side == "left" else 20, 0))
    canvas = ImageEnhance.Contrast(canvas).enhance(1.12)
    canvas = ImageEnhance.Color(canvas).enhance(1.15)
    return canvas, side


def tokens(text):
    """'I QUIT MY *JOB*' → [('I', False), ('QUIT', False), ('MY', False), ('JOB', True)]"""
    out = []
    for m in re.finditer(r"\*([^*]+)\*|(\S+)", text.upper()):
        if m[1]:
            out += [(w, True) for w in m[1].split()]
        else:
            out.append((m[2], False))
    return out


def layout(toks, font_path, box_w, box_h, max_lines=3):
    from PIL import ImageFont
    for size in range(190, 40, -6):
        f = ImageFont.truetype(font_path, size)
        space = f.getlength(" ")
        lines, cur, cur_w = [], [], 0
        for w, acc in toks:
            ww = f.getlength(w)
            if cur and cur_w + space + ww > box_w:
                lines.append(cur); cur, cur_w = [], 0
            cur.append((w, acc, ww)); cur_w += (space if len(cur) > 1 else 0) + ww
        if cur:
            lines.append(cur)
        line_h = int(size * 1.08)
        if len(lines) <= max_lines and line_h * len(lines) <= box_h and all(sum(x[2] for x in l) + space * (len(l) - 1) <= box_w for l in lines):
            return f, lines, line_h, space
    sys.exit("Text too long for a thumbnail. Use 2-5 words.")


def make(a):
    from PIL import Image, ImageDraw
    src = Path(a.frame).expanduser()
    if not src.is_file():
        sys.exit(f"Frame not found: {src}")
    room = next((p for p in src.resolve().parents if p.name.endswith(" - Editing Room")), None)
    td = (room / "thumbs") if room else er.workdir(src) / "thumbs"
    td.mkdir(exist_ok=True)
    im = Image.open(src).convert("RGB")
    canvas, side = base_canvas(im, a.side)
    accent = "#" + a.accent.strip("#")
    toks = tokens(a.text)
    box_w, box_h = int(TW * 0.5), int(TH * 0.78)
    x0 = 50 if side == "left" else TW - box_w - 50
    font, lines, lh, space = layout(toks, str(er.FONTS / "Anton-Regular.ttf"), box_w, box_h)
    total_h = lh * len(lines)
    y = (TH - total_h) // 2 - 10

    if a.style == "clean":                          # dark fade under the text side
        grad = Image.new("L", (TW, 1))
        for x in range(TW):
            t = x / TW if side == "right" else 1 - x / TW
            grad.putpixel((x, 0), int(200 * max(0.0, (t - 0.35) / 0.65)))
        canvas = Image.composite(Image.new("RGB", (TW, TH), "black"), canvas, grad.resize((TW, TH)))
    draw = ImageDraw.Draw(canvas)
    for line in lines:
        lw = sum(w[2] for w in line) + space * (len(line) - 1)
        x = x0 if side == "left" else x0 + box_w - lw
        if a.style == "box":
            draw.rectangle((x - 18, y - 4, x + lw + 18, y + lh - 2), fill=accent)
        for w, acc, ww in line:
            if a.style == "box":
                draw.text((x, y - lh * 0.04), w, font=font, fill="black")
            elif a.style == "clean":
                draw.text((x, y), w, font=font, fill=accent if acc else "white")
            else:
                draw.text((x + 6, y + 8), w, font=font, fill=(0, 0, 0))
                draw.text((x, y), w, font=font, fill=accent if acc else "white", stroke_width=max(4, font.size // 18), stroke_fill="black")
            x += ww + space
        y += lh + (14 if a.style == "box" else 0)
    name = a.name or re.sub(r"[^\w -]", "", a.text.replace("*", ""))[:40].strip() or "thumbnail"
    out = td / f"{name}.jpg"
    canvas.save(out, quality=92)
    print(f"Thumbnail: {out}  ({a.style}, text on the {side})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("frames"); p1.add_argument("video"); p1.add_argument("--out"); p1.add_argument("--count", type=int, default=8)
    p2 = sub.add_parser("make"); p2.add_argument("frame"); p2.add_argument("--text", required=True)
    p2.add_argument("--style", default="punch", choices=["punch", "box", "clean"])
    p2.add_argument("--accent", default="FFD400"); p2.add_argument("--side", default="auto", choices=["auto", "left", "right"])
    p2.add_argument("--name")
    a = ap.parse_args()
    frames(a) if a.cmd == "frames" else make(a)
