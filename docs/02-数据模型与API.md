# InkScript 数据模型与 API 设计文档

> **版本**：V3 | **更新**：2026-06-08 | **依据**：实际代码

---

## 一、数据模型（Pydantic V2）

### 1.1 核心实体层级

```
Script (根对象)
├── meta: ScriptMeta           ← 元数据 + 统计信息
├── characters: list[Character] ← 角色列表
└── scenes: list[Scene]         ← 场景列表
    ├── scene_id, title, location, time
    └── beats: list[Beat]       ← Tagged Union
        ├── DialogueBeat  (type="dialogue")
        ├── ActionBeat    (type="action")
        └── NarrationBeat (type="narration")
```

### 1.2 完整模型定义

| 类名 | 字段 | 说明 |
|------|------|------|
| `BeatType` | `DIALOGUE="dialogue"`, `ACTION="action"`, `NARRATION="narration"` | 枚举常量 |
| `SourceLocation` | `chapter_index:int`, `start_paragraph:int`, `end_paragraph:int`, `start_offset:int`, `end_offset:int` | 原文位置映射（滚动联动用） |
| `DialogueBeat` | `type="dialogue"`, `character:str`, `content:str`, `emotion:str?`, `source_location?` | 对白 Beat |
| `ActionBeat` | `type="action"`, `content:str`, `duration:float?`, `source_location?` | 动作 Beat（含镜头指示） |
| `NarrationBeat` | `type="narration"`, `content:str`, `speaker:str?`, `source_location?` | 旁白 Beat |
| `Beat` | `DialogueBeat \| ActionBeat \| NarrationBeat` | Tagged Union |
| `Character` | `name:str`, `aliases:list[str]`, `description:str`, `emotion_distribution:dict` | 角色 |
| `Scene` | `scene_id:int`, `title:str`, `location:str`, `time:str`, `beats:list[Beat]` | 场景 |
| `ScriptMeta` | `version`, `generated_at`, `model_name`, `total_beats`, `dialogue_count`, `action_count`, `narration_count`, `characters:list[str]` | 剧本元数据 |
| `Script` | `meta:ScriptMeta`, `characters:list[Character]`, `scenes:list[Scene]` | 完整剧本 |
| `EditMeta` | `novel_scroll_top`, `script_scroll_top`, `left_panel_visible`, `right_panel_visible`, `operation_log:list[OperationLog]` | 编辑器状态 |
| `OperationLog` | `timestamp`, `action`, `beat_id?`, `field?`, `old_value?`, `new_value?` | 操作历史 |

### 1.3 辅助函数

```python
to_yaml(script: Script) -> str    # Script → YAML 字符串
from_yaml(yaml_str: str) -> Script # YAML 字符串 → Script
```

---

## 二、API 完整参考

### 2.1 约定

- **Base URL**: `http://127.0.0.1:{port}/api/v1`
- **响应格式**: `{"code": 0, "data": {...}, "message": "..."}`
- **错误格式**: `{"code": -1, "message": "错误描述"}`
- **SSE 端点**: `GET /convert/{task_id}/sse` 返回 `text/event-stream`

### 2.2 项目管理 (`/projects`) — 29 个端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/projects` | 列出所有项目（支持 search/sort_by/order） |
| `POST` | `/projects` | 创建项目 `{name: str}` |
| `GET` | `/projects/{id}` | 获取项目详情 |
| `PUT` | `/projects/{id}` | 更新项目名称 `{name?: str}` |
| `DELETE` | `/projects/{id}` | 删除项目（软删除到回收站） |
| `GET` | `/projects/trash` | 列出回收站项目 |
| `POST` | `/projects/trash/{id}/restore` | 从回收站恢复 |
| `DELETE` | `/projects/trash/{id}` | 永久删除 |
| `GET` | `/projects/{id}/novel` | 读取小说原文 |
| `PUT` | `/projects/{id}/novel` | 保存小说原文 `{content: str}` |
| `GET` | `/projects/{id}/script` | 读取剧本 YAML |
| `PUT` | `/projects/{id}/script` | 保存剧本 YAML `{yaml: str}` |
| `GET` | `/projects/{id}/download` | 下载项目文件 |
| `GET` | `/projects/{id}/versions` | 列出版本快照 |
| `GET` | `/projects/{id}/versions/{vid}` | 获取指定版本 |
| `POST` | `/projects/{id}/versions/{vid}/rollback` | 回滚到指定版本 |
| `POST` | `/projects/{id}/novel-snapshot` | 创建小说快照 `{description?: str}` |
| `GET` | `/projects/{id}/config-snapshot` | 查看项目配置快照 |
| `POST` | `/projects/{id}/config-snapshot` | 保存项目配置快照 `{config: dict}` |
| `GET` | `/projects/{id}/operations` | 列出操作日志 |
| `POST` | `/projects/{id}/operations` | 添加操作日志 `{action, beat_id?, ...}` |
| `DELETE` | `/projects/{id}/operations` | 清空操作日志 |
| `GET` | `/projects/{id}/characters` | 获取角色列表（从 Script 解析） |
| `GET` | `/projects/{id}/edit-meta` | 获取编辑器元数据 |
| `PUT` | `/projects/{id}/edit-meta` | 更新编辑器元数据 |
| `POST` | `/projects/{id}/import-file` | 导入文件（支持 .txt/.docx/.pdf） |
| `GET` | `/projects/{id}/files` | 列出项目文件 |
| `GET` | `/projects/{id}/files/download?file_path=...` | 下载项目文件 |

### 2.3 转换任务 (`/convert`) — 2 个端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/convert/{project_id}` | 启动转换任务 `{mode?: "ai"\|"local"}`，返回 `{task_id}` |
| `GET` | `/convert/{task_id}/sse` | SSE 事件流，接收实时进度 |

**SSE 事件类型**：

| 事件 | data 内容 | 触发时机 |
|------|----------|---------|
| `step_start` | `{step, message}` | 每步开始前 |
| `step_complete` | `{step, message, percent}` | 每步完成后 |
| `warning` | `{message}` | 质量警告（如未识别到角色） |
| `task_complete` | `{message, result}` | 全部完成 |
| `task_failed` | `{message, error}` | 转换失败 |

### 2.4 配置管理 (`/config`) — 3 个端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/config` | 获取当前配置（不含 API Key） |
| `PUT` | `/config` | 更新配置 `{provider, base_url, api_key, model_name, temperature, max_tokens, ...}` |
| `POST` | `/config/test` | 测试 API 连接 `{base_url, api_key, model_name}` |

### 2.5 Skills 管理 (`/skills`) — 9 个端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/skills` | 列出所有 Skills（返回 `{builtin:[], user:[]}`） |
| `GET` | `/skills/{name}` | 获取 Skill 详情 |
| `POST` | `/skills/{name}/enable` | 启用/禁用 Skill `{enabled: bool}` |
| `POST` | `/skills/{name}/priority` | 更新优先级 `{priority: int}` |
| `POST` | `/skills/{name}/run` | 运行 Skill `{project_id, yaml_content}` |
| `GET` | `/skills/{name}/errors` | 获取 Skill 错误日志 |
| `POST` | `/skills` | 创建用户 Skill `{name, description, prompt}` |
| `POST` | `/skills/install` | 安装 Skill `{path}` |
| `DELETE` | `/skills/{name}` | 删除用户 Skill |

---

## 三、API 调用示例

### 启动转换
```bash
POST /api/v1/convert/{project_id}
→ {"code":0, "data":{"task_id":"task_xxx"}}
```

### 监听进度（SSE）
```javascript
const es = new EventSource(`/api/v1/convert/${taskId}/sse`);
es.addEventListener('step_complete', e => {
  const d = JSON.parse(e.data);
  console.log(`${d.step}: ${d.percent}%`);
});
```

### 运行 Skill
```bash
POST /api/v1/skills/character-analysis/run
Body: {"project_id":"proj_xxx", "yaml_content":"..."}
→ {"code":0, "data":{"skill_name":"character-analysis", "result":{...}}}
```

---

## 四、数据流总览

```
用户输入小说
  ↓ PUT /projects/{id}/novel
project_store.save_novel() → novel.txt
  ↓ POST /convert/{id}
Pipeline.run(script, novel_text)
  ├── text_splitter     [AI]
  ├── character_extractor [AI]
  ├── scene_splitter    [AI]
  ├── dialogue_parser   [AI] → 3种beat
  ├── emotion_tagger    [AI]
  └── yaml_generator    [本地]
  ↓
store.save_script() → script.yaml
  ├── script_to_txt()    → script.txt    [本地]
  ├── script_to_html()   → script.html   [本地]
  └── script_to_fountain() → script.fountain [本地]
  ↓
GET /projects/{id}/script → 前端编辑器展示
```
