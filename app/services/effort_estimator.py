from __future__ import annotations


def estimate(direct: int, indirect: int, possible: int, modules: int, change_type: str) -> dict:
    points = direct * 2 + indirect + possible * 0.4 + modules * 1.2 + (1.5 if change_type == "remove" else 1 if change_type == "modify" else 2)
    if points < 5:
        level, range_text = "Low", "a few hours"
    elif points < 10:
        level, range_text = "Medium", "approximately one to three working days"
    else:
        level, range_text = "High", "more than three working days"
    return {"level": level, "range": range_text, "points": round(points, 1), "disclaimer": "Illustrative heuristic estimate requiring developer review; it is not a prediction of actual engineering hours."}
