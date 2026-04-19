import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.labeler import (
    LabelRule,
    apply_rules,
    group_by_auto_label,
    format_labeled,
)


def make_batch(label: str) -> BatchResult:
    runs = [RunResult(elapsed=0.1, returncode=0, stdout="", stderr="")]
    return BatchResult(label=label, runs=runs)


RULES = [
    LabelRule(pattern=r"python", label="python"),
    LabelRule(pattern=r"node|npm", label="node"),
    LabelRule(pattern=r"curl", label="network"),
]


def test_apply_rules_matches_python():
    batches = [make_batch("python script.py")]
    result = apply_rules(batches, RULES)
    assert result[0].auto_label == "python"


def test_apply_rules_matches_node():
    batches = [make_batch("node server.js")]
    result = apply_rules(batches, RULES)
    assert result[0].auto_label == "node"


def test_apply_rules_no_match_returns_none():
    batches = [make_batch("ls -la")]
    result = apply_rules(batches, RULES)
    assert result[0].auto_label is None


def test_apply_rules_first_match_wins():
    batches = [make_batch("python curl_test.py")]
    result = apply_rules(batches, RULES)
    assert result[0].auto_label == "python"


def test_apply_rules_preserves_batch():
    batch = make_batch("curl http://example.com")
    result = apply_rules([batch], RULES)
    assert result[0].batch is batch


def test_group_by_auto_label_groups_correctly():
    batches = [make_batch("python a.py"), make_batch("python b.py"), make_batch("node app.js")]
    labeled = apply_rules(batches, RULES)
    groups = group_by_auto_label(labeled)
    assert len(groups["python"]) == 2
    assert len(groups["node"]) == 1


def test_group_by_auto_label_unlabeled_key():
    batches = [make_batch("ls -la")]
    labeled = apply_rules(batches, RULES)
    groups = group_by_auto_label(labeled)
    assert "__unlabeled__" in groups


def test_format_labeled_contains_label():
    batches = [make_batch("python run.py")]
    labeled = apply_rules(batches, RULES)
    output = format_labeled(labeled)
    assert "python run.py" in output
    assert "python" in output


def test_format_labeled_none_shown_as_none():
    batches = [make_batch("ls")]
    labeled = apply_rules(batches, RULES)
    output = format_labeled(labeled)
    assert "(none)" in output
