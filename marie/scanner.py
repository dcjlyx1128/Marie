from pathlib import Path
from typing import List

from .models import FileInfo


def scan(folder: Path, recursive: bool = False) -> List[FileInfo]:
    """扫描文件夹,返回文件列表(跳过隐藏文件)。"""
    it = folder.rglob("*") if recursive else folder.iterdir()
    files = []
    for p in it:
        if p.is_file() and not p.name.startswith("."):
            st = p.stat()
            files.append(FileInfo(p, st.st_size, st.st_mtime))
    return files
