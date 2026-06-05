# Novel2Script 文档问题审查报告

> 审查日期：2026-06-05
> 审查范围：PRD.md / architecture.md / extensibility-design-spec.md / prompt-design.md / yaml-schema.md

---

## 一、已完成修正的问题

| # | 问题 | 涉及文档 | 修正内容 | 状态 |
|---|------|---------|---------|------|
| 1 | 项目名称不统一 | `extensibility-design-spec.md` | 标题及页脚 `InkScript` → `Novel2Script` | DONE |
| 2 | `novel.txt` vs `novel.md` 不一致 | `architecture.md`（§6.2、§6.4） | 两处 `novel.md` → `novel.txt` | DONE |
| 3 | 分段阈值三处不一致 | `architecture.md` §8.2：`50000` | `50000` → `6000`（与 PRD 一致） | DONE |
| 4 | 自动保存 debounce 时间不一致 | `architecture.md` §6.6：`1000` | `1000) // 1秒防抖` → `2000) // 2秒防抖（与 PRD 一致）` | DONE |
| 5 | `uuid4().hex[:8]` 碰撞风险 | `architecture.md` §6.4 / `extensibility-design-spec.md` §3.1.2 | `uuid4().hex[:8]` → `uuid4().hex`（完整 32 字符 hex） | DONE |
| 6 | `source_location` 字段在 YAML Schema 中缺失 | `yaml-schema.md` §2.6 / §5.2 | `DialogueBeat`/`ActionBeat`/`NarrationBeat` 均补充 `source_location: Optional[SourceLocation] = None`；新增 `SourceLocation` 模型 | DONE |
| 7 | `reorder_steps()` 方法只有文档承诺没有实现 | `architecture.md` §3.3 | 补充 `reorder_steps()` 和 `skip_steps()` 方法定义 | DONE |
| 8 | `requires_llm` 字段未被 SkillManager 处理 | `extensibility-design-spec.md` §7.8 | 补充 `execute()` 和 `execute_safe()` 方法，处理 `requires_llm` 逻辑 | DONE |
| 9 | `on_step_complete` 传入空字符串无意义 | `architecture.md` §3.3 | 修改 `Pipeline.run()` 调用 `_make_step_summary()` 生成摘要 | DONE |
| 10 | `config.json` API Key 明文存储，未提醒文件权限 | PRD §11.2 / `architecture.md` §8.3 | PRD §11.2 已包含 `文件权限 | 配置文件创建时设置 600 权限`；`architecture.md` §8.3 已包含脱敏逻辑 | DONE |
| 11 | `extensibility-design-spec.md` 与 `architecture.md` 伪代码逻辑不一致 | `architecture.md` §3.3 / `extensibility-design-spec.md` §2.1.3 | 统一 `_fire_hook` 返回值处理：`architecture.md` 已更新为 `context = await self._fire_hook(...)` | DONE |

---

## 二、修正优先级总结

> 所有 identified issues 均已修正。

| 优先级 | Issue 编号 | 问题 | 状态 |
|-------|-----------|------|------|
| P0 | ISSUE-001 | `requires_llm` 未处理 | DONE |
| P0 | ISSUE-002 | `on_step_complete` 传空字符串 | DONE |
| P1 | ISSUE-003 | API Key 明文存储无权限提醒 | DONE (PRD 已包含) |
| P1 | ISSUE-004 | 伪代码逻辑不一致 | DONE |

---

## 三、修正记录

| 日期 | 修正内容 | 修正人 |
|------|---------|---------|
| 2026-06-05 | 项目名称统一（`InkScript` → `Novel2Script`） | AI |
| 2026-06-05 | `novel.md` → `novel.txt` 统一 | AI |
| 2026-06-05 | 分段阈值统一为 `6000` | AI |
| 2026-06-05 | 自动保存 debounce 统一为 `2000ms`（2 秒） | AI |
| 2026-06-05 | `uuid4().hex[:8]` → `uuid4().hex`（完整 uuid） | AI |
| 2026-06-05 | `yaml-schema.md` 补充 `source_location` 字段 | AI |
| 2026-06-05 | `architecture.md` 补充 `reorder_steps()` 和 `skip_steps()` 方法 | AI |
| 2026-06-05 | `extensibility-design-spec.md` 补充 `SkillManager.execute()` 逻辑 | AI |
| 2026-06-05 | `architecture.md` 修复 `on_step_complete` 空字符串问题 | AI |
| 2026-06-05 | 统一 `architecture.md` 与 `extensibility-design-spec.md` 的 `_fire_hook` 返回值处理 | AI |

---

*此文件由 AI 审查助手生成，记录所有发现的问题及修正状态。*
*所有 identified issues 均已修正。*
