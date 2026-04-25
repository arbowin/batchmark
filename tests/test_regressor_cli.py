"""Tests for batchmark.regressor_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from batchmark.regressor_cli import build_regressor_parser, main


def _write_baseline(tmp_path: Path, data: dict) -> str:
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps(data))
    return str(p)


def _write_current(tmp_path: Path, batches: list) -> str:
    p = tmp_path / "current.json"
    p.write_text(json.dumps(batches))
    return str(p)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_build_regressor_parser_defaults():
    parser = build_regressor_parser()
    args = parser.parse_args(["baseline.json", "current.json"])
    assert args.baseline == "baseline.json"
    assert args.current == "current.json"
    assert args.threshold == 5.0
    assert args.exit_code is False


def test_build_regressor_parser_custom_threshold():
    parser = build_regressor_parser()
    args = parser.parse_args(["b.json", "c.json", "--threshold", "10.0"])
    assert args.threshold == 10.0


def test_build_regressor_parser_exit_code_flag():
    parser = build_regressor_parser()
    args = parser.parse_args(["b.json", "c.json", "--exit-code"])
    assert args.exit_code is True


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

def test_main_prints_report(tmp_path, capsys):
    bl = _write_baseline(tmp_path, {"cmd": 1.0})
    cur = _write_current(
        tmp_path,
        [{"label": "cmd", "runs": [{"elapsed": 1.0, "returncode": 0}]}],
    )
    main([bl, cur])
    captured = capsys.readouterr()
    assert "cmd" in captured.out


def test_main_missing_baseline_exits(tmp_path):
    cur = _write_current(
        tmp_path,
        [{"label": "cmd", "runs": [{"elapsed": 1.0, "returncode": 0}]}],
    )
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "no_file.json"), cur])
    assert exc.value.code == 2


def test_main_exit_code_on_regression(tmp_path):
    bl = _write_baseline(tmp_path, {"cmd": 1.0})
    cur = _write_current(
        tmp_path,
        [{"label": "cmd", "runs": [{"elapsed": 2.0, "returncode": 0}]}],
    )
    with pytest.raises(SystemExit) as exc:
        main([bl, cur, "--exit-code"])
    assert exc.value.code == 1


def test_main_no_exit_code_when_stable(tmp_path):
    bl = _write_baseline(tmp_path, {"cmd": 1.0})
    cur = _write_current(
        tmp_path,
        [{"label": "cmd", "runs": [{"elapsed": 1.01, "returncode": 0}]}],
    )
    # Should NOT raise SystemExit
    main([bl, cur, "--exit-code"])
