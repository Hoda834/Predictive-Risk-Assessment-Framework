from __future__ import annotations

import json
import sys
from typing import Any, Dict

from praf.domain import Context, Activity, ProjectStage
from praf.domain.domains import activity_domain_weights
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains
from praf.engine.rules import decide
from praf.engine.explainability import explain
from praf.engine.audit_trail import build_audit_trail
from praf.io.loaders import load_json_inputs
from praf.config.defaults import Defaults


def main() -> int:
    if len(sys.argv) < 2:
        return 2

    input_path = sys.argv[1]
    loaded = load_json_inputs(input_path)

    payload_activity = "product_design"
    payload_stage = "design"

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        payload_activity = str(raw.get("context", {}).get("activity", payload_activity))
        payload_stage = str(raw.get("context", {}).get("stage", payload_stage))
    except Exception:
        pass

    ctx = Context(activity=Activity(payload_activity), stage=ProjectStage(payload_stage))
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
    classifications = classify_domains(aggregated.domain_scores, defaults.low_threshold, defaults.high_threshold)
    decision = decide(classifications)
    expl = explain(classifications, score_result.indicator_details, score_result.local_scores, top_n=5)
    audit = build_audit_trail(classifications, decision, score_result.indicator_details, score_result.local_scores)

    report: Dict[str, Any] = {
        "context": {"activity": ctx.activity.value, "stage": ctx.stage.value},
        "overall_decision": decision.overall.value,
        "per_domain_decision": {d.value: decision.per_domain[d].value for d in decision.per_domain},
        "domain_scores": {d.value: {"score": classifications[d].score, "level": classifications[d].level.value} for d in classifications},
        "top_contributors_by_domain": {d.value: expl.top_contributors_by_domain.get(d, []) for d in classifications},
        "audit_trail": [{"key": a.key, "value": a.value} for a in audit],
    }

    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
