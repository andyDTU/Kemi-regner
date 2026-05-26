from fractions import Fraction
import random

from core.hess_solver import format_reaction_vector, parse_hess_reaction, solve_hess_problem


def _vector_from_reaction(text: str):
    ast = parse_hess_reaction(text)
    vec = {}
    for item in ast["reactants"]:
        key = item["species_key"]
        vec[key] = vec.get(key, Fraction(0, 1)) - Fraction(item["coefficient"])
    for item in ast["products"]:
        key = item["species_key"]
        vec[key] = vec.get(key, Fraction(0, 1)) + Fraction(item["coefficient"])
    return {k: v for k, v in vec.items() if v != 0}


def _assert_exact_target_match(result, target_reaction: str):
    assert result["ok"]
    assert result["validation"]["residual_zero"]
    assert result["validation"]["matches_target_exactly"]

    target_vec = _vector_from_reaction(target_reaction)
    summed_vec = _vector_from_reaction(result["summed_reaction"])
    assert summed_vec == target_vec


def test_hess_solver_ammonia_example():
    target = "N2(g) + 3 H2(g) -> 2 NH3(g)"
    known = "\n".join(
        [
            "N2(g) + O2(g) -> 2 NO(g) ; 180.8",
            "H2(g) + 1/2 O2(g) -> H2O(g) ; -241.8",
            "4 NH3(g) + 5 O2(g) -> 4 NO(g) + 6 H2O(g) ; -904.0",
        ]
    )

    result = solve_hess_problem(target, known)
    _assert_exact_target_match(result, target)

    expected_delta_h = sum(
        factors * dh
        for factors, dh in zip(
            result["factors"],
            [Fraction("180.8"), Fraction("-241.8"), Fraction("-904.0")],
        )
    )
    assert result["delta_h_total"] == expected_delta_h


def test_hess_solver_baco3_decomposition_example():
    target = "BaCO3(s) -> BaO(s) + CO2(g)"
    known = "\n".join(
        [
            "2 Ba(s) + O2(g) -> 2 BaO(s) ; -1107",
            "Ba(s) + CO2(g) + 1/2 O2(g) -> BaCO3(s) ; -823",
        ]
    )

    result = solve_hess_problem(target, known)
    _assert_exact_target_match(result, target)

    expected_delta_h = sum(
        factors * dh
        for factors, dh in zip(
            result["factors"],
            [Fraction("-1107"), Fraction("-823")],
        )
    )
    assert result["delta_h_total"] == expected_delta_h


def test_hess_solver_cus_roast_example():
    target = "CuS(s) + O2(g) -> Cu(s) + SO2(g)"
    known = "\n".join(
        [
            "2 CuS(s) + 3 O2(g) -> 2 CuO(s) + 2 SO2(g) ; -830",
            "2 Cu(s) + O2(g) -> 2 CuO(s) ; -312",
        ]
    )

    result = solve_hess_problem(target, known)
    _assert_exact_target_match(result, target)

    expected_delta_h = sum(
        factors * dh
        for factors, dh in zip(
            result["factors"],
            [Fraction("-830"), Fraction("-312")],
        )
    )
    assert result["delta_h_total"] == expected_delta_h


def test_hess_solver_reports_unsat_case():
    target = "BaCO3(s) -> BaO(s) + CO2(g)"
    known = "H2(g) + 1/2 O2(g) -> H2O(g) ; -241.8"

    result = solve_hess_problem(target, known)
    assert not result["ok"]
    assert "cannot be formed" in result["error"].lower()
    assert "missing_target_species" in result.get("diagnostics", {})


def test_hess_solver_property_random_synthetic_targets():
    rng = random.Random(12345)
    species_pool = [
        "H2(g)",
        "O2(g)",
        "H2O(g)",
        "CO(g)",
        "CO2(g)",
        "N2(g)",
        "NH3(g)",
        "NO(g)",
        "SO2(g)",
        "Cu(s)",
        "CuO(s)",
        "CuS(s)",
    ]

    def random_reaction_vector():
        react_count = rng.randint(1, 3)
        prod_count = rng.randint(1, 3)
        chosen = rng.sample(species_pool, react_count + prod_count)
        reactants = chosen[:react_count]
        products = chosen[react_count:]

        vec = {}
        for sp in reactants:
            vec[sp] = -Fraction(rng.randint(1, 3), 1)
        for sp in products:
            vec[sp] = Fraction(rng.randint(1, 3), 1)
        return vec

    for _ in range(25):
        known_vectors = [random_reaction_vector() for _ in range(5)]
        known_dh = [Fraction(rng.randint(-500, 500), 1) for _ in range(5)]
        factors = [Fraction(rng.randint(-2, 2), rng.choice([1, 1, 2])) for _ in range(5)]
        if all(f == 0 for f in factors):
            factors[0] = Fraction(1, 1)

        target_vec = {}
        for f, vec in zip(factors, known_vectors):
            if f == 0:
                continue
            for sp, c in vec.items():
                target_vec[sp] = target_vec.get(sp, Fraction(0, 1)) + f * c
        target_vec = {k: v for k, v in target_vec.items() if v != 0}
        if not target_vec:
            continue

        target_rxn = format_reaction_vector(target_vec)
        known_lines = "\n".join(
            [
                f"{format_reaction_vector(vec)} ; {float(dh)}"
                for vec, dh in zip(known_vectors, known_dh)
            ]
        )

        result = solve_hess_problem(target_rxn, known_lines)
        assert result["ok"]
        assert result["validation"]["residual_zero"]
        assert result["validation"]["matches_target_exactly"]

        expected_delta_h = sum(f * d for f, d in zip(result["factors"], known_dh))
        assert result["delta_h_total"] == expected_delta_h


def test_hess_solver_parser_supports_unicode_arrow_and_half_symbol():
    target = "H2(g) + ½ O2(g) → H2O(g)"
    known = "H2(g) + 1/2 O2(g) -> H2O(g) ; -241.8"

    result = solve_hess_problem(target, known)
    assert result["ok"]
    assert result["validation"]["residual_zero"]
    assert result["validation"]["matches_target_exactly"]
    assert result["delta_h_total"] == Fraction("-241.8")
