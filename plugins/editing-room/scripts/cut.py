# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2", "imageio-ffmpeg>=0.5,<1", "pillow>=10,<13", "opencv-python-headless>=4.9,<5", "numpy<3"]
# ///
"""Silence Slayer: find pauses and ums, then cut them out.

  uv run cut.py plan   VIDEO [--max-pause 0.4] [--breath 0.15] [--keep-fillers] [--out DIR]
  uv run cut.py render VIDEO [--out DIR] [--crf 20]
  uv run cut.py check  VIDEO [--out DIR]   (re-transcribes the cut, lists words that went missing)

plan   → DIR/cut_plan.json: every cut with its reason, plus "flags" (sound with no words:
         often a swallowed um or a false start). Edit "cut": true/false per row, or add rows.
render → DIR/<name> - cut.mp4 from the plan.
Needs DIR/words.json from transcribe.py (plan runs it if missing).
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import er_lib as er


def context(words, s, e, n=4):
    mid = lambda w: (w["s"] + w["e"]) / 2
    before = [w["w"] for w in words if mid(w) <= s][-n:]
    after = [w["w"] for w in words if mid(w) >= e][:n]
    return f"...{' '.join(before)} ‖ {' '.join(after)}..."


def plan(a):
    video = er.check_video(a.video)
    d = er.workdir(video, a.out)
    words = er.ensure_words(video, d)
    info = er.probe(video)
    dur = info["duration"]
    real = [w for w in words if not er.is_filler(w["w"])]
    sil = er.silences(video, noise=a.noise, min_len=min(0.3, a.max_pause))
    rows = []

    # 1. Pauses longer than max-pause → shrink to a breath on each side.
    #    The quiet-detector is the truth for where sound is. Whisper word ENDS stretch across
    #    pauses, so ignore them; a word START inside a quiet stretch is a soft word the
    #    detector missed, so protect it.
    for s, e in sil:
        if e - s < a.max_pause:
            continue
        lo, hi = s, e
        blocks = sorted((w["s"] - 0.08, w["s"] + 0.25) for w in real if s + 0.1 < w["s"] < e - 0.1)
        free, cur = [], lo
        for bs, be in blocks:
            free.append((cur, bs)); cur = be
        free.append((cur, hi))
        for fs, fe in free:
            cs = 0.0 if fs <= 0.05 else fs + a.breath      # dead air at the very start goes
            ce = dur if fe >= dur - 0.05 else fe - a.breath  # and at the very end
            if ce - cs > 0.1:
                rows.append({"start": round(cs, 3), "end": round(ce, 3), "reason": "pause", "cut": True})

    # 2. Filler words (um, uh...). Cut the word plus the gap up to its neighbours.
    if not a.keep_fillers:
        for i, w in enumerate(words):
            if not er.is_filler(w["w"]):
                continue
            prev_end = words[i - 1]["e"] if i > 0 else 0.0
            next_start = words[i + 1]["s"] if i + 1 < len(words) else dur
            cs = max(prev_end + 0.04, w["s"] - 0.08)
            ce = min(next_start - 0.04, w["e"] + 0.08)
            if ce - cs > 0.08:
                rows.append({"start": round(cs, 3), "end": round(ce, 3), "reason": f"filler '{w['w']}'", "cut": True})

    # 3. Flags: sound that has no words (a swallowed um, a laugh, a false start). Not cut by default.
    loud, cur = [], 0.0
    for s, e in sil:
        if s > cur:
            loud.append((cur, s))
        cur = e
    if cur < dur:
        loud.append((cur, dur))
    for s, e in loud:
        covered = sum(max(0.0, min(e, w["e"]) - max(s, w["s"])) for w in words)
        if e - s >= 0.6 and covered < 0.3 * (e - s):
            rows.append({"start": round(s, 3), "end": round(e, 3), "reason": "flag: sound with no words", "cut": False})

    rows.sort(key=lambda r: r["start"])
    for r in rows:
        r["at"] = er.ts(r["start"], ms=True)
        r["context"] = context(words, r["start"], r["end"])
    cuts = [(r["start"], r["end"]) for r in rows if r["cut"]]
    kept = sum(e - s for s, e in er.keeps_from_cuts(cuts, dur))
    out = {"source": str(video), "duration": round(dur, 2), "new_duration": round(kept, 2),
           "settings": {"max_pause": a.max_pause, "breath": a.breath, "noise": a.noise}, "cuts": rows}
    (d / "cut_plan.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    n_p = sum(r["reason"] == "pause" for r in rows)
    n_f = sum(r["reason"].startswith("filler") for r in rows)
    n_x = sum(not r["cut"] for r in rows)
    print(f"Plan: {n_p} pauses, {n_f} fillers to cut, {n_x} flagged spots to check.")
    print(f"Length: {er.ts(dur)} → {er.ts(kept)} ({dur - kept:.1f}s shorter).")
    spoken = [w for w in words if not er.is_filler(w["w"])]
    mins = max(dur / 60, 0.01)
    print(f"Stats: {len(spoken) / mins:.0f} words per minute, {n_f} ums/uhs ({n_f / mins:.1f} per minute), "
          f"{sum(e - s for s, e in sil if e - s >= 0.4):.1f}s of pauses over 0.4s.")
    if dur - kept < dur * 0.04:
        print("Note: a light trim. This speaker barely pauses. `--max-pause 0.3 --breath 0.08` cuts tighter.")
    print(f"Transcript: {d / 'transcript.txt'}")
    print(f"Plan file: {d / 'cut_plan.json'}")


def render(a):
    video = er.check_video(a.video)
    d = er.workdir(video, a.out)
    p = d / "cut_plan.json"
    if not p.exists():
        sys.exit("No cut_plan.json yet. Run `cut.py plan` first.")
    pl = json.loads(p.read_text(encoding="utf-8"))
    info = er.probe(video)
    cuts = [(float(r["start"]), float(r["end"])) for r in pl["cuts"] if r.get("cut")]
    keeps = er.keeps_from_cuts(cuts, info["duration"])
    out = d / f"{video.stem} - cut.mp4"
    print(f"Rendering {len(keeps)} pieces...", flush=True)
    kept = er.render_keeps(video, out, keeps, info, crf=a.crf)
    print(f"Done: {out}\nLength {er.ts(info['duration'])} → {er.ts(kept)}.")


def check(a):
    """Re-transcribe the cut and compare word by word. Lost real words = a cut went too deep."""
    import difflib
    video = er.check_video(a.video)
    d = er.workdir(video, a.out)
    cut = d / f"{video.stem} - cut.mp4"
    if not cut.exists():
        sys.exit("No cut video yet. Run `cut.py render` first.")
    src = er.ensure_words(video, d)
    new = er.ensure_words(cut, d)
    A, B = [er.norm(w["w"]) for w in src], [er.norm(w["w"]) for w in new]
    pl = json.loads((d / "cut_plan.json").read_text(encoding="utf-8"))
    cuts = [(r["start"], r["end"]) for r in pl["cuts"] if r.get("cut")]
    near_cut = lambda w: any(cs - 0.5 <= w["e"] and w["s"] <= ce + 0.5 for cs, ce in cuts)
    lost = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            gone = [src[i] for i in range(i1, i2) if not er.is_filler(src[i]["w"]) and near_cut(src[i])]
            if gone and (op == "delete" or len(gone) > (j2 - j1)):
                lost.append(gone)
    if not lost:
        print("Check passed: no real words went missing.")
    for g in lost:
        print(f"Maybe lost at {er.ts(g[0]['s'], ms=True)} (original clock): {' '.join(w['w'] for w in g)}")
    if lost:
        print("These can be Whisper noise. Untick the nearest cut in cut_plan.json and render again if a word is truly gone.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("plan")
    p1.add_argument("video"); p1.add_argument("--out")
    p1.add_argument("--max-pause", type=float, default=0.4, help="pauses longer than this get shortened")
    p1.add_argument("--breath", type=float, default=0.15, help="silence left on each side of a cut")
    p1.add_argument("--noise", default="-32dB", help="what counts as quiet")
    p1.add_argument("--keep-fillers", action="store_true")
    p2 = sub.add_parser("render")
    p2.add_argument("video"); p2.add_argument("--out"); p2.add_argument("--crf", type=int, default=20)
    p3 = sub.add_parser("check")
    p3.add_argument("video"); p3.add_argument("--out")
    a = ap.parse_args()
    {"plan": plan, "render": render, "check": check}[a.cmd](a)
