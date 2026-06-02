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
    match: List[str] = field(default_factory=list)  # 文件名 glob 规则(更具体,优先于扩展名)
    ai: bool = False
    subcategories: List[str] = field(default_factory=list)


@dataclass
class Config:
    base: str = "."
    ai_fallback: bool = True
    model: str = "qwen-plus"
    vision_model: str = "qwen-vl-plus"
    base_url: str = ""  # OpenAI 兼容接口地址;留空用内置默认(可被环境变量 MARIE_BASE_URL 覆盖)
    categories: Dict[str, Category] = field(default_factory=dict)
    fallback: str = "其他/待分类"


# 内置默认配置(单一事实来源:default_config 与 init 都用它)
DEFAULT_YAML = """\
base: "."                    # 整理到哪个根目录
ai_fallback: true            # 模糊文件是否调用 AI
model: qwen-plus
vision_model: qwen-vl-plus
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1  # 任意 OpenAI 兼容接口

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
            match=list(c.get("match") or []),
            ai=bool(c.get("ai", False)),
            subcategories=list(c.get("subcategories") or []),
        )
    return Config(
        base=data.get("base", "."),
        ai_fallback=bool(data.get("ai_fallback", True)),
        model=data.get("model", "qwen-plus"),
        vision_model=data.get("vision_model", "qwen-vl-plus"),
        base_url=data.get("base_url", ""),
        categories=cats,
        fallback=data.get("fallback", "其他/待分类"),
    )


def default_config() -> Config:
    return _parse(yaml.safe_load(DEFAULT_YAML))


def load_config(start_dir: Path = Path("."), path: Path = None) -> Config:
    """加载配置。指定 path 时只读该文件;否则就近查找:本地 → 全局 → 内置默认。"""
    if path:
        return _parse(yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})
    for p in (Path(start_dir) / CONFIG_NAME, GLOBAL_CONFIG):
        if p.is_file():
            return _parse(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    return default_config()


def init_config(path: Path) -> Path:
    """写出默认 marie.yaml(不覆盖已存在文件)。"""
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_YAML, encoding="utf-8")
    return path
