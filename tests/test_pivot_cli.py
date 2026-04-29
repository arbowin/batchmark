"""Tests for batchmark.pivot_cli."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from batchmark.pivot_cli import build_pivot_parser, main


def _sample_data():
    return [
        {
            "label": "alpha",
            "runs": [
                {"elapsed": 1.0, "returncode": 0, "stdout": "", "stderr": ""},
                {"elapsed": 2.0, "returncode": 0, "stdout": "", "stderr": ""},
            ],
        },
        {
            "label": "beta",
            "runs": [
                {"elapsed": 3.0, "returncode": 0, "stdout": "", "stderr": ""},
                {"elapsed": 4.0, "returncode": 1, "stdout": "", "stderr": ""},
            ],
        },
    ]


def _write_json(tmp_path: Path, data) -> Path:
    p = tmp_path / "batches.json"
    p.write_text(json.dumps(data))
    return p


def test_build_pivot_parser_defaults():
    parser = build_pivot_parser()
    args = parser.parse_args(["some_file.json"])
    assert args.input == "some_file.json"
    assert args.metrics is None
    assert args.precision == 4


def test_build_pivot_parser_custom_metrics():
    parser = build_pivot_parser()
    args = parser.parse_args(["f.json", "--metrics", "mean", "min"])
    assert args.metrics == ["mean", "min"]


def test_build_pivot_parser_custom_precision():
    parser = build_pivot_parser()
    args = parser.parse_args(["f.json", "--precision", "2"])
    assert args.precision == 2


def test_main_output_contains_labels(tmp_path, capsys):
    p = _write_json(tmp_path, _sample_data())
    main([str(p), "--metrics", "mean"])
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_main_output_contains_metric_header(tmp_path, capsys):
    p = _write_json(tmp_path, _sample_data())
    main([str(p), "--metrics", "mean", "max"])
    out = capsys.readouterr().out
    assert "mean" in out
    assert "max" in out


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.json")])
    assert exc_info.value.code == 1


def test_main_empty_batches_exits(tmp_path):
    p = _write_json(tmp_path, [])
    with pytest.raises(SystemExit) as exc_info:
        main([str(p)])
    assert exc_info.value.code == 1
