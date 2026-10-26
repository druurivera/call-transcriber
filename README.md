# Call Transcriber

Local Whisper transcription for discovery calls. Taglish aware. No API cost, nothing
leaves your machine. Two modes: a recording you already have, or live during the call.

## Quick start (no terminal typing)

**Mac**
1. Download this repo as a zip (green "Code" button → "Download ZIP") and extract it.
2. Double-click **`setup.command`**. If macOS says it's from an "unidentified
   developer" and won't open, **right-click it → Open** instead, then confirm. That's
   a one-time thing for any script downloaded from the internet, not specific to this
   one. Installs Homebrew (if you don't have it) and the required packages, then
   downloads the Whisper model and runs a test transcription on a bundled sample
   clip, so the model is already cached before you try it on a real call. Takes a
   few minutes the first time; safe to run again later.
3. To transcribe a call: drag the audio file onto **`Call Transcriber.app`**.

**Windows**
1. Download this repo as a zip and extract it.
2. Double-click **`setup.bat`**. If "Windows protected your PC" (SmartScreen) shows
   up, click **More info → Run anyway**, that's a one-time thing for any script
   downloaded from the internet. If it installs Python/ffmpeg for the first time, it
   will tell you to close the window and double-click it again, that's expected. It
   also downloads the Whisper model and runs a test transcription on a bundled
   sample clip, so it's cached before your first real call.
3. To transcribe a call: drag the audio file onto **`process_call.bat`**, type the
   prospect name when it asks, press Enter.

That's it for most people. Everything below is the manual path (more control, needed
for live mode and two-channel recording) or for troubleshooting the quick start.

`sample-call.wav` in this repo is just the setup test clip (a few seconds, nothing
sensitive), not a real call. The throwaway note it generates during setup is
deleted automatically each run; the clip itself stays so setup can reuse it.

## Manual install

### Mac

```bash
brew install ffmpeg portaudio python@3.12
cd ~/call-transcriber
/opt/homebrew/bin/python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

### Windows

`mlx-whisper` (the Mac/Apple Silicon engine) is skipped entirely, so use
`requirements-windows.txt` instead of `requirements.txt`. `ENGINE=auto` already
falls back to `faster-whisper` (CPU) when `mlx_whisper` isn't installed, no
code changes needed.

```powershell
winget install Gyan.FFmpeg
winget install Python.Python.3.12
cd call-transcriber
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-windows.txt
copy .env.example .env
```

Everywhere below that says `./.venv/bin/python script.py`, run
`.\.venv\Scripts\python.exe script.py` instead. `process_call.ps1` and
`record.ps1` are the Windows equivalents of `process_call.sh` and
`record.sh`; the AppleScript droplet app (`Call Transcriber.app`) is Mac only.

**Running the .ps1 scripts.** Windows blocks running `.ps1` files by default
("running scripts is disabled on this system"). `process_call.bat` and `record.bat`
already handle this for you (drag a file onto `process_call.bat`, or double-click
`record.bat`). Calling the `.ps1` files directly needs the bypass flag, this only
affects that one invocation, nothing permanent gets changed:

```powershell
powershell -ExecutionPolicy Bypass -File .\process_call.ps1 -Audio call.m4a -Prospect "Name"
powershell -ExecutionPolicy Bypass -File .\record.ps1 -Name "Arcenith"
```

Model downloads itself on first run, about 1.6GB, cached in `~/.cache/huggingface`
(`%USERPROFILE%\.cache\huggingface` on Windows).

## Mode 1: a recording you already have

Phone voice memos, Zoom files, anything ffmpeg reads.

```bash
cd ~/call-transcriber
./.venv/bin/python transcribe.py ~/Downloads/arcenith.m4a --prospect "Arcenith"
```

Writes a Markdown note to the vault. If `10 - Projects/Arcenith.../` exists it goes in
that project under `Calls/`, otherwise it lands in `00 - Inbox/Call Transcripts/`.

Two channel recording (see mode 3) gets real speaker labels for free:

```bash
./.venv/bin/python transcribe.py call.wav --prospect "Techwork" --split --speakers "You,COO"
```

## Mode 2: live during the call

```bash
./.venv/bin/python live.py --list                    # find your input device
./.venv/bin/python live.py --prospect "Arcenith"
```

Prints each phrase as it lands and appends to a note in the vault. Leave that note open
in Obsidian on the iPad or second window and it updates itself. Ctrl+C ends the call and
writes the buying signals summary.

Phrases flush after 0.7s of silence, so text appears a few seconds behind the speaker.
That is the tradeoff for accuracy: Whisper needs a complete phrase to get Tagalog right.

**Audio source.** With no extra setup it uses the built in mic, so put the call on
speaker. For clean audio and free speaker separation, install BlackHole and build an
Aggregate Device (see mode 3), then pass `--device`.

## Mode 3: two channel recording, free speaker labels

One time setup, needs your admin password:

```bash
brew install --cask blackhole-2ch
```

Then in **Audio MIDI Setup**:
1. Plus button, Create Aggregate Device.
2. Tick your microphone, then tick BlackHole 2ch. Mic first.
3. Name it "Call Recorder".
4. In the Meet or Zoom output settings, send the call audio to BlackHole.

Now `./record.sh Arcenith` writes a 2 channel WAV: you on the left, them on the right.
Transcribe it with `--split` and every line is attributed correctly, with no
speaker detection model and no error rate.

**Windows equivalent.** Install VB-Audio Virtual Cable instead of BlackHole, set it
as the call app's output device, then run `ffmpeg -list_devices true -f dshow -i dummy`
once to get the exact device name and pass it to `.\record.ps1 -Device "audio=..."`.

## Taglish tuning

Whisper is inconsistent on code switching, so the config is measured, not guessed:

```bash
./.venv/bin/python transcribe.py ~/Downloads/real-call.m4a --compare
```

Runs four configurations on the same audio and prints them side by side with speed:
forced English with the Taglish primer, forced English without it, forced Tagalog, and
auto detect. Read them and pick the one where Tagalog words stay Tagalog and the peso
figures are right. Put the winner in `.env` as `LANGUAGE=`.

The primer is a sentence of Taglish vocabulary in `engine.py` that biases the decoder.
Add client specific words to it (clinic names, product names) to improve accuracy.

## Mode 4: the analysis pass

```bash
./.venv/bin/python analyze.py "/path/to/the/transcript.md"
```

Appends the five qualifying gates, objections quoted, buying signals, what you promised,
next actions, and a draft follow up in the prospect's own register. Needs
`OPENROUTER_API_KEY` in `.env`. Costs well under a cent per call on DeepSeek.

## Consent

Philippines RA 4200 makes recording a private conversation without every party's consent
a criminal offence. Open every call with it and let the recording capture the yes:

> "I record my calls so I can write the proposal properly, is that okay with you?"

## Notes for this machine

M1 MacBook Air, 8GB, fanless. `large-v3-turbo` is the default for that reason. Full
`large-v3` is roughly twice the memory and several times slower here, so only reach for
it with `MODEL=mlx-community/whisper-large-v3` if turbo fails the Taglish comparison.

Close Meet or Zoom before running a long file mode transcription. On 8GB the two fight.
