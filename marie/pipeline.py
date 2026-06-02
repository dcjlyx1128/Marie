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


def archive_root(folder: Path, config: Config) -> Path:
    """归档根目录:config.base 为 '.' 或空时即原文件夹;否则用 base(支持 ~ 与相对 folder 的路径)。"""
    b = (config.base or ".").strip()
    if b in ("", "."):
        return Path(folder)
    p = Path(b).expanduser()
    if not p.is_absolute():
        p = Path(folder) / p
    return p.resolve()


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
        from . import cache, llm

        store = cache.load()
        keys = {}
        for f in ai_files:
            try:
                keys[f.path] = cache.key(f.path)
            except OSError:
                keys[f.path] = None  # 读不到内容则不缓存,本次照常询问
        to_ask = [f for f in ai_files if not (keys[f.path] and keys[f.path] in store)]
        fresh = {}
        if to_ask:
            allowed = {f.path: config.categories[cat_of[f.path]].subcategories for f in to_ask}
            try:
                fresh = llm.classify_files(to_ask, allowed, config.model, config.vision_model, config.base_url, rule)
            except Exception:
                fresh = {}
            wrote = False
            for f in to_ask:  # 仅缓存"模型有应答"的结果(失败/省略的留待下次重试)
                if keys[f.path] and f.path in fresh:
                    store[keys[f.path]] = list(fresh[f.path])
                    wrote = True
            if wrote:
                cache.save(store)
        for f in ai_files:
            cat, k = cat_of[f.path], keys[f.path]
            sub, new_name = store[k] if k and k in store else fresh.get(f.path, ("", f.name))
            out[f.path] = (f"{cat}/{sub}", new_name) if sub in config.categories[cat].subcategories \
                else (config.fallback, f.name)
    else:
        for f in ai_files:  # 不开 AI:归大类本身,不细分
            out[f.path] = (cat_of[f.path], f.name)
    return out
