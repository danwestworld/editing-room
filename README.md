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
- A paid Claude plan (Pro or higher, the free plan doesn't include Claude Code). That's the only cost.
- About 2 GB of free space and 15 minutes, once.

## Setup (do this once)

**1. Get Claude.**
Open the Terminal. On a Mac: press Cmd + Space, type `Terminal`, hit Enter. On Windows: press the Start button, type `PowerShell`, hit Enter. (Windows only: install [Git for Windows](https://git-scm.com/downloads/win) first, just click Next all the way through.)

Copy this line, paste it into the window, hit Enter:

Mac:
```
curl -fsSL https://claude.ai/install.sh | bash
```
Windows:
```
irm https://claude.ai/install.ps1 | iex
```

Close the window and open a new one when it finishes.

**2. Add The Editing Room.**
Paste this one line, hit Enter (same line on Mac and Windows):

```
claude plugin marketplace add danwestworld/editing-room; claude plugin install editing-room@dan-west
```

You should see two green ticks. Now type `claude` and hit Enter. First time, it asks you to log in with your Claude account. Do that.

**3. Let it set itself up.**
Inside Claude (the window from step 2), type:

```
/editing-room:setup
```

Claude will ask to install a small free tool called uv and download a speech model (around 500 MB). When it asks permission, pick Yes and press Enter. Make a coffee. When every line says OK, you're done. You never do this again.

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
