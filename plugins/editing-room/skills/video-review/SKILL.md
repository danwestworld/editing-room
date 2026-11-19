---
name: video-review
description: "Critique a talking video like a YouTube coach would: the hook, structure, pacing, filler words, framing and ending, with timestamps and what to do next time. Use when the person asks for feedback, a review, a critique or \"is this video good?\"."
allowed-tools: Bash, Read
argument-hint: "[video name or path]"
---

# Video Review

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Nothing gets rendered: this is notes only.

1. Find the video (the raw one is best: it shows their real pauses and ums).
2. Gather facts:
   - `uv run "<scripts>/cut.py" plan "<video>"` (transcribes too) → its "Stats" line gives words
     per minute (130-170 is a good pace), ums per minute and seconds of pauses. Whisper misses
     some ums, so treat the um count as a floor.
   - Read `<folder>/transcript.txt` (lines are `[mm:ss] text`).
   - `uv run "<scripts>/thumbs.py" frames "<video>" --count 4` → Read the sheet: light on
     the face, eyes near the top third, background tidy, face not cut off.
3. Judge, with timestamps:
   - **Hook (first 15 seconds):** do they say who it's for and what the viewer gets? Or do
     they warm up ("hey guys, so today...")? Quote the first line and give a better one in
     their voice.
   - **Structure:** one clear idea? Does each part earn the next? Where does it drag?
   - **Delivery:** pace, ums per minute, energy dips (long sentences, trailing off).
   - **Look:** light, framing, sound (echo, wind) only if it hurts.
   - **Ending:** one clear next step for the viewer, or does it fade out?
   Sound (wind, echo) can't be measured here: mention it only if the transcript is full of
   misheard words. Video under 2 minutes → judge the hook on the first 5 seconds and skip
   the structure point if there's only one idea.
4. Reply in under 250 words, direct, like a coach who wants them to post tomorrow:
   - Score out of 10, one line why.
   - 3 things to keep doing.
   - 3 things to fix next video, most important first, each with the time and a fix.
   - The one Editing Room tool that helps most now, with the number from step 2 (e.g. how many
     seconds Silence Slayer would cut, from the plan's "Length" line).
   Never mock. Never tell them to buy gear first: the phone is enough.
