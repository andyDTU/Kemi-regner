"""
Run this script ONCE before an exam (with internet access) to download
all structure images locally.  After that, the app works fully offline.

Usage:
    python3 scripts/download_structure_images.py

Re-running is safe: already-downloaded files are skipped.
Previously failed downloads are retried automatically.
"""

import os
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Ensure we run inside the project's virtual environment so all packages
# (periodictable etc.) are available without manual activation.
import subprocess

_REPO_ROOT = Path(__file__).resolve().parent.parent
_VENV_DIR = _REPO_ROOT / ".venv"

# Python executable path differs between Mac/Linux and Windows
if sys.platform == "win32":
    _VENV_PYTHON = _VENV_DIR / "Scripts" / "python.exe"
else:
    _VENV_PYTHON = _VENV_DIR / "bin" / "python3"

if not _VENV_PYTHON.exists():
    print("Opretter virtuelt miljø og installerer pakker (kun første gang, ~1-2 min)...")
    subprocess.check_call([sys.executable, "-m", "venv", str(_VENV_DIR)])
    subprocess.check_call([str(_VENV_PYTHON), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    subprocess.check_call([str(_VENV_PYTHON), "-m", "pip", "install", "--quiet",
                           "-r", str(_REPO_ROOT / "requirements.txt")])
    print("Pakker installeret.\n")

# sys.prefix is the venv root when running inside a venv — reliable on all platforms
if Path(sys.prefix) != _VENV_DIR:
    if sys.platform == "win32":
        # os.execv doesn't work well on Windows — use subprocess instead
        result = subprocess.run([str(_VENV_PYTHON)] + sys.argv)
        sys.exit(result.returncode)
    else:
        os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

# Add repo root to path so we can import molecule_db
sys.path.insert(0, str(_REPO_ROOT))

from core.molecule_db import SUBSTANCES

OUT_DIR = _REPO_ROOT / "data" / "structure_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/PNG?image_size=large"
TIMEOUT = 15
MAX_RETRIES = 3


def _fetch_png(term: str) -> "bytes | None":
    url = PUBCHEM_URL.format(quote(term))
    req = Request(url, headers={"User-Agent": "kemi-regner-offline/1.0"})
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=TIMEOUT) as resp:
                if resp.status == 200 and "image" in resp.headers.get("Content-Type", ""):
                    return resp.read()
                return None  # non-200 or wrong content type — no point retrying
        except HTTPError as e:
            if e.code == 404:
                return None  # not found — no point retrying
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)  # 2s, 4s backoff
        except (URLError, Exception):
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
    return None


def main() -> None:
    substances = SUBSTANCES
    total = len(substances)
    found = 0
    skipped = 0
    failed = 0

    print(f"Downloader strukturbilleder for {total} stoffer til {OUT_DIR}\n")
    print("Tip: scriptet kan afbrydes og genstartes — allerede hentede billeder springes over.\n")

    for i, s in enumerate(substances, 1):
        dest = OUT_DIR / f"{s.id}.png"

        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            print(f"[{i:3}/{total}] ⏭  {s.id} (allerede hentet)")
            continue

        # Try English name first, then Danish, then formula
        search_terms = [t for t in [s.name_en, s.name_da, s.formula] if t]
        data = None
        used_term = None
        for term in search_terms:
            data = _fetch_png(term)
            if data:
                used_term = term
                break

        if data:
            dest.write_bytes(data)
            found += 1
            label = f"({used_term})" if used_term != s.name_da else ""
            print(f"[{i:3}/{total}] ✅  {s.id} {s.name_da} {label}")
        else:
            failed += 1
            print(f"[{i:3}/{total}] ❌  {s.id} ({s.name_da}) – ikke fundet på PubChem")

        # Be polite to PubChem (max ~3 req/sec)
        time.sleep(0.35)

    print(f"\nFærdig: {found} hentet, {skipped} sprunget over, {failed} ikke fundet.")
    if failed:
        print(f"Tip: kør scriptet igen for at prøve de {failed} fejlede stoffer igen.")
    print(f"Billeder gemt i: {OUT_DIR}")


if __name__ == "__main__":
    main()
