# 详细设计质询报告（Detailed Design Grill Report）

> 质询时间：2026-06-06
> 质询对象：`docs/api-design.md` + `docs/data-model-design.md` + `docs/prompt-template-design.md`
> 质询方法：Grill Me Skill（结构化质询）
> 质询目标：发现设计漏洞、评估可实现性、提出改进建议

---

## 目录

1. [质询总结](#1-质询总结)
2. [阻塞问题（必须修复）](#2-阻塞问题必须修复)
3. [建议改进（应该修复）](#3-建议改进应该修复)
4. [可选优化（可以以后做）](#4-可选优化可以以后做)
5. [质询详细记录](#5-质询详细记录)
6. [决策记录](#6-决策记录)
7. [下一步行动](#7-下一步行动)

---

## 1. 质询总结

### 1.1 整体评价

| 维度 | 评分 | 说明 |
|------|------|------|
| **完整性** | ⭐⭐⭐⭐☆ 4/5 | 覆盖了主要设计方面，但缺少一些边界情况处理 |
| **一致性** | ⭐⭐⭐⭐⭐ 5/5 | 3 个文档之间的设计保持一致 |
| **可实现性** | ⭐⭐⭐☆☆ 3/5 | 部分设计过于理想化，需要简化 |
| **可测试性** | ⭐⭐⭐⭐☆ 4/5 | 提供了清晰的接口定义，但缺少测试用例设计 |
| **可扩展性** | ⭐⭐⭐⭐⭐ 5/5 | 插件式扩展设计优秀 |

### 1.2 主要发现

| 发现 | 类型 | 严重程度 | 状态 |
|------|------|---------|------|
| **#1：API 端点过多，V1 应该精简** | 设计过度 | 🔴 阻塞 | 待修复 |
| **#2：Pydantic 模型缺少默认值处理** | 可实现性 | 🟡 建议 | 待修复 |
| **#3：Prompt 模板缺少 Token 优化策略** | 性能 | 🟡 建议 | 待修复 |
| **#4：SSE 心跳机制可能不够可靠** | 可靠性 | 🔴 阻塞 | 待修复 |
| **#5：数据模型缺少版本兼容性处理** | 可维护性 | 🟢 可选 | 待修复 |
| **#6：Prompt 模板没有考虑多语言支持** | 可扩展性 | 🟢 可选 | 待修复 |

---

## 2. 阻塞问题（必须修复）

### 问题 #1：API 端点过多，V1 应该精简

**发现时间**：质询 `docs/api-design.md` 第 3 节

**问题描述**：
- `docs/api-design.md` 定义了 **19 个 API 端点**
- V1 是 MVP（最小可行产品），应该聚焦核心功能
- 部分端点可以在 V2 再实现

**详细分析**：

当前定义的 19 个端点：

| 端点 | 必要性 | 建议 |
|------|---------|------|
| `GET /projects` | ✅ 必需 | 保留 |
| `POST /projects` | ✅ 必需 | 保留 |
| `GET /projects/{id}` | ✅ 必需 | 保留 |
| `PUT /projects/{id}` | ⚠️ 可以简化 | V1 只支持更新 `name`，不支持更新 `config` |
| `DELETE /projects/{id}` | ✅ 必需 | 保留，但 `permanent` 参数改为 V2 实现 |
| `GET /projects/{id}/download` | ✅ 必需 | 保留 |
| `POST /projects/{id}/convert` | ✅ 必需 | 保留，但 `steps` 参数改为可选（使用默认 Pipeline） |
| `GET /convert/{id}/status` | ⚠️ 可以简化 | V1 只使用 SSE，不需要轮询接口 |
| `GET /convert/{id}/progress` | ✅ 必需 | 保留（SSE） |
| `POST /convert/{id}/cancel` | ⚠️ 可以简化 | V1 可以先不支持取消，或只支持简单取消 |
| `GET /projects/{id}/novel` | ✅ 必需 | 保留 |
| `PUT /projects/{id}/novel` | ✅ 必需 | 保留 |
| `GET /projects/{id}/script` | ✅ 必需 | 保留 |
| `PUT /projects/{id}/script` | ✅ 必需 | 保留 |
| `POST /projects/{id}/script/validate` | ⚠️ 可以简化 | V1 可以在前端校验，不需要后端校验接口 |
| `GET /skills` | ⚠️ 可以简化 | V1 可以先不支持 Skill 管理，硬编码内置 Skill |
| `POST /skills/{name}/toggle` | ❌ 不需要 | V2 实现 |
| `POST /skills/install` | ❌ 不需要 | V2 实现 |
| `DELETE /skills/{name}` | ❌ 不需要 | V2 实现 |
| `GET /config` | ✅ 必需 | 保留 |
| `PUT /config` | ✅ 必需 | 保留 |
| `POST /config/test-llm` | ⚠️ 可以简化 | V1 可以先不支持测试，或只简单测试连接 |

**建议的 V1 端点清单**（精简到 **12 个**）：

| 方法 | 路径 | 功能 | 必要性 |
|------|------|------|------|
| GET | `/api/v1/projects` | 获取项目列表 | ✅ 必需 |
| POST | `/api/v1/projects` | 创建项目 | ✅ 必需 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 | ✅ 必需 |
| PUT | `/api/v1/projects/{id}` | 更新项目（仅 name） | ⚠️ 简化 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 | ✅ 必需 |
| GET | `/api/v1/projects/{id}/download` | 下载项目文件 | ✅ 必需 |
| POST | `/api/v1/projects/{id}/convert` | 启动转换任务 | ✅ 必需 |
| GET | `/api/v1/convert/{id}/progress` | 获取转换进度（SSE） | ✅ 必需 |
| GET | `/api/v1/projects/{id}/novel` | 获取小说原文 | ✅ 必需 |
| PUT | `/api/v1/projects/{id}/novel` | 保存小说原文 | ✅ 必需 |
| GET | `/api/v1/projects/{id}/script` | 获取剧本 YAML | ✅ 必需 |
| PUT | `/api/v1/projects/{id}/script` | 保存剧本 YAML | ✅ 必需 |
| GET | `/api/v1/config` | 获取当前配置 | ✅ 必需 |
| PUT | `/api/v1/config` | 更新配置 | ✅ 必需 |

**修复建议**：
1. 从 `docs/api-design.md` 中移除 V2 才需要的端点
2. 简化 `POST /projects/{id}/convert` 的请求体（移除 `steps` 参数，使用默认 Pipeline）
3. 移除 `POST /convert/{id}/cancel`（V1 不支持取消）
4. 移除 Skill 管理相关端点（V1 硬编码内置 Skill）

**预计修复工作量**：0.5 小时

---

### 问题 #2：SSE 心跳机制可能不够可靠

**发现时间**：质询 `docs/api-design.md` 第 4 节

**问题描述**：
- `docs/api-design.md` 定义了心跳机制（每 15 秒发送一次 `heartbeat` 事件）
- 但是，如果客户端在网络中断后重连，可能会丢失中间的事件
- 没有定义 SSE 连接的超时和清理机制

**详细分析**：

当前设计的心跳机制：

```python
# 每 15 秒发送一次心跳
if time.time() - last_heartbeat > 15:
    yield {
        "event": "heartbeat",
        "data": json.dumps({"ts": int(time.time())})
    }
    last_heartbeat = time.time()
```

**问题**：
1. **网络中断后重连会丢失事件**：如果客户端网络中断 30 秒后重连，中间 30 秒的事件会丢失
2. **没有定义 SSE 连接的超时**：如果客户端断开连接后，服务端可能还在继续推送事件，浪费资源
3. **没有定义 SSE 连接的最大持续时间**：如果转换任务很长（如 1 小时），SSE 连接可能会因为代理/负载均衡的超时而断开

**建议的改进方案**：

#### 方案 A：增加事件缓存（推荐）

```python
from collections import deque
import time

class SSEManager:
    def __init__(self, max_cache_size: int = 100):
        self.clients: dict[str, SSEClient] = {}
        self.event_cache: deque = deque(maxlen=max_cache_size)  # 缓存最近 100 个事件
        
    def push_event(self, task_id: str, event: dict) -> None:
        """推送事件给所有订阅该任务的客户端，并缓存"""
        # 缓存事件
        self.event_cache.append({
            "task_id": task_id,
            "event": event,
            "ts": time.time()
        })
        
        # 推送给所有客户端
        for client in self.clients.values():
            if client.task_id == task_id:
                client.queue.put(event)
    
    def get_cached_events(self, task_id: str, since_ts: float) -> list[dict]:
        """获取自某个时间戳以来的缓存事件"""
        return [
            item["event"]
            for item in self.event_cache
            if item["task_id"] == task_id and item["ts"] > since_ts
        ]

# SSE 端点实现
@app.get("/api/v1/convert/{task_id}/progress")
async def get_convert_progress(
    task_id: str,
    last_event_ts: float = 0.0,  # 客户端传入上次收到事件的时间戳
):
    async def event_generator():
        # 1. 先推送缓存的事件（防止网络中断丢失事件）
        cached_events = sse_manager.get_cached_events(task_id, last_event_ts)
        for event in cached_events:
            yield event
        
        # 2. 然后继续推送新事件
        client_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        
        sse_manager.clients[client_id] = SSEClient(task_id, queue)
        
        try:
            while True:
                # 等待新事件（超时 15 秒发送心跳）
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"ts": time.time()})
                    }
        finally:
            # 清理客户端
            del sse_manager.clients[client_id]
    
    return EventSourceResponse(event_generator())
```

#### 方案 B：使用 Redis 作为事件总线（V2）

如果未来需要支持多进程/多服务器，可以使用 Redis 的 Pub/Sub 功能。

**修复建议**：
1. 实现方案 A（事件缓存）
2. 定义 SSE 连接的超时和清理机制
3. 前端实现自动重连，并传入 `last_event_ts` 参数

**预计修复工作量**：2 小时

---

## 3. 建议改进（应该修复）

### 问题 #3：Pydantic 模型缺少默认值处理

**发现时间**：质询 `docs/data-model-design.md` 第 3 节

**问题描述**：
- `docs/data-model-design.md` 定义的 Pydantic 模型，部分字段缺少合理的默认值
- 如果 LLM 输出缺少某些字段，Pydantic 校验会失败

**详细分析**：

当前定义的 `DialogueBeat` 模型：

```python
class DialogueBeat(BaseModel):
    type: Literal["dialogue"] = "dialogue"
    character: str = Field(..., description="角色名称")
    content: str = Field(..., description="对白内容")
    emotion: str | None = Field(None, description="情绪标签")
```

**问题**：
- 如果 LLM 输出的 JSON 中缺少 `emotion` 字段，Pydantic 会自动使用默认值 `None`，这没问题
- 但是，如果 LLM 输出的 JSON 中缺少 `type` 字段，Pydantic 会校验失败（因为 `type` 字段有默认值，但 `Literal["dialogue"]` 校验会失败）

**建议的改进方案**：

```python
class DialogueBeat(BaseModel):
    type: Literal["dialogue"] = "dialogue"  # 有默认值，LLM 可以不输出
    character: str = Field(..., description="角色名称")
    content: str = Field(..., description="对白内容")
    emotion: str | None = Field(None, description="情绪标签")
    
    @model_validator(mode="before")
    @classmethod
    def set_default_type(cls, data: dict) -> dict:
        """如果缺少 type 字段，自动设置为默认值"""
        if "type" not in data:
            data["type"] = "dialogue"
        return data
```

**修复建议**：
1. 为所有 Beat 模型添加 `model_validator`，自动设置 `type` 默认值
2. 为可选字段添加合理的默认值

**预计修复工作量**：1 小时

---

### 问题 #4：Prompt 模板缺少 Token 优化策略

**发现时间**：质询 `docs/prompt-template-design.md` 第 3 节

**问题描述**：
- `docs/prompt-template-design.md` 定义的 Prompt 模板，没有考虑 Token 优化
- 如果小说文本很长（如 10 万字），Prompt 可能会超出 LLM 的上下文窗口

**详细分析**：

当前定义的 `character_extractor` Prompt 模板：

```markdown
# Input Text
以下是需要处理的文本：
```
{novel_text}
```
```

**问题**：
- 如果 `novel_text` 很长（如 10 万字），Prompt 会超出 LLM 的上下文窗口（如 gpt-3.5-turbo 的 4096 tokens）
- 没有定义长文本的处理策略（分段？摘要？）

**建议的改进方案**：

#### 方案 A：智能分段（推荐）

```python
# prompts/prompt_executor.py

class PromptExecutor:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model
        self.max_context_tokens = 4096  # 根据模型调整
        
    def _count_tokens(self, text: str) -> int:
        """计算文本的 Token 数（粗略估计：1 个中文字符 ≈ 2 个 Token）"""
        return len(text) * 2
    
    def _split_text(self, text: str, max_tokens: int) -> list[str]:
        """将文本分割为多个片段，每个片段不超过 max_tokens"""
        max_chars = max_tokens // 2  # 1 个中文字符 ≈ 2 个 Token
        
        segments = []
        current_segment = ""
        
        for line in text.splitlines():
            if self._count_tokens(current_segment + line) > max_tokens:
                segments.append(current_segment)
                current_segment = line
            else:
                current_segment += line + "\n"
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    async def execute(
        self,
        prompt_template: str,
        variables: dict[str, Any],
        schema: dict,
        max_retries: int = 3,
    ) -> dict:
        """执行 Prompt，包含自动修复和降级重试"""
        
        # 1. 检查文本长度
        novel_text = variables.get("novel_text", "")
        if self._count_tokens(novel_text) > self.max_context_tokens:
            # 分段处理
            segments = self._split_text(novel_text, self.max_context_tokens)
            
            # 并行处理所有分段
            results = await asyncio.gather(*[
                self._execute_single(prompt_template, {**variables, "novel_text": seg})
                for seg in segments
            ])
            
            # 合并结果
            merged_result = self._merge_results(results)
            return merged_result
        
        else:
            # 直接处理
            return await self._execute_single(prompt_template, variables)
    
    async def _execute_single(
        self,
        prompt_template: str,
        variables: dict[str, Any],
    ) -> dict:
        """执行单个 Prompt"""
        # ...（实现见前一个版本）
```

**修复建议**：
1. 在 `docs/prompt-template-design.md` 中增加 "Token 优化策略" 章节
2. 定义长文本的处理策略（智能分段、并行处理、结果合并）
3. 实现 `_count_tokens()` 和 `_split_text()` 方法

**预计修复工作量**：3 小时

---

## 4. 可选优化（可以以后做）

### 问题 #5：数据模型缺少版本兼容性处理

**发现时间**：质询 `docs/data-model-design.md` 第 3 节

**问题描述**：
- `docs/data-model-design.md` 定义的 Pydantic 模型，没有考虑版本兼容性
- 如果未来 V2 版本修改了数据模型，V1 生成的 YAML 文件可能无法解析

**详细分析**：

当前定义的 `ScriptMeta` 模型：

```python
class ScriptMeta(BaseModel):
    version: str = "1.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_name: str = ""
    total_beats: int = 0
    dialogue_count: int = 0
    action_count: int = 0
    narration_count: int = 0
    characters: list[str] = Field(default_factory=list)
```

**问题**：
- 如果 V2 版本在 `ScriptMeta` 中添加了新字段（如 `generator_version`），V1 版本的 Pydantic 模型可能无法解析 V2 生成的 YAML 文件
- 没有定义版本兼容性策略（向前兼容？向后兼容？）

**建议的改进方案**：

#### 方案 A：使用 Pydantic 的 `model_config = {"extra": "ignore"}`（推荐）

```python
class ScriptMeta(BaseModel):
    version: str = "1.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_name: str = ""
    total_beats: int = 0
    dialogue_count: int = 0
    action_count: int = 0
    narration_count: int = 0
    characters: list[str] = Field(default_factory=list)
    
    model_config = {"extra": "ignore"}  # 忽略额外字段
```

**优点**：
- V1 版本的代码可以解析 V2 生成的 YAML 文件（忽略不认识的字段）
- 向前兼容

**缺点**：
- 如果 V2 版本修改了现有字段的类型，V1 版本的代码可能会出错

#### 方案 B：版本化数据模型

```python
# schema/v1.py
class ScriptMetaV1(BaseModel):
    version: str = "1.0"
    # ... V1 字段

# schema/v2.py
class ScriptMetaV2(BaseModel):
    version: str = "2.0"
    # ... V2 字段（可能修改了 V1 的字段）
    
    @model_validator(mode="before")
    @classmethod
    def migrate_v1_to_v2(cls, data: dict) -> dict:
        """从 V1 迁移到 V2"""
        if data.get("version") == "1.0":
            # 执行迁移逻辑
            data["new_field"] = "default_value"
        return data
```

**优点**：
- 明确的版本迁移逻辑
- 可以向后兼容（V2 可以解析 V1 的数据）

**缺点**：
- 需要维护多个版本的模型
- 迁移逻辑可能很复杂

**修复建议**：
1. 实现方案 A（简单，适合 V1）
2. V2 再考虑方案 B（如果需要）

**预计修复工作量**：1 小时

---

### 问题 #6：Prompt 模板没有考虑多语言支持

**发现时间**：质询 `docs/prompt-template-design.md` 第 3 节

**问题描述**：
- `docs/prompt-template-design.md` 定义的 Prompt 模板，都是中文的
- 如果未来需要支持英文小说，Prompt 模板需要重构

**详细分析**：

当前定义的 `character_extractor` Prompt 模板：

```markdown
# Role
你是一个专业的文学分析专家，擅长从小说中提取所有登场角色信息。

# Task
你的任务是从以下小说文本中，提取所有登场角色的名称和基本信息。

# Input
输入是小说文本（可能是整本小说，也可能是单个章节）。

# Output
请严格按照以下 JSON Schema 输出结果：
```

**问题**：
- Prompt 模板是中文的，如果输入是英文小说，LLM 可能无法理解 Prompt
- 没有定义多语言支持的架构（每个语言一个 Prompt 模板？还是同一个 Prompt 模板支持多语言？）

**建议的改进方案**：

#### 方案 A：每个语言一个 Prompt 模板（推荐）

```
prompts/
├── zh-CN/  # 中文 Prompt
│   ├── character_extractor.md
│   ├── scene_splitter.md
│   └── ...
├── en-US/  # 英文 Prompt
│   ├── character_extractor.md
│   ├── scene_splitter.md
│   └── ...
└── few_shots/  # 共享的 few-shot 示例库（可以是多语言的）
```

**优点**：
- 每个语言的 Prompt 模板可以针对该语言优化
- 易于维护和更新

**缺点**：
- 需要维护多个语言的 Prompt 模板
- 如果支持 10 种语言，需要维护 10 套 Prompt 模板

#### 方案 B：同一个 Prompt 模板支持多语言

```markdown
# Role
You are a professional literary analysis expert, good at extracting character information from novels.

# Task
Your task is to extract the names and basic information of all characters from the following novel text.

# Input
Input is the novel text (may be the entire novel or a single chapter).

# Output
Please output the result strictly according to the following JSON Schema:
```

**优点**：
- 只需要维护一套 Prompt 模板
- 适合多语言支持

**缺点**：
- Prompt 模板需要使用英文（LLM 最理解的语言）
- 可能不如针对每个语言优化的 Prompt 模板效果好

**修复建议**：
1. V1 只支持中文，使用方案 A（中文 Prompt 模板）
2. V2 如果需要支持英文，可以添加 `en-US/` 目录

**预计修复工作量**：0.5 小时

---

## 5. 质询详细记录

### 5.1 质询会话 1：API 设计

**时间**：2026-06-06 10:00 - 10:30

**参与者**：AI Agent（质询者），`docs/api-design.md`（被质询文档）

**质询问题**：

1. **Q1**：API 端点是否过多？V1 是否应该精简？
   - **A1**：是的，V1 应该精简到核心功能。建议从 19 个端点精简到 12 个。

2. **Q2**：SSE 心跳机制是否足够可靠？
   - **A2**：不够可靠。建议增加事件缓存，防止网络中断丢失事件。

3. **Q3**：错误码规范是否完整？
   - **A3**：基本完整，但缺少 `429` 限速错误的详细处理建议。

**决策**：

| 决策 | 理由 | 行动 |
|------|------|------|
| 精简 API 端点到 12 个 | V1 聚焦核心功能 | 更新 `docs/api-design.md` |
| 增加 SSE 事件缓存 | 防止网络中断丢失事件 | 更新 `docs/api-design.md` |
| 补充错误码处理建议 | 提高可操作性 | 更新 `docs/api-design.md` |

---

### 5.2 质询会话 2：数据模型设计

**时间**：2026-06-06 10:30 - 11:00

**参与者**：AI Agent（质询者），`docs/data-model-design.md`（被质询文档）

**质询问题**：

1. **Q1**：Pydantic 模型是否考虑了默认值处理？
   - **A1**：部分考虑了，但缺少 `model_validator` 自动设置默认值。

2. **Q2**：数据模型是否考虑了版本兼容性？
   - **A2**：没有。建议使用 `model_config = {"extra": "ignore"}` 实现向前兼容。

3. **Q3**：YAML Schema 校验规则是否完整？
   - **A3**：基本完整，但缺少自定义校验器的示例。

**决策**：

| 决策 | 理由 | 行动 |
|------|------|------|
| 添加 `model_validator` 自动设置默认值 | 提高容错性 | 更新 `docs/data-model-design.md` |
| 使用 `model_config = {"extra": "ignore"}` | 实现向前兼容 | 更新 `docs/data-model-design.md` |
| 补充自定义校验器示例 | 提高可操作性 | 更新 `docs/data-model-design.md` |

---

### 5.3 质询会话 3：Prompt 模板设计

**时间**：2026-06-06 11:00 - 11:30

**参与者**：AI Agent（质询者），`docs/prompt-template-design.md`（被质询文档）

**质询问题**：

1. **Q1**：Prompt 模板是否考虑了 Token 优化？
   - **A1**：没有。建议增加智能分段和并行处理。

2. **Q2**：Prompt 模板是否考虑了多语言支持？
   - **A2**：没有。建议 V1 只支持中文，V2 再考虑多语言。

3. **Q3**：Few-shot 示例是否足够多样？
   - **A3**：基本足够，但可以增加更多边界情况的示例。

**决策**：

| 决策 | 理由 | 行动 |
|------|------|------|
| 增加 Token 优化策略 | 支持长文本处理 | 更新 `docs/prompt-template-design.md` |
| V1 只支持中文 | 聚焦核心功能 | 更新 `docs/prompt-template-design.md` |
| 增加边界情况的 Few-shot 示例 | 提高准确性 | 更新 `docs/prompt-template-design.md` |

---

## 6. 决策记录

### 6.1 架构决策记录（ADR）

#### ADR-011：V1 API 端点精简

**状态**：已接受

**背景**：
- `docs/api-design.md` 最初设计了 19 个 API 端点
- V1 是 MVP，应该聚焦核心功能

**决策**：
- 精简 API 端点到 **12 个**
- 移除 V2 才需要的功能（Skill 管理、转换取消、轮询接口）

**后果**：
- ✅ 减少开发工作量
- ✅ 降低维护成本
- ❌ V1 功能相对较少

---

#### ADR-012：SSE 事件缓存

**状态**：已接受

**背景**：
- SSE 心跳机制可能不够可靠
- 网络中断后重连会丢失中间的事件

**决策**：
- 增加 **事件缓存**（缓存最近 100 个事件）
- 客户端重连时，先推送缓存的事件

**后果**：
- ✅ 提高可靠性
- ✅ 防止事件丢失
- ❌ 增加内存消耗（缓存事件）

---

#### ADR-013：Pydantic 模型向前兼容

**状态**：已接受

**背景**：
- 数据模型没有考虑版本兼容性
- 如果未来 V2 修改了数据模型，V1 生成的 YAML 文件可能无法解析

**决策**：
- 使用 `model_config = {"extra": "ignore"}` 忽略额外字段
- V1 可以解析 V2 生成的 YAML 文件（向前兼容）

**后果**：
- ✅ 实现简单
- ✅ 向前兼容
- ❌ 如果 V2 修改了现有字段的类型，V1 可能会出错

---

## 7. 下一步行动

### 7.1 立即行动（阻塞问题）

| 行动 | 负责人 | 预计工作量 | 截止日期 |
|------|---------|---------|---------|
| 精简 API 端点到 12 个 | AI Agent | 0.5 小时 | 2026-06-06 |
| 增加 SSE 事件缓存 | AI Agent | 2 小时 | 2026-06-06 |
| 更新 `docs/api-design.md` | AI Agent | 1 小时 | 2026-06-06 |

---

### 7.2 建议行动（建议改进）

| 行动 | 负责人 | 预计工作量 | 截止日期 |
|------|---------|---------|---------|
| 添加 `model_validator` 自动设置默认值 | AI Agent | 1 小时 | 2026-06-07 |
| 增加 Token 优化策略 | AI Agent | 3 小时 | 2026-06-07 |
| 补充自定义校验器示例 | AI Agent | 1 小时 | 2026-06-07 |

---

### 7.3 可选行动（可选优化）

| 行动 | 负责人 | 预计工作量 | 截止日期 |
|------|---------|---------|---------|
| 使用 `model_config = {"extra": "ignore"}` | AI Agent | 1 小时 | V2 |
| V1 只支持中文 Prompt | AI Agent | 0.5 小时 | V2 |
| 增加边界情况的 Few-shot 示例 | AI Agent | 2 小时 | V2 |

---

## 8. 总结

本次质询发现了 **6 个设计问题**，其中：
- **2 个阻塞问题**（必须修复）
- **2 个建议改进**（应该修复）
- **2 个可选优化**（可以以后做）

**关键决策**：
1. ✅ V1 精简 API 端点到 12 个
2. ✅ SSE 增加事件缓存
3. ✅ Pydantic 模型向前兼容

**下一步**：
1. 修复阻塞问题（任务 3.5）
2. 实施建议改进（任务 3.5）
3. 完成阶段 3 交付物（Git 提交）

---

**报告状态**：✅ 已完成

**最后更新**：2026-06-06
