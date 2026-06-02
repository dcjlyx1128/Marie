# 🧹 Marie

> 用自然语言指挥 AI 整理任何文件夹 —— 它能读懂文件**内容**,自动分类、重命名、归档。

<!-- TODO(最重要): 在这里放一张演示 GIF,乱文件夹 → 一键整洁 -->
<!-- ![demo](docs/demo.gif) -->

## ✨ Features
- 🗂️ 一键整理凌乱的下载 / 桌面文件夹
- 🧠 读懂文件**内容**再分类(不只看扩展名) — *即将支持*
- 💬 用**自然语言**定义整理规则 — *即将支持*
- 🔒 安全优先:默认预览(dry-run)、只移动不删除、**一键撤销**
- 🏠 支持本地模型(Ollama),数据不出本机 — *即将支持*

## 🚀 Quick Start
```bash
pip install -e .

marie organize ~/Downloads          # 预览整理方案(默认 dry-run)
marie organize ~/Downloads --apply  # 真正执行
marie undo ~/Downloads              # 一键撤销上次整理
```

试一下(生成一个演示用的乱文件夹):
```bash
python examples/make_demo.py
marie organize examples/messy
```

## 🧠 AI 智能分类(读内容 + 自然语言规则)
通过 OpenAI 兼容接口调用,默认用通义千问(Qwen / DashScope):
```bash
pip install -e ".[llm,extract]"
export MARIE_API_KEY=sk-你的DashScope密钥

marie organize examples/messy --ai                       # AI 读内容分类+重命名
marie organize ~/Downloads --rule "发票放到 财务/发票,按内容重命名"   # 自然语言规则
```
也可切换其它模型(同一套接口):
```bash
export MARIE_BASE_URL=http://localhost:11434/v1   # 本地 Ollama
export MARIE_MODEL=qwen2.5                          # 或 qwen-plus / gpt-4o-mini ...
```

## 🗺️ Roadmap
- [x] 规则分类 + 预览 + 执行 + 撤销
- [x] LLM 读内容智能分类 + 自然语言规则
- [ ] 本地模型(Ollama)开箱即用
- [ ] 图片 / PDF 多模态理解
- [ ] 配置文件持久化规则

## 📄 License
MIT
