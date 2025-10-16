@echo off
chcp 65001 >nul
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
python main.py %*

