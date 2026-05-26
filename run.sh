#!/bin/bash
# Starter Chemistry Calculator på Mac
# Dobbeltklik på denne fil i Finder — eller kør: bash run.sh

set -e
cd "$(dirname "$0")"

VENV_DIR=".venv"

# Opret virtuelt miljø første gang
if [ ! -d "$VENV_DIR" ]; then
    echo "Opretter virtuelt Python-miljø..."
    python3 -m venv "$VENV_DIR"
fi

# Aktivér
source "$VENV_DIR/bin/activate"

# Installer/opdatér pakker
echo "Tjekker pakker..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Start app
echo ""
echo "Starter Chemistry Calculator — åbner i browser..."
echo "Stop med Ctrl+C"
echo ""
streamlit run app.py --server.headless false
