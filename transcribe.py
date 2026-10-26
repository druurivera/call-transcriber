#!/usr/bin/env python3
"""
File mode. Transcribe a recording (phone voice memo, Zoom, Meet, anything ffmpeg reads)
into a vault note. Handles mono and two channel (mic left, prospect right).

  python transcribe.py CALL.m4a --prospect "Arcenith"
  python transcribe.py CALL.wav --prospect "Techwork" --split --speakers "You,COO"
  python transcribe.py CALL.m4a --compare        # Taglish config benchmark
"""
import argparse, json, os, subprocess, sys, tempfile, time
import engine, vaultout


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True, text=True,
    )
    data = json.loads(out.stdout or "{}")
    dur = float(data.get("format", {}).get("duration", 0) or 0)
    ch = 1
    for s in data.get("streams", []):
        if s.get("codec_type") == "audio":
            ch = int(s.get("channels", 1))
            break
    return dur, ch


def to_wav(src, dst, channel=None):
    """16kHz mono wav. channel=0 left, 1 right, None downmix."""
    cmd = ["ffmpeg", "-y", "-i", src]
    if channel is not None:
        cmd += ["-af", f"pan=mono|c0=c{channel}"]
    else:
        cmd += ["-ac", "1"]
    cmd += ["-ar", "16000", "-vn", dst]
    subprocess.run(cmd, capture_output=True, check=True)


def run(path, language, prompt, eng, model):
    t0 = time.time()
    segs, lang = engine.transcribe(path, language=language, prompt=prompt, engine=eng, model=model)
    return segs, lang, time.time() - t0


def compare(src, tmp, eng, model):
    """Run the Taglish matrix so the config picks itself."""
    wav = os.path.join(tmp, "cmp.wav")
    to_wav(src, wav)
    dur, _ = probe_duration(wav)
    configs = [
        ("forced en + primer", "en", engine.TAGLISH_PRIMER),
        ("forced en, no primer", "en", None),
        ("forced tl + primer", "tl", engine.TAGLISH_PRIMER),
        ("auto detect + primer", "auto", engine.TAGLISH_PRIMER),
    ]
    print(f"\nBenchmark on {os.path.basename(src)} ({vaultout.ts(dur)} of audio)\n")
    blocks = []
    for name, lang, pr in configs:
        try:
            segs, detected, took = run(wav, lang, pr, eng, model)
        except Exception as e:
            print(f"  {name}: FAILED, {e}")
            continue
        text = " ".join(s[2] for s in segs)
        speed = dur / took if took else 0
        print(f"  {name}: {took:.0f}s ({speed:.1f}x realtime), detected={detected}, {len(text)} chars")
        blocks.append((name, detected, took, speed, text[:1200]))
    print("\n" + "=" * 70)
    for name, detected, took, speed, sample in blocks:
        print(f"\n### {name}  [{speed:.1f}x realtime, detected {detected}]\n")
        print(sample)
    print("\n" + "=" * 70)
    print("\nPick the config where Tagalog words stay Tagalog and the peso figures are right.")
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--prospect", default="Unknown")
    ap.add_argument("--lang", default=os.getenv("LANGUAGE", "en"))
    ap.add_argument("--split", action="store_true", help="two channel: left=you, right=them")
    ap.add_argument("--speakers", default="You,Prospect")
    ap.add_argument("--engine", default=os.getenv("ENGINE", "auto"))
    ap.add_argument("--model", default=os.getenv("MODEL"))
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--no-primer", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.audio):
        sys.exit(f"No such file: {a.audio}")

    prompt = None if a.no_primer else engine.TAGLISH_PRIMER
    me, them = (a.speakers.split(",") + ["Prospect"])[:2]

    with tempfile.TemporaryDirectory() as tmp:
        if a.compare:
            compare(a.audio, tmp, a.engine, a.model)
            return

        dur, channels = probe_duration(a.audio)
        rows = []

        if a.split and channels >= 2:
            print(f"Two channel file. Transcribing {me} and {them} separately.")
            for idx, who in ((0, me), (1, them)):
                wav = os.path.join(tmp, f"ch{idx}.wav")
                to_wav(a.audio, wav, channel=idx)
                segs, lang, took = run(wav, a.lang, prompt, a.engine, a.model)
                print(f"  {who}: {len(segs)} segments in {took:.0f}s")
                rows += [(s, who, t) for s, _, t in segs]
            rows.sort(key=lambda r: r[0])
            language = a.lang
        else:
            if a.split:
                print("Warning: file is mono, cannot split speakers. Continuing as one track.")
            wav = os.path.join(tmp, "mono.wav")
            to_wav(a.audio, wav)
            segs, language, took = run(wav, a.lang, prompt, a.engine, a.model)
            speed = dur / took if took else 0
            print(f"{len(segs)} segments in {took:.0f}s ({speed:.1f}x realtime)")
            rows = [(s, "Speaker", t) for s, _, t in segs]

        note = vaultout.write_note(rows, a.prospect, a.audio, language, dur)
        print(f"\nSaved: {note}")


if __name__ == "__main__":
    main()
