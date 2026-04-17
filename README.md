<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
    <img src="./assets/hero-light.svg" alt="yt-summary — summarize YouTube videos in any AI agent" width="560">
  </picture>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Cursor%20%C2%B7%20OpenCode%20%C2%B7%2040%2B-FF0000" alt="Works with Claude Code, Cursor, OpenCode, and 40+ agents">
</p>

Paste a YouTube link into your coding agent. `yt-summary` fetches the captions with `yt-dlp`, formats the transcript by video type (tutorials get a TL;DR plus sections, interviews get key questions and answers, news gets bullets, reviews get pros and cons), and caches it locally. Follow-up questions answer instantly from the cache, even across sessions.

<p align="center">
  <img src="./assets/session.svg" alt="yt-summary running in an AI agent: a user pastes a YouTube URL and the agent returns a formatted summary" width="880">
</p>

## Install

### 1. Make sure `yt-dlp` is on your `PATH`

It's the only external tool the skill needs. Check first:

```bash
yt-dlp --version
```

If it's not installed:

```bash
brew install yt-dlp              # macOS
pipx install yt-dlp              # cross-platform (preferred)
pip install yt-dlp               # fallback
winget install yt-dlp.yt-dlp     # Windows
```

More install options and standalone binaries at [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp#installation).

### 2. Install the skill in your agent

Jump to the section for the agent you use.

#### Claude Code

```
/plugin marketplace add ultr4nerd/yt-summary
/plugin install yt-summary@yt-summary
```

Installs to `~/.claude/skills/yt-summary/`.

#### Cursor

```bash
npx skills add ultr4nerd/yt-summary
```

Installs to `.agents/skills/yt-summary/` in the current project. Run the command from the project folder you want the skill in.

#### OpenCode

OpenCode needs a skills loader plugin. Install it first:

```bash
npx skills add malhashemi/opencode-skills
```

Then the skill itself:

```bash
npx skills add ultr4nerd/yt-summary
```

Installs to `~/.config/opencode/skills/yt-summary/`.

#### Other agents (40+)

For any agent supported by [vercel-labs/skills](https://github.com/vercel-labs/skills) (auto-detects what you have installed):

```bash
npx skills add ultr4nerd/yt-summary
```

<details>
<summary><b>Shell fallback (no Node.js)</b></summary>

Detects Claude Code / Cursor / OpenCode and installs manually:

```bash
curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh | bash
```

Or force a specific target:

```bash
AGENT=cursor   bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
AGENT=opencode bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
AGENT=claude   bash <(curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh)
```

</details>

## Usage

Once installed, there's nothing to remember — paste a YouTube URL into your agent:

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

The skill grep's the cached transcript and answers with literal quotes — no re-download, even across sessions.

## Your cache

- **Where:** `${XDG_DATA_HOME:-~/.local/share}/yt-summary/`
- **What's inside:** one `.md` file per video with YAML frontmatter (metadata) and the cleaned transcript. Summaries are produced fresh each turn and displayed in chat — they are not persisted.
- **Size:** typically 20–50 KB per video.
- **Clear it at any time:** `rm -rf ~/.local/share/yt-summary/`

<details>
<summary><b>For contributors</b></summary>

### Project layout

```
yt-summary/
├── .claude-plugin/              # Claude Code plugin manifests
├── skills/yt-summary/
│   ├── SKILL.md                 # the skill definition (Anthropic Agent Skills Spec)
│   └── scripts/yt-summary.py    # the bundled script (Python stdlib only)
├── assets/                      # hero SVGs + session screenshot + VHS demo tape
├── tests/test_script.py         # 27 tests, no external deps
└── install.sh                   # shell fallback installer
```

### Requirements for running the script directly

- **Python 3.8+** — preinstalled on modern macOS and every Linux distro. On Windows install from the Microsoft Store or with `winget install Python.Python.3`.
- **yt-dlp** — same install commands as above.

The script is plain Python (stdlib only), so it runs natively on macOS, Linux, and Windows — no WSL, no Git Bash required.

### Running the script standalone

```bash
python3 skills/yt-summary/scripts/yt-summary.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
# Prints: NEW:<path> (first time) or CACHED:<path> (subsequent runs)
```

On Windows use `python` or `py -3` if `python3` is not on `PATH`.

### Running the tests

```bash
python3 tests/test_script.py
```

Covers URL parsing, slug generation, VTT cleanup, and every CLI exit code. The happy-path test requires `yt-dlp` and network access; everything else runs offline.

### Standalone-script demo GIF

`assets/demo.gif` is a VHS-recorded terminal capture of the bundled script running end-to-end (cache miss → cache hit). It's there as a sanity check for people who want to see the plumbing without installing a whole agent.

Regenerate it with [`vhs`](https://github.com/charmbracelet/vhs) (`brew install vhs`):

```bash
find ~/.local/share/yt-summary -name '*efGXZselN64*.md' -delete 2>/dev/null
vhs assets/demo.tape
```

</details>

## License

MIT. See [LICENSE](./LICENSE).
