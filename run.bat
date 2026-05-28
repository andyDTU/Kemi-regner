@echo off
setlocal
cd /d "%~dp0"

set VENV_DIR=.venv

:: Stop evt. eksisterende streamlit på port 8501
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8501"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Opret virtuelt miljø første gang
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Opretter virtuelt Python-miljo (kun forste gang, tager 1-2 min^)...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo FEJL: Kunne ikke oprette venv. Sikr dig at Python 3.10+ er installeret.
        pause
        exit /b 1
    )
)

:: Installer/opdater pakker
echo Tjekker pakker...
%VENV_DIR%\Scripts\pip install --quiet --upgrade pip
%VENV_DIR%\Scripts\pip install --quiet -r requirements.txt

echo.
echo Starter Chemistry Calculator - aabner i browser paa http://localhost:8501
echo Stop med Ctrl+C
echo.

%VENV_DIR%\Scripts\streamlit run app.py --server.port 8501 --server.headless false
pause
