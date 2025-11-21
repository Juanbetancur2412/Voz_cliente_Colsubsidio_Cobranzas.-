# src/exporter.py
from pathlib import Path
from datetime import datetime
import pandas as pd


def export_to_excel(data, output_dir: Path):
    """
    Exporta la información de Voz del Cliente a un Excel.

    Columnas:
    - Número de llamada
    - Documento
    - Edad
    - Sexo
    - Ciudad 
    - Fecha de llamada
    - Número cliente
    - TMO
    - Tipo de gestión
    - Voz de cliente (Resultado de la gestion)                (bucket general: asepta, no asepta / volver a llamar.)
    - Voz de cliente zoom (Motivo de caída)        
    - Total o rango de la Deuda        
    - Responsable de no aceptación               
    - Fraude
    - Tipo de fraude 
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = "voz_cliente_fidelizacion_IA.xlsx"
    output_file = output_dir / base_name

    columnas = [
         "Número de llamada",
         "Documento",
         "Edad",
         "Sexo",
         "Ciudad",
         "Fecha de llamada",
         "Número cliente",
         "TMO",
         "Tipo de gestión",
         "Voz de cliente (Resultado de la gestión)",                
         "Voz de cliente zoom (Motivo de caída)",        
         "Total o rango de la Deuda",        
         "Responsable de no aceptación",               
         "Fraude",
         "Tipo de fraude"
    ]

    # DataFrame con las nuevas filas
    if not data:
        print("No hay datos NUEVOS procesados en este lote.")
        df_new = pd.DataFrame(columns=columnas)
    else:
        df_new = pd.DataFrame(data)
        df_new = df_new.reindex(columns=columnas)

    # Intentar leer el Excel existente (para acumular)
    if output_file.exists():
        try:
            df_existing = pd.read_excel(output_file)
            # Aseguramos que tenga las mismas columnas, en caso de versiones anteriores
            df_existing = df_existing.reindex(columns=columnas)
            print(f"Se cargaron {len(df_existing)} filas existentes desde: {output_file}")
        except Exception as e:
            print(f"⚠ No se pudo leer el Excel existente ({e}). Se creará uno nuevo.")
            df_existing = None
    else:
        df_existing = None

    # Combinar existente + nuevas filas
    if df_existing is not None and not df_existing.empty:
        df = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df = df_new

    # Si no hay nada (ni antes ni ahora), igual creamos el archivo vacío
    if df.empty:
        print("No hay datos para escribir en el Excel (archivo quedará vacío).")

    # Intentamos sobrescribir el archivo; si está abierto, guardamos con timestamp
    try:
        df.to_excel(output_file, index=False)
        print(f"Excel exportado con éxito: {output_file}")
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt_file = output_dir / f"voz_cliente_fidelizacion_IA_{ts}.xlsx"
        df.to_excel(alt_file, index=False)
        print(
            f"⚠ No se pudo sobrescribir '{output_file}' (probablemente está abierto). "
            f"Se guardó en: {alt_file}"
        )
