# API 接口设计文档（API Design Specification）

> 版本：V1.0 | 日期：2026-06-06 | 状态：待确认
> 输入来源：`docs/system-architecture.md` + `docs/requirements-spec.md`
> 输出用途：指导后端实现、前端集成、测试用例编写

---

## 目录

1. [API 设计原则](#1-api-设计原则)
2. [API 版本管理](#2-api-版本管理)
3. [RESTful API 端点设计（V1 精简版）](#3-restful-api-端点设计v1-精简版)
4. [SSE 端点设计](#4-sse-端点设计)
5. [错误码规范](#5-错误码规范)
6. [认证与授权](#6-认证与授权)
7. [请求/响应格式规范](#7-请求响应格式规范)
8. [API 端点详细说明](#8-api-端点详细说明)
9. [附录](#9-附录)

---

## 3. RESTful API 端点设计（V1 精简版）

> **质询修复 #1**：V1 是 MVP，应该聚焦核心功能。从 19 个端点精简到 **12 个**。

### 3.1 V1 核心端点清单（12 个）

| 方法 | 路径 | 功能 | 必要性 | 状态 |
|------|------|------|---------|------|
| GET | `/api/v1/projects` | 获取项目列表 | ✅ 必需 | ✅ 保留 |
| POST | `/api/v1/projects` | 创建项目 | ✅ 必需 | ✅ 保留 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 | ✅ 必需 | ✅ 保留 |
| PUT | `/api/v1/projects/{id}` | 更新项目（仅 name） | ⚠️ 简化 | ✅ 保留（简化版） |
| DELETE | `/api/v1/projects/{id}` | 删除项目 | ✅ 必需 | ✅ 保留 |
| GET | `/api/v1/projects/{id}/download` | 下载项目文件 | ✅ 必需 | ✅ 保留 |
| POST | `/api/v1/projects/{id}/convert` | 启动转换任务 | ✅ 必需 | ✅ 保留（简化版） |
| GET | `/api/v1/convert/{id}/progress` | 获取转换进度（SSE） | ✅ 必需 | ✅ 保留 |
| GET | `/api/v1/projects/{id}/novel` | 获取小说原文 | ✅ 必需 | ✅ 保留 |
| PUT | `/api/v1/projects/{id}/novel` | 保存小说原文 | ✅ 必需 | ✅ 保留 |
| GET | `/api/v1/projects/{id}/script` | 获取剧本 YAML | ✅ 必需 | ✅ 保留 |
| PUT | `/api/v1/projects/{id}/script` | 保存剧本 YAML | ✅ 必需 | ✅ 保留 |
| GET | `/api/v1/config` | 获取当前配置 | ✅ 必需 | ✅ 保留 |
| PUT | `/api/v1/config` | 更新配置 | ✅ 必需 | ✅ 保留 |

### 3.2 V1 移除的端点（移到 V2）

| 方法 | 路径 | 功能 | 移除原因 | V2 状态 |
|------|------|------|---------|---------|
| GET | `/api/v1/convert/{id}/status` | 获取转换进度（轮询） | V1 只使用 SSE，不需要轮询接口 | 🔜 V2 可选 |
| POST | `/api/v1/convert/{id}/cancel` | 取消转换任务 | V1 可以先不支持取消 | 🔜 V2 实现 |
| POST | `/api/v1/projects/{id}/script/validate` | 校验 YAML 格式 | V1 可以在前端校验，不需要后端校验接口 | 🔜 V2 可选 |
| GET | `/api/v1/skills` | 获取 Skill 列表 | V1 可以先不支持 Skill 管理，硬编码内置 Skill | 🔜 V2 实现 |
| POST | `/api/v1/skills/{name}/toggle` | 启用/禁用 Skill | 同上 | 🔜 V2 实现 |
| POST | `/api/v1/skills/install` | 安装用户 Skill | 同上 | 🔜 V2 实现 |
| DELETE | `/api/v1/skills/{name}` | 卸载 Skill | 同上 | 🔜 V2 实现 |
| POST | `/api/v1/config/test-llm` | 测试 LLM 连接 | V1 可以先不支持测试，或只简单测试连接 | 🔜 V2 可选 |

### 3.3 简化版端点详细说明

#### 3.3.1 更新项目（简化版）

```
PUT /api/v1/projects/{project_id}
```

**请求体**（简化版：只支持更新 `name`）：

```json
{
  "name": "新项目名称"
}
```

**说明**：V1 不支持更新 `config`（配置通过 `/api/v1/config` 统一管理）。

#### 3.3.2 启动转换任务（简化版）

```
POST /api/v1/projects/{project_id}/convert
```

**请求体**（简化版：不使用 `steps` 参数，使用默认 Pipeline）：

```json
{
  "options": {
    "enable_sse": true
  }
}
```

**说明**：V1 使用默认 Pipeline 步骤（character_extract → scene_split → dialogue_parse → emotion_tag → yaml_generate），不支持自定义步骤。

**响应示例**：

```json
{
  "code": 0,
  "message": "转换任务已启动",
  "data": {
    "task_id": "task_20240605_120000",
    "sse_url": "/api/v1/convert/task_20240605_120000/progress"
  }
}
```

---

### 3.4 项目管理系统（详细版）

---

## 1. API 设计原则

### 1.1 设计理念

| 原则 | 说明 | 示例 |
|------|------|------|
| **RESTful 风格** | 使用标准 HTTP 方法，资源命名清晰 | `GET /api/v1/projects`（获取项目列表） |
| **版本化** | 所有 API 带版本前缀，便于未来演进 | `/api/v1/...`，`/api/v2/...` |
| **SSE 优先** | 长时间任务使用 SSE 推送进度，避免轮询 | `GET /api/v1/convert/{task_id}/progress` |
| **类型安全** | 使用 Pydantic 模型定义请求/响应，自动生成 OpenAPI 文档 | 见各端点定义 |
| **错误标准化** | 统一错误响应格式，便于前端处理 | 见 [错误码规范](#5-错误码规范) |

### 1.2 基础 URL

```
生产环境：http://localhost:8000/api/v1
开发环境：http://localhost:8000/api/v1
未来云端：https://api.novel2script.com/api/v1
```

---

## 2. API 版本管理

### 2.1 版本策略

| 版本 | 状态 | 说明 |
|------|------|------|
| **V1** | ✅ 当前版本 | 基础功能：项目管理、转换、编辑、Skill |
| **V2** | 🔜 未来版本 | 多用户、协作编辑、云端存储 |

### 2.2 版本兼容性

- **向后兼容**：V1 API 在 V2 中继续保留，标记为 `deprecated`
- ** breaking change**：只在主版本号变更时进行
- **弃用策略**：弃用 API 在文档中标记，至少保留 1 个主版本

---

## 3. RESTful API 端点设计

### 3.1 项目管理系统（Project Management）

#### 3.1.1 获取项目列表

```
GET /api/v1/projects
```

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20，最大 100 |
| `status` | string | 否 | 过滤项目状态：`draft` / `completed` / `archived` |
| `sort_by` | string | 否 | 排序字段：`created_at` / `updated_at`，默认 `updated_at` |
| `order` | string | 否 | 排序方向：`asc` / `desc`，默认 `desc` |

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "projects": [
      {
        "project_id": "proj_20240605_120000",
        "name": "我的小说",
        "status": "completed",
        "created_at": "2024-06-05T12:00:00Z",
        "updated_at": "2024-06-05T14:30:00Z",
        "novel_file": "novel.txt",
        "script_file": "script.yaml"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

#### 3.1.2 创建项目

```
POST /api/v1/projects
```

**请求体**：

```json
{
  "name": "我的小说",
  "novel_content": "小说内容...",  // 或者直接上传文件，见下方说明
  "config": {
    "model_name": "gpt-4o-mini",
    "temperature": 0.7
  }
}
```

**说明**：
- 支持两种上传方式：
  1. `multipart/form-data`：上传 `novel_file`（TXT/MD）
  2. `application/json`：在 `novel_content` 字段中提供文本内容

**响应示例**：

```json
{
  "code": 0,
  "message": "项目创建成功",
  "data": {
    "project_id": "proj_20240605_120000",
    "name": "我的小说",
    "status": "draft",
    "created_at": "2024-06-05T12:00:00Z"
  }
}
```

#### 3.1.3 获取项目详情

```
GET /api/v1/projects/{project_id}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "project_id": "proj_20240605_120000",
    "name": "我的小说",
    "status": "completed",
    "created_at": "2024-06-05T12:00:00Z",
    "updated_at": "2024-06-05T14:30:00Z",
    "config_snapshot": {
      "model_name": "gpt-4o-mini",
      "temperature": 0.7
    },
    "files": {
      "novel": "novel.txt",
      "script": "script.yaml",
      "meta": "meta.json"
    }
  }
}
```

#### 3.1.4 更新项目

```
PUT /api/v1/projects/{project_id}
```

**请求体**：

```json
{
  "name": "新项目名称",
  "config": {
    "model_name": "gpt-4"
  }
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "项目更新成功",
  "data": {
    "project_id": "proj_20240605_120000",
    "name": "新项目名称",
    "updated_at": "2024-06-05T15:00:00Z"
  }
}
```

#### 3.1.5 删除项目

```
DELETE /api/v1/projects/{project_id}
```

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `permanent` | bool | 否 | 是否永久删除（放入回收站 vs 彻底删除），默认 `false` |

**响应示例**：

```json
{
  "code": 0,
  "message": "项目已删除",
  "data": null
}
```

#### 3.1.6 下载项目文件

```
GET /api/v1/projects/{project_id}/download
```

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_type` | string | 是 | 文件类型：`novel` / `script` / `meta` / `all`（打包为 zip） |

**响应**：
- `file_type=novel/script/meta`：返回文件内容（plain text / YAML）
- `file_type=all`：返回 ZIP 压缩包

---

### 3.2 转换系统（Conversion System）

#### 3.2.1 启动转换任务

```
POST /api/v1/projects/{project_id}/convert
```

**请求体**：

```json
{
  "steps": ["character_extract", "scene_split", "dialogue_parse", "emotion_tag", "yaml_generate"],
  "options": {
    "enable_sse": true,  // 是否使用 SSE 推送进度
    "skill_names": ["auto_format", "consistency_check"]
  }
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "转换任务已启动",
  "data": {
    "task_id": "task_20240605_120000",
    "sse_url": "/api/v1/convert/task_20240605_120000/progress"
  }
}
```

#### 3.2.2 获取转换进度（轮询备选方案）

```
GET /api/v1/convert/{task_id}/status
```

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_20240605_120000",
    "status": "running",  // pending | running | completed | failed | cancelled
    "current_step": 3,
    "total_steps": 5,
    "progress_percent": 60,
    "step_detail": "正在解析对白...",
    "started_at": "2024-06-05T12:00:00Z",
    "estimated_completion": "2024-06-05T12:05:00Z"
  }
}
```

#### 3.2.3 取消转换任务

```
POST /api/v1/convert/{task_id}/cancel
```

**响应示例**：

```json
{
  "code": 0,
  "message": "取消请求已发送",
  "data": null
}
```

---

### 3.3 编辑器系统（Editor System）

#### 3.3.1 获取小说原文

```
GET /api/v1/projects/{project_id}/novel
```

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "content": "小说原文内容...",
    "encoding": "utf-8",
    "line_count": 1234,
    "last_modified": "2024-06-05T14:30:00Z"
  }
}
```

#### 3.3.2 保存小说原文

```
PUT /api/v1/projects/{project_id}/novel
```

**请求体**：

```json
{
  "content": "更新后的小说原文...",
  "encoding": "utf-8"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "保存成功",
  "data": {
    "last_modified": "2024-06-05T15:00:00Z",
    "line_count": 1235
  }
}
```

#### 3.3.3 获取剧本 YAML

```
GET /api/v1/projects/{project_id}/script
```

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "yaml_content": "yaml版本内容...",
    "beat_count": 256,
    "last_modified": "2024-06-05T14:30:00Z"
  }
}
```

#### 3.3.4 保存剧本 YAML

```
PUT /api/v1/projects/{project_id}/script
```

**请求体**：

```json
{
  "yaml_content": "更新后的 YAML 内容...",
  "validate": true  // 是否校验 YAML 格式
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "保存成功",
  "data": {
    "last_modified": "2024-06-05T15:00:00Z",
    "beat_count": 257
  }
}
```

#### 3.3.5 校验 YAML 格式

```
POST /api/v1/projects/{project_id}/script/validate
```

**请求体**：

```json
{
  "yaml_content": "要校验的 YAML 内容..."
}
```

**响应示例**（成功）：

```json
{
  "code": 0,
  "message": "YAML 格式正确",
  "data": {
    "is_valid": true,
    "beat_count": 256
  }
}
```

**响应示例**（失败）：

```json
{
  "code": 40001,
  "message": "YAML 格式错误",
  "data": {
    "is_valid": false,
    "errors": [
      {
        "line": 42,
        "column": 15,
        "message": "missing required field: character"
      }
    ]
  }
}
```

---

### 3.4 Skill 管理系统（Skill Management）

#### 3.4.1 获取 Skill 列表

```
GET /api/v1/skills
```

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "skills": [
      {
        "name": "auto_format",
        "display_name": "自动格式化",
        "version": "1.0.0",
        "type": "builtin",  // builtin | user
        "description": "自动格式化 YAML 输出",
        "is_enabled": true
      }
    ]
  }
}
```

#### 3.4.2 启用/禁用 Skill

```
POST /api/v1/skills/{skill_name}/toggle
```

**请求体**：

```json
{
  "is_enabled": true
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Skill 已启用",
  "data": null
}
```

#### 3.4.3 安装用户 Skill

```
POST /api/v1/skills/install
```

**请求体**：

```
multipart/form-data:
  - skill_package: <上传的 .zip 或 .py 文件>
  - overwrite: true / false
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Skill 安装成功",
  "data": {
    "name": "my_custom_skill",
    "version": "1.0.0"
  }
}
```

#### 3.4.4 卸载 Skill

```
DELETE /api/v1/skills/{skill_name}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Skill 已卸载",
  "data": null
}
```

---

### 3.5 配置管理系统（Configuration Management）

#### 3.5.1 获取当前配置

```
GET /api/v1/config
```

**响应示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "model_name": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_base": "https://api.openai.com/v1",
    "language": "zh-CN",
    "theme": "dark"
  }
}
```

#### 3.5.2 更新配置

```
PUT /api/v1/config
```

**请求体**：

```json
{
  "model_name": "gpt-4",
  "temperature": 0.5
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "配置已更新",
  "data": null
}
```

#### 3.5.3 测试 LLM 连接

```
POST /api/v1/config/test-llm
```

**请求体**：

```json
{
  "model_name": "gpt-4o-mini",
  "api_key": "sk-...",  // 可选，使用当前配置的 API Key
  "api_base": "https://api.openai.com/v1"
}
```

**响应示例**（成功）：

```json
{
  "code": 0,
  "message": "LLM 连接测试成功",
  "data": {
    "model": "gpt-4o-mini",
    "response_time_ms": 1234
  }
}
```

**响应示例**（失败）：

```json
{
  "code": 50001,
  "message": "LLM 连接失败：API Key 无效",
  "data": null
}
```

---

## 4. SSE 端点设计

### 4.1 SSE 连接建立

```
GET /api/v1/convert/{task_id}/progress
```

**说明**：
- 返回 `Content-Type: text/event-stream`
- 支持跨域（CORS）和缓存控制（`Cache-Control: no-cache`）

### 4.2 SSE 事件类型

| 事件 | 触发时机 | 数据格式 | 示例 |
|------|---------|---------|------|
| `step_start` | 步骤开始 | `{step, total_steps, current}` | `{"step": "scene_split", "total_steps": 5, "current": 2}` |
| `step_progress` | 步骤内进度更新 | `{step, detail, percent}` | `{"step": "dialogue_parse", "detail": "已处理 100/256 个对白", "percent": 39}` |
| `step_complete` | 步骤完成 | `{step, result_summary}` | `{"step": "emotion_tag", "result_summary": "标注了 256 个 Beat 的情绪"}` |
| `step_error` | 步骤出错 | `{step, error}` | `{"step": "yaml_generate", "error": "LLM 输出格式错误"}` |
| `heartbeat` | 每 15 秒 | `{"ts": <timestamp>}` | `{"ts": 1717603200}` |
| `task_complete` | 任务完成 | `{result}` | `{"result": {"project_id": "...", "beat_count": 256}}` |
| `task_failed` | 任务失败 | `{error}` | `{"error": "LLM API 调用失败：429 Too Many Requests"}` |
| `task_cancelled` | 任务被取消 | `{reason}` | `{"reason": "用户取消"}` |
| `skill_start` | Skill 开始执行 | `{skill_name}` | `{"skill_name": "auto_format"}` |
| `skill_complete` | Skill 执行完成 | `{skill_name, result}` | `{"skill_name": "consistency_check", "result": "发现 3 处不一致"}` |
| `skill_error` | Skill 执行出错 | `{skill_name, error}` | `{"skill_name": "auto_format", "error": "Skill 执行超时"}` |
| `project_saved` | 项目保存成功 | `{project_id, file_type}` | `{"project_id": "...", "file_type": "script"}` |

### 4.3 SSE 前端监听示例

```javascript
const eventSource = new EventSource(`/api/v1/convert/${taskId}/progress`);

eventSource.addEventListener('step_start', (event) => {
  const data = JSON.parse(event.data);
  console.log(`开始步骤：${data.step} (${data.current}/${data.total_steps})`);
});

eventSource.addEventListener('step_progress', (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data.percent);
});

eventSource.addEventListener('task_complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('任务完成：', data.result);
  eventSource.close();
});

eventSource.addEventListener('heartbeat', (event) => {
  // 心跳事件，用于保持连接
  console.log('心跳：', JSON.parse(event.data).ts);
});

eventSource.onerror = (error) => {
  console.error('SSE 连接错误：', error);
  eventSource.close();
};
```

### 4.4 SSE 后端实现要点（质询修复 #2）

> **质询发现问题**：SSE 心跳机制可能不够可靠。网络中断后重连会丢失中间的事件。
> 
> **解决方案**：增加事件缓存机制，客户端重连时可以获取丢失的事件。

#### 4.4.1 SSE 事件管理器

```python
from collections import deque
from typing import Dict, List, Optional
import time
import json
import asyncio

class SSEManager:
    """SSE 事件管理器（含事件缓存）"""
    
    def __init__(self, max_cache_size: int = 100):
        self.clients: Dict[str, asyncio.Queue] = {}
        self.event_cache: deque = deque(maxlen=max_cache_size)
        self._lock = asyncio.Lock()
    
    async def push_event(self, task_id: str, event: dict) -> None:
        """推送事件给所有订阅该任务的客户端，并缓存"""
        # 缓存事件
        cached_event = {
            "task_id": task_id,
            "event": event,
            "ts": time.time()
        }
        
        async with self._lock:
            self.event_cache.append(cached_event)
            
            # 推送给所有客户端
            for client_id, queue in self.clients.items():
                if client_id.startswith(task_id):  # 简单匹配，实际应该用映射表
                    try:
                        await queue.put(event)
                    except Exception:
                        pass  # 忽略推送失败
    
    def get_cached_events(self, task_id: str, since_ts: float) -> List[dict]:
        """获取自某个时间戳以来的缓存事件"""
        events = []
        
        async with self._lock:
            for item in self.event_cache:
                if item["task_id"] == task_id and item["ts"] > since_ts:
                    events.append(item["event"])
        
        return events
    
    async def register_client(self, client_id: str, task_id: str) -> asyncio.Queue:
        """注册客户端，返回事件队列"""
        queue = asyncio.Queue()
        self.clients[client_id] = queue
        return queue
    
    async def unregister_client(self, client_id: str) -> None:
        """注销客户端"""
        if client_id in self.clients:
            del self.clients[client_id]


# 全局 SSE 管理器实例
sse_manager = SSEManager()
```

#### 4.4.2 SSE 端点实现（含事件缓存）

```python
from fastapi import APIRouter
from sse_starlette import EventSourceResponse
import asyncio
import time
import json

router = APIRouter()

@router.get("/convert/{task_id}/progress")
async def get_convert_progress(
    task_id: str,
    last_event_ts: float = 0.0  # 客户端传入上次收到事件的时间戳
):
    """
    SSE 端点：获取转换进度（含事件缓存）
    
    Args:
        task_id: 任务 ID
        last_event_ts: 上次收到事件的时间戳（用于重连时获取丢失的事件）
    """
    
    async def event_generator():
        # 1. 先推送缓存的事件（防止网络中断丢失事件）
        cached_events = sse_manager.get_cached_events(task_id, last_event_ts)
        
        for event in cached_events:
            yield event
        
        # 2. 然后继续推送新事件
        client_id = f"{task_id}_{int(time.time() * 1000)}"
        queue = await sse_manager.register_client(client_id, task_id)
        
        try:
            last_heartbeat = time.time()
            
            while True:
                # 等待新事件（超时 15 秒发送心跳）
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event
                except asyncio.TimeoutError:
                    # 发送心跳
                    heartbeat_event = {
                        "event": "heartbeat",
                        "data": json.dumps({"ts": time.time()})
                    }
                    yield heartbeat_event
                    
                    # 缓存心跳事件
                    await sse_manager.push_event(task_id, heartbeat_event)
        
        finally:
            # 清理客户端
            await sse_manager.unregister_client(client_id)
    
    return EventSourceResponse(event_generator())
```

#### 4.4.3 任务状态更新（推送事件）

```python
async def update_task_progress(task_id: str, step: str, detail: str, percent: float):
    """更新任务进度，并推送 SSE 事件"""
    
    # 更新任务状态
    task_status = await get_task_status(task_id)
    task_status.current_step = step
    task_status.step_detail = detail
    task_status.progress_percent = percent
    
    # 推送进度事件
    progress_event = {
        "event": "step_progress",
        "data": json.dumps({
            "step": step,
            "detail": detail,
            "percent": percent
        })
    }
    
    await sse_manager.push_event(task_id, progress_event)


async def complete_task(task_id: str, result: dict):
    """完成任务，并推送完成事件"""
    
    # 更新任务状态
    task_status = await get_task_status(task_id)
    task_status.status = "completed"
    task_status.result = result
    
    # 推送完成事件
    complete_event = {
        "event": "task_complete",
        "data": json.dumps({"result": result})
    }
    
    await sse_manager.push_event(task_id, complete_event)
```

#### 4.4.4 前端重连示例（含事件缓存）

```javascript
let eventSource = null;
let lastEventTs = 0;

function connectSSE(taskId) {
    // 传入上次收到事件的时间戳
    const url = `/api/v1/convert/${taskId}/progress?last_event_ts=${lastEventTs}`;
    
    eventSource = new EventSource(url);
    
    eventSource.addEventListener('step_progress', (event) => {
        const data = JSON.parse(event.data);
        updateProgressBar(data.percent);
        
        // 更新最后事件时间戳
        lastEventTs = Date.now() / 1000;
    });
    
    eventSource.addEventListener('heartbeat', (event) => {
        // 心跳事件，更新最后事件时间戳
        lastEventTs = JSON.parse(event.data).ts;
    });
    
    eventSource.addEventListener('task_complete', (event) => {
        const data = JSON.parse(event.data);
        console.log('任务完成：', data.result);
        eventSource.close();
    });
    
    eventSource.onerror = (error) => {
        console.error('SSE 连接错误：', error);
        
        // 自动重连（1 秒后）
        setTimeout(() => {
            console.log('正在重连...');
            connectSSE(taskId);
        }, 1000);
    };
}

// 开始连接
connectSSE('task_20240605_120000');
```

---

## 5. 错误码规范

### 5.1 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "code": 40001,
  "message": "错误描述信息",
  "data": {
    "field": "详细错误信息"
  }
}
```

### 5.2 错误码分段

| 错误码范围 | 类别 | 说明 |
|-----------|------|------|
| **0** | 成功 | 所有成功响应 |
| **400xx** | 客户端错误（请求错误） | 4xx HTTP 状态码对应 |
| **500xx** | 服务端错误 | 5xx HTTP 状态码对应 |

### 5.3 详细错误码表

#### 5.3.1 客户端错误（4xx）

| 错误码 | HTTP 状态码 | 说明 | 处理建议 |
|--------|------------|------|---------|
| **40000** | 400 | 请求参数错误 | 检查请求体格式和字段类型 |
| **40001** | 400 | YAML 格式错误 | 检查 YAML 语法和必填字段 |
| **40002** | 400 | 文件格式不支持 | 仅支持 TXT/MD 格式 |
| **40003** | 400 | 项目 name 已存在 | 使用其他项目名称 |
| **40100** | 401 | 未授权（未来 V2） | 登录后重试 |
| **40300** | 403 | 无权限（未来 V2） | 联系管理员 |
| **40400** | 404 | 项目不存在 | 检查 `project_id` |
| **40401** | 404 | 任务不存在 | 检查 `task_id` |
| **40402** | 404 | Skill 不存在 | 检查 `skill_name` |
| **40900** | 409 | 项目名冲突 | 使用其他项目名称 |
| **41300** | 413 | 文件太大 | 文件大小超过限制（默认 10MB） |
| **42900** | 429 | 请求频率过高 | 降低请求频率，等待后重试 |

#### 5.3.2 服务端错误（5xx）

| 错误码 | HTTP 状态码 | 说明 | 处理建议 |
|--------|------------|------|---------|
| **50000** | 500 | 内部服务器错误 | 联系开发者 |
| **50001** | 500 | LLM API 调用失败 | 检查 API Key 和网络连接 |
| **50002** | 500 | LLM 输出格式错误 | 系统将自动重试 |
| **50003** | 500 | 文件读写失败 | 检查磁盘空间和文件权限 |
| **50004** | 500 | Skill 执行失败 | 检查 Skill 代码 |
| **50300** | 503 | 服务不可用 | 服务正在重启，请稍后重试 |
| **50400** | 504 | LLM API 超时 | 增加超时时间或重试 |

### 5.4 错误码使用示例

**示例 1：YAML 格式错误**

```json
{
  "code": 40001,
  "message": "YAML 格式错误",
  "data": {
    "errors": [
      {
        "line": 42,
        "column": 15,
        "message": "missing required field: character"
      }
    ]
  }
}
```

**示例 2：LLM API 调用失败**

```json
{
  "code": 50001,
  "message": "LLM API 调用失败：429 Too Many Requests",
  "data": {
    "llm_error": {
      "status_code": 429,
      "error_type": "rate_limit_exceeded",
      "retry_after": 30
    }
  }
}
```

---

## 6. 认证与授权

### 6.1 V1 版本（无认证）

V1 版本为单机版，无多用户，因此**不需要认证**。

**安全措施**：
1. **本地访问限制**：默认绑定 `127.0.0.1`，不允许远程访问
2. **API Key 加密存储**：使用 `cryptography (Fernet)` 加密后存储在配置文件中
3. **Skill 沙箱**（未来 V2）：限制 Skill 的文件系统访问权限

### 6.2 V2 版本（未来扩展）

V2 版本若支持云端部署，将引入：
- **JWT Token 认证**
- **OAuth 2.0 集成**
- **RBAC 权限控制**

---

## 7. 请求/响应格式规范

### 7.1 请求头规范

| 请求头 | 说明 | 示例 |
|--------|------|------|
| `Content-Type` | 请求体格式 | `application/json` 或 `multipart/form-data` |
| `Accept` | 期望的响应格式 | `application/json` |
| `X-Request-ID` | 请求追踪 ID（可选） | `req_20240605_120000` |

### 7.2 响应头规范

| 响应头 | 说明 | 示例 |
|--------|------|------|
| `Content-Type` | 响应体格式 | `application/json` 或 `text/event-stream` |
| `X-Request-ID` | 回显请求 ID | `req_20240605_120000` |
| `Cache-Control` | 缓存控制（SSE） | `no-cache` |

### 7.3 时间格式规范

所有时间字段使用 **ISO 8601** 格式：

```
2024-06-05T12:00:00Z       # UTC 时间
2024-06-05T20:00:00+08:00  # 北京时间（UTC+8）
```

### 7.4 分页规范

列表接口统一使用 **page + page_size** 分页：

**请求参数**：
- `page`：页码，从 1 开始
- `page_size`：每页数量，默认 20，最大 100

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

---

## 8. API 端点详细说明

### 8.1 项目管理系统

#### 8.1.1 获取项目列表

```
GET /api/v1/projects
```

**功能**：获取当前用户的所有项目（分页）

**权限**：无需认证（V1 单机版）

**请求参数**：见 [3.1.1](#311-获取项目列表)

**响应**：见 [3.1.1](#311-获取项目列表)

**cURL 示例**：

```bash
curl -X GET "http://localhost:8000/api/v1/projects?page=1&page_size=20" \
  -H "Accept: application/json"
```

---

#### 8.1.2 创建项目

```
POST /api/v1/projects
```

**功能**：创建新项目（上传小说文件或提供文本内容）

**权限**：无需认证

**请求体**：见 [3.1.2](#312-创建项目)

**响应**：见 [3.1.2](#312-创建项目)

**cURL 示例**（JSON 方式）：

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "我的小说",
    "novel_content": "小说内容...",
    "config": {
      "model_name": "gpt-4o-mini"
    }
  }'
```

**cURL 示例**（文件上传方式）：

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Accept: application/json" \
  -F "name=我的小说" \
  -F "novel_file=@novel.txt" \
  -F "config={\"model_name\": \"gpt-4o-mini\"}"
```

---

### 8.2 转换系统

#### 8.2.1 启动转换任务

```
POST /api/v1/projects/{project_id}/convert
```

**功能**：启动 Pipeline 转换任务

**权限**：无需认证

**请求体**：见 [3.2.1](#321-启动转换任务)

**响应**：见 [3.2.1](#321-启动转换任务)

**SSE 进度推送**：
- 如果请求体中 `enable_sse=true`，前端应连接 `sse_url` 接收实时进度
- 如果 `enable_sse=false`，前端可以轮询 [3.2.2](#322-获取转换进度轮询备选方案) 接口

**cURL 示例**：

```bash
curl -X POST "http://localhost:8000/api/v1/projects/proj_20240605_120000/convert" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "steps": ["character_extract", "scene_split", "dialogue_parse", "emotion_tag", "yaml_generate"],
    "options": {
      "enable_sse": true,
      "skill_names": ["auto_format"]
    }
  }'
```

---

## 9. 附录

### 9.1 完整 API 端点汇总

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/api/v1/projects` | 获取项目列表 | ❌ |
| POST | `/api/v1/projects` | 创建项目 | ❌ |
| GET | `/api/v1/projects/{project_id}` | 获取项目详情 | ❌ |
| PUT | `/api/v1/projects/{project_id}` | 更新项目 | ❌ |
| DELETE | `/api/v1/projects/{project_id}` | 删除项目 | ❌ |
| GET | `/api/v1/projects/{project_id}/download` | 下载项目文件 | ❌ |
| POST | `/api/v1/projects/{project_id}/convert` | 启动转换任务 | ❌ |
| GET | `/api/v1/convert/{task_id}/status` | 获取转换进度（轮询） | ❌ |
| GET | `/api/v1/convert/{task_id}/progress` | 获取转换进度（SSE） | ❌ |
| POST | `/api/v1/convert/{task_id}/cancel` | 取消转换任务 | ❌ |
| GET | `/api/v1/projects/{project_id}/novel` | 获取小说原文 | ❌ |
| PUT | `/api/v1/projects/{project_id}/novel` | 保存小说原文 | ❌ |
| GET | `/api/v1/projects/{project_id}/script` | 获取剧本 YAML | ❌ |
| PUT | `/api/v1/projects/{project_id}/script` | 保存剧本 YAML | ❌ |
| POST | `/api/v1/projects/{project_id}/script/validate` | 校验 YAML 格式 | ❌ |
| GET | `/api/v1/skills` | 获取 Skill 列表 | ❌ |
| POST | `/api/v1/skills/{skill_name}/toggle` | 启用/禁用 Skill | ❌ |
| POST | `/api/v1/skills/install` | 安装用户 Skill | ❌ |
| DELETE | `/api/v1/skills/{skill_name}` | 卸载 Skill | ❌ |
| GET | `/api/v1/config` | 获取当前配置 | ❌ |
| PUT | `/api/v1/config` | 更新配置 | ❌ |
| POST | `/api/v1/config/test-llm` | 测试 LLM 连接 | ❌ |

### 9.2 OpenAPI 文档生成

FastAPI 会自动生成 OpenAPI 文档，访问以下地址查看：

- **Swagger UI**：`http://localhost:8000/docs`
- **ReDoc**：`http://localhost:8000/redoc`
- **OpenAPI JSON**：`http://localhost:8000/openapi.json`

### 9.3 Postman Collection

可以导入 `docs/postman_collection.json` 快速测试 API（由开发者提供）。

---

## 10. 总结

本文档详细设计了 InkScript V1 版本的所有 API 接口，包括：

1. ✅ **RESTful API 端点**：覆盖项目管理、转换、编辑、Skill、配置等 5 大系统
2. ✅ **SSE 端点**：实现实时进度推送，包含 12 种事件类型
3. ✅ **错误码规范**：统一定义客户端错误（4xx）和服务端错误（5xx）
4. ✅ **请求/响应格式规范**：时间格式、分页、请求头、响应头

**下一步**：
- 根据本文档实现后端 API
- 前端集成 API
- 编写测试用例

---

**文档状态**：✅ 已完成，待用户确认

**最后更新**：2026-06-06
