#!/usr/bin/env bash
# Double-click this file in Finder to set up Call Transcriber. Safe to run again.
set -e
cd "$(dirname "$0")"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found, installing it now (you may be asked for your Mac password)..."
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew install didn't finish correctly. Install it manually from https://brew.sh, then run this file again."
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
echo "Downloading the Whisper model and running a quick test (one-time, a few minutes)..."
if VAULT="$(pwd)/.setup-test" ./.venv/bin/python transcribe.py sample-call.wav --prospect "Setup Test"; then
  echo ""
  echo "Setup test passed, model is cached. You're ready."
else
  echo ""
  echo "Setup test failed, something above needs attention before you try a real call."
fi
rm -rf .setup-test

echo ""
echo "Done. Drag an audio file onto 'Call Transcriber.app' to transcribe it,"
echo "or run: ./.venv/bin/python transcribe.py yourfile.m4a --prospect \"Name\""
read -p "Press Enter to close..." _
