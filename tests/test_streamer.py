"""Tests for batchmark.streamer."""

from __future__ import annotations

import pytest

from batchmark.runner import BatchResult, RunResult
from batchmark.streamer import (
    StreamConfig,
    StreamSession,
    collect_stream,
    stream,
)


def _make_run(elapsed: float = 0.1, success: bool = True) -> RunResult:
    return RunResult(elapsed=elapsed, returncode=0 if success else 1, stdout="", stderr="")


def _make_batch(label: str = "cmd", n: int = 3) -> BatchResult:
    runs = [_make_run() for _ in range(n)]
    return BatchResult(label=label, runs=runs)


def _fake_benchmark(cmd: str, label: str = "", iterations: int = 5) -> BatchResult:
    runs = [_make_run(elapsed=0.05 * (i + 1)) for i in range(iterations)]
    return BatchResult(label=label or cmd, runs=runs)


@pytest.fixture(autouse=True)
def patch_benchmark(monkeypatch):
    monkeypatch.setattr("batchmark.streamer.benchmark_command", _fake_benchmark)


def _cfg(**kwargs) -> StreamConfig:
    defaults = dict(commands=["echo a", "echo b"], labels=["a", "b"], iterations=3)
    defaults.update(kwargs)
    return StreamConfig(**defaults)


def test_stream_yields_correct_count():
    results = list(stream(_cfg()))
    assert len(results) == 2


def test_stream_labels_preserved():
    results = list(stream(_cfg()))
    assert results[0].label == "a"
    assert results[1].label == "b"


def test_stream_calls_on_result_callback():
    seen = []
    cfg = _cfg(on_result=lambda r: seen.append(r.label))
    list(stream(cfg))
    assert seen == ["a", "b"]


def test_stream_mismatched_labels_raises():
    cfg = _cfg(labels=["only_one"])
    with pytest.raises(ValueError, match="same length"):
        list(stream(cfg))


def test_stream_invalid_iterations_raises():
    cfg = _cfg(iterations=0)
    with pytest.raises(ValueError, match="iterations"):
        list(stream(cfg))


def test_collect_stream_session_completed():
    session = collect_stream(_cfg())
    assert session.completed == 2


def test_collect_stream_session_total():
    session = collect_stream(_cfg())
    assert session.total == 2


def test_collect_stream_progress_full():
    session = collect_stream(_cfg())
    assert session.progress == pytest.approx(1.0)


def test_collect_stream_results_stored():
    session = collect_stream(_cfg())
    assert len(session.results) == 2


def test_stream_session_progress_empty():
    cfg = _cfg(commands=[], labels=[], iterations=3)
    # empty is valid for session progress calculation
    session = StreamSession(config=cfg)
    assert session.progress == 0.0
