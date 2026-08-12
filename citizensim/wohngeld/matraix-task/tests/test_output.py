import json
import os
from pathlib import Path

OUT = Path("/app/output/citizensim_result.json")
REQUIRED = {
    "completed": bool,
    "wohngeld_shown": bool,
    "wohngeld_path": str,
    "clicked_wohngeld_next_step": bool,
    "understood_that_result_is_only_a_routing_hint": bool,
    "confidence": (int, float),
    "friction": list,
    "reason": str,
}


def verifier_dir() -> Path:
    explicit = os.environ.get("HARBOR_VERIFIER_DIR")
    path = Path(explicit) if explicit else Path("/logs/verifier")
    path.mkdir(parents=True, exist_ok=True)
    return path


def facet(key, label, value, *, kind="categorical", role="primary"):
    if kind == "categorical" and isinstance(value, bool):
        value = "true" if value else "false"
    return {"key": key, "label": label, "role": role, "kind": kind, "value": value}


def test_output_schema():
    assert OUT.exists(), f"missing {OUT}"
    data = json.loads(OUT.read_text(encoding="utf-8"))
    for key, typ in REQUIRED.items():
        assert key in data, f"missing key: {key}"
        assert isinstance(data[key], typ), f"wrong type for {key}"
    assert data["wohngeld_path"] in {"mietzuschuss", "lastenzuschuss", "none"}
    assert 0 <= float(data["confidence"]) <= 1

    structured = {
        "schemaVersion": "1.0",
        "artifactType": "matraix.trial_evaluation",
        "taskType": "web",
        "presenceCheck": {
            "passed": True,
            "requiredArtifacts": [OUT.name],
            "missingArtifacts": [],
        },
        "sourceArtifacts": {"taskOutput": str(OUT)},
        "contexts": [
            {
                "key": "decision.primary",
                "label": "CitizenSim result",
                "contextType": "decision",
                "facets": [
                    facet("completed", "Flow completed", data["completed"]),
                    facet("wohngeld_shown", "Wohngeld surfaced", data["wohngeld_shown"]),
                    facet("wohngeld_path", "Wohngeld route", data["wohngeld_path"]),
                    facet("clicked_wohngeld_next_step", "Official next-step click", data["clicked_wohngeld_next_step"]),
                    facet(
                        "understood_that_result_is_only_a_routing_hint",
                        "Routing disclaimer understood",
                        data["understood_that_result_is_only_a_routing_hint"],
                    ),
                    facet("confidence", "Confidence", float(data["confidence"]), kind="numerical", role="score"),
                    facet("reason", "Reason", data["reason"].strip(), kind="textual", role="explanation"),
                    facet("friction", "Friction", "; ".join(map(str, data["friction"])), kind="textual", role="evidence"),
                ],
            }
        ],
    }
    (verifier_dir() / "structured_output.json").write_text(
        json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8"
    )
