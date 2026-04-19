"""Tests for batchmark.notifier."""
import pytest
from batchmark.runner import BatchResult
from batchmark.notifier import NotifierConfig, evaluate, notify, NotificationEvent


def make_batch(label: str, times, success_count: int) -> BatchResult:
    return BatchResult(label=label, times=times, success_count=success_count)


def test_evaluate_no_events_when_thresholds_met():
    result = make_batch("cmd", [10.0, 20.0], 2)
    config = NotifierConfig(min_success_rate=0.5, max_mean_ms=100.0)
    assert evaluate(result, config) == []


def test_evaluate_error_on_low_success_rate():
    result = make_batch("cmd", [10.0, 20.0], 0)
    config = NotifierConfig(min_success_rate=0.8)
    events = evaluate(result, config)
    assert len(events) == 1
    assert events[0].level == "error"
    assert "Success rate" in events[0].message


def test_evaluate_warn_on_high_mean():
    result = make_batch("slow", [200.0, 300.0], 2)
    config = NotifierConfig(max_mean_ms=100.0)
    events = evaluate(result, config)
    assert len(events) == 1
    assert events[0].level == "warn"
    assert "Mean" in events[0].message


def test_evaluate_both_violations():
    result = make_batch("bad", [500.0], 0)
    config = NotifierConfig(min_success_rate=1.0, max_mean_ms=100.0)
    events = evaluate(result, config)
    assert len(events) == 2


def test_evaluate_empty_times():
    result = make_batch("empty", [], 0)
    config = NotifierConfig(min_success_rate=0.5)
    events = evaluate(result, config)
    assert events[0].level == "error"


def test_notify_collects_all_events():
    results = [
        make_batch("a", [500.0], 0),
        make_batch("b", [10.0], 1),
    ]
    config = NotifierConfig(min_success_rate=0.5, max_mean_ms=100.0)
    events = notify(results, config)
    labels = [e.label for e in events]
    assert "a" in labels


def test_notify_calls_on_event_callback():
    collected = []
    result = make_batch("x", [999.0], 0)
    config = NotifierConfig(min_success_rate=1.0, on_event=collected.append)
    notify([result], config)
    assert len(collected) >= 1


def test_notify_no_callback_no_error():
    result = make_batch("ok", [5.0], 1)
    config = NotifierConfig()
    events = notify([result], config)
    assert isinstance(events, list)


def test_event_label_matches_result():
    result = make_batch("mylabel", [50.0], 0)
    config = NotifierConfig(min_success_rate=1.0)
    events = evaluate(result, config)
    assert events[0].label == "mylabel"
