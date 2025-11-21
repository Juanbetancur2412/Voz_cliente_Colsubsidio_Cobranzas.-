# src/analyzer.py
from openai import OpenAI
from .config import OPENAI_API_KEY
import json

# ===================== Cliente OpenAI =====================
client = OpenAI(api_key=OPENAI_API_KEY)

# ===================== Diccionario de servicios =====================
SERVICE_SYNONYMS = {
    "amazon prime": "Amazon Prime",
    "prime video": "Amazon Prime",
    "hbo max": "HBO Max",
    "hbo": "HBO Max",
    "netflix": "Netflix",
    "disney+": "Disney+",
    "disney plus": "Disney+",
    "star+": "Star+",
    "star plus": "Star+",
    "paramount+": "Paramount+",
    "paramount plus": "Paramount+",
    "claro video": "Claro Video",
}

def detect_additional_service(transcript: str) -> str:
    """
    Detecta el servicio adicional mencionado en la transcripción
    usando coincidencias de palabras clave y las unifica a un nombre canónico.
    """
    if not transcript:
        return "No identificado"

    t = transcript.lower()
    for pattern, canonical in SERVICE_SYNONYMS.items():
        if pattern in t:
            return canonical

    return "No identificado"


# ===================== Diccionario de sentimiento =====================
POSITIVE_KEYWORDS = [
    "gracias", "perfecto", "bien", "excelente", "resuelto",
    "funciona", "funcionando", "activado", "activada",
    "ok", "listo", "genial", "todo claro", "muy amable"
]

NEGATIVE_KEYWORDS = [
    "error", "no funciona", "no me funciona", "cansado", "cansada",
    "problema", "problemas", "lento", "demorado", "molesto",
    "inconforme", "inconformidad", "reclamo", "no me sirve",
    "no quiero", "no entiendo", "cobro", "cobros"
]

def classify_sentiment(text: str) -> str:
    """
    Clasifica el sentimiento en positivo / negativo / neutral
    usando un diccionario de palabras clave.
    Si hay mezcla de positivo y negativo, se marca neutral.
    """
    if not text:
        return "neutral"

    lower = text.lower()
    has_pos = any(k in lower for k in POSITIVE_KEYWORDS)
    has_neg = any(k in lower for k in NEGATIVE_KEYWORDS)

    if has_pos and not has_neg:
        return "positivo"
    if has_neg and not has_pos:
        return "negativo"
    # mezcla o nada detectado
    return "neutral"


# ===================== Buckets de Voz del Cliente =====================

VALID_BUCKETS = {
    "No, fui a la oficina y no pude",
    "No, me sale error",
    "No, no lo he activado",
    "No, no sabía",
    "No, nunca lo hice",
    "Sí, el técnico lo activó",
    "Sí, lo uso",
    "Sí, ya está activo.",
    "Sí, ya hice la activación",
    "Sí, ya lo tengo",
}


# ===================== Función principal de análisis =====================

def analyze_voc(customer_transcript: str) -> dict:
    """
    Analiza la transcripción de UNA llamada (campaña Fidelización) y devuelve:

    - additional_service: servicio adicional detectado (Netflix, HBO Max, Amazon Prime, etc.)
    - knows_additional_service: "Si" | "No"
    - customer_voice: resumen corto en palabras del cliente (texto libre)
    - voice_bucket: una de las frases generales predefinidas
    - sentiment: "positivo" | "negativo" | "neutral" (por diccionario)
    """

    # 1) Detectamos servicio adicional por heurística (palabras clave)
    service_guess = detect_additional_service(customer_transcript)

    # 2) Construimos el prompt para OpenAI (VOZ, CONOCE y BUCKET)
    prompt = f"""
Eres analista de Voz del Cliente para una campaña de fidelización de servicios adicionales.

A partir de la siguiente transcripción de una llamada (en español), debes:

1. Confirmar cuál es el servicio adicional del que realmente habla el cliente
   (por ejemplo: Netflix, HBO Max, Amazon Prime, Disney+, Star+, Paramount+, Claro Video).
2. Indicar si el cliente conocía (o sabía que tenía) ese servicio adicional.
3. Resumir en una frase corta la voz del cliente frente a ese servicio.
4. Clasificar la voz del cliente en UNA de las siguientes frases EXACTAS (elige la que mejor represente lo que dice el cliente):

- "No, fui a la oficina y no pude"
- "No, me sale error"
- "No, no lo he activado"
- "No, no sabía"
- "No, nunca lo hice"
- "Sí, el técnico lo activó"
- "Sí, lo uso"
- "Sí, ya está activo."
- "Sí, ya hice la activación"
- "Sí, ya lo tengo"

YA tenemos una detección automática preliminar del servicio: "{service_guess}".
Tú debes validar si es correcto según el contenido de la llamada; si no lo es, corrígelo.

Devuelve EXCLUSIVAMENTE un JSON VÁLIDO con esta estructura:

{{
  "additional_service": "Netflix" | "HBO Max" | "Amazon Prime" | "Disney+" | "Star+" | "Paramount+" | "Claro Video" | "Otro" | "No identificado",
  "knows_additional_service": "Si" o "No",
  "customer_voice": "frase corta que resuma en palabras del cliente su percepción del servicio adicional",
  "voice_bucket": "UNA de las frases de la lista anterior, copiada EXACTAMENTE"
}}

Reglas:
- "knows_additional_service" debe ser EXACTAMENTE "Si" o "No" (sin tilde).
- "voice_bucket" debe ser EXACTAMENTE una de las frases de la lista, sin inventar otras.
- Si no se identifica claramente ningún servicio adicional, usa:
  - "additional_service": "No identificado"
  - "knows_additional_service": "No"
  - "customer_voice": explica que no se evidencia conocimiento del servicio.
  - Para "voice_bucket" en ese caso, usa: "No, no sabía".
- No incluyas texto antes ni después del JSON.
- No inventes servicios ni frases que no tengan relación con la transcripción.

Transcripción de la llamada:

\"\"\"{customer_transcript}\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # o el modelo de chat que estés utilizando
        messages=[
            {
                "role": "system",
                "content": "Eres un analista de calidad para call center y SIEMPRE devuelves JSON válido con las claves indicadas."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # ---- Parseo robusto del JSON devuelto ----
    try:
        data = json.loads(raw)
    except Exception:
        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last != -1 and last > first:
            data = json.loads(raw[first:last + 1])
        else:
            raise ValueError(f"No se pudo parsear JSON desde la respuesta del modelo:\n{raw}")

    add_service = (data.get("additional_service") or "").strip()
    knows = (data.get("knows_additional_service") or data.get("knows") or "").strip()
    voice = (data.get("customer_voice") or data.get("voz_cliente") or "").strip()
    voice_bucket = (data.get("voice_bucket") or "").strip()

    # Normalizar servicio si viene vacío
    if not add_service:
        add_service = service_guess if service_guess != "No identificado" else "No identificado"

    # Normalizar Si/No
    if knows.lower().startswith("s"):
        knows_norm = "Si"
    else:
        knows_norm = "No"

    # Normalizar bucket (fallback si viene vacío o mal)
    if voice_bucket not in VALID_BUCKETS:
        # Si el modelo no respetó la lista, usamos un valor por defecto
        voice_bucket = "No, no sabía"

    # Sentimiento basado en DICCIONARIO, no en el modelo
    sentiment = classify_sentiment(voice if voice else customer_transcript)

    return {
        "additional_service": add_service,
        "knows_additional_service": knows_norm,
        "customer_voice": voice,
        "voice_bucket": voice_bucket,
        "sentiment": sentiment,
    }
