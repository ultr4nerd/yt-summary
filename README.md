<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
    <img src="./assets/hero-light.svg" alt="yt-summary — summarize YouTube videos in any AI agent" width="680">
  </picture>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/tests-27%2F27%20passing-success" alt="Tests: 27/27 passing">
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Cursor%20%C2%B7%20OpenCode%20%C2%B7%2040%2B-FF0000" alt="Works with Claude Code, Cursor, OpenCode, and 40+ agents">
</p>

A skill that summarizes YouTube videos by extracting the transcript with `yt-dlp`, producing an adaptive-format summary in your conversation language, and caching the full transcript locally so follow-up questions are answered without re-downloading.

Works out of the box with Claude Code, Cursor, OpenCode, and 40+ other agents.

<p align="center">
  <img src="./assets/demo.gif" alt="yt-summary standalone demo" width="820">
</p>

## How it works

```mermaid
flowchart LR
    URL([YouTube URL]) --> Script[yt-summary.py]
    Script --> YTDLP[yt-dlp]
    YTDLP --> VTT[Cleaned transcript]
    VTT --> Cache[(Local cache)]
    Cache --> Agent[Your agent]
    Agent --> Summary([Adaptive summary])
```

The bundled Python script calls `yt-dlp` to fetch the captions, strips timing cues and duplicate lines, and writes the cleaned transcript to a local cache. Your agent then reads the transcript, picks a format based on the video type (tutorial, interview, news, review, keynote…), and writes the summary in your conversation language. Follow-up questions hit the cached transcript directly — no re-download, even across sessions.

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

## Install

| Multi-agent (recommended) | Claude Code plugin | Shell fallback |
|:---|:---|:---|
| Auto-detects your agent and copies the skill to the right place. Works with 40+ agents via [`vercel-labs/skills`](https://github.com/vercel-labs/skills). | Install as a native Claude Code plugin. | Detects Claude Code / Cursor / OpenCode and installs manually. |
| `npx skills add ultr4nerd/yt-summary` | `/plugin marketplace add ultr4nerd/yt-summary` then `/plugin install yt-summary@yt-summary` | <code>curl&nbsp;-fsSL&nbsp;https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh&nbsp;\|&nbsp;bash</code> |

You can force a specific target with the shell fallback:

```bash
AGENT=cursor   bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
AGENT=opencode bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
AGENT=claude   bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
```

### Agent compatibility

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
- Format: one `.md` file per video with YAML frontmatter (metadata) and the cleaned transcript. Summaries are produced fresh each turn and displayed in chat — they are not persisted.
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
