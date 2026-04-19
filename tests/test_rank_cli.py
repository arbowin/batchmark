import pytest
from unittest.mock import patch, MagicMock
from batchmark.rank_cli import build_rank_parser, main
from batchmark.runner import BatchResult


def make_batch(label, times):
    return BatchResult(label=label, times=times, total=len(times), successes=len(times))


def test_build_rank_parser_defaults():
    parser = build_rank_parser()
    args = parser.parse_args(["echo hello"])
    assert args.iterations == 5
    assert args.labels is None


def test_build_rank_parser_custom_iterations():
    parser = build_rank_parser()
    args = parser.parse_args(["-n", "10", "sleep 0"])
    assert args.iterations == 10


def test_build_rank_parser_labels():
    parser = build_rank_parser()
    args = parser.parse_args(["cmd1", "cmd2", "--labels", "A", "B"])
    assert args.labels == ["A", "B"]


def test_main_mismatched_labels_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["cmd1", "cmd2", "--labels", "OnlyOne"])
    assert exc.value.code == 1


def test_main_calls_benchmark_and_prints(capsys):
    batches = [
        make_batch("fast", [0.5, 0.6]),
        make_batch("slow", [2.0, 2.1]),
    ]
    with patch("batchmark.rank_cli.benchmark_command", side_effect=batches):
        main(["fast_cmd", "slow_cmd", "-n", "2"])
    captured = capsys.readouterr()
    assert "fast" in captured.out or "slow" in captured.out


def test_main_benchmark_error_exits(capsys):
    with patch("batchmark.rank_cli.benchmark_command", side_effect=RuntimeError("fail")):
        with pytest.raises(SystemExit) as exc:
            main(["bad_cmd"])
    assert exc.value.code == 1
