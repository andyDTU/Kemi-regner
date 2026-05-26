"""
Extend offline ΔHf° database from authoritative sources.

Sources:
- NIST Chemistry WebBook (SRD 69) for neutral species (g/l/s)
- USP PDF table for aqueous ions

Output:
- data/dhf.extended.json
- data/dhf.extended.report.json
"""

from __future__ import annotations

import argparse
import io
import json
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from core.dhf_database import normalizeSpeciesKey


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

NIST_BASE = "https://webbook.nist.gov/chemistry/"
NIST_SEARCH = "https://webbook.nist.gov/cgi/cbook.cgi?Name={name}&Units=SI"
NIST_ID_PAGE = "https://webbook.nist.gov/cgi/cbook.cgi?ID={idcode}&Units=SI"
NIST_MASK_PAGE = "https://webbook.nist.gov/cgi/cbook.cgi?ID={idcode}&Units=SI&Mask={mask}"
ION_PDF_URL = "https://sistemas.eel.usp.br/docentes/arquivos/5817712/TDQ%20I/R-standard_enthalpy_of_formation.pdf"

OUT_JSON = DATA_DIR / "dhf.extended.json"
OUT_REPORT = DATA_DIR / "dhf.extended.report.json"


TARGETS: List[str] = [
    "acetone", "acetonitrile", "benzaldehyde", "benzonitrile", "butanal", "butanone", "butanol",
    "tert-butanol", "1-butanol", "2-butanol", "formaldehyde", "acetaldehyde", "propanal",
    "ethanol", "methanol", "diethyl ether", "dimethyl ether", "methyl tert-butyl ether",
    "tetrahydrofuran", "1,4-dioxane", "benzene", "toluene", "ethylbenzene", "o-xylene", "m-xylene",
    "p-xylene", "styrene", "phenol", "aniline", "nitrobenzene", "chlorobenzene", "bromobenzene",
    "iodobenzene", "fluorobenzene", "o-dichlorobenzene", "p-dichlorobenzene", "trichloroethylene",
    "tetrachloroethylene", "formic acid", "acetic acid", "propionic acid", "benzoic acid",
    "methyl acetate", "ethyl acetate", "dimethyl carbonate", "ethylene carbonate", "ethylene glycol",
    "propylene glycol", "glycerol", "ammonia", "hydrazine", "hydroxylamine", "hydrogen cyanide",
    "hydrogen sulfide", "sulfur dioxide", "sulfur trioxide", "carbon disulfide", "carbonyl sulfide",
    "nitric oxide", "nitrous oxide", "nitrogen dioxide", "dinitrogen tetroxide", "dinitrogen pentoxide",
    "hydrogen chloride", "hydrogen bromide", "hydrogen iodide", "hydrogen fluoride", "chlorine monoxide",
    "chlorine dioxide", "hypochlorous acid", "chloric acid", "perchloric acid", "ozone", "hydrogen peroxide",
    "phosgene", "urea", "silane", "disilane", "silicon tetrachloride", "silicon tetrafluoride",
    "boron trifluoride", "boron trichloride", "diborane", "phosphine", "phosphorus trichloride",
    "phosphorus pentachloride", "carbon tetrachloride", "chloroform", "dichloromethane", "chloromethane",
    "bromoform", "nitromethane", "dimethylformamide", "dimethyl sulfoxide", "sulfolane", "hexane",
    "heptane", "octane", "cyclohexane", "methylcyclohexane", "ethylene", "propene", "1-butene",
    "isobutene", "1,3-butadiene", "acetylene", "isopropanol", "diisopropyl ether",
    "methane", "ethane", "propane", "n-butane", "isobutane", "pentane", "isopentane", "neopentane",
    "n-hexane", "n-heptane", "n-octane", "n-nonane", "n-decane", "n-undecane", "n-dodecane",
    "cyclopentane", "cycloheptane", "cyclooctane", "methylcyclopentane", "ethylcyclohexane",
    "1-propanol", "2-propanol", "1-pentanol", "2-pentanol", "1-hexanol", "2-hexanol", "1-heptanol",
    "1-octanol", "1-decanol", "1-dodecanol", "methanal", "ethanal", "2-methylpropanal", "pentanal",
    "hexanal", "heptanal", "octanal", "nonanal", "decanal", "acetophenone", "propiophenone",
    "cyclohexanone", "cyclopentanone", "methyl ethyl ketone", "methyl isobutyl ketone", "diethyl ketone",
    "acrylonitrile", "propionitrile", "butyronitrile", "isobutyronitrile", "valeronitrile", "adiponitrile",
    "ethyl formate", "propyl acetate", "isopropyl acetate", "butyl acetate", "isobutyl acetate",
    "sec-butyl acetate", "tert-butyl acetate", "methyl formate", "ethyl propionate", "methyl propionate",
    "ethyl butyrate", "methyl butyrate", "dimethyl oxalate", "diethyl oxalate", "dimethyl malonate",
    "ethyl lactate", "methyl methacrylate", "ethyl methacrylate", "vinyl acetate", "acetic anhydride",
    "formamide", "acetamide", "N,N-dimethylacetamide", "N-methylformamide", "N-methyl-2-pyrrolidone",
    "tetrahydrofuran", "2-methyltetrahydrofuran", "1,3-dioxolane", "1,2-dimethoxyethane", "diethylene glycol",
    "triethylene glycol", "1,2-propanediol", "1,3-propanediol", "1,4-butanediol", "2,3-butanediol",
    "anisole", "cumene", "indane", "tetralin", "naphthalene", "biphenyl", "diphenyl ether",
    "pyridine", "picoline", "quinoline", "furan", "thiophene", "pyrrole", "imidazole", "piperidine",
    "morpholine", "triethylamine", "diethylamine", "ethylamine", "methylamine", "aniline",
    "chloromethane", "bromomethane", "iodomethane", "fluoromethane", "1,2-dichloroethane",
    "1,1-dichloroethane", "1,1,1-trichloroethane", "1,1,2-trichloroethane", "vinyl chloride",
    "allyl chloride", "benzyl chloride", "chloropropane", "2-chloropropane", "1-bromopropane", "2-bromopropane",
    "methyl chloride", "methylene chloride", "ethyl chloride", "ethyl bromide", "ethyl iodide",
    "carbon monoxide", "carbon dioxide", "water", "sulfur hexafluoride", "sulfur tetrafluoride",
    "nitric acid", "hydrobromic acid", "hydroiodic acid", "hydrochloric acid", "hydrofluoric acid",
]


@dataclass
class FetchResult:
    key: str
    value: float
    source: str
    source_url: str


NUM_RE = re.compile(r"[−–—]")
VALUE_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)")
ID_RE = re.compile(r"ID=([A-Za-z0-9]+)")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_num_text(text: str) -> str:
    return NUM_RE.sub("-", text)


def load_json(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {normalizeSpeciesKey(k): v for k, v in data.items() if isinstance(v, dict)}


def existing_keys_for_baseline(base_db: Path) -> set[str]:
    baseline = load_json(base_db)
    for p in [DATA_DIR / "dhf.openstax.tableG1.json", DATA_DIR / "dhf.exampack.json", DATA_DIR / "dhf.json"]:
        baseline.update(load_json(p))
    return set(baseline.keys())


def resolve_nist_id(session: requests.Session, name: str) -> Optional[str]:
    url = NIST_SEARCH.format(name=quote(name))
    response = session.get(url, timeout=40)
    response.raise_for_status()
    html = response.text
    matches = ID_RE.findall(html)
    if not matches:
        return None
    counts = Counter(matches)
    # Prefer most frequent ID occurrence; this usually corresponds to the main species page.
    return counts.most_common(1)[0][0]


def extract_formula(session: requests.Session, idcode: str) -> Optional[str]:
    url = NIST_ID_PAGE.format(idcode=idcode)
    response = session.get(url, timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    strings = list(soup.stripped_strings)
    indices = [i for i, token in enumerate(strings) if token == "Formula"]
    for idx in indices:
        if idx + 2 >= len(strings) or strings[idx + 1] != ":":
            continue
        formula_parts: List[str] = []
        for token in strings[idx + 2:]:
            if token == "Molecular weight":
                break
            formula_parts.append(token)
        if not formula_parts:
            continue
        formula = "".join(formula_parts)
        formula = re.sub(r"\s+", "", formula)
        if formula:
            return formula
    return None


def pick_numeric(cells: List[str], start_idx: int = 0) -> Optional[float]:
    for cell in cells[start_idx:]:
        norm = normalize_num_text(cell)
        m = VALUE_RE.search(norm)
        if not m:
            continue
        try:
            return float(m.group(1))
        except ValueError:
            continue
    return None


def extract_phase_dhf(session: requests.Session, idcode: str, phase: str) -> Tuple[Optional[float], int]:
    phase_map = {"g": (1, "gas"), "l": (2, "liquid"), "s": (2, "solid")}
    mask, phase_word = phase_map[phase]

    url = NIST_MASK_PAGE.format(idcode=idcode, mask=mask)
    response = session.get(url, timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    candidates: List[float] = []
    for tr in soup.find_all("tr"):
        cells = [" ".join(td.stripped_strings) for td in tr.find_all(["th", "td"])]
        if len(cells) < 2:
            continue
        row0 = normalize_num_text(cells[0]).lower()
        if "Δ" not in cells[0] and "delta" not in row0:
            continue
        if "f" not in row0 or "h" not in row0:
            continue
        if phase_word not in row0:
            continue
        if len(cells) > 2 and "kj/mol" not in normalize_num_text(cells[2]).lower() and "kj/mol" not in " ".join(normalize_num_text(c).lower() for c in cells):
            continue

        value = pick_numeric([cells[1]], start_idx=0)
        if value is None:
            continue
        candidates.append(value)

    if not candidates:
        return None, 0

    return candidates[0], len(candidates)


def nist_entries_for_name(session: requests.Session, name: str) -> Tuple[List[FetchResult], List[str]]:
    warnings: List[str] = []
    idcode = resolve_nist_id(session, name)
    if not idcode:
        return [], [f"NIST ID not found for: {name}"]

    formula = extract_formula(session, idcode)
    if not formula:
        return [], [f"Formula not found for: {name} (ID={idcode})"]

    # Restrict to neutral species for NIST path.
    if re.search(r"[+-]", formula):
        return [], [f"Skipped charged species from NIST neutral flow: {name} -> {formula}"]

    out: List[FetchResult] = []
    for phase in ["g", "l", "s"]:
        val, n_candidates = extract_phase_dhf(session, idcode, phase)
        if val is None:
            continue
        if n_candidates > 1:
            warnings.append(f"Multiple ΔHf candidates for {formula}({phase}); selected first value {val}")
        key = normalizeSpeciesKey(f"{formula}({phase})")
        out.append(
            FetchResult(
                key=key,
                value=float(val),
                source="NIST Chemistry WebBook SRD 69 (standard enthalpy of formation)",
                source_url=NIST_MASK_PAGE.format(idcode=idcode, mask=1 if phase == "g" else 2),
            )
        )
    if not out:
        warnings.append(f"No parseable ΔHf found for {name} (ID={idcode})")
    return out, warnings


def parse_ion_pdf_entries(session: requests.Session) -> Tuple[List[FetchResult], List[str]]:
    warnings: List[str] = []
    response = session.get(ION_PDF_URL, timeout=80)
    response.raise_for_status()
    reader = PdfReader(io.BytesIO(response.content))
    if len(reader.pages) < 2:
        return [], ["Ion PDF did not contain expected pages"]

    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    text = normalize_num_text(text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("−", "-")

    # Match forms like "SO4 2-(aq) -907.5" or "Na+(aq) -239.7".
    pattern = re.compile(
        r"([A-Za-z][A-Za-z0-9()]*\s*(?:\d+\s*[+-]|[+-])?)\s*\(aq\)\s*([+-]?\d+(?:\.\d+)?)"
    )

    found: Dict[str, FetchResult] = {}
    for ion_raw, val_raw in pattern.findall(text):
        ion = normalize_num_text(ion_raw.strip())
        ion = re.sub(r"\s+(\d+)\s*([+-])$", r"^\1\2", ion)
        ion = re.sub(r"\s+", "", ion)
        ion = re.sub(r"(?<!\^)(\d+)([+-])$", r"^\1\2", ion)
        key = normalizeSpeciesKey(f"{ion}(aq)")
        try:
            value = float(val_raw)
        except ValueError:
            continue
        found[key] = FetchResult(
            key=key,
            value=value,
            source="USP PDF – Standard Enthalpy of Formation for Atomic and Molecular Ions",
            source_url=ION_PDF_URL,
        )

    if not found:
        warnings.append("No ion entries parsed from USP PDF")
    return list(found.values()), warnings


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_extended_db(base_db_path: Path, out_path: Path, out_report: Path, min_new: int) -> int:
    existing = existing_keys_for_baseline(base_db_path)
    retrieved_utc = utc_now_iso()

    session = requests.Session()
    session.headers.update({"User-Agent": "chem-calc-dhf-extender/1.0"})

    added: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []
    warnings: List[str] = []
    nist_added = 0
    ion_added = 0

    for name in TARGETS:
        entries, warns = nist_entries_for_name(session, name)
        warnings.extend(warns)
        if not entries:
            failures.append(f"NIST miss: {name}")
            continue

        was_added_for_name = False
        for entry in entries:
            if entry.key in existing or entry.key in added:
                continue
            added[entry.key] = {
                "dhf_kj_per_mol": float(entry.value),
                "source": entry.source,
                "source_url": entry.source_url,
                "retrieved_utc": retrieved_utc,
            }
            nist_added += 1
            was_added_for_name = True

        if len(added) >= min_new:
            break
        if not was_added_for_name:
            failures.append(f"No new key from NIST target: {name}")

    ion_entries, ion_warnings = parse_ion_pdf_entries(session)
    warnings.extend(ion_warnings)
    for entry in ion_entries:
        if entry.key in existing or entry.key in added:
            continue
        added[entry.key] = {
            "dhf_kj_per_mol": float(entry.value),
            "source": entry.source,
            "source_url": entry.source_url,
            "retrieved_utc": retrieved_utc,
        }
        ion_added += 1

    added_sorted = dict(sorted(added.items()))
    write_json(out_path, added_sorted)

    rng = random.Random(42)
    sample_keys = list(added_sorted.keys())
    sample = rng.sample(sample_keys, k=min(20, len(sample_keys))) if sample_keys else []

    report = {
        "generated_utc": retrieved_utc,
        "base_db": str(base_db_path),
        "output": str(out_path),
        "existing_key_count": len(existing),
        "added_key_count": len(added_sorted),
        "added_from_nist": nist_added,
        "added_from_ion_pdf": ion_added,
        "random_sample": [{"key": k, **added_sorted[k]} for k in sample],
        "failures": failures,
        "warnings": warnings,
    }
    write_json(out_report, report)

    print("ΔHf extension completed")
    print(f"Existing keys (baseline): {len(existing)}")
    print(f"New keys added total: {len(added_sorted)}")
    print(f"  - from NIST: {nist_added}")
    print(f"  - from ion PDF: {ion_added}")
    print("20 random new entries:")
    for item in report["random_sample"]:
        print(f"  - {item['key']}: {item['dhf_kj_per_mol']} [{item['source']}]")
    print(f"Failures logged: {len(failures)}")

    if len(added_sorted) < min_new:
        print(
            f"ERROR: Added only {len(added_sorted)} keys (< {min_new}). "
            f"See {out_report} for details.",
            file=sys.stderr,
        )
        return 2
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extend ΔHf DB from NIST + USP ion PDF")
    parser.add_argument("--base-db", default=str(DATA_DIR / "dhf.json"), help="Path to existing db for baseline de-dup")
    parser.add_argument("--out", default=str(OUT_JSON), help="Output JSON for new extension layer")
    parser.add_argument("--report", default=str(OUT_REPORT), help="Output report JSON path")
    parser.add_argument("--min-new", type=int, default=150, help="Minimum number of newly added keys")
    args = parser.parse_args(argv)

    return build_extended_db(
        base_db_path=Path(args.base_db),
        out_path=Path(args.out),
        out_report=Path(args.report),
        min_new=int(args.min_new),
    )


if __name__ == "__main__":
    raise SystemExit(main())
