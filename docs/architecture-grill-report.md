# 架构设计质询报告

> 质询方法：Grill Me Skill  
> 输入文档：`docs/system-architecture.md` + `docs/architecture.md`  
> 质询时间：2026-06-06  
> 质询重点：可扩展性、性能、安全性、边界条件

---

## 一、质询发现的问题

### 问题 1：Pipeline 缺乏取消检查点（性能/用户体验）

**描述**：`system-architecture.md` 第 4.2 节的 Pipeline 执行流程中，没有显示定义"取消检查点"。如果用户输入 50 万字小说，Pipeline 全程无中断能力，用户只能杀进程。

**风险等级**：高

**建议修改**：
- 在 `Pipeline.run()` 的每个 Step 开始前增加 `if self._cancel_requested: raise PipelineCancelledError()` 检查
- 在 `text_segmenter` 的每个分段处理前增加取消检查
- SSE 推送 `task_cancelled` 事件

**修改位置**：`docs/system-architecture.md` 第 4.2 节 Pipeline 执行流程；`docs/architecture.md` 第 4.1 节

---

### 问题 2：Skill 沙箱隔离不足（安全性）

**描述**：`system-architecture.md` 第 8.4 节提到 Skill 错误隔离，但仅捕获异常不让其传播。恶意 Skill 可以：
1. 读取 `~/.novel2script/config.json` 获取 API Key（明文或加密但密钥在同机）
2. 访问文件系统任意路径
3. 发起网络请求泄露数据

**风险等级**：中高（V1 是本地工具，风险相对可控；V2 若引入在线 Skill 则风险极高）

**建议修改**：
- V1：在 `SkillManager.execute_safe()` 中增加可选的资源限制（执行超时、文件访问白名单）
- V2：引入 `restrictedpython` 或 `subprocess` 沙箱执行用户 Skill
- 在 `skill.json` 中增加 `permissions` 字段（类比 VS Code 插件权限声明）

**修改位置**：`docs/system-architecture.md` 第 8.4 节；`docs/architecture.md` 第 7.13 节扩展点

---

### 问题 3：配置层级中"运行时参数"优先级高于"项目配置快照"不合理（逻辑错误）

**描述**：`system-architecture.md` 第 9.1 节配置层级中，优先级顺序是：
```
默认值 → 全局配置 → 项目配置快照 → 环境变量 → 运行时参数
```
但 `architecture.md` 第 8.1 节也是这样写的。**项目配置快照应该拥有最高优先级之一**，因为它记录了项目创建时的确切配置，确保复现性。如果环境变量能覆盖项目快照，那么项目快照就失去了意义。

**风险等级**：中

**建议修改**：重新定义优先级：
```
默认值 → 全局配置 → 环境变量 → 项目配置快照 → 运行时参数
```
项目快照应介于环境变量和运行时参数之间：它应该能被运行时参数覆盖（用户主动修改），但不应该被环境变量静默覆盖。

**修改位置**：`docs/system-architecture.md` 第 9.1 节；`docs/architecture.md` 第 8.1 节

---

### 问题 4：分段合并时角色别名合并算法过于简单（准确性）

**描述**：`architecture.md` 第 4.3 节使用 `difflib.get_close_matches` 做字符串相似度匹配来合并角色别名。这个方法的问题：
1. 中文人名相似度计算不准确（"李明"和"李明辉"会被误判为同一人）
2. 没有利用 LLM 已经输出的 `CharacterRegistry` 中的 `aliases` 字段
3. 阈值 `0.8` 是硬编码，没有配置入口

**风险等级**：中（会影响转换准确率）

**建议修改**：
- 优先使用 LLM 输出的 `aliases` 字段做精确匹配合并
-  fallback 到字符串相似度时，对中文人名使用专门的分词+姓氏比较
- 将阈值放入 `AppConfig` 可配置

**修改位置**：`docs/architecture.md` 第 4.3 节 `merge_characters()` 函数

---

### 问题 5：PyWebView 回退机制中 `uvicorn.run` 会阻塞主线程（正确性）

**描述**：`system-architecture.md` 第 3.2 节回退机制中，如果 PyWebView 未安装，代码直接调用 `uvicorn.run()`，这会阻塞当前线程。但在 CLI 模式（`novel2script serve`）中，这是正确的；在 `start_gui()` 中回退时，应该将 `uvicorn.run()` 放在后台线程（就像正常 PyWebView 模式那样）。

**风险等级**：高（回退路径有 Bug）

**建议修改**：回退路径复用与 PyWebView 模式相同的服务器启动逻辑：
```python
# start_gui() 回退路径
self.server_thread = threading.Thread(target=self._run_server, daemon=True)
self.server_thread.start()
webbrowser.open(f"http://{host}:{port}")
# 主线程等待（或监听退出信号）
```

**修改位置**：`docs/system-architecture.md` 第 3.2 节；`docs/architecture.md` 第 3.1 节

---

### 问题 6：SSE 连接在 Pipeline 长时间运行时可能中断（可靠性）

**描述**：SSE 连接默认有超时（许多 HTTP 客户端/代理默认 30-120 秒无数据就断开）。如果某个 Step（如 `dialogue_parser` 处理 50 个场景）耗时超过 30 秒，SSE 连接可能中断，前端丢失进度更新。

**风险等级**：中高

**建议修改**：
- 在 SSE 流中定期发送心跳事件（如每 15 秒发送 `{"event": "heartbeat"}`）
- 前端实现自动重连逻辑
- 在 `sse.py` 中增加 `keep_alive()` 协程

**修改位置**：`docs/system-architecture.md` 附录 C；`docs/architecture.md` 第 3.7 节

---

### 问题 7：版本历史清理策略可能导致磁盘空间耗尽（边界条件）

**描述**：`architecture.md` 第 6.4 节中 `MAX_VERSIONS = 10`，但每次 `save_script()` 都会生成一个版本快照。如果用户开启自动保存（每 2 秒防抖），短时间内可能产生大量版本。虽然最多保留 10 个，但每个版本是一个完整 YAML 文件（可能几 MB），10 个版本就是几十 MB，多个项目累计可能 GB 级。

**风险等级**：低中（V1 影响不大，V2 批量使用时需关注）

**建议修改**：
- 在 `save_script()` 中增加版本生成频率限制（如至少间隔 5 分钟才生成新版本）
- 增加版本总大小限制配置
- 在 `meta.json` 中记录版本总大小

**修改位置**：`docs/architecture.md` 第 6.4 节 `save_script()` 方法

---

### 问题 8：`source_location` 在小说原文编辑后会失效（核心功能缺陷）

**描述**：滚动联动功能依赖 `source_location: { chapter, start, end }` 来定位小说原文位置。但如果用户在左侧编辑器修改了小说原文（增删文字），所有 `source_location.end` 和 `source_location.start` 都会偏移，导致滚动联动功能失效甚至定位到错误位置。

**风险等级**：高（核心交互功能在编辑后会损坏）

**建议修改**：
- 方案 A（推荐）：不存储绝对位置，存储"章节 + 上下文锚点（前后各 N 个字）"，联动时做模糊匹配定位
- 方案 B：在小说原文保存时，同步更新所有 `source_location`（需要遍历所有 Beat，调用 LLM 重新定位，成本高）
- 方案 C（V2）：在 YAML 编辑器中禁止直接编辑小说原文，只通过"同步编辑"模式修改（原文和剧本联动编辑）

**修改位置**：`docs/system-architecture.md` 第 6.3 节；`docs/architecture.md` 第 5.3 节

---

### 问题 9：LLM 输出格式错误的自动修复策略不够具体（可靠性）

**描述**：`system-architecture.md` 第 10.1 节提到"自动修复 → 降级重试 → 标记 `[PARSE_ERROR]`"，但没有定义"自动修复"的具体策略。什么情况下可以自动修复？修复规则是什么？

**风险等级**：中

**建议修改**：在文档中明确"自动修复"的规则，例如：
1. 尝试 `json.loads()` 前先提取 `<json>...</json>` 代码块
2. 尝试修复常见 JSON 错误（尾逗号、单引号、未转义换行）
3. 以上都失败 → 将原始输出传给 LLM 并附加"请只输出纯 JSON，不要附加任何解释"的修正 Prompt

**修改位置**：`docs/system-architecture.md` 第 10.1 节；`docs/architecture.md` 第 9.2 节

---

### 问题 10：打包后 `sys._MEIPASS` 路径在开发中不可达（开发体验）

**描述**：`architecture.md` 第 11.5 节提供了 `get_web_dir()` 函数来处理打包后的静态文件路径。但开发模式下返回的是 `files("novel2script.web")` 的路径，这要求 `web/` 目录在 Python 包中可被 `importlib.resources` 访问（需要 `web/` 目录中有 `__init__.py` 或在 `pyproject.toml` 中配置 `package-data`）。

**风险等级**：中（可能导致开发时前端资源 404）

**建议修改**：
- 在 `get_web_dir()` 中增加开发模式检测：`if not getattr(sys, 'frozen', False): return "src/web"`（直接返回源码路径）
- 确保 `pyproject.toml` 中配置了 `package-data`

**修改位置**：`docs/architecture.md` 第 11.5 节

---

## 二、质询结论

| # | 问题 | 风险等级 | 是否阻塞 V1 发布 |
|---|------|---------|----------------|
| 1 | Pipeline 无取消检查点 | 高 | **是** |
| 2 | Skill 沙箱隔离不足 | 中高 | 否（V1 本地工具） |
| 3 | 配置优先级逻辑错误 | 中 | **是** |
| 4 | 角色别名合并算法简单 | 中 | 否（可后续优化） |
| 5 | PyWebView 回退路径 Bug | 高 | **是** |
| 6 | SSE 长时运行可能断连 | 中高 | **是** |
| 7 | 版本历史磁盘空间 | 低中 | 否 |
| 8 | `source_location` 编辑后失效 | 高 | **是** |
| 9 | LLM 输出自动修复策略不明确 | 中 | 否 |
| 10 | 开发模式静态文件路径 | 中 | **是**（影响开发体验） |

**阻塞 V1 发布的问题**：#1、#3、#5、#6、#8、#10 → 共 6 个，需要在 V1 架构设计中修复。

---

## 三、架构优点（值得保留的设计）

1. **五层架构 + 核心不变性保证**：业务层接口冻结的设计非常好，真正做到了"对扩展开放，对修改封闭"
2. **ProjectStore Protocol 设计**：数据访问层隔离，未来迁移 SQLite 零成本
3. **Skill 动态加载机制**：`importlib.util.spec_from_file_location` 比 `entry_points` 更灵活，适合运行时扩展
4. **配置层级设计**：虽然优先级有问题（问题 #3），但多层级的思路是正确的
5. **SSE 而非 WebSocket**：单向推送确实够用，简化了架构

---

*报告生成时间：2026-06-06*  
*下一步：根据本报告修改 `docs/system-architecture.md` 和 `docs/architecture.md`（任务 2.4）*
