# Prompt 模板设计文档（Prompt Template Design Specification）

> 版本：V1.0 | 日期：2026-06-06 | 状态：待确认
> 输入来源：`docs/system-architecture.md` + `docs/requirements-spec.md`
> 输出用途：指导 Prompt 实现、few-shot 示例设计、错误处理策略

---

## 目录

1. [设计原则](#1-设计原则)
2. [Prompt 模板结构](#2-prompt-模板结构)
3. [Pipeline 步骤 Prompt 模板](#3-pipeline-步骤-prompt-模板)
4. [Few-Shot 示例设计](#4-few-shot-示例设计)
5. [错误处理策略](#5-错误处理策略)
6. [Prompt 优化策略](#6-prompt-优化策略)
7. [Prompt 测试与评估](#7-prompt-测试与评估)
8. [附录](#8-附录)

---

## 1. 设计原则

### 1.1 核心原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **清晰明确** | 使用简洁、无歧义的语言 | "提取所有角色名称" vs "找出小说里的人都叫什么" |
| **结构化的输出** | 要求 LLM 输出 JSON 格式 | `请返回 JSON 格式：{"characters": [...]}` |
| **Few-shot 示例** | 提供 2-3 个示例 | 见 [第 4 节](#4-few-shot-示例设计) |
| **分步骤引导** | 复杂任务拆解为多个子任务 | 先提取角色 → 再分割场景 → 最后解析对白 |
| **错误容忍** | 设计自动修复策略 | 见 [第 5 节](#5-错误处理策略) |

### 1.2 Prompt 模板文件结构

```
prompts/
├── character_extractor.md   # 角色识别 Prompt
├── scene_splitter.md        # 场景分割 Prompt
├── dialogue_parser.md       # 对白解析 Prompt
├── emotion_tagger.md       # 情绪标注 Prompt
├── yaml_generator.md       # YAML 生成 Prompt
├── quality_checker.md      # 质量检查 Prompt
└── few_shots/             # Few-shot 示例库
    ├── character_extractor_examples.json
    ├── scene_splitter_examples.json
    ├── dialogue_parser_examples.json
    ├── emotion_tagger_examples.json
    └── yaml_generator_examples.json
```

---

## 2. Prompt 模板结构

### 2.1 通用模板结构

每个 Prompt 模板包含以下部分：

```
# Prompt 模板通用结构

## 1. Role（角色定义）
你是一个专业的剧本分析专家，擅长从小说中提取结构化信息...

## 2. Task（任务描述）
你的任务是从以下小说文本中 {具体任务}...

## 3. Input（输入格式）
输入是小说文本，格式为：
```
{输入格式说明}
```

## 4. Output（输出格式）
请严格按照以下 JSON Schema 输出结果：
```json
{JSON Schema}
```

## 5. Constraints（约束条件）
- 必须提取所有 {目标对象}
- 不要遗漏任何 {目标对象}
- 输出必须是合法的 JSON 格式
- 不要添加任何解释或说明

## 6. Examples（Few-shot 示例）
### 示例 1：
输入：
```
{示例输入}
```
输出：
```json
{示例输出}
```

### 示例 2：
...

## 7. Input Text（实际输入）
以下是需要处理的文本：
```
{实际输入文本}
```

## 8. Output（要求输出）
请只输出 JSON，不要添加任何解释。
```

### 2.2 Prompt 模板变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `{novel_text}` | 小说文本 | 实际输入的小说内容 |
| `{json_schema}` | JSON Schema 定义 | 见各步骤的 Schema 定义 |
| `{examples}` | Few-shot 示例 | 见 [第 4 节](#4-few-shot-示例设计) |
| `{constraints}` | 约束条件 | 步骤特定的约束 |
| `{chapter_info}` | 章节信息 | 如果按章处理，提供章节上下文 |

---

## 3. Pipeline 步骤 Prompt 模板

### 3.1 步骤 1：角色识别（character_extractor）

#### 3.1.1 Prompt 模板

```markdown
# Role
你是一个专业的文学分析专家，擅长从小说中提取所有登场角色信息。

# Task
你的任务是从以下小说文本中，提取所有登场角色的名称和基本信息。

# Input
输入是小说文本（可能是整本小说，也可能是单个章节）。

# Output
请严格按照以下 JSON Schema 输出结果：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "characters": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "description": "角色名称"},
          "aliases": {"type": "array", "items": {"type": "string"}, "description": "别名/昵称"},
          "gender": {"type": "string", "enum": ["男", "女", "未知"]},
          "first_appearance": {"type": "string", "description": "首次出现的章节或段落"}
        },
        "required": ["name"]
      }
    }
  },
  "required": ["characters"]
}
```

# Constraints
- 提取所有有对白或动作描写的角色（包括次要角色）
- 同一个角色可能有多个称呼（如"李明"、"小李"、"李大哥"），请在 `aliases` 中列出
- 如果无法确定性别，填"未知"
- 输出必须是合法的 JSON 格式
- 不要添加任何解释或说明

# Examples

### 示例 1（简单）：
输入：
```
"你好！"李明笑着说，"好久不见。"
"你好。"王芳点了点头。
```

输出：
```json
{
  "characters": [
    {
      "name": "李明",
      "aliases": [],
      "gender": "男",
      "first_appearance": "开头"
    },
    {
      "name": "王芳",
      "aliases": [],
      "gender": "女",
      "first_appearance": "开头"
    }
  ]
}
```

### 示例 2（复杂，含别名）：
输入：
```
"小李，快来！"王经理喊道。
李明跑过来："王总，什么事？"
```

输出：
```json
{
  "characters": [
    {
      "name": "李明",
      "aliases": ["小李"],
      "gender": "男",
      "first_appearance": "开头"
    },
    {
      "name": "王经理",
      "aliases": ["王总"],
      "gender": "男",
      "first_appearance": "开头"
    }
  ]
}
```

# Input Text
以下是需要处理的文本：
```
{novel_text}
```

# Output
请只输出 JSON，不要添加任何解释。
```

#### 3.1.2 输入/输出格式

**输入**：
- `novel_text`（str）：小说文本（全量或单章）

**输出**（JSON）：
```json
{
  "characters": [
    {
      "name": "李明",
      "aliases": ["小李"],
      "gender": "男",
      "first_appearance": "第1章"
    }
  ]
}
```

#### 3.1.3 错误处理策略

| 错误类型 | 处理策略 |
|---------|---------|
| **JSON 解析失败** | 自动修复（提取 ```json ``` 代码块 → 修复常见错误） → 降级重试 |
| **角色名称为空** | 过滤掉 `name` 为空的条目 |
| **性别识别错误** | 允许"未知"，不强制要求准确识别 |
| **别名遗漏** | 后续步骤（dialogue_parser）可以补充 |

---

### 3.2 步骤 2：场景分割（scene_splitter）

#### 3.2.1 Prompt 模板

```markdown
# Role
你是一个专业的剧本场景分析专家，擅长将小说文本分割为独立的场景。

# Task
你的任务是将以下小说文本分割为多个场景（scene），每个场景是一个连续的时间/空间单元。

# Input
输入是小说文本（单个章节或分段）。

# Output
请严格按照以下 JSON Schema 输出结果：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "scenes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "scene_id": {"type": "integer", "description": "场景 ID，从 1 开始"},
          "location": {"type": "string", "description": "场景发生地点"},
          "time": {"type": "string", "description": "场景发生时间"},
          "summary": {"type": "string", "description": "场景内容摘要"},
          "start_line": {"type": "integer", "description": "起始行号"},
          "end_line": {"type": "integer", "description": "结束行号"}
        },
        "required": ["scene_id", "start_line", "end_line"]
      }
    }
  },
  "required": ["scenes"]
}
```

# Constraints
- 场景分割依据：时间跳跃、地点变化、人物切换
- 每个场景应该有明确的边界（空行或分隔符）
- `start_line` 和 `end_line` 必须准确对应当输入文本的行号
- 输出必须是合法的 JSON 格式
- 不要添加任何解释或说明

# Examples

### 示例 1（简单）：
输入：
```
第1章

清晨，李明走出家门。

（空行）

他来到公司，看见王芳正在工作。

"早上好！"他说。

"早上好。"她回答。

（空行）

中午，他们一起去吃饭。
```

输出：
```json
{
  "scenes": [
    {
      "scene_id": 1,
      "location": "家门外",
      "time": "清晨",
      "summary": "李明出门",
      "start_line": 3,
      "end_line": 3
    },
    {
      "scene_id": 2,
      "location": "公司",
      "time": "早上",
      "summary": "李明和王芳打招呼",
      "start_line": 5,
      "end_line": 11
    },
    {
      "scene_id": 3,
      "location": "餐厅",
      "time": "中午",
      "summary": "李明和王芳一起吃午饭",
      "start_line": 13,
      "end_line": 13
    }
  ]
}
```

# Input Text
以下是需要处理的文本：
```
{novel_text}
```

# Output
请只输出 JSON，不要添加任何解释。
```

#### 3.2.2 输入/输出格式

**输入**：
- `novel_text`（str）：小说文本（单章或分段）

**输出**（JSON）：
```json
{
  "scenes": [
    {
      "scene_id": 1,
      "location": "家门外",
      "time": "清晨",
      "summary": "李明出门",
      "start_line": 3,
      "end_line": 3
    }
  ]
}
```

#### 3.2.3 错误处理策略

| 错误类型 | 处理策略 |
|---------|---------|
| **JSON 解析失败** | 自动修复 → 降级重试 |
| **场景边界不准确** | 使用启发式规则修正（空行作为分隔符） |
| **行号错误** | 重新计算行号（基于原始文本） |

---

### 3.3 步骤 3：对白解析（dialogue_parser）

#### 3.3.1 Prompt 模板

```markdown
# Role
你是一个专业的剧本对白分析专家，擅长从小说中提取对白、动作和旁白。

# Task
你的任务是将以下小说场景解析为结构化 Beat 列表（对白、动作、旁白）。

# Input
输入是一个小说场景的文本，以及已知角色列表。

# Output
请严格按照以下 JSON Schema 输出结果：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "beats": {
      "type": "array",
      "items": {
        "oneOf": [
          {
            "type": "object",
            "properties": {
              "type": {"enum": ["dialogue"]},
              "character": {"type": "string", "description": "角色名称"},
              "content": {"type": "string", "description": "对白内容"},
              "emotion": {"type": "string", "description": "情绪标签"}
            },
            "required": ["type", "character", "content"]
          },
          {
            "type": "object",
            "properties": {
              "type": {"enum": ["action"]},
              "content": {"type": "string", "description": "动作描述"}
            },
            "required": ["type", "content"]
          },
          {
            "type": "object",
            "properties": {
              "type": {"enum": ["narration"]},
              "content": {"type": "string", "description": "旁白内容"}
            },
            "required": ["type", "content"]
          }
        ]
      }
    }
  },
  "required": ["beats"]
}
```

# Constraints
- 对白必须归属于已知角色（参考角色列表）
- 动作描述应该简洁明了
- 旁白用于描述场景、氛围、心理活动
- 输出必须是合法的 JSON 格式
- 不要添加任何解释或说明

# Examples

### 示例 1（简单）：
输入：
```
"你好！"李明笑着说，"好久不见。"
王芳点了点头："你好。"
```

已知角色：["李明", "王芳"]

输出：
```json
{
  "beats": [
    {
      "type": "dialogue",
      "character": "李明",
      "content": "你好！好久不见。",
      "emotion": "友善"
    },
    {
      "type": "action",
      "content": "王芳点了点头"
    },
    {
      "type": "dialogue",
      "character": "王芳",
      "content": "你好。",
      "emotion": "平静"
    }
  ]
}
```

# Input Text
以下是需要处理的场景文本：
```
{scene_text}
```

已知角色列表：
```
{characters}
```

# Output
请只输出 JSON，不要添加任何解释。
```

#### 3.3.2 输入/输出格式

**输入**：
- `scene_text`（str）：单个场景的文本
- `characters`（list[str]）：已知角色列表

**输出**（JSON）：
```json
{
  "beats": [
    {
      "type": "dialogue",
      "character": "李明",
      "content": "你好！",
      "emotion": "友善"
    }
  ]
}
```

#### 3.3.3 错误处理策略

| 错误类型 | 处理策略 |
|---------|---------|
| **JSON 解析失败** | 自动修复 → 降级重试 |
| **角色名称不匹配** | 模糊匹配（允许 10% 差异） → 标记为 `[UNKNOWN_CHARACTER]` |
| **情绪标签缺失** | 不强制要求，设为 `null` |

---

### 3.4 步骤 4：情绪标注（emotion_tagger）

#### 3.4.1 Prompt 模板

```markdown
# Role
你是一个专业的情绪分析专家，擅长从对白内容推断角色的情绪状态。

# Task
你的任务是为以下对白 Beat 标注情绪标签。

# Input
输入是对白 Beat 列表，每个 Beat 包含 `character` 和 `content`。

# Output
请严格按照以下 JSON Schema 输出结果：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "beats": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "character": {"type": "string"},
          "content": {"type": "string"},
          "emotion": {"type": "string", "description": "情绪标签"}
        },
        "required": ["character", "content", "emotion"]
      }
    }
  },
  "required": ["beats"]
}
```

# Constraints
- 情绪标签应该从以下列表中选择：友善、平静、愤怒、悲伤、惊讶、恐惧、厌恶、害羞、激动、困惑
- 如果无法确定情绪，填"平静"
- 输出必须是合法的 JSON 格式
- 不要添加任何解释或说明

# Examples

### 示例 1：
输入：
```json
{
  "beats": [
    {"character": "李明", "content": "你好！好久不见！"},
    {"character": "王芳", "content": "嗯。"}
  ]
}
```

输出：
```json
{
  "beats": [
    {
      "character": "李明",
      "content": "你好！好久不见！",
      "emotion": "友善"
    },
    {
      "character": "王芳",
      "content": "嗯。",
      "emotion": "平静"
    }
  ]
}
```

# Input
以下是对白 Beat 列表：
```
{beats}
```

# Output
请只输出 JSON，不要添加任何解释。
```

#### 3.4.2 输入/输出格式

**输入**：
- `beats`（list[dict]）：对白 Beat 列表

**输出**（JSON）：
```json
{
  "beats": [
    {
      "character": "李明",
      "content": "你好！",
      "emotion": "友善"
    }
  ]
}
```

#### 3.4.3 错误处理策略

| 错误类型 | 处理策略 |
|---------|---------|
| **JSON 解析失败** | 自动修复 → 降级重试 |
| **情绪标签不在列表中** | 映射到最接近的标签 → 标记为 `[UNCLEAR_EMOTION]` |

---

### 3.5 步骤 5：YAML 生成（yaml_generator）

#### 3.5.1 Prompt 模板

```markdown
# Role
你是一个专业的 YAML 格式生成专家，擅长将结构化数据转换为符合 Schema 的 YAML 文件。

# Task
你的任务是将以下 Beat 列表转换为符合 Script YAML Schema 的 YAML 文件。

# Input
输入是 Beat 列表（包含对白、动作、旁白），以及元数据（角色列表、生成时间等）。

# Output
请输出符合以下 YAML Schema 的 YAML 文件：

```yaml
meta:
  version: "1.0"
  generated_at: "2024-06-05T12:00:00Z"
  model_name: "{model_name}"
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
    content: "你好！"
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

# Constraints
- 必须包含所有 Beat（不能遗漏）
- `meta` 中的统计信息必须准确
- `source_location` 必须准确对应当输入文本的位置
- 输出必须是合法的 YAML 格式
- 不要添加任何解释或说明

# Input
以下是 Beat 列表：
```json
{beats}
```

以下是元数据：
```json
{meta}
```

# Output
请只输出 YAML，不要添加任何解释。
```

#### 3.5.2 输入/输出格式

**输入**：
- `beats`（list[dict]）：Beat 列表
- `meta`（dict）：元数据

**输出**（YAML）：
```yaml
meta:
  version: "1.0"
  ...
beats:
  - type: "dialogue"
    ...
```

#### 3.5.3 错误处理策略

| 错误类型 | 处理策略 |
|---------|---------|
| **YAML 格式错误** | 使用 PyYAML 重新序列化 → 降级重试 |
| **Beat 遗漏** | 对比输入/输出 Beat 数量 → 补充遗漏 |
| **source_location 不准确** | 使用模糊匹配修正 |

---

## 4. Few-Shot 示例设计

### 4.1 示例选择原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **多样性** | 覆盖不同类型的输入 | 简单对白、复杂对白、多角色对话 |
| **代表性** | 代表常见场景 | 日常对话、争吵、内心独白 |
| **难度递增** | 从简单到复杂 | 示例 1 简单 → 示例 2 中等 → 示例 3 复杂 |

### 4.2 Few-Shot 示例库

#### 4.2.1 character_extractor 示例

```json
// prompts/few_shots/character_extractor_examples.json

{
  "examples": [
    {
      "input": "\"你好！\"李明笑着说。",
      "output": {
        "characters": [
          {"name": "李明", "aliases": [], "gender": "男", "first_appearance": "开头"}
        ]
      }
    },
    {
      "input": "\"小李，快来！\"王经理喊道。李明跑过来：\"王总，什么事？\"",
      "output": {
        "characters": [
          {"name": "李明", "aliases": ["小李"], "gender": "男", "first_appearance": "开头"},
          {"name": "王经理", "aliases": ["王总"], "gender": "男", "first_appearance": "开头"}
        ]
      }
    }
  ]
}
```

#### 4.2.2 dialogue_parser 示例

```json
// prompts/few_shots/dialogue_parser_examples.json

{
  "examples": [
    {
      "input": "\"你好！\"李明笑着说，\"好久不见。\"",
      "characters": ["李明"],
      "output": {
        "beats": [
          {
            "type": "dialogue",
            "character": "李明",
            "content": "你好！好久不见。",
            "emotion": "友善"
          }
        ]
      }
    },
    {
      "input": "王芳点了点头：\"你好。\"她转身离开。",
      "characters": ["王芳"],
      "output": {
        "beats": [
          {
            "type": "action",
            "content": "王芳点了点头"
          },
          {
            "type": "dialogue",
            "character": "王芳",
            "content": "你好。",
            "emotion": "平静"
          },
          {
            "type": "action",
            "content": "她转身离开"
          }
        ]
      }
    }
  ]
}
```

---

## 5. 错误处理策略

### 5.1 错误分类与处理

| 错误类型 | 检测方式 | 处理策略 | 重试次数 |
|---------|---------|---------|---------|
| **LLM 输出格式错误** | JSON/YAML 解析失败 | 自动修复 → 降级重试 → 标记 `[PARSE_ERROR]` | 3 |
| **LLM API 错误** | HTTP 状态码 | 429 限速退避重试；401/403 直接报错 | 5（仅 429） |
| **网络错误** | 连接超时 | 重试 3 次，指数退避 | 3 |
| **角色引用不存在** | 校验阶段 | 标记为 `[UNKNOWN_CHARACTER]`，不中断流程 | 0（不重试） |
| **场景覆盖不全** | 统计信息 | 校验阶段标记警告 | 0（不重试） |

### 5.2 自动修复策略详细实现

```python
# prompts/auto_fix.py

import json
import re
from typing import dict, str

def auto_fix_llm_output(raw: str, schema: dict) -> dict | None:
    """
    尝试自动修复 LLM 输出格式错误
    
    Args:
        raw: LLM 原始输出
        schema: JSON Schema 定义
        
    Returns:
        修复后的 dict，如果无法修复则返回 None
    """
    
    # 策略 1：提取 <json>...</json> 或 ```json ... ``` 代码块
    code_block = extract_code_block(raw)
    if code_block:
        try:
            return json.loads(code_block)
        except json.JSONDecodeError:
            pass  # 继续尝试其他策略
    
    # 策略 2：修复常见 JSON 错误
    fixed = raw
    fixed = fixed.replace("'", "\"")          # 单引号 → 双引号
    fixed = re.sub(r",\s*}", "}", fixed)   # 去掉尾逗号
    fixed = re.sub(r",\s*\]", "]", fixed)   # 去掉数组中尾逗号
    fixed = fixed.replace("\n", "\\n")         # 未转义换行
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # 策略 3：让 LLM 自己修复（附加修正 Prompt）
    # 由调用方处理：将原始输出和错误信息传给 LLM，要求重新输出纯 JSON
    return None  # 返回 None 表示需要降级重试


def extract_code_block(text: str) -> str | None:
    """
    从文本中提取代码块（<json>...</json> 或 ```json ... ```）
    """
    
    # 模式 1：<json>...</json>
    pattern1 = r"<json>([\s\S]*?)</json>"
    match1 = re.search(pattern1, text)
    if match1:
        return match1.group(1).strip()
    
    # 模式 2：```json ... ```
    pattern2 = r"```json\s*([\s\S]*?)\s*```"
    match2 = re.search(pattern2, text)
    if match2:
        return match2.group(1).strip()
    
    # 模式 3：``` ... ```（无语言标识）
    pattern3 = r"```\s*([\s\S]*?)\s*```"
    match3 = re.search(pattern3, text)
    if match3:
        return match3.group(1).strip()
    
    return None


def build_retry_prompt(original_prompt: str, raw_output: str, error_msg: str) -> str:
    """
    构建重试 Prompt（策略 3）
    """
    
    retry_prompt = f"""
{original_prompt}

---
⚠️ 上次输出格式有误：{error_msg}

上次输出：
```
{raw_output}
```

请严格按照 JSON Schema 输出，不要附加任何解释。
"""
    
    return retry_prompt
```

### 5.3 降级重试流程

```python
# prompts/prompt_executor.py

import json
from typing import Any, dict
from openai import OpenAI

class PromptExecutor:
    """Prompt 执行器（含错误处理）"""
    
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model
    
    async def execute(
        self,
        prompt_template: str,
        variables: dict[str, Any],
        schema: dict,
        max_retries: int = 3,
    ) -> dict:
        """
        执行 Prompt，包含自动修复和降级重试
        
        Args:
            prompt_template: Prompt 模板
            variables: 模板变量
            schema: JSON Schema 定义
            max_retries: 最大重试次数
            
        Returns:
            解析后的 dict
        """
        
        # 1. 渲染 Prompt
        prompt = prompt_template.format(**variables)
        
        # 2. 调用 LLM
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                
                raw_output = response.choices[0].message.content
                
                # 3. 尝试解析
                try:
                    result = json.loads(raw_output)
                    return result
                
                except json.JSONDecodeError as e:
                    # 4. 尝试自动修复
                    fixed = auto_fix_llm_output(raw_output, schema)
                    if fixed is not None:
                        return fixed
                    
                    # 5. 自动修复失败，准备重试
                    if attempt < max_retries - 1:
                        # 构建重试 Prompt
                        prompt = build_retry_prompt(
                            prompt_template.format(**variables),
                            raw_output,
                            str(e),
                        )
                        continue
                    else:
                        # 重试次数用尽，标记错误
                        return {
                            "error": "PARSE_ERROR",
                            "message": str(e),
                            "raw_output": raw_output,
                        }
            
            except Exception as e:
                # LLM API 调用失败
                if attempt < max_retries - 1:
                    continue
                else:
                    raise e
        
        # 理论上不会到达这里
        raise RuntimeError("重试次数用尽")
```

---

## 6. Token 优化策略（质询修复 #4）

> **质询发现问题**：Prompt 模板没有考虑 Token 优化，长文本可能超出 LLM 上下文窗口。
>
> **解决方案**：智能分段 + 并行处理 + 结果合并。

### 6.1 问题背景

V1 版本需要支持 **10 万字** 的小说，但 LLM 的上下文窗口有限：

| 模型 | 上下文窗口 | 说明 |
|------|------------|------|
| gpt-3.5-turbo | 4K tokens | 约 2000 中文字符 |
| gpt-4o-mini | 128K tokens | 约 64000 中文字符 |
| gpt-4o | 128K tokens | 约 64000 中文字符 |
| DeepSeek-V2 | 128K tokens | 约 64000 中文字符 |

**问题**：如果小说文本很长（如 10 万字），直接放入 Prompt 会超出上下文窗口。

### 6.2 优化策略

#### 策略 1：智能分段（推荐）

```python
# prompts/prompt_executor.py

class PromptExecutor:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model
        self.max_context_tokens = 128000  # 根据模型调整（gpt-4o-mini = 128K）
        
    def _count_tokens(self, text: str) -> int:
        """
        计算文本的 Token 数
        
        注意：这是粗略估计，实际 Token 数需要使用 tiktoken 库
        1 个中文字符 ≈ 2 个 Token
        1 个英文单词 ≈ 1-2 个 Token
        """
        # 简化版：1 个中文字符 = 2 个 Token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len(text.split()) - chinese_chars
        return chinese_chars * 2 + english_words
    
    def _split_text(self, text: str, max_tokens: int) -> list[str]:
        """
        将文本分割为多个片段，每个片段不超过 max_tokens
        
        分割策略：
        1. 优先按章节分割（如果有章节标题）
        2. 否则按段落分割
        3. 最后按句子分割
        """
        max_chars = max_tokens // 2  # 1 个中文字符 ≈ 2 个 Token
        
        segments = []
        current_segment = ""
        
        # 策略 1：按章节分割
        if "第" in text and "章" in text:
            chapters = re.split(r"(?=第\d+章)", text)
            for chapter in chapters:
                if self._count_tokens(chapter) > max_tokens:
                    # 单个章节超长，继续分割
                    sub_segments = self._split_by_paragraph(chapter, max_chars)
                    segments.extend(sub_segments)
                else:
                    segments.append(chapter)
        else:
            # 策略 2：按段落分割
            segments = self._split_by_paragraph(text, max_chars)
        
        return segments
    
    def _split_by_paragraph(self, text: str, max_chars: int) -> list[str]:
        """按段落分割（双换行为段落分隔符）"""
        paragraphs = text.split("\n\n")
        segments = []
        current_segment = ""
        
        for para in paragraphs:
            if len(current_segment) + len(para) > max_chars:
                if current_segment:
                    segments.append(current_segment)
                current_segment = para
            else:
                current_segment += "\n\n" + para if current_segment else para
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
```

#### 策略 2：并行处理

```python
# prompts/prompt_executor.py

class PromptExecutor:
    async def execute(
        self,
        prompt_template: str,
        variables: dict[str, Any],
        schema: dict,
        max_retries: int = 3,
    ) -> dict:
        """
        执行 Prompt，包含自动修复和降级重试
        
        优化：如果输入文本过长，自动分段并并行处理
        """
        
        # 1. 检查文本长度
        novel_text = variables.get("novel_text", "")
        if self._count_tokens(novel_text) > self.max_context_tokens:
            # 分段处理
            segments = self._split_text(novel_text, self.max_context_tokens)
            
            # 并行处理所有分段
            tasks = [
                self._execute_single(prompt_template, {**variables, "novel_text": seg})
                for seg in segments
            ]
            results = await asyncio.gather(*tasks)
            
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

#### 策略 3：结果合并

```python
# prompts/prompt_executor.py

class PromptExecutor:
    def _merge_results(self, results: list[dict]) -> dict:
        """
        合并多个分段的结果
        
        不同步骤的合并策略不同：
        - character_extractor：合并角色列表（去重）
        - scene_splitter：合并场景列表（重新编号）
        - dialogue_parser：合并 Beat 列表
        - emotion_tagger：合并 Beat 列表
        """
        
        if not results:
            return {}
        
        # 假设所有结果都是 {"characters": [...]} 格式
        # 实际情况需要根据步骤类型定制
        
        merged = {"characters": []}
        
        for result in results:
            if "characters" in result:
                for char in result["characters"]:
                    # 去重（根据 name 字段）
                    if not any(c["name"] == char["name"] for c in merged["characters"]):
                        merged["characters"].append(char)
        
        return merged
```

### 6.3 Token 优化建议

| 建议 | 说明 | 示例 |
|------|------|------|
| **使用更短的 Prompt** | 移除冗余说明，使用简洁语言 | "提取角色" vs "你需要从以下文本中提取所有角色的名称和基本信息..." |
| **减少 Few-shot 示例** | 每个示例消耗 Token | 从 3 个示例减少到 2 个 |
| **使用 Chat API** | Chat API 的 Token 计算更高效 | `client.chat.completions.create()` vs `client.completions.create()` |
| **缓存常见结果** | 如果多章使用相同的 Prompt，可以缓存结果 | V2 实现 |

---

## 7. Prompt 优化策略

### 7.1 优化方法

| 方法 | 说明 | 示例 |
|------|------|------|
| **Chain-of-Thought** | 让 LLM 先思考再输出 | "请先分析...再输出..." |
| **Self-Consistency** | 多次采样，选择最一致的结果 | 采样 5 次，选择出现次数最多的结果 |
| **Tree-of-Thought** | 探索多个推理路径 | 复杂任务使用（V2） |
| **Prompt 压缩** | 减少 token 消耗 | 移除冗余说明，使用简洁语言 |

### 6.2 Prompt 版本管理

```
prompts/
├── v1/
│   ├── character_extractor.md
│   └── ...
├── v2/
│   ├── character_extractor.md  # 优化后的版本
│   └── ...
└── few_shots/  # 共享的 few-shot 示例库
```

---

## 7. Prompt 测试与评估

### 7.1 测试用例设计

| 测试类型 | 说明 | 示例 |
|---------|------|------|
| **单元测试** | 测试单个 Prompt 的准确性 | 输入固定文本，检查输出是否符合预期 |
| **集成测试** | 测试整个 Pipeline | 输入完整小说，检查最终 YAML 是否正确 |
| **边界测试** | 测试极端情况 | 空输入、超长输入、特殊字符 |
| **回归测试** | 确保优化不引入新错误 | 每次优化后运行完整测试套件 |

### 7.2 评估指标

| 指标 | 说明 | 目标 |
|------|------|------|
| **准确率** | 输出正确的比例 | ≥ 95% |
| **召回率** | 提取完整的比例 | ≥ 90% |
| **F1 分数** | 准确率和召回率的调和平均 | ≥ 92% |
| **Token 消耗** | 每次调用的 token 数 | 尽量降低 |
| **耗时** | 每次调用的耗时 | ≤ 模型超时时间 |

---

## 8. 附录

### 8.1 Prompt 模板汇总

| 步骤 | Prompt 模板文件 | Few-Shot 示例文件 |
|------|----------------|-------------------|
| character_extractor | `prompts/character_extractor.md` | `prompts/few_shots/character_extractor_examples.json` |
| scene_splitter | `prompts/scene_splitter.md` | `prompts/few_shots/scene_splitter_examples.json` |
| dialogue_parser | `prompts/dialogue_parser.md` | `prompts/few_shots/dialogue_parser_examples.json` |
| emotion_tagger | `prompts/emotion_tagger.md` | `prompts/few_shots/emotion_tagger_examples.json` |
| yaml_generator | `prompts/yaml_generator.md` | `prompts/few_shots/yaml_generator_examples.json` |
| quality_checker | `prompts/quality_checker.md` | `prompts/few_shots/quality_checker_examples.json` |

### 8.2 参考资料

- **OpenAI Prompt Engineering Guide**：https://platform.openai.com/docs/guides/prompt-engineering
- **Pydantic Documentation**：https://docs.pydantic.dev/
- **JSON Schema Specification**：https://json-schema.org/

---

## 9. 总结

本文档详细设计了 InkScript V1 版本的所有 Prompt 模板，包括：

1. ✅ **Pipeline 步骤 Prompt 模板**：6 个步骤的详细 Prompt 设计
2. ✅ **Few-Shot 示例设计**：示例选择原则和示例库
3. ✅ **错误处理策略**：自动修复、降级重试、错误分类
4. ✅ **Prompt 优化策略**：Chain-of-Thought、Self-Consistency
5. ✅ **Prompt 测试与评估**：测试用例设计、评估指标

**下一步**：
- 根据本文档实现 `prompts/` 目录下的模板文件
- 准备 few-shot 示例库
- 实现 `PromptExecutor` 类

---

**文档状态**：✅ 已完成，待用户确认

**最后更新**：2026-06-06
