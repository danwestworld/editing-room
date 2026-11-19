---
name: silence-slayer
description: "Cut the pauses, ums, uhs and retakes out of a talking video. Use when the person wants to remove silences, dead air, ums, filler words or mistakes, tighten a video, or \"edit\" a raw recording."
allowed-tools: Bash, Read, Edit
argument-hint: "[video name or path] [tighter|natural]"
---

# Silence Slayer

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first. Script: `${CLAUDE_PLUGIN_ROOT}/scripts/cut.py`.

1. Find the video. Then plan the cuts (transcribes first, ~1 min per 5 min of video):
   `uv run "<scripts>/cut.py" plan "<video>"`
   Pace: default is fine. "Tighter / snappier" → `--max-pause 0.3 --breath 0.08`.
   "Keep it natural" → `--max-pause 0.8 --breath 0.25`. "Keep my ums" → `--keep-fillers`.
2. Find retakes (the script can't): Read `<folder>/transcript.txt`. Look for a sentence that
   starts, breaks off and starts again, the same line said twice, or "let me say that again".
   Keep the LAST good take. For each, Read `words.json` around that spot and add a row to
   `cut_plan.json` → `cuts`: `{"start": <first word of the dropped take>.s,
   "end": <first word of the kept take>.s - 0.05, "reason": "retake", "cut": true}`.
3. Flags (`"reason": "flag: sound with no words"`, `cut: false`): sound with no words, often a
   swallowed um, a laugh or a false start. Look at `context`. Clearly a stumble → set
   `"cut": true`. Unsure → leave it.
4. Retakes added → tell them which lines you'll drop (quote a few words + time) and ask once
   "Cut those too?". No retakes → go straight on.
5. Render: `uv run "<scripts>/cut.py" render "<video>"`
6. Check: `uv run "<scripts>/cut.py" check "<video>"`. "Maybe lost" lines are often Whisper
   noise. A real word is gone → find the nearest cut in `cut_plan.json`, set `"cut": false`,
   render and check again.
7. Tell them: how many pauses / ums / retakes went, old length → new length, the file
   (`<name> - cut.mp4`). Open it. The plan printed "a light trim" → say they barely pause and
   offer the tighter setting. Offer captions next.
