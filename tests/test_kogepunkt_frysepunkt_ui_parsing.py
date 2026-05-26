import pytest

from calculators.kogepunkt_frysepunkt import _parse_required_float


def test_parse_required_float_rejects_empty_value():
    with pytest.raises(ValueError, match="mangler"):
        _parse_required_float("", "Felt")


def test_parse_required_float_rejects_whitespace_value():
    with pytest.raises(ValueError, match="mangler"):
        _parse_required_float("   ", "Felt")


def test_parse_required_float_rejects_non_numeric_value():
    with pytest.raises(ValueError, match="gyldigt tal"):
        _parse_required_float("abc", "Felt")


def test_parse_required_float_accepts_comma_decimal():
    value = _parse_required_float("1,25", "Felt")
    assert value == pytest.approx(1.25)
