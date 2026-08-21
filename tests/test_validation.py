import pytest

from praf.domain import INDICATOR_LIBRARY
from praf.config.validation import (
    validate_inputs,
    validate_thresholds,
    validate_domain_weights,
    ConfigValidationError,
)


def _ids():
    return list(INDICATOR_LIBRARY.keys())


def test_empty_input_is_flagged_incomplete():
    report = validate_inputs(_ids(), {}, {}, {}, {})
    assert report.complete is False
    assert report.completeness_ratio == 0.0
    assert report.indicators_fully_answered == 0
    # Every indicator is missing all four axes.
    assert set(report.missing.keys()) == set(_ids())
    assert report.missing[_ids()[0]] == ["response", "likelihood", "impact", "detectability"]


def test_full_input_is_complete():
    ids = _ids()
    full = {i: 3 for i in ids}
    responses = {i: "no" for i in ids}
    report = validate_inputs(ids, responses, full, full, full)
    assert report.complete is True
    assert report.completeness_ratio == 1.0


def test_unknown_indicator_ids_reported():
    report = validate_inputs(_ids(), {"I999": "no", "ZZZ": "yes"}, {}, {}, {})
    assert "I999" in report.unknown_indicator_ids
    assert "ZZZ" in report.unknown_indicator_ids


def test_out_of_range_reported():
    report = validate_inputs(_ids(), {}, {"I001": 99}, {"I001": -4}, {})
    assert "likelihood" in report.out_of_range.get("I001", [])
    assert "impact" in report.out_of_range.get("I001", [])


def test_validate_thresholds_rejects_inverted():
    with pytest.raises(ConfigValidationError):
        validate_thresholds(70.0, 40.0)
    with pytest.raises(ConfigValidationError):
        validate_thresholds(40.0, 40.0)
    with pytest.raises(ConfigValidationError):
        validate_thresholds(-1.0, 50.0)
    # Valid pair does not raise.
    validate_thresholds(40.0, 70.0)


def test_validate_domain_weights_rejects_negative():
    with pytest.raises(ConfigValidationError):
        validate_domain_weights({"design_maturity": -0.5})
    validate_domain_weights({"design_maturity": 1.25})
