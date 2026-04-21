"""Tests for batchmark.group_cli."""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from batchmark.group_cli import build_group_parser, main


# --- parser ---

def test_build_group_parser_defaults():
    parser = build_group_parser()
    args = parser.parse_args(["results.json"])
    assert args.strategy == "prefix"
    assert args.sep == ":"
    assert args.input == "results.json"


def test_build_group_parser_custom_strategy():
    parser = build_group_parser()
    args = parser.parse_args(["results.json", "--strategy", "label"])
    assert args.strategy == "label"


def test_build_group_parser_custom_sep():
    parser = build_group_parser()
    args = parser.parse_args(["results.json", "--sep", "/"])
    assert args.sep == "/"


# --- main ---

def _write_json(tmp_path, data):
    p = tmp_path / "results.json"
    p.write_text(json.dumps(data))
    return str(p)


def _sample_data():
    return [
        {
            "label": "python:fast",
            "runs": [{"elapsed": 0.1, "returncode": 0}],
        },
        {
            "label": "python:slow",
            "runs": [{"elapsed": 0.5, "returncode": 0}],
        },
        {
            "label": "node:fast",
            "runs": [{"elapsed": 0.2, "returncode": 0}],
        },
    ]


def test_main_outputs_group_header(tmp_path, capsys):
    path = _write_json(tmp_path, _sample_data())
    main([path])
    out = capsys.readouterr().out
    assert "[python]" in out
    assert "[node]" in out


def test_main_label_strategy_outputs_each_label(tmp_path, capsys):
    path = _write_json(tmp_path, _sample_data())
    main([path, "--strategy", "label"])
    out = capsys.readouterr().out
    assert "python:fast" in out
    assert "node:fast" in out


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "nonexistent.json")])
    assert exc_info.value.code == 1


def test_main_empty_batches_exits(tmp_path):
    path = _write_json(tmp_path, [])
    with pytest.raises(SystemExit) as exc_info:
        main([path])
    assert exc_info.value.code == 1


def test_main_custom_sep(tmp_path, capsys):
    data = [
        {"label": "a/x", "runs": [{"elapsed": 0.1, "returncode": 0}]},
        {"label": "a/y", "runs": [{"elapsed": 0.2, "returncode": 0}]},
    ]
    path = _write_json(tmp_path, data)
    main([path, "--sep", "/"])
    out = capsys.readouterr().out
    assert "[a]" in out
    assert "2 batch" in out
