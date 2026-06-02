"""决策流水线:规则优先(阶段2 起加入 AI 兜底)。产出 路径 → (分类, 新文件名)。"""
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .classifier import rule_category
from .config import Config
from .models import FileInfo


def category_dirs(config: Config) -> Set[str]:
    """所有分类(含 fallback)的顶层目录名,扫描时据此跳过已整理目录(幂等)。"""
    names = list(config.categories) + [config.fallback]
    return {Path(n).parts[0] for n in names}


def decide_all(files: List[FileInfo], config: Config, use_ai: bool = False) -> Dict[Path, Tuple[str, str]]:
    """对每个文件给出 (分类, 新文件名)。阶段1:仅规则层,未命中归 fallback,不改名。"""
    out: Dict[Path, Tuple[str, str]] = {}
    for f in files:
        cat = rule_category(f, config)
        out[f.path] = (cat or config.fallback, f.name)
    return out
