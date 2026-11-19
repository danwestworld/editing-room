# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2", "imageio-ffmpeg>=0.5,<1", "pillow>=10,<13", "opencv-python-headless>=4.9,<5", "numpy<3"]
# ///
"""One-time setup + health check for The Editing Room.

  uv run setup_check.py [--model small]

Getting here means uv already installed Python and the packages. This script then:
fetches the ffmpeg build, downloads the speech model once (~500 MB for 'small'),
and renders a 3-second test video with captions, so every tool is proven to work.
"""
import argparse, subprocess, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import er_lib as er

ok = lambda m: print(f"  OK  {m}", flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="small"); a = ap.parse_args()
    print("Checking The Editing Room setup...", flush=True)
    ok(f"Python {sys.version.split()[0]} and packages")
    ff = er.ffmpeg()
    out = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    missing = [f for f in ("silencedetect", "subtitles", "zscale", "select") if f" {f} " not in out]
    if missing:
        sys.exit(f"  FAIL  ffmpeg is missing: {', '.join(missing)}. Set EDITING_ROOM_FFMPEG to a full ffmpeg build.")
    ok("ffmpeg (video engine)")
    import cv2
    assert hasattr(cv2, "CascadeClassifier")
    ok("face finder")
    t = time.time()
    print(f"  ..  speech model '{a.model}' (first time: a few minutes to download, then never again)", flush=True)
    r = subprocess.run([sys.executable, "-c", "from faster_whisper import WhisperModel; "
                        f"WhisperModel('{a.model}', device='cpu', compute_type='int8')"])
    if r.returncode != 0:
        sys.exit("  FAIL  could not download the speech model. Check the internet connection and run setup again.")
    ok(f"speech model ready ({time.time() - t:.0f}s)")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        src = d / "test.mp4"
        er.run(["-f", "lavfi", "-i", "testsrc2=size=720x1280:rate=30:duration=3", "-f", "lavfi", "-i", "sine=frequency=300:duration=3",
                "-shortest"] + er.encode_args() + [str(src)])
        import captions as cap
        words = [{"w": w, "s": 0.3 + i * 0.5, "e": 0.75 + i * 0.5} for i, w in enumerate("the editing room works".split())]
        info = er.probe(src)
        ass, _ = cap.build_ass(words, info, cap.STYLES["bold"], "bottom", None, 1.0, None)
        cap.burn(src, d / "out.mp4", ass, d, info)
        keeps = [(0.0, 1.0), (1.5, 3.0)]
        er.render_keeps(d / "out.mp4", d / "cut.mp4", keeps, er.probe(d / "out.mp4"))
        dur = er.probe(d / "cut.mp4")["duration"]
        if abs(dur - 2.5) > 0.15:
            sys.exit(f"  FAIL  test cut came out {dur:.2f}s, expected 2.5s")
    ok("test video cut and captioned")
    print("\nAll set. The Editing Room is ready.")


if __name__ == "__main__":
    main()
