"""Tests for batchmark.reporter module."""

import os
import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.reporter import Report, build_report, save_report


def make_batch(label: str, times, successes=None):
    n = len(times)
    if successes is None:
        successes = [True] * n
    runs = [RunResult(duration=t, success=s, stdout="", stderr="") for t, s in zip(times, successes)]
    return BatchResult(label=label, runs=runs)


def test_report_to_text_contains_title():
    r = make_batch("cmd", [0.1, 0.2, 0.3])
    report = build_report([r], title="My Report")
    text = report.to_text()
    assert "My Report" in text


def test_report_to_text_contains_label():
    r = make_batch("echo hello", [0.1, 0.2])
    report = build_report([r])
    text = report.to_text()
    assert "echo hello" in text


def test_report_to_html_contains_title():
    r = make_batch("ls", [0.05, 0.06])
    report = build_report([r], title="HTML Report")
    html = report.to_html()
    assert "<title>HTML Report</title>" in html
    assert "<h1>HTML Report</h1>" in html


def test_report_to_html_contains_pre():
    r = make_batch("ls", [0.05, 0.06])
    report = build_report([r])
    html = report.to_html()
    assert "<pre>" in html


def test_build_report_multiple_includes_comparison():
    r1 = make_batch("fast", [0.1, 0.1, 0.1])
    r2 = make_batch("slow", [0.5, 0.5, 0.5])
    report = build_report([r1, r2])
    text = report.to_text()
    assert "Comparison" in text


def test_build_report_single_no_comparison():
    r = make_batch("only", [0.2, 0.3])
    report = build_report([r])
    text = report.to_text()
    assert "Comparison" not in text


def test_build_report_empty_raises():
    with pytest.raises(ValueError):
        build_report([])


def test_save_report_text(tmp_path):
    r = make_batch("cmd", [0.1, 0.2])
    report = build_report([r], title="Saved")
    out = str(tmp_path / "report.txt")
    save_report(report, out, fmt="text")
    assert os.path.exists(out)
    content = open(out).read()
    assert "Saved" in content


def test_save_report_html(tmp_path):
    r = make_batch("cmd", [0.1, 0.2])
    report = build_report([r], title="HTMLOut")
    out = str(tmp_path / "report.html")
    save_report(report, out, fmt="html")
    content = open(out).read()
    assert "<!DOCTYPE html>" in content
    assert "HTMLOut" in content
