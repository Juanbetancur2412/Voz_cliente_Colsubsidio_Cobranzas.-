# src/transcriber.py
import requests
from pathlib import Path
from typing import List
from .config import (
    DEEPGRAM_API_KEY,
    AUDIO_INPUT_DIR,
    TRANSCRIPTS_DIR,
    DEEPGRAM_MODEL,
    DEEPGRAM_LANG,
)

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


def list_audio_files() -> List[Path]:
    """
    Lista los archivos de audio en la carpeta de entrada.
    """
    AUDIO_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    files: List[Path] = []
    for ext in (".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"):
        files.extend(AUDIO_INPUT_DIR.glob(f"*{ext}"))
    return sorted(files)


def transcribe_file_with_deepgram(path: Path) -> str:
    """
    Utiliza la API de Deepgram para transcribir el audio.
    Además:
    - Imprime por consola un resumen de la transcripción.
    - Guarda la transcripción en un .txt para debug.
    """
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
    }

    # 🔑 Aquí ya usamos las variables de entorno DEEPGRAM_MODEL y DEEPGRAM_LANG
    params = {
        "model": DEEPGRAM_MODEL,   # p.ej. nova-3
        "language": DEEPGRAM_LANG, # p.ej. es-419
        # Opcional: formateo inteligente
        # "smart_format": "true",
    }

    with path.open("rb") as audio_file:
        response = requests.post(
            DEEPGRAM_URL,
            headers=headers,
            params=params,
            files={"file": audio_file},
        )

    if response.status_code != 200:
        raise RuntimeError(f"Error en Deepgram [{response.status_code}]: {response.text}")

    data = response.json()
    transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]

    # ----- LOG EN CONSOLA -----
    preview = transcript[:200].replace("\n", " ")
    print(f"[Deepgram] Modelo={DEEPGRAM_MODEL} Idioma={DEEPGRAM_LANG}")
    print(f"[Deepgram] {path.name}: {len(transcript)} caracteres")
    print(f"[Deepgram] Preview: {preview}")

    # ----- GUARDAR TRANSCRIPCIÓN EN TXT PARA REVISAR -----
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = TRANSCRIPTS_DIR / f"{path.stem}.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"[Deepgram] Transcripción guardada en: {txt_path}")

    return transcript
