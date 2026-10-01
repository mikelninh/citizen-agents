import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERSONAS = json.loads((HERE / "personas.json").read_text(encoding="utf-8"))


def baseline_routes(p):
    """Old geld-check.html trigger: rent + rough income signal."""
    return bool(p["pays_rent"] and p["low_to_middle_income"])


def candidate_routes(p):
    """Discovery routing only — NOT a legal eligibility calculation."""
    housing_path = p["pays_rent"] or p["owns_home"]
    return bool(
        p["main_residence_berlin"]
        and housing_path
        and p["low_to_middle_income"]
        and not p["housing_transfer_benefit"]
        and not p["all_household_bafog_bab_entitled"]
    )


def evaluate(name, fn):
    rows = []
    tp = fp = tn = fn_count = 0
    for p in PERSONAS:
        predicted = fn(p)
        actual = bool(p["should_route"])
        if predicted and actual:
            outcome = "TP"; tp += 1
        elif predicted and not actual:
            outcome = "FP"; fp += 1
        elif not predicted and not actual:
            outcome = "TN"; tn += 1
        else:
            outcome = "FN"; fn_count += 1
        rows.append({
            "id": p["id"], "label": p["label"],
            "predicted_route": predicted, "should_route": actual,
            "outcome": outcome,
        })

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn_count) if tp + fn_count else 0.0
    accuracy = (tp + tn) / len(rows)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "test": name,
        "semantics": "Routing to an official Wohngeld check; not a legal eligibility determination.",
        "n": len(rows),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn_count},
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "accuracy": round(accuracy, 4),
            "f1": round(f1, 4),
        },
        "failures": [r for r in rows if r["outcome"] in {"FP", "FN"}],
        "all_cases": rows,
    }


def main():
    results = HERE / "results"
    results.mkdir(exist_ok=True)

    baseline = evaluate("CitizenSim v1 / Wohngeld routing baseline", baseline_routes)
    candidate = evaluate("CitizenSim v1 / Wohngeld candidate routing regression", candidate_routes)
    candidate["warning"] = (
        "Regression fixture only. The cohort was designed around known failure modes; "
        "100% here is not a real-world or legal accuracy claim."
    )

    (results / "baseline.json").write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (results / "candidate.json").write_text(
        json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    assert baseline["metrics"]["precision"] == 0.625
    assert baseline["metrics"]["recall"] == 0.8333
    assert candidate["confusion_matrix"] == {"tp": 6, "fp": 0, "tn": 6, "fn": 0}

    print(json.dumps({"baseline": baseline["metrics"], "candidate": candidate["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
