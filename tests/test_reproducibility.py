"""Golden regression: the tracked example output must match a fresh run.

The generator pins the report timestamp, so the pipeline is fully deterministic
over the example inputs. If a scoring change alters the numbers, this test fails
and forces the example output (and MODEL_VERSION) to be regenerated knowingly —
scoring drift can never slip in silently.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PINNED = "2026-01-01T00:00:00+00:00"


def _fresh_report() -> dict:
    # Make the subprocess work from a fresh clone too: the parent test run gets
    # src/ via pytest's pythonpath option, but a child interpreter does not.
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "praf.cli.main",
            str(REPO / "data" / "examples" / "example_inputs.json"),
            "--generated-at",
            PINNED,
        ],
        cwd=str(REPO),
        env=env,
        stderr=subprocess.DEVNULL,
    )
    return json.loads(out)


def test_pinned_run_is_deterministic():
    assert _fresh_report() == _fresh_report()


def test_example_output_matches_fresh_run():
    golden_path = REPO / "data" / "examples" / "example_outputs.json"
    assert golden_path.exists(), (
        "example_outputs.json is missing — run scripts/generate_example_outputs.py"
    )
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert _fresh_report() == golden, (
        "Scoring output drifted from the tracked example. If the change is "
        "intentional, bump MODEL_VERSION and regenerate via "
        "scripts/generate_example_outputs.py."
    )
