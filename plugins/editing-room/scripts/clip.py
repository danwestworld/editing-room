# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2", "imageio-ffmpeg>=0.5,<1", "pillow>=10,<13", "opencv-python-headless>=4.9,<5", "numpy<3"]
# ///
"""Shorts Clipper: cut one moment into a vertical 9:16 Short with captions.

  uv run clip.py VIDEO --start 1:02.5 --end 1:48 [--name "best bit"] [--style bold]
                       [--color FFD400] [--position bottom] [--crop auto|center|none] [--loose]

--start/--end: seconds or m:ss. They snap to the nearest word so no word is clipped.
--crop auto: follows the face (median position), center: middle, none: fit with blurred bars.
Pauses inside the clip are tightened unless --loose.
Writes 'shorts/<name>.mp4' (+ a .jpg still) inside the Editing Room folder.
"""
import argparse, statistics, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import er_lib as er
import captions as cap

OUT_W, OUT_H = 1080, 1920


def parse_t(x):
    parts = [float(p) for p in str(x).split(":")]
    t = 0.0
    for p in parts:
        t = t * 60 + p
    return t


def face_x(video, info):
    """Median horizontal face centre (0..1), from 2 frames per second. None if no face found."""
    import cv2
    casc = er.cascade("haarcascade_frontalface_default.xml")
    xs = []
    with tempfile.TemporaryDirectory() as td:
        er.run(["-i", str(video), "-vf", "fps=2,scale=480:-2", "-q:v", "4", str(Path(td) / "f%04d.jpg")])
        for f in sorted(Path(td).glob("*.jpg")):
            g = cv2.cvtColor(er.imread(f), cv2.COLOR_BGR2GRAY)
            faces = casc.detectMultiScale(g, 1.1, 6, minSize=(g.shape[0] // 10, g.shape[0] // 10))
            if len(faces):
                x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
                xs.append((x + w / 2) / g.shape[1])
    return statistics.median(xs) if len(xs) >= 2 else None


def frame_filter(info, crop, video):
    W, H = info["width"], info["height"]
    if W / H <= OUT_W / OUT_H + 0.01:                       # already vertical: just fit
        return f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H}", "vertical source"
    if crop == "none":
        return (f"split[a][b];[a]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H},"
                f"boxblur=30:5[bg];[b]scale={OUT_W}:-2[fg];[bg][fg]overlay=0:(H-h)/2"), "fit with blurred bars"
    cw = int(H * OUT_W / OUT_H) // 2 * 2
    cx = face_x(video, info) if crop == "auto" else None
    how = f"face at {cx:.0%} across" if cx is not None else "centre (no face found)"
    cx = 0.5 if cx is None else cx
    x = int(min(max(cx * W - cw / 2, 0), W - cw))
    return f"crop={cw}:{H}:{x}:0,scale={OUT_W}:{OUT_H}", how


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--out")
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--name")
    ap.add_argument("--style", default="bold", choices=list(cap.STYLES))
    ap.add_argument("--color"); ap.add_argument("--position", default="bottom", choices=["bottom", "middle", "top"])
    ap.add_argument("--words", type=int); ap.add_argument("--size", type=float, default=1.0)
    ap.add_argument("--crop", default="auto", choices=["auto", "center", "none"])
    ap.add_argument("--loose", action="store_true", help="keep the pauses inside the clip")
    a = ap.parse_args()

    video = er.check_video(a.video)
    d = er.workdir(video, a.out)
    info = er.probe(video)
    s, e = parse_t(a.start), parse_t(a.end)
    words = er.ensure_words(video, d)
    inside = [w for w in words if w["s"] >= s - 0.4 and w["e"] <= e + 0.4]
    if inside:                                              # snap to whole words
        s = max(0.0, inside[0]["s"] - 0.08)
        e = min(info["duration"], inside[-1]["e"] + 0.25)
    if e - s < 3:
        sys.exit("Clip is shorter than 3 seconds. Check --start and --end.")
    if e - s > 180:
        print("Warning: over 3 minutes. YouTube won't treat it as a Short.")
    import re
    name = re.sub(r"[^\w ,.'!&()-]", "", a.name or "").strip(" .") or f"short {er.ts(s).replace(':', '.')}"
    shorts = d / "shorts"; shorts.mkdir(exist_ok=True)
    tmp = d / f"_clip - {name}.mp4"

    # 1. Cut the moment out (accurate seek, HDR → SDR), 2. tighten its pauses.
    raw = d / f"_raw - {name}.mp4"
    er.run(["-ss", f"{s:.3f}", "-i", str(video), "-t", f"{e - s:.3f}", "-vf", f"{er.tonemap_chain(info)}fps={er.out_fps(info)}",
            "-map", "0:v:0", "-map", "0:a?"] + er.encode_args(16) + [str(raw)])
    rinfo = er.probe(raw)
    if a.loose:
        raw.replace(tmp)
    else:
        sil = er.silences(raw, min_len=0.35)
        cuts = [(0.0 if s0 <= 0.05 else s0 + 0.1, rinfo["duration"] if e0 >= rinfo["duration"] - 0.05 else e0 - 0.1)
                for s0, e0 in sil]
        keeps = er.keeps_from_cuts([c for c in cuts if c[1] - c[0] > 0.1], rinfo["duration"])
        er.render_keeps(raw, tmp, keeps, rinfo, crf=16)
        raw.unlink(missing_ok=True)

    # 3. Vertical frame + captions in one pass.
    tinfo = er.probe(tmp)
    vf, how = frame_filter(tinfo, a.crop, tmp)
    cwords = cap.clean_words(er.ensure_words(tmp, d))
    out = shorts / f"{name}.mp4"
    if out.resolve() == video:
        sys.exit("That name would overwrite your original video. Pick another --name.")
    vinfo = dict(tinfo, width=OUT_W, height=OUT_H)
    ass, srt = cap.build_ass(cwords, vinfo, cap.STYLES[a.style], a.position, a.words, a.size, a.color)
    cap.burn(tmp, out, ass, d, dict(tinfo, hdr=False), extra_vf=vf)
    tmp.unlink(missing_ok=True)
    oinfo = er.probe(out)
    er.run(["-ss", f"{oinfo['duration'] / 3:.2f}", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(out.with_suffix(".jpg"))])
    print(f"Still for checking: {out.with_suffix('.jpg')}")
    print(f"Done: {out}\n{er.ts(er.probe(out)['duration'])} long, framing: {how}.")


if __name__ == "__main__":
    main()
