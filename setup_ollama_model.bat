@echo off
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama was not found on PATH.
  echo Install Ollama for Windows from https://ollama.com/download and reopen this terminal.
  exit /b 1
)
echo Pulling CPU-friendly SmolLM2 360M instruct Q4 model...
ollama pull smollm2:360m-instruct-q4_0
if errorlevel 1 exit /b 1
echo.
echo Model ready. Run:
echo   python run_tests.py --engine ollama --quick
echo Then:
echo   python run_tests.py --engine ollama
