#!/usr/bin/env python3
"""
Real time mode. Listens to an input device, transcribes as you talk, prints to the
terminal and appends to a note in the vault that you can leave open in Obsidian.

  python live.py --list                      # see input devices
  python live.py --prospect "Arcenith"       # default mic, phone on speaker
  python live.py --device 3 --prospect "X"   # aggregate device with BlackHole
"""
import argparse, datetime, os, queue, sys, threading, time
import numpy as np
import sounddevice as sd
import engine, vaultout

SR = 16000
BLOCK = 1024
SILENCE_HOLD = 0.7     # seconds of quiet that ends a phrase
MIN_CHUNK = 1.5        # do not bother Whisper with anything shorter
MAX_CHUNK = 22.0       # force a flush before Whisper's 30s window
CALIBRATE = 1.0        # seconds of room tone to learn the noise floor


class Live:
    def __init__(self, args):
        self.a = args
        self.audio_q = queue.Queue()
        self.work_q = queue.Queue()
        self.rows = []
        self.t0 = time.time()
        self.floor = None
        self.running = True
        self.note = self._note_path()

    def _note_path(self):
        d = datetime.date.today().isoformat()
        p = vaultout.resolve_path(self.a.prospect, d)
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                f"---\ntype: call-transcript\nstatus: live\n"
                f"tags: [call, transcript, live]\nupdated: \"{d}\"\n---\n\n"
                f"# Live Call, {self.a.prospect}\n\n"
                f"Started {datetime.datetime.now():%H:%M}. Consent confirmed before recording.\n\n"
            )
        return p

    def _cb(self, indata, frames, t, status):
        if status:
            pass
        self.audio_q.put(indata[:, 0].copy())

    def _append(self, line):
        with open(self.note, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _worker(self):
        while self.running or not self.work_q.empty():
            try:
                start, chunk = self.work_q.get(timeout=0.3)
            except queue.Empty:
                continue
            try:
                segs, _ = engine.transcribe(
                    chunk, language=self.a.lang,
                    prompt=engine.TAGLISH_PRIMER,
                    engine=self.a.engine, model=self.a.model,
                )
            except Exception as e:
                print(f"  [transcribe failed: {e}]", file=sys.stderr)
                continue
            text = " ".join(s[2] for s in segs).strip()
            if not text or len(text) < 2:
                continue
            stamp = vaultout.ts(start)
            hit = next((k for k in vaultout.SIGNALS if k in text.lower()), None)
            mark = f"  <-- {hit.upper()}" if hit else ""
            print(f"[{stamp}] {text}{mark}", flush=True)
            self.rows.append((start, self.a.speaker, text))
            self._append(f"`{stamp}` {text}" + (f"  **[{hit}]**" if hit else ""))

    def run(self):
        threading.Thread(target=self._worker, daemon=True).start()
        buf = []
        quiet = 0.0
        speaking = False
        seg_start = 0.0
        cal = []
        cal_until = time.time() + CALIBRATE
        per_block = BLOCK / SR

        print(f"Listening. Note: {self.note}")
        print("Calibrating room tone, stay quiet for a second.\n")

        with sd.InputStream(samplerate=SR, channels=1, blocksize=BLOCK,
                            device=self.a.device, callback=self._cb, dtype="float32"):
            try:
                while True:
                    block = self.audio_q.get()
                    rms = float(np.sqrt(np.mean(block ** 2)) + 1e-9)

                    if self.floor is None:
                        cal.append(rms)
                        if time.time() >= cal_until:
                            self.floor = max(float(np.median(cal)) * 3.0, 0.004)
                            print(f"Ready. Speech threshold {self.floor:.4f}\n")
                        continue

                    loud = rms > self.floor
                    now = time.time() - self.t0

                    if loud:
                        if not speaking:
                            speaking = True
                            seg_start = now
                            buf = []
                        quiet = 0.0
                        buf.append(block)
                    elif speaking:
                        buf.append(block)
                        quiet += per_block

                    dur = len(buf) * per_block
                    if speaking and (quiet >= SILENCE_HOLD or dur >= MAX_CHUNK):
                        if dur >= MIN_CHUNK:
                            self.work_q.put((seg_start, np.concatenate(buf).astype(np.float32)))
                        speaking = False
                        quiet = 0.0
                        buf = []
            except KeyboardInterrupt:
                print("\nStopping, draining the queue.")

        self.running = False
        time.sleep(0.5)
        while not self.work_q.empty():
            time.sleep(0.5)
        self._append("\n_Call ended._\n")
        if self.rows:
            hits = vaultout.find_signals(self.rows)
            if hits:
                self._append("\n## Buying signals\n")
                for s, sp, kw, tx in hits:
                    self._append(f"- `{vaultout.ts(s)}` **{kw}**: {tx}")
        print(f"Saved: {self.note}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--device", type=int, default=None)
    ap.add_argument("--prospect", default="Live Call")
    ap.add_argument("--speaker", default="Call")
    ap.add_argument("--lang", default=os.getenv("LANGUAGE", "en"))
    ap.add_argument("--engine", default=os.getenv("ENGINE", "auto"))
    ap.add_argument("--model", default=os.getenv("MODEL"))
    a = ap.parse_args()

    if a.list:
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                print(f"{i}: {d['name']}  ({d['max_input_channels']} in)")
        return
    Live(a).run()


if __name__ == "__main__":
    main()
