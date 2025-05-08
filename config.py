import json
from pathlib import Path

def load_config(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_config(path: Path, cfg: dict):
    path.write_text(json.dumps(cfg, indent=2))
