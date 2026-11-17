@echo off
chcp 65001 > nul

set PYTHONPATH=%~dp0
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe

if "%~1"=="" (
    "%PYTHON_EXE%" -m src.app --username admin --password admin
) else (
    "%PYTHON_EXE%" -m src.app %*
)