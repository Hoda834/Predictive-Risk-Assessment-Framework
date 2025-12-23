from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "data" / "examples" / "example_inputs.json"
    cmd = [sys.executable, "-m", "praf.cli.main", str(input_path)]
    out = subprocess.check_output(cmd, cwd=str(repo_root))
    output_path = repo_root / "data" / "examples" / "example_outputs.json"
    output_path.write_bytes(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
