"""Tests for batchmark.sort_cli."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from batchmark.sort_cli import build_sort_parser, main


def _write_json(data: list, suffix: str = ".json") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    return path


def _sample_data() -> list:
    return [
        {"label": "slow", "runs": [{"elapsed": 2.0, "returncode": 0}, {"elapsed": 3.0, "returncode": 0}]},
        {"label": "fast", "runs": [{"elapsed": 0.4, "returncode": 0}, {"elapsed": 0.5, "returncode": 0}]},
        {"label": "mid", "runs": [{"elapsed": 1.0, "returncode": 0}]},
    ]


def test_build_sort_parser_defaults():
    parser = build_sort_parser()
    args = parser.parse_args(["results.json"])
    assert args.key == "mean"
    assert args.order == "asc"
    assert not args.json_output


def test_build_sort_parser_custom_key():
    parser = build_sort_parser()
    args = parser.parse_args(["results.json", "--key", "median"])
    assert args.key == "median"


def test_build_sort_parser_desc_order():
    parser = build_sort_parser()
    args = parser.parse_args(["results.json", "--order", "desc"])
    assert args.order == "desc"


def test_main_text_output_contains_label(capsys):
    path = _write_json(_sample_data())
    try:
        main([path])
        captured = capsys.readouterr()
        assert "fast" in captured.out
        assert "slow" in captured.out
    finally:
        os.unlink(path)


def test_main_text_output_sorted_order(capsys):
    path = _write_json(_sample_data())
    try:
        main([path, "--key", "mean", "--order", "asc"])
        captured = capsys.readouterr()
        fast_pos = captured.out.index("fast")
        slow_pos = captured.out.index("slow")
        assert fast_pos < slow_pos
    finally:
        os.unlink(path)


def test_main_json_output_is_valid_json(capsys):
    path = _write_json(_sample_data())
    try:
        main([path, "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 3
    finally:
        os.unlink(path)


def test_main_missing_file_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_file_xyz.json"])
    assert exc_info.value.code != 0
