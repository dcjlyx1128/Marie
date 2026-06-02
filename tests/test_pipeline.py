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


def test_ai_constrains_to_subcategory(monkeypatch):
    c = default_config()
    f = _fi("report.pdf")  # 文档,ai:true

    def fake(files, allowed, *a, **k):
        assert [x.path for x in files] == [f.path]
        assert allowed[f.path] == c.categories["文档"].subcategories  # 只允许该大类子类
        return {f.path: ("财务/发票", "发票.pdf")}

    monkeypatch.setattr("marie.llm.classify_files", fake)
    assert decide_all([f], c, use_ai=True)[f.path] == ("文档/财务/发票", "发票.pdf")


def test_ai_invalid_goes_fallback(monkeypatch):
    c = default_config()
    f = _fi("report.pdf")
    monkeypatch.setattr("marie.llm.classify_files", lambda files, allowed, *a, **k: {f.path: ("乱编的", "x.pdf")})
    assert decide_all([f], c, use_ai=True)[f.path] == (c.fallback, "report.pdf")


def test_ai_only_called_for_ambiguous(monkeypatch):
    c = default_config()
    mp4, pdf, unk = _fi("a.mp4"), _fi("doc.pdf"), _fi("x.unknown")
    seen = []

    def fake(files, allowed, *a, **k):
        seen.extend(x.path for x in files)
        return {pdf.path: ("工作", "doc.pdf")}

    monkeypatch.setattr("marie.llm.classify_files", fake)
    d = decide_all([mp4, pdf, unk], c, use_ai=True)
    assert seen == [pdf.path]                       # 仅 ai 大类文件送 AI
    assert d[mp4.path] == ("视频", "a.mp4")          # 规则确定,不调 AI
    assert d[pdf.path] == ("文档/工作", "doc.pdf")
    assert d[unk.path] == (c.fallback, "x.unknown")  # 未命中,不调 AI


def test_no_ai_keeps_category(monkeypatch):
    c = default_config()
    pdf = _fi("doc.pdf")
    monkeypatch.setattr("marie.llm.classify_files",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("不应调用 AI")))
    assert decide_all([pdf], c, use_ai=False)[pdf.path] == ("文档", "doc.pdf")  # 归大类本身


def test_ai_call_failure_goes_fallback(monkeypatch):
    c = default_config()
    pdf = _fi("doc.pdf")

    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr("marie.llm.classify_files", boom)
    assert decide_all([pdf], c, use_ai=True)[pdf.path] == (c.fallback, "doc.pdf")
