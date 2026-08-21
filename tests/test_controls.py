import pytest

from praf.domain import INDICATOR_LIBRARY
from praf.domain.controls import (
    parse_controls,
    Control,
    ControlStatus,
    ControlDefinitionError,
)


def _ids():
    return list(INDICATOR_LIBRARY.keys())


def _entry(**over):
    base = {
        "control_id": "C001",
        "name": "Test control",
        "indicator_ids": ["I001"],
        "status": "verified",
        "likelihood_reduction": 1,
        "detectability_reduction": 0,
    }
    base.update(over)
    return base


def test_parse_valid_control():
    result = parse_controls([_entry()], _ids())
    assert len(result.controls) == 1
    c = result.controls[0]
    assert c.control_id == "C001"
    assert c.status == ControlStatus.VERIFIED
    assert c.applies
    assert result.issues == []


def test_planned_control_does_not_apply():
    result = parse_controls([_entry(status="planned")], _ids())
    assert result.controls[0].applies is False


def test_not_a_list_raises():
    with pytest.raises(ControlDefinitionError):
        parse_controls({"control_id": "C001"}, _ids())


def test_missing_control_id_raises():
    with pytest.raises(ControlDefinitionError):
        parse_controls([_entry(control_id="")], _ids())


def test_duplicate_control_id_raises():
    with pytest.raises(ControlDefinitionError):
        parse_controls([_entry(), _entry()], _ids())


def test_unknown_status_raises():
    with pytest.raises(ControlDefinitionError):
        parse_controls([_entry(status="wishful")], _ids())


def test_out_of_range_reduction_raises():
    with pytest.raises(ControlDefinitionError):
        parse_controls([_entry(likelihood_reduction=9)], _ids())
    with pytest.raises(ControlDefinitionError):
        parse_controls([_entry(detectability_reduction=-1)], _ids())


def test_empty_indicator_ids_raises():
    with pytest.raises(ControlDefinitionError):
        parse_controls([_entry(indicator_ids=[])], _ids())


def test_unknown_indicator_reference_is_reported_not_fatal():
    result = parse_controls([_entry(indicator_ids=["I001", "I999"])], _ids())
    assert result.controls[0].indicator_ids == ("I001",)
    assert any("I999" in issue for issue in result.issues)


def test_zero_effect_control_is_reported():
    result = parse_controls(
        [_entry(likelihood_reduction=0, detectability_reduction=0)], _ids()
    )
    assert any("no reduction" in issue for issue in result.issues)
