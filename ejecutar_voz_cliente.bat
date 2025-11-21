@echo off
REM === Ir a la carpeta del proyecto ===
cd /d "C:\Desarrollos\Voz_cliente_fidelizacion"

REM === (Opcional) Activar entorno virtual si tuvieras uno ===
REM call .venv\Scripts\activate.bat

REM === Ejecutar el proceso de Python ===
python main.py

echo.
echo ==============================================
echo   Proceso de Voz del Cliente finalizado.
echo ==============================================
echo.
pause
