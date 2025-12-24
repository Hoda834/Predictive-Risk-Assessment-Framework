import pandas as pd


def assets_to_df(assets):
    return pd.DataFrame([a.__dict__ for a in assets])


def risks_to_df(risks):
    return pd.DataFrame([r.__dict__ for r in risks])


def control_coverage(risks, catalogue):
    count = {}
    for r in risks:
        for c in r.selected_controls:
            count[c] = count.get(c, 0) + 1

    rows = []
    for c in catalogue:
        rows.append(
            {
                "control_id": c["id"],
                "control_title": c["title"],
                "used_in_risks": count.get(c["id"], 0),
            }
        )
    return pd.DataFrame(rows)
