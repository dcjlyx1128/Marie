from marie.models import FileInfo
from marie.planner import plan


def _mk(tmp, name):
    p = tmp / name
    p.write_text("x")
    return FileInfo(p, 1, 0.0)


def test_plan_categorizes(tmp_path):
    files = [_mk(tmp_path, "a.jpg"), _mk(tmp_path, "b.pdf"), _mk(tmp_path, "c.zzz")]
    cats = {a.src.name: a.category for a in plan(files, tmp_path)}
    assert cats == {"a.jpg": "图片", "b.pdf": "文档", "c.zzz": "其他/待分类"}


def test_plan_dest_under_category(tmp_path):
    [action] = plan([_mk(tmp_path, "a.jpg")], tmp_path)
    assert action.dest == tmp_path / "图片" / "a.jpg"


def test_plan_skips_already_placed(tmp_path):
    # 已在目标位置的文件不再产生移动(幂等,watch 据此避免重复搬动)
    (tmp_path / "音频").mkdir()
    f = _mk(tmp_path / "音频", "song.mp3")
    assert plan([f], tmp_path, lambda _f: ("音频", "song.mp3")) == []
