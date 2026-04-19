"""Save and load benchmark snapshots for later diffing."""
import json
import os
from dataclasses import dataclass, asdict
from typing import List
from batchmark.runner import BatchResult, RunResult


@dataclass
class Snapshot:
    name: str
    batches: List[BatchResult]


def _batch_to_dict(b: BatchResult) -> dict:
    return {
        'label': b.label,
        'runs': [{'elapsed': r.elapsed, 'returncode': r.returncode} for r in b.runs],
    }


def _dict_to_batch(d: dict) -> BatchResult:
    runs = [RunResult(elapsed=r['elapsed'], returncode=r['returncode'], stdout='', stderr='') for r in d['runs']]
    return BatchResult(label=d['label'], runs=runs)


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    data = {
        'name': snapshot.name,
        'batches': [_batch_to_dict(b) for b in snapshot.batches],
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_snapshot(path: str) -> Snapshot:
    if not os.path.exists(path):
        raise FileNotFoundError(f'Snapshot file not found: {path}')
    with open(path) as f:
        data = json.load(f)
    return Snapshot(
        name=data['name'],
        batches=[_dict_to_batch(b) for b in data['batches']],
    )
