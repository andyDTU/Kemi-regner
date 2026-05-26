"""Validation tests for Ka/Kb/pKa/pKb coverage in molecule database."""

import math

from core.molecule_db import SUBSTANCES, get_substance_by_id


KW_25C = 1.0e-14


def _is_acid_or_base(substance) -> bool:
    return (
        substance.category in {"syre", "base"}
        or substance.acid_base_role in {"syre", "base"}
    )


def test_all_acids_and_bases_have_all_constants():
    acids_bases = [s for s in SUBSTANCES if _is_acid_or_base(s)]
    assert acids_bases, "No acid/base substances found in database"

    missing = []
    for s in acids_bases:
        if None in (s.ka, s.kb, s.pka, s.pkb):
            missing.append(s.id)

    assert not missing, f"Missing Ka/Kb/pKa/pKb for: {missing}"


def test_all_acids_and_bases_are_internal_consistent():
    acids_bases = [s for s in SUBSTANCES if _is_acid_or_base(s)]

    for s in acids_bases:
        assert s.ka is not None and s.ka > 0, f"Invalid Ka for {s.id}"
        assert s.kb is not None and s.kb > 0, f"Invalid Kb for {s.id}"
        assert s.pka is not None, f"Missing pKa for {s.id}"
        assert s.pkb is not None, f"Missing pKb for {s.id}"

        assert math.isclose(s.pka, -math.log10(s.ka), rel_tol=0.0, abs_tol=1e-9), f"pKa mismatch for {s.id}"
        assert math.isclose(s.pkb, -math.log10(s.kb), rel_tol=0.0, abs_tol=1e-9), f"pKb mismatch for {s.id}"
        assert math.isclose(s.ka * s.kb, KW_25C, rel_tol=0.0, abs_tol=1e-18), f"Ka*Kb != Kw for {s.id}"
        assert math.isclose(s.pka + s.pkb, 14.0, rel_tol=0.0, abs_tol=1e-9), f"pKa+pKb != 14 for {s.id}"


def test_ten_concrete_reference_values():
    # 10 concrete reference checks for known substances.
    refs = [
        ("hcl", "pka", -6.30, 0.05),
        ("hno3", "pka", -1.40, 0.05),
        ("h2so4", "pka", -3.00, 0.05),
        ("h3po4", "pka", 2.15, 0.05),
        ("ch3cooh", "pka", 4.76, 0.05),
        ("c2h5cooh", "pka", 4.87, 0.05),
        ("hf", "pka", 3.17, 0.05),
        ("h2co3", "pka", 6.35, 0.05),
        ("nh3", "pkb", 4.74, 0.05),
        ("naoh", "pkb", -1.74, 0.05),
    ]

    for substance_id, field_name, expected, tolerance in refs:
        substance = get_substance_by_id(substance_id)
        assert substance is not None, f"Missing substance {substance_id}"
        value = getattr(substance, field_name)
        assert value is not None, f"Missing {field_name} for {substance_id}"
        assert abs(value - expected) <= tolerance, (
            f"{substance_id} {field_name} expected {expected} +/- {tolerance}, got {value}"
        )
