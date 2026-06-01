"""提取文件文本片段,供周末2的 LLM 分类使用。重依赖按需懒加载。"""
from pathlib import Path


def snippet(path: Path, limit: int = 1000) -> str:
    ext = path.suffix.lower()
    try:
        if ext in {".txt", ".md", ".csv", ".log", ".json"}:
            return path.read_text(errors="ignore")[:limit]
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "".join(p.extract_text() or "" for p in reader.pages[:2])[:limit]
        if ext == ".docx":
            import docx
            return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)[:limit]
    except Exception:
        return ""
    return ""
