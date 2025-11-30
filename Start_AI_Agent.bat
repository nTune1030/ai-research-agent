@echo off
REM --- Switch to the directory where this script is located ---
cd /d "%~dp0"

REM --- 1. Start the AI Engine ---
echo Setting up GPU Optimization...
set OLLAMA_FLASH_ATTENTION=1

echo Waking up Llama 3.1...
start "Ollama Server" ollama serve

REM --- 2. Wait ---
timeout /t 5 /nobreak >nul

REM --- 3. Activate venv (Relative Path) ---
call .venv\Scripts\activate

echo.
echo Starting AI Research Agent...
echo.

REM --- 4. Run app ---
streamlit run app.py --server.address=127.0.0.1

pause