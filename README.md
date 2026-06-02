# 🧹 Marie

> 一个可靠、便宜、能自动运行的 AI 文件管家:**规则兜底保证快和省,AI 只在必要时出手**,分类稳定可预测,还能监听文件夹自动整理。

<p align="center">
  <img src="docs/demo.gif" alt="Marie 演示:乱文件夹一键整洁" width="800">
</p>

## ✨ 特性
- 🗂️ **固定分类体系(配置驱动)**:分类在 `marie.yaml` 里定义,AI 只能把文件归入预设分类,不会每次乱发明文件夹。
- ⚡ **规则优先,AI 兜底**:扩展名/文件名规则先处理显而易见的文件(零 API 成本);只有标了 `ai` 的大类才调用 LLM 细分。
- 💸 **结果缓存**:按文件内容缓存 AI 决策,重复文件 / 重复运行不再重复花钱。
- 👀 **watch 自动整理**:`marie watch <folder>` 监听文件夹,新文件到达后自动归类(防抖、忽略下载中的临时文件)。
- 🔒 **安全优先**:`organize` 默认预览(dry-run)、**只移动不删除**、保留 undo 日志一键撤销、重复运行幂等(跳过已整理目录)、AI 拿不准归入 `fallback` 绝不臆测。
- 🧠 **读内容 + 看图**:文本/文档读内容片段分类,图片用视觉模型看画面判断(截图/照片/发票…)。
- 🔌 **后端不锁定**:任意 OpenAI 兼容接口(Qwen / OpenAI / 本地 Ollama 通吃)。

## 🚀 快速开始
```bash
pip install -e .

marie init                          # 在当前目录生成 marie.yaml(可选,不生成则用内置默认分类)
marie organize ~/Downloads          # 预览整理方案(默认 dry-run,只移动不删除)
marie organize ~/Downloads --apply  # 真正执行
marie undo ~/Downloads              # 一键撤销上次整理
```

试一下(生成一个演示用的乱文件夹):
```bash
python examples/make_demo.py
marie organize examples/messy          # 纯规则:快、免费、稳定一致
```

## 👀 watch 自动整理(杀手功能)
```bash
marie watch ~/Downloads                 # 监听并整理进 ~/Downloads 内部
marie watch ~/Downloads --to ~/Archive  # 监听 ~/Downloads,但归档到 ~/Archive
```
监听文件夹,新文件稳定后自动归类。只移不删、写 undo 日志,`marie undo ~/Downloads` 可撤销(撤销始终锚定在被监听文件夹)。Ctrl-C 停止。

> **监听与归档都灵活**:监听哪个文件夹由命令行参数决定;归档到哪由 `--to`(或配置 `base`)决定,默认就地整理进原文件夹。`organize` 同样支持 `--to`。

## 🧠 AI 智能细分(可选)
仅对配置中标了 `ai: true` 的大类(如 文档、图片)中的文件才调用 LLM,细分到固定子类:
```bash
pip install -e ".[llm,extract,vision]"
export MARIE_API_KEY=sk-你的DashScope密钥

marie organize examples/messy --ai                        # 模糊文件读内容/看图,细分到固定子类
marie organize ~/Downloads --rule "发票放到 财务/发票"     # 附加自然语言规则
```
> 没设 key 也不会崩:AI 不可用时模糊文件安全落入 `fallback`(默认 `其他/待分类`)。

## ⚙️ 配置(marie.yaml)
就近查找:`./marie.yaml` → `~/.marie/config.yaml` → 内置默认。也可用 `--config <path>` 显式指定。
```yaml
base: "."
ai_fallback: true                 # 模糊文件是否调用 AI
model: qwen-plus
vision_model: qwen-vl-plus
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1   # 任意 OpenAI 兼容接口
watch_debounce: 2                 # watch:文件大小稳定几秒后处理
watch_ignore: [.crdownload, .part, .download, .tmp]

categories:
  视频:   { ext: [.mp4, .mov, .mkv] }
  音频:   { ext: [.mp3, .wav, .flac] }
  代码:   { ext: [.py, .js, .ts, .go] }
  发票:   { match: ["invoice_*", "发票*"] }   # 按文件名规则归类(无需 AI)
  图片:
    ext: [.jpg, .png, .gif, .webp]
    ai: true
    subcategories: [截图, 照片, 设计稿]
  文档:
    ext: [.pdf, .docx, .txt, .md]
    ai: true
    subcategories: [财务/发票, 工作, 学习/论文, 合同]

fallback: 其他/待分类
```
环境变量 `MARIE_API_KEY` / `MARIE_BASE_URL` / `MARIE_MODEL` / `MARIE_VISION_MODEL` 优先级高于配置文件。

## 🗺️ Roadmap
- [x] 固定分类体系(配置驱动)+ `marie init`
- [x] 规则优先 + AI 兜底(结果约束在固定子类内)
- [x] 图片多模态理解(看图分类)+ 并发处理
- [x] 结果缓存(重复文件/重复运行不重复调用)
- [x] watch 自动整理(防抖 + 忽略临时文件 + undo)
- [ ] 本地模型(Ollama)开箱即用
- [ ] 后台开机自启服务

## 📄 License
MIT
