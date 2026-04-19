import pytest
from batchmark.runner import BatchResult, RunResult
from batchmark.tagger import (
    TaggedResult, TagIndex, tag_result, build_index, filter_by_tags, format_tagged
)


def make_batch(label: str) -> BatchResult:
    runs = [RunResult(exit_code=0, duration=0.1, stdout="", stderr="")]
    return BatchResult(label=label, runs=runs)


def test_tag_result_stores_tags():
    b = make_batch("cmd_a")
    tr = tag_result(b, ["fast", "linux"])
    assert "fast" in tr.tags
    assert "linux" in tr.tags


def test_tag_result_normalizes_tags():
    b = make_batch("cmd_a")
    tr = tag_result(b, [" Fast ", "LINUX"])
    assert "fast" in tr.tags
    assert "linux" in tr.tags


def test_tag_result_skips_empty_tags():
    b = make_batch("cmd_a")
    tr = tag_result(b, ["", "  ", "valid"])
    assert tr.tags == ["valid"]


def test_build_index_contains_all_entries():
    entries = [tag_result(make_batch(f"cmd_{i}"), ["t1"]) for i in range(3)]
    index = build_index(entries)
    assert len(index.entries) == 3


def test_index_all_tags_unique_sorted():
    entries = [
        tag_result(make_batch("a"), ["slow", "linux"]),
        tag_result(make_batch("b"), ["fast", "linux"]),
    ]
    index = build_index(entries)
    assert index.all_tags() == ["fast", "linux", "slow"]


def test_index_by_tag_filters_correctly():
    entries = [
        tag_result(make_batch("a"), ["fast"]),
        tag_result(make_batch("b"), ["slow"]),
    ]
    index = build_index(entries)
    result = index.by_tag("fast")
    assert len(result) == 1
    assert result[0].batch.label == "a"


def test_index_by_label():
    entries = [
        tag_result(make_batch("cmd_x"), ["t1"]),
        tag_result(make_batch("cmd_y"), ["t2"]),
    ]
    index = build_index(entries)
    result = index.by_label("cmd_x")
    assert len(result) == 1
    assert result[0].batch.label == "cmd_x"


def test_filter_by_tags_requires_all():
    entries = [
        tag_result(make_batch("a"), ["fast", "linux"]),
        tag_result(make_batch("b"), ["fast"]),
        tag_result(make_batch("c"), ["linux"]),
    ]
    index = build_index(entries)
    result = filter_by_tags(index, ["fast", "linux"])
    assert len(result) == 1
    assert result[0].batch.label == "a"


def test_format_tagged_with_tags():
    b = make_batch("my_cmd")
    tr = tag_result(b, ["fast", "ci"])
    out = format_tagged(tr)
    assert "my_cmd" in out
    assert "fast" in out
    assert "ci" in out


def test_format_tagged_no_tags():
    b = make_batch("my_cmd")
    tr = TaggedResult(batch=b, tags=[])
    out = format_tagged(tr)
    assert "(none)" in out
