# Prompt 工程设计文档

## 1. 总体策略

### 1.1 分段处理 vs 一次性处理
小说文本可能很长（3章以上），一次性丢给 LLM 会导致：
- 超出上下文窗口
- 输出质量下降（长文本注意力分散）
- 角色一致性难保证

**策略**：先做章节分割，再按章节逐步处理，最后全局合并与校验。

### 1.2 规则引擎 vs LLM
| 环节 | 方法 | 原因 |
|------|------|------|
| 章节分割 | 规则（正则匹配） | 章节标题通常有明确格式（"第X章"） |
| 角色识别 | LLM + 规则 | LLM 理解上下文，规则做去重和别名映射 |
| 场景分割 | LLM | 场景边界依赖语义理解（时空变化、氛围转换） |
| 对白/动作分类 | LLM | 需要理解叙述逻辑 |
| 情绪标注 | LLM | 情绪判断依赖上下文和语气理解 |
| 别名合并 | LLM + 规则 | LLM 识别同一人物，规则做 ID 映射 |

### 1.3 输出格式约束
所有 LLM 调用均要求输出 JSON，原因：
- JSON 可直接解析，避免 YAML 缩进错误
- 可用 pydantic 校验
- 最后一步再统一转 YAML

关键技巧：
- 在 system prompt 中给出完整的输出 JSON Schema
- 提供 1-2 个 few-shot 示例
- 要求 LLM 严格遵循格式，不要输出任何多余文本

---

## 2. 各环节 Prompt 设计

### 2.1 角色识别

**目标**：从小说章节中提取所有角色，识别别名/昵称，判断角色类型。

**System Prompt 核心要点**：
- 你是一个专业的剧本分析助手
- 任务是从小说文本中提取所有出场人物
- 需要识别同一人物的不同称呼（别名/昵称/职位称呼）
- 输出 JSON 数组

**输出格式**：
```json
{
  "characters": [
    {
      "id": "char_001",
      "name": "林晚",
      "aliases": ["她", "咖啡馆老板"],
      "role": "protagonist",
      "description": "半夏咖啡馆的老板，三年前从母亲手中接过店铺",
      "first_appearance": "第一章"
    }
  ]
}
```

**跨章节合并策略**：
- 每章独立提取角色
- 全局合并时，以角色名为 primary key
- 别名冲突时，保留最完整的描述
- 用 LLM 判断不同章节的"她"指代是否为同一人

### 2.2 场景分割

**目标**：按时空变化将章节拆分为独立场景。

**System Prompt 核心要点**：
- 场景切换的条件：地点变化、时间跳转、氛围突变
- 不是每个段落都是新场景
- 同一地点、连续时间的对话属于同一场景
- 输出每个场景的起止位置和元信息

**输出格式**：
```json
{
  "scenes": [
    {
      "id": "scene_001",
      "chapter_id": "ch_001",
      "title": "咖啡馆的日常",
      "time": "afternoon",
      "location": {
        "type": "interior",
        "name": "半夏咖啡馆"
      },
      "environment": "秋天下午，桂花香从窗外飘入",
      "start_marker": "秋天的风裹着桂花的甜味",
      "end_marker": "他把纸条留在桌上",
      "characters_present": ["char_001", "char_002"],
      "summary": "林晚在咖啡馆遇到神秘的陆行舟"
    }
  ]
}
```

**难点与策略**：
- 模糊边界：让 LLM 给出 confidence 分数，低于阈值时标记为"待确认"
- 章节开头通常自动成为新场景
- "---"分隔符暗示场景或时间跳转

### 2.3 对白/动作/旁白解析

**目标**：将每个场景内的文本拆解为结构化的台词、动作和旁白。

**System Prompt 核心要点**：
- 中文小说的引号内容是对白（"" 和「」）
- 引号外的叙述文字需要判断：是动作描写、环境描写、还是旁白
- 内心活动应标记为 "think" 类型
- 旁白/叙述性文字标记为 "voiceover"

**输出格式**：
```json
{
  "elements": [
    {
      "element_type": "action",
      "content": "林晚靠在吧台后面，百无聊赖地擦着杯子",
      "character_ids": ["char_001"]
    },
    {
      "element_type": "dialogue",
      "type": "spoken",
      "character_id": "char_002",
      "content": "请问，有什么推荐的吗？",
      "parenthetical": "低沉沙哑"
    },
    {
      "element_type": "action",
      "content": "他微微点头，拿出手机放在桌上",
      "character_ids": ["char_002"]
    }
  ]
}
```

**关键考量**：
- 中文小说中，叙述者经常在对话之间插入动作描写（"她转身去做咖啡"），这些需要归类为动作
- 有些对白没有明确的说话人标记，需要根据上下文推断
- 长段叙述可能需要拆分为多个元素

### 2.4 情绪标注

**目标**：为每段对白和关键动作标注情绪标签。

**System Prompt 核心要点**：
- 情绪标签不是每个元素都需要，只在情绪明确或与上下文有对比时标注
- 重点关注：情绪转折、情感暗涌、表面平静内心波动
- 使用预定义的情绪标签集（见 schema.py 中的 EmotionTag）

**策略**：
- 与对白解析合并处理，减少 LLM 调用次数
- 在解析 prompt 中同时要求输出 emotion 和 parenthetical 字段
- 单独一轮"情绪复审"用于检查遗漏和矛盾

---

## 3. 上下文管理

### 3.1 长文本分段
- 按章节分段处理
- 每段保留上一段的"上下文摘要"（最后 200 字 + 角色状态）
- 角色表作为全局上下文，每次调用都传入

### 3.2 一致性保障
- 角色ID必须与前序步骤输出的角色表一致
- 场景ID必须全局唯一
- 每个处理环节的输出都经过 pydantic 校验

### 3.3 渐进式处理流程
```
小说全文
  │
  ├──[规则] 章节分割 → chapters[]
  │
  ├──[LLM] 角色识别（逐章）→ characters[] → 全局合并
  │
  ├──[LLM] 场景分割（逐章）→ scenes[] + 上下文摘要
  │
  ├──[LLM] 对白/动作解析（逐场景）→ elements[]
  │       └── 同时输出 emotion + parenthetical（含情绪复审）
  │
  ├──[规则] YAML 组装 + pydantic 校验
  │
  ├──[LLM] 情绪标注（emotion_tagger）→ 逐场景标注情绪（含复审逻辑）
  │
  ├──[规则] 分段结果合并（如分段过）
  │
  ├──[LLM] YAML 生成 + 校验（yaml_generator）
  │
  ├──[LLM] 质量检查（quality_checker）→ 生成 conversion_notes
  │
  └──[Hook] after_convert → post_processor Skills
```

> 说明：
> - **情绪复审**已合并到 `emotion_tagger` 步骤中，不再单独调用 LLM
> - **质量检查**对应 `architecture.md` 中新增的 `quality_checker` 步骤（放在 `yaml_generator` 之后）
> - 与 `architecture.md` §3.3 的 Pipeline 步骤完全对应

---

## 4. Token 估算

| 环节 | 输入估算 | 输出估算 | 调用次数 |
|------|---------|---------|---------|
| 角色识别 | ~2K/章 | ~0.5K | N(章数) |
| 场景分割 | ~2K/章 | ~1K | N |
| 对白解析 | ~1K/场景 | ~2K | M(场景数) |
| 情绪复审 | ~3K | ~1K | 1 |
| 质量检查 | ~5K | ~1K | 1 |

3章小说估算：约 15-20K 总 token 输入，5-8K 输出

---

## 5. 错误处理

| 场景 | 处理方式 |
|------|---------|
| LLM 输出不是合法 JSON | 重试 2 次，追加修正提示 |
| 角色ID引用不存在 | 标记为 "unknown_character"，记录到 conversion_notes |
| 场景分割置信度低 | 标记为 "needs_review"，保留 LLM 建议的分割点 |
| 情绪标签不在预定义集合 | 映射到最接近的标签，记录原始标签 |
| 超长章节 | 按段落分割，每段不超过 3000 字 |

---

## 6. 扩展性设计关联

> 本 Prompt 工程设计遵循《扩展性设计详细规范.md》中的原则。

### 6.1 Prompt 模板的可扩展性设计

**设计原则**：
1. **Prompt 模板外置** —— 不硬编码在代码中，放在 `src/prompts/` 目录
2. **模板可配置** —— 通过配置文件调整 Prompt 参数（如温度、示例数量）
3. **模板版本化** —— 每个模板有版本号，支持回滚

#### 6.1.1 Prompt 模板文件结构**

```
src/prompts/
├── extract_characters.py      # 角色识别 Prompt 模板
├── merge_aliases.py          # 别名合并 Prompt 模板
├── split_scenes.py           # 场景分割 Prompt 模板
├── parse_dialogue.py         # 对白解析 Prompt 模板
├── tag_emotions.py          # 情绪标注 Prompt 模板
└── template_config.json      # Prompt 配置（温度、示例等）
```

#### 6.1.2 Prompt 模板示例**

```python
# src/prompts/extract_characters.py

EXTRACT_CHARACTERS_PROMPT = """
你是专业的剧本分析助手。

## 任务
从小说文本中提取所有出场人物，识别别名/昵称，判断角色类型。

## 输出格式
{format_instructions}

## 示例
{few_shot_examples}

## 输入文本
{input_text}

## 要求
1. 严格按输出格式返回 JSON
2. 不要输出任何多余文本
3. 别名识别要全面（包括昵称、职位称呼、描述性指代）
"""
```

#### 6.1.3 Prompt 配置示例**

```json
// src/prompts/template_config.json
{
  "extract_characters": {
    "temperature": 0.3,
    "max_tokens": 2048,
    "few_shot_count": 2,
    "version": "1.0.0"
  },
  "split_scenes": {
    "temperature": 0.2,
    "max_tokens": 4096,
    "few_shot_count": 1,
    "version": "1.0.0"
  }
}
```

### 6.2 与 Pipeline Hook 的集成**

**场景**：需要在 Prompt 执行前后注入自定义逻辑（如日志记录、结果后处理）。

**方案**：通过 Pipeline Hook 机制实现（见《扩展性设计详细规范》2.1）。

```python
# 示例：注册 Prompt 执行前后的 Hook
from src.core.pipeline import Pipeline

pipeline = Pipeline()

# 注册 before_step Hook：记录 Prompt 输入
async def log_prompt_input(context, **kwargs):
    step_name = kwargs.get("step_name")
    logger.info(f"Step '{step_name}' 输入: {context.novel_text[:100]}...")
    return context

pipeline.hook("before_step", log_prompt_input)

# 注册 after_step Hook：记录 Prompt 输出
async def log_prompt_output(context, **kwargs):
    step_name = kwargs.get("step_name")
    logger.info(f"Step '{step_name}' 输出: {context.beats[:5]}...")
    return context

pipeline.hook("after_step", log_prompt_output)
```

### 6.3 与 Skill 系统的集成**

**场景**：需要自定义 Prompt 模板（如针对特定类型小说的优化 Prompt）。

**方案**：通过 Skill 系统实现（见《扩展性设计详细规范》7.1）。

```python
# 示例：创建自定义 Prompt Skill
# my-custom-prompt-skill/skill.json
{
  "name": "custom-dialogue-parser",
  "type": "pre_processor",
  "version": "1.0.0",
  "description": "针对武侠小说的对白解析 Prompt",
  "author": "用户名",
  "hooks": [
    {
      "event": "before_step",
      "function": "custom_dialogue_prompt",
      "priority": 10
    }
  ]
}

# my-custom-prompt-skill/main.py
async def custom_dialogue_prompt(context, **kwargs):
    """自定义对白解析 Prompt"""
    # 使用针对武侠小说优化的 Prompt
    custom_prompt = """
    你是专业的武侠小说剧本分析助手。
    
    ## 特殊要求
    1. 识别武侠小说的特有对白风格（如"阁下"、"在下"等）
    2. 注意内力传音、传音入密等特殊交流方式
    ...
    """
    
    # 替换默认 Prompt
    context.custom_prompt = custom_prompt
    return context
```

### 6.4 Prompt 版本管理**

**设计**：Prompt 模板版本与 Schema 版本同步（见《扩展性设计详细规范》3.1.4）。

| Schema 版本 | Prompt 版本 | 说明 |
|---------------|---------------|------|
| v1.0.0 | v1.0.0 | 初始版本 |
| v1.1.0 | v1.1.0 | Prompt 优化，向后兼容 |
| v2.0.0 | v2.0.0 | 支持新 Beat 类型，不向后兼容 |

### 6.5 与《扩展性设计详细规范》的关联**

| prompt-design.md 章节 | 对应的扩展性设计规范 | 说明 |
|------------------------|--------------------------------|------|
| 1.3 输出格式约束 | 2.1.1 Hook 接口定义 | Prompt 输出通过 Hook 校验 |
| 2.1 角色识别 | 2.2.1 Step 接口定义 | Prompt 作为 Step 的一部分 |
| 3.1 长文本分段 | 9.1 增量转换接口 | Prompt 需要处理分段后的文本 |
| 4. Token 估算 | 2.2.3 Step 执行顺序控制 | Token 估算影响并发度设置 |
| 5. 错误处理 | 2.1.5 Hook 异常处理策略 | Prompt 错误通过 Hook 处理 |

---

> **详细规范**：请参考《扩展性设计详细规范.md》文档。
