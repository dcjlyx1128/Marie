from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

from .classifier import rule_category
from .config import default_config
from .models import Action, FileInfo

Decide = Callable[[FileInfo], Tuple[str, str]]  # 文件 -> (分类, 新文件名)

_DEFAULT_CONFIG = None


def _rule(f: FileInfo) -> Tuple[str, str]:
    global _DEFAULT_CONFIG
    if _DEFAULT_CONFIG is None:
        _DEFAULT_CONFIG = default_config()
    return rule_category(f, _DEFAULT_CONFIG) or _DEFAULT_CONFIG.fallback, f.name


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
        target = base / cat / new_name
        if target == f.path:  # 已在目标位置,跳过(幂等)
            continue
        dest = _unique(target, reserved)
        reserved.add(dest)
        actions.append(Action(f.path, dest, cat))
    return actions
