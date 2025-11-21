from pathlib import Path
from src.pipeline import process_calls
from src.config import AUDIO_INPUT_DIR, VOC_MAX_CALLS_PER_BATCH

if __name__ == "__main__":
    # Definir las rutas
    input_dir = Path(AUDIO_INPUT_DIR)  # Carpeta donde están las llamadas
    output_dir = Path('./output')  # Carpeta de salida para los resultados

    # Servicio adicional para esta campaña de fidelización
    additional_service = "Netflix"  # Aquí puedes ajustar según el servicio adicional de cada llamada

    # Procesar las llamadas y exportar el resultado a Excel
    process_calls(input_dir, output_dir, additional_service)
