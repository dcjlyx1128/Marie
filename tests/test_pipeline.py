from pathlib import Path

from marie.classifier import is_ambiguous, rule_category
from marie.config import default_config
from marie.executor import execute
from marie.models import FileInfo
from marie.pipeline import category_dirs, decide_all
from marie.planner import plan
from marie.scanner import scan


def _fi(p):
    return FileInfo(Path(p), 1, 0.0)


def test_rule_category_by_ext():
    c = default_config()
    assert rule_category(_fi("a.mp4"), c) == "视频"
    assert rule_category(_fi("b.py"), c) == "代码"


def test_rule_category_by_filename_glob():
    c = default_config()
    c.categories["视频"].match = ["movie_*"]
    assert rule_category(_fi("movie_intro.bin"), c) == "视频"  # 文件名命中,无视扩展名


def test_rule_category_none():
    assert rule_category(_fi("x.unknown"), default_config()) is None


def test_is_ambiguous():
    c = default_config()
    assert is_ambiguous(_fi("a.jpg"), c) is True      # 图片 标 ai,需细分
    assert is_ambiguous(_fi("a.mp4"), c) is False     # 视频 规则即可确定
    assert is_ambiguous(_fi("x.unknown"), c) is True  # 未命中


def test_decide_all_rules_only():
    c = default_config()
    d = decide_all([_fi("a.mp4"), _fi("x.unknown")], c)
    assert d[Path("a.mp4")] == ("视频", "a.mp4")
    assert d[Path("x.unknown")] == (c.fallback, "x.unknown")  # 未命中归 fallback


def test_organize_idempotent(tmp_path):
    c = default_config()
    (tmp_path / "a.mp4").write_text("x")
    skip = category_dirs(c)
    files = scan(tmp_path, skip=skip)
    dec = decide_all(files, c)
    execute(plan(files, tmp_path, lambda f: dec[f.path]), tmp_path)
    assert (tmp_path / "视频" / "a.mp4").exists()
    # 第二次:已整理目录被跳过,无文件可整理
    assert scan(tmp_path, recursive=True, skip=skip) == []
