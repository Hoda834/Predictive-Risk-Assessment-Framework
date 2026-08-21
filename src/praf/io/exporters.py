from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict


def export_json_report(path: str, report: Dict[str, Any]) -> None:
    """Write a report to ``path`` as JSON.

    Creates the parent directory if needed and writes atomically (to a temp file
    in the same directory, then ``os.replace``) so a partial/corrupt report is
    never left behind if the process is interrupted mid-write.
    """
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        # Clean up the temp file on any failure rather than leaking it.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
