"""AI 决策缓存:按文件内容指纹缓存,持久化到 ~/.marie/cache.json。
重复文件 / 重复运行命中缓存,不再调用 API。"""
import hashlib
import json
from pathlib import Path

CACHE_FILE = Path.home() / ".marie" / "cache.json"
_BLOCK = 65536  # 大文件只取首尾块,避免全量读取


def key(path: Path) -> str:
    """内容指纹:size + 首尾块 hash(同内容文件得到同一 key)。"""
    p = Path(path)
    size = p.stat().st_size
    h = hashlib.sha256(str(size).encode())
    with p.open("rb") as f:
        h.update(f.read(_BLOCK))
        if size > _BLOCK:
            f.seek(size - _BLOCK)
            h.update(f.read(_BLOCK))
    return h.hexdigest()


def load(path: Path = None) -> dict:
    p = Path(path or CACHE_FILE)
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save(data: dict, path: Path = None) -> None:
    p = Path(path or CACHE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
