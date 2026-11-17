@echo off
chcp 65001 > nul

set PYTHONPATH=%~dp0
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe

"%PYTHON_EXE%" -m coverage run --branch --source=src.app,src.client,src.data_layer -m pytest "%~dp0tests\test_mbt.py" -v
"%PYTHON_EXE%" -m coverage report -m