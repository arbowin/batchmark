"""Tests for batchmark.stack_cli."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from batchmark.stack_cli import build_stack_parser, main


def _sample_data(labels=("cmd_a", "cmd_b")):
    return [
        {
            "label": label,
            "runs": [
                {"elapsed": 1.0 + i * 0.1, "returncode": 0}
                for i in range(3)
            ],
        }
        for label in labels
    ]


def _write_json(tmp_path: Path, name: str, data) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_build_stack_parser_defaults():
    parser = build_stack_parser()
    args = parser.parse_args(["a.json", "b.json"])
    assert args.precision == 4
    assert args.files == ["a.json", "b.json"]


def test_build_stack_parser_custom_precision():
    parser = build_stack_parser()
    args = parser.parse_args(["a.json", "--precision", "2"])
    assert args.precision == 2


def test_build_stack_parser_named_files():
    parser = build_stack_parser()
    args = parser.parse_args(["src1=a.json", "src2=b.json"])
    assert "src1=a.json" in args.files


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def test_main_single_file(tmp_path, capsys):
    p = _write_json(tmp_path, "data.json", _sample_data())
    main([str(p)])
    out = capsys.readouterr().out
    assert "cmd_a" in out


def test_main_named_source(tmp_path, capsys):
    p = _write_json(tmp_path, "data.json", _sample_data(["cmd_x"]))
    main([f"mysrc={p}"])
    out = capsys.readouterr().out
    assert "mysrc" in out


def test_main_two_files(tmp_path, capsys):
    p1 = _write_json(tmp_path, "a.json", _sample_data(["cmd"]))
    p2 = _write_json(tmp_path, "b.json", _sample_data(["cmd"]))
    main([str(p1), str(p2)])
    out = capsys.readouterr().out
    assert "cmd" in out


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "nonexistent.json")])
    assert exc_info.value.code == 1


def test_main_precision_flag(tmp_path, capsys):
    p = _write_json(tmp_path, "data.json", _sample_data(["cmd"]))
    main([str(p), "--precision", "2"])
    out = capsys.readouterr().out
    assert "cmd" in out
