"""Tests for batchmark.exporter module."""

import json
import csv
import io
import pytest
from unittest.mock import MagicMock
from batchmark.exporter import export_json, export_csv, export


def make_batch_result(label, times, success_count):
    br = MagicMock()
    br.label = label
    br.times = times
    br.success_count = success_count
    return br


def test_export_json_structure():
    br = make_batch_result("echo", [0.1, 0.2, 0.15], 3)
    result = json.loads(export_json([br]))
    assert len(result) == 1
    entry = result[0]
    assert entry["label"] == "echo"
    assert entry["iterations"] == 3
    assert entry["success_count"] == 3
    assert "mean" in entry
    assert "median" in entry
    assert "stdev" in entry
    assert "min" in entry
    assert "max" in entry


def test_export_json_multiple():
    brs = [
        make_batch_result("cmd1", [0.1, 0.2], 2),
        make_batch_result("cmd2", [0.3, 0.4], 1),
    ]
    result = json.loads(export_json(brs))
    assert len(result) == 2
    assert result[0]["label"] == "cmd1"
    assert result[1]["label"] == "cmd2"


def test_export_csv_header():
    br = make_batch_result("sleep", [1.0, 1.1], 2)
    output = export_csv([br])
    reader = csv.DictReader(io.StringIO(output))
    fieldnames = reader.fieldnames
    assert "label" in fieldnames
    assert "mean" in fieldnames
    assert "stdev" in fieldnames


def test_export_csv_row_values():
    br = make_batch_result("ls", [0.05, 0.07], 2)
    output = export_csv([br])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["label"] == "ls"
    assert rows[0]["iterations"] == "2"


def test_export_dispatch_json():
    br = make_batch_result("x", [0.1], 1)
    result = export([br], "json")
    assert result.startswith("{" ) or result.startswith("[")


def test_export_dispatch_csv():
    br = make_batch_result("x", [0.1], 1)
    result = export([br], "csv")
    assert "label" in result


def test_export_invalid_format():
    br = make_batch_result("x", [0.1], 1)
    with pytest.raises(ValueError, match="Unsupported export format"):
        export([br], "xml")
