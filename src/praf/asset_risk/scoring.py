def level_to_int(level: str) -> int:
    m = level.lower()
    if m == "low":
        return 1
    if m == "medium":
        return 2
    if m == "high":
        return 3
    return 2


def calculate_score(likelihood: str, impact: str) -> int:
    return level_to_int(likelihood) * level_to_int(impact)


def suggest_treatment(score: int, threshold: int = 4) -> str:
    if score >= threshold:
        return "Reduce"
    return "Accept"
