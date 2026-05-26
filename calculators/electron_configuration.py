"""
Electron configuration calculator wrapper.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.electron_configuration import (
    build_orbital_distribution,
    electron_configuration,
    parse_element_charge_input,
)
from core.radius import resolve_radius


def calculate_electron_configuration_with_steps(
    raw_input: str,
    max_abs_charge: int = 8,
    orbital_view: str = "all",
) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Parse user input and compute electron configuration with explanatory steps.
    """
    parsed = parse_element_charge_input(raw_input, max_abs_charge=max_abs_charge)
    result = electron_configuration(parsed.Z, charge=parsed.charge, max_abs_charge=max_abs_charge)
    radius = resolve_radius(parsed.Z, parsed.charge, unit="pm")
    result["radius"] = radius
    orbital_distribution = build_orbital_distribution(result.get("orbitals", []), view=orbital_view)
    result["orbital_distribution"] = orbital_distribution

    steps: List[str] = []
    steps.append("**Step 1: Parse input**")
    steps.append(f"Input: {raw_input}")
    steps.append(f"Parsed as: symbol={parsed.symbol}, Z={parsed.Z}, charge={parsed.charge:+d}")

    steps.append("\n**Step 2: Determine electron count**")
    steps.append(f"Electrons = Z - charge = {parsed.Z} - ({parsed.charge:+d}) = {result['electrons']}")

    steps.append("\n**Step 3: Build electron configuration**")
    steps.append(f"Aufbau / fyldningsrækkefølge: {result['aufbau']}")
    steps.append("Skal-sorteret elektronkonfiguration:")
    for line in str(result["shell_sorted_grouped"]).splitlines():
        steps.append(line)
    steps.append(f"Long notation: {result['long']}")
    steps.append(f"Noble-gas notation: {result['noble']}")

    steps.append("\n**Step 4: Resolve radius from local data**")
    if radius["value"] is None:
        steps.append(f"Radius: ukendt ({radius.get('note', 'ingen data')})")
    else:
        radius_type = "atomradius (neutral)" if parsed.charge == 0 else ("ionradius (kation)" if parsed.charge > 0 else "ionradius (anion)")
        steps.append(f"Radius: {radius['value']:.3g} {radius['unit']} ({radius_type})")

    steps.append(f"Elektroner i yderste skal: {result['outer_shell_electrons']}")

    steps.append("\n**Step 5: Orbitalfordeling (Hund + Pauli)**")
    if not orbital_distribution:
        steps.append("Orbitalfordeling: ingen under-skaller valgt i aktiv visning.")
    else:
        for row in orbital_distribution:
            steps.append(row["text"])

    steps.append("\n**Step 6: Kvantetal (n, l, m) for viste orbitaler**")
    if not orbital_distribution:
        steps.append("Kvantetal: ingen orbitaler i aktiv visning.")
    else:
        for row in orbital_distribution:
            m_values_text = ", ".join(str(value) for value in row.get("m_values", []))
            steps.append(
                f"{row['subshell_label']}: n={row.get('n')}, l={row.get('l')}, m=({m_values_text})"
            )

    metadata = {
        "symbol": parsed.symbol,
        "Z": parsed.Z,
        "charge": parsed.charge,
        "electrons": result["electrons"],
        "radius": radius,
        "orbital_distribution": orbital_distribution,
        "aufbau": result["aufbau"],
        "shell_sorted": result["shell_sorted"],
        "shell_sorted_grouped": result["shell_sorted_grouped"],
        "outer_shell_electrons": result["outer_shell_electrons"],
    }
    return result, steps, metadata
