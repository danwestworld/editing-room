"""Shared helpers for The Editing Room scripts. Imported by every tool script.

Everything runs on the ffmpeg binary that the imageio-ffmpeg wheel ships, so buyers
never install ffmpeg by hand. Set EDITING_ROOM_FFMPEG to use another ffmpeg.
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

for _st in (sys.stdout, sys.stderr):          # Windows consoles default to cp1252: never crash on "→" or "é"
    try:
        _st.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
os.environ.setdefault("PYTHONUTF8", "1")      # child processes (transcribe.py) too
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
os.environ.setdefault("CT2_VERBOSE", "-1")  # hide ctranslate2 tips (e.g. the MPS one)
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FONTS = PLUGIN_ROOT / "assets" / "fonts"
HDR_TRANSFERS = ("arib-std-b67", "smpte2084")
FILLERS = {"um", "umm", "ummm", "uh", "uhh", "uhm", "er", "erm", "ah", "ahh", "hmm", "mm", "mhm", "eh"}


def ffmpeg():
    env = os.environ.get("EDITING_ROOM_FFMPEG")
    if env:
        return env
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args, cwd=None, quiet=True):
    """Run ffmpeg with args. Raise with the last stderr lines on failure."""
    cmd = [ffmpeg(), "-hide_banner", "-nostdin", "-y"] + (["-loglevel", "error"] if quiet else []) + list(args)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    if p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-15:])
        sys.exit(f"ffmpeg failed:\n{tail}")
    return p


def probe(path):
    """Duration, display size (after rotation), fps, audio, HDR, parsed from `ffmpeg -i`."""
    p = subprocess.run([ffmpeg(), "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace")
    err = p.stderr
    if "Invalid data" in err or "No such file" in err:
        sys.exit(f"Can't read this file as a video: {path}")
    info = {"duration": 0.0, "width": 0, "height": 0, "fps": 30.0, "has_audio": " Audio:" in err, "hdr": False}
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if m:
        info["duration"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    vline = next((l for l in err.splitlines() if " Video:" in l and "attached pic" not in l), "")
    m = re.search(r", (\d{2,5})x(\d{2,5})", vline)
    if m:
        info["width"], info["height"] = int(m[1]), int(m[2])
    m = re.search(r"([\d.]+) fps", vline) or re.search(r"([\d.]+) tbr", vline)
    if m:
        info["fps"] = float(m[1])
    info["hdr"] = any(t in vline for t in HDR_TRANSFERS)
    rot = re.search(r"rotation of (-?[\d.]+) degrees", err) or re.search(r"rotate\s*:\s*(-?\d+)", err)
    if rot and abs(round(float(rot[1]))) % 180 == 90:
        info["width"], info["height"] = info["height"], info["width"]
    return info


def out_fps(info):
    """Constant output frame rate: 24/25/30/50/60 nearest to the source, never above 60."""
    f = info["fps"] or 30.0
    return min((24, 25, 30, 50, 60), key=lambda c: abs(c - f))


def tonemap_chain(info):
    """iPhone HDR (HLG/PQ) → normal SDR so colours don't look washed out on YouTube."""
    if not info["hdr"]:
        return ""
    return ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


def encode_args(crf=20):
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]


def workdir(video, out=None):
    """Output folder next to the video: '<name> - Editing Room/'.
    A video that already sits in such a folder (a cut, a clip) keeps using that folder."""
    v = Path(video).resolve()
    if out:
        d = Path(out).resolve()
    elif v.parent.name.endswith(" - Editing Room"):
        d = v.parent
    else:
        d = v.parent / f"{v.stem} - Editing Room"
    d.mkdir(parents=True, exist_ok=True)
    return d


def words_path(video, d):
    """words.json for the original video, 'words - <name>.json' for files made inside the folder."""
    v = Path(video).resolve()
    return Path(d) / ("words.json" if v.parent != Path(d).resolve() else f"words - {v.stem}.json")


def ensure_words(video, d, model="small"):
    """Transcribe in a child process: Whisper's video library and OpenCV clash in one process on Mac."""
    p = words_path(video, d)
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("transcribe.py")), str(video),
                        "--out", str(d), "--model", model])
    if r.returncode != 0 or not p.exists():
        sys.exit("Transcription failed (see the message above).")
    return load_words(p)


def check_video(video):
    v = Path(video).expanduser()
    if not v.is_file():
        sys.exit(f"File not found: {v}")
    return v.resolve()


def load_words(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["words"] if isinstance(data, dict) else data


def norm(w):
    return re.sub(r"[^a-z']", "", w.lower())


def is_filler(w):
    return norm(w) in FILLERS


def copy_fonts(dest):
    d = Path(dest) / "fonts"
    d.mkdir(exist_ok=True)
    for f in FONTS.glob("*.ttf"):
        if not (d / f.name).exists():
            shutil.copy(f, d / f.name)
    return d


def ts(sec, ms=False):
    sec = max(0.0, sec)
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    base = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    return base + (f".{int((sec % 1) * 10)}" if ms else "")


def silences(video, noise="-32dB", min_len=0.4):
    """[(start, end)] of quiet stretches, via ffmpeg silencedetect."""
    p = subprocess.run([ffmpeg(), "-hide_banner", "-nostdin", "-i", str(video), "-vn",
                        "-af", f"silencedetect=noise={noise}:d={min_len}", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    if len(ends) < len(starts):
        ends.append(probe(video)["duration"])
    return [(max(0.0, s), e) for s, e in zip(starts, ends)]


def imread(path):
    """cv2.imread fails on non-ASCII paths on Windows (C:\\Users\\José\\...). Decode from bytes."""
    import cv2, numpy as np
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def cascade(name):
    """Haar face/eye detector loaded from memory, so a non-ASCII install path can't break it."""
    import cv2
    xml = (Path(cv2.data.haarcascades) / name).read_text(encoding="utf-8")
    fs = cv2.FileStorage(xml, cv2.FILE_STORAGE_READ | cv2.FILE_STORAGE_MEMORY)
    c = cv2.CascadeClassifier()
    if not c.read(fs.getFirstTopLevelNode()):
        c = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / name))
    if c.empty():
        sys.exit(f"Could not load the face finder ({name}). Run /editing-room:setup.")
    return c


def merge(spans, gap=0.0):
    out = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1] + gap:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def keeps_from_cuts(cuts, duration):
    keeps, cur = [], 0.0
    for s, e in merge(cuts):
        if s > cur:
            keeps.append((cur, s))
        cur = max(cur, e)
    if cur < duration:
        keeps.append((cur, duration))
    return [(s, e) for s, e in keeps if e - s > 0.05]


def render_keeps(src, out, keeps, info, extra_vf="", crf=20):
    """Join the keep spans. Spans snap to the output frame grid and audio runs in 1 ms frames,
    so each span keeps exactly as much audio as video and nothing drifts.

    Up to CHUNK spans go in one streaming pass. More spans (long videos) render in chunks,
    each seeking to its own range, then join once: the select expression stays short, so
    a 60-minute video with 1,000 cuts renders in minutes, not hours.
    """
    CHUNK = 60
    fps = out_fps(info)
    snap = lambda t: round(t * fps) / fps
    spans = [(snap(s), snap(e)) for s, e in keeps]
    spans = [(s, e) for s, e in spans if e > s]
    if not spans:
        sys.exit("Nothing would be left after cutting. Keep some of the cuts and try again.")
    if len(spans) <= CHUNK:
        _render_spans(src, out, spans, 0.0, None, info, fps, extra_vf, crf, final=True)
        return sum(e - s for s, e in spans)
    out = Path(out)
    parts, lst = [], out.with_name(out.stem + ".parts.txt")
    try:
        for i in range(0, len(spans), CHUNK):
            ch = spans[i:i + CHUNK]
            part = out.with_name(f"{out.stem}.part{i // CHUNK:03d}.mkv")
            _render_spans(src, part, ch, ch[0][0], ch[-1][1], info, fps, extra_vf, crf, final=False)
            parts.append(part)
            print(f"  ...{min(i + CHUNK, len(spans))}/{len(spans)} pieces", flush=True)
        lst.write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
        a_args = ["-c:a", "aac", "-b:a", "192k"] if info["has_audio"] else []
        run(["-f", "concat", "-safe", "0", "-i", lst.name, "-c:v", "copy"] + a_args +
            ["-movflags", "+faststart", str(out.resolve())], cwd=out.parent)
    finally:
        for p in parts + [lst]:
            Path(p).unlink(missing_ok=True)
    return sum(e - s for s, e in spans)


def _render_spans(src, out, spans, t0, t1, info, fps, extra_vf, crf, final):
    """One pass over [t0, t1] of the source. Video ends with even dimensions (x264 needs them).
    Chunk parts keep audio as PCM in .mkv so joining them adds no AAC padding at the seams."""
    sel = lambda half: "+".join(f"between(t\\,{s - t0 - half:.4f}\\,{e - t0 - half:.4f})" for s, e in spans)
    tail = (f",{extra_vf}" if extra_vf else "") + ",scale=trunc(iw/2)*2:trunc(ih/2)*2"
    graph = [f"[0:v]setpts=PTS-STARTPTS,{tonemap_chain(info)}fps={fps},select='{sel(0.5 / fps)}',setpts=N/{fps}/TB{tail}[v]"]
    maps = ["-map", "[v]"]
    if info["has_audio"]:
        graph.append(f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,asetnsamples=n=48:p=0,aselect='{sel(0.0005)}',asetpts=N/SR/TB[a]")
        maps += ["-map", "[a]"]
    script = Path(out).with_suffix(".filter.txt")
    script.write_text(";\n".join(graph), encoding="utf-8")
    seek = ["-ss", f"{t0:.4f}", "-to", f"{t1 + 0.5:.4f}"] if t1 is not None else []
    if final:
        enc = encode_args(crf)
    else:
        enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(fps),
               "-c:a", "pcm_s16le", "-ar", "48000"]
    try:
        run(seek + ["-i", str(src), "-/filter_complex", str(script)] + maps + enc + [str(out)])
    finally:
        script.unlink(missing_ok=True)
