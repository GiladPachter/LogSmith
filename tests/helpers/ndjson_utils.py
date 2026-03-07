import json
from pathlib import Path


def load_ndjson(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def is_valid_ndjson(path: Path) -> bool:
    try:
        _ = load_ndjson(path)
        return True
    except Exception:
        return False
