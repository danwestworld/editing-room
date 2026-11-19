# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2", "imageio-ffmpeg>=0.5,<1", "pillow>=10,<13", "opencv-python-headless>=4.9,<5", "numpy<3"]
# ///
"""Word-level transcript of a video, on this computer (faster-whisper, no API key).

  uv run transcribe.py VIDEO [--out DIR] [--model small] [--lang en] [--force]

Writes into DIR (default '<video> - Editing Room/'):
  words.json      every word with start/end seconds (fillers like "um" kept on purpose)
  transcript.txt  one line per sentence, "[mm:ss] text"
Re-running on the same unchanged file reuses the result.
"""
import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import er_lib as er

# Whisper drops "um"/"uh" unless the prompt shows them. This keeps them so Silence Slayer can cut them.
FILLER_PROMPT = "Umm, so, uh, I was like, you know, hmm. Er, okay, so basically, um, yeah."


def transcribe(video, out_dir, model="small", lang=None, force=False, name="words.json"):
    video = er.check_video(video)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / name
    st = video.stat()
    key = {"src": str(video), "size": st.st_size, "mtime": int(st.st_mtime), "model": model}
    if target.exists() and not force:
        old = json.loads(target.read_text(encoding="utf-8"))
        if old.get("key") == key:
            print(f"Transcript already done: {target}")
            return target

    if not er.probe(video)["has_audio"]:
        sys.exit("This video has no sound, so there's nothing to transcribe.")
    import numpy as np
    raw = out_dir / "_audio16k.f32"
    er.run(["-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", str(raw)])
    audio = np.fromfile(raw, dtype=np.float32)
    raw.unlink(missing_ok=True)
    from faster_whisper import WhisperModel
    t0 = time.time()
    print(f"Loading the '{model}' speech model (first run downloads it once)...", flush=True)
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, info = m.transcribe(audio, language=lang, word_timestamps=True, initial_prompt=FILLER_PROMPT,
                              condition_on_previous_text=False, vad_filter=False, beam_size=5)
    words, lines, last = [], [], 0.0
    for seg in segs:
        seg_words = [w for w in (seg.words or []) if w.word.strip()]
        for w in seg_words:
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 2)})
        text = seg.text.strip()
        if text:
            lines.append(f"[{er.ts(seg.start)}] {text}")
        if seg.end - last >= 120:
            last = seg.end
            print(f"  ...{er.ts(seg.end)} of {er.ts(info.duration)} done", flush=True)
    data = {"key": key, "language": info.language, "duration": round(info.duration, 3), "words": words}
    target.write_text(json.dumps(data, indent=0, ensure_ascii=False), encoding="utf-8")
    txt = out_dir / ("transcript.txt" if name == "words.json" else Path(name).stem.replace("words", "transcript", 1) + ".txt")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Done in {time.time() - t0:.0f}s: {len(words)} words, language '{info.language}'.")
    print(f"Words: {target}\nTranscript: {txt}")
    return target


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--model", default="small", help="tiny | base | small | medium (bigger = slower, more accurate)")
    ap.add_argument("--lang", default=None, help="language code, e.g. en (default: detect)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    d = er.workdir(a.video, a.out)
    transcribe(a.video, d, a.model, a.lang, a.force, name=er.words_path(a.video, d).name)
