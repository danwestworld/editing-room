---
name: upload-pack
description: "Write the YouTube description, timestamped chapters and tags for a video from what the person actually said in it. Use when the person wants a description, chapters, timestamps, tags or upload copy for YouTube."
allowed-tools: Bash, Read, Write
argument-hint: "[video name or path]"
---

# Upload Pack

Read `${CLAUDE_PLUGIN_ROOT}/HOW-TO-RUN.md` first.

1. Find the FINAL video, the exact file they will upload (chapter times must match it). After
   Silence Slayer that is `<name> - cut.mp4` or `<name> - cut - captions.mp4`; ask if unsure.
2. Transcribe it: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe.py" "<video>"`. Read the
   transcript it names (lines are `[mm:ss] text`).
3. Ask once, optional: "Any link you want in the description (your offer, a free guide,
   your calendar)?" No answer → use `[YOUR LINK]`.
4. Write, in their own words and tone (reuse their phrases from the transcript):
   - **Description:** first 2 lines = why watch (YouTube shows only these before "more").
     Then 2-4 short sentences on what's inside. Then the link line. Then chapters. Then 3
     hashtags.
   - **Chapters:** first one is `0:00`, at least 3, each at least 10 seconds long (YouTube
     ignores them otherwise). Start each at the line where the new part begins. Names
     2-5 words, specific ("Why I quit my job"), never "Intro / Conclusion" only.
   - **Tags:** 10-15, under 500 characters in total, comma-separated: the topic, the
     problem, the audience, 2-3 phrasings people would search.
   No hype words ("unlock", "game-changer", "dive into", "journey", "in this video we'll
   explore"), no emoji walls, no claims they didn't make in the video.
5. Save to `upload pack.md` in the Editing Room folder, and also paste it in the chat in
   plain blocks they can copy (Description / Tags).
