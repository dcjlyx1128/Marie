# Marie 任务清单(Tasks)

按阶段推进,每个阶段独立可测、可提交(git commit)。勾选完成项。

## 阶段 0 — 配置基础(对应 R1)
- [ ] 0.1 新增依赖 `pyyaml`(pyproject 的 base 依赖)
- [ ] 0.2 `config.py`:`Category` / `Config` 数据类
- [ ] 0.3 `default_config()` 内置默认分类(同 requirements 示例)
- [ ] 0.4 `load_config()`:就近查找 `./marie.yaml` → `~/.marie/config.yaml` → 默认
- [ ] 0.5 `marie init` 命令:生成默认 `marie.yaml`
- [ ] 0.6 测试:配置加载 + 就近优先 + init 生成
- [ ] ✅ 验收:`marie init` 生成配置,可被读取;提交

## 阶段 1 — 规则优先引擎(对应 R2 前半 + R5 幂等)
- [ ] 1.1 `classifier.rule_category(file, config)`:ext → 大类
- [ ] 1.2 `classifier.is_ambiguous(file, config)`:是否需要 AI
- [ ] 1.3 `pipeline.decide_all(...)`:规则层先行,产出 `(category, new_name)`
- [ ] 1.4 scanner/planner:扫描时跳过已存在的分类目录(幂等)
- [ ] 1.5 `organize` 接入 config + pipeline(暂不调 AI)
- [ ] 1.6 测试:规则分类稳定、幂等(重复运行无重复移动)
- [ ] ✅ 验收:不开 AI 也能稳定、免费、一致整理;提交

## 阶段 2 — AI 兜底(对应 R2 后半 + R1 约束)
- [ ] 2.1 `llm` prompt 改造:传入允许分类清单,只能选其一,否则 `fallback`
- [ ] 2.2 pipeline:仅模糊文件送 AI(文本批量 + 图片并发)
- [ ] 2.3 拿不准 / 调用失败 → 归 `fallback`
- [ ] 2.4 测试:AI 结果落在固定子类内;只对模糊文件调用
- [ ] ✅ 验收:`--ai` 仅处理模糊文件且结果受约束;提交

## 阶段 3 — 结果缓存(对应 R3)
- [ ] 3.1 `cache.py`:基于内容 hash 的 key + JSON 读写(`~/.marie/cache.json`)
- [ ] 3.2 pipeline 调 AI 前查缓存、后写缓存
- [ ] 3.3 测试:连续运行两次,第二次 AI 调用为 0
- [ ] ✅ 验收:重复文件/重复运行不再调用 API;提交

## 阶段 4 — watch 自动整理(对应 R4)
- [ ] 4.1 新增依赖 `watchdog`
- [ ] 4.2 `watcher.py`:监听 on_created/on_moved + 防抖 + 忽略临时文件
- [ ] 4.3 稳定文件 → pipeline → 执行 + undo 日志 + 控制台日志
- [ ] 4.4 `marie watch <folder>` 命令
- [ ] 4.5 测试:临时目录新建文件 → 被移动到正确分类
- [ ] ✅ 验收:拖文件进受监听文件夹,数秒内自动归类;提交

## 阶段 5 — 打磨与发布(对应 R5 + 发布)
- [ ] 5.1 更新 README(新功能、配置说明、watch 用法)
- [ ] 5.2 录制 watch 模式新演示 GIF
- [ ] 5.3 跑通全部测试 + CI 绿
- [ ] 5.4 提交并推送 GitHub
- [ ] ✅ 验收:仓库展示完整"真工具"形态

## 备注
- 每阶段结束:跑 `pytest`,确认无回归,再 `git commit`。
- 安全红线:只移不删、默认预览、保留 undo、幂等跳过已整理目录。
- 推送走代理:`git push`(全局已配 7892);若卡用 `git -c http.proxy= -c https.proxy= push`。
