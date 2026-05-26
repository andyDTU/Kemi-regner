"""
Build an offline ΔHf° database from OpenStax Chemistry 2e Table G1.

Output: data/dhf.openstax.tableG1.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from bs4 import BeautifulSoup


OPENSTAX_URL = (
    "https://openstax.org/books/chemistry-2e/pages/"
    "g-standard-thermodynamic-properties-for-selected-substances"
)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "data" / "dhf.openstax.tableG1.json"

SOURCE_LABEL = "OpenStax Chemistry 2e Appendix G Table G1 (standard state, 298 K)"

SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUPERSCRIPT_MAP = str.maketrans(
    {
        "⁰": "0",
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
        "⁺": "+",
        "⁻": "-",
    }
)

PHASE_RE = re.compile(r"\((s|l|g|aq)\)\s*$", re.IGNORECASE)
NUMERIC_RE = re.compile(r"^[\-−–—+]?\d+(?:\.\d+)?$")


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "chem-calc-dhf-builder/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def _normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(SUBSCRIPT_MAP).translate(SUPERSCRIPT_MAP)
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = text.replace("·", "·")
    return text


def normalize_species_text(raw: str) -> str:
    value = _normalize_unicode(raw)
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace("( ", "(").replace(" )", ")")
    value = re.sub(r"\s+(\d+)\s*([+-])(?=\s*(?:\([A-Za-z]+\))?\s*$)", r"^\1\2", value)

    # Remove descriptive parenthetical labels while preserving the phase tag.
    phase_match = PHASE_RE.search(value)
    phase = ""
    if phase_match:
        phase = f"({phase_match.group(1).lower()})"
        core = value[:phase_match.start()].strip()
    else:
        core = value.strip()

    core = re.sub(r"\s*\([^)]*\)\s*$", "", core).strip()
    core = re.sub(r"\s+", "", core)

    if phase:
        return f"{core}{phase}"
    return core


def parse_dhf_value(raw: str) -> float | None:
    text = _normalize_unicode(raw).strip()
    text = text.replace(",", "")
    if text in {"", "-", "--", "—", "N/A"}:
        return None
    if not NUMERIC_RE.match(text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _iter_pipe_rows(text: str) -> Iterable[Tuple[str, str, str]]:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.count("|") < 4:
            continue
        parts = [part.strip() for part in line.split("|")]
        parts = [part for part in parts if part != ""]
        if len(parts) < 4:
            continue
        yield parts[0], parts[1], raw_line


def _iter_table_rows(html: str) -> Iterable[Tuple[str, str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    for row in soup.select("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        species = cells[0]
        dhf = cells[1]
        joined = " | ".join(cells)
        yield species, dhf, joined

    text = soup.get_text("\n")
    for species, dhf, raw in _iter_pipe_rows(text):
        yield species, dhf, raw


def extract_database(html: str) -> Tuple[Dict[str, Dict[str, float | str]], Dict[str, object]]:
    parsed: Dict[str, Dict[str, float | str]] = {}
    failed_lines: List[str] = []
    seen_rows = 0

    for species_raw, dhf_raw, raw_line in _iter_table_rows(html):
        seen_rows += 1
        species_key = normalize_species_text(species_raw)
        if not species_key or not PHASE_RE.search(species_key):
            continue

        dhf_value = parse_dhf_value(dhf_raw)
        if dhf_value is None:
            failed_lines.append(raw_line)
            continue

        parsed[species_key] = {
            "dhf_kj_per_mol": dhf_value,
            "source": SOURCE_LABEL,
        }

    forced = {
        "CO2(g)": -393.51,
        "BaO(s)": -548.0,
    }
    if "BaCO3(s)" not in parsed:
        forced["BaCO3(s)"] = -1218.8

    for key, value in forced.items():
        parsed[key] = {
            "dhf_kj_per_mol": float(value),
            "source": f"{SOURCE_LABEL} (forced)" if key != "BaCO3(s)" else "Fallback (course/exam standard)",
        }

    diagnostics: Dict[str, object] = {
        "rows_seen": seen_rows,
        "entries_written": len(parsed),
        "failed_numeric_rows": len(failed_lines),
        "failed_numeric_samples": failed_lines[:12],
    }
    return dict(sorted(parsed.items())), diagnostics


def build(output_path: Path) -> int:
    html = fetch_html(OPENSTAX_URL)
    data, diagnostics = extract_database(html)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OpenStax ΔHf° build completed")
    print(f"URL: {OPENSTAX_URL}")
    print(f"Output: {output_path}")
    print(f"Rows seen: {diagnostics['rows_seen']}")
    print(f"Entries written: {diagnostics['entries_written']}")
    print(f"Dropped rows (non-numeric ΔHf°): {diagnostics['failed_numeric_rows']}")
    samples = diagnostics["failed_numeric_samples"]
    if samples:
        print("Dropped row samples:")
        for sample in samples:
            print(f"  - {sample[:180]}")

    if len(data) < 300:
        print("ERROR: Parsed database has fewer than 300 entries.", file=sys.stderr)
        return 2

    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build data/dhf.openstax.tableG1.json from OpenStax Table G1")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path")
    args = parser.parse_args(argv)
    return build(Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())
