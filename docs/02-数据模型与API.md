# InkScript 数据模型与 API 设计文档

> 版本：V2 | 日期：2026-06-07 | 状态：与代码同步
> 本文档合并自：data-model-design.md、api-design.md、yaml-schema.md
> 核心原则：**类型安全、可扩展、以代码为准**

---

## 目录

1. [数据模型设计](#1-数据模型设计)
2. [API 设计](#2-api-设计)
3. [YAML Schema 设计](#3-yaml-schema-设计)
4. [错误处理](#4-错误处理)
5. [附录](#5-附录)

---

## 1. 数据模型设计

### 1.1 设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **类型安全** | 使用 Pydantic V2 提供运行时类型校验 | `Beat = Union[DialogueBeat, ActionBeat, NarrationBeat]` |
| **可扩展性** | 使用 `model_config = {"extra": "ignore"}` 支持向前兼容 | V1 可以解析 V2 生成的 YAML |
| **可校验性** | 导出 JSON Schema 供前端 CodeMirror 校验 | `Script.model_json_schema()` |
| **可序列化** | 支持 YAML / JSON 双向序列化 | `PyYAML` + Pydantic `.model_dump()` |
| **向后兼容** | 新增字段使用 `Optional` + 默认值 | `emotion: str | None = None` |

### 1.2 核心数据模型

#### 1.2.1 Beat 联合类型（核心）

```python
# schema.py

from pydantic import BaseModel, Field
from typing import Literal, Union
from enum import Enum

class BeatType(str, Enum):
    DIALOGUE = "dialogue"
    ACTION = "action"
    NARRATION = "narration"

class BaseBeat(BaseModel):
    """所有 Beat 的基类"""
    model_config = {"extra": "forbid"}
    
    source_location: dict | None = Field(
        None,
        description="原文定位：chapter_index + paragraph range + offset"
    )

class DialogueBeat(BaseBeat):
    """对白 Beat：角色说话内容"""
    
    type: Literal["dialogue"] = "dialogue"
    character: str = Field(..., description="角色名称，必须存在于角色列表中")
    content: str = Field(..., description="对白内容")
    emotion: str | None = Field(None, description="情绪标签（可选）")
    
    # V1 扩展字段（可选）
    volume: str | None = Field(None, description="音量：whisper | normal | shout")
    speed: str | None = Field(None, description="语速：slow | normal | fast")

class ActionBeat(BaseBeat):
    """动作 Beat：描述动作、表情、场景变化"""
    
    type: Literal["action"] = "action"
    content: str = Field(..., description="动作描述")
    duration: float | None = Field(None, description="预估持续时间（秒）")

class NarrationBeat(BaseBeat):
    """旁白 Beat：描述场景、氛围、心理活动"""
    
    type: Literal["narration"] = "narration"
    content: str = Field(..., description="旁白内容")
    speaker: str | None = Field(None, description="旁白配音角色（可选）")

# Beat 联合类型（简化版，不使用 Tagged Union）
Beat = Union[DialogueBeat, ActionBeat, NarrationBeat]
```

> **⚠️ 代码修正说明**：实际代码中使用简单的 `Union` 而不是 Pydantic V2 的 `Annotated[Union[..., Tag("...")], Discriminator("type")]`。以代码为准。

#### 1.2.2 场景模型

```python
# schema.py

class Scene(BaseModel):
    """场景信息"""
    
    model_config = {"extra": "ignore"}
    
    scene_id: int = Field(..., description="场景编号（从 1 开始）")
    title: str = Field("", description="场景标题")
    location: str = Field("", description="场景地点")
    time: str = Field("", description="场景时间")
    beats: list[Beat] = Field(default_factory=list, description="场景内的 Beat 列表")
```

#### 1.2.3 角色模型

```python
# schema.py

class Character(BaseModel):
    """角色信息"""
    
    model_config = {"extra": "ignore"}
    
    name: str = Field(..., description="角色名称")
    aliases: list[str] = Field(default_factory=list, description="别名列表")
    description: str = Field("", description="角色描述")
    voice_profile: str | None = Field(None, description="声音配置（TTS 用）")
    emotion_distribution: dict[str, float] = Field(
        default_factory=dict,
        description="情绪分布（用于雷达图）：happy/sad/angry/calm/excited/fear -> 0.0-1.0"
    )
```

#### 1.2.4 剧本元数据模型

```python
# schema.py

class ScriptMeta(BaseModel):
    """剧本元数据（向前兼容）"""
    
    
    model_config = {"extra": "ignore"}  # 忽略额外字段
    
    version: str = "1.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_name: str = ""  # 使用的 LLM 模型
    source_location_enabled: bool = True  # 是否包含 source_location
    
    # 统计信息
    total_beats: int = 0
    dialogue_count: int = 0
    action_count: int = 0
    narration_count: int = 0
    
    # 角色列表（去重）
    characters: list[str] = Field(default_factory=list)
    
    def model_post_init(self):
        """初始化后处理"""
        # 确保 characters 去重
        self.characters = list(set(self.characters))
```

#### 1.2.5 完整剧本模型

```python
# schema.py

class Script(BaseModel):
    """完整剧本（YAML 根对象）"""
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
    
    meta: ScriptMeta = Field(default_factory=ScriptMeta)
    characters: list[Character] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    
    def add_beat(self, scene_id: int, beat: Beat) -> None:
        """添加 Beat（自动更新统计）"""
        if scene_id < 1 or scene_id > len(self.scenes):
            raise ValueError(f"场景 ID {scene_id} 无效")
            
        self.scenes[scene_id - 1].beats.append(beat)
        self.meta.total_beats += 1
            
        if isinstance(beat, DialogueBeat):
            self.meta.dialogue_count += 1
        elif isinstance(beat, ActionBeat):
            self.meta.action_count += 1
        elif isinstance(beat, NarrationBeat):
            self.meta.narration_count += 1
            
        # 更新角色列表
        if isinstance(beat, DialogueBeat):
            if beat.character not in self.meta.characters:
                self.meta.characters.append(beat.character)
    
    def validate_characters(self, valid_characters: list[str]) -> list[str]:
        """校验所有对白 Beat 的角色是否在有效角色列表中"""
        errors = []
        for i, beat in enumerate(self.beats):
            if isinstance(beat, DialogueBeat):
                if beat.character not in valid_characters:
                    errors.append(f"Beat {i}: 角色 '{beat.character}' 未定义")
        return errors
    
    @property
    def beats(self) -> list[Beat]:
        """获取所有 Beat（扁平化）"""
        result = []
        for scene in self.scenes:
            result.extend(scene.beats)
        return result
```

#### 1.2.6 编辑元数据模型

```python
# schema.py

class OperationLog(BaseModel):
    """操作日志：记录每次编辑操作（用于逐句修改历史）"""
    
    model_config = {"extra": "forbid"}
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="操作时间")
    user: str = Field("user", description="操作用户（预留多人协作）")
    action: str = Field(..., description="操作类型：create_beat | update_beat | delete_beat | update_novel")
    beat_id: str | None = Field(None, description="关联的 Beat ID（如果是 Beat 操作）")
    field: str | None = Field(None, description="修改的字段名（如 character, content, emotion）")
    old_value: str | None = Field(None, description="修改前的值")
    new_value: str | None = Field(None, description="修改后的值")
    scene_id: str | None = Field(None, description="关联的场景 ID")

class EditMeta(BaseModel):
    """编辑器元数据：保存用户编辑器的滚动位置、展开状态等"""
    
    model_config = {"extra": "ignore"}
    
    # 编辑器滚动位置
    novel_scroll_top: float = Field(0.0, description="小说编辑器滚动位置")
    script_scroll_top: float = Field(0.0, description="剧本编辑器滚动位置")
    
    # 光标位置
    novel_cursor_pos: int | None = Field(None, description="小说编辑器光标位置")
    script_cursor_pos: int | None = Field(None, description="剧本编辑器光标位置")
    
    # UI 状态
    left_panel_visible: bool = Field(True, description="左面板是否可见")
    right_panel_visible: bool = Field(True, description="右面板是否可见")
    panel_ratio: float = Field(50.0, description="左右分栏比例（左侧占比%）")
    
    # 当前激活的面板
    active_panel: str = Field("novel", description="当前激活的面板（novel/script）")
    
    # 展开/折叠状态
    guide_expanded: bool = Field(True, description="使用指南是否展开")
    version_panel_visible: bool = Field(False, description="版本历史面板是否可见")
    skill_panel_visible: bool = Field(False, description="Skill 面板是否可见")
    
    # 操作日志（逐句修改历史）
    operation_log: list[OperationLog] = Field(default_factory=list)
    
    # 最后更新时间
    last_updated: datetime | None = Field(None, description="最后更新时间")
```

### 1.3 配置模型

```python
# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError
from pathlib import Path
from typing import Optional
import json
import base64
from cryptography.fernet import Fernet

class AppConfig(BaseSettings):
    """应用配置（支持环境变量、.env、JSON 文件）"""
    
    model_config = SettingsConfigDict(
        env_prefix="INKSCRIPT_",
        env_file=".env",
        extra="ignore",
    )
    
    # 基础配置
    app_name: str = "InkScript"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # LLM 配置
    llm_provider: str = "openai"  # openai, deepseek, anthropic, qwen, gemini, custom
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""  # 加密存储
    llm_model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(0.7, ge=0.0, le=2.0)
    llm_top_p: float = Field(1.0, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(4096, ge=1)
    llm_frequency_penalty: float = Field(0.0, ge=0.0, le=2.0)
    llm_presence_penalty: float = Field(0.0, ge=0.0, le=2.0)
    llm_request_timeout: float = Field(60.0, ge=1.0)
    llm_max_retries: int = Field(3, ge=0)
    llm_request_interval: float = Field(0.5, ge=0.0)
    
    # 项目配置
    projects_dir: Path = Path.home() / ".novel2script" / "projects"
    max_novel_length: int = Field(100_000, ge=1000)
    
    # 服务器配置
    host: str = "127.0.0.1"
    port: int = Field(8000, ge=1024, le=65535)
    sse_heartbeat_interval: int = Field(15, ge=5, le=60)
    
    # 日志配置
    log_level: str = "INFO"
    
    def encrypt_api_key(self) -> str:
        """加密 API Key（使用 cryptography.fernet）"""
        from cryptography.fernet import Fernet
        import base64
        
        key = self._get_or_create_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(self.llm_api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密 API Key"""
        from cryptography.fernet import Fernet
        import base64
        
        key = self._get_or_create_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(base64.urlsafe_b64decode(encrypted_key))
        return decrypted.decode()
    
    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        import base64
        from pathlib import Path
        
        key_file = Path.home() / ".novel2script" / ".key"
        if key_file.exists():
            return base64.urlsafe_b64decode(key_file.read_text())
        else:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_text(base64.urlsafe_b64encode(key).decode())
            key_file.chmod(0o600)  # 只有用户可读写
            return key
    
    @field_validator("llm_base_url")
    @classmethod
    def validate_llm_base_url(cls, v: str) -> str:
        if not v.startswith("http"):
            raise ValueError("llm_base_url 必须是有效的 URL")
        return v.rstrip("/")
```

---

## 2. API 设计

### 2.1 API 设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **RESTful 风格** | 使用标准 HTTP 方法，资源命名清晰 | `GET /api/v1/projects`（获取项目列表） |
| **版本化** | 所有 API 带版本前缀，便于未来演进 | `/api/v1/...`, `/api/v2/...` |
| **SSE 优先** | 长时间任务使用 SSE 推送进度，避免轮询 | `GET /api/v1/convert/{task_id}/progress` |
| **类型安全** | 使用 Pydantic 模型定义请求/响应，自动生成 OpenAPI 文档 | 见各端点定义 |
| **错误标准化** | 统一错误响应格式，便于前端处理 | 见 [4. 错误处理](#4-错误处理) |

### 2.2 实际 API 端点（比文档更丰富）

#### 2.2.1 项目管理 API（`/api/v1/projects`）

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/` | 列表项目（支持搜索和排序） | ✅ 已实现 |
| POST | `/` | 创建项目 | ✅ 已实现 |
| GET | `/{project_id}` | 获取项目详情 | ✅ 已实现 |
| PUT | `/{project_id}` | 更新项目 | ✅ 已实现 |
| DELETE | `/{project_id}` | 删除项目（支持软删除） | ✅ 已实现 |
| GET | `/trash` | 列出回收站 | ✅ 已实现 |
| POST | `/trash/{project_id}/restore` | 从回收站恢复 | ✅ 已实现 |
| DELETE | `/trash/{project_id}` | 从回收站永久删除 | ✅ 已实现 |
| GET | `/{project_id}/novel` | 获取小说原文 | ✅ 已实现 |
| PUT | `/{project_id}/novel` | 保存小说原文 | ✅ 已实现 |
| GET | `/{project_id}/script` | 获取剧本 YAML | ✅ 已实现 |
| PUT | `/{project_id}/script` | 保存剧本 YAML | ✅ 已实现 |
| GET | `/{project_id}/download` | 下载项目文件 | ✅ 已实现 |
| GET | `/{project_id}/versions` | 列出版本历史 | ✅ 已实现 |
| GET | `/{project_id}/versions/{version_id}` | 获取版本详情 | ✅ 已实现 |
| POST | `/{project_id}/novel-snapshot` | 创建小说原文快照 | ✅ 已实现 |
| POST | `/{project_id}/versions/{version_id}/rollback` | 回滚到指定版本 | ✅ 已实现 |
| GET | `/{project_id}/config-snapshot` | 获取配置快照 | ✅ 已实现 |
| POST | `/{project_id}/config-snapshot` | 保存配置快照 | ✅ 已实现 |
| GET | `/{project_id}/operations` | 列出操作日志 | ✅ 已实现 |
| POST | `/{project_id}/operations` | 添加操作日志 | ✅ 已实现 |
| DELETE | `/{project_id}/operations` | 清空操作日志 | ✅ 已实现 |
| GET | `/{project_id}/edit-meta` | 获取编辑器元数据 | ✅ 已实现 |
| PUT | `/{project_id}/edit-meta` | 更新编辑器元数据 | ✅ 已实现 |

#### 2.2.2 转换 API（`/api/v1/convert`）

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| POST | `/{project_id}` | 启动转换任务 | ✅ 已实现 |
| GET | `/{task_id}/sse` | 获取 SSE 事件流 | ✅ 已实现 |

#### 2.2.3 配置 API（`/api/v1/config`）

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/` | 获取当前配置（api_key 脱敏） | ✅ 已实现 |
| PUT | `/` | 更新配置（支持加密 API Key） | ✅ 已实现 |
| POST | `/test` | 测试 API 连接 | ✅ 已实现 |

#### 2.2.4 Skill API（`/api/v1/skills`）

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/` | 列出所有 Skill | ✅ 已实现 |
| GET | `/{skill_name}` | 获取 Skill 详情 | ✅ 已实现 |
| POST | `/{skill_name}/enable` | 启用/禁用 Skill | ✅ 已实现 |
| POST | `/{skill_name}/priority` | 更新 Skill 优先级 | ✅ 已实现 |
| POST | `/{skill_name}/run` | 运行 Skill | ✅ 已实现 |
| GET | `/{skill_name}/errors` | 获取 Skill 错误日志 | ✅ 已实现 |
| POST | `/` | 创建用户自定义 Skill | ✅ 已实现 |
| POST | `/install` | 从本地路径安装 Skill | ✅ 已实现 |
| DELETE | `/{skill_name}` | 删除用户自定义 Skill | ✅ 已实现 |

### 2.3 API 端点详细说明

#### 2.3.1 创建项目

```
POST /api/v1/projects
```

**请求体**：

```json
{
  "name": "我的小说",
  "novel_text": "小说内容...",  // 或者直接上传文件，见下方说明
  "config": {
    "model_name": "gpt-4o-mini",
    "temperature": 0.7
  }
}
```

**说明**：
- 支持两种上传方式：
  1. `multipart/form-data`：上传 `novel_file`（TXT/MD）
  2. `application/json`：在 `novel_text` 字段中提供文本内容

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

#### 2.3.2 启动转换任务

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
    "sse_url": "/api/v1/convert/task_20240605_120000/sse"
  }
}
```

#### 2.3.3 获取 SSE 进度推送

```
GET /api/v1/convert/{task_id}/sse
```

**说明**：
- 返回 `Content-Type: text/event-stream`
- 支持跨域（CORS）和缓存控制（`Cache-Control: no-cache`）

**SSE 事件类型**：

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
| `skill_error` | Skill 执行出错 | `{skill_name, error}` | `{"skill_name": "auto_format", "error": "Skill 执行超时"}` |

**前端监听示例**：

```javascript
const eventSource = new EventSource(`/api/v1/convert/${taskId}/sse`);

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

---

## 3. YAML Schema 设计

### 3.1 设计目标与使用场景

本 Schema 定义了「AI 小说转剧本工具」的输出格式规范。核心使用场景为：

1. **AI 自动转换**：将 3 章以上的小说文本自动解析为结构化剧本 YAML，作为初稿输出
2. **作者手工编辑**：作者拿到 YAML 初稿后，用任意文本编辑器即可阅读和修改，无需专业软件
3. **下游消费**：YAML 可被其他工具链读取，导入到 Final Draft、排版系统、拍摄计划工具等

设计目标不是替代 Fountain 或 FDX 等专业剧本格式，而是补足**小说→剧本的中间态**——既保留小说的丰富信息（别名映射、旁白、心理描写），又具备剧本的结构化表达能力。

### 3.2 设计原则

| 原则 | 说明 |
|------|------|
| **作者友好** | YAML 缩进表示层级，字段名自解释，避免过度嵌套（最深 4 层），作者用 VSCode / Vim 即可编辑 |
| **可编辑性** | 字段粒度适中——对白逐条可改，动作描述整段可换，不会因为改一处而牵动全局 |
| **可扩展** | 每个实体保留 `metadata` 字段，用 key-value 形式挂载扩展信息，不破坏已有结构 |
| **小说适配** | 专门处理小说特征：角色别名映射、旁白→画外音转换、心理描写→动作/OS 标注、叙述性场景描述 |
| **工具友好** | 每个实体有唯一 `id`，角色通过 `character_id` 交叉引用，场景通过 `scene_id` 引用，方便程序遍历和校验 |

### 3.3 YAML 文件结构示例

```yaml
# script.yaml 示例（简化版，与实际代码对齐）
meta:
  version: "1.0"
  generated_at: "2024-06-05T12:00:00Z"
  model_name: "gpt-4o-mini"
  total_beats: 256
  dialogue_count: 128
  action_count: 64
  narration_count: 64
  characters:
    - "李明"
    - "王芳"

characters:
  - name: "李明"
    aliases: ["小李", "明哥"]
    description: "男主角，25岁，性格内向"
    voice_profile: null
    emotion_distribution: {happy: 0.2, sad: 0.3, angry: 0.1, calm: 0.3, excited: 0.1, fear: 0.0}

scenes:
  - scene_id: 1
    title: "第一章：相遇"
    location: "咖啡馆"
    time: "下午"
    beats:
      - type: "dialogue"
        character: "李明"
        content: "你好，好久不见！"
        emotion: "友善"
        source_location: { chapter_index: 0, start_paragraph: 42, end_paragraph: 48, start_offset: 0, end_offset: 20 }
      
      - type: "action"
        content: "他微笑着伸出手"
        duration: 2.5
      
      - type: "narration"
        content: "两人握手寒暄"
        speaker: null
```

### 3.4 校验规则详细定义

#### 3.4.1 根级校验

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `meta` | `dict` | ✅ | 必须是有效的元数据字典 |
| `characters` | `list` | ✅ | 必须是非空数组，每个元素是有效的角色字典 |
| `scenes` | `list` | ✅ | 必须是非空数组，每个元素是有效的场景字典 |

#### 3.4.2 Beat 级校验

**通用规则**：
- `type` 字段必须是 `dialogue` / `action` / `narration` 之一
- 根据 `type` 字段自动路由到对应模型校验

**DialogueBeat 校验规则**：

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `type` | `str` | ✅ | 必须等于 `"dialogue"` |
| `character` | `str` | ✅ | 非空字符串，长度 1-50 |
| `content` | `str` | ✅ | 非空字符串，长度 1-1000 |
| `emotion` | `str \| None` | ❌ | 如果提供，长度 1-20 |
| `source_location` | `dict \| None` | ❌ | 如果提供，必须包含 `chapter_index`, `start_paragraph`, `end_paragraph` |

**ActionBeat 校验规则**：

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `type` | `str` | ✅ | 必须等于 `"action"` |
| `content` | `str` | ✅ | 非空字符串，长度 1-1000 |
| `duration` | `float \| None` | ❌ | 如果提供，必须 > 0 |

**NarrationBeat 校验规则**：

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `type` | `str` | ✅ | 必须等于 `"narration"` |
| `content` | `str` | ✅ | 非空字符串，长度 1-1000 |
| `speaker` | `str \| None` | ❌ | 如果提供，长度 1-50 |

### 3.5 校验流程

```python
# validation.py

from pydantic import ValidationError
from novel2script.schema import Script
import yaml

def validate_script_yaml(yaml_content: str) -> tuple[bool, list[str]]:
    """
    校验 YAML 内容是否符合 Script Schema
    
    Returns:
        (is_valid, errors)
    """
    try:
        # 1. 解析 YAML
        data = yaml.safe_load(yaml_content)
        
        if not isinstance(data, dict):
            return False, ["YAML 根元素必须是字典"]
        
        # 2. Pydantic 校验
        script = Script(**data)
        
        # 3. 自定义校验
        script.validate_characters([char.name for char in script.characters])
        
        return True, []
        
    except ValidationError as e:
        # Pydantic 校验错误
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{loc}: {msg}")
        return False, errors
    
    except yaml.YAMLError as e:
        # YAML 解析错误
        return False, [f"YAML 解析错误：{str(e)}"]
    
    except Exception as e:
        # 其他错误
        return False, [f"未知错误：{str(e)}"]
```

### 3.6 JSON Schema 导出（供前端 CodeMirror 校验）

```python
# export_schema.py

import json
from novel2script.schema import Script

def export_json_schema(output_file: str = "script.schema.json") -> None:
    """导出 Script 模型的 JSON Schema"""
    
    # 方法1：使用 Pydantic V2 内置方法
    schema = Script.model_json_schema()
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON Schema 已导出到 {output_file}")

if __name__ == "__main__":
    export_json_schema()
```

**前端集成示例（CodeMirror 6）**：

```javascript
// 前端代码：使用导出的 JSON Schema 校验 YAML
import jsonSchema from 'https://json-schema.org/draft/07/schema#';
import { yaml } from '@codemirror/lang-yaml';
import { linter } from '@codemirror/lint';

// 1. 加载 JSON Schema
const schema = await fetch('/api/v1/schema/script').then(r => r.json());

// 2. 创建 YAML 校验器
const yamlLinter = linter(async (view) => {
  const content = view.state.doc.toString();
  
  // 解析 YAML
  const data = jsyaml.load(content);
    
  // 使用 Ajv 校验（JSON Schema 校验库）
  const ajv = new Ajv();
  const validate = ajv.compile(schema);
  const isValid = validate(data);
    
  if (!isValid) {
    return validate.errors.map(error => ({
      from: 0,  // TODO: 计算准确位置
      to: view.state.doc.length,
      severity: 'error',
      message: error.message,
    }));
  }
    
  return [];
});

// 3. 应用到 CodeMirror
const editor = new EditorView({
  state: EditorState.create({
    extensions: [
      yaml(),
      yamlLinter,
    ],
  }),
});
```

---

## 4. 错误处理

### 4.1 错误响应格式

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

### 4.2 错误码分段

| 错误码范围 | 类别 | 说明 |
|-----------|------|------|
| **0** | 成功 | 所有成功响应 |
| **400xx** | 客户端错误（请求错误） | 4xx HTTP 状态码对应 |
| **500xx** | 服务端错误 | 5xx HTTP 状态码对应 |

### 4.3 详细错误码表

#### 4.3.1 客户端错误（4xx）

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

#### 4.3.2 服务端错误（5xx）

| 错误码 | HTTP 状态码 | 说明 | 处理建议 |
|--------|------------|------|---------|
| **50000** | 500 | 内部服务器错误 | 联系开发者 |
| **50001** | 500 | LLM API 调用失败 | 检查 API Key 和网络连接 |
| **50002** | 500 | LLM 输出格式错误 | 系统将自动重试 |
| **50003** | 500 | 文件读写失败 | 检查磁盘空间和文件权限 |
| **50004** | 500 | Skill 执行失败 | 检查 Skill 代码 |
| **50300** | 503 | 服务不可用 | 服务正在重启，请稍后重试 |
| **50400** | 504 | LLM API 超时 | 增加超时时间或重试 |

### 4.4 错误码使用示例

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

## 5. 附录

### 5.1 完整模型定义汇总

| 模型 | 定义位置 | 用途 |
|------|---------|------|
| `Beat` | `schema.py` | Beat 联合类型 |
| `DialogueBeat` | `schema.py` | 对白 Beat |
| `ActionBeat` | `schema.py` | 动作 Beat |
| `NarrationBeat` | `schema.py` | 旁白 Beat |
| `ScriptMeta` | `schema.py` | 剧本元数据 |
| `Script` | `schema.py` | 剧本根对象 |
| `Character` | `schema.py` | 角色信息 |
| `Scene` | `schema.py` | 场景信息 |
| `OperationLog` | `schema.py` | 操作日志 |
| `EditMeta` | `schema.py` | 编辑器元数据 |
| `AppConfig` | `config.py` | 应用配置 |

### 5.2 参考资料

- **Pydantic V2 文档**：https://docs.pydantic.dev/
- **PyYAML 文档**：https://pyyaml.org/wiki/PyYAMLDocumentation
- **JSON Schema 规范**：https://json-schema.org/
- **CodeMirror 6 文档**：https://codemirror.net/docs/

### 5.3 与代码不一致的说明

本文档以实际代码为准，修正了之前文档中的以下不一致之处：

| 文档描述 | 实际代码 | 修正说明 |
|---------|---------|---------|
| `PipelineContext` 类 | `dict[str, Any]` | 简化设计，使用 dict |
| `register_step()` 方法 | `add_step()` 方法 | 方法命名差异 |
| `async def` ProjectStore | `def` ProjectStore | 同步实现，V2 规划异步化 |
| `SkillProtocol` 定义 | 无 Protocol，动态加载 | 简化设计，直接加载 `run()` 函数 |
| 取消机制 | 未实现 | V2 规划功能 |
| `v2/` API 目录 | 不存在 | V2 规划功能 |
| `event-bus.js` | 不存在，集成在 `app.js` | 简化设计 |

---

*文档合并时间：2026-06-07*  
*合并来源：data-model-design.md + api-design.md + yaml-schema.md*  
*修正说明：以实际代码为准，修正了文档与代码的不一致之处*
