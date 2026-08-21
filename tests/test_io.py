import json

import pytest

from praf.io.loaders import load_json_inputs, InputLoadError
from praf.io.exporters import export_json_report


def test_missing_file_raises_input_load_error(tmp_path):
    with pytest.raises(InputLoadError):
        load_json_inputs(str(tmp_path / "does_not_exist.json"))


def test_malformed_json_raises_input_load_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json ", encoding="utf-8")
    with pytest.raises(InputLoadError):
        load_json_inputs(str(bad))


def test_non_object_top_level_raises(tmp_path):
    arr = tmp_path / "arr.json"
    arr.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(InputLoadError):
        load_json_inputs(str(arr))


def test_wrong_section_type_raises(tmp_path):
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps({"responses": [1, 2, 3]}), encoding="utf-8")
    with pytest.raises(InputLoadError):
        load_json_inputs(str(p))


def test_valid_file_loads_context(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text(
        json.dumps(
            {
                "context": {"activity": "supplier_selection", "stage": "design"},
                "responses": {"I001": "no"},
                "likelihood": {"I001": 4},
            }
        ),
        encoding="utf-8",
    )
    loaded = load_json_inputs(str(p))
    assert loaded.context["activity"] == "supplier_selection"
    assert loaded.responses == {"I001": "no"}
    assert loaded.likelihood == {"I001": 4}
    assert loaded.impact == {}


def test_export_is_atomic_and_creates_dirs(tmp_path):
    out = tmp_path / "nested" / "report.json"
    export_json_report(str(out), {"a": 1, "b": [1, 2]})
    assert out.exists()
    # No leftover temp files in the directory.
    assert [p.name for p in out.parent.iterdir()] == ["report.json"]
    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 1, "b": [1, 2]}
