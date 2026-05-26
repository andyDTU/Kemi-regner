#!/bin/bash
# Starter Chemistry Calculator på Mac
# Dobbeltklik på denne fil i Finder — eller kør: bash run.sh

set -e
cd "$(dirname "$0")"

VENV_DIR=".venv"
PORT=8501

# Stop evt. eksisterende instans på porten
if lsof -ti tcp:$PORT >/dev/null 2>&1; then
    echo "Stopper eksisterende instans på port $PORT..."
    lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Opret virtuelt miljø første gang
if [ ! -d "$VENV_DIR" ]; then
    echo "Opretter virtuelt Python-miljø (kun første gang, tager ~1-2 min)..."
    python3 -m venv "$VENV_DIR"
fi

# Aktivér
source "$VENV_DIR/bin/activate"

# Installer/opdatér pakker (hurtigt hvis allerede installeret)
echo "Tjekker pakker..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Slå telemetri fra
mkdir -p ~/.streamlit
if ! grep -q "gatherUsageStats" ~/.streamlit/config.toml 2>/dev/null; then
    echo -e "\n[browser]\ngatherUsageStats = false" >> ~/.streamlit/config.toml
fi

# Start app
echo ""
echo "✅ Starter Chemistry Calculator — åbner i browser på http://localhost:$PORT"
echo "   Stop med Ctrl+C"
echo ""
streamlit run app.py --server.port $PORT --server.headless false
