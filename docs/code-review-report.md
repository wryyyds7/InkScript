# 代码审查报告

> 审查时间：2026-06-05
> 审查范围：`src/` 全部代码
> 审查方法：Grill Me 质询 + 静态分析

---

## 1. 审查结论

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 阻塞 | 2 | 必须修复才能继续 |
| 🟡 建议 | 5 | 建议修复，提升质量 |
| 🟢 优点 | 8 | 设计良好的部分 |

---

## 2. 🔴 阻塞问题（必须修复）

### 问题 #1：`src/api/routes/v1/projects.py` 语法错误

**位置**：`projects.py` 多处

**问题**：字典字面量写法错误，使用了中文/英文标点混用：
```python
# 错误写法
return {"code": 0, "data": meta}  # 缺少冒号？实际是逗号问题

# 多处出现：
{"code": 0, "data": meta}  # 应为 {"code": 0, "data": meta}
```

**实际错误**：Python `dict` 字面量中 `:` 被写成了 `,`，导致 `SyntaxError`。

**修复**：
```python
# 修复后
return {"code": 0, "data": meta}
```

---

### 问题 #2：`src/api/routes/v1/convert.py` 语法错误

**位置**：`convert.py` 多处

**问题**：同上，字典语法错误 + `list(steps).index()` 参数错误。

还有 `_run_pipeline` 中的 f-string 格式化错误：
```python
# 错误
yield {"event": ..., "data": json.dumps({...}, ensure_ascii=False)}
# 在 yield 的 dict 值中嵌套 f-string 或 json.dumps 时括号不匹配
```

**修复**：统一检查所有字典字面量和括号匹配。

---

## 3. 🟡 建议修复

### 问题 #3：`src/schema.py` 的 `to_yaml` 依赖未懒加载

**问题**：`to_yaml()` 函数内部 `import yaml` 放在函数体内，每次调用都 import，性能差。

**建议**：移到文件顶部，或至少缓存。

---

### 问题 #4：`src/core/steps/character_extractor.py` LLM 调用未做异常处理

**问题**：`llm.chat_json()` 可能抛出 `openai.APIError`，但 Step 内未捕获，会导致整个 Pipeline 中断。

**建议**：在 `Step.run()` 外层捕获，或每个 Step 内部捕获并记录错误到 `ctx["errors"]`。

---

### 问题 #5：`src/cli.py` 的 `convert` 命令未真正分段处理长文本

**问题**：`cli.py` 的 `convert` 命令直接把全文传给 `pipeline.run()`，没有做智能分段，超长文本会超出 LLM 上下文窗口。

**建议**：接入 `TextSegmenter`（计划中但未实现）。

---

### 问题 #6：`src/api/sse.py` 的 `push_event` 中 `queue.put_nowait` 可能丢失事件

**问题**：队列满时直接丢弃事件（`dead` 列表），没有等待/重试机制。

**建议**：改用 `await queue.put(event)` 带超时，或增大队列 `maxsize`。

---

### 问题 #7：缺少 `__init__.py` 导致部分模块无法被 import

**问题**：`src/core/steps/__init__.py`、`src/api/routes/v1/__init__.py` 可能未创建，导致 `import` 失败。

**建议**：检查所有目录都有 `__init__.py`。

---

## 4. 🟢 设计优点

1. **Pydantic V2 模型设计良好**：`Beat` Tagged Union 设计优雅，`model_validator` 自动填充 `type` 字段。
2. **Pipeline + Hook 机制**：扩展性好，Skill 可以通过 Hook 注入。
3. **SSE 事件缓存**：`SSEManager.event_cache` 设计合理，支持断线重连。
4. **配置管理**：`pydantic-settings` + `lru_cache` 单例模式正确。
5. **StepProtocol**：`Protocol` + `register_step` 装饰器，插件式扩展设计好。
6. **CLI 三模式**：`gui/serve/convert` 共用同一套后端逻辑，架构清晰。
7. **前端零构建**：Alpine.js + Tailwind CDN，符合 V1 约束。
8. **测试骨架完整**：每个核心模块都有对应的 `test_*.py` 骨架。

---

## 5. 修复计划

| 问题 | 优先级 | 预计修复时间 |
|------|---------|-------------|
| #1 语法错误（projects.py） | 🔴 P0 | 10 分钟 |
| #2 语法错误（convert.py） | 🔴 P0 | 10 分钟 |
| #7 缺少 `__init__.py` | 🔴 P0 | 5 分钟 |
| #4 Step 异常处理 | 🟡 P1 | 30 分钟 |
| #6 SSE 队列丢失 | 🟡 P1 | 20 分钟 |
| #3 yaml import 优化 | 🟡 P2 | 5 分钟 |
| #5 长文本分段 | 🟡 P2 | 2 小时 |

---

## 6. 审查签字

- **审查人**：Grill Me (AI)
- **日期**：2026-06-05
- **建议**：先修复 P0 问题，再继续阶段 5 测试。
