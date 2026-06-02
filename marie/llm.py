"""LLM 智能分类:读文件名 + 内容片段,返回分类和建议文件名。
通过 OpenAI 兼容接口调用,默认用通义千问(DashScope)。

环境变量:
  MARIE_API_KEY   API key(DashScope 的 sk-...)            [必填]
  MARIE_BASE_URL  默认 https://dashscope.aliyuncs.com/compatible-mode/v1
  MARIE_MODEL     默认 qwen-plus
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from .extractor import snippet
from .models import FileInfo

DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"

SYSTEM = (
    "你是文件整理助手。根据文件名和内容片段,为每个文件给出 category(简洁的中文分类"
    "文件夹名,如 财务/发票、工作、图片、安装包)和 new_name(规范清晰的文件名,必须"
    "保留原扩展名;原名已合适则原样返回)。"
    '只输出 JSON,格式:{"results":[{"i":0,"category":"...","new_name":"..."}]}'
)


def _client():
    from openai import OpenAI

    key = os.environ.get("MARIE_API_KEY")
    if not key:
        raise RuntimeError("未设置 MARIE_API_KEY,请先 export MARIE_API_KEY=你的key")
    return OpenAI(api_key=key, base_url=os.environ.get("MARIE_BASE_URL", DEFAULT_BASE))


def _safe_name(new_name: str, original: Path) -> str:
    """防止改坏:保留原扩展名、去掉路径分隔符。"""
    ext = original.suffix
    name = (new_name or original.name).strip().replace("/", "_").replace("\\", "_")
    if not name:
        name = original.name
    if not name.lower().endswith(ext.lower()):
        name = Path(name).stem + ext
    return name


def classify_files(files: List[FileInfo], rule: str = "") -> Dict[Path, Tuple[str, str]]:
    items = [{"i": i, "name": f.name, "snippet": snippet(f.path, 500)} for i, f in enumerate(files)]
    payload = {"rule": rule or "(无特殊规则)", "files": items}
    resp = _client().chat.completions.create(
        model=os.environ.get("MARIE_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    text = resp.choices[0].message.content
    match = re.search(r"\{.*\}", text, re.S)
    results = json.loads(match.group(0) if match else text).get("results", [])
    out: Dict[Path, Tuple[str, str]] = {}
    for r in results:
        f = files[r["i"]]
        out[f.path] = (r.get("category") or "其他", _safe_name(r.get("new_name", ""), f.path))
    return out
