#!/bin/sh
# Chains transcribe.py then analyze.py in one call.
# Usage inside the container: ./run.sh /app/incoming/call.mov "KJR"
set -e

AUDIO="$1"
PROSPECT="$2"

if [ -z "$AUDIO" ] || [ -z "$PROSPECT" ]; then
    echo "Usage: run.sh <audio_or_video_path> <prospect_name>"
    exit 1
fi

echo "Transcribing..."
OUT=$(python transcribe.py "$AUDIO" --prospect "$PROSPECT")
echo "$OUT"

NOTE=$(echo "$OUT" | grep "^Saved:" | sed 's/^Saved: //')

if [ -z "$NOTE" ]; then
    echo "Could not find the saved note path, skipping analysis."
    exit 1
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "OPENROUTER_API_KEY not set, transcript is done but analysis was skipped."
    exit 0
fi

echo ""
echo "Running analysis..."
python analyze.py "$NOTE"

echo ""
echo "Done. Full result at: $NOTE"
