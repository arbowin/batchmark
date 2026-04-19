"""File-based trigger watcher for re-running benchmarks on change."""

import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class WatchedFile:
    path: str
    last_hash: Optional[str] = None


@dataclass
class WatcherConfig:
    paths: List[str]
    interval: float = 1.0
    max_triggers: int = 0  # 0 = unlimited


def _file_hash(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return None


def _init_watched(paths: List[str]) -> List[WatchedFile]:
    return [WatchedFile(path=p, last_hash=_file_hash(p)) for p in paths]


def _changed_files(watched: List[WatchedFile]) -> List[str]:
    changed = []
    for wf in watched:
        current = _file_hash(wf.path)
        if current != wf.last_hash:
            wf.last_hash = current
            changed.append(wf.path)
    return changed


def watch(config: WatcherConfig, callback: Callable[[List[str]], None]) -> int:
    """Watch files and invoke callback with changed paths. Returns trigger count."""
    watched = _init_watched(config.paths)
    triggers = 0
    while True:
        time.sleep(config.interval)
        changed = _changed_files(watched)
        if changed:
            callback(changed)
            triggers += 1
            if config.max_triggers > 0 and triggers >= config.max_triggers:
                break
    return triggers
