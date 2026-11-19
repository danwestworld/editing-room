---
name: caption-print
description: "Burn word-by-word captions into a video, in a choice of styles and colours, plus an .srt subtitle file for YouTube. Use when the person wants captions, subtitles, text on screen or karaoke-style words."
allowed-tools: Bash, Read, Edit
argument-hint: "[video name or path] [bold|clean|boxed|punch] [colour]"
---

# Caption Print

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Script: `${CLAUDE_PLUGIN_ROOT}/scripts/captions.py`.

1. Find the video. If a `- cut.mp4` exists from Silence Slayer, caption that one.
2. Spelling: run `uv run "<scripts>/transcribe.py" "<video>"`, Read the transcript it names.
   Names, brands and niche words get misheard. Fix each wrong word in the matching
   `words*.json` (`"w"` field only, keep the times). Ask them only if you can't tell.
3. Style (they named one → skip to 4). Make previews:
   `uv run "<scripts>/captions.py" "<video>" --styles-preview` → Read the 4 stills, open the
   folder, and describe them in one line each:
   - **bold**: big white capitals, the spoken word pops in yellow (the classic Shorts look)
   - **clean**: calm mixed-case text, the spoken word goes bright white (talking-head YouTube)
   - **boxed**: text on a dark box, the spoken word in yellow (readable on busy backgrounds)
   - **punch**: 2 huge words at a time, green pop (high-energy Shorts)
   No answer or "you pick" → bold for vertical videos, clean for horizontal.
4. Render: `uv run "<scripts>/captions.py" "<video>" --style <style>` plus what they asked for:
   `--color <hex>` (turn colour names into hex: yellow FFD400, green 3CFF6E, red FF3B3B,
   blue 2EA8FF, pink FF4FD8, orange FF8A00, white FFFFFF), `--position bottom|middle|top`,
   `--words N` (words on screen at once), `--size 1.2` (bigger) / `0.85` (smaller).
5. Read the still the script names (middle of the video): words readable, not cut off,
   not over the face. Bad → change position/size and render again.
6. Tell them: the captioned file (`<name> - captions.mp4`), and the `.srt` file. Tip: for
   long YouTube videos many creators upload the `.srt` in YouTube Studio → Subtitles instead
   of burning captions in. Burned captions suit Shorts.
