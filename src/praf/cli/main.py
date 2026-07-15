from __future__ import annotations

import json
import sys
from typing import Any, Dict

from praf.domain import Context
from praf.domain.domains import activity_domain_weights
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains
from praf.engine.rules import decide
from praf.engine.explainability import explain
from praf.engine.audit_trail import build_audit_trail
from praf.engine.validation import validate_context, validate_inputs, InputValidationError
from praf.io.loaders import load_json_inputs
from praf.config.defaults import Defaults


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: python -m praf.cli.main <input.json>\n")
        return 2

    input_path = sys.argv[1]

    try:
        loaded = load_json_inputs(input_path)
    except FileNotFoundError:
        sys.stderr.write(f"error: input file not found: {input_path}\n")
        return 2
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"error: input file is not valid JSON: {exc}\n")
        return 2

    try:
        activity, stage = validate_context(loaded.activity, loaded.stage)
        validate_inputs(loaded.responses, loaded.likelihood, loaded.impact, loaded.detectability)
    except InputValidationError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    ctx = Context(activity=activity, stage=stage)
    domain_weights = activity_domain_weights(ctx.activity)

    defaults = Defaults()

    score_result = score_indicators(
        responses=loaded.responses,
        likelihood=loaded.likelihood,
        impact=loaded.impact,
        detectability=loaded.detectability,
        domain_weights=domain_weights,
    )

    aggregated = aggregate_scores(score_result.indicator_details, score_result.local_scores)
    classifications = classify_domains(
        aggregated.domain_scores,
        defaults.low_threshold,
        defaults.high_threshold,
        coverage=aggregated.domain_coverage,
        coverage_threshold=defaults.coverage_threshold,
    )
    decision = decide(classifications)
    expl = explain(classifications, score_result.indicator_details, score_result.local_scores, top_n=5)
    audit = build_audit_trail(classifications, decision, score_result.indicator_details, score_result.local_scores)

    report: Dict[str, Any] = {
        "context": {"activity": ctx.activity.value, "stage": ctx.stage.value},
        "overall_decision": decision.overall.value,
        "per_domain_decision": {d.value: decision.per_domain[d].value for d in decision.per_domain},
        "domain_scores": {
            d.value: {
                "score": classifications[d].score,
                "level": classifications[d].level.value,
                "coverage": round(classifications[d].coverage, 3),
            }
            for d in classifications
        },
        "top_contributors_by_domain": {d.value: expl.top_contributors_by_domain.get(d, []) for d in classifications},
        "audit_trail": [{"key": a.key, "value": a.value} for a in audit],
    }

    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
