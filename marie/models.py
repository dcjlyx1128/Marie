from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileInfo:
    path: Path
    size: int
    mtime: float

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def ext(self) -> str:
        return self.path.suffix.lower()


@dataclass
class Action:
    src: Path
    dest: Path
    category: str
