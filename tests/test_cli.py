import json

from praf.cli.main import main


def test_no_argument_returns_usage_error(capsys):
    rc = main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "Usage" in err


def test_help_flag_returns_zero(capsys):
    rc = main(["--help"])
    assert rc == 0
    assert "Usage" in capsys.readouterr().out


def test_missing_file_returns_error(capsys):
    rc = main(["/no/such/file.json"])
    assert rc == 1
    assert "error:" in capsys.readouterr().err


def test_invalid_activity_returns_error(tmp_path, capsys):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"context": {"activity": "flying"}}), encoding="utf-8")
    rc = main([str(p)])
    assert rc == 1
    assert "Unknown activity" in capsys.readouterr().err


def test_incomplete_input_warns_but_succeeds(tmp_path, capsys):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"responses": {"I001": "no"}}), encoding="utf-8")
    rc = main([str(p)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "incomplete" in captured.err
    report = json.loads(captured.out)
    assert report["input_completeness"]["complete"] is False


def test_writes_output_file(tmp_path):
    src = tmp_path / "in.json"
    src.write_text(
        json.dumps({"responses": {"I001": "no"}, "likelihood": {"I001": 5}}),
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    rc = main([str(src), str(out)])
    assert rc == 0
    assert out.exists()
    written = json.loads(out.read_text(encoding="utf-8"))
    assert "overall_decision" in written
