@echo off
echo ==============================================================================
echo   ESP32 Acoustic Direction of Arrival (DoA) TinyML Platform
echo ==============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv.
    echo Please run installation or setup first.
    pause
    exit /b 1
)

echo [1/3] Checking DSP Benchmark...
test_dsp.exe
echo.

echo [2/3] Checking Model and Document Assets...
if exist "IEEE_Acoustic_DoA_Internship_Report.pdf" (
    echo   - IEEE Report PDF: Ready
)
if exist "Acoustic_DoA_Internship_Presentation.pptx" (
    echo   - Presentation PPTX: Ready
)
if exist "doa_model_int8.tflite" (
    echo   - Quantized int8 Model: Ready (2.89 KB)
)
echo.

echo [3/3] Launching Interactive DoA Dashboard on http://localhost:8000 ...
start http://localhost:8000
.\.venv\Scripts\python.exe server.py
