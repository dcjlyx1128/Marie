from pathlib import Path
from typing import List, Set

from .models import FileInfo


def scan(folder: Path, recursive: bool = False, skip: Set[str] = frozenset()) -> List[FileInfo]:
    """扫描文件夹,返回文件列表(跳过隐藏文件与已整理的分类目录 skip)。"""
    it = folder.rglob("*") if recursive else folder.iterdir()
    files = []
    for p in it:
        if not p.is_file() or p.name.startswith("."):
            continue
        rel = p.relative_to(folder)
        if len(rel.parts) > 1 and rel.parts[0] in skip:  # 已整理目录,跳过(幂等)
            continue
        st = p.stat()
        files.append(FileInfo(p, st.st_size, st.st_mtime))
    return files
