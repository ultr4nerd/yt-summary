---
name: yt-summary
description: Summarize YouTube videos by fetching the transcript with yt-dlp, producing an adaptive-format summary, and caching the transcript locally for follow-up questions. Invoke automatically when the user shares a YouTube URL (youtube.com/watch, youtu.be/, youtube.com/shorts/) or asks to summarize/explain/extract content from a YouTube video. Also available as /yt-summary <url>. Supports multiple videos in one message (individual or comparative mode). Answers follow-up questions about previously summarized videos by searching the local cache.
license: MIT
---

# yt-summary

Summarize YouTube videos using `yt-dlp`. A bundled shell script handles the download and transcript cleanup; this skill tells the agent how to drive it and how to turn the cached transcript into an adaptive summary.

Transcripts are cached under `$XDG_DATA_HOME/yt-summary/` (defaults to `~/.local/share/yt-summary/`) so follow-up questions can be answered without re-downloading.

## When to use

- The user pastes a YouTube URL (`youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/shorts/...`).
- The user invokes `/yt-summary <url>`.
- The user asks to summarize, explain, or extract content from a linked video.
- The user asks a follow-up question about a previously summarized video (see "Follow-up questions" below).

## Language of the summary

**Match the user's conversation language.** If the user is writing in English, summarize in English. If in Spanish, summarize in Spanish. Etc. The video's own language does not matter — translate if needed.

## Requirements

Two dependencies. Both are cross-platform (macOS / Linux / Windows).

**Python 3.8 or newer.** Comes preinstalled on modern macOS and every Linux distro. On Windows install from the Microsoft Store or `winget install Python.Python.3`.

**yt-dlp.** If `yt-dlp` is not on `PATH`, stop and tell the user to install it:

```bash
brew install yt-dlp              # macOS
pipx install yt-dlp              # cross-platform (preferred)
pip install yt-dlp               # fallback
winget install yt-dlp.yt-dlp     # Windows
```

## Flow

### 1. Run the bundled script

The script lives at `scripts/yt-summary.py` relative to this skill. Run it with the URL as the only argument, using whichever Python interpreter is available on the machine:

```bash
python3 "<PATH_TO_THIS_SKILL>/scripts/yt-summary.py" "<URL>"
```

On Windows where `python3` may not exist, fall back to `python` or the `py` launcher:

```bash
python  "<PATH_TO_THIS_SKILL>/scripts/yt-summary.py" "<URL>"
py -3   "<PATH_TO_THIS_SKILL>/scripts/yt-summary.py" "<URL>"
```

Read the first line of its stdout. It will be one of:

- `CACHED:<path>` — the transcript is already in the local cache. `Read` the file and continue to step 3 (re-summarize from the cached transcript; it's cheap because no re-download happens).
- `NEW:<path>` — the script just downloaded the transcript and wrote a fresh cache entry. `Read` the file and continue to step 3.

The cache file only stores metadata + the cleaned transcript. Summaries are generated fresh each time; they are not persisted to disk.

Script exit codes:
- `1` — invalid URL (ask the user to provide a valid YouTube link).
- `2` — `yt-dlp` missing (tell the user to install it; see Requirements).
- `3` — no subtitles available (tell the user and stop).
- `4` — yt-dlp failure (private, age-gated, geo-blocked, removed — surface the error to the user).

### 2. Read the cache file

`Read` the path the script printed. The file has YAML frontmatter with all metadata, and a `## Transcript` section at the bottom.

If `Read` fails because the file is too large (>25K tokens): use `Read` with `offset`/`limit` to sample the beginning, middle, and end, or `Grep` the file for keywords suggested by the title.

### 3. Generate an adaptive summary

Write the summary in the user's conversation language. Begin with a metadata block built from the frontmatter:

```markdown
## 📺 "<title>"
**Channel:** <channel> · **Duration:** <duration> · **Published:** <upload_date> · **<views> views**
```

Pick the format based on the video type (inferred from duration, channel, title, transcript structure):

| Video type | Format |
|---|---|
| Tutorial / how-to / product demo (dense, >10 min) | TL;DR (1-2 lines) + thematic section headers + "Tips / limitations" section if mentioned |
| News / short video (<5 min) | 3-5 concise bullets |
| Interview / podcast | Key questions + key answers, grouped by topic |
| Review / opinion | Verdict + pros + cons + recommendation |
| Talk / keynote | Central thesis + 3-5 supporting arguments + conclusions |

### 4. Show the transparent footer

Collect cache stats and append this footer to the chat output:

```bash
FILE=<path from step 1>
SIZE=$(du -h "$FILE" 2>/dev/null | cut -f1)
CACHE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/yt-summary"
COUNT=$(ls "$CACHE_DIR" 2>/dev/null | wc -l | tr -d ' ')
TOTAL=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
```

Present to the user:

```
📎 Transcript saved: <path> (<size>)
   Cache total: <count> files, <total>
```

The footer lets the user monitor disk usage and clean up manually (`rm -rf ~/.local/share/yt-summary/`) if needed.

## Multiple videos in one message

If the user pastes 2+ YouTube URLs, or asks to summarize several videos together, detect intent:

**Mode A — Individual summaries (default):**
- Run the full flow (steps 1-4) for each video sequentially.
- Present each summary with its own metadata block, separated by `---`.
- Show a single footer at the end with the cumulative cache count across all videos processed in this turn.

**Mode B — Comparative synthesis:**
Triggered when the user explicitly says "compare", "what do they have in common", "differences", "which is better", etc:
1. Run steps 1-2 for each video (cache every transcript).
2. Produce **one combined output** containing:
   - A metadata table for all N videos (title, channel, duration, views)
   - A short summary of each (3-4 bullets)
   - "Common points" and "Key differences" sections
   - A verdict if relevant
3. One final footer with the cumulative cache count.

**Optimizations for N>3 videos:**
- Run the script for every URL first — cache hits return instantly, so you quickly learn which ones need real work.
- Report progress as you go: "Processing 3/7…".

## Edge cases

- **Playlist URL** (`list=...` without `v=...`): ask the user for an individual video URL — the script only accepts single-video URLs.
- **Rate limit 429**: already mitigated inside the script — it requests multiple languages (`en,es,en-US,es-419`) and proceeds with whichever succeeds.
- **No captions available** (script exit `3`): tell the user. Suggest a different video, or an out-of-scope alternative such as transcribing the audio with Whisper separately.
- **Private / age-gated / geo-blocked video** (script exit `4`): surface yt-dlp's error message verbatim.
- **Same video pasted twice**: the script's cache check avoids any re-download.
- **Huge transcripts** (>25K tokens): sample the cache file with `Read` (offset/limit) or `Grep` for keywords from the title.

## Follow-up questions about cached videos

If the user later asks about a video that isn't in the current visible summary but was cached before (possibly in a previous session):

1. Locate the cached file: `ls ~/.local/share/yt-summary/` and identify the video by title/date/context in the conversation.
2. `Grep` the transcript for terms relevant to the question (e.g. `grep -in "webhook" ~/.local/share/yt-summary/...md`).
3. `Read` only the nearby lines (`offset` + `limit` around a match).
4. Answer by quoting literal fragments from the transcript.

This uses the full cached transcript to answer precisely without any re-download and without blowing the context window.
