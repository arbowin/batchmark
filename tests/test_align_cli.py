"""Tests for batchmark.align_cli."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from batchmark.align_cli import build_align_parser, main


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_json(tmp_path: Path, name: str, labels: list[str]) -> str:
    data = [
        {
            "label": lbl,
            "runs": [
                {"elapsed": 0.1, "returncode": 0, "stdout": "", "stderr": ""}
                for _ in range(3)
            ],
        }
        for lbl in labels
    ]
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


# ---------------------------------------------------------------------------
# parser defaults
# ---------------------------------------------------------------------------

def test_build_align_parser_defaults():
    p = build_align_parser()
    args = p.parse_args(["a.json"])
    assert args.fill_missing is True
    assert args.common_only is False
    assert args.names is None


def test_build_align_parser_no_fill():
    p = build_align_parser()
    args = p.parse_args(["a.json", "--no-fill"])
    assert args.fill_missing is False


def test_build_align_parser_common_only():
    p = build_align_parser()
    args = p.parse_args(["a.json", "--common-only"])
    assert args.common_only is True


def test_build_align_parser_names():
    p = build_align_parser()
    args = p.parse_args(["a.json", "b.json", "--names", "alpha", "beta"])
    assert args.names == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

def test_main_mismatched_names_exits(tmp_path):
    f1 = _write_json(tmp_path, "s1.json", ["a"])
    f2 = _write_json(tmp_path, "s2.json", ["a"])
    with pytest.raises(SystemExit):
        main([f1, f2, "--names", "only-one"])


def test_main_missing_file_exits(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "nonexistent.json")])
    assert exc.value.code == 1


def test_main_outputs_alignment(tmp_path, capsys):
    f1 = _write_json(tmp_path, "s1.json", ["fast", "slow"])
    f2 = _write_json(tmp_path, "s2.json", ["fast"])
    main([f1, f2, "--names", "A", "B"])
    out = capsys.readouterr().out
    assert "fast" in out
    assert "slow" in out


def test_main_common_only_flag(tmp_path, capsys):
    f1 = _write_json(tmp_path, "s1.json", ["fast", "slow"])
    f2 = _write_json(tmp_path, "s2.json", ["fast"])
    main([f1, f2, "--common-only"])
    out = capsys.readouterr().out
    assert "fast" in out
    assert "slow" not in out


def test_main_no_fill_records_missing(tmp_path, capsys):
    f1 = _write_json(tmp_path, "s1.json", ["a"])
    f2 = _write_json(tmp_path, "s2.json", ["a", "b"])
    main([f1, f2, "--no-fill"])
    out = capsys.readouterr().out
    # 'b' should appear in the missing section for source-0
    assert "b" in out
