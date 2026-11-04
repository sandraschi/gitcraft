@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\gitcraft-cli.exe" (
    ".venv\Scripts\gitcraft-cli.exe" %*
) else (
    uv run gitcraft-cli %*
)
