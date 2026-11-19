---
name: packaging-pick
description: "Write YouTube titles and make thumbnails from the person's own video frames. Use when the person wants a title, title ideas, a thumbnail, packaging, or a better click-through rate for a video."
allowed-tools: Bash, Read, Write
argument-hint: "[video name or path]"
---

# Packaging Pick

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Script: `${CLAUDE_PLUGIN_ROOT}/scripts/thumbs.py`.

## Titles
1. Find the video. Transcribe (`uv run "<scripts>/transcribe.py" "<video>"`), Read the transcript.
2. Find the one promise of the video: what does the viewer get or avoid? Use their words.
3. Write 10 titles across 3 angles: **result** ("How I got my first 3 clients from YouTube"),
   **curiosity** ("The video I almost didn't post"), **contrarian** ("Stop niching down").
   Rules: under 60 characters, the payoff in the first 5 words, plain words a 12-year-old
   reads, no clickbait the video doesn't pay off, no ALL CAPS titles, no emojis, none of:
   "unlock", "ultimate guide", "game-changer", "dive into", "secrets revealed".
4. Pick the best 3 and say why in one line each.

## Thumbnails
5. `uv run "<scripts>/thumbs.py" frames "<video>"` → Read `<folder>/thumbs/frames sheet.jpg`. Pick the
   3 frames with open eyes and the strongest expression that fits the title.
6. For each of the top 3 titles, write thumbnail text: 2-5 words that ADD to the title (never
   repeat it). Put `*stars*` round the one word to colour.
7. Make one per frame:
   `uv run "<scripts>/thumbs.py" make "<folder>/thumbs/frame N.jpg" --text "MY *FIRST* CLIENT" --style punch --name "option 1"`
   Styles: `punch` (white text, black outline, one colour word), `box` (black text on a
   colour block), `clean` (white text on a dark fade). Use at least 2 styles across the 3.
   `--accent` changes the colour (hex), `--side left|right` moves the text.
8. Read each thumbnail. Text must not cover the face and must read at phone size. Fix and
   remake if not.
9. Write `packaging.md` in the Editing Room folder: the 10 titles, the top 3 with their
   thumbnail text. Open the thumbs folder. Tell them: test 2 thumbnails with YouTube's
   "Test & compare" if they have it.
