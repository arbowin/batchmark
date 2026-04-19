"""Configuration loading for batchmark from TOML/JSON files."""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BenchmarkConfig:
    commands: List[str]
    iterations: int = 5
    timeout: Optional[float] = None
    strategy: str = "sequential"
    export_format: Optional[str] = None
    export_path: Optional[str] = None
    report_path: Optional[str] = None
    report_format: str = "text"
    title: str = "Batchmark Report"


def _load_toml(path: str) -> dict:
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            raise ImportError("Install 'tomli' for TOML support on Python < 3.11")
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(path: str) -> BenchmarkConfig:
    """Load a BenchmarkConfig from a JSON or TOML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif ext in (".toml",):
        data = _load_toml(path)
    else:
        raise ValueError(f"Unsupported config format: {ext}")

    commands = data.get("commands", [])
    if not commands:
        raise ValueError("Config must include at least one command")

    return BenchmarkConfig(
        commands=commands,
        iterations=int(data.get("iterations", 5)),
        timeout=data.get("timeout"),
        strategy=data.get("strategy", "sequential"),
        export_format=data.get("export_format"),
        export_path=data.get("export_path"),
        report_path=data.get("report_path"),
        report_format=data.get("report_format", "text"),
        title=data.get("title", "Batchmark Report"),
    )
