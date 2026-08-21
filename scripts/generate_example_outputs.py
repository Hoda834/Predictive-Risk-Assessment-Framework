"""Regenerate data/examples/example_outputs.json reproducibly.

The report timestamp is pinned with --generated-at so that two runs over the
same inputs produce byte-identical output. This lets the example output be
tracked in git and used as a golden regression reference (see
tests/test_reproducibility.py).
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

# Fixed timestamp: the example output must not change between runs.
PINNED_TIMESTAMP = "2026-01-01T00:00:00+00:00"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "data" / "examples" / "example_inputs.json"
    cmd = [
        sys.executable,
        "-m",
        "praf.cli.main",
        str(input_path),
        "--generated-at",
        PINNED_TIMESTAMP,
    ]
    out = subprocess.check_output(cmd, cwd=str(repo_root))
    output_path = repo_root / "data" / "examples" / "example_outputs.json"
    output_path.write_bytes(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
