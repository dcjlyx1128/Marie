# Marie 设计文档(Design)

## 总体架构
分类流程重构为一条清晰的流水线,职责分离:

```
扫描(scanner) → 决策流水线(classify pipeline) → 方案(planner) → 执行/撤销(executor)
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
   规则层(rules)   →  模糊判定        →  AI 层(llm,带缓存)
   ext→大类,免费     标 ai:true 的大类     仅模糊文件,约束进固定子类
```

核心原则:**规则优先、AI 兜底、结果约束在固定分类体系内、可缓存、可撤销。**

## 模块设计

### config.py(新)
- `Config` 数据类:`base`、`ai_fallback`、`model`、`vision_model`、`categories`(dict)、`fallback`。
- `Category`:`name`、`ext: set[str]`、`ai: bool`、`subcategories: list[str]`。
- `load_config(start_dir) -> Config`:就近查找 `./marie.yaml` → `~/.marie/config.yaml` → 内置默认。
- `default_config()`:返回内置默认配置(等同 requirements 示例)。
- `init_config(path)`:写出默认 `marie.yaml`。

### classifier.py(重构)
- `rule_category(file, config) -> str | None`:按 ext 命中配置大类,返回大类名;未命中返回 None。
- `is_ambiguous(file, config) -> bool`:命中的大类是否标了 `ai: true`(需要细分),或未命中(需 AI/兜底)。
- 输出统一为 `(category, new_name)`,category 必须属于配置体系或 `fallback`。

### pipeline.py(新,编排决策)
- `decide_all(files, config, use_ai) -> dict[path -> (category, new_name)]`:
  1. 对每个文件先走规则层 → 能定的直接定(大类,不改名)。
  2. 收集"模糊文件"(`ai:true` 大类 / 未命中)。
  3. 若 `use_ai`:先查缓存;未命中的批量送 LLM(文本批量 + 图片并发),**约束 prompt 只能从该大类的 subcategories 选**,拿不准 → `fallback`;写回缓存。
  4. 若不开 AI:模糊文件归入其大类本身或 `fallback`。

### llm.py(改造)
- prompt 增加约束:传入**允许的分类清单**,要求模型只能从中选择,否则返回 `fallback`。
- 复用现有 文本批量 / 视觉并发 / `_safe_name` / 图片压缩。
- 解耦"调用模型"与"决定调不调"(后者交给 pipeline)。

### cache.py(新)
- `key(path)`:基于内容 hash(大文件可取 size+mtime+首尾块 hash,避免全量读取)。
- `get(key)` / `set(key, value)`:读写 `~/.marie/cache.json`。
- pipeline 在调用 AI 前后读写缓存。

### watcher.py(新)
- `watch(folder, config)`:用 `watchdog` 监听 `on_created` / `on_moved`。
- 防抖:文件出现后等待其大小**连续 N 秒不变**再处理(规避下载中)。
- 忽略临时后缀:`.crdownload`、`.part`、`.download`、`.tmp`、以 `.` 开头。
- 稳定后:走 `decide_all`(单文件)→ plan → execute(自动 apply)→ 写 undo 日志 + 控制台日志。

### planner.py / executor.py(基本不变)
- planner 继续接收 `decide` 回调,产出 `Action`,处理重名。
- 扫描时**跳过配置中已存在的分类目录**,保证幂等(R5)。

### cli.py(扩展命令)
- `marie init`:生成默认配置。
- `marie organize <folder> [--apply] [--ai] [--rule TEXT]`:沿用,内部改走 pipeline + config。
- `marie watch <folder>`:启动监听(自动 apply + undo 日志)。
- `marie undo <folder>`:不变。

## 关键决策点
- **一致性**:AI 输出被 schema 约束在固定 subcategories,从根本上解决"每次分类不同"。
- **成本**:规则层拦截大多数文件;AI 仅处理模糊文件且带缓存。
- **安全**:organize 默认预览;watch 自动执行但只移不删 + undo;幂等跳过已整理目录。
- **失败兜底**:AI 调用失败 / 拿不准 → 归 `fallback`,绝不丢文件。

## 依赖新增
- `pyyaml`(配置解析)
- `watchdog`(文件监听)

## 测试策略
- 单元:配置加载与就近查找、规则分类、模糊判定、缓存读写、_safe_name(已存在)。
- 集成:给定一个混合文件夹,验证"规则命中的不调 AI""模糊文件落在固定子类""重复运行 AI 次数为 0""undo 还原"。
- watch:用临时目录创建文件,断言被移动到正确分类。
