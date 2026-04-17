# yt-summary

A skill that summarizes YouTube videos by extracting the transcript with `yt-dlp`, producing an adaptive-format summary in your conversation language, and caching the full transcript locally so follow-up questions are answered without re-downloading.

Works out of the box with Claude Code, Cursor, OpenCode, and 40+ other agents.

## What it does

1. You paste a YouTube URL or say "summarize this video: …".
2. The bundled Python script downloads the captions with `yt-dlp` and normalizes the VTT into clean text.
3. Your agent reads the transcript, picks a format based on the video type (tutorial, interview, news, review, keynote…), and writes the summary.
4. The cleaned transcript is saved to `~/.local/share/yt-summary/<date>-<video-id>-<slug>.md`.
5. A footer tells you where the file is and how much disk the cache is using.

If you ask a follow-up question later — even in a different session — the agent finds the cached file by video ID and grep/reads only the relevant lines instead of re-downloading.

## Requirements

- **Python 3.8+** — bundled with modern macOS and every Linux distro. On Windows install from the Microsoft Store or with `winget install Python.Python.3`.
- **yt-dlp** — the only external binary dependency. Official install guide: [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp#installation).

Common `yt-dlp` install commands:

```bash
brew install yt-dlp              # macOS
pipx install yt-dlp              # cross-platform (preferred)
pip install yt-dlp               # fallback
winget install yt-dlp.yt-dlp     # Windows
```

If none of these fit your environment, follow the [official instructions](https://github.com/yt-dlp/yt-dlp#installation) — yt-dlp also ships standalone binaries for macOS, Linux, and Windows.

The bundled script is plain Python (stdlib only), so it runs natively on **macOS, Linux, and Windows** — no WSL, no Git Bash required.

## Installation

Pick the option that matches your setup.

### Option 1 — Multi-agent (recommended)

Uses [`vercel-labs/skills`](https://github.com/vercel-labs/skills) to auto-detect which coding agent you have installed (Claude Code, Cursor, OpenCode, and 40+ more) and copy the skill to the right place.

```bash
npx skills add ultr4nerd/yt-summary
```

### Option 2 — Claude Code plugin

```
/plugin marketplace add ultr4nerd/yt-summary
/plugin install yt-summary@yt-summary
```

### Option 3 — Shell oneliner (fallback)

Detects Claude Code, Cursor, or OpenCode and installs the skill manually:

```bash
curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh | bash
```

You can force a specific target:

```bash
AGENT=cursor   bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
AGENT=opencode bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
AGENT=claude   bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
```

### Agent-specific notes

| Agent | Native skill support | Install location |
|---|---|---|
| **Claude Code** | ✅ native | `~/.claude/skills/yt-summary/` |
| **Cursor** | ✅ native | `.agents/skills/yt-summary/` (per-project) |
| **OpenCode** | ⚠️ requires a skills loader plugin such as [`malhashemi/opencode-skills`](https://github.com/malhashemi/opencode-skills) | `~/.config/opencode/skills/yt-summary/` |

## Usage

Once installed, there's nothing to remember — paste a YouTube URL:

```
Summarize this: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Or invoke it explicitly:

```
/yt-summary https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Multiple videos

Paste several URLs in one message; the skill processes them sequentially and caches each one. Say "compare these" or "what do they have in common" to get a combined comparative summary instead of individual ones.

### Follow-up questions

```
What did Jack say about webhooks in the Claude Code 2.0 video?
```

The skill grep's the cached transcript and answers with literal quotes — no re-download.

## Cache

- Location: `${XDG_DATA_HOME:-~/.local/share}/yt-summary/`
- Format: one `.md` file per video with YAML frontmatter (metadata), the summary, and the full transcript.
- Typical size: 20–50 KB per video.
- Clear the cache at any time: `rm -rf ~/.local/share/yt-summary/`

## Standalone usage of the script

The Python script inside the skill works on its own — you don't need an agent to use it:

```bash
python3 skills/yt-summary/scripts/yt-summary.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
# Prints: NEW:<path> (first time) or CACHED:<path> (subsequent runs)
```

On Windows where `python3` may not exist, use `python` or `py -3`:

```powershell
python skills\yt-summary\scripts\yt-summary.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Tests

Run the bundled test suite (stdlib only, no pytest needed):

```bash
python3 tests/test_script.py
```

Covers URL parsing, slug generation, VTT cleanup, and every CLI exit code. The happy-path test requires `yt-dlp` and network access; everything else runs offline.

## License

MIT. See [LICENSE](./LICENSE).
