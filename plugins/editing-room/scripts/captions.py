# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2", "imageio-ffmpeg>=0.5,<1", "pillow>=10,<13", "opencv-python-headless>=4.9,<5", "numpy<3"]
# ///
"""Caption Print: word-by-word captions burned into the video, plus an .srt file for YouTube.

  uv run captions.py VIDEO [--style bold|clean|boxed|punch] [--color FFD400]
                           [--position bottom|middle|top] [--words 3] [--size 1.0] [--out DIR]
  uv run captions.py VIDEO --styles-preview      (one still per style, to pick from)

Writes '<name> - captions.mp4' and '<name>.srt' into the Editing Room folder.
Transcribes the video first if needed. Works on vertical and horizontal video.
"""
import argparse, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import er_lib as er

STYLES = {
    #        font                  text      active    outline   border  out  shadow upper words(v,h) active-scale
    "bold":  dict(font="Poppins ExtraBold", text="FFFFFF", hl="FFD400", edge="000000", box=False, out=5, shadow=2, upper=True,  words=(3, 4), pop=112),
    "clean": dict(font="Poppins ExtraBold", text="B3B3B3", hl="FFFFFF", edge="000000", box=False, out=0, shadow=3, upper=False, words=(5, 7), pop=100),
    "boxed": dict(font="Poppins ExtraBold", text="FFFFFF", hl="FFD400", edge="111111", box=True,  out=14, shadow=0, upper=False, words=(4, 6), pop=100),
    "punch": dict(font="Anton",             text="FFFFFF", hl="3CFF6E", edge="000000", box=False, out=6, shadow=3, upper=True,  words=(2, 3), pop=118),
}


def ass_color(hexrgb, alpha="00"):
    h = hexrgb.strip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", h):
        sys.exit(f"Colour must be 6 hex digits like FFD400, got {hexrgb}")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}&"


def ass_time(t):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def srt_time(t):
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def groups(words, per_line, max_gap=0.6):
    """Split words into short caption lines: break on a pause, at sentence ends, or at N words."""
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= per_line or w["s"] - cur[-1]["e"] > max_gap or re.search(r"[.?!]$", cur[-1]["w"])):
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def clean_words(words):
    ws = [dict(w) for w in words if not er.is_filler(w["w"])]
    for i, w in enumerate(ws):            # Whisper ends stretch over pauses: cap each word
        nxt = ws[i + 1]["s"] if i + 1 < len(ws) else w["e"]
        w["e"] = min(w["e"], max(nxt, w["s"] + 0.05), w["s"] + 1.2)
    return ws


def build_ass(words, info, st, position, per_line, size, color):
    W, H = info["width"], info["height"]
    vertical = H > W
    fs = int((0.085 * W if vertical else 0.058 * H) * size * (1.12 if st["font"] == "Anton" else 1.0))
    margin_v = {"bottom": int(H * (0.22 if vertical else 0.08)), "middle": 0, "top": int(H * 0.12)}[position]
    align = {"bottom": 2, "middle": 5, "top": 8}[position]
    hl = ass_color(color or st["hl"])
    base = ass_color(st["text"])
    edge = ass_color(st["edge"], "30" if st["box"] else "00")
    border_style = 3 if st["box"] else 1
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['font']},{fs},{base},{base},{edge},&H80000000&,0,0,0,0,100,100,0,0,{border_style},{max(1, int(st['out'] * fs / 80)) if st['out'] else 0},{st['shadow']},{align},{int(W*0.06)},{int(W*0.06)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, srt = [], []
    gs = groups(words, per_line or st["words"][0 if vertical else 1])
    for gi, g in enumerate(gs):
        g_end = g[-1]["e"] + 0.25
        if gi + 1 < len(gs):
            g_end = min(g_end, gs[gi + 1][0]["s"])
        txt = [w["w"].upper() if st["upper"] else w["w"] for w in g]
        if st["upper"]:
            txt = [re.sub(r"[,.]$", "", t) for t in txt]
        for i, w in enumerate(g):
            s = w["s"] if i == 0 else g[i - 1]["e"] if g[i - 1]["e"] < w["s"] else w["s"]
            s = min(s, w["s"])
            e = g[i + 1]["s"] if i + 1 < len(g) else g_end
            parts = []
            for j, t in enumerate(txt):
                if j == i:
                    pop = f"\\fscx{st['pop']}\\fscy{st['pop']}" if st["pop"] != 100 else ""
                    parts.append(f"{{\\c{hl}{pop}}}{t}{{\\c{base}\\fscx100\\fscy100}}")
                else:
                    parts.append(t)
            lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(max(e, s + 0.05))},Cap,,0,0,0,,{' '.join(parts)}")
        srt.append(f"{len(srt) + 1}\n{srt_time(g[0]['s'])} --> {srt_time(g_end)}\n{' '.join(w['w'] for w in g)}\n")
    return head + "\n".join(lines) + "\n", "\n".join(srt)


def burn(video, out, ass_text, d, info, extra_vf=""):
    """Burn an ASS file. Runs ffmpeg inside the folder so no path ever needs escaping (Windows-safe)."""
    er.copy_fonts(d)
    (d / "_captions.ass").write_text(ass_text, encoding="utf-8")
    vf = f"{er.tonemap_chain(info)}{extra_vf + ',' if extra_vf else ''}scale=trunc(iw/2)*2:trunc(ih/2)*2,subtitles=_captions.ass:fontsdir=fonts"
    er.run(["-i", str(video), "-vf", vf, "-map", "0:v:0", "-map", "0:a?"] + er.encode_args(18) + [str(out)], cwd=d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--out")
    ap.add_argument("--style", default="bold", choices=list(STYLES))
    ap.add_argument("--color", help="highlight colour, hex like FFD400")
    ap.add_argument("--position", default="bottom", choices=["bottom", "middle", "top"])
    ap.add_argument("--words", type=int, help="words per caption line")
    ap.add_argument("--size", type=float, default=1.0, help="1.0 = default, 1.2 = 20%% bigger")
    ap.add_argument("--styles-preview", action="store_true")
    a = ap.parse_args()
    video = er.check_video(a.video)
    d = er.workdir(video, a.out)
    info = er.probe(video)
    words = clean_words(er.ensure_words(video, d))
    if not words:
        sys.exit("No speech found in this video, so there is nothing to caption.")

    if a.styles_preview:
        # Freeze on the middle of a line with 3+ words so each still shows a highlighted word.
        mid = next((g for g in groups(words, 3) if len(g) >= 3 and g[0]["s"] > info["duration"] * 0.2), groups(words, 3)[0])
        w1 = mid[min(1, len(mid) - 1)]
        t = (w1["s"] + w1["e"]) / 2
        er.copy_fonts(d)
        for name, st in STYLES.items():
            ass, _ = build_ass(words, info, st, a.position, a.words, a.size, a.color)
            (d / "_captions.ass").write_text(ass, encoding="utf-8")
            outp = d / f"style - {name}.jpg"
            er.run(["-ss", f"{t:.2f}", "-copyts", "-i", str(video), "-vf",
                    f"{er.tonemap_chain(info)}subtitles=_captions.ass:fontsdir=fonts,scale='min(1280,iw)':-2",
                    "-frames:v", "1", "-q:v", "3", str(outp)], cwd=d)
            print(f"{name}: {outp}")
        return

    ass, srt = build_ass(words, info, STYLES[a.style], a.position, a.words, a.size, a.color)
    (d / f"{video.stem}.srt").write_text(srt, encoding="utf-8")
    out = d / f"{video.stem} - captions.mp4"
    print(f"Burning '{a.style}' captions into {er.ts(info['duration'])} of video...", flush=True)
    burn(video, out, ass, d, info)
    still = out.with_suffix(".jpg")
    er.run(["-ss", f"{info['duration'] / 2:.2f}", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(still)])
    print(f"Still for checking: {still}")
    print(f"Done: {out}\nSubtitle file for YouTube: {d / (video.stem + '.srt')}")


if __name__ == "__main__":
    main()
