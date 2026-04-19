import os
import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.snapshot import Snapshot, save_snapshot, load_snapshot


def make_batch(label, times):
    runs = [RunResult(elapsed=t, returncode=0, stdout='', stderr='') for t in times]
    return BatchResult(label=label, runs=runs)


def test_save_creates_file(tmp_path):
    snap = Snapshot(name='v1', batches=[make_batch('cmd', [1.0, 1.1])])
    p = str(tmp_path / 'snap.json')
    save_snapshot(snap, p)
    assert os.path.exists(p)


def test_roundtrip_name(tmp_path):
    snap = Snapshot(name='release-1', batches=[make_batch('a', [0.5])])
    p = str(tmp_path / 's.json')
    save_snapshot(snap, p)
    loaded = load_snapshot(p)
    assert loaded.name == 'release-1'


def test_roundtrip_labels(tmp_path):
    snap = Snapshot(name='x', batches=[make_batch('alpha', [1.0]), make_batch('beta', [2.0])])
    p = str(tmp_path / 's.json')
    save_snapshot(snap, p)
    loaded = load_snapshot(p)
    labels = [b.label for b in loaded.batches]
    assert 'alpha' in labels and 'beta' in labels


def test_roundtrip_elapsed(tmp_path):
    snap = Snapshot(name='t', batches=[make_batch('cmd', [1.23, 4.56])])
    p = str(tmp_path / 's.json')
    save_snapshot(snap, p)
    loaded = load_snapshot(p)
    times = [r.elapsed for r in loaded.batches[0].runs]
    assert abs(times[0] - 1.23) < 1e-9


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(str(tmp_path / 'nope.json'))


def test_empty_batches(tmp_path):
    snap = Snapshot(name='empty', batches=[])
    p = str(tmp_path / 'e.json')
    save_snapshot(snap, p)
    loaded = load_snapshot(p)
    assert loaded.batches == []
