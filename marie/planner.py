from pathlib import Path
from typing import List, Set

from .classifier import classify
from .models import Action, FileInfo


def _unique(dest: Path, reserved: Set[Path]) -> Path:
    """避免重名:已被占用或已预定时,追加 _1 / _2 …"""
    cand, i = dest, 1
    while cand in reserved or cand.exists():
        cand = dest.with_name(f"{dest.stem}_{i}{dest.suffix}")
        i += 1
    return cand


def plan(files: List[FileInfo], base: Path) -> List[Action]:
    """生成整理方案:每个文件 → base/分类/文件名。"""
    actions, reserved = [], set()
    for f in files:
        cat = classify(f)
        dest = _unique(base / cat / f.name, reserved)
        reserved.add(dest)
        actions.append(Action(f.path, dest, cat))
    return actions
