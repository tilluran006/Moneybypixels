"""Free voiceover with Kokoro (open-weight, Apache 2.0). No account, key or credits.

The model files are downloaded once from the kokoro-onnx GitHub releases and cached.
Default voice: bm_george (British male), chosen by the owner on 26 Nov 2026.

Write voiceover text in words, not digits or symbols ("fifty-one thousand rupees",
not "₹51,486"), so it is read the way we want.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

CACHE = Path.home() / ".cache" / "mbp-tts"
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {"kokoro.onnx": "kokoro-v1.0.int8.onnx", "voices.bin": "voices-v1.0.bin"}
VOICE, LANG, SPEED = "bm_george", "en-gb", 1.1
SR = 24000

_engine = None


def ensure_model() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for local, remote in FILES.items():
        f = CACHE / local
        if not f.exists() or f.stat().st_size < 1_000_000:
            subprocess.run(["curl", "-sSL", "-m", "600", "-o", str(f), BASE + remote], check=True)


def engine():
    global _engine
    if _engine is None:
        ensure_model()
        from kokoro_onnx import Kokoro
        _engine = Kokoro(str(CACHE / "kokoro.onnx"), str(CACHE / "voices.bin"))
    return _engine


def say(text: str, voice: str = VOICE, speed: float = SPEED) -> np.ndarray:
    """Return mono float32 audio at 24 kHz."""
    samples, sr = engine().create(text, voice=voice, speed=speed, lang=LANG)
    assert sr == SR
    return np.asarray(samples, dtype=np.float32)


def check_text(text: str) -> list[str]:
    errs = []
    if any(ch.isdigit() for ch in text) or "₹" in text or "%" in text:
        errs.append(f"voiceover must spell out numbers and symbols in words: {text[:60]!r}")
    return errs
