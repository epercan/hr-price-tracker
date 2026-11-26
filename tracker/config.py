import tomllib
from pathlib import Path


def load_config(path="config.toml"):
    path = Path(path).resolve()
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    base = path.parent
    cfg["data_dir"] = base / cfg.get("data_dir", "data")
    cfg["db_path"] = base / cfg.get("db_path", "data/tracker.db")
    return cfg
