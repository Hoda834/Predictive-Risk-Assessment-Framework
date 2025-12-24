import csv


def load_control_catalogue(path: str):
    controls = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            controls.append(
                {
                    "id": row["control_id"],
                    "title": row["control_title"],
                }
            )
    return controls
