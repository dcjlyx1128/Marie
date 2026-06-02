from pathlib import Path

from marie.llm import _safe_name


def test_keeps_extension():
    assert _safe_name("我的发票", Path("a.pdf")) == "我的发票.pdf"


def test_strips_path_separators():
    assert "/" not in _safe_name("a/b/c", Path("x.png"))


def test_empty_falls_back_to_original():
    assert _safe_name("", Path("orig.txt")) == "orig.txt"
