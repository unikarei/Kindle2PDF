@echo off
rem ========================================================================
rem Kindle to PDF - Main Execution Script (run_kindle_to_pdf.bat)
rem - Activates virtual environment and runs kindle_to_pdf.py
rem ========================================================================

rem Move to script directory (project root)
cd /d %~dp0

rem Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    .venv\Scripts\python.exe kindle_to_pdf.py
) else (
    echo Virtual environment not found. Using system Python...
    python kindle_to_pdf.py
)

pause
