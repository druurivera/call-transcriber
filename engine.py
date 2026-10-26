"""Whisper engine wrapper. MLX (Apple GPU) primary, faster-whisper (CPU) fallback."""
import os
import wave

import numpy as np

TAGLISH_PRIMER = (
    "Discovery call recording. The speakers switch between English and Tagalog. "
    "Common words: magkano, presyo, bayad, kailan, sige, oo, hindi, pwede, kuya, "
    "ma'am, sir, clinic, pasyente, appointment, booking, solar, kuryente, Meralco, "
    "installation, budget, monthly, installment, quota, GHL, WhatsApp, Facebook."
)

DEFAULT_MLX_MODEL = "mlx-community/whisper-large-v3-turbo"
DEFAULT_FW_MODEL = "large-v3-turbo"


def _mlx(path, language, prompt, model):
    import mlx_whisper
    r = mlx_whisper.transcribe(
        path,
        path_or_hf_repo=model or DEFAULT_MLX_MODEL,
        language=language,
        initial_prompt=prompt,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
        compression_ratio_threshold=2.4,
        temperature=(0.0, 0.2, 0.4),
        verbose=False,
    )
    segs = [(s["start"], s["end"], s["text"].strip()) for s in r["segments"]]
    return segs, r.get("language", language)


def _wav_to_array(path):
    """Read a 16 bit PCM wav straight into a float32 array, bypassing
    faster-whisper's PyAV decode_audio: newer PyAV dropped the
    metadata_errors kwarg it calls av.open() with, so any string/file
    path crashes. An ndarray skips that call entirely."""
    with wave.open(path, "rb") as w:
        raw = w.readframes(w.getnframes())
        channels = w.getnchannels()
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data


def _faster(path, language, prompt, model):
    from faster_whisper import WhisperModel
    audio = path if isinstance(path, np.ndarray) else _wav_to_array(path)
    m = WhisperModel(model or DEFAULT_FW_MODEL, device="cpu", compute_type="int8")
    segments, info = m.transcribe(
        audio,
        language=language,
        initial_prompt=prompt,
        condition_on_previous_text=False,
        vad_filter=True,
        temperature=(0.0, 0.2, 0.4),
    )
    segs = [(s.start, s.end, s.text.strip()) for s in segments]
    return segs, info.language


def transcribe(path, language="en", prompt=TAGLISH_PRIMER, engine=None, model=None):
    """Returns (segments, detected_language). segments = [(start, end, text)]."""
    engine = engine or os.getenv("ENGINE", "auto")
    if language in ("auto", "", None):
        language = None
    if engine in ("auto", "mlx"):
        try:
            return _mlx(path, language, prompt, model)
        except ImportError:
            if engine == "mlx":
                raise
    return _faster(path, language, prompt, model)
