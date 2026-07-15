import pytest

from praf.domain.activities import Activity, ProjectStage
from praf.engine.validation import (
    validate_context,
    validate_inputs,
    InputValidationError,
)


def test_valid_inputs_pass():
    validate_inputs(
        responses={"I001": "yes", "I004": "high", "I008": "no"},
        likelihood={"I001": 3},
        impact={"I001": 5},
        detectability={"I001": 1},
    )  # should not raise


def test_unknown_indicator_id_rejected():
    with pytest.raises(InputValidationError) as exc:
        validate_inputs({"I999": "yes"}, {}, {}, {})
    assert any("unknown indicator id" in e for e in exc.value.errors)


def test_out_of_range_lid_rejected():
    with pytest.raises(InputValidationError) as exc:
        validate_inputs({}, {"I001": 9}, {"I002": 0}, {"I003": "x"})
    assert len(exc.value.errors) == 3


def test_bad_response_for_answer_type_rejected():
    with pytest.raises(InputValidationError) as exc:
        validate_inputs({"I001": "maybe"}, {}, {}, {})  # yes_no expects yes/no
    assert any("answer type yes_no" in e for e in exc.value.errors)


def test_low_med_high_accepts_words_and_numbers():
    validate_inputs({"I004": "high"}, {}, {}, {})
    validate_inputs({"I004": 4}, {}, {}, {})


def test_missing_answers_are_not_errors():
    # No responses at all is valid input; low coverage is handled downstream.
    validate_inputs({}, {}, {}, {})


def test_all_errors_collected_at_once():
    with pytest.raises(InputValidationError) as exc:
        validate_inputs({"I001": "maybe", "IZZZ": "yes"}, {"I002": 99}, {}, {})
    assert len(exc.value.errors) == 3


def test_validate_context_ok():
    act, stg = validate_context("supplier_selection", "pilot")
    assert act == Activity.SUPPLIER_SELECTION
    assert stg == ProjectStage.PILOT


def test_validate_context_rejects_unknown():
    with pytest.raises(InputValidationError) as exc:
        validate_context("nonsense", "nowhere")
    assert len(exc.value.errors) == 2
