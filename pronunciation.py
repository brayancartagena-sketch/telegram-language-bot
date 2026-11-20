"""Evaluación de pronunciación basada en ASR (Whisper) contra una frase de referencia.

Es un indicador de inteligibilidad (qué tan bien entiende el ASR lo que dijo el
estudiante), no un puntaje fonético tipo GOP. Ver README, sección de limitaciones.
"""
import difflib
import random
import re
import subprocess

import imageio_ffmpeg
import numpy as np

import config

PHRASES = {
    "en": [
        "The weather is very nice today",
        "I would like a cup of coffee please",
        "She sells seashells by the seashore",
        "Thank you for your help yesterday",
    ],
    "fr": [
        "Bonjour, je voudrais un croissant s'il vous plaît",
        "Il fait très beau aujourd'hui",
        "Je ne comprends pas la question",
        "Merci beaucoup pour votre aide",
    ],
}

_asr = None


def _get_asr():
    global _asr
    if _asr is None:
        from transformers import pipeline

        _asr = pipeline("automatic-speech-recognition", model=config.ASR_MODEL, token=config.HF_TOKEN)
    return _asr


def random_phrase(lang: str) -> str:
    return random.choice(PHRASES[lang])


def _norm(text: str) -> list:
    return re.sub(r"[^\w\s']", "", text.lower()).split()


def transcribe(audio_path: str, lang: str) -> str:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [
            ffmpeg,
            "-i",
            audio_path,
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    audio = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if audio.size == 0:
        raise ValueError("No se pudo extraer audio de la nota de voz.")

    kwargs = {"language": config.WHISPER_LANG[lang], "task": "transcribe"}
    result = _get_asr()(
        {"raw": audio, "sampling_rate": 16000}, generate_kwargs=kwargs
    )
    return result["text"].strip()


def assess(audio_path: str, reference: str, lang: str) -> dict:
    heard = transcribe(audio_path, lang)
    ref_words, heard_words = _norm(reference), _norm(heard)
    matcher = difflib.SequenceMatcher(None, ref_words, heard_words)
    hits = sum(block.size for block in matcher.get_matching_blocks())
    score = round(100 * hits / max(len(ref_words), 1))
    wrong = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            wrong.append((" ".join(ref_words[i1:i2]), " ".join(heard_words[j1:j2]) or "(no se oyó)"))
    return {"score": score, "heard": heard, "wrong": wrong}
