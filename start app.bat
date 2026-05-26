@echo off
setlocal

cd /d "%~dp0"

echo Starter Chem Calc app i browseren...
py -m streamlit run app.py

if errorlevel 1 (
  echo.
  echo Kunne ikke starte via "py". Prover med "python"...
  python -m streamlit run app.py
)

echo.
echo Appen er stoppet.
pause
