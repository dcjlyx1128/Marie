import json
import shutil
from pathlib import Path
from typing import List

from .models import Action

JOURNAL = ".marie_undo.json"


def execute(actions: List[Action], base: Path, append: bool = False) -> int:
    """执行移动,并写入撤销日志(只移动,绝不删除)。append=True 时追加到已有日志(watch 用)。"""
    j = base / JOURNAL
    moved = json.loads(j.read_text()) if append and j.exists() else []
    n0 = len(moved)
    for a in actions:
        a.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(a.src), str(a.dest))
        moved.append({"src": str(a.src), "dest": str(a.dest)})
    j.write_text(json.dumps(moved, ensure_ascii=False, indent=2))
    return len(moved) - n0


def undo(base: Path) -> int:
    """根据日志把文件移回原位,并清理因此变空的分类目录(只删空目录,绝不碰文件)。"""
    base = Path(base)
    j = base / JOURNAL
    if not j.exists():
        return 0
    moves = json.loads(j.read_text())
    for m in reversed(moves):
        src, dest = Path(m["src"]), Path(m["dest"])
        if dest.exists():
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest), str(src))
    j.unlink()
    for m in moves:  # 自底向上删空目录,遇到非空即停
        d = Path(m["dest"]).parent
        while d != base and base in d.parents:
            try:
                d.rmdir()
            except OSError:
                break
            d = d.parent
    return len(moves)
