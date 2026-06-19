import json
from typing import Any

from ..security import validate_trace_path

SCHEMA_VERSION = "ozark.dataset.v1"


def export_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA_VERSION,
        "id": dataset["id"],
        "name": dataset["name"],
        "description": dataset["description"],
        "source": dataset["source"],
        "metadata": dataset.get("metadata", {}),
        "items": [
            {
                "scenario": item["scenario"],
                "tags": item.get("tags", []),
                "source_run_id": item.get("source_run_id", ""),
                "source_result_name": item.get("source_result_name", ""),
            }
            for item in dataset.get("items", [])
        ],
    }


def load_dataset_pack(path: str) -> dict[str, Any]:
    source = validate_trace_path(path)
    pack = json.loads(source.read_text(encoding="utf-8"))
    if "dataset" in pack and isinstance(pack["dataset"], dict):
        pack = pack["dataset"]
    if pack.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported dataset schema: {pack.get('schema')}")
    return pack
