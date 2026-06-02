import marie.config as cfg
from marie.config import Config, default_config, init_config, load_config


def test_default_config_has_categories():
    c = default_config()
    assert isinstance(c, Config)
    assert c.categories["图片"].ai is True
    assert ".jpg" in c.categories["图片"].ext
    assert "财务/发票" in c.categories["文档"].subcategories
    assert c.fallback == "其他/待分类"


def test_load_config_prefers_local(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "GLOBAL_CONFIG", tmp_path / "no_global.yaml")
    (tmp_path / "marie.yaml").write_text("categories:\n  自定义:\n    ext: [.foo]\n", encoding="utf-8")
    c = load_config(tmp_path)
    assert set(c.categories) == {"自定义"}
    assert ".foo" in c.categories["自定义"].ext


def test_load_config_falls_back_to_default(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "GLOBAL_CONFIG", tmp_path / "no_global.yaml")
    c = load_config(tmp_path / "empty")
    assert "图片" in c.categories


def test_init_config_generates_loadable_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "GLOBAL_CONFIG", tmp_path / "no_global.yaml")
    init_config(tmp_path / "marie.yaml")
    assert (tmp_path / "marie.yaml").exists()
    assert "文档" in load_config(tmp_path).categories
