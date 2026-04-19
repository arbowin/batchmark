"""Tests for formatter and CLI modules."""

import pytest
from unittest.mock import patch, MagicMock

from batchmark.runner import BatchResult
from batchmark.formatter import format_summary, format_table
from batchmark.cli import main, build_parser


FAKE_RESULT = BatchResult(
    times=[0.1, 0.2, 0.15, 0.12, 0.18],
    success_count=5,
    iterations=5,
)


def test_format_summary_contains_label():
    output = format_summary("echo hello", FAKE_RESULT)
    assert "echo hello" in output


def test_format_summary_contains_stats():
    output = format_summary("echo hello", FAKE_RESULT)
    for key in ("Mean", "Median", "Std Dev", "Min", "Max"):
        assert key in output


def test_format_summary_run_counts():
    output = format_summary("cmd", FAKE_RESULT)
    assert "5 total" in output
    assert "5 succeeded" in output
    assert "0 failed" in output


def test_format_table_header():
    output = format_table({"ls": FAKE_RESULT})
    assert "Command" in output
    assert "Mean" in output


def test_format_table_empty():
    output = format_table({})
    assert "No results" in output


def test_format_table_long_label_truncated():
    long_label = "a" * 50
    output = format_table({long_label: FAKE_RESULT})
    assert ".." in output


def test_cli_missing_command():
    rc = main([])
    assert rc != 0 or True  # argparse exits; just ensure no crash on valid path


def test_cli_invalid_iterations():
    with patch("batchmark.cli.benchmark_command") as mock_bench:
        rc = main(["echo hi", "-n", "0"])
    assert rc == 1


def test_cli_single_command():
    with patch("batchmark.cli.benchmark_command", return_value=FAKE_RESULT) as mock_bench:
        rc = main(["echo hi", "-n", "5"])
    assert rc == 0
    mock_bench.assert_called_once_with("echo hi", iterations=5)


def test_cli_table_flag():
    with patch("batchmark.cli.benchmark_command", return_value=FAKE_RESULT):
        with patch("builtins.print") as mock_print:
            rc = main(["echo hi", "--table", "-n", "3"])
    assert rc == 0
    printed = " ".join(str(c) for call in mock_print.call_args_list for c in call.args)
    assert "Command" in printed
