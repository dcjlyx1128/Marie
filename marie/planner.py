from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

from .classifier import classify
from .models import Action, FileInfo

Decide = Callable[[FileInfo], Tuple[str, str]]  # 文件 -> (分类, 新文件名)


def _rule(f: FileInfo) -> Tuple[str, str]:
    return classify(f), f.name


def _unique(dest: Path, reserved: Set[Path]) -> Path:
    """避免重名:已被占用或已预定时,追加 _1 / _2 …"""
    cand, i = dest, 1
    while cand in reserved or cand.exists():
        cand = dest.with_name(f"{dest.stem}_{i}{dest.suffix}")
        i += 1
    return cand


def plan(files: List[FileInfo], base: Path, decide: Optional[Decide] = None) -> List[Action]:
    """生成整理方案:每个文件 → base/分类/文件名。decide 缺省用扩展名规则。"""
    decide = decide or _rule
    actions, reserved = [], set()
    for f in files:
        cat, new_name = decide(f)
        dest = _unique(base / cat / new_name, reserved)
        reserved.add(dest)
        actions.append(Action(f.path, dest, cat))
    return actions
