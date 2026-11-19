# The Editing Room

My best videos were unedited. Most of yours will be too, and that's fine.

But some days you'll fluff a line, um your way through the intro, or want a Short out of the good bit. This is for those days. Six tools that live inside Claude and edit your videos on your own laptop. There's no editing software to learn, and nothing gets uploaded anywhere.

| Tool | What it does |
|---|---|
| Silence Slayer | Cuts out your pauses, ums and retakes |
| Caption Print | Word-by-word captions, in 4 styles and any colour |
| Packaging Pick | 10 titles and 3 thumbnails made from your own face |
| Shorts Clipper | Finds your best moments, crops them to vertical, adds captions |
| Upload Pack | Description, chapters and tags, written from what you actually said |
| Video Review | Honest notes on your hook, pacing and delivery, with timestamps |

## What you need

- A Mac or a Windows computer. (Your phone films, the laptop edits.)
- A paid Claude plan (Pro or higher, the free plan doesn't include the Code side of the app). That's the only cost.
- About 2 GB of free space and 15 minutes, once.

You won't touch a Terminal or a line of code. Setup is a few clicks inside the Claude app.

## Setup (do this once)

**1. Get the Claude app.**
Download it from [claude.com/download](https://claude.com/download), install it like any other app and log in. Already have it? Update it and skip ahead.

**2. Add The Editing Room.**
In the app's left sidebar, click **Customize**, then **Plugins**. Top right, click **Add**, then **Add marketplace**, and paste this in:

```
danwestworld/editing-room
```

Editing Room shows up in the list. Click **Add to this computer**.

**3. Let it set itself up.**
Switch to the Code side of the app (the `</>` button, top left) and start a new session. If it asks for a folder, pick your Desktop. Then type this in the message box and send it:

```
/editing-room:setup
```

Claude will ask to install a small free tool called uv and download a speech model (around 500 MB). Each time it asks permission, click Allow. Make a coffee. When every line says OK, you're done. You never do this again.

## Using it

**Get your video onto the laptop.** iPhone to Mac: AirDrop it. Anything to Windows: plug the phone in, or email/WhatsApp it to yourself and save it. Put it on your Desktop or in Downloads and give it a name you'll remember, like `day 1`.

**Then just ask, in normal words:**

- "Cut the pauses out of day 1"
- "Put captions on it, yellow, big"
- "Give me titles and a thumbnail for day 1"
- "Clip 3 Shorts from day 1"
- "Write my YouTube description for day 1"
- "Review day 1, be honest"

Claude finds the video, does the work and opens the result for you. Everything lands in a folder next to your video called `day 1 - Editing Room`. Your original is never touched.

**A good order for one video:** Silence Slayer → Caption Print (Shorts only, or skip it) → Packaging Pick → Upload Pack. Shorts Clipper and Video Review run on the original whenever you like.

## Good to know

- A 10-minute video takes a few minutes per tool. It all runs on your laptop, so an older laptop is slower. Leave it running and go film tomorrow's.
- Filmed on an iPhone in HDR? It converts the colours on its own so nothing comes out washed out. (Or turn off Settings → Camera → Formats → HDR Video and skip the issue entirely.)
- Captions got a name wrong? Tell Claude the right spelling ("it's Siobhan, not Shivon") and it fixes them before burning them in.
- It's your edit. Don't like a cut or a crop? Say so: "keep the pause after the joke", "move captions to the top", "less shouty thumbnail". It redoes it.

## If something breaks

1. Type `/editing-room:setup` again. It checks everything and fixes most problems on its own.
2. Still stuck? Screenshot the message and reply to any Zero to One email. A human reads those.
