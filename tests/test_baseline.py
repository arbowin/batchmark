"""Tests for batchmark.baseline."""

import json
import pytest
from pathlib import Path

from batchmark.runner import BatchResult, RunResult
from batchmark.baseline import (
    save_baseline,
    load_baseline,
    compare_to_baseline,
    format_baseline_comparison,
)


def make_batch(label: str, times: list[float], successes: int | None = None) -> BatchResult:
    if successes is None:
        successes = len(times)
    runs = [RunResult(exit_code=0, elapsed=t, stdout="", stderr="") for t in times]
    return BatchResult(label=label, runs=runs)


def test_save_baseline_creates_file(tmp_path):
    br = make_batch("cmd_a", [0.1, 0.2, 0.3])
    out = tmp_path / "baseline.json"
    save_baseline([br], out)
    assert out.exists()


def test_save_baseline_json_structure(tmp_path):
    br = make_batch("cmd_a", [0.1, 0.2, 0.3])
    out = tmp_path / "baseline.json"
    save_baseline([br], out)
    data = json.loads(out.read_text())
    assert len(data) == 1
    assert data[0]["label"] == "cmd_a"
    assert "mean" in data[0]
    assert "stdev" in data[0]


def test_load_baseline_returns_dict(tmp_path):
    br = make_batch("cmd_a", [0.1, 0.2, 0.3])
    out = tmp_path / "baseline.json"
    save_baseline([br], out)
    baseline = load_baseline(out)
    assert "cmd_a" in baseline
    assert baseline["cmd_a"]["mean"] == pytest.approx(0.2, rel=1e-3)


def test_load_baseline_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_baseline(tmp_path / "nonexistent.json")


def test_compare_to_baseline_delta(tmp_path):
    old = make_batch("cmd_a", [0.1, 0.1, 0.1])
    out = tmp_path / "baseline.json"
    save_baseline([old], out)
    baseline = load_baseline(out)

    current = make_batch("cmd_a", [0.2, 0.2, 0.2])
    comparisons = compare_to_baseline([current], baseline)
    assert len(comparisons) == 1
    c = comparisons[0]
    assert c.label == "cmd_a"
    assert c.delta == pytest.approx(0.1, rel=1e-3)
    assert c.improved is False


def test_compare_to_baseline_improved(tmp_path):
    old = make_batch("cmd_a", [0.3, 0.3, 0.3])
    out = tmp_path / "baseline.json"
    save_baseline([old], out)
    baseline = load_baseline(out)

    current = make_batch("cmd_a", [0.1, 0.1, 0.1])
    comparisons = compare_to_baseline([current], baseline)
    assert comparisons[0].improved is True


def test_compare_skips_missing_label(tmp_path):
    old = make_batch("cmd_a", [0.1, 0.1])
    out = tmp_path / "baseline.json"
    save_baseline([old], out)
    baseline = load_baseline(out)

    current = make_batch("cmd_b", [0.2, 0.2])
    comparisons = compare_to_baseline([current], baseline)
    assert comparisons == []


def test_format_baseline_comparison_contains_label(tmp_path):
    old = make_batch("cmd_a", [0.1, 0.1, 0.1])
    out = tmp_path / "baseline.json"
    save_baseline([old], out)
    baseline = load_baseline(out)
    current = make_batch("cmd_a", [0.2, 0.2, 0.2])
    comparisons = compare_to_baseline([current], baseline)
    text = format_baseline_comparison(comparisons)
    assert "cmd_a" in text
    assert "regressed" in text
