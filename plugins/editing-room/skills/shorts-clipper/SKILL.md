---
name: shorts-clipper
description: "Find the best moments in a longer video and turn them into vertical 9:16 Shorts, cropped on the face and captioned. Use when the person wants Shorts, Reels, TikToks, clips or vertical cuts from a video."
allowed-tools: Bash, Read
argument-hint: "[video name or path] [how many]"
---

# Shorts Clipper

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Script: `${CLAUDE_PLUGIN_ROOT}/scripts/clip.py`.

1. Find the video (the original, not a captioned one: captions are added here). Transcribe
   (`uv run "<scripts>/transcribe.py" "<video>"`), Read the transcript.
2. Pick 3-5 moments (or the number they asked for). Each one:
   - stands alone: makes sense with no context from the rest of the video
   - opens with a strong line in the first 3 seconds (a claim, a number, a question)
   - one idea, ends on a payoff (the answer, the punchline, the lesson)
   - 20-60 seconds (never over 3 minutes)
   Under 2 minutes of video → 1-2 moments is fine. Nothing stands alone → say so honestly.
3. Show the list: name, start-end, the opening line, why it works. Ask "Clip all of these?"
   They said "just do it" → skip the question.
4. Clip each (times as m:ss, they snap to whole words; pauses inside are tightened):
   `uv run "<scripts>/clip.py" "<video>" --start 1:02 --end 1:48 --name "<short name>"`
   Caption options as in Caption Print: `--style bold|clean|boxed|punch` (default bold),
   `--color`, `--position`. Framing: `--crop auto` (follows the face, default), `center`,
   `none` (whole frame with blurred bars, for screen shares or two people).
5. Read each `.jpg` still the script names: face in frame, captions readable. Bad framing →
   redo with `--crop center` or `none`.
6. Open the `shorts` folder. Give each Short one line they can use as its title/caption.
