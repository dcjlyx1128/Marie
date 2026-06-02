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


def decide_all(files: List[FileInfo], config: Config, use_ai: bool = False, rule: str = "") -> Dict[Path, Tuple[str, str]]:
    """对每个文件给出 (分类, 新文件名)。
    规则命中且非 ai 大类 → 直接定;规则未命中 → fallback;
    命中 ai:true 大类 → 需细分:use_ai 时送 LLM(约束选其 subcategories,拿不准/失败归 fallback),否则归大类本身。"""
    out: Dict[Path, Tuple[str, str]] = {}
    ai_files, cat_of = [], {}
    for f in files:
        cat = rule_category(f, config)
        if cat is None:
            out[f.path] = (config.fallback, f.name)
        elif config.categories[cat].ai:
            cat_of[f.path] = cat
            ai_files.append(f)
        else:
            out[f.path] = (cat, f.name)

    if ai_files and use_ai:
        from . import llm

        allowed = {f.path: config.categories[cat_of[f.path]].subcategories for f in ai_files}
        try:
            results = llm.classify_files(ai_files, allowed, config.model, config.vision_model, config.base_url, rule)
        except Exception:
            results = {}
        for f in ai_files:
            cat = cat_of[f.path]
            sub, new_name = results.get(f.path, ("", f.name))
            out[f.path] = (f"{cat}/{sub}", new_name) if sub in config.categories[cat].subcategories \
                else (config.fallback, f.name)
    else:
        for f in ai_files:  # 不开 AI:归大类本身,不细分
            out[f.path] = (cat_of[f.path], f.name)
    return out
