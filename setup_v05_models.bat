@echo off
setlocal
where ollama >nul 2>nul || (echo Ollama not found in PATH. Install/start Ollama first.& exit /b 1)
echo Pulling small CPU-friendly evidence models...
ollama pull smollm2:360m-instruct-q4_0 || exit /b 1
ollama pull qwen2.5:0.5b-instruct-q4_0 || exit /b 1
ollama pull llama3.2:1b-instruct-q4_0 || exit /b 1
echo Done.
