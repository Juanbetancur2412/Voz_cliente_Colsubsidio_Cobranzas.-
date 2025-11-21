# src/pipeline.py
from pathlib import Path
from datetime import datetime
import json

from .transcriber import transcribe_file_with_deepgram
from .analyzer import analyze_voc
from .exporter import export_to_excel
from .config import VOC_MAX_CALLS_PER_BATCH


def process_calls(input_dir: Path, output_dir: Path, additional_service: str | None = None):
    """
    Procesa las llamadas:
    1. Recorre los audios de la carpeta de entrada.
    2. Omite los audios que ya fueron procesados (según processed_calls.json).
    3. Transcribe cada nuevo audio con Deepgram.
    4. Analiza Voz del Cliente con OpenAI (servicio, conoce, voz, bucket).
    5. Exporta/actualiza un Excel con las columnas:
    - Número de llamada
    - Documento
    - Edad
    - Sexo
    - Ciudad 
    - Fecha de llamada
    - Número cliente
    - TMO
    - Tipo de gestión
    - Voz de cliente (Resultado de la gestion) (bucket general)
    - Voz de cliente zoom (Motivo de caída) (Texto especifico)       
    - Total o rango de la Deuda        
    - Responsable de no aceptación               
    - Fraude
    - Tipo de fraude 
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    # Archivo donde se guarda el historial de audios ya procesados
    processed_ids_file = output_dir / "processed_calls.json"

    # 1) Cargar IDs ya procesados (stems de los archivos de audio)
    if processed_ids_file.exists():
        try:
            with processed_ids_file.open("r", encoding="utf-8") as f:
                processed_ids = set(json.load(f))
        except Exception as e:
            print(f"[WARN] No se pudo leer processed_calls.json ({e}). Se reinicia el historial.")
            processed_ids = set()
    else:
        processed_ids = set()

    # 2) Listar todos los audios en la carpeta de entrada
    audio_files = list(input_dir.glob("*"))
    if not audio_files:
        print("No se encontraron audios en la carpeta de entrada.")
        export_to_excel([], output_dir)
        return

    # Filtrar solo audios nuevos (no procesados aún)
    new_audio_files = [f for f in audio_files if f.stem not in processed_ids]

    print(f"Total de audios en carpeta: {len(audio_files)}")
    print(f"Audios ya procesados (según JSON): {len(processed_ids)}")
    print(f"Audios NUEVOS por procesar: {len(new_audio_files)}")

    if not new_audio_files:
        print("No hay llamadas nuevas por procesar. Fin del proceso.")
        return

    # Limitar cuántas llamadas nuevas se procesan por ejecución
    if len(new_audio_files) > VOC_MAX_CALLS_PER_BATCH:
        print(f"Se procesarán solo las primeras {VOC_MAX_CALLS_PER_BATCH} llamadas nuevas para este batch.")
        new_audio_files = new_audio_files[:VOC_MAX_CALLS_PER_BATCH]

    processed_data = []

    # 3) Procesar solo los audios nuevos
    for idx, audio_file in enumerate(new_audio_files, start=1):
        print(f"\nProcesando: {audio_file.name}")

        # 3.1) Transcripción con Deepgram
        transcript = transcribe_file_with_deepgram(audio_file)

        # 3.2) Análisis Voz del Cliente (servicio, conoce, voz, bucket, sentimiento)
        voc_data = analyze_voc(transcript)

        # ----- LOG DE LO QUE DETECTA EL ANALYSIS -----
        print(f"[VOC] Servicio detectado: {voc_data.get('additional_service')}")
        print(f"[VOC] Conoce servicio:    {voc_data.get('knows_additional_service')}")
        print(f"[VOC] Bucket:             {voc_data.get('voice_bucket')}")
        print(f"[VOC] Voz Zoom:           {voc_data.get('customer_voice')}")
        print(f"[VOC] Sentimiento:        {voc_data.get('sentiment')}")

        # 3.3) Parsear nombre del archivo
        # Formato esperado:
        # documento_fechaHora_min_seg_numeroCliente_TMO.ext
        # ej: 53134176_2025-11-01 10_48_49_3164660199_54.mp3
        file_name = audio_file.stem
        partes = file_name.split("_")

        # Documento asesor
        documento = partes[0] if len(partes) >= 1 else ""

        # Número cliente y TMO: usamos los dos últimos elementos
        numero_cliente = partes[-2] if len(partes) >= 2 else ""
        tmo = partes[-1] if len(partes) >= 1 else ""

        # Fecha de llamada
        fecha_llamada = ""
        if len(partes) >= 2:
            # partes[1] = "2025-11-01 10"
            fecha_hora_bruta = partes[1]
            solo_fecha = fecha_hora_bruta.split(" ")[0]  # "2025-11-01"
            try:
                dt = datetime.strptime(solo_fecha, "%Y-%m-%d")
                fecha_llamada = dt.strftime("%d-%m-%Y")  # "01-11-2025"
            except Exception:
                fecha_llamada = solo_fecha  # fallback

        # 3.4) Agregar registro a la lista de filas nuevas
        processed_data.append({
            # Este número es solo el consecutivo dentro del batch de audios nuevos
            "Número de llamada": idx,
            "Documento": documento,
            "Fecha de llamada": fecha_llamada,
            "Número cliente": numero_cliente,
            "TMO": tmo,
            "Servicio adicional": voc_data.get("additional_service", ""),
            "Voz de cliente": voc_data.get("voice_bucket", ""),
            "Voz cliente Zoom": voc_data.get("customer_voice", ""),
            "Conoce (Si/No)": voc_data.get("knows_additional_service", ""),
            "Sentimiento": voc_data.get("sentiment", ""),
        })

        # 3.5) Marcar este audio como procesado (usamos el nombre sin extensión como ID)
        processed_ids.add(audio_file.stem)

    # 4) Guardar el historial actualizado de audios procesados
    try:
        with processed_ids_file.open("w", encoding="utf-8") as f:
            json.dump(sorted(processed_ids), f, ensure_ascii=False, indent=2)
        print(f"\nHistorial de llamadas procesadas actualizado en: {processed_ids_file}")
    except Exception as e:
        print(f"[WARN] No se pudo guardar processed_calls.json: {e}")

    # 5) Exportar/actualizar Excel con las NUEVAS filas
    export_to_excel(processed_data, output_dir)
