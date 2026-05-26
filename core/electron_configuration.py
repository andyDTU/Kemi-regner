"""
Electron configuration parsing and computation utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Literal, Tuple

import periodictable


_L_BY_SUBSHELL: Dict[str, int] = {"s": 0, "p": 1, "d": 2, "f": 3}
_CAPACITY_BY_SUBSHELL: Dict[str, int] = {"s": 2, "p": 6, "d": 10, "f": 14}

_AUFBAU_SEQUENCE: List[Tuple[int, str]] = [
    (1, "s"),
    (2, "s"),
    (2, "p"),
    (3, "s"),
    (3, "p"),
    (4, "s"),
    (3, "d"),
    (4, "p"),
    (5, "s"),
    (4, "d"),
    (5, "p"),
    (6, "s"),
    (4, "f"),
    (5, "d"),
    (6, "p"),
    (7, "s"),
    (5, "f"),
    (6, "d"),
    (7, "p"),
]

_NOBLE_GASES: List[Tuple[int, str]] = [
    (2, "He"),
    (10, "Ne"),
    (18, "Ar"),
    (36, "Kr"),
    (54, "Xe"),
    (86, "Rn"),
    (118, "Og"),
]

_AR_PREFIX = "1s2 2s2 2p6 3s2 3p6"
_KR_PREFIX = f"{_AR_PREFIX} 4s2 3d10 4p6"
_XE_PREFIX = f"{_KR_PREFIX} 5s2 4d10 5p6"

_NEUTRAL_EXCEPTION_LONG: Dict[int, str] = {
    # 3d series
    24: f"{_AR_PREFIX} 4s1 3d5",   # Cr
    29: f"{_AR_PREFIX} 4s1 3d10",  # Cu
    # 4d series
    41: f"{_KR_PREFIX} 5s1 4d4",   # Nb
    42: f"{_KR_PREFIX} 5s1 4d5",   # Mo
    44: f"{_KR_PREFIX} 5s1 4d7",   # Ru
    45: f"{_KR_PREFIX} 5s1 4d8",   # Rh
    46: f"{_KR_PREFIX} 4d10",      # Pd (5s0)
    47: f"{_KR_PREFIX} 5s1 4d10",  # Ag
    # Lanthanide/5d edge cases used in teaching contexts
    57: f"{_XE_PREFIX} 6s2 5d1",        # La
    58: f"{_XE_PREFIX} 6s2 4f1 5d1",    # Ce
    # 5d series
    78: f"{_XE_PREFIX} 6s1 4f14 5d9",   # Pt
    79: f"{_XE_PREFIX} 6s1 4f14 5d10",  # Au
}

_ORBITAL_LABELS: Dict[str, List[str]] = {
    "s": ["s"],
    "p": ["px", "py", "pz"],
    "d": ["dxy", "dyz", "dxz", "dx2−y2", "dz2"],
    "f": ["f1", "f2", "f3", "f4", "f5", "f6", "f7"],
}

_M_VALUES_BY_SUBSHELL: Dict[str, List[int]] = {
    "s": [0],
    "p": [-1, 0, 1],
    "d": [-2, -1, 0, 1, 2],
    "f": [-3, -2, -1, 0, 1, 2, 3],
}


@dataclass(frozen=True)
class ParsedElectronInput:
    Z: int
    symbol: str
    charge: int


@dataclass
class OrbitalState:
    n: int
    subshell: str
    electrons: int = 0

    @property
    def l(self) -> int:
        return _L_BY_SUBSHELL[self.subshell]

    @property
    def capacity(self) -> int:
        return _CAPACITY_BY_SUBSHELL[self.subshell]

    @property
    def label(self) -> str:
        return f"{self.n}{self.subshell}"


def parse_element_charge_input(text: str, max_abs_charge: int = 8) -> ParsedElectronInput:
    """
    Parse element input with optional ionic charge.

    Supported inputs include examples like: Na, O2-, O^2-, Fe3+, 26 2+, Cl-, Br1-, Cu+.
    """
    if not text or not text.strip():
        raise ValueError("Tomt input. Angiv et grundstofsymbol eller atomnummer.")

    tokens = text.strip().split()
    if len(tokens) > 2:
        raise ValueError("Ugyldigt inputformat. Brug fx 'Fe3+' eller '26 2+'.")

    base_token = tokens[0]
    charge_token = ""

    if len(tokens) == 2:
        charge_token = tokens[1]
        if not re.fullmatch(r"[A-Za-z]{1,3}|\d{1,3}", base_token):
            raise ValueError("Ugyldigt format for grundstof. Brug symbol eller atomnummer først.")
    else:
        m = re.fullmatch(r"([A-Za-z]{1,3}|\d{1,3})(.*)", base_token)
        if not m:
            raise ValueError("Ugyldigt grundstofinput. Brug symbol (fx Fe) eller atomnummer (fx 26).")
        base_token = m.group(1)
        charge_token = m.group(2)

    charge = _parse_charge_token(charge_token)
    if abs(charge) > max_abs_charge:
        raise ValueError(f"Ladning uden for tilladt interval: {charge}. Maks |ladning| er {max_abs_charge}.")

    z_value, symbol = _resolve_element(base_token)
    return ParsedElectronInput(Z=z_value, symbol=symbol, charge=charge)


def electron_configuration(Z: int, charge: int = 0, max_abs_charge: int = 8) -> Dict[str, object]:
    """
    Compute long and noble-gas electron configuration for element Z and ionic charge.
    """
    if not isinstance(Z, int) or Z < 1 or Z > 118:
        raise ValueError("Atomnummer Z skal være et heltal i intervallet 1..118.")
    if not isinstance(charge, int):
        raise ValueError("Ladning skal være et heltal.")
    if abs(charge) > max_abs_charge:
        raise ValueError(f"Ladning uden for tilladt interval. Maks |ladning| er {max_abs_charge}.")

    electrons = Z - charge
    if electrons < 0:
        raise ValueError(f"Ugyldig ladning: Z={Z} og ladning={charge} giver negativt antal elektroner.")
    max_supported_electrons = sum(_CAPACITY_BY_SUBSHELL[subshell] for _, subshell in _AUFBAU_SEQUENCE)
    if electrons > max_supported_electrons:
        raise ValueError(
            f"Elektrontal {electrons} er større end understøttet maksimum {max_supported_electrons} i orbitalrækkefølgen."
        )

    orbitals = _neutral_orbitals(Z)

    if charge < 0:
        _add_electrons(orbitals, -charge)
    elif charge > 0:
        _remove_electrons(orbitals, charge)

    long_text = _render_long_configuration(orbitals)
    noble_text = _render_noble_configuration(orbitals)
    parsed_long = parse_electron_configuration(long_text)
    shell_sorted_items = sort_by_shell_order(parsed_long)
    shell_sorted_flat = render_shell_sorted(shell_sorted_items, grouped=False)
    shell_sorted_grouped = render_shell_sorted(shell_sorted_items, grouped=True)
    occupied_orbitals = [
        {
            "label": orb.label,
            "n": orb.n,
            "subshell": orb.subshell,
            "l": orb.l,
            "m_values": _M_VALUES_BY_SUBSHELL[orb.subshell],
            "electrons": orb.electrons,
            "capacity": orb.capacity,
        }
        for orb in orbitals
        if orb.electrons > 0
    ]

    total_unpaired = count_total_unpaired_electrons(occupied_orbitals)
    d_electrons = count_d_electrons(occupied_orbitals)
    d_unpaired = count_d_unpaired_electrons(occupied_orbitals)
    outer_shell_electrons = count_outer_shell_electrons(occupied_orbitals)

    return {
        "long": long_text,
        "aufbau": long_text,
        "noble": noble_text,
        "shell_sorted": shell_sorted_flat,
        "shell_sorted_grouped": shell_sorted_grouped,
        "electrons": electrons,
        "orbitals": occupied_orbitals,
        "outer_shell_electrons": outer_shell_electrons,
        "total_unpaired_electrons": total_unpaired,
        "d_electrons": d_electrons,
        "d_unpaired_electrons": d_unpaired,
    }


def ground_state_configuration_structured(Z: int) -> List[Dict[str, object]]:
    """
    Return neutral ground-state configuration for element Z as structured data.
    """
    if not isinstance(Z, int) or Z < 1 or Z > 118:
        raise ValueError("Atomnummer Z skal være et heltal i intervallet 1..118.")

    orbitals = _neutral_orbitals(Z)
    return [
        {
            "shell": orb.n,
            "subshell": orb.subshell,
            "electrons": orb.electrons,
            "capacity": orb.capacity,
            "label": orb.label,
        }
        for orb in orbitals
        if orb.electrons > 0
    ]


def format_configuration_long(orbitals: List[Dict[str, object]]) -> str:
    """Render structured configuration to long/Aufbau notation."""
    parts = [
        f"{int(orb['shell'])}{str(orb['subshell'])}{int(orb['electrons'])}"
        for orb in orbitals
        if int(orb.get("electrons", 0)) > 0
    ]
    return " ".join(parts)


def format_configuration_noble(orbitals: List[Dict[str, object]]) -> str:
    """
    Render structured configuration to noble-gas notation.
    """
    states = _orbitals_from_structured(orbitals)
    return _render_noble_configuration(states)


def parse_electron_configuration(config: str) -> List[Dict[str, object]]:
    """
    Parse electron configuration text to structured items.

    Example token: 3p6 -> {n: 3, subshell: 'p', electrons: 6}
    """
    items: List[Dict[str, object]] = []
    tokens = [token.strip() for token in config.split() if token.strip()]
    for token in tokens:
        match = re.fullmatch(r"(\d)([spdf])(\d+)", token)
        if not match:
            raise ValueError(f"Ugyldigt orbitaltoken i konfiguration: '{token}'.")
        n_value = int(match.group(1))
        subshell = match.group(2)
        electrons = int(match.group(3))
        items.append(
            {
                "n": n_value,
                "subshell": subshell,
                "electrons": electrons,
                "label": f"{n_value}{subshell}",
            }
        )
    return items


def sort_by_shell_order(items: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Sort configuration items by shell (n), then orbital type order s<p<d<f."""
    return sorted(items, key=lambda item: (int(item["n"]), _L_BY_SUBSHELL[str(item["subshell"])]))


def render_shell_sorted(items: List[Dict[str, object]], grouped: bool = True) -> str:
    """
    Render shell-sorted configuration either grouped by n (multi-line) or as flat text.
    """
    if not grouped:
        return " ".join(f"{item['label']}{int(item['electrons'])}" for item in items)

    lines: List[str] = []
    grouped_map: Dict[int, List[Dict[str, object]]] = {}
    for item in items:
        n_value = int(item["n"])
        grouped_map.setdefault(n_value, []).append(item)

    for n_value in sorted(grouped_map.keys()):
        parts = [f"{entry['label']}{int(entry['electrons'])}" for entry in grouped_map[n_value]]
        lines.append(" ".join(parts))

    return "\n".join(lines)


def parseElectronConfiguration(config: str) -> List[Dict[str, object]]:
    """CamelCase alias for parse_electron_configuration."""
    return parse_electron_configuration(config)


def sortByShellOrder(items: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """CamelCase alias for sort_by_shell_order."""
    return sort_by_shell_order(items)


def renderShellSorted(items: List[Dict[str, object]], grouped: bool = True) -> str:
    """CamelCase alias for render_shell_sorted."""
    return render_shell_sorted(items, grouped=grouped)


def distribute_subshell(subshell: Literal["s", "p", "d", "f"], electrons: int) -> List[str]:
    """
    Distribute electrons in a subshell according to Hund + Pauli.

    Returns orbital box occupancies such as ["↑", "↑", "↑↓"].
    """
    if subshell not in _ORBITAL_LABELS:
        raise ValueError(f"Ugyldig under-skal: {subshell}")
    if electrons < 0:
        raise ValueError("Elektrontal i under-skal kan ikke være negativt.")

    orbital_count = len(_ORBITAL_LABELS[subshell])
    capacity = 2 * orbital_count
    if electrons > capacity:
        raise ValueError(
            f"Elektrontal {electrons} overstiger kapacitet {capacity} for {subshell}-under-skal."
        )

    boxes = ["" for _ in range(orbital_count)]
    remaining = electrons

    for idx in range(orbital_count):
        if remaining == 0:
            break
        boxes[idx] = "↑"
        remaining -= 1

    for idx in range(orbital_count):
        if remaining == 0:
            break
        if boxes[idx] == "↑":
            boxes[idx] = "↑↓"
            remaining -= 1

    if remaining != 0:
        raise ValueError("Intern fejl: ikke alle elektroner blev fordelt i under-skal.")

    return boxes


def subshell_orbital_occupancy(subshell: Literal["s", "p", "d", "f"], electrons: int) -> List[int]:
    """
    Return occupancy counts per orbital box for a subshell (e.g. p4 -> [2,1,1]).
    """
    boxes = distribute_subshell(subshell, electrons)
    return [len(box) for box in boxes]


def count_total_unpaired_electrons(orbitals: List[Dict[str, object]]) -> int:
    """Count total unpaired electrons across all occupied subshells."""
    total = 0
    for orb in orbitals:
        subshell = str(orb["subshell"])
        electrons = int(orb["electrons"])
        boxes = distribute_subshell(subshell, electrons)
        total += sum(1 for box in boxes if box == "↑")
    return total


def count_d_electrons(orbitals: List[Dict[str, object]]) -> int:
    """Count electrons in the valence d subshell (highest occupied n among d subshells)."""
    d_orbitals = [orb for orb in orbitals if str(orb["subshell"]) == "d" and int(orb["electrons"]) > 0]
    if not d_orbitals:
        return 0
    max_d_shell = max(_orbital_shell_number(orb) for orb in d_orbitals)
    return sum(int(orb["electrons"]) for orb in d_orbitals if _orbital_shell_number(orb) == max_d_shell)


def count_d_unpaired_electrons(orbitals: List[Dict[str, object]]) -> int:
    """Count unpaired electrons in the valence d subshell (highest occupied n among d subshells)."""
    d_orbitals = [orb for orb in orbitals if str(orb["subshell"]) == "d" and int(orb["electrons"]) > 0]
    if not d_orbitals:
        return 0
    max_d_shell = max(_orbital_shell_number(orb) for orb in d_orbitals)

    total = 0
    for orb in d_orbitals:
        if _orbital_shell_number(orb) != max_d_shell:
            continue
        electrons = int(orb["electrons"])
        boxes = distribute_subshell("d", electrons)
        total += sum(1 for box in boxes if box == "↑")
    return total


def build_orbital_distribution(
    orbitals: List[Dict[str, object]],
    view: Literal["all", "valence", "partial"] = "valence",
) -> List[Dict[str, object]]:
    """
    Build orbital distribution rows from occupied subshell list.
    """
    if view not in {"all", "valence", "partial"}:
        raise ValueError("view skal være 'all', 'valence' eller 'partial'.")

    if not orbitals:
        return []

    selected_orbitals = select_subshells_for_orbital_diagram(
        orbitals,
        show_all=(view == "all"),
        view=view,
    )
    rows: List[Dict[str, object]] = []

    for orb in selected_orbitals:
        subshell = str(orb["subshell"])
        electrons = int(orb["electrons"])
        n_value = int(orb["n"])
        l_value = _L_BY_SUBSHELL[subshell]
        m_values = _M_VALUES_BY_SUBSHELL[subshell]

        boxes = distribute_subshell(subshell, electrons)
        names = _ORBITAL_LABELS[subshell]
        parts = [f"{name} [{box}]" if box else f"{name} [ ]" for name, box in zip(names, boxes)]
        rows.append(
            {
                "subshell_label": str(orb["label"]),
                "n": n_value,
                "l": l_value,
                "m_values": m_values,
                "orbitals": [
                    {
                        "name": name,
                        "occupancy": box,
                        "n": n_value,
                        "l": l_value,
                        "m": m_value,
                    }
                    for name, box, m_value in zip(names, boxes, m_values)
                ],
                "text": f"{orb['label']}: " + "  ".join(parts),
            }
        )

    return rows


def select_subshells_for_orbital_diagram(
    subshells: List[Dict[str, object]],
    show_all: bool,
    view: Literal["all", "valence", "partial"] = "valence",
) -> List[Dict[str, object]]:
    """
    Select subshells used for orbital diagram rendering.

    - show_all=True: include all subshells with electrons > 0.
    - show_all=False: preserve existing behavior for the selected view.
    """
    if not subshells:
        return []

    occupied = [orb for orb in subshells if int(orb.get("electrons", 0)) > 0]
    if show_all:
        return occupied

    if view == "partial":
        return [
            orb
            for orb in occupied
            if 0 < int(orb["electrons"]) < int(orb["capacity"])
        ]

    max_n = max(int(orb["n"]) for orb in occupied)
    return [
        orb
        for orb in occupied
        if (int(orb["n"]) == max_n) or (0 < int(orb["electrons"]) < int(orb["capacity"]))
    ]


def selectSubshellsForOrbitalDiagram(
    subshells: List[Dict[str, object]],
    showAll: bool,
) -> List[Dict[str, object]]:
    """CamelCase alias for select_subshells_for_orbital_diagram with default non-all view behavior."""
    return select_subshells_for_orbital_diagram(
        subshells,
        show_all=showAll,
        view="valence",
    )


def _resolve_element(base_token: str) -> Tuple[int, str]:
    if base_token.isdigit():
        z_value = int(base_token)
        if z_value < 1 or z_value > 118:
            raise ValueError(f"Atomnummer uden for interval 1..118: {z_value}.")
        element = periodictable.elements[z_value]
        return z_value, element.symbol

    symbol = base_token[0].upper() + base_token[1:].lower()
    try:
        element = getattr(periodictable, symbol)
    except AttributeError as exc:
        raise ValueError(f"Ukendt grundstofsymbol: {base_token}.") from exc

    z_value = int(element.number)
    if z_value < 1 or z_value > 118:
        raise ValueError(f"Atomnummer uden for interval 1..118: {z_value}.")
    return z_value, symbol


def _parse_charge_token(charge_token: str) -> int:
    token = charge_token.strip()
    if token == "":
        return 0

    token = token.replace("^", "")
    if token == "0":
        return 0

    m = re.fullmatch(r"([+-])(\d*)", token)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        magnitude = int(m.group(2)) if m.group(2) else 1
        return sign * magnitude

    m = re.fullmatch(r"(\d+)([+-])", token)
    if m:
        magnitude = int(m.group(1))
        sign = 1 if m.group(2) == "+" else -1
        return sign * magnitude

    m = re.fullmatch(r"([+-])(\d+)", token)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        magnitude = int(m.group(2))
        return sign * magnitude

    raise ValueError(f"Ugyldigt ladningsformat: '{charge_token}'.")


def _neutral_orbitals(Z: int) -> List[OrbitalState]:
    if Z in _NEUTRAL_EXCEPTION_LONG:
        orbitals = _orbitals_from_configuration_string(_NEUTRAL_EXCEPTION_LONG[Z])
        _validate_total_electrons(orbitals, expected_electrons=Z)
        return orbitals
    return _fill_electrons(Z)


def _fill_electrons(electron_count: int) -> List[OrbitalState]:
    orbitals = _empty_orbitals()
    remaining = electron_count

    for orbital in orbitals:
        if remaining <= 0:
            break
        add_here = min(orbital.capacity, remaining)
        orbital.electrons = add_here
        remaining -= add_here

    return orbitals


def _add_electrons(orbitals: List[OrbitalState], add_count: int) -> None:
    remaining = add_count
    for orbital in orbitals:
        if remaining <= 0:
            return
        space = orbital.capacity - orbital.electrons
        if space <= 0:
            continue
        add_here = min(space, remaining)
        orbital.electrons += add_here
        remaining -= add_here

    if remaining > 0:
        raise ValueError("Kan ikke tilføje flere elektroner i den understøttede orbitalrække.")


def _remove_electrons(orbitals: List[OrbitalState], remove_count: int) -> None:
    remaining = remove_count

    while remaining > 0:
        occupied = [orb for orb in orbitals if orb.electrons > 0]
        if not occupied:
            raise ValueError("Kan ikke fjerne flere elektroner end der er til stede.")

        target = max(occupied, key=lambda orb: (orb.n, orb.l))
        target.electrons -= 1
        remaining -= 1


def _empty_orbitals() -> List[OrbitalState]:
    return [OrbitalState(n=n, subshell=subshell, electrons=0) for n, subshell in _AUFBAU_SEQUENCE]


def _orbitals_from_configuration_string(config: str) -> List[OrbitalState]:
    orbitals = _empty_orbitals()
    by_label = {orb.label: orb for orb in orbitals}

    tokens = [token.strip() for token in config.split() if token.strip()]
    for token in tokens:
        m = re.fullmatch(r"(\d)([spdf])(\d+)", token)
        if not m:
            raise ValueError(f"Ugyldigt orbitaltoken i undtagelsestabel: '{token}'.")
        label = f"{m.group(1)}{m.group(2)}"
        electrons = int(m.group(3))
        if label not in by_label:
            raise ValueError(f"Orbital '{label}' er ikke understøttet i orbitalrækkefølgen.")
        target = by_label[label]
        if electrons < 0 or electrons > target.capacity:
            raise ValueError(f"Ugyldig elektronoccupancy i undtagelsestabel: {token}.")
        target.electrons = electrons

    return orbitals


def _render_long_configuration(orbitals: List[OrbitalState]) -> str:
    parts = [f"{orb.label}{orb.electrons}" for orb in orbitals if orb.electrons > 0]
    return " ".join(parts) if parts else ""


def _render_noble_configuration(orbitals: List[OrbitalState]) -> str:
    best_noble = None
    best_prefix = None

    for noble_electrons, noble_symbol in _NOBLE_GASES:
        prefix_orbitals = _fill_electrons(noble_electrons)
        if _matches_prefix(orbitals, prefix_orbitals):
            best_noble = (noble_electrons, noble_symbol)
            best_prefix = prefix_orbitals

    if not best_noble or not best_prefix:
        return _render_long_configuration(orbitals)

    _, noble_symbol = best_noble
    prefix_labels = {orb.label for orb in best_prefix if orb.electrons > 0}
    suffix_items = [
        orb
        for orb in orbitals
        if orb.electrons > 0 and orb.label not in prefix_labels
    ]
    suffix_items = sorted(suffix_items, key=lambda orb: (orb.n, orb.l))
    suffix_parts = [f"{orb.label}{orb.electrons}" for orb in suffix_items]

    if not suffix_parts:
        return f"[{noble_symbol}]"
    return f"[{noble_symbol}] " + " ".join(suffix_parts)


def _matches_prefix(current: List[OrbitalState], prefix: List[OrbitalState]) -> bool:
    for orb_current, orb_prefix in zip(current, prefix):
        if orb_prefix.electrons > 0 and orb_current.electrons != orb_prefix.electrons:
            return False
    return True


def _orbitals_from_structured(orbitals: List[Dict[str, object]]) -> List[OrbitalState]:
    states = _empty_orbitals()
    by_label = {state.label: state for state in states}

    for orb in orbitals:
        shell = int(orb["shell"])
        subshell = str(orb["subshell"])
        electrons = int(orb["electrons"])
        label = f"{shell}{subshell}"
        if label not in by_label:
            raise ValueError(f"Orbital '{label}' er ikke understøttet i orbitalrækkefølgen.")
        target = by_label[label]
        if electrons < 0 or electrons > target.capacity:
            raise ValueError(f"Ugyldig electron-occupancy for orbital '{label}': {electrons}.")
        target.electrons = electrons

    return states


def _orbital_shell_number(orbital: Dict[str, object]) -> int:
    if "n" in orbital:
        return int(orbital["n"])
    if "shell" in orbital:
        return int(orbital["shell"])
    raise ValueError("Orbital dictionary mangler både 'n' og 'shell'.")


def count_outer_shell_electrons(orbitals: List[Dict[str, object]]) -> int:
    """Count electrons in the outermost occupied shell (highest principal quantum number)."""
    occupied_shells = [_orbital_shell_number(orbital) for orbital in orbitals if int(orbital.get("electrons", 0)) > 0]
    if not occupied_shells:
        return 0

    outer_shell = max(occupied_shells)
    return sum(
        int(orbital.get("electrons", 0))
        for orbital in orbitals
        if _orbital_shell_number(orbital) == outer_shell
    )


def _validate_total_electrons(orbitals: List[OrbitalState], expected_electrons: int) -> None:
    total = sum(orb.electrons for orb in orbitals)
    if total != expected_electrons:
        raise ValueError(
            f"Undtagelseskonfiguration har forkert elektrontal: forventet {expected_electrons}, fik {total}."
        )
