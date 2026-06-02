"""规则分类:配置驱动(文件名 glob 规则 + 扩展名),代码不写死任何分类名。"""
import fnmatch
from typing import Optional

from .config import Config
from .models import FileInfo


def rule_category(f: FileInfo, config: Config) -> Optional[str]:
    """文件名规则(更具体)优先,再按扩展名命中配置大类;都未命中返回 None。"""
    name = f.name.lower()
    for cat in config.categories.values():
        if any(fnmatch.fnmatch(name, p.lower()) for p in cat.match):
            return cat.name
    for cat in config.categories.values():
        if f.ext in cat.ext:
            return cat.name
    return None


def is_ambiguous(f: FileInfo, config: Config) -> bool:
    """是否需要 AI:未命中规则,或命中的大类标了 ai(需细分子类)。"""
    cat = rule_category(f, config)
    return cat is None or config.categories[cat].ai
