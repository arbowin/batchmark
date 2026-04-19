"""Tests for batchmark.watcher."""

import os
import tempfile
import time
from unittest.mock import patch

import pytest

from batchmark.watcher import (
    WatchedFile,
    WatcherConfig,
    _file_hash,
    _init_watched,
    _changed_files,
    watch,
)


def write_file(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def test_file_hash_returns_string(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello")
    result = _file_hash(str(p))
    assert isinstance(result, str) and len(result) == 32


def test_file_hash_missing_returns_none():
    assert _file_hash("/nonexistent/path/file.txt") is None


def test_file_hash_changes_on_content_change(tmp_path):
    p = tmp_path / "b.txt"
    p.write_text("v1")
    h1 = _file_hash(str(p))
    p.write_text("v2")
    h2 = _file_hash(str(p))
    assert h1 != h2


def test_init_watched_sets_hashes(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("data")
    watched = _init_watched([str(p)])
    assert len(watched) == 1
    assert watched[0].last_hash is not None


def test_changed_files_detects_modification(tmp_path):
    p = tmp_path / "d.txt"
    p.write_text("original")
    watched = _init_watched([str(p)])
    p.write_text("modified")
    changed = _changed_files(watched)
    assert str(p) in changed


def test_changed_files_no_change(tmp_path):
    p = tmp_path / "e.txt"
    p.write_text("same")
    watched = _init_watched([str(p)])
    changed = _changed_files(watched)
    assert changed == []


def test_changed_files_updates_hash(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("v1")
    watched = _init_watched([str(p)])
    p.write_text("v2")
    _changed_files(watched)
    # second call should not report change again
    changed = _changed_files(watched)
    assert changed == []


def test_watch_triggers_callback(tmp_path):
    p = tmp_path / "g.txt"
    p.write_text("init")
    config = WatcherConfig(paths=[str(p)], interval=0.01, max_triggers=1)
    triggered = []

    def modify_and_wait():
        time.sleep(0.02)
        p.write_text("changed")

    import threading
    t = threading.Thread(target=modify_and_wait)
    t.start()

    count = watch(config, lambda files: triggered.extend(files))
    t.join()
    assert count == 1
    assert str(p) in triggered
