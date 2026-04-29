"""Tests for batchmark.mix_export."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.mixer import mix
from batchmark.mix_export import export_mix_json, export_mix_csv, save_mix_export


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times, rc: int = 0) -> BatchResult:
    return BatchResult(label=label, runs=[_run(t, rc) for t in times])


def _result():
    src = {
        "a": [make_batch("cmd1", [1.0, 2.0, 3.0])],
        "b": [make_batch("cmd1", [4.0])],
    }
    return mix(src)


# ---------------------------------------------------------------------------
# export_mix_json
# ---------------------------------------------------------------------------

def test_export_mix_json_is_valid_json():
    data = json.loads(export_mix_json(_result()))
    assert isinstance(data, list)


def test_export_mix_json_contains_label():
    data = json.loads(export_mix_json(_result()))
    labels = [item["label"] for item in data]
    assert "cmd1" in labels


def test_export_mix_json_has_mean():
    data = json.loads(export_mix_json(_result()))
    assert data[0]["mean"] is not None


def test_export_mix_json_sources_list():
    data = json.loads(export_mix_json(_result()))
    assert isinstance(data[0]["sources"], list)
    assert "a" in data[0]["sources"]


def test_export_mix_json_runs_present():
    data = json.loads(export_mix_json(_result()))
    assert len(data[0]["runs"]) == 4


# ---------------------------------------------------------------------------
# export_mix_csv
# ---------------------------------------------------------------------------

def test_export_mix_csv_header():
    text = export_mix_csv(_result())
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    assert "label" in header
    assert "mean" in header


def test_export_mix_csv_row_count():
    text = export_mix_csv(_result())
    rows = list(csv.reader(io.StringIO(text)))
    # header + 1 label row
    assert len(rows) == 2


def test_export_mix_csv_label_value():
    text = export_mix_csv(_result())
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[1][0] == "cmd1"


# ---------------------------------------------------------------------------
# save_mix_export
# ---------------------------------------------------------------------------

def test_save_mix_export_json_creates_file():
    result = _result()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "out.json")
        save_mix_export(result, path, fmt="json")
        assert os.path.exists(path)


def test_save_mix_export_csv_creates_file():
    result = _result()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "out.csv")
        save_mix_export(result, path, fmt="csv")
        assert os.path.exists(path)


def test_save_mix_export_invalid_fmt_raises():
    with pytest.raises(ValueError, match="unsupported format"):
        save_mix_export(_result(), "/dev/null", fmt="xml")
