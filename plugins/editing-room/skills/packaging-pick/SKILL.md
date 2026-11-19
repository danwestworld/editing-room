---
name: packaging-pick
description: "Write YouTube titles and make thumbnails from the person's own video frames. Use when the person wants a title, title ideas, a thumbnail, packaging, or a better click-through rate for a video."
allowed-tools: Bash, Read, Write
argument-hint: "[video name or path]"
---

# Packaging Pick

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Script: `${CLAUDE_PLUGIN_ROOT}/scripts/thumbs.py`.

## Titles
0. Read `${CLAUDE_PLUGIN_ROOT}/references/titles.md` in full first. It holds the patterns and
   92 real outlier titles from coaching and creator channels. Every title you write uses one of
   its patterns, in the creator's own words. Never copy an example title.
1. Find the video. Transcribe (`uv run "<scripts>/transcribe.py" "<video>"`, instant if already done), Read the transcript.
2. Find the one promise of the video: what does the viewer get or avoid? Use their words.
3. Pick the 4-5 patterns from the reference that fit THIS video (a fitness coach with no
   results yet → call-out, age/identity, hypothetical reset; a coach with a client win → exact
   result, case study, outcome + parenthetical). Write 10 titles across them, at least one in
   lowercase. Follow the reference's rules: exact numbers only if the creator said them, two
   devices at most, under 60 characters, payoff in the first 5 words, no hype words, no
   emojis, nothing the video doesn't pay off.
4. Pick the best 3. For each, name its pattern and say in one line why it fits.

## Thumbnails
5. `uv run "<scripts>/thumbs.py" frames "<video>"` → Read `<folder>/thumbs/frames sheet.jpg`. Pick the
   3 frames with open eyes and the strongest expression that fits the title.
6. For each of the top 3 titles, write thumbnail text: 2-4 words that ADD a second hook (the
   fight, the scale or the open loop; see "Thumbnails" in the reference). Never repeat the
   title. Put `*stars*` round the one word to colour; red (`--accent FF3B3B`) suits an enemy.
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
