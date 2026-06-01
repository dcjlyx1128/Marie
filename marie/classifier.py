"""分类器。MVP 用扩展名规则;周末2 将替换为 LLM 读内容分类。"""
from .models import FileInfo

RULES = {
    "图片": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".svg"},
    "文档": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages"},
    "表格": {".xls", ".xlsx", ".csv", ".numbers"},
    "幻灯片": {".ppt", ".pptx", ".key"},
    "压缩包": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "音频": {".mp3", ".wav", ".flac", ".m4a", ".aac"},
    "视频": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "安装包": {".dmg", ".pkg", ".exe", ".msi", ".deb", ".apk"},
    "代码": {".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".sh", ".json"},
}


def classify(f: FileInfo) -> str:
    for cat, exts in RULES.items():
        if f.ext in exts:
            return cat
    return "其他"
