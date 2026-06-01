import json
import shutil
from pathlib import Path
from typing import List

from .models import Action

JOURNAL = ".marie_undo.json"


def execute(actions: List[Action], base: Path) -> int:
    """执行移动,并写入撤销日志(只移动,绝不删除)。"""
    moved = []
    for a in actions:
        a.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(a.src), str(a.dest))
        moved.append({"src": str(a.src), "dest": str(a.dest)})
    (base / JOURNAL).write_text(json.dumps(moved, ensure_ascii=False, indent=2))
    return len(moved)


def undo(base: Path) -> int:
    """根据日志把文件移回原位。"""
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
    return len(moves)
