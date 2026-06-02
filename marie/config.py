"""配置:固定分类体系(配置驱动)。

就近查找:./marie.yaml → ~/.marie/config.yaml → 内置默认。
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

import yaml

CONFIG_NAME = "marie.yaml"
GLOBAL_CONFIG = Path.home() / ".marie" / "config.yaml"


@dataclass
class Category:
    name: str
    ext: Set[str] = field(default_factory=set)
    ai: bool = False
    subcategories: List[str] = field(default_factory=list)


@dataclass
class Config:
    base: str = "."
    ai_fallback: bool = True
    model: str = "qwen-plus"
    vision_model: str = "qwen-vl-plus"
    categories: Dict[str, Category] = field(default_factory=dict)
    fallback: str = "其他/待分类"


# 内置默认配置(单一事实来源:default_config 与 init 都用它)
DEFAULT_YAML = """\
base: "."                    # 整理到哪个根目录
ai_fallback: true            # 模糊文件是否调用 AI
model: qwen-plus
vision_model: qwen-vl-plus

categories:
  视频:   { ext: [.mp4, .mov, .mkv] }
  音频:   { ext: [.mp3, .wav, .flac] }
  安装包: { ext: [.dmg, .pkg, .exe] }
  压缩包: { ext: [.zip, .rar, .7z] }
  代码:   { ext: [.py, .js, .ts, .go] }
  图片:
    ext: [.jpg, .png, .gif, .webp]
    ai: true
    subcategories: [截图, 照片, 设计稿]
  文档:
    ext: [.pdf, .docx, .txt, .md]
    ai: true
    subcategories: [财务/发票, 工作, 学习/论文, 合同]

fallback: 其他/待分类
"""


def _parse(data: dict) -> Config:
    cats = {}
    for name, c in (data.get("categories") or {}).items():
        c = c or {}
        cats[name] = Category(
            name=name,
            ext={e.lower() for e in (c.get("ext") or [])},
            ai=bool(c.get("ai", False)),
            subcategories=list(c.get("subcategories") or []),
        )
    return Config(
        base=data.get("base", "."),
        ai_fallback=bool(data.get("ai_fallback", True)),
        model=data.get("model", "qwen-plus"),
        vision_model=data.get("vision_model", "qwen-vl-plus"),
        categories=cats,
        fallback=data.get("fallback", "其他/待分类"),
    )


def default_config() -> Config:
    return _parse(yaml.safe_load(DEFAULT_YAML))


def load_config(start_dir: Path = Path(".")) -> Config:
    """就近查找配置:本地 ./marie.yaml 优先,其次全局,最后内置默认。"""
    for path in (Path(start_dir) / CONFIG_NAME, GLOBAL_CONFIG):
        if path.is_file():
            return _parse(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return default_config()


def init_config(path: Path) -> Path:
    """写出默认 marie.yaml(不覆盖已存在文件)。"""
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_YAML, encoding="utf-8")
    return path
