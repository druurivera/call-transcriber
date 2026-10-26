#!/usr/bin/env bash
# Double-click this file in Finder to set up Call Transcriber. Safe to run again.
set -e
cd "$(dirname "$0")"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Install it first from https://brew.sh, then run this file again."
  read -p "Press Enter to close..." _
  exit 1
fi

echo "Installing ffmpeg, portaudio, python (skips anything already installed)..."
brew install ffmpeg portaudio python@3.12

echo ""
echo "Setting up the virtual environment..."
/opt/homebrew/bin/python3.12 -m venv .venv
./.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env. Edit it later if you want the analysis pass (OPENROUTER_API_KEY)."
fi

echo ""
echo "Done. Drag an audio file onto 'Call Transcriber.app' to transcribe it,"
echo "or run: ./.venv/bin/python transcribe.py yourfile.m4a --prospect \"Name\""
read -p "Press Enter to close..." _
