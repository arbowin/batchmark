"""Tests for batchmark.stream_cli."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.stream_cli import build_stream_parser, main


def _make_run(elapsed: float = 0.1) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=0, stdout="", stderr="")


def _fake_collect(config):
    from batchmark.streamer import StreamSession
    results = []
    for cmd, label in zip(config.commands, config.labels):
        runs = [_make_run() for _ in range(config.iterations)]
        br = BatchResult(label=label, runs=runs)
        results.append(br)
        if config.on_result:
            config.on_result(br)
    session = StreamSession(config=config, results=results, completed=len(results))
    return session


@pytest.fixture(autouse=True)
def patch_collect(monkeypatch):
    monkeypatch.setattr("batchmark.stream_cli.collect_stream", _fake_collect)


def test_build_stream_parser_defaults():
    parser = build_stream_parser()
    args = parser.parse_args(["echo hello"])
    assert args.iterations == 5
    assert args.quiet is False


def test_build_stream_parser_custom_iterations():
    parser = build_stream_parser()
    args = parser.parse_args(["echo hi", "-n", "10"])
    assert args.iterations == 10


def test_build_stream_parser_labels():
    parser = build_stream_parser()
    args = parser.parse_args(["echo a", "echo b", "-l", "A", "B"])
    assert args.labels == ["A", "B"]


def test_main_mismatched_labels_exits():
    with pytest.raises(SystemExit) as exc:
        main(["echo a", "echo b", "-l", "only_one"])
    assert exc.value.code == 1


def test_main_runs_without_error(capsys):
    main(["echo a", "echo b", "-l", "A", "B", "-n", "2"])
    captured = capsys.readouterr()
    assert "2/2" in captured.out


def test_main_quiet_suppresses_per_result(capsys):
    main(["echo a", "-l", "A", "--quiet", "-n", "2"])
    captured = capsys.readouterr()
    # summary line still printed
    assert "1/1" in captured.out
