#!/usr/bin/env python3
"""Tests for yt-summary.py.

No external dependencies — run directly with:

    python3 tests/test_script.py

The happy-path test requires `yt-dlp` on PATH and network access. All other
tests run offline.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = ROOT / "skills" / "yt-summary" / "scripts" / "yt-summary.py"

# A real video with English captions. Used by the happy-path integration test.
TEST_URL = "https://www.youtube.com/watch?v=efGXZselN64"

# An unlikely-to-exist ID — forces the script past the cache check and into
# yt-dlp territory without actually hitting a real video.
FAKE_URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"


# Load yt-summary.py as a module so we can unit-test its pure functions
# without spawning a subprocess for each.
_spec = importlib.util.spec_from_file_location("yt_summary", SCRIPT)
assert _spec and _spec.loader
yt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(yt)


PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        print(f"  ✓ {name}")
        PASS += 1
    else:
        print(f"  ✗ {name}  {detail}")
        FAIL += 1


def run_script(url: str | None, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if extra_env is not None:
        env.update(extra_env)
    argv = [sys.executable, str(SCRIPT)]
    if url is not None:
        argv.append(url)
    return subprocess.run(argv, capture_output=True, text=True, env=env)


# ─── Unit tests: pure functions ────────────────────────────────────────────────

print("extract_video_id:")
check("watch?v=", yt.extract_video_id("https://www.youtube.com/watch?v=efGXZselN64") == "efGXZselN64")
check("youtu.be/", yt.extract_video_id("https://youtu.be/efGXZselN64") == "efGXZselN64")
check("shorts/", yt.extract_video_id("https://www.youtube.com/shorts/efGXZselN64") == "efGXZselN64")
check("embed/", yt.extract_video_id("https://www.youtube.com/embed/efGXZselN64") == "efGXZselN64")
check("with extra query params", yt.extract_video_id("https://www.youtube.com/watch?v=efGXZselN64&t=120s") == "efGXZselN64")
check("non-youtube URL returns None", yt.extract_video_id("https://example.com") is None)
check("playlist-only URL returns None", yt.extract_video_id("https://www.youtube.com/playlist?list=PLabc123") is None)

print("\nbuild_slug:")
check("normal title", yt.build_slug("Claude Code 2.0 Is Here... Automate Anything") == "claude-code-20-is-here-automate")
check("only symbols -> untitled", yt.build_slug("!!!???") == "untitled")
check("caps at 6 words", yt.build_slug("one two three four five six seven eight") == "one-two-three-four-five-six")
check("collapses punctuation", yt.build_slug("Hello, World! It's a test.") == "hello-world-its-a-test")

print("\nnormalize_date:")
check("YYYYMMDD -> YYYY-MM-DD", yt.normalize_date("20260416") == "2026-04-16")
check("empty passthrough", yt.normalize_date("") == "")
check("non-numeric passthrough", yt.normalize_date("abc") == "abc")
check("already-normalized passthrough", yt.normalize_date("2026-04-16") == "2026-04-16")

print("\nclean_vtt:")
with tempfile.NamedTemporaryFile(suffix=".vtt", mode="w", delete=False, encoding="utf-8") as _f:
    _f.write(
        "WEBVTT\n"
        "Kind: captions\n"
        "Language: en\n"
        "\n"
        "00:00:00.000 --> 00:00:02.000\n"
        "Hello world\n"
        "\n"
        "00:00:02.000 --> 00:00:04.000\n"
        "<c.colorFFFFFF>Hello world</c>\n"
        "\n"
        "00:00:04.000 --> 00:00:06.000\n"
        "Another line\n"
    )
    _vtt = Path(_f.name)
check("strips timing/headers/tags and dedupes", yt.clean_vtt(_vtt) == "Hello world Another line")
_vtt.unlink()


# ─── Integration tests: invoke the script as a subprocess ──────────────────────

print("\nscript invocation:")

r = run_script(None)
check("missing URL -> exit 1", r.returncode == 1, f"got {r.returncode}")

r = run_script("not a url")
check("invalid URL -> exit 1", r.returncode == 1, f"got {r.returncode}")

r = run_script("https://www.youtube.com/playlist?list=PLabc123")
check("playlist URL -> exit 1", r.returncode == 1, f"got {r.returncode}")

# Force the script to bypass the cache (via a fake unused ID), then strip PATH
# so shutil.which("yt-dlp") returns None. Should exit 2 with install hint.
r = run_script(FAKE_URL, extra_env={"PATH": ""})
check("no yt-dlp on PATH -> exit 2", r.returncode == 2, f"got {r.returncode}; stderr={r.stderr!r}")
check("stderr mentions yt-dlp install hint", "yt-dlp" in r.stderr and "install" in r.stderr.lower())

# Happy path. If the Jack Roberts video is already in the cache this returns
# instantly; otherwise it makes a real yt-dlp call.
r = run_script(TEST_URL)
check("valid URL -> exit 0", r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}")
check("stdout begins with NEW: or CACHED:", r.stdout.startswith("NEW:") or r.stdout.startswith("CACHED:"))

# Verify the cache file structure the script produced.
prefix, _, path_str = r.stdout.partition(":")
cache_path = Path(path_str.strip())
if cache_path.exists():
    content = cache_path.read_text(encoding="utf-8")
    check("cache file has YAML frontmatter", content.startswith("---\n") and "\n---\n" in content)
    check("cache file has ## Transcript section", "## Transcript\n" in content)
    check("cache file does NOT have ## Summary section", "## Summary" not in content)
    check("cache file does NOT have pending placeholder", "Summary pending" not in content)


# ─── Summary ───────────────────────────────────────────────────────────────────

total = PASS + FAIL
print(f"\n{PASS}/{total} tests passed")
sys.exit(0 if FAIL == 0 else 1)
