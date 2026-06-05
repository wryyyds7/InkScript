# 数据模型设计文档（Data Model Design Specification）

> 版本：V1.0 | 日期：2026-06-06 | 状态：待确认
> 输入来源：`docs/system-architecture.md` + `docs/architecture.md`
> 输出用途：指导后端实现、YAML 校验、前端集成

---

## 目录

1. [设计原则](#1-设计原则)
2. [核心数据模型](#2-核心数据模型)
3. [Pydantic 模型详细定义](#3-pydantic-模型详细定义)
4. [YAML Schema 校验规则](#4-yaml-schema-校验规则)
5. [JSON Schema 导出](#5-json-schema-导出)
6. [数据库表结构（V2）](#6-数据库表结构v2)
7. [数据迁移策略](#7-数据迁移策略)
8. [附录](#8-附录)

---

## 1. 设计原则

### 1.1 核心原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **类型安全** | 使用 Pydantic V2 提供运行时类型校验 | `Beat = TaggedUnion[DialogueBeat, ActionBeat, NarrationBeat]` |
| **可扩展性** | Tagged Union 机制支持新增 Beat 类型 | 加新 Beat 类型只需在 Union 中添加模型 |
| **可校验性** | 导出 JSON Schema 供前端 CodeMirror 校验 | `schema.py` → `script.schema.json` |
| **可序列化** | 支持 YAML / JSON 双向序列化 | `PyYAML` + Pydantic `.model_dump()` |
| **向后兼容** | 新增字段使用 `Optional` + 默认值 | `emotion: str | None = None` |

### 1.2 技术选型

| 技术 | 用途 | 原因 |
|------|------|------|
| **Pydantic V2** | 类型校验、序列化、JSON Schema 导出 | 比 V1 快 5-50 倍，与 FastAPI 深度集成 |
| **PyYAML** | YAML 序列化/反序列化 | Python 标准 YAML 库，稳定可靠 |
| **Tagged Union** | Beat 类型多态 | Pydantic V2 原生支持，自动根据 `type` 字段反序列化 |

---

## 2. 核心数据模型

### 2.1 模型关系图

```
┌─────────────────────────────────────────────────────────┐
│                    Project（项目）                        │
│  - project_id: str                                     │
│  - name: str                                           │
│  - created_at: datetime                                │
│  - updated_at: datetime                                │
│  - config_snapshot: AppConfig                          │
│  - meta: ProjectMeta                                  │
└───────────────┬─────────────────────────────────────────┘
                │
                ├───────────────┐
                │               │
                ▼               ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Novel（小说）      │    │ Script（剧本）        │
│  - content: str     │    │  - beats: List[Beat]│
│  - encoding: str    │    │  - meta: ScriptMeta │
│  - line_count: int  │    │  - version: str     │
└─────────────────────┘    └─────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │ Beat（剧本单元）      │
                          │  - type: Literal     │
                          │  - ... (联合类型)    │
                          └─────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
          │ DialogueBeat  │ │ ActionBeat   │ │NarrationBeat │
          │ - character   │ │ - content    │ │ - content    │
          │ - content     │ │ - duration?  │ │ - speaker?   │
          │ - emotion     │ │              │ │              │
          └──────────────┘ └──────────────┘ └──────────────┘
```

### 2.2 模型清单

| 模型 | 用途 | 定义位置 |
|------|------|---------|
| `Beat` | 剧本基本单元（联合类型） | `schema.py` |
| `DialogueBeat` | 对白 Beat | `schema.py` |
| `ActionBeat` | 动作 Beat | `schema.py` |
| `NarrationBeat` | 旁白 Beat | `schema.py` |
| `ScriptMeta` | 剧本元数据 | `schema.py` |
| `ProjectMeta` | 项目元数据 | `schema.py` |
| `AppConfig` | 应用配置 | `config.py` |
| `ProjectCreateRequest` | 创建项目请求 | `api/schemas.py` |
| `ProjectDetail` | 项目详情响应 | `api/schemas.py` |

---

## 3. Pydantic 模型详细定义

### 3.1 Beat 联合类型（核心）

```python
# schema.py

from pydantic import BaseModel, Field, TaggedUnion
from typing import Literal, Union, Annotated
from datetime import datetime
from enum import Enum

# 3.1.1 Beat 类型枚举（用于未来扩展）
class BeatType(str, Enum):
    DIALOGUE = "dialogue"
    ACTION = "action"
    NARRATION = "narration"
    # 未来可扩展：THOUGHT = "thought", SFX = "sfx", etc.

# 3.1.2 对白 Beat
class DialogueBeat(BaseModel):
    """对白 Beat：角色说话内容"""
    
    type: Literal[BeatType.DIALOGUE] = BeatType.DIALOGUE
    character: str = Field(..., description="角色名称，必须存在于角色列表中")
    content: str = Field(..., description="对白内容")
    emotion: str | None = Field(None, description="情绪标签（可选）")
    
    # V1 扩展字段（可选）
    volume: str | None = Field(None, description="音量：whisper | normal | shout")
    speed: str | None = Field(None, description="语速：slow | normal | fast")
    
    # 元数据（不序列化到 YAML，仅运行时使用）
    model_config = {"extra": "forbid"}  # 禁止额外字段
    
    # 质询修复 #3：自动设置 type 默认值
    @model_validator(mode="before")
    @classmethod
    def set_default_type(cls, data: dict) -> dict:
        """如果缺少 type 字段，自动设置为默认值"""
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.DIALOGUE
        return data

# 3.1.3 动作 Beat
class ActionBeat(BaseModel):
    """动作 Beat：描述动作、表情、场景变化"""
    
    type: Literal[BeatType.ACTION] = BeatType.ACTION
    content: str = Field(..., description="动作描述")
    duration: float | None = Field(None, description="预估持续时间（秒）")
    
    model_config = {"extra": "forbid"}
    
    # 质询修复 #3：自动设置 type 默认值
    @model_validator(mode="before")
    @classmethod
    def set_default_type(cls, data: dict) -> dict:
        """如果缺少 type 字段，自动设置为默认值"""
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.ACTION
        return data

# 3.1.4 旁白 Beat
class NarrationBeat(BaseModel):
    """旁白 Beat：描述场景、氛围、心理活动"""
    
    type: Literal[BeatType.NARRATION] = BeatType.NARRATION
    content: str = Field(..., description="旁白内容")
    speaker: str | None = Field(None, description="旁白配音角色（可选）")
    
    model_config = {"extra": "forbid"}
    
    # 质询修复 #3：自动设置 type 默认值
    @model_validator(mode="before")
    @classmethod
    def set_default_type(cls, data: dict) -> dict:
        """如果缺少 type 字段，自动设置为默认值"""
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.NARRATION
        return data

# 3.1.5 Beat 联合类型（Tagged Union）
Beat = Annotated[
    Union[
        Annotated[DialogueBeat, Tag("dialogue")],
        Annotated[ActionBeat, Tag("action")],
        Annotated[NarrationBeat, Tag("narration")],
    ],
    Discriminator("type"),
]
```

### 3.2 剧本元数据模型

```python
# schema.py

class ScriptMeta(BaseModel):
    """剧本元数据（质询修复 #5：向前兼容）"""
    
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
    
    # 质询修复 #5：向前兼容（V1 可以解析 V2 生成的 YAML）
    model_config = {"extra": "ignore"}  # 忽略额外字段
    
    def model_post_init(self):
        """初始化后处理"""
        # 确保 characters 去重
        self.characters = list(set(self.characters))
```

### 3.3 剧本根模型

```python
# schema.py

class Script(BaseModel):
    """剧本根对象"""
    
    meta: ScriptMeta = Field(default_factory=ScriptMeta)
    beats: list[Beat] = Field(default_factory=list)
    
    def add_beat(self, beat: Beat) -> None:
        """添加 Beat（自动更新统计）"""
        self.beats.append(beat)
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
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
```

### 3.4 项目元数据模型

```python
# schema.py

class ProjectMeta(BaseModel):
    """项目元数据"""
    
    project_id: str = Field(..., description="项目唯一 ID")
    name: str = Field(..., description="项目名称")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 文件信息
    novel_file: str = "novel.txt"
    script_file: str = "script.yaml"
    meta_file: str = "meta.json"
    
    # 配置快照（确保可复现性）
    config_snapshot: dict = Field(default_factory=dict)
    
    # 版本历史（V1 简化版）
    versions: list[dict] = Field(default_factory=list)
    
    def touch(self) -> None:
        """更新 updated_at 时间戳"""
        self.updated_at = datetime.utcnow()
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
```

### 3.5 应用配置模型

```python
# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError
from typing import Optional

class AppConfig(BaseSettings):
    """应用配置（支持环境变量、.env、JSON 文件）"""
    
    model_config = SettingsConfigDict(
        env_prefix="N2S_",
        json_file="~/.novel2script/config.json",
        json_file_encoding="utf-8",
        env_file=".env",
        extra="ignore",
    )
    
    # LLM 配置
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 高级配置
    max_concurrent: int = 3  # 最大并发 LLM 请求数
    timeout: int = 60  # LLM API 超时时间（秒）
    max_retries: int = 3  # 失败重试次数
    
    # 应用配置
    language: str = "zh-CN"
    theme: str = "dark"
    auto_save_interval: int = 30  # 自动保存间隔（秒）
    
    # 路径配置
    projects_dir: str = "~/.novel2script/projects"
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature 必须在 0.0 ~ 2.0 之间")
        return v
    
    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_tokens 必须为正整数")
        return v
    
    @field_validator("api_base")
    @classmethod
    def validate_api_base(cls, v: str) -> str:
        if not v.startswith("http"):
            raise ValueError("api_base 必须是有效的 URL")
        return v
    
    def encrypt_api_key(self) -> str:
        """加密 API Key（使用 cryptography.fernet）"""
        from cryptography.fernet import Fernet
        import base64
        
        key = self._get_or_create_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(self.api_key.encode())
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
            return key
```

---

## 4. YAML Schema 校验规则

### 4.1 YAML 文件结构

```yaml
# script.yaml 示例
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

beats:
  - type: "dialogue"
    character: "李明"
    content: "你好，好久不见！"
    emotion: "友善"
    source_location:
      chapter: 1
      start: 42
      end: 48
      context_before: "夜色渐深，"
      context_after: "他抬起头"

  - type: "action"
    content: "他微笑着伸出手"
    duration: 2.5

  - type: "narration"
    content: "两人握手寒暄"
    speaker: null
```

### 4.2 校验规则详细定义

#### 4.2.1 根级校验

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `meta` | `ScriptMeta` | ✅ | 必须是有效的 `ScriptMeta` 对象 |
| `beats` | `list[Beat]` | ✅ | 必须是非空数组，每个元素是有效的 `Beat` |

#### 4.2.2 Beat 级校验

**通用规则**：
- `type` 字段必须是 `dialogue` / `action` / `narration` 之一
- 根据 `type` 字段自动路由到对应模型校验

**DialogueBeat 校验规则**：

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `type` | `Literal["dialogue"]` | ✅ | 必须等于 `"dialogue"` |
| `character` | `str` | ✅ | 非空字符串，长度 1-50 |
| `content` | `str` | ✅ | 非空字符串，长度 1-1000 |
| `emotion` | `str \| None` | ❌ | 如果提供，长度 1-20 |
| `source_location` | `dict \| None` | ❌ | 如果提供，必须包含 `chapter`, `start`, `end` |

**ActionBeat 校验规则**：

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `type` | `Literal["action"]` | ✅ | 必须等于 `"action"` |
| `content` | `str` | ✅ | 非空字符串，长度 1-1000 |
| `duration` | `float \| None` | ❌ | 如果提供，必须 > 0 |

**NarrationBeat 校验规则**：

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `type` | `Literal["narration"]` | ✅ | 必须等于 `"narration"` |
| `content` | `str` | ✅ | 非空字符串，长度 1-1000 |
| `speaker` | `str \| None` | ❌ | 如果提供，长度 1-50 |

#### 4.2.3 source_location 校验规则

| 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|---------|
| `chapter` | `int` | ✅ | 必须 ≥ 1 |
| `start` | `int` | ✅ | 必须 ≥ 0 |
| `end` | `int` | ✅ | 必须 > `start` |
| `context_before` | `str \| None` | ❌ | 如果提供，长度 1-100 |
| `context_after` | `str \| None` | ❌ | 如果提供，长度 1-100 |

### 4.3 自定义校验器

```python
# schema.py

from pydantic import field_validator, model_validator
from typing import Any

class DialogueBeat(BaseModel):
    # ... 字段定义见上方
    
    @field_validator("character")
    @classmethod
    def validate_character(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("character 不能为空")
        if len(v) > 50:
            raise ValueError("character 长度不能超过 50")
        return v.strip()
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("content 不能为空")
        if len(v) > 1000:
            raise ValueError("content 长度不能超过 1000")
        return v.strip()
    
    @field_validator("emotion")
    @classmethod
    def validate_emotion(cls, v: str | None) -> str | None:
        if v is not None:
            if len(v) > 20:
                raise ValueError("emotion 长度不能超过 20")
        return v

class Script(BaseModel):
    # ... 字段定义见上方
    
    @model_validator(mode="after")
    def validate_script(self) -> "Script":
        """校验整个 Script 的一致性"""
        
        # 校验1：角色一致性
        character_errors = self.validate_characters(self.meta.characters)
        if character_errors:
            raise ValueError(f"角色不一致：{character_errors}")
        
        # 校验2：source_location 不重叠（可选）
        # TODO: V2 实现
        
        return self
```

### 4.4 校验流程

```python
# validation.py

from pydantic import ValidationError
from typing import Union
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
        script.validate_script()
        
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

# 使用示例
is_valid, errors = validate_script_yaml(yaml_content)

if not is_valid:
    print("校验失败：")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ YAML 格式正确")
```

---

## 5. JSON Schema 导出

### 5.1 导出目的

导出 JSON Schema 供前端 **CodeMirror 6** 做实时校验。

### 5.2 导出方法

```python
# export_schema.py

import json
from schema import Script, Beat

def export_json_schema(output_file: str = "script.schema.json") -> None:
    """导出 Script 模型的 JSON Schema"""
    
    # 方法1：使用 Pydantic V2 内置方法
    schema = Script.model_json_schema()
    
    # 方法2：手动构建（更灵活）
    # schema = build_custom_json_schema()
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON Schema 已导出到 {output_file}")

if __name__ == "__main__":
    export_json_schema()
```

### 5.3 导出的 JSON Schema 示例

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Script",
  "type": "object",
  "properties": {
    "meta": {
      "$ref": "#/definitions/ScriptMeta"
    },
    "beats": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Beat"
      }
    }
  },
  "definitions": {
    "ScriptMeta": {
      "type": "object",
      "properties": {
        "version": {"type": "string"},
        "generated_at": {"type": "string", "format": "date-time"},
        "model_name": {"type": "string"},
        "total_beats": {"type": "integer"},
        "dialogue_count": {"type": "integer"},
        "action_count": {"type": "integer"},
        "narration_count": {"type": "integer"},
        "characters": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "Beat": {
      "oneOf": [
        {"$ref": "#/definitions/DialogueBeat"},
        {"$ref": "#/definitions/ActionBeat"},
        {"$ref": "#/definitions/NarrationBeat"}
      ]
    },
    "DialogueBeat": {
      "type": "object",
      "required": ["type", "character", "content"],
      "properties": {
        "type": {"enum": ["dialogue"]},
        "character": {"type": "string"},
        "content": {"type": "string"},
        "emotion": {"type": "string", "nullable": true},
        "source_location": {"$ref": "#/definitions/SourceLocation"}
      }
    },
    "ActionBeat": {...},
    "NarrationBeat": {...},
    "SourceLocation": {...}
  }
}
```

### 5.4 前端集成（CodeMirror 6）

```javascript
// 前端代码：使用导出的 JSON Schema 校验 YAML
import jsonSchema from 'https://json-schema.org/draft/07/schema';
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

## 6. 数据库表结构（V2）

### 6.1 设计说明

V1 版本使用 **文件系统存储**（ProjectStore + JSON/YAML 文件），不使用数据库。

V2 版本如果需要支持多用户、协作编辑、云端存储，可以考虑引入 **SQLite** 或 **PostgreSQL**。

### 6.2 V2 数据库表结构（预览）

```sql
-- V2 数据库表结构（预览，V1 不使用）

-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config_snapshot TEXT,  -- JSON 格式
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 小说表
CREATE TABLE novels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    encoding VARCHAR(20) DEFAULT 'utf-8',
    line_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 剧本表
CREATE TABLE scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    version INTEGER DEFAULT 1,
    yaml_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Beat 表（V2.1 考虑拆分，支持细粒度编辑）
CREATE TABLE beats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    character VARCHAR(50),
    content TEXT NOT NULL,
    emotion VARCHAR(20),
    sort_order INTEGER NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- 索引
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_novels_project_id ON novels(project_id);
CREATE INDEX idx_scripts_project_id ON scripts(project_id);
CREATE INDEX idx_beats_script_id ON beats(script_id);
```

---

## 7. 数据迁移策略

### 7.1 V1 → V2 迁移（文件系统 → 数据库）

```python
# migration.py（V2 实现）

import sqlite3
import yaml
import json
from pathlib import Path

def migrate_v1_to_v2(projects_dir: str, db_path: str) -> None:
    """
    将 V1 文件系统存储迁移到 V2 数据库
    
    Args:
        projects_dir: V1 项目目录（~/.novel2script/projects）
        db_path: V2 数据库文件路径
    """
    
    # 1. 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. 遍历所有 V1 项目
    projects_path = Path(projects_dir)
    
    for project_dir in projects_path.iterdir():
        if not project_dir.is_dir():
            continue
        
        # 读取 meta.json
        meta_file = project_dir / "meta.json"
        if not meta_file.exists():
            continue
        
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        # 插入项目
        cursor.execute(
            "INSERT INTO projects (name, created_at, updated_at, config_snapshot) VALUES (?, ?, ?, ?)",
            (
                meta["name"],
                meta["created_at"],
                meta["updated_at"],
                json.dumps(meta.get("config_snapshot", {})),
            ),
        )
        project_id = cursor.lastrowid
        
        # 插入小说
        novel_file = project_dir / meta["novel_file"]
        if novel_file.exists():
            with open(novel_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            cursor.execute(
                "INSERT INTO novels (project_id, content, encoding, line_count) VALUES (?, ?, ?, ?)",
                (project_id, content, "utf-8", len(content.splitlines())),
            )
        
        # 插入剧本
        script_file = project_dir / meta["script_file"]
        if script_file.exists():
            with open(script_file, "r", encoding="utf-8") as f:
                yaml_content = f.read()
            
            cursor.execute(
                "INSERT INTO scripts (project_id, version, yaml_content) VALUES (?, ?, ?)",
                (project_id, 1, yaml_content),
            )
            script_id = cursor.lastrowid
            
            # 解析 YAML，插入 Beat（可选，V2.1 再做）
            # data = yaml.safe_load(yaml_content)
            # for i, beat in enumerate(data.get("beats", [])):
            #     cursor.execute(...)
        
        print(f"✅ 迁移项目：{meta['name']}")
    
    # 提交事务
    conn.commit()
    conn.close()
    
    print(f"✅ 迁移完成：{projects_path} → {db_path}")
```

---

## 8. 附录

### 8.1 完整模型定义汇总

| 模型 | 定义位置 | 用途 |
|------|---------|------|
| `Beat` | `schema.py` | Beat 联合类型 |
| `DialogueBeat` | `schema.py` | 对白 Beat |
| `ActionBeat` | `schema.py` | 动作 Beat |
| `NarrationBeat` | `schema.py` | 旁白 Beat |
| `ScriptMeta` | `schema.py` | 剧本元数据 |
| `Script` | `schema.py` | 剧本根对象 |
| `ProjectMeta` | `schema.py` | 项目元数据 |
| `AppConfig` | `config.py` | 应用配置 |
| `ProjectCreateRequest` | `api/schemas.py` | API 请求模型 |
| `ProjectDetail` | `api/schemas.py` | API 响应模型 |

### 8.2 校验错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| `VALUE_ERROR` | 字段值错误（Pydantic ValidationError） | 检查字段格式和范围 |
| `YAML_ERROR` | YAML 解析错误 | 检查 YAML 语法 |
| `SCHEMA_ERROR` | Schema 校验错误 | 检查是否符合 Script Schema |
| `CHARACTER_ERROR` | 角色不一致 | 检查对白 Beat 的 character 字段 |

### 8.3 参考资料

- **Pydantic V2 文档**：https://docs.pydantic.dev/
- **PyYAML 文档**：https://pyyaml.org/wiki/PyYAMLDocumentation
- **JSON Schema 规范**：https://json-schema.org/
- **CodeMirror 6 文档**：https://codemirror.net/docs/

---

## 9. 总结

本文档详细设计了 InkScript V1 版本的所有数据模型，包括：

1. ✅ **Pydantic 模型**：Beat 联合类型、Script、ProjectMeta、AppConfig
2. ✅ **YAML Schema 校验规则**：字段校验、自定义校验器、校验流程
3. ✅ **JSON Schema 导出**：供前端 CodeMirror 6 实时校验
4. ✅ **V2 数据库表结构**（预览）：为未来版本做准备
5. ✅ **数据迁移策略**：V1 → V2 迁移方案

**下一步**：
- 根据本文档实现 `schema.py` 和 `config.py`
- 实现 YAML 校验功能
- 导出 JSON Schema 供前端使用

---

**文档状态**：✅ 已完成，待用户确认

**最后更新**：2026-06-06
