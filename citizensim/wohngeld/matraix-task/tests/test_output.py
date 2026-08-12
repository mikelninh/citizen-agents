import json
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


def test_output_schema():
    assert OUT.exists(), f"missing {OUT}"
    data = json.loads(OUT.read_text(encoding="utf-8"))
    for key, typ in REQUIRED.items():
        assert key in data, f"missing key: {key}"
        assert isinstance(data[key], typ), f"wrong type for {key}"
    assert data["wohngeld_path"] in {"mietzuschuss", "lastenzuschuss", "none"}
    assert 0 <= float(data["confidence"]) <= 1
