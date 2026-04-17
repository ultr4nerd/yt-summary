#!/usr/bin/env bash
# Fallback installer for yt-summary — use this if you don't want to go through
# the `npx skills add` flow or the Claude Code `/plugin install` flow.
#
# Detects the first supported agent installed on the machine and copies the
# skill to that agent's user-level skills directory.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ultr4nerd/yt-summary/main/install.sh | bash
#
# Override the target:
#   AGENT=cursor bash install.sh       # force .agents/skills/ in the current dir
#   AGENT=opencode bash install.sh     # force ~/.config/opencode/skills/
#   AGENT=claude bash install.sh       # force ~/.claude/skills/

set -euo pipefail

REPO_RAW="${YT_SUMMARY_REPO_RAW:-https://raw.githubusercontent.com/ultr4nerd/yt-summary/main}"
SKILL_NAME="yt-summary"

detect_agent() {
  # Respect an explicit override.
  if [ -n "${AGENT:-}" ]; then
    echo "$AGENT"
    return
  fi
  # Priority order: Claude Code > Cursor > OpenCode.
  if [ -d "$HOME/.claude" ]; then echo "claude"; return; fi
  if [ -d ".agents" ] || [ -d ".cursor" ]; then echo "cursor"; return; fi
  if [ -d "$HOME/.config/opencode" ]; then echo "opencode"; return; fi
  # Default to Claude Code user-level.
  echo "claude"
}

AGENT=$(detect_agent)
case "$AGENT" in
  claude)   TARGET="$HOME/.claude/skills/$SKILL_NAME" ;;
  cursor)   TARGET=".agents/skills/$SKILL_NAME" ;;
  opencode) TARGET="$HOME/.config/opencode/skills/$SKILL_NAME" ;;
  *)
    echo "ERROR: unknown agent: $AGENT" >&2
    echo "Supported values: claude, cursor, opencode" >&2
    exit 1
    ;;
esac

echo "Installing yt-summary skill for: $AGENT"
echo "Target directory: $TARGET"

mkdir -p "$TARGET/scripts"

curl -fsSL "$REPO_RAW/skills/$SKILL_NAME/SKILL.md" \
  -o "$TARGET/SKILL.md"
curl -fsSL "$REPO_RAW/skills/$SKILL_NAME/scripts/yt-summary.py" \
  -o "$TARGET/scripts/yt-summary.py"
chmod +x "$TARGET/scripts/yt-summary.py"

echo ""
echo "Installed files:"
echo "  $TARGET/SKILL.md"
echo "  $TARGET/scripts/yt-summary.py"

# Warn about missing runtime dependencies.
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo ""
  echo "WARNING: no Python interpreter found. The skill requires Python 3.8+."
  echo "  macOS:   already preinstalled on macOS 12+"
  echo "  Linux:   install via your distro package manager"
  echo "  Windows: winget install Python.Python.3"
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo ""
  echo "WARNING: yt-dlp is not installed. The skill will not work until you install it."
  echo "  macOS:          brew install yt-dlp"
  echo "  cross-platform: pipx install yt-dlp"
  echo "  fallback:       pip install yt-dlp"
  echo "  Windows:        winget install yt-dlp.yt-dlp"
fi

echo ""
echo "Done. Restart your agent (or open a new session) to pick up the new skill."
