"""LLM 智能分类:对"模糊文件"细分,结果被约束在调用方给定的「允许分类」清单内。
文本/文档读内容批量分类;图片用视觉模型"看图"分类。通过 OpenAI 兼容接口调用。

环境变量(优先级高于配置文件):
  MARIE_API_KEY       API key                                   [必填]
  MARIE_BASE_URL      OpenAI 兼容接口地址(默认 DashScope)
  MARIE_MODEL         文本模型
  MARIE_VISION_MODEL  视觉模型
"""
import base64
import io
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Tuple

from .extractor import snippet
from .models import FileInfo

DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_VISION = "qwen-vl-plus"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

SYSTEM = (
    "你是文件整理助手。为每个文件从它的 allowed 候选分类中选一个最合适的:"
    'category 必须严格等于 allowed 里的某一项原文;若都不合适或无法判断,category 返回空字符串 ""。'
    "同时给出 new_name(规范清晰的文件名,必须保留原扩展名;原名已合适则原样返回)。"
    '只输出 JSON:{"results":[{"i":0,"category":"...","new_name":"..."}]}'
)
SYSTEM_IMG = (
    "你是文件整理助手。观察图片内容,从给定的 allowed 候选分类中选一个最合适的:"
    'category 必须严格等于 allowed 里的某一项原文;都不合适或无法判断则返回空字符串 ""。'
    '返回 JSON:{"category":"...","new_name":"含义清晰的文件名(保留原扩展名)"}。只输出 JSON。'
)


def _client(base_url: str = ""):
    from openai import OpenAI

    key = os.environ.get("MARIE_API_KEY")
    if not key:
        raise RuntimeError("未设置 MARIE_API_KEY,请先 export MARIE_API_KEY=你的key")
    return OpenAI(api_key=key, base_url=os.environ.get("MARIE_BASE_URL") or base_url or DEFAULT_BASE)


def _chat(model: str, messages: list, base_url: str = "", json_mode: bool = True) -> dict:
    kwargs = {"model": model, "messages": messages, "temperature": 0}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    text = _client(base_url).chat.completions.create(**kwargs).choices[0].message.content
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


def _classify_text(files, allowed, model, base_url, rule) -> Dict[Path, Tuple[str, str]]:
    if not files:
        return {}
    items = [
        {"i": i, "name": f.name, "snippet": snippet(f.path, 500), "allowed": allowed.get(f.path, [])}
        for i, f in enumerate(files)
    ]
    data = _chat(
        model,
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": json.dumps({"rule": rule or "(无)", "files": items}, ensure_ascii=False)}],
        base_url,
    )
    out = {}
    for r in data.get("results", []):
        f = files[r["i"]]
        out[f.path] = (r.get("category") or "", _safe_name(r.get("new_name", ""), f.path))
    return out


def _classify_image(f, allowed, vision_model, base_url, rule) -> Tuple[str, str]:
    b64, mime = _image_b64(f.path)
    data = _chat(
        vision_model,
        [{"role": "system", "content": SYSTEM_IMG},
         {"role": "user", "content": [
             {"type": "text", "text": f"文件名:{f.name}\nallowed:{allowed}\n整理规则:{rule or '(无)'}"},
             {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
         ]}],
        base_url,
        json_mode=False,
    )
    return data.get("category") or "", _safe_name(data.get("new_name", ""), f.path)


def classify_files(files: List[FileInfo], allowed: Dict[Path, List[str]],
                   model: str = "", vision_model: str = "", base_url: str = "",
                   rule: str = "") -> Dict[Path, Tuple[str, str]]:
    """并发分类(文本批量 + 图片并行)。返回 路径 → (所选分类, 新文件名);
    分类为 allowed 中某项,或空字符串(模型拿不准)。单个失败则该文件省略,由调用方兜底。"""
    model = os.environ.get("MARIE_MODEL") or model or DEFAULT_MODEL
    vision_model = os.environ.get("MARIE_VISION_MODEL") or vision_model or DEFAULT_VISION
    images = [f for f in files if f.ext in IMAGE_EXTS]
    others = [f for f in files if f.ext not in IMAGE_EXTS]
    out: Dict[Path, Tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        text_fut = ex.submit(_classify_text, others, allowed, model, base_url, rule) if others else None
        img_futs = {ex.submit(_classify_image, f, allowed.get(f.path, []), vision_model, base_url, rule): f
                    for f in images}
        if text_fut:
            try:
                out.update(text_fut.result())
            except Exception as e:
                print(f"[文本分类失败] {e}", file=sys.stderr)
        for fut, f in img_futs.items():
            try:
                out[f.path] = fut.result()
            except Exception as e:
                print(f"[图片分类失败] {f.name}: {e}", file=sys.stderr)
    return out
