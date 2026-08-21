from __future__ import annotations

import json
import sys
from typing import List, Optional

from praf.domain import Context, Activity, ProjectStage, INDICATOR_LIBRARY
from praf.domain.controls import parse_controls, ControlDefinitionError
from praf.engine.pipeline import run_assessment
from praf.io.loaders import load_json_inputs, InputLoadError
from praf.io.exporters import export_json_report
from praf.config.defaults import Defaults

_USAGE = (
    "Usage: python -m praf.cli.main <input.json> [output.json] [--generated-at TIMESTAMP]\n"
    "\n"
    "Scores an indicator questionnaire and prints a JSON risk report to stdout.\n"
    "If <output.json> is given, the report is also written there.\n"
    "--generated-at pins the report timestamp (ISO 8601) for reproducible output.\n"
    "See data/examples/example_inputs.json for the expected input shape."
)


def _resolve_context(raw_context: dict) -> Context:
    """Build a Context from raw input, with clear errors for bad values."""
    activity_value = str(raw_context.get("activity", "product_design"))
    stage_value = str(raw_context.get("stage", "design"))
    try:
        activity = Activity(activity_value)
    except ValueError:
        valid = ", ".join(a.value for a in Activity)
        raise InputLoadError(f"Unknown activity '{activity_value}'. Valid: {valid}.")
    try:
        stage = ProjectStage(stage_value)
    except ValueError:
        valid = ", ".join(s.value for s in ProjectStage)
        raise InputLoadError(f"Unknown stage '{stage_value}'. Valid: {valid}.")
    return Context(activity=activity, stage=stage)


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Explicit help request: usage on stdout, success exit code.
    if argv and argv[0] in {"-h", "--help"}:
        sys.stdout.write(_USAGE + "\n")
        return 0

    # Extract the optional --generated-at flag (either "--generated-at TS" or
    # "--generated-at=TS") before positional parsing.
    generated_at: Optional[str] = None
    positional: List[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--generated-at":
            if i + 1 >= len(argv):
                sys.stderr.write("error: --generated-at requires a value\n")
                return 2
            generated_at = argv[i + 1]
            i += 2
        elif arg.startswith("--generated-at="):
            generated_at = arg.split("=", 1)[1]
            i += 1
        elif arg.startswith("--"):
            sys.stderr.write(f"error: unknown option '{arg}'\n{_USAGE}\n")
            return 2
        else:
            positional.append(arg)
            i += 1

    # Missing required argument: usage on stderr, error exit code.
    if not positional:
        sys.stderr.write(_USAGE + "\n")
        return 2

    input_path = positional[0]
    output_path = positional[1] if len(positional) > 1 else None

    try:
        loaded = load_json_inputs(input_path)
        ctx = _resolve_context(loaded.context)
        parsed = parse_controls(loaded.controls, list(INDICATOR_LIBRARY.keys()))
    except (InputLoadError, ControlDefinitionError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1

    result = run_assessment(
        responses=loaded.responses,
        likelihood=loaded.likelihood,
        impact=loaded.impact,
        detectability=loaded.detectability,
        context=ctx,
        defaults=Defaults(),
        controls=parsed.controls,
        control_issues=parsed.issues,
        generated_at=generated_at,
    )

    # Surface data-quality issues on stderr so they are impossible to miss, while
    # keeping stdout a clean JSON document.
    if not result.validation.complete:
        sys.stderr.write(
            "warning: input is incomplete — "
            f"{result.validation.indicators_fully_answered}/"
            f"{result.validation.total_indicators} indicators fully answered; "
            "missing values were scored with the neutral default.\n"
        )
    if result.validation.unknown_indicator_ids:
        sys.stderr.write(
            "warning: unknown indicator ids ignored: "
            f"{', '.join(result.validation.unknown_indicator_ids)}\n"
        )
    for issue in parsed.issues:
        sys.stderr.write(f"warning: {issue}\n")
    if result.residual.unverified_applied:
        sys.stderr.write(
            "warning: residual risk relies on implemented-but-unverified controls: "
            f"{', '.join(result.residual.unverified_applied)}\n"
        )

    text = json.dumps(result.report, ensure_ascii=False, indent=2)
    sys.stdout.write(text)
    sys.stdout.write("\n")

    if output_path:
        try:
            export_json_report(output_path, result.report)
        except OSError as exc:
            sys.stderr.write(f"error: could not write report to {output_path}: {exc}\n")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
