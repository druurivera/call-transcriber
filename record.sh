#!/usr/bin/env bash
# Two channel recorder. Left = your mic, right = the other side (via BlackHole).
# Needs an Aggregate Device set up once in Audio MIDI Setup.
#   ./record.sh Arcenith
set -euo pipefail
NAME="${1:-call}"
DEV="${AVF_DEVICE:-:0}"          # ffmpeg -f avfoundation audio device index
OUT="$HOME/call-recordings/$(date +%Y-%m-%d)-${NAME}.wav"
mkdir -p "$(dirname "$OUT")"
echo "Recording to $OUT. Say the consent line now. Ctrl+C to stop."
ffmpeg -f avfoundation -i "$DEV" -ac 2 -ar 48000 "$OUT"
