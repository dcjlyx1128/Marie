"""LLM 智能分类:文本/文档读内容批量分类;图片用视觉模型"看图"分类。
通过 OpenAI 兼容接口调用,默认用通义千问(DashScope)。

环境变量:
  MARIE_API_KEY       API key(DashScope 的 sk-...)            [必填]
  MARIE_BASE_URL      默认 https://dashscope.aliyuncs.com/compatible-mode/v1
  MARIE_MODEL         文本模型,默认 qwen-plus
  MARIE_VISION_MODEL  视觉模型,默认 qwen-vl-plus
"""
import base64
import io
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from .extractor import snippet
from .models import FileInfo

DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_VISION = "qwen-vl-plus"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

SYSTEM = (
    "你是文件整理助手。根据文件名和内容片段,为每个文件给出 category(简洁的中文分类"
    "文件夹名,如 财务/发票、工作、笔记)和 new_name(规范清晰的文件名,必须保留原扩展名;"
    '原名已合适则原样返回)。只输出 JSON:{"results":[{"i":0,"category":"...","new_name":"..."}]}'
)
SYSTEM_IMG = (
    "你是文件整理助手。观察这张图片的内容(如 截图、照片、发票、设计稿、表情包等),"
    "结合文件名和整理规则,返回 JSON:"
    '{"category":"中文分类文件夹名","new_name":"含义清晰的文件名(保留原扩展名)"}。只输出 JSON。'
)


def _client():
    from openai import OpenAI

    key = os.environ.get("MARIE_API_KEY")
    if not key:
        raise RuntimeError("未设置 MARIE_API_KEY,请先 export MARIE_API_KEY=你的key")
    return OpenAI(api_key=key, base_url=os.environ.get("MARIE_BASE_URL", DEFAULT_BASE))


def _chat(model: str, messages: list, json_mode: bool = True) -> dict:
    kwargs = {"model": model, "messages": messages, "temperature": 0}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    text = _client().chat.completions.create(**kwargs).choices[0].message.content
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def _safe_name(new_name: str, original: Path) -> str:
    """防止改坏:保留原扩展名、去掉路径分隔符。"""
    ext = original.suffix
    name = (new_name or original.name).strip().replace("/", "_").replace("\\", "_")
    if not name:
        name = original.name
    if not name.lower().endswith(ext.lower()):
        name = Path(name).stem + ext
    return name


def _image_b64(path: Path) -> Tuple[str, str]:
    """读图并压缩到 768px/JPEG(省 token);无 Pillow 时回退原图。"""
    raw = path.read_bytes()
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw))
        img.thumbnail((768, 768))
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode(), "jpeg"
    except Exception:
        mime = path.suffix.lower().lstrip(".").replace("jpg", "jpeg")
        return base64.b64encode(raw).decode(), mime


def _classify_text(files: List[FileInfo], rule: str) -> Dict[Path, Tuple[str, str]]:
    if not files:
        return {}
    items = [{"i": i, "name": f.name, "snippet": snippet(f.path, 500)} for i, f in enumerate(files)]
    payload = {"rule": rule or "(无特殊规则)", "files": items}
    data = _chat(
        os.environ.get("MARIE_MODEL", DEFAULT_MODEL),
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    out = {}
    for r in data.get("results", []):
        f = files[r["i"]]
        out[f.path] = (r.get("category") or "其他", _safe_name(r.get("new_name", ""), f.path))
    return out


def _classify_image(f: FileInfo, rule: str) -> Tuple[str, str]:
    b64, mime = _image_b64(f.path)
    data = _chat(
        os.environ.get("MARIE_VISION_MODEL", DEFAULT_VISION),
        [{"role": "system", "content": SYSTEM_IMG},
         {"role": "user", "content": [
             {"type": "text", "text": f"文件名:{f.name}\n整理规则:{rule or '(无)'}"},
             {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
         ]}],
        json_mode=False,
    )
    return data.get("category") or "图片", _safe_name(data.get("new_name", ""), f.path)


def classify_files(files: List[FileInfo], rule: str = "") -> Dict[Path, Tuple[str, str]]:
    images = [f for f in files if f.ext in IMAGE_EXTS]
    others = [f for f in files if f.ext not in IMAGE_EXTS]
    out = _classify_text(others, rule)
    for f in images:
        try:
            out[f.path] = _classify_image(f, rule)
        except Exception:
            pass  # 视觉失败 → CLI 中回退规则分类
    return out
