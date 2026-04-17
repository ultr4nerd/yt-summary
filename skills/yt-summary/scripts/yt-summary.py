#!/usr/bin/env python3
"""yt-summary — download and cache the cleaned transcript of a YouTube video.

Usage: yt-summary.py <youtube-url>

Output to stdout (one line):
  CACHED:<path>    if the video is already in the local cache
  NEW:<path>       if the video was just downloaded and a new cache entry was written

Cache location: $XDG_DATA_HOME/yt-summary/ (defaults to ~/.local/share/yt-summary/)
Each cached file is a markdown document with YAML frontmatter, a "## Summary"
section (initially a placeholder), and the full cleaned transcript.

Exit codes:
  0 — success
  1 — invalid or missing URL, or Python too old
  2 — yt-dlp not installed
  3 — video has no subtitles
  4 — yt-dlp failure (network, private video, geo-block, etc.)
"""
from __future__ import annotations

import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

MIN_PYTHON = (3, 8)


def ensure_supported_python() -> None:
    if sys.version_info[:2] >= MIN_PYTHON:
        return
    major, minor, micro = sys.version_info[:3]
    sys.stderr.write(
        "yt-summary requires Python 3.8+.\n"
        f"Detected Python {major}.{minor}.{micro}.\n"
        "Install a newer Python from https://www.python.org/ "
        "or your system package manager.\n"
    )
    raise SystemExit(1)


ensure_supported_python()

# Windows: make stdout/stderr UTF-8 so emojis and non-ASCII titles don't crash.
if os.name == "nt":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def cache_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    d = Path(base) / "yt-summary"
    d.mkdir(parents=True, exist_ok=True)
    return d


def extract_video_id(url: str) -> Optional[str]:
    match = re.search(
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)"
        r"([A-Za-z0-9_-]{11})",
        url,
    )
    return match.group(1) if match else None


def find_cached(video_id: str) -> Optional[Path]:
    for path in cache_dir().glob(f"*{video_id}*.md"):
        return path
    return None


def require_yt_dlp() -> str:
    path = shutil.which("yt-dlp")
    if path:
        return path
    sys.stderr.write(
        "ERROR: yt-dlp is not installed.\n"
        "Install with one of:\n"
        "  brew install yt-dlp              # macOS\n"
        "  pipx install yt-dlp              # cross-platform\n"
        "  pip install yt-dlp               # fallback\n"
        "  winget install yt-dlp.yt-dlp     # Windows\n"
    )
    raise SystemExit(2)


def download_subtitles(
    yt_dlp: str, url: str, tmp: Path
) -> Tuple[Optional[Path], str]:
    """Download subtitles into `tmp`. Return (first_vtt, log).

    yt-dlp may exit non-zero when one requested language fails (e.g. HTTP 429 on
    the second language) while another succeeds. We therefore ignore the exit
    code and decide based on whether any .vtt landed on disk.
    """
    result = subprocess.run(
        [
            yt_dlp,
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "en,es,en-US,es-419",
            "--sub-format", "vtt",
            "-o", str(tmp / "yt.%(ext)s"),
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    log = (result.stdout or "") + (result.stderr or "")
    vtts = sorted(tmp.glob("*.vtt"))
    return (vtts[0] if vtts else None), log


def fetch_metadata(yt_dlp: str, url: str) -> List[str]:
    """Return [title, channel, duration, upload_date, views]."""
    result = subprocess.run(
        [
            yt_dlp,
            "--skip-download",
            "--print",
            "%(title)s\t%(channel)s\t%(duration_string)s\t%(upload_date)s\t%(view_count)s",
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write("ERROR: yt-dlp failed to fetch metadata\n")
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise SystemExit(4)
    parts = (result.stdout.strip() or "").split("\t")
    while len(parts) < 5:
        parts.append("")
    return parts[:5]


def clean_vtt(vtt: Path) -> str:
    """Strip WEBVTT headers, timing cues, inline <c> tags, and duplicate lines."""
    raw = vtt.read_text(encoding="utf-8", errors="replace")
    lines: List[str] = []
    seen: set = set()
    skip_prefixes = ("WEBVTT", "Kind:", "Language:", "NOTE")
    tag_pattern = re.compile(r"<[^>]+>")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(skip_prefixes) or "-->" in line:
            continue
        cleaned = tag_pattern.sub("", line).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            lines.append(cleaned)
    return " ".join(lines)


def build_slug(title: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]+", "", title).lower().split()[:6]
    return "-".join(words) or "untitled"


def normalize_date(yyyymmdd: str) -> str:
    if yyyymmdd and len(yyyymmdd) == 8 and yyyymmdd.isdigit():
        return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
    return yyyymmdd


def write_cache_file(
    video_id: str, url: str, metadata: List[str], transcript: str
) -> Path:
    title, channel, duration, upload_date, views = metadata
    upload_date = normalize_date(upload_date)
    slug = build_slug(title)
    today = datetime.date.today().isoformat()
    filename = f"{today}-{video_id}-{slug}.md"
    path = cache_dir() / filename
    content = (
        "---\n"
        f"video_id: {video_id}\n"
        f"title: {title}\n"
        f"channel: {channel}\n"
        f"duration: {duration}\n"
        f"upload_date: {upload_date}\n"
        f"views: {views}\n"
        f"url: {url}\n"
        f"cached_at: {today}\n"
        "---\n\n"
        "## Transcript\n\n"
        f"{transcript}\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def main(argv: List[str]) -> int:
    if len(argv) < 2 or not argv[1]:
        sys.stderr.write("Usage: yt-summary.py <youtube-url>\n")
        return 1

    url = argv[1]
    video_id = extract_video_id(url)
    if not video_id:
        sys.stderr.write(f"ERROR: could not extract video ID from URL: {url}\n")
        return 1

    cached = find_cached(video_id)
    if cached is not None:
        print(f"CACHED:{cached}")
        return 0

    yt_dlp = require_yt_dlp()

    with tempfile.TemporaryDirectory(prefix="yt-summary-") as tmp_str:
        tmp = Path(tmp_str)
        vtt, log = download_subtitles(yt_dlp, url, tmp)
        if vtt is None:
            sys.stderr.write("ERROR: could not fetch subtitles. yt-dlp output:\n")
            tail = "\n".join(log.splitlines()[-10:])
            sys.stderr.write(tail + "\n")
            return 3

        metadata = fetch_metadata(yt_dlp, url)
        transcript = clean_vtt(vtt)
        path = write_cache_file(video_id, url, metadata, transcript)
        print(f"NEW:{path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
