#!/usr/bin/env bash
# One shot: transcribe a call recording, then run the analysis pass on it,
# then open the finished note. Built for the drag and drop app.
#
#   ./process_call.sh CALL.m4a "Arcenith"
#
set -euo pipefail
cd "$(dirname "$0")"

# Finder/AppleScript droplet launches strip Homebrew from PATH, so ffprobe/ffmpeg
# go missing when this is run by dragging onto Call Transcriber.app.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

AUDIO="${1:?Usage: process_call.sh <audio file> [\"Prospect Name\"]}"
PROSPECT="${2:-Unknown}"

echo "Transcribing: $AUDIO"
echo "Prospect: $PROSPECT"
echo

TRANSCRIBE_OUT="$(./.venv/bin/python transcribe.py "$AUDIO" --prospect "$PROSPECT")"
echo "$TRANSCRIBE_OUT"

NOTE_PATH="$(echo "$TRANSCRIBE_OUT" | grep '^Saved: ' | sed 's/^Saved: //')"

if [ -z "$NOTE_PATH" ]; then
  echo "Could not find the saved note path in transcribe.py output. Stopping before analysis."
  exit 1
fi

KEY="$(grep -m1 '^OPENROUTER_API_KEY=' .env | cut -d= -f2-)"

if [ -n "$KEY" ]; then
  echo
  echo "Running analysis pass..."
  ./.venv/bin/python analyze.py "$NOTE_PATH"
else
  echo
  echo "OPENROUTER_API_KEY is empty in .env, skipping the analysis pass."
  echo "You are getting the raw transcript only."
fi

open "$NOTE_PATH"
