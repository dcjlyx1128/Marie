"""提取文件文本片段,供 LLM 分类使用。重依赖按需懒加载,解析失败返回空串。"""
import logging
import warnings
from pathlib import Path

logging.getLogger("pypdf").setLevel(logging.ERROR)  # 静音损坏PDF的警告


def snippet(path: Path, limit: int = 1000) -> str:
    ext = path.suffix.lower()
    try:
        if ext in {".txt", ".md", ".csv", ".log", ".json"}:
            return path.read_text(errors="ignore")[:limit]
        if ext == ".pdf":
            from pypdf import PdfReader

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                reader = PdfReader(str(path))
                return "".join(p.extract_text() or "" for p in reader.pages[:2])[:limit]
        if ext == ".docx":
            import docx

            return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)[:limit]
    except Exception:
        return ""
    return ""
