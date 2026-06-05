# 剧本 YAML Schema 设计文档

## 1. 概述

### 1.1 目标与使用场景

本 Schema 定义了「AI 小说转剧本工具」的输出格式规范。核心使用场景为：

1. **AI 自动转换**：将 3 章以上的小说文本自动解析为结构化剧本 YAML，作为初稿输出
2. **作者手工编辑**：作者拿到 YAML 初稿后，用任意文本编辑器即可阅读和修改，无需专业软件
3. **下游消费**：YAML 可被其他工具链读取，导入到 Final Draft、排版系统、拍摄计划工具等

设计目标不是替代 Fountain 或 FDX 等专业剧本格式，而是补足**小说→剧本的中间态**——既保留小说的丰富信息（别名映射、旁白、心理描写），又具备剧本的结构化表达能力。

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **作者友好** | YAML 缩进表示层级，字段名自解释，避免过度嵌套（最深 4 层），作者用 VSCode / Vim 即可编辑 |
| **可编辑性** | 字段粒度适中——对白逐条可改，动作描述整段可换，不会因为改一处而牵动全局 |
| **可扩展** | 每个实体保留 `metadata` 字段，用 key-value 形式挂载扩展信息，不破坏已有结构 |
| **小说适配** | 专门处理小说特征：角色别名映射、旁白→画外音转换、心理描写→动作/OS 标注、叙述性场景描述 |
| **工具友好** | 每个实体有唯一 `id`，角色通过 `character_id` 交叉引用，场景通过 `scene_id` 引用，方便程序遍历和校验 |

---

## 2. Schema 完整定义

以下用 **TypeScript 接口风格** 给出完整定义，每个字段标注类型、必填性、默认值和说明。底部附等价的 YAML 自描述 Schema。

### 2.1 顶层结构

```typescript
interface Script {
  /** 剧本元信息 */
  meta: ScriptMeta;                          // 必填

  /** 角色表，key 为角色 ID */
  characters: Record<CharacterId, Character>; // 必填

  /** 章节/幕列表 */
  acts: Act[];                                // 必填

  /** 全局道具表（可选） */
  props?: Record<PropId, Prop>;

  /** 全局扩展字段 */
  metadata?: Record<string, any>;
}

type CharacterId = string;  // 格式建议: char_xxxx，如 char_001
type SceneId = string;      // 格式建议: sc_xxxx，如 sc_001
type PropId = string;       // 格式建议: prop_xxxx，如 prop_001
```

### 2.2 剧本元信息 ScriptMeta

```typescript
interface ScriptMeta {
  /** 剧本标题 */
  title: string;                             // 必填

  /** 原作名称（若为改编） */
  source_title?: string;                     // 可选，默认 null

  /** 原作作者 */
  source_author?: string;                    // 可选

  /** 改编者 */
  adapter?: string;                          // 可选

  /** 创建时间，ISO 8601 格式 */
  created_at: string;                        // 必填，默认生成时自动填充

  /** 最后修改时间 */
  updated_at?: string;                       // 可选

  /** Schema 版本号，语义化版本 */
  schema_version: string;                    // 必填，默认 "1.0.0"

  /** 整体风格标签，如 ["悬疑", "都市", "黑色幽默"] */
  genres: string[];                          // 必填，至少 1 项

  /** 语言 */
  language?: string;                         // 可选，默认 "zh-CN"

  /** 一句话梗概 */
  logline?: string;                          // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}
```

### 2.3 角色 Character

```typescript
interface Character {
  /** 角色姓名（主称谓，剧本中正式使用的名字） */
  name: string;                              // 必填

  /** 别名/昵称列表（小说中指代同一角色的不同称呼） */
  aliases: string[];                         // 必填，可为空数组

  /** 角色类型 */
  type: "protagonist" | "supporting" | "minor" | "extra";
  // 必填，默认 "supporting"

  /** 角色性别 */
  gender?: "male" | "female" | "other" | "unknown";

  /** 年龄段（小说未必给出精确年龄） */
  age_range?: string;                        // 可选，如 "30岁左右"、"少年"

  /** 角色简介（1-3 句话） */
  description: string;                       // 必填

  /** 角色关系列表 */
  relationships?: CharacterRelationship[];

  /** 角色首次出场的场景 ID */
  first_appearance?: SceneId;                // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}

interface CharacterRelationship {
  /** 关联角色的 ID */
  with: CharacterId;                         // 必填

  /** 关系描述，如 "妻子"、"宿敌"、"同窗" */
  relation: string;                          // 必填

  /** 关系备注（可选，补充说明） */
  note?: string;
}
```

### 2.4 章节/幕 Act

```typescript
interface Act {
  /** 章节 ID */
  id: string;                                // 必填，格式建议: act_01

  /** 章节标题 */
  title: string;                             // 必填

  /** 章节概要（2-5 句话概括本章核心事件） */
  summary: string;                           // 必填

  /** 对应原小说的章节标识，如 "第三章" */
  source_chapter?: string;                   // 可选

  /** 章节情绪基调，如 "压抑→爆发" */
  emotional_arc?: string;                    // 可选

  /** 场景列表 */
  scenes: Scene[];                           // 必填，至少 1 个

  /** 扩展字段 */
  metadata?: Record<string, any>;
}
```

### 2.5 场景 Scene

```typescript
interface Scene {
  /** 场景 ID（全局唯一） */
  id: SceneId;                               // 必填

  /** 场景标题（简短描述，如 "天台对峙"） */
  title: string;                             // 必填

  /** 时间段 */
  time_of_day: "morning" | "afternoon" | "dusk" | "evening" | "night" | "dawn" | "unspecified";
  // 必填，默认 "unspecified"

  /** 内外景 */
  setting: "INT" | "EXT" | "INT/EXT";
  // 必填，默认 "INT"

  /** 具体地点 */
  location: string;                          // 必填，如 "老陈的杂货铺"

  /** 环境描述（氛围、天气、光线等） */
  environment?: string;                      // 可选

  /** 场景中在场的角色 ID 列表 */
  present_characters: CharacterId[];         // 必填，可为空数组（纯旁白场景）

  /** 场景内容（台词与动作的有序序列） */
  beats: Beat[];                             // 必填，可为空数组

  /** 场景转换标记（场景结束后的转场方式） */
  transition?: TransitionType;               // 可选，默认 null（硬切）
  // TransitionType 见下方定义

  /** 节奏标记 */
  pacing?: "slow" | "moderate" | "fast" | "tense" | "climax"; // 可选

  /** 情绪强度（1-10，1=平静，10=极激烈） */
  emotional_intensity?: number;              // 可选，范围 1-10

  /** 场景中的关键道具 */
  key_props?: PropId[];                      // 可选

  /** 伏笔标记 */
  foreshadowing?: Foreshadowing[];           // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}

type TransitionType =
  | "CUT_TO"           // 切到（最常用，默认）
  | "FADE_IN"          // 淡入
  | "FADE_OUT"         // 淡出
  | "DISSOLVE"         // 溶解
  | "SMASH_CUT"        // 猛切
  | "MATCH_CUT"        // 相似物转场
  | "WIPE"             // 擦除
  | "TIME_CUT"         // 时间跳转
  | "FLASHBACK"        // 闪回
  | "FLASH_FORWARD"    // 闪前
  | string;            // 允许自定义转场
```

### 2.6 场景内容单元 Beat

Beat 是场景内的最小叙事单元，一条 Beat 可以是台词、动作、旁白或转场标记中的**一种**。采用联合类型（Tagged Union）设计，通过 `type` 字段区分：

```typescript
type Beat =
  | DialogueBeat
  | ActionBeat
  | NarrationBeat
  | TransitionBeat;

/** ===== 台词 Beat ===== */
interface DialogueBeat {
  type: "dialogue";                          // 必填

  /** 说话角色的 ID */
  character_id: CharacterId;                 // 必填

  /** 原文对白内容 */
  text: string;                              // 必填

  /** 语气/情绪标签 */
  emotion?: string;                          // 可选，如 "愤怒"、"低声下气"、"颤抖"

  /** 台词附注（给演员/导演的补充说明） */
  parenthetical?: string;                    // 可选，如 "（看了一眼手表）"

  /** 是否为画外音 / OS（Off-Screen） */
  is_voiceover?: boolean;                    // 可选，默认 false

  /** 对应小说原文片段（用于溯源对照） */
  source_text?: string;                      // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}

/** ===== 动作/舞台提示 Beat ===== */
interface ActionBeat {
  type: "action";                            // 必填

  /** 动作描述 */
  text: string;                              // 必填

  /** 涉及的角色 ID 列表（可选，方便按角色检索） */
  characters?: CharacterId[];                // 可选

  /** 动作类型标签 */
  action_type?: "movement" | "expression" | "interaction" | "business" | "stunt";
  // 可选
  // movement: 走位/移动
  // expression: 表情/神态
  // interaction: 角色间互动
  // business: 日常小动作（喝茶、翻书等）
  // stunt: 特殊动作/武打

  /** 对应小说原文片段 */
  source_text?: string;                      // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}

/** ===== 旁白/画外音 Beat ===== */
interface NarrationBeat {
  type: "narration";                         // 必填

  /** 旁白内容 */
  text: string;                              // 必填

  /** 旁白子类型 */
  narration_type?: "voiceover" | "title_card" | "epigraph";
  // 可选，默认 "voiceover"
  // voiceover: 画外音旁白
  // title_card: 字幕卡
  // epigraph: 题词/引言

  /** 对应小说原文片段 */
  source_text?: string;                      // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}

/** ===== 场景内转场 Beat ===== */
interface TransitionBeat {
  type: "transition";                        // 必填

  /** 转场方式 */
  transition: TransitionType;                // 必填

  /** 转场备注 */
  note?: string;                             // 可选，如 "（闪回到十年前）"
}
```

### 2.7 道具 Prop

```typescript
interface Prop {
  /** 道具名称 */
  name: string;                              // 必填

  /** 道具描述 */
  description?: string;                      // 可选

  /** 首次出现的场景 ID */
  first_appearance?: SceneId;                // 可选

  /** 是否为关键道具（推动剧情的道具） */
  is_key_prop?: boolean;                     // 可选，默认 false

  /** 扩展字段 */
  metadata?: Record<string, any>;
}
```

### 2.8 伏笔标记 Foreshadowing

```typescript
interface Foreshadowing {
  /** 伏笔描述 */
  hint: string;                              // 必填，如 "老陈收到的神秘信件"

  /** 伏笔类型 */
  type?: "plant" | "payoff" | "callback";
  // 可选
  // plant: 埋下伏笔
  // payoff: 伏笔回收
  // callback: 呼应前文

  /** 关联的场景 ID（回收伏笔时指向 payoff 所在场景） */
  linked_scene_id?: SceneId;                 // 可选

  /** 扩展字段 */
  metadata?: Record<string, any>;
}
```

### 2.9 YAML 自描述 Schema

以下为等价的 YAML 格式定义，方便直接嵌入项目：

```yaml
# script-schema.yaml — 剧本 YAML Schema 定义 v1.0.0
$schema_version: "1.0.0"

script:
  meta:
    title: string          # 必填 | 剧本标题
    source_title: string   # 可选 | 原作名称
    source_author: string  # 可选 | 原作作者
    adapter: string        # 可选 | 改编者
    created_at: string     # 必填 | ISO 8601 时间
    updated_at: string     # 可选 | 最后修改时间
    schema_version: string # 必填 | 默认 "1.0.0"
    genres: string[]       # 必填 | 风格标签，至少1项
    language: string       # 可选 | 默认 "zh-CN"
    logline: string        # 可选 | 一句话梗概
    metadata: map          # 可选 | 扩展字段

  characters:
    <character_id>:        # 必填 | key 为角色唯一 ID
      name: string         # 必填 | 角色姓名
      aliases: string[]    # 必填 | 别名列表，可为空
      type: enum           # 必填 | protagonist|supporting|minor|extra，默认 supporting
      gender: enum         # 可选 | male|female|other|unknown
      age_range: string    # 可选 | 年龄段
      description: string  # 必填 | 角色简介
      relationships:       # 可选 | 关系列表
        - with: string     #   必填 | 关联角色 ID
          relation: string #   必填 | 关系描述
          note: string     #   可选 | 关系备注
      first_appearance: string  # 可选 | 首次出场场景 ID
      metadata: map        # 可选 | 扩展字段

  acts:
    - id: string           # 必填 | 章节 ID
      title: string        # 必填 | 章节标题
      summary: string      # 必填 | 章节概要
      source_chapter: string  # 可选 | 原小说章节标识
      emotional_arc: string  # 可选 | 情绪基调
      scenes:              # 必填 | 场景列表
        - id: string       #   必填 | 场景 ID（全局唯一）
          title: string    #   必填 | 场景标题
          time_of_day: enum  # 必填 | morning|afternoon|dusk|evening|night|dawn|unspecified
          setting: enum    # 必填 | INT|EXT|INT/EXT，默认 INT
          location: string #   必填 | 具体地点
          environment: string  # 可选 | 环境描述
          present_characters: string[]  # 必填 | 在场角色 ID
          beats:           #   必填 | 内容序列
            - type: enum   #     必填 | dialogue|action|narration|transition
              # --- dialogue 特有 ---
              character_id: string  # 条件必填 | type=dialogue 时必填
              text: string          # 必填 | 对白/动作/旁白/转场备注的内容
              emotion: string       # 可选 | 语气/情绪
              parenthetical: string # 可选 | 台词附注
              is_voiceover: boolean # 可选 | 默认 false
              # --- action 特有 ---
              characters: string[]  # 可选 | 涉及角色 ID
              action_type: enum     # 可选 | movement|expression|interaction|business|stunt
              # --- narration 特有 ---
              narration_type: enum  # 可选 | voiceover|title_card|epigraph，默认 voiceover
              # --- transition 特有 ---
              transition: enum      # 条件必填 | type=transition 时必填
              # --- 通用 ---
              source_text: string   # 可选 | 小说原文溯源
              metadata: map         # 可选 | 扩展字段
          transition: enum  #   可选 | 场景结束转场方式
          pacing: enum      #   可选 | slow|moderate|fast|tense|climax
          emotional_intensity: int  # 可选 | 1-10
          key_props: string[]       # 可选 | 关键道具 ID
          foreshadowing:            # 可选 | 伏笔标记
            - hint: string          #   必填 | 伏笔描述
              type: enum            #   可选 | plant|payoff|callback
              linked_scene_id: string  # 可选 | 关联场景 ID
              metadata: map         #   可选 | 扩展字段
          metadata: map      # 可选 | 扩展字段
      metadata: map          # 可选 | 扩展字段

  props:
    <prop_id>:              # 可选 | key 为道具唯一 ID
      name: string          # 必填 | 道具名称
      description: string   # 可选 | 道具描述
      first_appearance: string  # 可选 | 首次出现场景 ID
      is_key_prop: boolean  # 可选 | 默认 false
      metadata: map         # 可选 | 扩展字段

  metadata: map              # 可选 | 全局扩展字段
```

---

## 3. 设计原因

### 3.1 顶层结构：为什么用 `meta / characters / acts / props` 四大块

**拆分而非嵌套**是核心思路。将角色表、道具表从场景树中抽离到顶层，有三个好处：

1. **去重与一致性**：同一个角色在 50 个场景中出现，只需在 `characters` 定义一次，场景中用 `character_id` 引用。如果角色表嵌在每个场景里，修改角色信息要改 50 处。
2. **快速查阅**：作者打开 YAML 文件，扫一眼 `characters` 就知道全剧有多少人、谁是谁。这比在场景树里翻找角色信息效率高一个数量级。
3. **程序处理友好**：角色 ID 是外键，程序可以轻松做交叉校验（如"场景引用了不存在的角色"）。

`props` 放顶层也是同理——关键道具贯穿多场戏，必须在全局可查。

### 3.2 角色表：为什么需要 aliases（别名映射）

这是**小说→剧本转换最独特的需求**。小说中同一角色常有多种称呼：

- 林小雨 → "小雨"（昵称）、"林总"（职场称呼）、"那个穿红裙子的女人"（旁白描述性指代）
- AI 转换时必须把所有别名归并到同一个 `character_id`，否则会产生大量"幽灵角色"

`aliases` 字段的作用：
1. **AI 提取阶段**：用来训练/校验别名识别的准确性
2. **作者审阅阶段**：作者一眼就能看到"哪些称呼被归到了这个角色"，如有遗漏可补充
3. **溯源阶段**：`source_text` 里可能出现任意别名，但 `character_id` 始终指向唯一的角色实体

### 3.3 角色关系：为什么是列表而非图结构

角色关系用 `relationships: [{with, relation, note}]` 的扁平列表表达，而非邻接矩阵或嵌套图。原因：

1. **YAML 可读性**：邻接矩阵在 YAML 里写起来是 N×N 的稀疏表格，阅读体验极差
2. **增量编辑**：加一条关系只需追加一条记录，不需要维护矩阵维度
3. **关系非对称**："A 是 B 的上司"和"B 是 A 的下属"是两条独立记录，各自可以有 note
4. **够用即可**：本工具关注剧本结构而非社交网络分析，简单列表足够

### 3.4 Beat 设计：为什么用 Tagged Union 而非把所有字段平铺

每个 Beat 只有 4 种类型（dialogue / action / narration / transition），如果平铺所有字段：

```yaml
# ❌ 平铺方案——字段太多，大部分是 null
- character_id: char_001
  dialogue: "你到底想怎样？"
  emotion: "愤怒"
  action: null
  narration: null
  action_type: null
  narration_type: null
  transition_type: null
```

Tagged Union 方案：

```yaml
# ✅ Tagged Union——只写需要的字段
- type: dialogue
  character_id: char_001
  text: "你到底想怎样？"
  emotion: "愤怒"
```

对比明显：**Tagged Union 更短、更清晰、更不容易填错字段**。代价是解析代码需要根据 `type` 分支处理，但这是程序的事，不是作者的事。

### 3.5 场景转换：为什么在两个层级都支持

转场标记出现在两个位置：
1. **Scene.transition**（场景末尾）：标记本场景结束后的转场方式
2. **Beat（type=transition）**（场景内部）：标记场景内部的特殊转场（如闪回、闪前后回到当前时间线）

这样设计是因为：
- 大多数转场发生在场景之间，放在 `Scene.transition` 最自然
- 但闪回/闪前/梦境的嵌套转场发生在场景内部，需要用 Beat 处理
- 两个层级互不冲突，作者根据实际需要选择

### 3.6 哪些字段是转换必需的，哪些是辅助增强

| 字段 | 类别 | 说明 |
|------|------|------|
| `meta.title` | **必需** | 没有标题就不是剧本 |
| `characters.*.name` | **必需** | 没有角色名无法展开对白 |
| `characters.*.aliases` | **必需** | 别名识别是小说转剧本的核心难题 |
| `acts.*.scenes.*.beats` | **必需** | 场景内容是剧本主体 |
| `beats[type=dialogue].character_id` | **必需** | 对白必须关联角色 |
| `beats[type=dialogue].text` | **必需** | 对白必须有内容 |
| `scene.location / setting` | **必需** | 剧本场景头必须标注内外景和地点 |
| `scene.time_of_day` | **必需** | 影响灯光设计和拍摄安排 |
| — | — | — |
| `characters.*.relationships` | **增强** | 帮助理解人物关系，不影响场景生成 |
| `beats[type=dialogue].emotion` | **增强** | 给演员/导演参考，不参与结构 |
| `scene.pacing` | **增强** | 辅助节奏分析，非结构必需 |
| `scene.emotional_intensity` | **增强** | 辅助情绪曲线可视化 |
| `scene.foreshadowing` | **增强** | 伏笔追踪，辅助创作审查 |
| `scene.key_props` | **增强** | 道具管理，辅助拍摄计划 |
| `beats[*].source_text` | **增强** | 小说溯源，方便对照修改 |
| `scene.environment` | **增强** | 氛围描述，辅助美术设计 |
| `meta.logline` | **增强** | 梗概，方便归档和推介 |
| `props` 整个顶层块 | **增强** | 道具管理是锦上添花 |

### 3.7 与 Fountain / FDX 的对比和取舍

| 维度 | Fountain | FDX (Final Draft) | 本 Schema (YAML) |
|------|----------|--------------------|--------------------|
| **格式** | 纯文本标记 | 二进制/XML专有格式 | YAML 文本 |
| **可读性** | 极高，像写纯文本 | 需专用软件 | 高，结构化但缩进清晰 |
| **可编辑性** | 任何编辑器 | 必须用 Final Draft | 任何编辑器 |
| **元信息** | 极少（标题、作者） | 丰富但封闭 | 丰富且开放 |
| **角色管理** | 无，角色名散落各处 | 有角色追踪 | 有完整角色表+别名 |
| **场景结构** | 隐式（靠 Scene Heading 识别） | 显式 | 显式，层级清晰 |
| **情绪/节奏标注** | 不支持 | 部分支持（通过颜色标记） | 原生支持 |
| **小说溯源** | 不支持 | 不支持 | `source_text` 字段 |
| **扩展性** | 低（标准固定） | 低（专有格式） | 高（metadata 字段） |
| **标准程度** | 业界标准 | 业界标准 | 本项目专用 |

**取舍决策**：

1. **不用 Fountain 作为输出格式**：Fountain 是写剧本的好格式，但它缺少角色表、元信息、情绪标注等结构化字段。它更像 Markdown——好写但不好解析。我们的场景需要**AI 写、人改、程序验**，YAML 的结构化更合适。

2. **不用 FDX 作为输出格式**：FDX 是最终交付格式，不是中间编辑格式。它的专有性意味着作者必须购买 Final Draft 才能编辑，违背"作者友好"原则。正确的做法是**YAML → FDX 导出**作为单独功能。

3. **可导出为 Fountain**：作为轻量级输出选项。YAML 中的场景信息可以无损转写为 Fountain 的 Scene Heading + Action + Dialogue 格式，只是丢失情绪标注等增强字段。

4. **保留 `metadata` 扩展点**：如果未来需要与 Fountain/FDX 双向同步，可以在 `metadata` 中存储 Fountain 原始文本块或 FDX 节点 ID，不破坏主结构。

### 3.8 ID 命名规范的设计考量

ID 采用 `{类型前缀}_{序号}` 格式（如 `char_001`、`sc_001`、`act_01`），而非 UUID 或自然语言：

1. **可读性**：`char_001` 比 `550e8400-e29b-41d4-a716-446655440000` 好读 100 倍，作者手动引用时不会写错
2. **有序性**：序号隐含出场顺序，方便快速定位
3. **稳定性**：不依赖名称——角色可能改名，但 ID 不变
4. **前缀区分**：一眼就能看出引用的是什么类型的实体

### 3.9 为什么 beats 是有序列表而非嵌套结构

一些编剧格式（如 FDX）会把台词和动作嵌套在"段落"或"节拍"里。我们选择**扁平有序列表**：

1. **简单性**：YAML 数组天然有序，不需要额外的 `order` 字段
2. **编辑方便**：作者要调整顺序，剪切粘贴一行即可；嵌套结构调整涉及缩进变更，容易出错
3. **够用**：电影/电视剧本本质就是"一段接一段"的线性结构，嵌套带来的分组能力在初稿阶段用不上

---

## 4. 示例

以下是一个包含 2 个场景的完整 YAML 示例，改编自虚构悬疑小说《雾城》第三章。

```yaml
meta:
  title: "雾城"
  source_title: "雾城"
  source_author: "李默白"
  adapter: "AI 编剧助手"
  created_at: "2025-06-05T14:30:00+08:00"
  updated_at: "2025-06-05T14:30:00+08:00"
  schema_version: "1.0.0"
  genres:
    - "悬疑"
    - "都市"
    - "黑色"
  language: "zh-CN"
  logline: "一个退休刑警在雾都老城重逢旧案证人，却发现证人早已不是当年那个人。"

characters:
  char_001:
    name: "陈守一"
    aliases:
      - "老陈"
      - "陈叔"
      - "守一"
    type: "protagonist"
    gender: "male"
    age_range: "60岁左右"
    description: "退休刑警，沉默寡言，左手有旧伤。习惯用沉默代替回答。"
    relationships:
      - with: "char_002"
        relation: "旧案证人"
        note: "十五年前'码头案'的关键证人，当年突然失踪"
      - with: "char_003"
        relation: "旧同事"
    first_appearance: "sc_001"
    metadata: {}

  char_002:
    name: "苏婉清"
    aliases:
      - "婉清"
      - "那个女人"
      - "苏老板"
    type: "supporting"
    gender: "female"
    age_range: "45岁左右"
    description: "码头附近杂货铺老板娘，十五年前是'码头案'证人。表面温和，眼底有挥之不去的警觉。"
    relationships:
      - with: "char_001"
        relation: "旧案调查人"
        note: "当年陈守一负责保护她，她却在庭审前消失"
    first_appearance: "sc_001"
    metadata: {}

  char_003:
    name: "赵德明"
    aliases:
      - "老赵"
      - "赵队"
    type: "supporting"
    gender: "male"
    age_range: "55岁"
    description: "陈守一的老搭档，现任市局顾问。对'码头案'讳莫如深。"
    relationships:
      - with: "char_001"
        relation: "老搭档"
    first_appearance: "sc_002"
    metadata: {}

props:
  prop_001:
    name: "铜钥匙"
    description: "一把老旧的铜钥匙，钥匙头刻着一个模糊的锚形图案。苏婉清杂货铺柜台抽屉里常年放着。"
    first_appearance: "sc_001"
    is_key_prop: true
    metadata: {}

  prop_002:
    name: "旧照片"
    description: "十五年前码头案现场的照片，被陈守一夹在退休证里。"
    first_appearance: "sc_002"
    is_key_prop: true
    metadata: {}

acts:
  - id: "act_01"
    title: "第三章：重逢"
    summary: >
      陈守一在苏婉清的杂货铺重逢这位消失十五年的证人，
      表面叙旧暗藏试探。赵德明电话打断，暗示陈守一不要继续追查。
    source_chapter: "第三章"
    emotional_arc: "平静→暗涌→压抑"
    scenes:
      # ========== 场景一 ==========
      - id: "sc_001"
        title: "杂货铺重逢"
        time_of_day: "dusk"
        setting: "INT"
        location: "苏婉清的杂货铺"
        environment: >
          黄昏的光线透过蒙尘的玻璃窗，铺子里弥漫着檀香和老木头的气味。
          货架上的商品摆放得一丝不苟，像是某种秩序的象征。
        present_characters:
          - "char_001"
          - "char_002"
        beats:
          - type: "narration"
            text: "黄昏。雾气从江面漫上来，把整条老街裹进灰白色的纱里。"
            narration_type: "voiceover"
            source_text: "黄昏时分，雾气从江面漫上来，把整条老街裹进灰白色的纱里。"

          - type: "action"
            text: >
              陈守一推开杂货铺的木门，门铃发出沙哑的响声。
              他站在门口，花了几秒钟让眼睛适应昏暗的光线。
            characters:
              - "char_001"
            action_type: "movement"
            source_text: "陈守一推开了那扇门，门铃沙哑地响了一声。他站在门口，没急着往里走。"

          - type: "action"
            text: >
              苏婉清从柜台后抬起头，手里的算盘停在半空。
              她的表情在一瞬间闪过惊惶，但很快被温和的微笑取代。
            characters:
              - "char_002"
            action_type: "expression"

          - type: "dialogue"
            character_id: "char_002"
            text: "陈……老陈？真的是你？"
            emotion: "惊讶中带着一丝慌张"
            parenthetical: "（放下算盘，绕出柜台）"

          - type: "dialogue"
            character_id: "char_001"
            text: "是我。好久不见，婉清。"
            emotion: "克制"

          - type: "action"
            text: >
              两人隔着三步的距离对视。
              陈守一的左手微微攥紧——那是他紧张时的老习惯。
              苏婉清注意到了，目光在他左手上停了一瞬。
            characters:
              - "char_001"
              - "char_002"
            action_type: "interaction"

          - type: "dialogue"
            character_id: "char_002"
            text: "坐吧，我给你泡壶茶。还是老样子，龙井？"
            emotion: "故作轻松"
            parenthetical: "（转身走向茶具架，背对陈守一）"

          - type: "dialogue"
            character_id: "char_001"
            text: "龙井。"
            emotion: "简短"
            parenthetical: "（在靠窗的老位置坐下）"

          - type: "action"
            text: >
              陈守一的目光扫过柜台——
              抽屉缝里露出半截铜钥匙的轮廓，钥匙头刻着模糊的锚形。
              他微微眯了一下眼，但没有动。
            characters:
              - "char_001"
            action_type: "expression"

          - type: "dialogue"
            character_id: "char_001"
            text: "十五年没回来过，这铺子倒是一点都没变。"
            emotion: "试探"

          - type: "dialogue"
            character_id: "char_002"
            text: "变什么呢。有些东西，变了也看不出来。"
            emotion: "意味深长"
            parenthetical: "（背对着他，倒茶的手停顿了一下）"

        transition: "CUT_TO"
        pacing: "slow"
        emotional_intensity: 4
        key_props:
          - "prop_001"
        foreshadowing:
          - hint: "柜台抽屉里的铜钥匙，锚形图案"
            type: "plant"
            linked_scene_id: null
        metadata: {}

      # ========== 场景二 ==========
      - id: "sc_002"
        title: "街口电话"
        time_of_day: "evening"
        setting: "EXT"
        location: "杂货铺外的街口"
        environment: >
          夜色降临，路灯昏黄。雾更浓了，能见度不到十米。
          远处江面上隐约有汽笛声。
        present_characters:
          - "char_001"
        beats:
          - type: "action"
            text: >
              陈守一走出杂货铺，在街口的路灯下站定。
              他从外套内袋掏出手机，翻到一个备注为"老赵"的号码，
              犹豫了两秒，拨了出去。
            characters:
              - "char_001"
            action_type: "movement"

          - type: "dialogue"
            character_id: "char_001"
            text: "老赵，是我。"
            emotion: "低沉"

          - type: "dialogue"
            character_id: "char_003"
            text: "守一？你在哪？"
            emotion: "警觉"
            is_voiceover: true
            parenthetical: "（电话那头）"

          - type: "dialogue"
            character_id: "char_001"
            text: "我找到她了。苏婉清，在老码头那条街。十五年，她一直在这儿。"
            emotion: "压抑的震动"

          - type: "action"
            text: >
              电话那头沉默了五秒。陈守一能听到赵德明在翻什么东西——
              纸张的声音，急促而凌乱。
            characters:
              - "char_003"
            action_type: "business"

          - type: "dialogue"
            character_id: "char_003"
            text: "守一，你听我说。别再查了。当年的事……不是你想的那样。"
            emotion: "急切而焦虑"
            is_voiceover: true
            parenthetical: "（电话那头，压低声音）"

          - type: "dialogue"
            character_id: "char_001"
            text: "什么叫'不是我想的那样'？"
            emotion: "冷"

          - type: "dialogue"
            character_id: "char_003"
            text: "我求你了，回来。明天我们见面谈。别一个人。"
            emotion: "近乎恳求"
            is_voiceover: true

          - type: "action"
            text: >
              电话挂断。陈守一握着手机站在雾中，
              路灯把他的影子拉得很长。
              他缓缓把手伸进外套内袋，摸出夹在退休证里的那张旧照片，
              看了一眼，又放了回去。
            characters:
              - "char_001"
            action_type: "movement"

          - type: "narration"
            text: "雾气吞没了街口，仿佛什么都没发生过。"
            narration_type: "voiceover"

        transition: "FADE_OUT"
        pacing: "tense"
        emotional_intensity: 7
        key_props:
          - "prop_002"
        foreshadowing:
          - hint: "赵德明说'当年的事不是你想的那样'"
            type: "plant"
            linked_scene_id: null
          - hint: "旧照片"
            type: "plant"
            linked_scene_id: null
        metadata: {}

    metadata: {}

metadata: {}
```

---

## 5. Schema 校验

### 5.1 校验方案：Pydantic V2 模型

使用 Pydantic V2 定义 Schema 模型，兼顾**类型校验**和**业务规则校验**。Pydantic 的优势：

1. **类型安全**：字段类型、枚举值、可选性在模型定义中一揽子搞定
2. **自定义校验器**：用 `@field_validator` / `@model_validator` 编写业务规则
3. **错误信息友好**：校验失败时给出字段路径和具体原因，方便定位
4. **YAML 反序列化**：`yaml.safe_load()` 得到 dict → `ScriptModel(**data)` 一步校验+转换

### 5.2 核心 Pydantic 模型定义

```python
from __future__ import annotations
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ===== 枚举 =====
class CharacterType(str, Enum):
    protagonist = "protagonist"
    supporting = "supporting"
    minor = "minor"
    extra = "extra"

class TimeOfDay(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    dusk = "dusk"
    evening = "evening"
    night = "night"
    dawn = "dawn"
    unspecified = "unspecified"

class Setting(str, Enum):
    INT = "INT"
    EXT = "EXT"
    INT_EXT = "INT/EXT"

class Pacing(str, Enum):
    slow = "slow"
    moderate = "moderate"
    fast = "fast"
    tense = "tense"
    climax = "climax"

class ActionType(str, Enum):
    movement = "movement"
    expression = "expression"
    interaction = "interaction"
    business = "business"
    stunt = "stunt"

class NarrationType(str, Enum):
    voiceover = "voiceover"
    title_card = "title_card"
    epigraph = "epigraph"

class ForeshadowingType(str, Enum):
    plant = "plant"
    payoff = "payoff"
    callback = "callback"


# ===== 子模型 =====
class ScriptMeta(BaseModel):
    title: str
    source_title: Optional[str] = None
    source_author: Optional[str] = None
    adapter: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    schema_version: str = "1.0.0"
    genres: list[str] = Field(..., min_length=1)
    language: str = "zh-CN"
    logline: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

class CharacterRelationship(BaseModel):
    with_: str = Field(alias="with")
    relation: str
    note: Optional[str] = None

class Character(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    type: CharacterType = CharacterType.supporting
    gender: Optional[Literal["male", "female", "other", "unknown"]] = None
    age_range: Optional[str] = None
    description: str
    relationships: list[CharacterRelationship] = Field(default_factory=list)
    first_appearance: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

class Foreshadowing(BaseModel):
    hint: str
    type: Optional[ForeshadowingType] = None
    linked_scene_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

class Prop(BaseModel):
    name: str
    description: Optional[str] = None
    first_appearance: Optional[str] = None
    is_key_prop: bool = False
    metadata: dict = Field(default_factory=dict)


# ===== Beat 联合类型 =====
class DialogueBeat(BaseModel):
    type: Literal["dialogue"]
    character_id: str
    text: str
    emotion: Optional[str] = None
    parenthetical: Optional[str] = None
    is_voiceover: bool = False
    source_text: Optional[str] = None
    source_location: Optional["SourceLocation"] = None  # 原文位置映射，用于滚动联动
    metadata: dict = Field(default_factory=dict)

class ActionBeat(BaseModel):
    type: Literal["action"]
    text: str
    characters: list[str] = Field(default_factory=list)
    action_type: Optional[ActionType] = None
    source_text: Optional[str] = None
    source_location: Optional["SourceLocation"] = None  # 原文位置映射，用于滚动联动
    metadata: dict = Field(default_factory=dict())

class NarrationBeat(BaseModel):
    type: Literal["narration"]
    text: str
    narration_type: NarrationType = NarrationType.voiceover
    source_text: Optional[str] = None
    source_location: Optional[SourceLocation] = None  # 原文位置映射，用于滚动联动
    metadata: dict = Field(default_factory=dict)

class TransitionBeat(BaseModel):
    type: Literal["transition"]
    transition: str
    note: Optional[str] = None

class SourceLocation(BaseModel):
    """原文位置映射（用于滚动联动）"""
    chapter_index: int       # 章节序号（从 0 开始）
    start_paragraph: int    # 起始段落索引
    end_paragraph: int      # 结束段落索引
    start_offset: int       # 段落内起始字符偏移
    end_offset: int         # 段落内结束字符偏移

Beat = DialogueBeat | ActionBeat | NarrationBeat | TransitionBeat


# ===== 场景 / 章节 =====
class Scene(BaseModel):
    id: str
    title: str
    time_of_day: TimeOfDay = TimeOfDay.unspecified
    setting: Setting = Setting.INT
    location: str
    environment: Optional[str] = None
    present_characters: list[str] = Field(default_factory=list)
    beats: list[Beat] = Field(default_factory=list)
    transition: Optional[str] = None
    pacing: Optional[Pacing] = None
    emotional_intensity: Optional[int] = Field(None, ge=1, le=10)
    key_props: list[str] = Field(default_factory=list)
    foreshadowing: list[Foreshadowing] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class Act(BaseModel):
    id: str
    title: str
    summary: str
    source_chapter: Optional[str] = None
    emotional_arc: Optional[str] = None
    scenes: list[Scene] = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)


# ===== 顶层模型 =====
class Script(BaseModel):
    meta: ScriptMeta
    characters: dict[str, Character]
    acts: list[Act]
    props: dict[str, Prop] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
```

### 5.3 业务规则校验

Pydantic 模型校验类型和基本约束，以下业务规则需要用自定义校验器实现：

| # | 规则 | 校验器类型 | 说明 |
|---|------|------------|------|
| 1 | **角色 ID 引用完整性** | model_validator | 场景中 `present_characters` 和 `beats[dialogue].character_id` 引用的 ID 必须在 `characters` 中存在 |
| 2 | **场景 ID 全局唯一** | model_validator | 所有场景的 `id` 不得重复 |
| 3 | **章节 ID 唯一** | model_validator | 所有 `act.id` 不得重复 |
| 4 | **道具 ID 引用完整性** | model_validator | 场景中 `key_props` 引用的 ID 必须在 `props` 中存在 |
| 5 | **伏笔关联场景存在** | field_validator | `foreshadowing.linked_scene_id`（非空时）必须指向一个真实存在的场景 |
| 6 | **角色 first_appearance 一致性** | model_validator | `character.first_appearance` 指向的场景，其 `present_characters` 必须包含该角色 ID |
| 7 | **emotional_intensity 范围** | Field 约束 | 1-10 整数，已在 Field 中用 `ge=1, le=10` 约束 |
| 8 | **genres 非空** | Field 约束 | 至少 1 个标签，已在 Field 中用 `min_length=1` 约束 |
| 9 | **别名不跨角色重叠** | model_validator | 同一别名不能出现在两个不同角色的 `aliases` 中 |
| 10 | **对话 Beat 必须有 character_id** | 类型约束 | 已通过 `DialogueBeat.character_id: str`（必填）保证 |

### 5.4 校验器示例代码

```python
from pydantic import model_validator


class Script(BaseModel):
    meta: ScriptMeta
    characters: dict[str, Character]
    acts: list[Act]
    props: dict[str, Prop] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cross_references(self) -> "Script":
        # 收集所有场景 ID 和场景数据
        all_scene_ids: set[str] = set()
        all_scenes: dict[str, Scene] = {}

        for act in self.acts:
            for scene in act.scenes:
                # 规则 2: 场景 ID 全局唯一
                if scene.id in all_scene_ids:
                    raise ValueError(f"场景 ID 重复: {scene.id}")
                all_scene_ids.add(scene.id)
                all_scenes[scene.id] = scene

        # 规则 1: 角色引用完整性
        for scene in all_scenes.values():
            for char_id in scene.present_characters:
                if char_id not in self.characters:
                    raise ValueError(
                        f"场景 '{scene.id}' 引用了不存在的角色 ID: {char_id}"
                    )
            for beat in scene.beats:
                if beat.type == "dialogue" and beat.character_id not in self.characters:
                    raise ValueError(
                        f"场景 '{scene.id}' 的对白引用了不存在的角色 ID: {beat.character_id}"
                    )

        # 规则 4: 道具引用完整性
        for scene in all_scenes.values():
            for prop_id in scene.key_props:
                if prop_id not in self.props:
                    raise ValueError(
                        f"场景 '{scene.id}' 引用了不存在的道具 ID: {prop_id}"
                    )

        # 规则 5: 伏笔关联场景存在
        for scene in all_scenes.values():
            for fs in scene.foreshadowing:
                if fs.linked_scene_id and fs.linked_scene_id not in all_scene_ids:
                    raise ValueError(
                        f"场景 '{scene.id}' 的伏笔引用了不存在的场景 ID: {fs.linked_scene_id}"
                    )

        # 规则 6: 角色 first_appearance 一致性
        for char_id, char in self.characters.items():
            if char.first_appearance:
                if char.first_appearance not in all_scene_ids:
                    raise ValueError(
                        f"角色 '{char_id}' 的 first_appearance 引用了不存在的场景: {char.first_appearance}"
                    )
                target_scene = all_scenes[char.first_appearance]
                if char_id not in target_scene.present_characters:
                    raise ValueError(
                        f"角色 '{char_id}' 的 first_appearance 场景 '{char.first_appearance}' 的 present_characters 中不包含该角色"
                    )

        # 规则 9: 别名不跨角色重叠
        alias_map: dict[str, str] = {}  # alias -> char_id
        for char_id, char in self.characters.items():
            for alias in char.aliases:
                if alias in alias_map and alias_map[alias] != char_id:
                    raise ValueError(
                        f"别名 '{alias}' 同时出现在角色 '{alias_map[alias]}' 和 '{char_id}' 中"
                    )
                alias_map[alias] = char_id

        return self
```

### 5.5 使用流程

```python
import yaml
from pydantic import ValidationError

def load_and_validate(yaml_path: str) -> Script:
    """加载 YAML 文件并校验，返回 Script 模型或抛出 ValidationError"""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    try:
        script = Script(**data)
        return script
    except ValidationError as e:
        # 打印友好的错误信息
        for error in e.errors():
            loc = " → ".join(str(x) for x in error["loc"])
            print(f"[校验失败] {loc}: {error['msg']}")
        raise
```

### 5.6 JSON Schema 导出（可选）

如需与不支持 Pydantic 的工具集成，可从 Pydantic 模型导出 JSON Schema：

```python
json_schema = Script.model_json_schema()
```

导出的 JSON Schema 可用于：
- 在线 YAML 编辑器的实时校验
- CI/CD 流水线中的 `ajv` 等校验工具
- IDE 的 YAML Schema 提示（如 VSCode 的 `yaml.schemas` 配置）

---

## 附录：设计决策速查表

| 决策点 | 选择 | 替代方案 | 选择理由 |
|--------|------|----------|----------|
| 数据格式 | YAML | JSON / TOML | 可读性最佳，注释原生支持，缩进表示层级 |
| 角色存储 | 顶层 dict（key=ID） | 嵌套在场景中 | 去重、一致性、快速查阅 |
| Beat 类型 | Tagged Union | 平铺所有字段 | 短、清晰、不易填错 |
| 场景转场 | 双层级（Scene+Beat） | 仅 Scene 级 | 支持场景内嵌套转场（闪回等） |
| ID 格式 | 前缀+序号 | UUID / 自然语言 | 可读+有序+稳定 |
| Beat 列表 | 扁平有序数组 | 嵌套分组结构 | 简单、编辑方便、初稿够用 |
| 扩展机制 | metadata dict | 无 / 严格 Schema | 开放扩展不破坏主结构 |
| 校验方案 | Pydantic V2 | JSON Schema only | 类型+业务规则一揽子校验，错误信息友好 |

---

## 6. 扩展性设计关联

> 本 Schema 设计遵循《扩展性设计详细规范.md》中的原则。

### 6.1 Schema 扩展性设计

**设计原则**：
1. **新增字段用 `Optional` + 默认值** —— 保证向后兼容性
2. **使用 `metadata: dict` 字段** —— 扩展信息不破坏主结构
3. **Tagged Union 设计** —— 新增 Beat 类型只需添加新模型类

#### 6.1.1 新增 Beat 类型示例

**场景**：V2 需要新增"音乐提示" Beat 类型。

**无需修改源码**，只需：

1. 在 `Beat` Union 中添加新模型类：

```python
# src/schema.py

class MusicBeat(BaseModel):
    """音乐提示 Beat（V2 新增）"""
    type: Literal["music"] = "music"
    content: str  # 音乐描述
    volume: int | None = None  # 音量（1-10）
    timing: str | None = None  # 播放时机（如 "scene_start"）
    metadata: dict = Field(default_factory=dict)

# 更新 Beat Union
Beat = Annotated[
    Union[
        Annotated[DialogueBeat, Tag("dialogue")],
        Annotated[ActionBeat, Tag("action")],
        Annotated[NarrationBeat, Tag("narration")],
        Annotated[TransitionBeat, Tag("transition")],
        Annotated[MusicBeat, Tag("music")],  # V2 新增
    ],
    Discriminator("type"),
]
```

2. 在 YAML Schema 中自动支持：

```yaml
# 新增的 music Beat 类型自动可用
beats:
  - type: music
    content: "悲伤的小提琴曲"
    volume: 5
    timing: "scene_start"
```

#### 6.1.2 向后兼容性保证

| 操作 | 是否允许 | 说明 |
|------|---------|------|
| **新增字段** | ✅ 允许 | 必须使用 `Optional` + 默认值 |
| **删除字段** | ❌ 禁止 | 走新版本（如 V2 Schema） |
| **修改字段语义** | ❌ 禁止 | 走新版本 |
| **新增 Beat 类型** | ✅ 允许 | 在 Union 中添加新模型类 |
| **修改已有 Beat 类型** | ❌ 禁止 | 走新版本 |

### 6.2 Pydantic V2 模型扩展性

**优势**：
1. **模型继承** —— 可通过继承扩展模型
2. **Validator 继承** —— 子类可覆盖或扩展校验器
3. **JSON Schema 导出** —— 自动生成最新的 JSON Schema

#### 6.2.1 模型继承示例

```python
# V1 基础模型
class BeatBase(BaseModel):
    type: str
    metadata: dict = Field(default_factory=dict)

# V2 扩展模型
class BeatV2(BeatBase):
    """V2 新增的公共字段"""
    source_location: dict | None = None  # 新增：原文位置映射
    confidence: float | None = None  # 新增：AI 置信度
```

### 6.3 与《扩展性设计详细规范》的关联

| yaml-schema.md 章节 | 对应的扩展性设计规范 | 说明 |
|------------------------|--------------------------------|------|
| 3.2 角色表：为什么需要 aliases | 3.1.4 数据模型版本兼容性设计 | 别名映射是扩展性设计的关键 |
| 3.4 Beat 设计：为什么用 Tagged Union | 8.1 CodeMirror 6 Extension 注册机制 | Tagged Union 与 Extension 机制类似 |
| 5.3 业务规则校验 | 2.1.5 Hook 异常处理策略 | 校验失败可通过 Hook 处理 |
| 5.4 校验器示例代码 | 2.2.5 新增 Step 示例 | 校验器可作为 Step 的预处理 |

---

> **详细规范**：请参考《扩展性设计详细规范.md》文档。
