---
AIGC:
    Label: "1"
    ContentProducer: 001191110102MACQD9K64018705
    ProduceID: 520543646253513_0/project_7647746939261518126-files/novel-to-script/docs/PRD.md
    ReservedCode1: ""
    ContentPropagator: 001191110102MACQD9K64028705
    PropagateID: 520543646253513#1780649045034
    ReservedCode2: ""
---
# AI 小说转剧本工具 (Novel2Script) — 产品需求文档 (PRD)

> 版本：v4.0 | 日期：2026-06-05 | 状态：开发中
> 产品代号：novel2script
> 文档结构：Part 1（V1 版本需求）+ Part 2（迭代路线图）

---

## 目录

- [Part 1: V1 版本需求](#part-1-v1-版本需求)
  - [1. 产品概述](#1-产品概述)
  - [2. 双启动模式](#2-双启动模式)
  - [3. 内置编辑器](#3-内置编辑器)
  - [4. 项目管理](#4-项目管理)
  - [5. Skill 系统](#5-skill-系统)
  - [6. 用户自选 AI](#6-用户自选-ai)
  - [7. 长文本智能分段](#7-长文本智能分段)
  - [8. SSE 实时进度推送](#8-sse-实时进度推送)
  - [9. 打包与部署](#9-打包与部署)
  - [10. 用户流程](#10-用户流程)
  - [11. 非功能需求](#11-非功能需求)
  - [12. 数据模型](#12-数据模型)
  - [13. 里程碑与交付计划](#13-里程碑与交付计划)
- [Part 2: 迭代路线图](#part-2-迭代路线图)
  - [14. V2 版本规划](#14-v2-版本规划)
  - [15. V3 版本规划](#15-v3-版本规划)
  - [16. 扩展性设计原则](#16-扩展性设计原则)
- [附录](#附录)

---

# Part 1: V1 版本需求

> 3 天交付，功能完整可用。所有设计为后续扩展预留接口和扩展点。

---

## 1. 产品概述

### 1.1 产品定位

**Novel2Script** 是一款本地安装的桌面级应用，将 **3 章以上**的小说文本自动转换为结构化 YAML 剧本。产品提供 **桌面模式** 和 **CLI 模式** 两种启动方式，共享同一套 FastAPI 后端和核心 Pipeline，覆盖从文本输入到剧本输出、内置编辑、项目管理、Skill 扩展的完整流程。

**V1 核心能力**：
1. **双启动模式**：桌面模式（PyWebView）+ CLI 模式，共享后端
2. **内置编辑器**：左右分栏、滚动联动、Beat 内联编辑、CodeMirror 6 驱动
3. **项目管理**：项目列表首页、自动归档、可持续编辑
4. **Skill 系统**：5 个内置 Skill + 用户自定义 Skill
5. **用户自选 AI**：6 个预设 + 自定义，API Key 本地存储
6. **长文本智能分段**：6000 字阈值 + 200 字上下文窗口
7. **SSE 实时进度推送**
8. **打包分发**：PyInstaller 单文件 exe

### 1.2 目标用户

| 用户类型 | 特征 | 主要使用方式 |
|---------|------|-------------|
| 剧本改编者 | 将小说快速转为剧本初稿，逐场景审阅修改 | 桌面模式 + 编辑器 |
| 独立编剧 | 小说原作者亲自改编剧本，需要可视化编辑和导出 | 桌面模式 + 编辑器 |
| 个人创作者 | 批量处理多部小说，集成到自动化流水线 | CLI 模式 |
| 技术研究者 | 研究小说→剧本的 AI 转换质量，需要调参对比 | 两者皆用 |
| Skill 开发者 | 开发自定义 Skill 扩展工具能力 | CLI + 文件编辑 |

### 1.3 核心价值

1. **效率跃升**：10 万字小说 5 分钟内生成结构化剧本初稿，人工改编需 2-3 天
2. **质量可控**：角色别名合并、场景智能分割、情绪标注等全流程 AI 辅助，人工可审可改
3. **可视化编辑**：内置编辑器支持左右分栏对照、Beat 内联编辑、实时校验，转换即编辑
4. **项目持久化**：每次转换自动创建项目，随时回来继续编辑，不用从头来
5. **格式标准**：输出 YAML 严格符合预定义 Schema，内置 Fountain 导出 Skill
6. **用户自主**：不绑定任何 AI 服务商，用户自选模型、自配 API、本地运行，数据不出本机
7. **可扩展**：Skill 系统允许按需扩展能力，编辑器组件化设计为后续功能留足空间
8. **开箱即用**：PyInstaller 打包为单文件 exe/二进制，双击即运行

### 1.4 与竞品的差异

| 维度 | Novel2Script | 在线剧本生成平台 | 通用 AI 写作工具 |
|------|-------------|----------------|----------------|
| 运行方式 | 本地安装，数据不出本机 | 云端 SaaS | 云端 SaaS |
| 启动方式 | 桌面窗口 + CLI 双模式 | 浏览器 | 浏览器 / App |
| AI 模型 | 用户自选，6 预设 + 自定义 | 平台指定 | 平台指定 |
| 内置编辑器 | ✅ 左右分栏 + 滚动联动 + 内联编辑 | ❌ | ❌ |
| 项目管理 | ✅ 项目列表 + 自动归档 + 持续编辑 | ❌ | ❌ |
| 输出格式 | 结构化 YAML（含角色表、场景图、情绪标注） | 纯文本/简单格式 | 纯文本 |
| 插件/扩展 | Skill 系统（内置 + 用户自定义） | ❌ | ❌ |
| 扩展性设计 | 插件式架构 + 数据层隔离 + API 版本化 | 封闭 | 封闭 |

---

## 2. 双启动模式

**描述**：应用提供两种启动方式，共享同一个 FastAPI 后端和核心 Pipeline，区别仅在 UI 壳。桌面模式面向普通用户，CLI 模式面向自动化和高级用户。

### 2.1 桌面模式

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| PyWebView 独立窗口 | 双击 exe 或运行 `novel2script gui`，启动 PyWebView 窗口 | P0 | 窗口无地址栏、有标题栏（显示 "Novel2Script"）和任务栏图标；关闭窗口即退出程序 | 后续可切换为 Electron/Tauri 壳，核心逻辑不变 |
| PyWebView 回退机制 | PyWebView 未安装时自动回退到浏览器模式 | P0 | 无 pywebview 依赖时，自动打开默认浏览器访问 `http://localhost:8765`，控制台打印回退提示 | 回退检测逻辑可扩展为检测多种壳（Electron 等） |
| 窗口尺寸 | 默认 1280×800，可调整大小，最小 960×600 | P1 | 启动后窗口居中显示，可拖拽缩放 | 尺寸偏好可持久化到用户配置 |
| 双击 exe 默认 gui | 打包后双击运行默认启动桌面模式 | P0 | 双击 exe 启动桌面模式，无需命令行参数 | 后续可加启动参数解析支持其他子命令 |
| 单实例运行 | 同时只允许运行一个桌面模式实例 | P1 | 二次启动时检测到已有实例，弹出提示而非重复打开 | 单实例检测机制可复用为"服务健康检测" |

### 2.2 CLI 模式

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| convert 命令 | `novel2script convert <input> <output_dir>` 执行完整转换 | P0 | 输入 .txt/.md 输出 .yaml 到指定目录，控制台打印进度 | 后续加 `--format` 支持多种输出格式 |
| validate 命令 | `novel2script validate <yaml_path>` 校验 YAML 文件 | P0 | 输出校验结果（通过/失败+错误详情），退出码 0=通过 1=失败 | 校验规则可通过 Skill 追加自定义规则 |
| skill 命令 | `novel2script skill run <name> --input <yaml_text>` 运行指定 Skill | P0 | 执行 Skill 并在终端输出结果 | 后续加 `skill install` / `skill publish` 子命令 |
| 配置参数 | `--model` `--api-key` `--api-endpoint` `--no-emotion` 等参数 | P0 | 参数正确传递到 Pipeline，缺省时读取本地配置文件 | 参数系统可扩展为从环境变量读取 |
| 输出格式 | `--format yaml\|json\|fountain` | P1 | 三种格式均可正确输出 | 新格式通过 exporter Skill 扩展，`--format` 自动发现已注册格式 |
| 进度输出 | `--progress` 参数控制是否输出进度到 stderr | P1 | 默认开启，`--no-progress` 关闭 | 后续可加 `--progress-format json` 供程序化消费 |

### 2.3 启动模式共享架构

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 共享 FastAPI 后端 | 两种模式启动同一个 FastAPI 服务实例 | P0 | 桌面模式与 CLI 模式使用相同的 API 端点和 Pipeline | — |
| 共享核心 Pipeline | 转换流程、配置管理、Skill 引擎完全共享 | P0 | 同一份代码、同一套配置，结果一致 | Pipeline 可通过 Hook 机制插入自定义环节 |
| UI 壳隔离 | 桌面模式通过 PyWebView 加载 Web UI，CLI 直接终端输出 | P0 | UI 层与核心逻辑解耦，互不影响 | 后续可加第三种壳（系统托盘 / 命令面板） |

---

## 3. 内置编辑器

**描述**：V1 的核心新增功能。提供左右分栏编辑界面，左边展示小说原文（只读/可编辑切换），右边展示 YAML 剧本（可编辑），支持滚动联动、Beat 内联编辑、小说预处理、自动保存和多格式导出。

### 3.1 编辑器布局与交互

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 左右分栏 | 左边小说原文面板，右边 YAML 剧本面板，可拖拽调整比例 | P0 | 分栏比例可调，默认 4:6，最小宽度各 300px | 后续可加"上下分栏"和"单面板"布局模式 |
| 小说原文面板 | 展示小说原文，默认只读，可切换为可编辑 | P0 | 只读时文本不可修改，切换编辑后可自由修改 | 后续可加"批注模式"——在原文上标注而不改文本 |
| YAML 剧本面板 | 展示转换后的 YAML 剧本，可编辑 | P0 | 支持 YAML 语法高亮，编辑后自动校验 | 后续可加"可视化剧本模式"——卡片/时间线视图替代纯文本 |
| 滚动联动 | 点击剧本某个 Beat，左边自动定位到对应的小说原文位置 | P0 | 点击 Beat 后左面板在 300ms 内滚动到 source_text 对应位置，高亮显示 | 后续可加"双向联动"——点原文跳剧本 |
| 分栏折叠 | 可折叠左/右面板为全屏编辑 | P1 | 点击折叠按钮后另一面板占满宽度，再次点击恢复 | 后续可加"专注模式"——隐藏所有非编辑 UI |

### 3.2 Beat 内联编辑

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 对白直接编辑 | 点击对白文本即进入编辑状态，修改后失焦自动保存 | P0 | 单击 → 出现光标 → 编辑 → 失焦 → 自动保存到项目 | 后续可加"AI 辅助改写"右键菜单（V3） |
| 情绪标签修改 | 点击情绪标签弹出下拉选择器，选择新标签 | P0 | 下拉列表展示预定义情绪标签，选择后 Beat 的 emotion 字段更新 | 后续可加自定义情绪标签 |
| 角色名修改 | 点击角色名弹出角色选择器，可切换为其他已有角色 | P0 | 选择后 character_id 更新，自动触发引用校验 | 后续可加"角色属性面板"——弹窗编辑角色详细信息 |
| Beat 类型切换 | 点击 Beat 类型标识，可切换 dialogue/action/narration/transition | P1 | 切换后 Beat 结构自动调整到对应 Tagged Union 格式 | 后续可加"Beat 拆分/合并"——一个 Beat 拆为多个或反向 |
| 新增/删除 Beat | 在 Beat 列表中插入新 Beat 或删除现有 Beat | P1 | 新 Beat 自动分配 ID，删除 Beat 后 scene 的 beats 列表更新 | 后续可加"Beat 排序"——拖拽调整 Beat 顺序 |

### 3.3 小说预处理

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 删章节 | 在原文面板中选中章节，点击删除 | P1 | 删除后转换时跳过该章节，原文标记删除线 | 后续可通过 pre_processor Skill 实现更复杂的过滤规则 |
| 合并段落 | 选中多个段落，右键合并为一个 | P2 | 合并后段落以换行符连接，重新分段不影响其他章节 | 后续可加"智能合并"——AI 判断哪些段落应合并 |
| 加标记 | 在原文中添加 `<!-- keep -->` / `<!-- skip -->` / `<!-- note: xxx -->` 标记 | P2 | 转换时根据标记决定是否处理该段，note 作为备注 | 后续标记类型可扩展为 Skill 注册的自定义标记 |
| 编辑原文 | 切换左面板为编辑模式后，可自由修改原文 | P0 | 修改后可重新转换，或手动保存 | 后续可加"原文版本管理"——记录每次修改 |

### 3.4 自动保存

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 编辑自动保存 | 编辑内容变更后自动保存到项目目录 | P0 | 编辑后 2 秒内自动保存，无需手动触发 | 后续可加"版本快照"——每次自动保存存一个快照（V2） |
| 保存路径 | `~/.novel2script/projects/<project_id>/` | P0 | 项目目录自动创建，文件读写正常 | 后续 ProjectStore 可替换为数据库，路径逻辑不变 |
| 保存内容 | 小说原文 + YAML 剧本 + 编辑配置（当前展开的 Beat、滚动位置等） | P1 | 重新打开项目时恢复到上次编辑状态 | 后续可加编辑偏好持久化 |
| 手动保存 | Ctrl+S 手动保存，状态栏显示"已保存" | P0 | 手动保存后状态栏显示保存确认 | — |

### 3.5 导出

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 导出 YAML | 保存为 .yaml 文件 | P0 | 导出的 YAML 可被 `novel2script validate` 校验通过 | 后续可加 YAML 导出选项（含/不含 source_text、含/不含 metadata） |
| 导出 Fountain | 保存为 .fountain 文件（通过内置 Skill） | P0 | 导出的 .fountain 可被 Final Draft / Fountain 应用正确打开 | 新导出格式通过 exporter Skill 扩展 |
| 导出纯文本 | 保存为 .txt 文件（格式化的剧本文本） | P1 | 导出为人类可读的剧本格式文本 | 后续可加 PDF/Word/FDX 格式（V3） |

### 3.6 编辑器技术选型

| 决策 | 选型 | 理由 |
|------|------|------|
| 前端编辑器组件 | **CodeMirror 6**（CDN 引入） | 模块化架构、优秀性能、扩展生态丰富，后续加语法高亮/自动补全/批注/lint 都很容易 |
| ❌ 禁止使用 | contenteditable / textarea | 后续加功能（高亮、折叠、补全、lint）极其痛苦，不可扩展 |
| YAML 编辑模式 | CodeMirror 6 + YAML 语言包 + Schema 校验 lint | 语法高亮 + 实时 Schema 校验提示（错误标红、警告标黄） |
| 小说编辑模式 | CodeMirror 6 + 自定义章节折叠插件 | 章节标题可折叠/展开，段落正常显示 |
| 联动引擎 | Beat 的 `source_location` 字段映射到原文行号 | 点击 Beat → 读取 source_location → 驱动左面板 EditorView.scrollTo() |
| 主题 | CodeMirror 6 主题系统 | 后续可加暗色主题、高对比度主题 |

> **扩展性设计说明**：CodeMirror 6 的 Extension 系统使得后续每个新功能都是一个独立的 Extension：
> - 语法高亮 → `StreamLanguage` / `LElement`
> - 自动补全 → `autocompletion` Extension
> - 批注 → `gutter` + `decoration` Extension
> - Schema 校验 → `linter` Extension
> - 章节折叠 → `foldGutter` Extension
> - 新功能只需注册新 Extension，不修改已有代码。

---

## 4. 项目管理

**描述**：V1 的核心新增功能。首页改为项目列表，每次转换自动创建项目，包含小说原文 + YAML 剧本 + 配置快照。用户可随时点进项目继续编辑。

### 4.1 项目列表首页

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 首页改为项目列表 | 打开应用后首页展示所有历史转换项目 | P0 | 首页展示项目卡片列表，非空白页 | 后续可加"最近编辑""收藏""标签筛选"等过滤 |
| 项目卡片信息 | 展示项目标题、创建时间、最近编辑时间、状态 | P0 | 卡片显示标题 + 时间 + 状态标签（草稿/已完成/编辑中） | 后续可加缩略图/预览、标签 |
| 项目搜索 | 按标题关键词搜索项目 | P1 | 搜索结果实时过滤，无匹配时显示空状态 | 后续可加全文搜索（搜索项目内对白/角色名） |
| 项目删除 | 删除项目（移入回收站，可恢复） | P1 | 删除后从列表消失，回收站可恢复 | 后续可加"永久删除"和"项目归档" |
| 项目排序 | 按创建时间/最近编辑/标题排序 | P2 | 排序切换即时生效 | 后续可加自定义排序 |

### 4.2 项目创建与存储

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 自动创建项目 | 每次转换自动创建项目 | P0 | 转换完成后项目自动出现在列表中 | 后续可加"项目模板"——预设 Skill 配置和导出偏好 |
| 项目 ID | UUID 格式，自动生成 | P0 | ID 全局唯一，不可预测 | — |
| 项目存储路径 | `~/.novel2script/projects/<project_id>/` | P0 | 目录不存在时自动创建 | ProjectStore 抽象层可替换底层存储（V2 换数据库） |
| 项目内容 | 小说原文(novel.txt) + YAML 剧本(script.yaml) + 配置快照(config_snapshot.json) + 编辑元数据(edit_meta.json) | P0 | 四个文件均存在且内容正确 | 后续可加版本快照目录/、批注文件/ |
| 项目标题 | 默认取小说第一行或文件名，用户可修改 | P0 | 标题显示在列表和编辑页头部 | 后续可加"项目描述"和"项目封面" |
| 手动创建项目 | 用户可先创建空项目，后续上传小说 | P2 | 空项目出现在列表，状态为"空" | 后续可加"从模板创建项目" |

### 4.3 项目数据模型

> **扩展性关键**：项目数据模型是后续版本快照、批注的基础，V1 必须设计好。

```python
class Project(BaseModel):
    """项目数据模型 — V1 基础版，为 V2/V3 扩展预留字段"""
    id: str                          # UUID
    title: str                       # 项目标题
    status: Literal["empty", "converting", "editing", "completed"]
    created_at: datetime             # 创建时间
    updated_at: datetime             # 最近编辑时间
    novel_file: str                  # 原文文件相对路径（相对项目目录）
    script_file: str                 # 剧本文件相对路径
    config_snapshot: dict            # 转换时使用的配置快照
    edit_meta: EditMeta              # 编辑元数据
    # --- V2 扩展字段（预留，V1 不实现但数据结构支持） ---
    # snapshots: list[SnapshotMeta]   # 版本快照列表
    # annotations: list[Annotation]   # 批注列表
    # tags: list[str]                 # 项目标签

class EditMeta(BaseModel):
    """编辑元数据"""
    last_scroll_novel: int           # 小说面板上次滚动位置（行号）
    last_scroll_script: int          # 剧本面板上次滚动位置（行号）
    expanded_beats: list[str]        # 当前展开的 Beat ID 列表
    active_scene: str | None         # 当前聚焦的场景 ID
    # --- V2 扩展 ---
    # last_diff_view: bool           # 是否在 diff 视图
    # annotation_filter: list[str]   # 批注过滤条件
```

**项目目录结构**：

```
~/.novel2script/projects/<project_id>/
├── novel.txt                  # 小说原文
├── script.yaml                # YAML 剧本
├── config_snapshot.json       # 转换时的配置快照
├── edit_meta.json             # 编辑元数据（滚动位置、展开状态等）
├── project.json               # 项目元信息（Project 模型序列化）
├── snapshots/                 # [V2] 版本快照目录
│   ├── v1_20260605_143022.yaml
│   └── v2_20260605_150830.yaml
├── annotations/               # [V2] 批注目录
│   └── annotations.json
```

### 4.4 项目操作

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 进入项目 | 点击项目卡片进入编辑器页面 | P0 | 编辑器加载项目数据，恢复上次编辑状态 | 后续可加"项目详情页"——展示统计、历史等 |
| 重新转换 | 在项目内点击"重新转换"，用当前原文重新生成剧本 | P1 | 重新转换后剧本更新，原文不变 | 后续可加"增量转换"——只转换指定章节（V2） |
| 导出项目 | 从项目编辑器内触发导出 | P0 | 导出为 .yaml / .fountain / .txt | 后续可加"批量导出"——从项目列表页选中多个导出 |
| 项目配置查看 | 查看该项目转换时使用的配置快照 | P1 | 展示 config_snapshot.json 内容 | 后续可加"从快照恢复配置"——将快照配置设为当前配置 |

---

## 5. Skill 系统

**描述**：Skill 是 Novel2Script 的可扩展插件架构，内置 5 个实用 Skill，支持用户自定义 Skill。Skill 接口设计为后续"Skill 商店/在线安装"留好扩展口。

### 5.1 Skill 导航与管理

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 导航栏 Skills 入口 | Web UI 导航栏新增"Skills"入口，点击进入 Skill 管理页面 | P0 | 导航栏显示"Skills"文字/图标，点击跳转 Skill 管理页 | 后续可加"Skill 商店"入口，与本地 Skill 管理页合并 |
| Skill 列表展示 | 展示所有已安装 Skill（内置+用户自定义），显示名称、类型、描述、来源 | P0 | 列表区分内置/用户 Skill，显示 skill.json 中的元信息 | 后续可加"已安装/可更新/商店推荐" Tab 切换 |
| Skill 运行 | 选择 Skill → 点击"运行" → 选择输入数据 → 展示结果 | P0 | 运行内置 Skill 成功，结果在页面展示 | 后续可加"Skill 链式执行"——多个 Skill 串联 |
| Skill 创建 | 用户点击"创建 Skill"，生成模板（skill.json + main.py） | P1 | 创建后在 `~/.novel2script/skills/` 下生成目录和模板 | 后续可加"Skill 可视化编辑器"——在线编辑 main.py |
| Skill 安装 | 支持从本地路径安装 Skill | P1 | 指定本地路径，复制到 skills 目录并生效 | 后续加"在线安装"——从 GitHub/Gitee URL 安装（V2） |
| Skill 覆盖规则 | 用户 Skill 同名可覆盖内置 Skill | P1 | 同名用户 Skill 优先级高于内置 Skill，列表标注"已覆盖" | 覆盖规则可扩展为"版本优先级"覆盖策略 |
| CLI 运行 Skill | `novel2script skill run <name> --input <yaml_text>` | P0 | 终端执行 Skill 并输出结果 | 后续加 `skill install <url>` / `skill publish` 子命令 |
| CLI 列出 Skill | `novel2script skill list` 列出所有可用 Skill | P1 | 输出 Skill 名称、类型、来源 | 后续可加 `skill info <name>` 展示详细信息 |

### 5.2 内置 Skill

以下 5 个内置 Skill 随应用分发，不可卸载。

| Skill 名称 | 类型 | 描述 | 优先级 | 验收标准 | 扩展点 |
|------------|------|------|-------|---------|--------|
| Fountain 导出 | exporter | 将 YAML 剧本导出为好莱坞标准 Fountain 格式 | P0 | 导出的 .fountain 可被 Final Draft 正确打开 | 后续可加 PDF/Word/FDX 导出（均通过 exporter Skill） |
| 角色分析报告 | analyzer | 生成角色出场频次、对白占比、情绪分布、关系图谱数据 | P1 | 输出 JSON 报告，包含各角色统计数据和关系矩阵 | 后续可加"角色一致性检查"——检测 OOC（V3） |
| 对白润色 | post_processor | LLM 润色台词，可选风格（写实/戏剧化/幽默） | P1 | 选择风格后运行，输出润色后的 YAML 剧本 | 后续可加"AI 辅助改写"——选中 Beat 右键改写（V3） |
| 风格适配 | post_processor | 将剧本适配为电影/电视剧/话剧/动画风格 | P1 | 选择目标风格后运行，输出适配后的 YAML 剧本 | 后续可加"自定义风格模板" |
| 章节概要 | analyzer | 为每章生成摘要（出场角色、情绪走向、关键事件） | P1 | 输出每章摘要，含角色列表和情绪曲线描述 | 后续可加"故事线分析"——跨章节叙事线追踪 |

### 5.3 用户自定义 Skill

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| Skill 目录 | 用户 Skill 存储在 `~/.novel2script/skills/` | P0 | 目录不存在时自动创建 | 后续可加"Skill 搜索路径"配置，支持多目录 |
| Skill 结构 | 每个 Skill 目录包含 `skill.json`（元信息）+ `main.py`（入口） | P0 | 结构正确，skill.json 可解析，main.py 可调用 | 后续可加 `requirements.txt` + 自动安装依赖 |
| skill.json 格式 | 包含 name、type、version、description、author 字段 | P0 | 格式校验通过，缺失必填字段时提示错误 | 后续可加 `repository_url`/`license`/`dependencies` 字段用于商店 |
| main.py 入口 | 需实现 `run(data, config) -> dict` 函数 | P0 | 调用 run 函数返回 dict 结果，异常时捕获并提示 | 后续可加 `on_install()`/`on_uninstall()` 生命周期钩子 |
| Skill 模板生成 | 创建 Skill 时自动生成带注释的模板代码 | P1 | 模板包含 run 函数签名、参数说明、返回格式示例 | 后续可加多语言模板（TypeScript 等） |

**Skill 类型定义**：

| 类型 | 标识 | 说明 | 运行时机 | 扩展点 |
|------|------|------|---------|--------|
| 前置处理器 | pre_processor | 转换前对输入文本进行处理 | Pipeline 启动前 | 后续可加"条件执行"——仅在特定条件下触发 |
| 后置处理器 | post_processor | 转换后对 YAML 结果进行处理 | Pipeline 完成后 | 后续可加"链式处理"——多个 post_processor 按序执行 |
| 导出器 | exporter | 将 YAML 结果导出为特定格式 | 用户触发导出时 | 后续导出器可在"导出"菜单中自动注册 |
| 分析器 | analyzer | 对 YAML 结果进行分析，生成报告 | 用户触发分析时 | 后续可加"定时分析"——每次保存自动运行 |

**Skill 目录结构**：

```
~/.novel2script/skills/
├── my-custom-skill/
│   ├── skill.json           # 元信息
│   └── main.py              # 入口，需实现 run(data, config) -> dict
└── another-skill/
    ├── skill.json
    └── main.py
```

**skill.json 格式**：

```json
{
  "name": "my-custom-skill",
  "type": "post_processor",
  "version": "1.0.0",
  "description": "我的自定义 Skill 描述",
  "author": "用户名",
  "_comment_repository_url": "V2 预留：Skill 商店用",
  "_comment_license": "V2 预留：Skill 商店用",
  "_comment_dependencies": "V2 预留：依赖声明"
}
```

### 5.4 Skill 扩展点设计

> **为"Skill 商店/在线安装"预留的接口**：

V1 的 Skill 加载器（`skills/loader.py`）设计以下抽象层，后续加在线安装无需改核心代码：

```python
class SkillSource(Protocol):
    """Skill 来源抽象 — V1 实现 LocalSkillSource，V2 加 RemoteSkillSource"""
    def list_skills(self) -> list[SkillMeta]: ...
    def get_skill(self, name: str) -> SkillPackage: ...
    def install_skill(self, source: str) -> SkillMeta: ...  # V1: source=本地路径; V2: source=Git URL

class LocalSkillSource(SkillSource):
    """V1 实现：从本地文件系统加载 Skill"""
    ...

# V2 新增，无需改 SkillLoader 核心：
# class RemoteSkillSource(SkillSource):
#     """从 GitHub/Gitee 仓库安装 Skill"""
#     ...
```

---

## 6. 用户自选 AI

**描述**：用户自行配置 AI 模型接入方式，工具不内置任何 API Key。提供 6 个预设模型配置 + 完全自定义选项。

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| Web UI 设置页 | 提供表单填写 API Endpoint / API Key / 模型名称 | P0 | 表单含三个字段+保存按钮，保存后写入本地配置 | 后续可加"模型性能对比"——记录各模型转换耗时/质量 |
| 6 个预设模型 | 下拉预设：GPT-4o / DeepSeek-Chat / Moonshot-v1 / GLM-4 / Ollama（本地） / SiliconFlow | P0 | 选择预设后自动填充 Endpoint 和模型名，仅需填 API Key | 预设列表可从远程配置更新，无需发版 |
| 自定义配置 | 用户可完全自定义 API Key / Endpoint / Model | P0 | 手动填写三个字段，不依赖预设列表 | 后续可加"自定义请求头/参数"——支持非标准 API |
| 连接测试 | 设置页提供"测试连接"按钮，验证 API 可用性 | P1 | 点击后发送简短请求，返回成功/失败+模型名确认 | 后续可加"模型能力检测"——自动识别是否支持 JSON Mode |
| 配置持久化 | 保存到 `~/.novel2script/config.json` | P0 | 保存后重启应用仍可读取；API Key 明文存储（本地工具） | 后续可加密存储（如 keyring 库） |
| CLI 参数覆盖 | CLI 参数优先级高于配置文件 | P0 | `--api-key xxx` 覆盖 config.json 中的值，不影响文件内容 | 后续可加 `--config <path>` 指定配置文件路径 |
| Ollama 支持 | API Endpoint 填 `http://localhost:11434/v1`，API Key 填任意值 | P1 | Ollama 运行时可通过连接测试 | 后续可加"Ollama 模型列表自动发现" |

**配置文件格式**：

```json
{
  "api_endpoint": "https://api.openai.com/v1",
  "api_key": "sk-xxx",
  "model": "gpt-4o-mini",
  "pipeline": {
    "enable_emotion_tag": true,
    "chapter_concurrency": 3,
    "scene_concurrency": 5,
    "max_retries": 3
  }
}
```

---

## 7. 长文本智能分段

**描述**：自动处理超长章节，确保不超出 LLM 上下文窗口，同时保持跨段一致性。

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| 超长章节自动分段 | 单章超过 6000 字时按段落边界自动分段 | P0 | 6001 字的章节自动分为 2 段，分段点在段落边界 | 阈值可通过 config.json 调整，后续可按模型上下文长度自动计算 |
| 上下文窗口 | 每段保留前一段末尾 200 字作为上下文衔接 | P0 | 分段处理后 LLM 可看到前段尾 200 字，角色指代不丢失 | 上下文窗口大小可通过 config.json 调整 |
| 分段合并 | 各段处理结果自动合并为完整章节结果 | P0 | 合并后角色 ID 全局统一，无重复角色 | 后续可加"智能合并"——跨段场景合并 |
| 全章角色表预注入 | 分段处理前先完成全文章节的角色识别，角色表作为全局上下文 | P0 | 分段场景分割时 LLM 可引用已识别的角色表 | 后续可加"角色表增量更新"——新增角色自动合并 |
| Token 估算 | 处理前估算各章节 token 数，提前判断是否需要分段 | P1 | 估算误差 < 20%，超过模型上下文 80% 时触发分段 | 后续可加"实际 token 计数"——基于 tiktoken 精确计数 |

---

## 8. SSE 实时进度推送

**描述**：转换过程中通过 Server-Sent Events 实时推送各环节状态，桌面模式和 CLI 模式均可用。

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| SSE 端点 | `GET /api/v1/convert/{task_id}/stream` | P0 | SSE 连接建立后持续推送事件直到转换完成/失败 | 后续可加进度详情子事件 |
| 事件格式 | `{stage: string, status: string, progress: float, message: string}` | P0 | 各字段含义清晰，前端可解析渲染 | 后续可加 `detail` 字段传递子环节信息 |
| 阶段事件 | 文本预处理/角色识别/场景分割/对白解析/情绪标注/YAML 生成，每阶段开始/完成/失败各推送一次 | P0 | 6 个阶段 × 3 种状态 = 18 种事件，前端实时渲染 | 后续新阶段只需注册事件，前端自动识别 |
| 进度百分比 | 每个阶段推送当前进度百分比 | P0 | 进度从 0 到 100 平滑递增 | 后续可加"剩余时间估算" |
| 错误事件 | 转换失败推送 error 事件，含错误信息和建议 | P0 | 前端展示错误信息和重试按钮 | 后续可加"部分失败"——某章节失败其他继续 |

---

## 9. 打包与部署

**描述**：使用 PyInstaller 将应用打包为单文件可执行程序，降低用户安装门槛。

| 功能点 | 描述 | 优先级 | 验收标准 | 扩展点 |
|-------|------|-------|---------|--------|
| PyInstaller 打包 | 打包为单个 exe（Windows）或二进制（Linux/Mac） | P0 | 双击 exe 即可启动桌面模式，无需安装 Python | 后续可加自动更新机制 |
| 用户零配置运行 | 用户无需安装 Python 环境 | P0 | 全新 Windows 10 机器上双击 exe 可正常启动 | 后续可加"绿色安装"——无需管理员权限 |
| 体积控制 | 打包体积约 50-80MB（含 Python 运行时） | P1 | 压缩后单文件 ≤ 80MB | 后续可优化体积（UPX 压缩、排除不必要模块） |
| pyproject.toml 开发者安装 | 开发者可通过 `pip install -e .` 安装 | P0 | `pip install -e .` 后 `novel2script` 命令可用 | 后续可发布到 PyPI |
| 资源文件打包 | 前端静态文件、Prompt 模板、内置 Skill、CodeMirror 6 CDN 资源正确打包 | P0 | 打包后 UI 正常加载、内置 Skill 可运行、CodeMirror 可用 | 后续可加离线 CDN 检测——无网络时用本地缓存 |
| 双击 exe 默认 gui | 打包后双击运行默认启动桌面模式 | P0 | 双击 exe 启动桌面模式，无需命令行参数 | 后续可加命令行参数支持其他子命令 |

---

## 10. 用户流程

### 10.1 桌面模式完整流程

```
[首次使用]
  双击 novel2script.exe（或运行 novel2script gui）
  → PyWebView 打开独立应用窗口
  → 首页：项目列表（空）+ "新建项目"按钮
  → 点击"新建项目"或直接上传小说
  → 进入设置页配置 AI（6 预设 + 自定义）
  → 测试连接 → 连接成功 → 保存配置
  → 进入编辑器页面

[日常使用 — 新建项目]
  首页 → 点击"新建项目"
  → 上传小说文件 / 粘贴文本
  → （可选）小说预处理：删章节、合并段落、加标记
  → 点击"开始转换"
  → 编辑器页面展示转换进度（SSE 实时推送）
  → 转换完成 → 自动进入编辑状态

[日常使用 — 编辑项目]
  首页 → 项目列表 → 点击项目卡片
  → 进入编辑器，恢复上次编辑状态
  → 左右分栏：左小说原文 / 右 YAML 剧本
  → 点击 Beat → 左面板自动定位对应原文
  → 内联编辑对白/情绪/角色
  → 编辑自动保存
  → 导出为 .yaml / .fountain / .txt

[Skill 使用]
  编辑器内或导航栏 → Skills 入口
  → Skill 列表 → 选择 Skill → 运行 → 查看结果
  → 角色分析报告 / 对白润色 / 风格适配 / 章节概要

[退出]
  关闭 PyWebView 窗口 → 程序退出
```

### 10.2 CLI 模式典型使用场景

```bash
# 单文件转换
novel2script convert novel.txt output/

# 指定模型
novel2script convert novel.txt output/ \
  --model deepseek-chat \
  --api-endpoint https://api.deepseek.com/v1 \
  --api-key sk-xxx

# 校验 YAML
novel2script validate output/script.yaml

# 运行 Skill
novel2script skill run fountain-export --input output/script.yaml
novel2script skill run character-analysis --input output/script.yaml

# 列出 Skill
novel2script skill list
```

---

## 11. 非功能需求

### 11.1 性能

| 指标 | 目标 | 说明 |
|------|------|------|
| 10 万字小说转换耗时 | ≤ 3 分钟 | 含角色识别+场景分割+对白解析+情绪标注 |
| 桌面模式启动时间 | ≤ 3 秒 | 双击 exe 到窗口完全加载 |
| Web UI 首屏加载 | ≤ 2 秒 | 本地 FastAPI 服务，HTML/CSS/JS 直出 |
| 编辑器响应 | ≤ 100ms | CodeMirror 6 输入延迟 |
| 滚动联动响应 | ≤ 300ms | 点击 Beat 到原文定位完成 |
| 自动保存 | ≤ 2 秒 | 编辑后 2 秒内自动保存 |
| 内存占用 | ≤ 500MB | 处理 10 万字小说时的峰值内存 |
| 打包体积 | 50-80MB | 含 Python 运行时的单文件 exe |

### 11.2 安全

| 要求 | 说明 |
|------|------|
| API Key 本地存储 | 配置文件 `~/.novel2script/config.json` 存储 API Key，仅本机可读 |
| 无外发数据 | 除用户配置的 LLM API 调用外，不向任何外部服务发送数据 |
| 无内置密钥 | 工具不内置任何 API Key |
| 文件权限 | 配置文件创建时设置 600 权限 |
| Skill 沙箱 | 用户自定义 Skill 在子进程中运行，异常不影响主程序 |

### 11.3 兼容性

| 维度 | 要求 |
|------|------|
| 操作系统 | macOS 12+ / Ubuntu 20.04+ / Windows 10+ |
| Python 版本 | 3.10+（开发者用；打包版无需 Python） |
| 浏览器（回退模式） | Chrome 100+ / Firefox 100+ / Safari 15+ / Edge 100+ |
| LLM API | OpenAI API 兼容接口 |

### 11.4 可靠性

| 要求 | 说明 |
|------|------|
| 断点续传 | Pipeline 中间结果缓存到 `.cache/` 目录，失败后可从最近检查点恢复 |
| LLM 重试 | 单次 LLM 调用失败自动重试最多 3 次 |
| 优雅降级 | PyWebView 不可用时回退浏览器；情绪标注失败不阻塞 YAML 生成 |
| 编辑不丢失 | 自动保存机制 + 项目持久化，关闭窗口再打开不丢数据 |
| Skill 异常隔离 | 自定义 Skill 运行异常不崩溃主程序 |

---

## 12. 数据模型

### 12.1 输入数据

```python
class Chapter(BaseModel):
    index: int              # 章节序号，从 1 开始
    title: str              # 章节标题
    paragraphs: list[str]   # 段落列表
```

### 12.2 输出数据

最终输出遵循 `yaml-schema.md` 定义的 Script Schema，核心层级：

```
Script
├── meta              # 剧本元信息
├── characters        # 角色表（dict, key=character_id）
│   └── Character
│       ├── name / aliases / type / gender / age_range
│       ├── description
│       ├── relationships[]
│       └── first_appearance
├── acts[]            # 章节/幕列表
│   └── Act
│       ├── title / summary / source_chapter
│       └── scenes[]
│           └── Scene
│               ├── title / location / setting / time_of_day
│               ├── present_characters[]
│               ├── beats[]
│               │   └── Beat (dialogue | action | narration | transition)
│               ├── transition / pacing / emotional_intensity
│               ├── foreshadowing[]
│               └── key_props[]
└── props             # 道具表（dict, key=prop_id）
```

### 12.3 Skill 数据模型

```python
class SkillMeta(BaseModel):
    name: str
    type: Literal["pre_processor", "post_processor", "exporter", "analyzer"]
    version: str
    description: str
    author: str

class SkillResult(BaseModel):
    skill_name: str
    success: bool
    data: dict
    error: str | None = None
    duration_ms: int
```

### 12.4 项目数据模型

见 [4.3 项目数据模型](#43-项目数据模型)。

### 12.5 编辑器数据模型

```python
class SourceLocation(BaseModel):
    """Beat 与原文的映射关系"""
    chapter_index: int       # 章节序号
    start_paragraph: int     # 起始段落索引
    end_paragraph: int       # 结束段落索引
    start_offset: int        # 段落内起始字符偏移
    end_offset: int          # 段落内结束字符偏移

class EditState(BaseModel):
    """编辑器状态（用于自动保存和恢复）"""
    novel_scroll: int        # 小说面板滚动位置
    script_scroll: int       # 剧本面板滚动位置
    active_beat_id: str | None
    expanded_scenes: list[str]
    expanded_beats: list[str]
```

---

## 13. 里程碑与交付计划

### 总体原则

- **3 天开发周期**，P0 功能必须完成，P1 尽量完成，P2 作为后续迭代
- 每天有明确交付物和验收标准
- 增量开发：CLI 骨架 + 桌面模式 → 编辑器 + 项目管理 → Skill 系统 → 打包打磨

### Day 1：核心 Pipeline + CLI + 桌面模式 + 项目管理基础

| 任务 | 优先级 | 交付物 | 验收标准 |
|------|-------|-------|---------|
| 项目脚手架 | P0 | pyproject.toml + 目录结构 + typer CLI | `novel2script --help` 正常输出 |
| 配置管理 | P0 | config.py | 读写 config.json，CLI 参数可覆盖 |
| LLM 客户端 | P0 | llm_client.py | 支持 OpenAI 兼容接口，含重试和 JSON 解析 |
| 文本预处理 | P0 | preprocessor.py | 章节分割 + 清洗 + 段落切分 |
| 角色识别 | P0 | character_extractor.py | 提取角色 + 别名合并 |
| 场景分割 | P0 | scene_splitter.py | 按时空变化分割场景 |
| 对白解析 | P0 | dialogue_parser.py | 对白/旁白/动作/内心独白分类 |
| YAML 生成 + 校验 | P0 | yaml_generator.py + validator.py | 生成符合 Schema 的 YAML |
| Pipeline 编排 | P0 | pipeline.py | 顺序编排 + 断点缓存 + SSE 进度回调 |
| 长文本智能分段 | P0 | 集成到 pipeline.py | 超 6000 字章节自动分段 + 上下文窗口 |
| CLI convert / validate | P0 | main.py | CLI 可跑通完整转换 |
| PyWebView 桌面模式 | P0 | desktop.py | 独立窗口启动 + 回退浏览器 |
| FastAPI 服务 | P0 | server.py | SSE 进度推送可用 |
| **项目管理基础** | **P0** | **project_store.py** | **项目 CRUD + 项目目录创建 + 项目列表 API** |
| **项目列表首页** | **P0** | **Web UI** | **首页展示项目卡片列表** |

### Day 2：内置编辑器 + Skill 系统

| 任务 | 优先级 | 交付物 | 验收标准 |
|------|-------|-------|---------|
| **编辑器左右分栏** | **P0** | **Web UI + CodeMirror 6** | **左小说原文 + 右 YAML 剧本，分栏比例可调** |
| **YAML 语法高亮** | **P0** | **CodeMirror 6 YAML 扩展** | **关键字/值/注释有不同颜色，层级可折叠** |
| **小说章节折叠** | **P0** | **CodeMirror 6 自定义扩展** | **章节标题可折叠/展开** |
| **滚动联动** | **P0** | **联动引擎** | **点击 Beat → 左面板自动定位原文位置** |
| **Beat 内联编辑** | **P0** | **Web UI** | **对白/情绪/角色可内联编辑** |
| **小说预处理** | **P1** | **Web UI** | **原文可切换编辑模式，可删章节** |
| **自动保存** | **P0** | **项目持久化** | **编辑后 2 秒自动保存到项目目录** |
| **导出功能** | **P0** | **Web UI** | **导出 .yaml / .fountain / .txt** |
| Skill 引擎：加载器 | P0 | skills/loader.py | 发现、解析、校验内置和用户 Skill |
| Skill 引擎：运行器 | P0 | skills/runner.py | 执行 Skill，异常隔离 |
| 内置 Skill：Fountain 导出 | P0 | builtins/fountain-export/ | YAML → .fountain 转换正确 |
| 内置 Skill：角色分析/对白润色/风格适配/章节概要 | P1 | builtins/ | 各 Skill 运行成功 |
| Skill 管理页面 | P0 | Web UI | 列表展示 + 运行 + 结果展示 |
| CLI skill 命令 | P0 | main.py | `skill run` + `skill list` |
| 设置页 | P0 | Web UI | 6 预设 + 自定义 API 配置 + 连接测试 + 保存 |
| SSE 进度页 | P0 | Web UI | 转换过程实时展示进度 |

### Day 3：打磨 + 打包 + 测试

| 任务 | 优先级 | 交付物 | 验收标准 |
|------|-------|-------|---------|
| Schema 校验 lint | P0 | CodeMirror 6 linter 扩展 | 编辑 YAML 时实时校验提示 |
| 项目搜索/排序 | P1 | Web UI | 按标题搜索，按时间/名称排序 |
| 中间结果预览 | P1 | Web UI | 各环节完成后可预览角色表/场景列表 |
| 原文溯源查看 | P1 | Web UI | 点击 Beat 查看 source_text 原文 |
| .docx 文件解析 | P1 | preprocessor.py | 上传 .docx 文件正确提取文本 |
| Skill 创建模板 | P1 | Web UI + loader.py | 点击"创建 Skill"生成模板 |
| Skill 安装（本地） | P1 | Web UI + loader.py | 从本地路径安装 Skill |
| PyInstaller 打包 | P0 | novel2script.spec + 打包脚本 | 打包为单个 exe，双击可启动 |
| 打包资源完整性 | P0 | 验证 | 打包后 UI 正常加载、Skill 可运行、CodeMirror 可用 |
| 整体测试 + Bug 修复 | P0 | - | 核心流程无阻断性 Bug |

### 交付物总览

| 类别 | 交付物 |
|------|-------|
| 可执行程序 | `novel2script.exe`（Windows）/ `novel2script`（Linux/Mac） |
| CLI 命令 | `novel2script gui` / `convert` / `validate` / `skill run` / `skill list` |
| 桌面应用 | PyWebView 独立窗口（含回退到浏览器模式） |
| 内置编辑器 | 左右分栏 + 滚动联动 + Beat 内联编辑 + 自动保存 + 多格式导出 |
| 项目管理 | 项目列表首页 + 自动归档 + 持续编辑 |
| Skill 系统 | 5 个内置 Skill + 创建/安装/运行机制 |
| 文档 | PRD.md / architecture.md / yaml-schema.md / prompt-design.md |
| 测试 | 核心模块单元测试 + 端到端转换测试 |

---

# Part 2: 迭代路线图

> V1 之后的功能规划，按版本和优先级排列。

---

## 14. V2 版本规划

> 时间：V1 交付后 1-2 周
> 主题：**版本管理 + 增量能力 + 深度分析**

### 14.1 版本快照

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖 V1 扩展点 |
|-------|------|-------|---------|---------------|
| 自动快照 | 每次编辑/重新转换自动存快照 | P0 | 编辑 5 次后存在 5 个快照 | V1 项目数据模型预留 `snapshots` 字段 |
| 快照列表 | 在项目内查看所有历史快照 | P0 | 列表展示快照时间+操作描述 | V1 项目目录预留 `snapshots/` 目录 |
| Diff 对比 | 选择两个快照对比差异 | P1 | 差异高亮展示（新增/删除/修改） | 编辑器 CodeMirror diff 扩展 |
| 快照回滚 | 选择快照回滚到该版本 | P1 | 回滚后剧本和原文恢复到快照状态 | V1 ProjectStore 可扩展 |
| 快照清理 | 手动/自动清理旧快照 | P2 | 保留最近 N 个快照，自动删除更早的 | V1 项目目录结构支持 |

### 14.2 增量转换

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖 V1 扩展点 |
|-------|------|-------|---------|---------------|
| 指定章节重转 | 只重新转换指定章节，其余保持不变 | P0 | 选择章节后只重转选中章节，其他章节 YAML 不变 | V1 Pipeline 支持单章执行 |
| 增量角色合并 | 重转章节的新角色自动合并到全局角色表 | P1 | 新角色分配新 ID，已有角色映射正确 | V1 角色表全局预注入机制 |
| 增量场景合并 | 重转章节的场景替换旧场景 | P1 | 旧场景删除，新场景插入，ID 重新分配 | V1 Pipeline 编排支持部分执行 |

### 14.3 批注与标注

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖 V1 扩展点 |
|-------|------|-------|---------|---------------|
| Beat 级批注 | 在任意 Beat 上添加文字批注 | P0 | 批注与 Beat ID 绑定，可增删改 | V1 Beat 数据模型可扩展字段 |
| TODO 标记 | 在 Beat 上标记 TODO 状态 | P1 | TODO 标记可在项目列表中统计显示 | V1 项目数据模型预留字段 |
| 批注过滤 | 按类型/状态过滤批注 | P2 | 过滤后只显示匹配的批注 | V1 编辑器组件化架构 |

### 14.4 剧本统计仪表盘

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖 V1 扩展点 |
|-------|------|-------|---------|---------------|
| 对白/动作/叙述占比 | 饼图展示三类 Beat 占比 | P0 | 数据实时计算，图表交互 | V1 YAML 数据可直接统计 |
| 角色台词量柱状图 | 柱状图展示各角色台词字数 | P1 | 支持排序、点击跳转到角色对白 | V1 编辑器可注册新面板 |
| 情绪走向曲线 | 折线图展示情绪强度变化 | P1 | X 轴为场景序号，Y 轴为情绪强度 | V1 情绪标注数据可直接使用 |
| 仪表盘面板 | 编辑器右侧新增可折叠仪表盘 | P2 | 仪表盘不影响编辑器布局 | V1 前端组件化 + 事件总线 |

### 14.5 Skill 在线安装

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖 V1 扩展点 |
|-------|------|-------|---------|---------------|
| GitHub/Gitee 安装 | 从仓库 URL 安装 Skill | P0 | 输入 URL → 下载 → 安装到 skills 目录 | V1 SkillSource 抽象层 |
| 安装校验 | 校验 Skill 结构和依赖 | P1 | 安装前校验 skill.json 格式和 main.py 入口 | V1 Skill 加载器的校验逻辑 |
| Skill 元数据扩展 | skill.json 新增 repository_url/license/dependencies 字段 | P1 | 新字段可被解析和展示 | V1 skill.json 可扩展 |
| Skill 更新检测 | 检测已安装 Skill 是否有新版本 | P2 | 新版本可用时在列表中标注"可更新" | V1 Skill 列表展示可扩展 |

---

## 15. V3 版本规划

> 时间：V1 交付后 1-2 月
> 主题：**AI 深度 + 多格式 + 国际化**

### 15.1 AI 辅助改写

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖扩展点 |
|-------|------|-------|---------|-----------|
| 选中改写 | 选中一段对白，右键"AI改写" | P0 | 弹出风格选择面板，改写后替换原文 | V1 Beat 内联编辑可加右键菜单 |
| 风格选择 | 可选择改写风格（更口语/更文学/更戏剧化等） | P1 | 至少 4 种预设风格 | V1 LLM 客户端可直接使用 |
| 改写对比 | 改写结果与原文对比展示 | P1 | 高亮差异，可接受/拒绝 | V1 编辑器 CodeMirror diff 能力 |
| 批量改写 | 选中多个 Beat 批量 AI 改写 | P2 | 批量执行，逐个确认 | V1 Skill 运行器可复用 |

### 15.2 角色一致性检查

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖扩展点 |
|-------|------|-------|---------|-----------|
| 角色名矛盾检测 | 检测同一角色在不同场景的名字不一致 | P0 | 列出矛盾项，建议修正 | V1 角色别名合并机制可扩展 |
| 性格 OOC 检测 | 检测角色言行与性格描述不符 | P1 | 标记疑似 OOC 的 Beat | V1 角色数据模型 + LLM 客户端 |
| 一致性报告 | 生成角色一致性分析报告 | P1 | 报告含问题列表和建议 | V1 analyzer Skill 可扩展 |

### 15.3 导出更多格式

| 格式 | 描述 | 优先级 | 验收标准 | 依赖扩展点 |
|------|------|-------|---------|-----------|
| PDF | 导出为格式化 PDF | P0 | PDF 排版正确，支持中文 | V1 exporter Skill 可扩展 |
| Word (.docx) | 导出为 Word 文档 | P1 | .docx 可被 Word 正确打开 | V1 exporter Skill 可扩展 |
| FDX (Final Draft) | 导出为 Final Draft 格式 | P2 | .fdx 可被 Final Draft 正确打开 | V1 exporter Skill 可扩展 |

> **扩展点设计**：所有新格式均通过新增 exporter 类型 Skill 实现。V1 的导出菜单已通过 Skill 注册机制自动发现可用格式，新增 Skill 后导出菜单自动出现新选项，无需修改 UI 代码。

### 15.4 多语言支持

| 功能点 | 描述 | 优先级 | 验收标准 | 依赖扩展点 |
|-------|------|-------|---------|-----------|
| 英文小说输入 | 支持英文小说转剧本 | P1 | 英文小说转换结果结构正确 | V1 Prompt 模板可多语言切换 |
| 日文小说输入 | 支持日文小说转剧本 | P2 | 日文小说转换结果结构正确 | V1 文本预处理可扩展分词逻辑 |
| UI 国际化 | Web UI 支持中/英切换 | P2 | 切换语言后所有界面文案更新 | V1 前端组件化 + i18n 适配 |

---

## 16. 扩展性设计原则

> 以下原则是 V1 设计的底层约束，确保后续加功能时不大改老代码。
> 
> **详细规范见**：《扩展性设计详细规范.md》

### 原则 1：插件式架构

**核心思想**：所有新功能通过 Skill / Hook / Plugin 接入，不修改核心 Pipeline。

#### 1.1 Pipeline Hook 机制

- **Hook 接口定义**：`PipelineHook` Protocol（见《扩展性设计详细规范》2.1.1）
- **Hook 事件类型**：`before_convert` / `after_convert` / `before_step` / `after_step` / `on_error`
- **Hook 注册机制**：`pipeline.hook(event, callback)` 方法（见 2.1.3）
- **Hook 执行顺序**：按注册顺序执行，支持优先级（V2 扩展）（见 2.1.4）
- **Hook 异常处理**：默认忽略非致命异常，可配置为中止 Pipeline（见 2.1.5）
- **用户 Skill 注册 Hook**：通过 `skill.json` 声明，SkillManager 自动注册（见 2.1.6）

#### 1.2 Step 插件机制

- **Step 接口定义**：`StepProtocol` Protocol（见《扩展性设计详细规范》2.2.1）
- **Step 注册机制**：`pipeline.register_step(name, step, after=...)` 方法（见 2.2.2）
- **Step 执行顺序控制**：支持指定插入位置、调整执行顺序、跳过指定步骤（见 2.2.3）
- **Step 依赖管理**：Step 可声明依赖的其他 Step，Pipeline 执行前校验（见 2.2.4）
- **新增 Step 示例**：见《扩展性设计详细规范》2.2.5

#### 1.3 Skill 扩展

- **Skill 类型**：`pre_processor` / `post_processor` / `exporter` / `analyzer`
- **Skill 依赖管理**：通过 `skill.json` 声明依赖，SkillManager 自动解析（见《扩展性设计详细规范》7.1）
- **Skill 配置管理**：每个 Skill 可有自己的配置文件（见 7.2）
- **Skill 沙箱隔离**：用户 Skill 运行在沙箱中，异常不影响主程序（见 7.3）

**V1 实现**：
- Pipeline 类提供 `hook(event, callback)` 和 `register_step(name, step)` 方法
- Skill 加载器自动发现并注册所有 Skill
- 导出菜单根据已注册的 exporter Skill 动态生成
- 用户 Skill 可通过 `skill.json` 声明 Hook 注册需求

### 原则 2：数据层隔离

**核心思想**：项目数据用统一的数据访问层（ProjectStore），后续换数据库不用改业务逻辑。

#### 2.1 ProjectStore 接口定义

- **Protocol 定义**：`ProjectStore` Protocol（见《扩展性设计详细规范》3.1.1）
- **核心方法**：`create_project()` / `get_project()` / `list_projects()` / `update_project()` / `delete_project()`
- **内容读写方法**：`get_novel()` / `save_novel()` / `get_script()` / `save_script()`
- **Beat 级操作方法**：`update_beat()`
- **元信息方法**：`get_meta()` / `update_meta()`

#### 2.2 实现类

- **V1 实现**：`FileSystemProjectStore`（基于文件系统）
- **V2 扩展**：`SQLiteProjectStore`（基于 SQLite 数据库）
- **切换方式**：配置 `project_store_type: "filesystem"` 或 `"sqlite"`（见 3.1.3）

#### 2.3 数据模型版本兼容性

- **新增字段**：使用 `Optional` + 默认值（如 `snapshots: list[SnapshotMeta] | None = None`）
- **V1 代码读取 V2 数据**：Pydantic V2 默认忽略未知字段，不报错
- **数据迁移方案**：V2 提供迁移脚本（见《扩展性设计详细规范》3.1.4）

**V1 实现**：
- 所有项目数据读写通过 `ProjectStore` 接口
- 业务逻辑代码不直接操作文件系统
- `FileSystemProjectStore` 实现文件系统存储
- 后续换 SQLite，只需新增实现类 + 修改配置

### 原则 3：前端组件化

**核心思想**：Alpine.js 组件 + 事件总线，新功能 = 新组件 + 注册路由。

#### 3.1 Alpine.js 组件注册机制

- **组件注册接口**：`registerComponent(name, factory)` 函数（见《扩展性设计详细规范》4.1.1）
- **路由注册机制**：路由表配置化，新增页面只需加配置（见 4.1.2）
- **组件通信规范**：强制通过 EventBus 通信，不允许直接引用其他组件（见 4.1.3）
- **组件生命周期钩子**：`init()`（初始化）+ `destroy()`（销毁）（见 4.1.4）

#### 3.2 事件总线

- **EventBus 实现**：见《扩展性设计详细规范》4.1.3
- **事件类型**：`beat:updated` / `beat:created` / `beat:deleted` / `novel:changed` / `script:changed` 等
- **组件通信示例**：见 4.1.3

#### 3.3 CodeMirror 6 Extension 注册机制

- **Extension 注册接口**：`registerExtension(name, factory)` 函数（见《扩展性设计详细规范》8.1.1）
- **新增 Extension 示例**：见 8.1.2

**V1 实现**：
- 事件总线：`EventBus` 对象，组件间通信通过事件
- 组件注册：`registerComponent()` 函数
- 路由注册：路由表配置化
- 编辑器扩展：CodeMirror 6 的 Extension 系统

### 原则 4：API 版本化

**核心思想**：`/api/v1/` 前缀，后续 V2 功能加 `/api/v2/` 不破坏老接口。

#### 4.1 版本化路由注册

- **路由目录结构**：`api/routes/v1/` + `api/routes/v2/`（见《扩展性设计详细规范》5.1.1）
- **路由注册代码**：见 5.1.2
- **V1 端点**：`/api/v1/projects` / `/api/v1/convert` / `/api/v1/skills` 等
- **V2 新增端点**：`/api/v2/projects/{id}/snapshots` / `/api/v2/convert/incremental` 等

#### 4.2 版本弃用策略

- **新增字段**：允许（必须有默认值），V1 客户端忽略不认识的字段
- **删除字段**：禁止（走新版本）
- **修改语义**：禁止（走新版本）
- **新增端点**：走新版本（如 `/api/v2/...`）
- **老版本保留周期**：至少保留 2 个版本（如 V3 发布后，V1 仍可继续使用）
- **版本弃用策略详细规则**：见《扩展性设计详细规范》5.1.3

**V1 实现**：
- FastAPI 路由统一使用 `/api/v1/` 前缀
- API 响应包含 `version` 字段
- 后续新增 `/api/v2/` 路由，与 `/api/v1/` 共存

### 原则 5：配置驱动

**核心思想**：新功能通过 config.json 开关控制，不硬编码。

#### 5.1 功能开关配置

- **配置模型**：`AppConfig` 中的 `features: dict[str, bool]` 字段（见《扩展性设计详细规范》6.1.1）
- **功能开关使用**：后端通过 `config.features.get("feature_name", False)` 判断（见 6.1.2）
- **前端使用**：根据功能开关显示/隐藏 UI 元素（见 6.1.2）

#### 5.2 功能依赖管理

- **配置声明**：`feature_dependencies` 字段（见《扩展性设计详细规范》6.1.3）
- **依赖校验逻辑**：`validate_feature_dependencies()` 函数（见 6.1.3）

#### 5.3 配置层级

```
默认值（代码中）
    ↓ 覆盖
全局配置文件（~/.novel2script/config.json）
    ↓ 覆盖
项目配置快照（config_snapshot.json）
    ↓ 覆盖
环境变量（N2S_ 前缀）
    ↓ 覆盖
运行时参数（CLI --option / API 请求体）
```

**V1 实现**：
- 配置文件包含 `features` 字段，所有功能开关集中管理
- 前端根据功能开关显示/隐藏 UI 元素
- 后端根据功能开关启用/禁用 Pipeline 环节
- 后续新增功能只需加新开关，无需改代码逻辑
- 功能依赖通过 `feature_dependencies` 字段声明

### 原则 6：扩展性检查清单

**每次新增功能时，必须检查以下清单**（详见《扩展性设计详细规范》10.1）：

| 检查项 | 说明 | 是否满足 |
|-------|------|---------|
| **是否新增了文件，而非修改现有文件？** | 新增功能应该通过新增文件实现（如新增 Step 类、新增 Extension 等） | ✅ / ❌ |
| **是否通过注册机制接入，而非修改核心代码？** | 新增功能应该通过注册机制（如 `register_step()`, `hook()`, `registerComponent()` 等）接入 | ✅ / ❌ |
| **是否通过配置开关控制，而非硬编码？** | 新增功能应该有对应的配置开关（如 `features.new_feature`） | ✅ / ❌ |
| **是否保持了向后兼容性？** | 新增字段应该用 `Optional` + 默认值，不修改已有字段的语义 | ✅ / ❌ |
| **是否编写了单元测试？** | 新增功能应该有对应的单元测试 | ✅ / ❌ |
| **是否更新了文档？** | 新增功能应该更新 PRD、架构设计文档、API 文档等 | ✅ / ❌ |

---

## 17. 扩展性设计详细规范引用

> 以上 5 大原则的具体实现细节，请参考《扩展性设计详细规范.md》文档。

该文档详细回答了以下 10 个质询问题：

1. **Pipeline Hook 的具体接口定义** —— 见 2.1.1 Hook 接口定义
2. **Hook 的执行顺序保证** —— 见 2.1.3 Hook 注册机制 + 2.1.4 Hook 执行顺序保证
3. **Hook 的异常处理策略** —— 见 2.1.5 Hook 异常处理策略
4. **用户 Skill 如何零代码注册 Hook** —— 见 2.1.6 用户 Skill 如何零代码注册 Hook
5. **数据模型的版本兼容性** —— 见 3.1.4 数据模型版本兼容性设计
6. **数据迁移策略** —— 见 3.1.4 数据模型版本兼容性设计（V2 数据迁移方案）
7. **ProjectStore 接口是否支持复杂查询** —— 见 3.1.1 ProjectStore Protocol（`list_projects()` 方法支持 `search` / `sort_by` / `order` 参数）
8. **前端路由注册的接口** —— 见 4.1.2 路由注册机制
9. **组件通信的规范** —— 见 4.1.3 组件通信规范
10. **组件是否有生命周期钩子** —— 见 4.1.4 组件生命周期钩子

---

## 18. 扩展性设计原则总结

| 原则 | 核心思想 | 技术方案 | 不改源码的扩展方式 |
|------|---------|---------|---------|
| **插件式架构** | 所有新功能通过插件接入，不修改核心代码 | Hook 机制 + Step 插件 + Skill 系统 | 新增文件 + 注册机制 |
| **数据层隔离** | 业务逻辑不直接操作数据，通过接口访问 | ProjectStore Protocol + 依赖注入 | 新增实现类 + 配置切换 |
| **前端组件化** | 新功能 = 新组件 + 注册，不修改现有组件 | Alpine.js 组件 + EventBus + CodeMirror 6 Extension | 新增组件 + 注册 |
| **API 版本化** | 新版本 API 不影响旧版本客户端 | `/api/v1/` `/api/v2/` 路由分离 | 新增路由文件 + 注册 |
| **配置驱动** | 功能开关通过配置控制，不硬编码 | pydantic-settings + features 字段 | 新增配置字段 + 功能开关 |

---

# 附录

## 附录 A：功能优先级清单

### P0（必须完成，3 天内交付）

1. CLI convert / validate 命令
2. 桌面模式：PyWebView 独立窗口 + 回退浏览器
3. **内置编辑器：左右分栏 + CodeMirror 6**
4. **内置编辑器：YAML 语法高亮 + Schema 校验 lint**
5. **内置编辑器：小说章节折叠**
6. **内置编辑器：滚动联动**
7. **内置编辑器：Beat 内联编辑（对白/情绪/角色）**
8. **内置编辑器：自动保存**
9. **内置编辑器：导出 .yaml / .fountain / .txt**
10. **项目管理：项目列表首页**
11. **项目管理：自动创建项目（转换后）**
12. **项目管理：项目持久化存储**
13. **项目管理：进入项目继续编辑**
14. 用户自选 AI（6 预设 + 自定义）
15. 配置持久化（config.json）
16. 长文本智能分段（6000 字 + 200 字上下文）
17. SSE 实时进度推送
18. Skill 引擎：加载器 + 运行器
19. 内置 Skill：Fountain 导出
20. Skill 管理页面 + CLI skill 命令
21. PyInstaller 打包为单文件 exe

### P1（尽量完成，提升体验）

1. 编辑器分栏折叠
2. 小说预处理（编辑原文、删章节）
3. Beat 类型切换 / 新增删除 Beat
4. 项目搜索 / 排序
5. 项目配置查看
6. 连接测试
7. 内置 Skill：角色分析报告 / 对白润色 / 风格适配 / 章节概要
7. Skill 创建模板 / 安装（本地路径）
8. Token 估算
9. .docx 文件解析
10. 中间结果预览
11. 原文溯源查看
12. 桌面模式单实例运行

### P2（后续迭代）

1. 小说预处理：合并段落、加标记
2. 编辑器"专注模式"
3. 角色关系图可视化
4. 撤销/重做
5. 批量处理（CLI --input-dir）
6. Skill 热加载

---

## 附录 B：API 端点设计（FastAPI）

> 所有端点统一使用 `/api/v1/` 前缀，后续 V2/V3 新增端点使用 `/api/v2/` `/api/v3/` 前缀。

### 项目 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/projects` | 获取项目列表（支持 `?search=` `?sort=` `?order=` 参数） |
| POST | `/api/v1/projects` | 创建新项目 |
| GET | `/api/v1/projects/{project_id}` | 获取项目详情 |
| PUT | `/api/v1/projects/{project_id}` | 更新项目（标题、状态等） |
| DELETE | `/api/v1/projects/{project_id}` | 删除项目 |
| GET | `/api/v1/projects/{project_id}/novel` | 获取项目小说原文 |
| PUT | `/api/v1/projects/{project_id}/novel` | 更新小说原文 |
| GET | `/api/v1/projects/{project_id}/script` | 获取项目 YAML 剧本 |
| PUT | `/api/v1/projects/{project_id}/script` | 更新 YAML 剧本 |
| GET | `/api/v1/projects/{project_id}/config-snapshot` | 获取转换时的配置快照 |
| GET | `/api/v1/projects/{project_id}/edit-state` | 获取编辑器状态（滚动位置等） |
| PUT | `/api/v1/projects/{project_id}/edit-state` | 保存编辑器状态 |
| POST | `/api/v1/projects/{project_id}/convert` | 在项目内启动/重新转换 |
| GET | `/api/v1/projects/{project_id}/stream` | SSE 实时进度推送 |
| POST | `/api/v1/projects/{project_id}/export` | 导出项目（`?format=yaml/fountain/txt`） |
| POST | `/api/v1/projects/{project_id}/validate` | 校验当前剧本 |

### 转换 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/convert` | 启动转换任务（返回 task_id） |
| GET | `/api/v1/convert/{task_id}/status` | 查询转换进度 |
| GET | `/api/v1/convert/{task_id}/result` | 获取转换结果 |
| GET | `/api/v1/convert/{task_id}/stream` | SSE 实时进度推送 |
| POST | `/api/v1/convert/{task_id}/save` | 保存结果到项目 |

### 配置 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/config` | 获取当前配置（API Key 脱敏） |
| PUT | `/api/v1/config` | 更新配置 |
| POST | `/api/v1/config/test` | 测试 API 连接 |

### Skill API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/skills` | 获取所有已安装 Skill 列表（内置+用户自定义，同名覆盖标注） |
| GET | `/api/v1/skills/{name}` | 获取指定 Skill 的元信息 |
| POST | `/api/v1/skills/{name}/run` | 运行指定 Skill |
| POST | `/api/v1/skills/create` | 创建用户自定义 Skill 模板 |
| POST | `/api/v1/skills/install` | 从本地路径安装 Skill |
| DELETE | `/api/v1/skills/{name}` | 卸载用户自定义 Skill（内置不可卸载，返回 403） |
| GET | `/api/v1/skills/{name}/template` | 获取 Skill 模板代码 |

### 通用 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回 Web UI 主页面 |
| POST | `/api/v1/upload` | 上传文件，返回文本内容 |
| POST | `/api/v1/validate` | 校验 YAML 文件 |

**Skill 运行请求示例**：

```json
POST /api/v1/skills/character-analysis/run
{
  "input_data": "<YAML 剧本文本或 project_id>",
  "config": {
    "detail_level": "full"
  }
}
```

**Skill 运行响应示例**：

```json
{
  "skill_name": "character-analysis",
  "success": true,
  "data": {
    "characters": [
      {
        "id": "char_001",
        "name": "张三",
        "appearance_count": 45,
        "dialogue_ratio": 0.32,
        "emotion_distribution": {"平静": 15, "愤怒": 10, "悲伤": 8},
        "relationships": [{"target": "char_002", "type": "对立", "scenes": 12}]
      }
    ]
  },
  "error": null,
  "duration_ms": 1520
}
```

---

## 附录 C：用户数据目录结构

```
~/.novel2script/
├── config.json                  # 用户配置（含 features 开关）
├── projects/                    # 项目数据
│   ├── <project_id_1>/
│   │   ├── project.json         # 项目元信息
│   │   ├── novel.txt            # 小说原文
│   │   ├── script.yaml          # YAML 剧本
│   │   ├── config_snapshot.json # 转换配置快照
│   │   ├── edit_meta.json       # 编辑元数据
│   │   ├── snapshots/           # [V2] 版本快照
│   │   └── annotations/         # [V2] 批注
│   └── <project_id_2>/
│       └── ...
├── skills/                      # 用户自定义 Skill
│   ├── my-custom-skill/
│   │   ├── skill.json
│   │   └── main.py
│   └── ...
└── cache/                       # 运行时缓存
```

## 附录 D：源码目录结构

```
novel2script/
├── src/
│   ├── __init__.py
│   ├── main.py                  # CLI 入口（typer）：gui / convert / validate / skill
│   ├── desktop.py               # PyWebView 桌面模式入口
│   ├── server.py                # FastAPI 服务入口（/api/v1/ 路由）
│   ├── pipeline.py              # 流程编排（含 Hook 机制）
│   ├── models.py                # Pydantic 数据模型
│   ├── preprocessor.py          # 文本预处理
│   ├── character_extractor.py   # 角色识别
│   ├── scene_splitter.py        # 场景分割
│   ├── dialogue_parser.py       # 对白解析
│   ├── emotion_tagger.py        # 情绪标注
│   ├── yaml_generator.py        # YAML 生成
│   ├── validator.py             # Schema 校验
│   ├── llm_client.py            # LLM 调用封装
│   ├── config.py                # 配置管理
│   ├── project_store.py         # 项目数据访问层（抽象 + 文件系统实现）
│   ├── skills/                  # Skill 引擎
│   │   ├── __init__.py
│   │   ├── loader.py            # Skill 加载器（SkillSource 抽象）
│   │   ├── runner.py            # Skill 运行器
│   │   └── builtins/            # 内置 Skill
│   │       ├── fountain-export/
│   │       ├── character-analysis/
│   │       ├── dialogue-polish/
│   │       ├── style-adapt/
│   │       └── chapter-summary/
│   ├── prompts/                 # Prompt 模板
│   └── static/                  # Web UI 前端文件
│       ├── index.html           # Alpine.js + Tailwind CSS CDN
│       ├── css/
│       ├── js/
│       │   ├── app.js           # 主应用（路由 + 事件总线）
│       │   ├── editor.js        # 编辑器组件（CodeMirror 6）
│       │   ├── projects.js      # 项目列表组件
│       │   ├── skills.js        # Skill 管理组件
│       │   └── settings.js      # 设置组件
│       └── vendor/              # 第三方库（CDN fallback）
│           └── codemirror/      # CodeMirror 6 本地缓存
├── tests/
├── docs/
│   ├── architecture.md
│   ├── yaml-schema.md
│   ├── prompt-design.md
│   └── PRD.md
├── pyproject.toml
├── novel2script.spec            # PyInstaller 打包配置
└── README.md
```

---

> 本内容由 Coze AI 生成，请遵循相关法律法规及《人工智能生成合成内容标识办法》使用与传播。
