"""Tests for batchmark.scaler_cli."""

import json
import textwrap
from pathlib import Path

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.scaler_cli import build_scale_parser, main


def _run(elapsed: float, rc: int = 0) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=rc, stdout="", stderr="")


def make_batch(label: str, times: list[float]) -> BatchResult:
    return BatchResult(label=label, runs=[_run(t) for t in times])


def _write_json(tmp_path: Path, batches: list[BatchResult]) -> Path:
    data = [
        {
            "label": b.label,
            "runs": [{"elapsed": r.elapsed, "returncode": r.returncode} for r in b.runs],
        }
        for b in batches
    ]
    p = tmp_path / "batches.json"
    p.write_text(json.dumps(data))
    return p


def test_build_scale_parser_defaults():
    parser = build_scale_parser()
    args = parser.parse_args(["input.json"])
    assert args.factor == 1.0
    assert args.offset == 0.0
    assert args.format == "text"
    assert args.precision == 4


def test_build_scale_parser_custom_factor():
    parser = build_scale_parser()
    args = parser.parse_args(["input.json", "--factor", "2.5"])
    assert args.factor == 2.5


def test_build_scale_parser_custom_offset():
    parser = build_scale_parser()
    args = parser.parse_args(["input.json", "--offset", "0.05"])
    assert args.offset == 0.05


def test_build_scale_parser_json_format():
    parser = build_scale_parser()
    args = parser.parse_args(["input.json", "--format", "json"])
    assert args.format == "json"


def test_main_text_output_contains_label(tmp_path, capsys):
    p = _write_json(tmp_path, [make_batch("cmd-a", [1.0, 2.0, 3.0])])
    main([str(p), "--factor", "2.0"])
    captured = capsys.readouterr()
    assert "cmd-a" in captured.out


def test_main_json_output_is_valid(tmp_path, capsys):
    p = _write_json(tmp_path, [make_batch("cmd-b", [1.0, 2.0])])
    main([str(p), "--format", "json", "--factor", "3.0"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_main_json_elapsed_scaled(tmp_path, capsys):
    p = _write_json(tmp_path, [make_batch("cmd-c", [2.0, 4.0])])
    main([str(p), "--format", "json", "--factor", "2.0"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    elapsed_values = [r["elapsed"] for r in data[0]["runs"]]
    assert elapsed_values == pytest.approx([4.0, 8.0])


def test_main_json_offset_applied(tmp_path, capsys):
    p = _write_json(tmp_path, [make_batch("cmd-d", [1.0, 2.0])])
    main([str(p), "--format", "json", "--offset", "1.0"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    elapsed_values = [r["elapsed"] for r in data[0]["runs"]]
    assert elapsed_values == pytest.approx([2.0, 3.0])
