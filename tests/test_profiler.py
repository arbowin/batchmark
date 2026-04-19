"""Tests for batchmark.profiler module."""

import pytest
from unittest.mock import patch, MagicMock
from batchmark.profiler import (
    ProfileSample,
    ProfileResult,
    profile_command,
    format_profile,
)


def make_sample(memory_kb=1024, cpu_user=0.1, cpu_sys=0.05, elapsed=0.2):
    return ProfileSample(
        elapsed=elapsed,
        peak_memory_kb=memory_kb,
        cpu_user=cpu_user,
        cpu_sys=cpu_sys,
    )


def test_profile_result_avg_memory():
    r = ProfileResult(label="test", samples=[make_sample(1000), make_sample(2000)])
    assert r.avg_memory_kb() == 1500.0


def test_profile_result_avg_cpu_user():
    r = ProfileResult(label="test", samples=[make_sample(cpu_user=0.2), make_sample(cpu_user=0.4)])
    assert abs(r.avg_cpu_user() - 0.3) < 1e-9


def test_profile_result_avg_cpu_sys():
    r = ProfileResult(label="test", samples=[make_sample(cpu_sys=0.1), make_sample(cpu_sys=0.3)])
    assert abs(r.avg_cpu_sys() - 0.2) < 1e-9


def test_profile_result_empty():
    r = ProfileResult(label="empty")
    assert r.avg_memory_kb() == 0.0
    assert r.avg_cpu_user() == 0.0
    assert r.avg_cpu_sys() == 0.0


def test_profile_result_summary_keys():
    r = ProfileResult(label="cmd", samples=[make_sample()])
    s = r.summary()
    assert "label" in s
    assert "samples" in s
    assert "avg_memory_kb" in s
    assert "avg_cpu_user" in s
    assert "avg_cpu_sys" in s


def test_profile_result_summary_label():
    r = ProfileResult(label="myjob", samples=[make_sample()])
    assert r.summary()["label"] == "myjob"


def test_profile_command_returns_profile_result():
    with patch("batchmark.profiler.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = profile_command("echo", "echo hello", iterations=3)
    assert result.label == "echo"
    assert len(result.samples) == 3


def test_profile_command_sample_fields():
    with patch("batchmark.profiler.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = profile_command("test", "true", iterations=1)
    s = result.samples[0]
    assert s.elapsed >= 0
    assert s.peak_memory_kb >= 0
    assert s.cpu_user >= 0
    assert s.cpu_sys >= 0


def test_format_profile_contains_label():
    r = ProfileResult(label="mytask", samples=[make_sample()])
    output = format_profile(r)
    assert "mytask" in output


def test_format_profile_contains_memory():
    r = ProfileResult(label="x", samples=[make_sample(memory_kb=2048)])
    output = format_profile(r)
    assert "KB" in output
