from pathlib import Path

import pytest

import marie.cache as cache
from marie.config import default_config
from marie.executor import undo
from marie.watcher import _ignored, handle


@pytest.fixture(autouse=True)
def _isolate_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_FILE", tmp_path / "cache.json")


def test_handle_moves_file(tmp_path):
    c = default_config()
    p = tmp_path / "song.mp3"
    p.write_text("x")
    dest = handle(p, tmp_path, c)
    assert dest == tmp_path / "音频" / "song.mp3"
    assert dest.exists() and not p.exists()


def test_handle_appends_undo_log(tmp_path):
    c = default_config()
    (tmp_path / "a.mp3").write_text("x")
    (tmp_path / "b.mp4").write_text("x")
    handle(tmp_path / "a.mp3", tmp_path, c)
    handle(tmp_path / "b.mp4", tmp_path, c)
    assert undo(tmp_path) == 2  # 两次处理都进了同一份 undo 日志
    assert (tmp_path / "a.mp3").exists() and (tmp_path / "b.mp4").exists()


def test_ignores_temp_and_hidden():
    c = default_config()
    assert _ignored(Path("download.crdownload"), c)
    assert _ignored(Path("chunk.part"), c)
    assert _ignored(Path(".hidden"), c)
    assert not _ignored(Path("song.mp3"), c)
