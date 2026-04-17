# yt-summary demo — regenerate with: vhs assets/demo.tape
# Requires: vhs (brew install vhs)
# Before recording, clear the cache entry so the first run shows NEW:
#   rm -f ~/.local/share/yt-summary/*efGXZselN64*.md

Output "assets/demo.gif"

Set Shell "bash"
Set FontSize 16
Set Width 1100
Set Height 480
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set PlaybackSpeed 1.0

Type "# yt-summary — standalone script demo"
Enter
Sleep 800ms

Type "# First run: downloads captions and caches the transcript"
Enter
Sleep 600ms
Type "python3 skills/yt-summary/scripts/yt-summary.py https://www.youtube.com/watch?v=efGXZselN64"
Enter
Sleep 3500ms

Type "# Second run: cache hit, no network"
Enter
Sleep 600ms
Type "python3 skills/yt-summary/scripts/yt-summary.py https://www.youtube.com/watch?v=efGXZselN64"
Enter
Sleep 1500ms

Type "# Now ask your agent to summarize — transcript is already local."
Enter
Sleep 2000ms
