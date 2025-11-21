# src/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# ===== Rutas base =====
BASE_DIR = Path(__file__).resolve().parent.parent

# AUDIO_INPUT_DIR y OUTPUT_DIR como Path (no como str)
AUDIO_INPUT_DIR = Path(os.getenv("AUDIO_INPUT_DIR", BASE_DIR / "input_calls"))
OUTPUT_DIR      = Path(os.getenv("OUTPUT_DIR",      BASE_DIR / "output"))

# Carpeta donde guardaremos transcripciones de debug
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"

# ===== Claves de las API =====
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")

# ===== Configuración de Deepgram =====
# Se leen del .env, pero tienen valores por defecto
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-3")
DEEPGRAM_LANG  = os.getenv("DEEPGRAM_LANG",  "es-419")

# ===== Configuración de análisis de Voz del Cliente =====
# Máximo de caracteres por análisis (por si luego agrupamos transcripciones)
VOC_MAX_CHARS = int(os.getenv("VOC_MAX_CHARS", 20000))

# ⚠️ Se mantiene el máximo de llamadas por batch, como pediste
VOC_MAX_CALLS_PER_BATCH = int(os.getenv("VOC_MAX_CALLS_PER_BATCH", 150))

# Servicio adicional por defecto (ya casi no lo usamos, pero lo dejamos por compatibilidad)
ADDITIONAL_SERVICE = os.getenv("ADDITIONAL_SERVICE", "Netflix")
