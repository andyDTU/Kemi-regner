"""
Run this script ONCE before an exam (with internet access) to download
all structure images locally.  After that, the app works fully offline.

Usage:
    python scripts/download_structure_images.py
"""

import os
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Add repo root to path so we can import molecule_db
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.molecule_db import ALL_SUBSTANCES

OUT_DIR = Path(__file__).parent.parent / "data" / "structure_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/PNG?image_size=large"
TIMEOUT = 10


def _safe_filename(substance_id: str) -> Path:
    return OUT_DIR / f"{substance_id}.png"


def _fetch_png(term: str) -> bytes | None:
    url = PUBCHEM_URL.format(quote(term))
    req = Request(url, headers={"User-Agent": "kemi-regner-offline/1.0"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status == 200 and "image" in resp.headers.get("Content-Type", ""):
                return resp.read()
    except (HTTPError, URLError, Exception):
        pass
    return None


def main() -> None:
    substances = ALL_SUBSTANCES
    total = len(substances)
    found = 0
    skipped = 0
    failed = 0

    print(f"Downloader strukturbilleder for {total} stoffer til {OUT_DIR}\n")

    for i, s in enumerate(substances, 1):
        dest = _safe_filename(s.id)

        if dest.exists():
            skipped += 1
            print(f"[{i:3}/{total}] ⏭  {s.id} (allerede hentet)")
            continue

        # Try English name first, then Danish, then formula
        search_terms = [t for t in [s.name_en, s.name_da, s.formula] if t]
        data = None
        for term in search_terms:
            data = _fetch_png(term)
            if data:
                break

        if data:
            dest.write_bytes(data)
            found += 1
            print(f"[{i:3}/{total}] ✅  {s.id} ({s.name_da})")
        else:
            failed += 1
            print(f"[{i:3}/{total}] ❌  {s.id} ({s.name_da}) – ikke fundet")

        # Be polite to PubChem (max ~3 req/sec)
        time.sleep(0.35)

    print(f"\nFærdig: {found} hentet, {skipped} sprunget over, {failed} ikke fundet.")
    print(f"Billeder gemt i: {OUT_DIR}")


if __name__ == "__main__":
    main()
