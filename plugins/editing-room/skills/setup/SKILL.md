---
name: setup
description: "One-time setup and health check for The Editing Room. Use when the person first installs The Editing Room, asks to set it up, or when any Editing Room tool fails because something is missing."
allowed-tools: Bash, Read
---

# Setup

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Tell the person: "Setting things up. This takes
5-10 minutes the first time, and you only do it once."

1. Check for uv (the tool that runs everything): `command -v uv || ls "$HOME/.local/bin/uv"`.
2. Missing → say "I need to install one small free tool called uv. Click Allow when asked." Then
   run the official installer (docs.astral.sh/uv):
   - Mac / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   Then use `"$HOME/.local/bin/uv"` for the rest of this session (the new path isn't loaded yet).
3. Run the check (timeout 600000; it downloads Python, the video engine and the ~500 MB speech
   model once): `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check.py"`
4. Every line says OK → tell them it's ready and how to use it:
   - Put the video somewhere easy (Desktop or Downloads), then say what you want in plain words:
     "cut the pauses out of my video called day 1", "add captions", "give me titles and a
     thumbnail", "clip some Shorts", "write my description", "review my video".
   - Or type one of: `/editing-room:silence-slayer`, `/editing-room:caption-print`,
     `/editing-room:packaging-pick`, `/editing-room:shorts-clipper`, `/editing-room:upload-pack`,
     `/editing-room:video-review`.
5. A FAIL line → fix what it names:
   - No internet / download failed → ask them to check the connection, run step 3 again.
   - ffmpeg missing a feature → rare, a Linux build. Tell them to install a full ffmpeg and set
     `EDITING_ROOM_FFMPEG` to its path.
   - Anything else → show the one FAIL line in plain words and suggest they reply to Dan's
     challenge email with a screenshot.
