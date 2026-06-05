---
AIGC:
    Label: "1"
    ContentProducer: 001191110102MACQD9K64018705
    ProduceID: 520543646253513_0/project_7647746939261518126-files/novel-to-script/docs/architecture.md
    ReservedCode1: ""
    ContentPropagator: 001191110102MACQD9K64028705
    PropagateID: 520543646253513#1780649059059
    ReservedCode2: ""
---
# Novel2Script 架构设计文档

> 版本：V1 | 日期：2026-06-05 | 状态：设计阶段
>
> 核心原则：**插件式扩展，核心不动** —— 每个模块都设计扩展点，后续加功能不改老代码。

---

## 目录

1. [系统概览](#1-系统概览)
2. [技术选型](#2-技术选型)
3. [模块设计](#3-模块设计)
4. [Pipeline 扩展设计](#4-pipeline-扩展设计)
5. [编辑器架构](#5-编辑器架构)
6. [项目管理架构](#6-项目管理架构)
7. [Skill 系统](#7-skill-系统)
8. [配置管理](#8-配置管理)
9. [错误处理](#9-错误处理)
10. [性能](#10-性能)
11. [部署](#11-部署)
12. [扩展性设计专题](#12-扩展性设计专题)
13. [附录](#附录)

---

## 1. 系统概览

### 1.1 目标与约束

**目标**：将 3 章以上小说自动转换为结构化 YAML 剧本，覆盖角色识别、场景分割、对白/动作/旁白分类、情绪标注全流程。提供桌面窗口、Web UI、CLI 三种使用方式，支持用户自选 AI 模型，支持 Skill 插件扩展，支持项目管理与编辑器交互。

**约束**：

- 本地安装运行，不依赖云服务（除 LLM API 外）
- 运行环境为普通笔记本（8-16GB 内存，无 GPU 要求）
- LLM 是核心依赖，通过用户自选的 OpenAI API 兼容接口调用
- 输入为 TXT/Markdown，输出为 YAML，格式需严格可校验
- 小说长度可能达 10 万字以上，必须处理长文本问题
- 前端不允许引入 Node.js 构建流程，零构建直接运行
- 单机单用户，不需要多用户认证/权限体系
- 打包为 exe 后用户无需安装 Python，双击即可运行

### 1.2 分层架构图

```
┌─────────────────────────────────────────────────────────┐
│                  UI 层（可替换）                          │
│  PyWebView / Browser / CLI / 未来 Electron               │
├─────────────────────────────────────────────────────────┤
│                API 层（版本化）                           │
│  /api/v1/...  /api/v2/...                               │
├─────────────────────────────────────────────────────────┤
│              业务层（核心不动）                            │
│  Pipeline / ProjectStore / SkillManager                  │
├─────────────────────────────────────────────────────────┤
│              扩展层（插件式）                              │
│  Skills / Hooks / Steps / Exporters                      │
├─────────────────────────────────────────────────────────┤
│              数据层（隔离）                               │
│  FileSystem / 未来 SQLite                          │
└─────────────────────────────────────────────────────────┘
```

**五层职责**：

| 层级 | 职责 | 替换成本 | 变更频率 |
|------|------|---------|---------|
| **UI 层** | 用户交互、视图渲染 | 低（可整体替换） | 高 |
| **API 层** | 接口定义、请求路由、版本管理 | 中（版本化隔离） | 中 |
| **业务层** | 核心逻辑编排、项目生命周期 | **极高（不动）** | **低** |
| **扩展层** | 插件注册、钩子回调、步骤注入 | 低（即插即用） | 高 |
| **数据层** | 数据存取、持久化、隔离 | 中（接口不变） | 低 |

**核心不变性保证**：业务层（Pipeline / ProjectStore / SkillManager）的公开接口一旦发布即冻结，所有新功能通过扩展层注入，不修改业务层代码。

### 1.3 三种运行模式

| 维度 | 桌面窗口模式（默认） | Web UI 模式 | CLI 模式 |
|------|---------------------|------------|---------|
| 入口 | `novel2script gui` 或双击 exe | `novel2script serve` | `novel2script convert` |
| 窗口 | PyWebView 独立窗口 | 系统浏览器 | 终端 |
| 进度反馈 | SSE → PyWebView 内页面 | SSE → 浏览器页面 | Rich 进度条 + 日志 |
| 文件输入 | 页面上传 / 项目管理 | 页面上传 / 项目管理 | 命令行参数指定路径 |
| 配置管理 | 页面设置 | 页面设置 | `--config` 参数 / 交互式引导 |
| 输出获取 | 页面下载 / 项目内保存 | 页面下载 / 项目内保存 | 直接写入本地路径 |
| 核心逻辑 | **完全相同** | **完全相同** | **完全相同** |
| 关闭方式 | 关闭窗口 → 退出程序 | Ctrl+C | 命令执行完退出 |

### 1.4 整体数据流

```
小说文件（TXT/MD）
      │
      ▼
  ┌──────────────┐     ┌──────────────────────────────┐
  │  项目管理层   │────▶│  ProjectStore                 │
  │  创建/保存项目 │     │  novel.md + script.yaml       │
  └──────┬───────┘     │  meta.json + config_snapshot  │
         │              └──────────────────────────────┘
         ▼
  ┌──────────────┐     ┌──────────────────────────────┐
  │  编辑器模块   │◀───▶│  双栏编辑 + 滚动联动          │
  │  CodeMirror 6 │     │  Beat 内联编辑                │
  └──────┬───────┘     └──────────────────────────────┘
         │ 保存
         ▼
  ┌──────────────────────────────────────────────────┐
  │              核心转换 Pipeline                      │
  │  章节 → 角色 → 场景 → 对白 → 情绪 → YAML           │
  │  ┌──────────────────────────────────────┐         │
  │  │  Hook 钩子 + Step 插件 + Skill 注入   │         │
  │  └──────────────────────────────────────┘         │
  └──────────────────────────────────────────────────┘
         │
         ▼
  YAML 剧本（Schema 校验通过）
         │
         ▼
  ┌──────────────┐
  │  Skill 系统   │  exporter / analyzer / post_processor
  └──────────────┘
```

---

## 2. 技术选型

> 每项选型均包含：**选了什么** → **为什么** → **没选什么** → **为什么没选** → **扩展性考量**

### 2.1 后端框架

| 维度 | 说明 |
|------|------|
| **选了** | **FastAPI** |
| **为什么** | 异步原生、自带 SSE 支持（`StreamingResponse`）、自动生成 OpenAPI 文档、性能高（基于 Starlette + uvicorn）；自带依赖注入系统便于模块解耦 |
| **没选** | Flask / Django / Starlette |
| **为什么没选** | Flask 非异步；Django 太重；Starlette 太底层需手写太多 |
| **扩展性考量** | FastAPI 的 Router 机制天然支持 API 版本化（v1/v2 路由分离）；中间件机制可无缝注入日志/限流/CORS；依赖注入系统可替换实现类而不改接口 |

### 2.2 桌面窗口

| 维度 | 说明 |
|------|------|
| **选了** | **pywebview** |
| **为什么** | 轻量（约 5MB），Python 原生，Windows 用 WebView2 / Mac 用 WebKit / Linux 用 WebKitGTK；无额外工具链依赖；双击 exe 即可启动独立窗口 |
| **没选** | Electron / Tauri / Qt WebEngine |
| **为什么没选** | Electron 太重（300MB+），需 Node.js；Tauri 需 Rust 工具链；Qt WebEngine 需 PyQt/PySide 依赖且体积大 |
| **扩展性考量** | pywebview 是窗口壳，内部跑的是标准 Web 页面；未来换 Electron/Tauri 只需替换窗口壳层，前端代码零改动 |

### 2.3 前端框架

| 维度 | 说明 |
|------|------|
| **选了** | **HTML + Tailwind CSS + Alpine.js + CodeMirror 6** |
| **为什么** | CDN 引入零构建；Alpine.js 16KB gzip 处理响应式绑定足够；CodeMirror 6 是编辑器领域的工业标准，模块化 Extension 架构天然支持扩展 |
| **没选** | React / Vue / Svelte / Monaco Editor |
| **为什么没选** | React/Vue/Svelte 引入 Node.js 构建流程，门槛大幅提高；Monaco 体积大（2MB+），模块化不如 CodeMirror 6，非 VS Code 场景过重 |
| **扩展性考量** | CodeMirror 6 的 Extension 机制是核心扩展点：新功能 = 新 Extension（批注、AI 补全、diff 高亮），无需修改编辑器核心；Alpine.js 组件化轻量，后续可渐进升级为 Vue/React 而不影响后端 |

### 2.4 LLM 客户端

| 维度 | 说明 |
|------|------|
| **选了** | **openai SDK (Python)** |
| **为什么** | 官方维护，兼容所有 OpenAI API 格式的服务商（OpenAI、DeepSeek、通义千问、Ollama 本地模型等）；结构化输出支持好 |
| **没选** | LangChain / LlamaIndex / litellm |
| **为什么没选** | LangChain/LlamaIndex 学习成本和调试成本高于收益，抽象层过厚；litellm 多了一层代理，对本地工具是多余依赖 |
| **扩展性考量** | 通过 LLMClient Protocol 封装，后续换模型 SDK / 加本地模型支持 / 加流式输出，只需写新实现类，Pipeline 代码不动 |

### 2.5 YAML / Schema 处理

| 维度 | 说明 |
|------|------|
| **选了** | **PyYAML + Pydantic V2** |
| **为什么** | PyYAML 做序列化/反序列化，Pydantic V2 做 Schema 校验和类型安全（Tagged Union Beat）。Pydantic V2 比 V1 快 5-50 倍 |
| **没选** | ruamel.yaml / marshmallow / cerberus |
| **为什么没选** | ruamel.yaml 注释保留功能我们不需要；marshmallow/cerberus 不如 Pydantic 与 FastAPI 集成紧密 |
| **扩展性考量** | Pydantic V2 的 Tagged Union 机制天然支持 Beat 类型扩展：加新 Beat 类型只需在 Union 中添加新模型，校验自动生效；Pydantic V2 支持 JSON Schema 导出，前端可直接用做校验 |

### 2.6 CLI 框架

| 维度 | 说明 |
|------|------|
| **选了** | **Typer + Rich** |
| **为什么** | Typer 基于 click 但更简洁，自动生成帮助文档；Rich 提供进度条、表格、语法高亮等美观输出 |
| **没选** | argparse / click / docopt |
| **为什么没选** | argparse 太原始；click 需手写太多装饰器；docopt 维护不活跃 |
| **扩展性考量** | Typer 的子命令组机制支持按模块注册命令，后续加新子命令只需新增函数 + 注册 |

### 2.7 实时通信

| 维度 | 说明 |
|------|------|
| **选了** | **SSE (Server-Sent Events)** |
| **为什么** | 单向推送够用（后端→前端），比 WebSocket 简单得多，FastAPI 原生支持，浏览器原生 `EventSource` API |
| **没选** | WebSocket / Long Polling / gRPC-streaming |
| **为什么没选** | WebSocket 双向通信能力和握手复杂度多余；Long Polling 性能差；gRPC-streaming 需要额外依赖且前端不原生支持 |
| **扩展性考量** | SSE 事件类型可自由扩展（新增事件 = 新增 event type，前端按需订阅）；V2 若需双向通信可渐进引入 WebSocket，与 SSE 共存 |

### 2.8 Skill 系统加载

| 维度 | 说明 |
|------|------|
| **选了** | **importlib 动态加载** |
| **为什么** | Python 标准库，无需额外依赖；运行时发现和加载 Skill，支持用户扩展而不修改核心代码 |
| **没选** | Pluggy / Stevedore / setuptools entry_points |
| **为什么没选** | Pluggy/Stevedore 引入插件框架是过度设计；entry_points 需要安装才能发现，不适合运行时动态加载 |
| **扩展性考量** | Skill 接口用 Protocol 定义，后续加异步 Skill / 流式 Skill 只需扩展 Protocol；Skill 注册表可替换：后续在线安装 = 新的 SkillSource 实现 |

### 2.9 打包方案

| 维度 | 说明 |
|------|------|
| **选了** | **PyInstaller** |
| **为什么** | 成熟稳定，支持单文件/单目录打包，自动收集依赖和数据文件；无需用户安装 Python |
| **没选** | Nuitka / cx_Freeze |
| **为什么没选** | Nuitka 兼容性和调试体验不如 PyInstaller；cx_Freeze 配置繁琐，对动态导入和数据文件支持不灵活 |
| **扩展性考量** | PyInstaller 的 spec 文件支持 hook 脚本，后续加新依赖可通过 hook 脚本收集而无需手动配置 |

### 2.10 配置管理

| 维度 | 说明 |
|------|------|
| **选了** | **pydantic-settings** |
| **为什么** | 基于 Pydantic V2，类型安全的配置管理，支持环境变量、.env 文件、JSON 配置文件 |
| **没选** | configparser / dynaconf / hydra |
| **为什么没选** | configparser 无类型校验；dynaconf/hydra 对单配置文件场景过重 |
| **扩展性考量** | pydantic-settings 的模型继承机制支持配置分层（默认值 → 文件 → 环境变量 → 运行时覆盖），后续加配置源只需扩展模型 |

---

## 3. 模块设计

### 3.1 启动层

#### 职责

统一入口分发，根据命令行参数启动不同运行模式。

#### 入口设计

```
novel2script gui      → PyWebView 桌面窗口
novel2script serve    → Web 服务器模式
novel2script convert  → CLI 模式
双击 exe              → 默认 gui
```

```python
# src/__main__.py
import sys

def main():
    if len(sys.argv) <= 1:
        # 双击 exe，无参数时默认启动 gui
        sys.argv.append("gui")
    from novel2script.cli import app
    app()

if __name__ == "__main__":
    main()
```

#### 回退机制

```python
def start_gui(host: str, port: int):
    """启动 GUI 模式，自动回退"""
    try:
        import webview  # pywebview
        app = DesktopApp(host, port)
        app.start()
    except ImportError:
        # pywebview 未安装，回退到默认浏览器
        import webbrowser
        from novel2script.api.main import app as fastapi_app
        import uvicorn
        print("⚠️  pywebview 未安装，使用浏览器模式")
        print(f"   访问地址: http://{host}:{port}")
        webbrowser.open(f"http://{host}:{port}")
        uvicorn.run(fastapi_app, host=host, port=port)
```

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增运行模式（如 Electron 壳） | 在 CLI 注册新子命令，实现对应启动函数 | 仅 `cli.py` |
| 自定义回退链 | 在 `start_gui` 中添加 `except` 分支 | 仅 `desktop/window.py` |
| 启动时初始化钩子 | 在 `lifespan` 中注册 `on_startup` 回调 | 仅 `api/main.py` |

---

### 3.2 API 层

#### 职责

提供版本化的 HTTP 接口，路由请求到业务层，处理序列化/反序列化。

#### 目录结构

```
api/
├── __init__.py
├── main.py              # FastAPI app 创建、中间件、生命周期
├── routes/
│   ├── v1/              # V1 版本路由
│   │   ├── __init__.py
│   │   ├── convert.py   # 转换相关 API
│   │   ├── config.py    # 配置相关 API
│   │   ├── files.py     # 文件上传下载
│   │   ├── projects.py  # 项目管理 API
│   │   ├── editor.py    # 编辑器 API
│   │   └── skills.py    # Skill 相关 API
│   └── v2/              # V2 版本路由（未来）
│       └── __init__.py
└── sse.py               # SSE 推送管理
```

#### 版本化路由注册

```python
# api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：加载配置、初始化 LLM 客户端、初始化 SkillManager
    app.state.config = load_config()
    app.state.project_store = FileSystemProjectStore()
    app.state.skill_manager = SkillManager(app.state.config)
    app.state.skill_manager.discover()
    yield
    # 关闭时：清理临时文件

app = FastAPI(title="Novel to Script", lifespan=lifespan)

# V1 版本路由
from novel2script.api.routes.v1 import (
    convert_router, config_router, files_router,
    projects_router, editor_router, skills_router,
)
app.include_router(convert_router, prefix="/api/v1/convert", tags=["v1-convert"])
app.include_router(config_router, prefix="/api/v1/config", tags=["v1-config"])
app.include_router(files_router, prefix="/api/v1/files", tags=["v1-files"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["v1-projects"])
app.include_router(editor_router, prefix="/api/v1/editor", tags=["v1-editor"])
app.include_router(skills_router, prefix="/api/v1/skills", tags=["v1-skills"])

# 挂载前端静态文件（最后挂载，作为 fallback）
app.mount("/", StaticFiles(directory="src/web", html=True), name="web")
```

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增 API 版本 | 创建 `routes/v2/` 目录，注册新 Router | 仅 `main.py` 加一行 |
| 新增 API 端点 | 在对应版本目录下新增路由文件 | 仅 `routes/v1/` |
| 替换序列化方案 | 在 Router 层替换响应模型 | 仅路由层 |
| 加中间件（日志/限流） | `app.add_middleware()` | 仅 `main.py` |

---

### 3.3 核心 Pipeline

#### 职责

编排小说转剧本的完整流程，管理步骤执行顺序、中间状态、错误恢复、进度回调。

#### 目录结构

```
core/
├── __init__.py
├── pipeline.py           # 流水线编排
├── steps/                # 步骤插件目录
│   ├── __init__.py
│   ├── base.py           # StepProtocol 定义
│   ├── character_extractor.py
│   ├── scene_splitter.py
│   ├── dialogue_parser.py
│   ├── emotion_tagger.py
│   └── yaml_generator.py
├── text_segmenter.py      # 长文本智能分段
└── merger.py              # 分段结果合并
```

#### Pipeline 执行流程

```
输入文件
  │
  ▼
【Hook: before_convert】
  │
  ▼
【pre_processor Skills】
  │
  ▼
text_segmenter.segment()           # 智能分段（如需要）
  │
  ▼
【Step: character_extractor】      # 角色识别（全量）
  │  Hook: after_step("character_extractor")
  ▼
【Step: scene_splitter】           # 场景分割（按段/章）
  │  Hook: after_step("scene_splitter")
  ▼
【Step: dialogue_parser】          # 对白解析（场景级并行）
  │  Hook: after_step("dialogue_parser")
  ▼
【Step: emotion_tagger】           # 情绪标注（场景级并行）
  │  Hook: after_step("emotion_tagger")
  ▼
merger.merge()                     # 分段结果合并（如分段过）
  │
  ▼
【Step: yaml_generator】           # YAML 生成 + 校验
  │  Hook: after_step("yaml_generator")
  ▼
【Step: quality_checker】          # 质量检查（生成 conversion_notes）
  │  Hook: after_step("quality_checker")
  ▼
【Hook: after_convert】
  │
  ▼
【post_processor Skills】
  │
  ▼
【exporter Skills】
  │
  ▼
输出结果
```

#### 进度回调协议

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ProgressCallback(Protocol):
    """进度回调协议，Web / 桌面 / CLI 各自实现"""
    def on_step_start(self, step: str, total_steps: int, current: int) -> None: ...
    def on_step_progress(self, step: str, detail: str, percent: float) -> None: ...
    def on_step_complete(self, step: str, result_summary: str) -> None: ...
    def on_error(self, step: str, error: str) -> None: ...
```

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增转换步骤 | 实现 `StepProtocol`，调用 `pipeline.register_step()` | 仅新增文件 + 一行注册 |
| 增量转换 | 实现 `pipeline.run_chapters([2, 3])` | Pipeline 内部，接口不变 |
| 步骤重排序 | 通过 `pipeline.reorder_steps()` 调整 | 无代码改动 |
| 自定义进度回调 | 实现 `ProgressCallback` 协议 | 仅调用方 |
| 步骤级并行度调整 | 通过配置修改 Semaphore 值 | 仅配置文件 |

---

### 3.4 LLM Client

#### 职责

封装 LLM API 调用，处理认证、重试、错误格式修复、限速退避。

#### 接口设计

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMClientProtocol(Protocol):
    """LLM 客户端协议"""
    async def chat(self, prompt: str, **kwargs) -> str: ...
    async def chat_json(self, prompt: str, schema: type, **kwargs) -> dict: ...
    async def chat_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]: ...
```

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 支持新 LLM 提供商 | 实现 `LLMClientProtocol` | 仅新增文件 |
| 本地模型支持 | 新增 `OllamaLLMClient` | 仅新增文件 |
| 流式输出 | `chat_stream` 方法已在 Protocol 中 | 无代码改动 |
| 请求/响应拦截 | 在实现类中加拦截器 | 仅实现类 |

---

### 3.5 Schema（Pydantic V2）

#### 职责

定义 YAML 剧本的数据模型，提供类型安全、校验、序列化。

#### 核心模型：Tagged Union Beat

```python
from pydantic import BaseModel, TaggedUnion

class DialogueBeat(BaseModel):
    type: Literal["dialogue"] = "dialogue"
    character: str
    content: str
    emotion: str | None = None

class ActionBeat(BaseModel):
    type: Literal["action"] = "action"
    content: str

class NarrationBeat(BaseModel):
    type: Literal["narration"] = "narration"
    content: str

Beat = Annotated[
    Union[Annotated[DialogueBeat, Tag("dialogue")],
          Annotated[ActionBeat, Tag("action")],
          Annotated[NarrationBeat, Tag("narration")]],
    Discriminator("type"),
]
```

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增 Beat 类型 | 在 Union 中添加新模型 | 仅 `schema.py` 加一个类 |
| Beat 自定义字段 | 扩展对应 Beat 模型 | 仅对应 Beat 模型 |
| 前端 Schema 校验 | 导出 JSON Schema → CodeMirror 校验 | 无后端改动 |

---

### 3.6 ConfigManager

#### 职责

管理应用配置的加载、校验、持久化、运行时覆盖。

```python
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="N2S_",
        json_file="~/.novel2script/config.json",
        json_file_encoding="utf-8",
    )
    api_key: str = ""
    api_endpoint: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_concurrent: int = 3
    # ...
```

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增配置项 | 在 `AppConfig` 中添加字段 | 仅 `config.py` |
| 新增配置源 | 继承 `AppConfig` 覆盖 `model_config` | 仅 `config.py` |
| 项目级配置覆盖 | 读取 `config_snapshot.json` 合并 | 仅 ProjectStore |

---

### 3.7 SSE 进度推送

#### 职责

通过 Server-Sent Events 向前端推送实时进度。

#### SSE 事件类型

| 事件 | 触发时机 | 数据 |
|------|---------|------|
| `step_start` | 步骤开始 | `{step, total_steps, current}` |
| `step_progress` | 步骤内进度更新 | `{step, detail, percent}` |
| `step_complete` | 步骤完成 | `{step, result_summary}` |
| `step_error` | 步骤出错 | `{step, error}` |
| `task_complete` | 任务完成 | `{result}` |
| `task_failed` | 任务失败 | `{error}` |
| `skill_start` | Skill 开始执行 | `{skill_name}` |
| `skill_complete` | Skill 执行完成 | `{skill_name, result}` |
| `skill_error` | Skill 执行出错 | `{skill_name, error}` |
| `project_saved` | 项目保存成功 | `{project_id, file_type}` |

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增事件类型 | 添加新 event type | 仅 `sse.py` |
| SSE → WebSocket 迁移 | 替换推送实现，事件类型不变 | 仅 `sse.py` |

---

### 3.8 TextSegmenter（长文本分段）

#### 职责

将超长小说（> 阈值）智能分段，每段独立处理后再合并。

#### 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新的分段策略 | 实现 `SegmentStrategy` Protocol | 仅新增文件 |
| 动态阈值 | 从配置读取分段阈值 | 仅配置文件 |

---

## 4. Pipeline 扩展设计

> 本章是架构的核心：Pipeline 是业务层的脊柱，必须保证"核心不动，扩展自由"。

### 4.1 Step 插件机制

每个 Pipeline 步骤是一个独立的 Step 类，实现 `StepProtocol`：

```python
from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class StepProtocol(Protocol):
    """Pipeline 步骤协议"""
    @property
    def name(self) -> str: ...

    async def run(self, context: PipelineContext) -> PipelineContext: ...
```

**PipelineContext** 是步骤间传递的数据容器：

```python
class PipelineContext:
    """Pipeline 步骤间传递的上下文"""
    novel_text: str                              # 原始文本
    chapters: list[Chapter]                      # 章节列表
    characters: CharacterRegistry | None         # 角色注册表
    scenes: list[Scene] | None                   # 场景列表
    beats: list[Beat] | None                     # Beat 列表
    segments: list[Segment] | None               # 分段列表
    metadata: dict[str, Any]                     # 扩展元数据（步骤可自由读写）
    config: AppConfig                            # 配置快照
```

**注册与编排**：

```python
class Pipeline:
    def __init__(self):
        self._steps: dict[str, StepProtocol] = {}
        self._step_order: list[str] = []
        self._hooks: dict[str, list[Callable]] = {}

    def register_step(self, name: str, step: StepProtocol, after: str | None = None):
        """注册步骤，可指定插入位置"""
        self._steps[name] = step
        if after:
            idx = self._step_order.index(after) + 1
            self._step_order.insert(idx, name)
        else:
            self._step_order.append(name)

    def reorder_steps(self, new_order: list[str]) -> None:
        """重排步骤执行顺序

        Args:
            new_order: 按执行顺序排列的步骤名称列表
                          已注册但未列出的步骤按原顺序追加到末尾
        """
        # 校验所有名称已注册
        for name in new_order:
            if name not in self._steps:
                raise ValueError(f"步骤 '{name}' 未注册")
        # 未列出的步骤保持原序追加到末尾
        remaining = [n for n in self._step_order if name not in new_order]
        self._step_order = new_order + remaining

    def skip_steps(self, skip: list[str]) -> None:
        """设置跳过的步骤（配置驱动）"""
        self._skip_steps = set(skip)

    async def run(self, context: PipelineContext, callback: ProgressCallback | None = None) -> PipelineContext:
        """执行 Pipeline"""
        await self._fire_hook("before_convert", context)

        for i, step_name in enumerate(self._step_order):
            step = self._steps[step_name]
            if callback:
                callback.on_step_start(step_name, len(self._step_order), i + 1)
            context = await step.run(context)
            # 使用 _fire_hook 的返回值，允许 Hook 修改上下文
            context = await self._fire_hook("after_step", context, step_name=step_name)
            if callback:
                # 生成有意义的步骤完成摘要
                summary = self._make_step_summary(step_name, context)
                callback.on_step_complete(step_name, summary)

        await self._fire_hook("after_convert", context)
        return context

    async def run_chapters(self, chapter_indices: list[int], context: PipelineContext) -> PipelineContext:
        """增量转换：只处理指定章节"""
        # 过滤出指定章节，走完 Pipeline
        ...
```

### 4.2 Hook 机制

Pipeline 钩子是所有扩展的入口点：

```python
class Pipeline:
    def hook(self, event: str, callback: Callable):
        """注册钩子

        事件类型：
        - "before_convert":  转换开始前
        - "after_convert":   转换完成后
        - "after_step":      每个步骤完成后（参数含 step_name）
        - "on_error":        步骤出错时
        """
        self._hooks.setdefault(event, []).append(callback)

    async def _fire_hook(self, event: str, context: PipelineContext, **kwargs):
        for callback in self._hooks.get(event, []):
            await callback(context, **kwargs)
```

**Hook 使用场景**：

| 谁注册 | 注册什么 | 时机 |
|--------|---------|------|
| SkillManager | pre_processor / post_processor 执行 | before_convert / after_convert |
| UI 层 | 进度推送、日志记录 | after_step |
| 未来：审计模块 | 操作记录 | after_step |
| 未来：缓存模块 | 中间结果缓存 | after_step |

### 4.3 增量转换接口

```python
# V1: 基础增量接口
async def run_chapters(self, chapter_indices: list[int], context: PipelineContext) -> PipelineContext:
    """增量转换：只处理指定章节，合并到已有结果"""
    ...

# V2 扩展方向（不改接口，只加方法）：
# async def run_since(self, last_version: str, context: PipelineContext) -> PipelineContext:
#     """增量转换：只处理自 last_version 以来变更的章节"""
#     ...
```

### 4.4 扩展点总览

| 扩展方向 | 机制 | 示例 |
|---------|------|------|
| 新增步骤 | `register_step()` | 加"伏笔检测"步骤 |
| 步骤重排序 | `reorder_steps()` | 调整执行顺序 |
| 前后置处理 | Hook `before_convert` / `after_convert` | Skill 注入 |
| 步骤级监控 | Hook `after_step` | 日志、缓存、审计 |
| 增量转换 | `run_chapters()` | 只转换修改的章节 |
| 步骤跳过 | 配置 `skip_steps: ["emotion_tagger"]` | 不需要情绪标注时跳过 |

---

## 5. 编辑器架构

> 编辑器是 V1 的重点新模块，承载"人机协同"的核心交互。

### 5.1 设计目标

1. **左右分栏**：左小说原文、右 YAML 剧本，同屏对照
2. **滚动联动**：点击右侧 Beat → 左侧自动定位对应小说原文
3. **YAML 模式**：语法高亮 + Schema 校验提示
4. **小说模式**：章节折叠、书签导航
5. **Beat 内联编辑**：点击对白改内容、改情绪标签
6. **自动保存**：编辑内容实时保存到项目

### 5.2 前端架构

#### 技术栈

- **CodeMirror 6**（CDN 引入，模块化）
- **Alpine.js**（组件编排）
- **Tailwind CSS**（样式）

#### 编辑器结构

```
┌──────────────────────────────────────────────────────────────┐
│  工具栏：保存 | 格式化 | 跳转章节 | Beat 类型筛选             │
├──────────────────────────┬───────────────────────────────────┤
│                          │                                   │
│   小说原文编辑器          │   YAML 剧本编辑器                  │
│   (CodeMirror 6)         │   (CodeMirror 6)                  │
│                          │                                   │
│   ┌─ 第一章 ────────┐    │   ┌─ Scene 1 ───────────────┐    │
│   │  可折叠          │    │   │  Beat[d]: "你好" 😊     │    │
│   │  ...            │◀───┼───│  Beat[a]: 走进房间      │    │
│   │  ...            │    │   │  Beat[n]: 夜色渐深      │    │
│   └─────────────────┘    │   └─────────────────────────┘    │
│                          │                                   │
│   ┌─ 第二章 ────────┐    │   ┌─ Scene 2 ───────────────┐    │
│   │  ...            │    │   │  ...                     │    │
│   └─────────────────┘    │   └─────────────────────────┘    │
│                          │                                   │
├──────────────────────────┴───────────────────────────────────┤
│  状态栏：已保存 | 位置映射中 | Beat 数: 42                    │
└──────────────────────────────────────────────────────────────┘
```

#### CodeMirror 6 Extension 架构

CodeMirror 6 的核心设计理念是"一切皆 Extension"。我们利用这一点实现模块化扩展：

```javascript
// 编辑器初始化
import { EditorState } from "@codemirror/state"
import { EditorView } from "@codemirror/view"

// 小说编辑器
const novelState = EditorState.create({
  doc: novelText,
  extensions: [
    // 基础
    lineNumbers(),
    highlightActiveLine(),
    // 章节折叠
    novelChapterFolding(),           // ← 自定义 Extension
    // 滚动联动
    scrollSyncLink(yamlView),        // ← 自定义 Extension
    // 自动保存
    autoSave("/api/v1/projects/{id}/novel"),  // ← 自定义 Extension
    // 未来扩展：批注、AI 补全、diff 高亮
    // annotationExtension(),          // ← V2: 批注
    // aiCompletionExtension(),       // ← V2: AI 补全
  ]
})

// YAML 剧本编辑器
const yamlState = EditorState.create({
  doc: yamlText,
  extensions: [
    lineNumbers(),
    highlightActiveLine(),
    // YAML 语法高亮
    yamlSyntaxHighlight(),
    // Schema 校验提示
    schemaValidation(beatSchema),    // ← 自定义 Extension
    // Beat 内联编辑
    beatInlineEditor(),              // ← 自定义 Extension
    // 滚动联动
    scrollSyncLink(novelView),
    // 自动保存
    autoSave("/api/v1/projects/{id}/script"),
  ]
})
```

### 5.3 滚动联动

**映射机制**：Pipeline 转换时，每个 Beat 记录其在小说原文中的起止位置（`source_location`），形成映射表。

```yaml
# script.yaml 中每个 Beat 的 source_location
beats:
  - type: dialogue
    character: "李明"
    content: "你好"
    emotion: "友善"
    source_location: { chapter: 1, start: 42, end: 48 }  # ← 映射锚点
```

**联动流程**：

```
用户点击右侧 Beat
    │
    ▼
读取 Beat.source_location
    │
    ▼
左侧编辑器 scrollTo(source_location.start)
    │
    ▼
高亮左侧对应文本段
```

### 5.4 Beat 内联编辑

**组件化设计**：不同 Beat 类型有不同的编辑器组件，后续加新 Beat 类型只需注册新组件。

```javascript
// Beat 编辑器注册表
const beatEditorRegistry = {
  "dialogue": DialogueBeatEditor,   // 对白编辑器：改内容 + 情绪标签
  "action": ActionBeatEditor,       // 动作编辑器：改内容
  "narration": NarrationBeatEditor, // 旁白编辑器：改内容
  // 未来扩展：
  // "transition": TransitionBeatEditor,  // V2: 转场编辑器
  // "music": MusicBeatEditor,            // V2: 音乐提示编辑器
}

// 点击 Beat → 弹出对应编辑器
function onBeatClick(beat) {
  const editor = beatEditorRegistry[beat.type]
  if (editor) editor.open(beat)
}
```

**DialogueBeatEditor 示例**：

```
┌────────────────────────────────────┐
│  对白编辑                           │
│  ┌──────────────────────────────┐  │
│  │ 角色：[李明        ▼]        │  │
│  │ 内容：[你好，好久不见！    ]  │  │
│  │ 情绪：[😊 友善 ▼]           │  │
│  └──────────────────────────────┘  │
│            [取消]  [保存]          │
└────────────────────────────────────┘
```

### 5.5 编辑器事件总线

所有编辑操作通过全局事件总线广播，后续加撤销/重做/批注都订阅事件即可：

```javascript
// 全局事件总线
class EventBus {
  constructor() { this._listeners = {} }

  on(event, callback) {
    (this._listeners[event] ??= []).push(callback)
  }

  off(event, callback) {
    this._listeners[event] = this._listeners[event]?.filter(cb => cb !== callback) ?? []
  }

  emit(event, data) {
    for (const cb of this._listeners[event] ?? []) cb(data)
  }
}

const eventBus = new EventBus()

// 编辑操作 → 发射事件
function updateBeat(beatId, changes) {
  // 1. 更新本地状态
  applyChanges(beatId, changes)
  // 2. 广播事件
  eventBus.emit("beat:updated", { beatId, changes })
  // 3. 自动保存
  autoSaveScript()
}

// 未来：撤销管理器订阅事件
// eventBus.on("beat:updated", undoManager.record)

```

**编辑器事件类型**：

| 事件 | 数据 | 触发时机 |
|------|------|---------|
| `beat:updated` | `{beatId, changes}` | Beat 内容/属性变更 |
| `beat:created` | `{beat}` | 新增 Beat |
| `beat:deleted` | `{beatId}` | 删除 Beat |
| `novel:changed` | `{chapterId, range}` | 小说原文变更 |
| `script:changed` | `{range}` | YAML 剧本变更 |
| `cursor:positioned` | `{line, col, source}` | 光标位置变更（联动） |
| `save:completed` | `{projectId, fileType}` | 保存完成 |
| `save:failed` | `{projectId, error}` | 保存失败 |

### 5.6 后端 API

| 方法 | 路径 | 功能 |
|------|------|------|
| PUT | `/api/v1/projects/{id}/novel` | 保存小说原文 |
| PUT | `/api/v1/projects/{id}/script` | 保存剧本 YAML |
| POST | `/api/v1/projects/{id}/beat/{beat_id}` | 更新单个 Beat |

```python
# PUT /api/v1/projects/{id}/novel
class NovelUpdateRequest(BaseModel):
    content: str          # 完整小说原文

# PUT /api/v1/projects/{id}/script
class ScriptUpdateRequest(BaseModel):
    content: str          # 完整 YAML 内容

# POST /api/v1/projects/{id}/beat/{beat_id}
class BeatUpdateRequest(BaseModel):
    character: str | None = None
    content: str | None = None
    emotion: str | None = None
```

### 5.7 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 批注功能 | 新增 CodeMirror `annotationExtension` | 仅新增 Extension 文件 |
| AI 补全 | 新增 CodeMirror `aiCompletionExtension` | 仅新增 Extension 文件 |
| Diff 高亮 | 新增 CodeMirror `diffHighlightExtension` | 仅新增 Extension 文件 |
| 新 Beat 类型编辑器 | 在 `beatEditorRegistry` 注册新组件 | 仅新增组件文件 + 一行注册 |
| 撤销/重做 | 订阅 `beat:updated` 等事件，记录操作栈 | 仅新增模块 |
| 编辑器主题 | 新增 CodeMirror 主题 Extension | 仅新增主题文件 |

---

## 6. 项目管理架构

> 项目管理层是 V1 新增的核心模块，统一管理"小说 + 剧本 + 元信息"的生命周期。

### 6.1 ProjectStore 设计

`ProjectStore` 是统一的项目数据访问层，所有项目操作都通过它完成。

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ProjectStore(Protocol):
    """项目数据访问层协议"""

    # 项目生命周期
    async def create_project(self, title: str, novel_text: str = "") -> Project: ...
    async def get_project(self, project_id: str) -> Project: ...
    async def list_projects(self) -> list[ProjectMeta]: ...
    async def delete_project(self, project_id: str) -> None: ...

    # 内容读写
    async def get_novel(self, project_id: str) -> str: ...
    async def save_novel(self, project_id: str, content: str) -> None: ...
    async def get_script(self, project_id: str) -> str: ...
    async def save_script(self, project_id: str, content: str) -> None: ...

    # Beat 级操作
    async def update_beat(self, project_id: str, beat_id: str, changes: dict) -> None: ...

    # 元信息
    async def get_meta(self, project_id: str) -> ProjectMeta: ...
    async def update_meta(self, project_id: str, **kwargs) -> None: ...
```

**关键设计**：`ProjectStore` 是 `Protocol`（接口），不是具体实现。当前默认实现是 `FileSystemProjectStore`，后续换 SQLite 只需写新实现类，**业务逻辑零改动**。

### 6.2 项目目录结构

```
~/.novel2script/projects/<project_id>/
├── novel.txt                  # 小说原文
├── script.yaml               # YAML 剧本
├── meta.json                 # 项目元信息
└── config_snapshot.json      # 项目创建时的配置快照
```

### 6.3 meta.json 结构

```json
{
  "id": "proj_abc123",
  "title": "长夜余火",
  "created_at": "2026-06-05T10:30:00+08:00",
  "updated_at": "2026-06-05T14:20:00+08:00",
  "status": "converted",
  "novel_word_count": 125000,
  "script_beat_count": 342,
  "chapters": 12,
  "last_converted_at": "2026-06-05T14:20:00+08:00",
  "tags": ["科幻", "长篇"]
}
```

**status 枚举**：

| 值 | 含义 |
|----|------|
| `draft` | 已创建，未转换 |
| `converting` | 正在转换 |
| `converted` | 转换完成 |
| `editing` | 编辑中 |
| `error` | 转换失败 |

### 6.4 FileSystemProjectStore 实现

```python
class FileSystemProjectStore:
    """基于文件系统的 ProjectStore 实现"""

    PROJECTS_DIR = Path.home() / ".novel2script" / "projects"

    async def create_project(self, title: str, novel_text: str = "") -> Project:
        project_id = f"proj_{uuid4().hex}"  # 完整 hex，避免碰撞
        project_dir = self.PROJECTS_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # 写入小说原文
        (project_dir / "novel.txt").write_text(novel_text, encoding="utf-8")

        # 初始化空剧本
        (project_dir / "script.yaml").write_text("", encoding="utf-8")

        # 写入元信息
        meta = ProjectMeta(
            id=project_id, title=title,
            created_at=datetime.now(), updated_at=datetime.now(),
            status="draft", novel_word_count=len(novel_text),
        )
        (project_dir / "meta.json").write_text(
            meta.model_dump_json(indent=2), encoding="utf-8"
        )

        # 保存配置快照
        config = load_config()
        (project_dir / "config_snapshot.json").write_text(
            config.model_dump_json(indent=2), encoding="utf-8"
        )

        return Project(id=project_id, meta=meta, novel=novel_text, script="")

    async def save_novel(self, project_id: str, content: str) -> None:
        project_dir = self.PROJECTS_DIR / project_id
        (project_dir / "novel.txt").write_text(content, encoding="utf-8")
        # 更新元信息
        await self._update_meta_field(project_id,
            updated_at=datetime.now(),
            novel_word_count=len(content),
        )
```

### 6.5 项目管理 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/projects` | 项目列表 |
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 |
| PUT | `/api/v1/projects/{id}/novel` | 保存小说原文（自动保存） |
| PUT | `/api/v1/projects/{id}/script` | 保存剧本 YAML（自动保存） |
| POST | `/api/v1/projects/{id}/beat/{beat_id}` | 更新单个 Beat |

```python
# POST /api/v1/projects
class ProjectCreateRequest(BaseModel):
    title: str
    novel_text: str = ""

class ProjectCreateResponse(BaseModel):
    id: str
    title: str
    status: str

# GET /api/v1/projects
class ProjectListItem(BaseModel):
    id: str
    title: str
    status: str
    updated_at: datetime
    novel_word_count: int
    script_beat_count: int

# GET /api/v1/projects/{id}
class ProjectDetail(BaseModel):
    id: str
    meta: ProjectMeta
    novel: str          # 小说原文
    script: str         # YAML 剧本
```

### 6.6 自动保存机制

编辑器前端通过 `debounce` 实现自动保存，避免频繁请求：

```javascript
// 自动保存 Extension
function autoSave(apiUrl) {
  let saveTimer = null
  return EditorView.updateListener.of((update) => {
    if (!update.docChanged) return
    clearTimeout(saveTimer)
    saveTimer = setTimeout(async () => {
      const content = update.state.doc.toString()
      await fetch(apiUrl, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      })
      eventBus.emit("save:completed", { apiUrl })
    }, 2000) // 2秒防抖（与 PRD 一致）
  })
}
```

### 6.7 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 快照/版本历史 | 扩展 ProjectStore，加 `create_snapshot()` / `list_snapshots()` | 仅 ProjectStore 实现类 |
| SQLite 存储 | 新增 `SQLiteProjectStore` 实现 | 仅新增文件 + 配置切换 |
| 项目模板 | 扩展 `create_project()`，加 `template` 参数 | 仅 ProjectStore 实现类 |
| 项目导入/导出 | 加 `export_project()` / `import_project()` 方法 | 仅 ProjectStore 实现类 |

---

## 7. Skill 系统

### 7.1 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    SkillManager                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │ 发现     │  │ 加载     │  │ 执行                   │ │
│  │discover()│─▶│load()    │─▶│execute() / execute_   │ │
│  │          │  │          │  │  safe()                │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ SkillSource（可替换）                              │   │
│  │  BuiltinSkillSource  ← src/skills/               │   │
│  │  UserSkillSource     ← ~/.novel2script/skills/    │   │
│  │  未来：OnlineSkillSource ← 在线仓库               │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 生命周期钩子                                      │   │
│  │  before_run / after_run / on_error                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Skill 接口设计

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class SkillProtocol(Protocol):
    """Skill 协议"""
    async def run(self, data: dict, config: dict) -> dict: ...
```

**当前是同步签名（`async def run`），后续扩展**：

```python
# V2: 流式 Skill（支持进度回调）
class StreamingSkillProtocol(SkillProtocol, Protocol):
    async def run(self, data: dict, config: dict,
                  progress: ProgressCallback | None = None) -> dict: ...

# V2: 批量 Skill（支持批量输入）
class BatchSkillProtocol(SkillProtocol, Protocol):
    async def run_batch(self, data_list: list[dict], config: dict) -> list[dict]: ...
```

### 7.3 Skill 类型

| 类型 | 执行时机 | 输入 | 输出 | 示例 |
|------|---------|------|------|------|
| `pre_processor` | Pipeline 转换前 | 原始文本 | 处理后文本 | 文本清洗、格式化 |
| `post_processor` | Pipeline 转换后 | YAML 路径 | YAML 路径 | 对白润色、风格适配 |
| `exporter` | 用户主动触发 | YAML 路径 | 导出文件路径 | Fountain 导出 |
| `analyzer` | 用户主动触发 | YAML 路径 | 分析报告 | 角色分析、章节概要 |

### 7.4 Skill 目录结构

```
# 内置 Skill 目录
src/skills/
├── __init__.py
├── manager.py              # SkillManager
├── fountain_export/        # Fountain 导出
│   ├── skill.json
│   └── main.py
├── character_report/       # 角色分析
│   ├── skill.json
│   └── main.py
├── dialogue_polish/        # 对白润色
│   ├── skill.json
│   └── main.py
├── style_adapter/          # 风格适配
│   ├── skill.json
│   └── main.py
└── chapter_summary/        # 章节概要
    ├── skill.json
    └── main.py

# 用户 Skill 目录
~/.novel2script/skills/
└── my_custom_skill/
    ├── skill.json
    └── main.py
```

### 7.5 skill.json 格式

```json
{
    "name": "fountain_export",
    "display_name": "Fountain 导出",
    "description": "将 YAML 剧本导出为 Fountain 格式",
    "type": "exporter",
    "inputs": ["yaml_path"],
    "outputs": ["fountain_path"],
    "requires_llm": false
}
```

### 7.6 main.py 入口

```python
"""Skill: Fountain 导出"""

async def run(data: dict, config: dict) -> dict:
    """
    Skill 入口函数

    Args:
        data: 输入数据
            - yaml_path: YAML 剧本文件路径
        config: Skill 配置
            - llm_client: LLM 客户端（如 requires_llm=true）
            - output_dir: 输出目录

    Returns:
        dict: 输出数据
            - fountain_path: 导出的 Fountain 文件路径
    """
    yaml_path = data["yaml_path"]
    output_dir = config.get("output_dir", "./output")
    # ... 实现转换逻辑 ...
    return {"fountain_path": fountain_path}
```

### 7.7 5 个内置 Skill

| # | 名称 | 类型 | 需要 LLM | 功能 |
|---|------|------|---------|------|
| 1 | `fountain_export` | exporter | ❌ | YAML → Fountain 格式导出 |
| 2 | `character_report` | analyzer | ❌ | 角色分析 + 关系图谱生成 |
| 3 | `dialogue_polish` | post_processor | ✅ | 对白润色（修正翻译腔、增强语言个性） |
| 4 | `style_adapter` | post_processor | ✅ | 风格适配（电影/电视/话剧/动画） |
| 5 | `chapter_summary` | analyzer | ❌ | 章节概要生成 |

### 7.8 SkillManager 核心接口

```python
class SkillManager:
    """Skill 生命周期管理"""

    def __init__(self, config: AppConfig):
        self._config = config
        self._registry: dict[str, SkillMeta] = {}     # 已发现的 Skill
        self._loaded: dict[str, ModuleType] = {}       # 已加载的模块
        self._enabled: set[str] = set()                # 已启用的 Skill
        self._hooks: dict[str, list[Callable]] = {     # 生命周期钩子
            "before_run": [], "after_run": [], "on_error": [],
        }

    # 发现与加载
    def discover(self) -> list[SkillMeta]: ...
    def load(self, name: str) -> None: ...

    # 执行
    async def execute(self, name: str, data: dict, config: dict) -> dict: ...
    async def execute_safe(self, name: str, data: dict, config: dict) -> SkillResult: ...

    # 启用/禁用
    def enable(self, name: str) -> None: ...
    def disable(self, name: str) -> None: ...

    # 生命周期钩子
    def add_hook(self, event: str, callback: Callable) -> None: ...

    # 管理
    def list_skills(self) -> list[SkillMeta]: ...
    async def create_template(self, name: str) -> str: ...
    async def install(self, source_path: str) -> str: ...
    async def uninstall(self, name: str) -> None: ...
```

### 7.9 生命周期钩子

```python
# 注册钩子
skill_manager.add_hook("before_run", log_skill_start)
skill_manager.add_hook("after_run", log_skill_complete)
skill_manager.add_hook("on_error", log_skill_error)

# 未来扩展：
# skill_manager.add_hook("before_run", check_quota)       # V2: 配额检查
# skill_manager.add_hook("after_run", cache_result)       # V2: 结果缓存
# skill_manager.add_hook("after_run", bill_usage)         # V2: 用量计费
```

### 7.10 Skill API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/skills` | 列出所有 Skill（含启用状态） |
| POST | `/api/v1/skills/run` | 执行指定 Skill |
| POST | `/api/v1/skills/toggle` | 启用/禁用 Skill |
| POST | `/api/v1/skills/create` | 创建用户 Skill 模板 |
| POST | `/api/v1/skills/install` | 从路径安装 Skill |
| DELETE | `/api/v1/skills/{name}` | 卸载用户 Skill |
| GET | `/api/v1/skills/{name}/dir` | 获取 Skill 目录路径 |

### 7.11 Skill 与 Pipeline 集成

```
Pipeline 执行流程中 Skill 的注入点：

  1. 加载输入文件
  2. ──▶ 执行所有已启用的 pre_processor Skill    ← 输入：原始文本
  3. 文本分段
  4. 角色 → 场景 → 对白 → 情绪（Pipeline Steps）
  5. 分段合并
  6. YAML 生成 + 校验
  7. ──▶ 执行所有已启用的 post_processor Skill   ← 输入：YAML 路径
  8. ──▶ 执行所有已启用的 exporter Skill          ← 输入：YAML 路径（用户主动触发）
  9. ──▶ 执行所有已启用的 analyzer Skill          ← 输入：YAML 路径（用户主动触发）
  10. 返回结果
```

**Skill 错误隔离**：Skill 失败不影响核心 Pipeline 流程：

```python
async def execute_skill_safe(self, name: str, data: dict, config: dict) -> SkillResult:
    """安全执行 Skill，异常不会传播到调用者"""
    start = time.monotonic()
    try:
        result = await self.execute(name, data, config)
        return SkillResult(skill_name=name, success=True, data=result,
                           duration_seconds=time.monotonic() - start)
    except SkillDisabledError:
        return SkillResult(skill_name=name, success=False,
                           error="Skill 已禁用", duration_seconds=0)
    except SkillNotFoundError:
        return SkillResult(skill_name=name, success=False,
                           error="Skill 不存在", duration_seconds=0)
    except Exception as e:
        logger.error(f"Skill '{name}' 执行失败: {e}", exc_info=True)
        return SkillResult(skill_name=name, success=False,
                           error=str(e), duration_seconds=time.monotonic() - start)
```

### 7.12 动态加载机制

使用 `importlib.util.spec_from_file_location` 实现运行时动态加载，不需要重启应用：

```python
spec = importlib.util.spec_from_file_location(f"skill_{name}", main_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
run_fn = module.run  # 获取入口函数
```

**为什么不用 `importlib.import_module`？** Skill 的 main.py 不在 Python 包路径下，且文件名都是 main.py 会冲突。`spec_from_file_location` 可以指定任意文件路径和模块名，更灵活。

### 7.13 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 异步/流式 Skill | 扩展 `SkillProtocol` | 仅 Protocol + Manager |
| 在线安装 Skill | 新增 `OnlineSkillSource` | 仅新增文件 |
| 生命周期钩子 | `add_hook()` 注册 | 仅调用方 |
| Skill 间依赖 | skill.json 加 `depends_on` 字段 | 仅 Manager 加载逻辑 |
| Skill 沙箱执行 | 在 `execute_safe` 中加隔离层 | 仅 Manager 执行逻辑 |
| Skill 计费 | `after_run` 钩子记录用量 | 仅钩子回调 |

---

## 8. 配置管理

### 8.1 配置层级

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

### 8.2 配置模型

```python
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="N2S_",
        json_file="~/.novel2script/config.json",
        json_file_encoding="utf-8",
    )

    # LLM 配置
    api_key: str = ""
    api_endpoint: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 4096

    # Pipeline 配置
    max_concurrent: int = 3
    segment_threshold: int = 6000    # 超过此字数触发分段
    enable_emotion_tag: bool = True

    # 项目管理
    projects_dir: str = "~/.novel2script/projects"

    # Skill 配置
    skills_dir: str = "~/.novel2script/skills"
    enabled_skills: list[str] = []   # 空列表 = 全部启用

    # 服务配置
    host: str = "127.0.0.1"
    port: int = 8765
```

### 8.3 配置 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/config` | 获取当前配置（api_key 脱敏） |
| PUT | `/api/v1/config` | 更新配置 |
| POST | `/api/v1/config/test` | 测试 API 连接是否可用 |

**安全考量**：GET 返回配置时，`api_key` 字段只显示末 4 位（如 `sk-****a1b2`），避免密钥泄露。PUT 更新时支持完整密钥写入。

### 8.4 扩展点

| 扩展方向 | 如何接入 | 改动范围 |
|---------|---------|---------|
| 新增配置项 | 在 `AppConfig` 中添加字段 | 仅 `config.py` |
| 新增配置源 | 继承 `AppConfig` 覆盖 `model_config` | 仅 `config.py` |
| 项目级配置 | 项目 `config_snapshot.json` 覆盖全局 | 仅 ProjectStore |
| 配置校验规则 | Pydantic `field_validator` | 仅 `config.py` |

---

## 9. 错误处理

### 9.1 错误分类

| 错误类型 | 示例 | 处理策略 |
|---------|------|---------|
| **LLM 输出格式错误** | JSON 解析失败、字段缺失 | 自动修复 → 降级重试 → 标记 `[PARSE_ERROR]` |
| **LLM API 错误** | 401 Key 无效、429 限速、500 服务端错误 | 429 限速退避重试；401/403 直接报错 |
| **网络错误** | 连接超时、DNS 解析失败 | 重试 3 次，指数退避 |
| **文件错误** | 文件不存在、编码不支持 | 前端校验 + 后端校验，提前报错 |
| **业务逻辑错误** | 角色引用不存在、场景覆盖不全 | 校验阶段标记警告，不中断流程 |
| **Skill 错误** | 加载失败、执行异常、输出格式不对 | 隔离 Skill 错误，不影响核心 Pipeline |
| **项目错误** | 项目不存在、ID 无效 | 404 响应 |
| **系统错误** | 内存不足、磁盘满 | 直接报错，记录日志 |

### 9.2 LLM 输出格式错误处理

```python
async def call_llm_with_retry(
    client: LLMClient,
    prompt: str,
    schema: type[BaseModel],
    max_retries: int = 3,
    progress_callback: ProgressCallback | None = None,
) -> BaseModel:
    for attempt in range(max_retries):
        try:
            raw = await client.chat(prompt)
            return schema.model_validate_json(raw)
        except (json.JSONDecodeError, ValidationError) as e:
            if progress_callback:
                await progress_callback.on_step_progress(
                    step="", detail=f"输出格式有误，正在重试 ({attempt+1}/{max_retries})", percent=0,
                )
            if attempt < max_retries - 1:
                prompt = f"{prompt}\n\n【注意】上次输出格式有误：{str(e)[:200]}，请严格按 JSON 格式输出。"
            else:
                raise LLMOutputError(f"重试 {max_retries} 次后仍无法解析")
```

### 9.3 任务级错误恢复

转换任务失败后，用户可以：

1. **查看错误详情**：前端展示失败步骤和错误原因
2. **重试**：从失败步骤重新开始（利用中间结果缓存）
3. **调整参数**：修改模型/温度等设置后重试
4. **取消**：放弃当前任务

---

## 10. 性能

### 10.1 处理速度估算

以 10 万字小说（约 10 章、50 场景）为例，使用 gpt-4o-mini：

| 模块 | 调用次数 | 串行总耗时 | 并行后总耗时 |
|------|---------|-----------|-------------|
| 文本预处理 + 分段 | 0 (本地) | < 1s | < 1s |
| 角色提取 | 10 + 1 | ~33s | ~33s |
| 场景分割 | 10 | ~40s | ~15s (并发=3) |
| 对白解析 | 50 | ~150s | ~30s (并发=5) |
| 情绪标注 | 50 | ~100s | ~20s (并发=5) |
| 合并 + YAML 生成 | 0 (本地) | < 2s | < 2s |
| Skill（对白润色） | 1 | ~15s | ~15s |
| **总计** | | **~340s** | **~115s** |

并行优化后约 2 分钟完成。

### 10.2 并行化策略

场景级并行（对白解析、情绪标注），使用 `asyncio.Semaphore` 控制并发数：

```python
async def process_segments_concurrently(
    segments: list[Segment],
    registry: CharacterRegistry,
    client: LLMClient,
    concurrency: int = 3,
) -> list[SegmentResult]:
    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(segment: Segment) -> SegmentResult:
        async with semaphore:
            scenes = await scene_splitter.split(segment, registry, client)
            dialogues = await dialogue_parser.parse(scenes, registry, client)
            emotions = await emotion_tagger.tag(dialogues, client)
            return SegmentResult(scenes=scenes, dialogues=dialogues, emotions=emotions)

    return await asyncio.gather(*[process_one(s) for s in segments])
```

### 10.3 内存使用

| 数据 | 大小估算 | 管理 |
|------|---------|------|
| 原始文本（10万字） | ~300KB | 常驻内存 |
| LLM 响应缓存 | 视缓存数量 | LRU 淘汰（最多 1000 条） |
| 中间结果 | ~2-5MB | 步骤完成后可释放 |
| FastAPI 应用 | ~50MB | 常驻 |
| PyWebView 窗口 | ~30-50MB | 常驻（桌面模式） |
| 已加载 Skill 模块 | ~1-5MB | 常驻 |

总内存 < 150MB（桌面模式），对 8GB 内存笔记本毫无压力。

### 10.4 大文件处理

限制上传文件大小为 10MB（约 300 万字），超过则拒绝。对于超长小说（50 万字以上），建议用户按卷/部拆分后分别处理。

---

## 11. 部署

### 11.1 安装方式

**pip 安装**（开发者/高级用户）：

```bash
pip install novel2script

# 桌面窗口模式（默认）
novel2script gui

# CLI 转换
novel2script convert input.txt -o output.yaml

# Web UI 模式
novel2script serve
```

**从源码安装**：

```bash
git clone https://github.com/xxx/novel-to-script.git
cd novel-to-script
pip install -e .
novel2script gui
```

**exe 安装**（普通用户）：

双击 `novel2script.exe` 即可启动桌面窗口模式。无需安装 Python。

### 11.2 启动入口统一

| 命令 | 功能 | 使用场景 |
|------|------|---------|
| `novel2script gui` | 桌面窗口模式（PyWebView） | 默认模式，双击 exe 等效 |
| `novel2script serve` | Web 服务器模式（浏览器访问） | 开发调试/远程访问 |
| `novel2script convert <file>` | CLI 转换模式 | 批处理/脚本集成 |
| `novel2script config` | 查看/修改配置 | 快速配置 |
| `novel2script skill run <name>` | CLI 运行 Skill | 命令行执行 Skill |
| `novel2script skill list` | CLI 列出 Skill | 查看可用 Skill |

### 11.3 桌面窗口模块

```python
# desktop/window.py
import threading
import webview
import uvicorn
import time

class DesktopApp:
    """PyWebView 桌面窗口应用"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.server_thread = None
        self.window = None

    def start(self):
        """启动桌面模式：后台线程运行 FastAPI，前台创建 PyWebView 窗口"""
        # 1. 后台线程启动 FastAPI
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        # 2. 等待服务就绪
        self._wait_for_server()

        # 3. 创建 PyWebView 窗口（主线程，阻塞）
        self.window = webview.create_window(
            title="Novel2Script - AI 小说转剧本",
            url=f"http://{self.host}:{self.port}",
            width=1280, height=800,
            min_size=(900, 600),
            resizable=True,
            text_select=True,
        )
        webview.start(debug=False)

    def _run_server(self):
        from novel2script.api.main import app
        uvicorn.run(app, host=self.host, port=self.port, log_level="warning")

    def _wait_for_server(self, timeout: float = 10.0):
        import urllib.request
        start = time.time()
        while time.time() - start < timeout:
            try:
                urllib.request.urlopen(f"http://{self.host}:{self.port}/", timeout=1)
                return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError(f"服务在 {timeout} 秒内未能启动")
```

**平台适配**：

| 平台 | 渲染引擎 | 备注 |
|------|---------|------|
| Windows | WebView2 (Edge Chromium) | Windows 10+ 内置 |
| macOS | WebKit (WKWebView) | 系统原生 |
| Linux | WebKitGTK | 需安装 `libwebkit2gtk-4.0-dev` |

### 11.4 CLI 模块

```python
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="AI 小说转剧本工具")
skill_app = typer.Typer(help="Skill 管理")
app.add_typer(skill_app, name="skill")

@app.command()
def convert(
    input_file: str = typer.Argument(help="输入文件路径"),
    output: str = typer.Option("output.yaml", help="输出文件路径"),
    model: str | None = typer.Option(None, help="覆盖默认模型"),
    no_emotion: bool = typer.Option(False, help="跳过情绪标注"),
): ...

@app.command()
def config(
    show: bool = typer.Option(False, help="显示当前配置"),
    set_key: str | None = typer.Option(None, help="设置 API Key"),
): ...

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8765),
    open_browser: bool = typer.Option(True),
): ...

@app.command()
def gui(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8765),
): ...

@skill_app.command("run")
def skill_run(name: str, input_file: str, output: str | None = None): ...

@skill_app.command("list")
def skill_list(): ...
```

### 11.5 PyInstaller 打包方案

#### 打包模式

| 模式 | 命令 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| 单文件 | `--onefile` | 一个 exe，分发简单 | 启动慢（需解压） | 临时使用 |
| 单目录 | `--onedir` | 启动快，无需解压 | 文件多 | 长期使用（推荐） |

#### spec 文件配置

```python
# novel2script.spec

a = Analysis(
    ['src/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/web/', 'novel2script/web/'),
        ('src/skills/', 'novel2script/skills/'),
        ('src/prompts/', 'novel2script/prompts/'),
    ],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        'webview', 'webview.platforms.winforms',
        'webview.platforms.cocoa', 'webview.platforms.gtk',
    ],
    hookspath=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PIL'],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='novel2script',
    debug=False,
    console=False,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True,
    name='novel2script',
)
```

#### 打包体积估算

| 组件 | 体积估算 |
|------|---------|
| Python 运行时 | ~15MB |
| FastAPI + uvicorn + 依赖 | ~10MB |
| openai SDK + 依赖 | ~5MB |
| Pydantic V2 | ~3MB |
| pywebview | ~5MB |
| 前端静态文件 + CodeMirror | ~1MB |
| 内置 Skill | ~0.1MB |
| 其他依赖 | ~10MB |
| **总计** | **~50-85MB** |

#### 打包注意事项

1. **hiddenimports**：uvicorn 和 pywebview 的子模块需显式声明
2. **datas**：前端静态文件和内置 Skill 需打包
3. **console=False**：桌面模式不显示控制台窗口
4. **UPX 压缩**：减小体积
5. **图标**：提供 .ico（Windows）和 .icns（macOS）

```python
# 打包后定位静态文件
import sys
from pathlib import Path

def get_web_dir() -> str:
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
        return str(base / "novel2script" / "web")
    else:
        from importlib.resources import files
        return str(files("novel2script.web"))
```

### 11.6 不做的事情

| 不做 | 原因 |
|------|------|
| Docker 镜像 | 本地工具，pip / exe 就够了 |
| 多用户/认证 | 纯个人端本地工具，单机单用户，无需认证 |
| 自动更新 | 增加复杂度和安全风险 |
| 云部署 | 本地工具，不提供 SaaS |

---

## 12. 扩展性设计专题

> 本章是架构的灵魂：**插件式扩展，核心不动**。
> 
> **详细规范见**：《扩展性设计详细规范.md》

### 12.1 五大扩展机制

#### 机制一：Hook 机制（Pipeline 钩子）

**问题**：如何让 Skill、UI、未来功能注入 Pipeline，而不改 Pipeline 代码？

**方案**：Pipeline 提供 Hook 注册接口，外部代码通过注册回调来扩展行为。

**详细实现**：
- **Hook 接口定义**：见《扩展性设计详细规范》2.1.1
- **Hook 事件类型**：见 2.1.2
- **Hook 注册机制**：见 2.1.3
- **Hook 执行顺序保证**：见 2.1.4
- **Hook 异常处理策略**：见 2.1.5
- **用户 Skill 零代码注册 Hook**：见 2.1.6

```python
# 注册 Hook
pipeline.hook("before_convert", my_preprocessor)
pipeline.hook("after_step", my_logger)
pipeline.hook("on_error", my_error_handler)

# Hook 执行
# Pipeline 内部：await self._fire_hook("before_convert", context)
```

**扩展场景**：

| 谁注册 | 注册什么 | 何时 |
|--------|---------|------|
| SkillManager | pre/post processor 执行 | before/after_convert |
| UI 层 | 进度推送、日志 | after_step |
| V2: 审计模块 | 操作记录 | after_step |
| V2: 缓存模块 | 中间结果缓存 | after_step |

#### 机制二：Step 插件（Pipeline 步骤可插拔）

**问题**：如何加新步骤而不改 Pipeline 代码？

**方案**：每个步骤实现 `StepProtocol`，通过 `register_step()` 注册。

**详细实现**：
- **Step 接口定义**：见《扩展性设计详细规范》2.2.1
- **Step 注册机制**：见 2.2.2
- **Step 执行顺序控制**：见 2.2.3
- **Step 依赖管理**：见 2.2.4
- **新增 Step 示例**：见 2.2.5

```python
# 定义新步骤
class ForeshadowDetector:
    @property
    def name(self) -> str: return "foreshadow_detector"

    async def run(self, context: PipelineContext) -> PipelineContext:
        # 检测伏笔逻辑
        ...
        return context

# 注册
pipeline.register_step("foreshadow_detector", ForeshadowDetector(), after="emotion_tagger")
```

**V2 扩展**：加"伏笔检测"、"节奏分析"等新步骤 = 写新 Step 类 + 一行注册。

#### 机制三：事件总线（前端编辑器）

**问题**：编辑器各组件如何解耦通信？

**方案**：全局 EventBus，编辑操作通过事件广播，各模块按需订阅。

**详细实现**：
- **Alpine.js 组件注册机制**：见《扩展性设计详细规范》4.1.1
- **路由注册机制**：见 4.1.2
- **组件通信规范**：见 4.1.3（强制通过 EventBus 通信）
- **组件生命周期钩子**：见 4.1.4

```javascript
// 发射事件
eventBus.emit("beat:updated", { beatId, changes })

// 订阅事件
eventBus.on("beat:updated", undoManager.record)    // V2: 撤销
eventBus.on("beat:updated", annotationManager.sync) // V2: 批注
```

**扩展场景**：

| 订阅者 | 订阅什么 | 版本 |
|--------|---------|------|
| 自动保存 | `beat:updated` / `novel:changed` | V1 |
| 撤销/重做管理器 | `beat:updated` / `beat:created` / `beat:deleted` | V2 |
| 批注同步 | `beat:updated` | V2 |
| AI 建议 | `novel:changed` | V2 |

#### 机制四：数据访问层隔离

**问题**：如何从文件系统平滑迁移到 SQLite，而不改业务逻辑？

**方案**：`ProjectStore` 是 Protocol（接口），不是具体实现。

**详细实现**：
- **ProjectStore 接口定义**：见《扩展性设计详细规范》3.1.1
- **FileSystemProjectStore 实现**：见 3.1.2
- **SQLiteProjectStore 实现**：见 3.1.3
- **数据模型版本兼容性设计**：见 3.1.4

```python
# 当前实现
store = FileSystemProjectStore()

# 未来切换
# store = SQLiteProjectStore("~/.novel2script/projects.db")

# 业务代码完全不变
project = await store.create_project("我的小说")
await store.save_novel(project.id, novel_text)
```

**切换成本**：写新实现类 + 配置文件指定实现类名。业务逻辑零改动。

#### 机制五：API 版本化

**问题**：如何在不兼容的 API 改动发生时，不破坏现有客户端？

**方案**：所有 API 在 `/api/v1/` 下，V2 新接口放 `/api/v2/`。

**详细实现**：
- **版本化路由注册**：见《扩展性设计详细规范》5.1.1
- **路由注册代码**：见 5.1.2
- **版本弃用策略**：见 5.1.3

```
/api/v1/convert/start     # V1: 启动转换
/api/v1/projects          # V1: 项目列表
/api/v2/convert/start     # V2: 支持增量转换参数
/api/v2/projects          # V2: 支持项目搜索/过滤
```

**规则**：
- 新增字段 → 在当前版本内添加（向后兼容）
- 删除/重命名字段 → 走新版本
- 老版本至少保留一个大版本周期

### 12.2 扩展性矩阵

| 模块 | 扩展机制 | 扩展示例 | 改动范围 |
|------|---------|---------|---------|
| Pipeline | Hook + Step 插件 | 新增"伏笔检测"步骤 | 仅新增文件 + 一行注册 |
| 编辑器 | CodeMirror Extension | AI 补全、批注、diff | 仅新增 Extension |
| 编辑器 | 事件总线 | 撤销、批注 | 仅新增订阅者 |
| 编辑器 | Beat 组件注册表 | 新 Beat 类型编辑器 | 仅新增组件 + 一行注册 |
| 项目管理 | ProjectStore Protocol | SQLite 存储 | 仅新增实现类 |
| Skill | SkillProtocol | 流式 Skill / 批量 Skill | 仅扩展 Protocol |
| Skill | SkillSource | 在线安装 | 仅新增 Source |
| Skill | 生命周期钩子 | 日志 / 计费 / 缓存 | 仅注册钩子 |
| API | 版本化路由 | V2 新接口 | 仅新增路由文件 |
| 配置 | pydantic-settings | 新配置源 | 仅扩展模型 |

### 12.3 "核心不动"保证

以下接口一旦发布即**冻结**，只能加不能改不能删：

| 冻结接口 | 位置 | 详细说明 |
|---------|------|---------|
| `StepProtocol` | `core/steps/base.py` | 见《扩展性设计详细规范》2.2.1 |
| `ProgressCallback` | `core/pipeline.py` | Pipeline 进度回调协议 |
| `ProjectStore` Protocol | `core/project_store.py` | 见《扩展性设计详细规范》3.1.1 |
| `SkillProtocol` | `skills/manager.py` | 见《扩展性设计详细规范》7.1 |
| `LLMClientProtocol` | `llm_client.py` | LLM 客户端协议 |
| `/api/v1/*` 所有端点 | `api/routes/v1/` | 见《扩展性设计详细规范》5.1 |
| `Beat` Tagged Union | `schema.py` | 见《扩展性设计详细规范》8.1 |
| `AppConfig` | `config.py` | 见《扩展性设计详细规范》6.1 |
| `PipelineContext` | `core/pipeline.py` | Pipeline 上下文 |

**兼容性保证**：
- 新增字段：✅ 允许（必须有默认值）
- 删除字段：❌ 禁止（走新版本）
- 修改语义：❌ 禁止
- 新增方法：✅ 允许

### 12.4 扩展性设计原则总结

1. **对扩展开放，对修改封闭**（OCP 原则）
2. **依赖抽象接口，不依赖具体实现**（DIP 原则）
3. **单一职责原则**（SRP 原则）
4. **接口隔离原则**（ISP 原则）
5. **配置优于硬编码**
6. **约定优于配置**（提供合理的默认值）
7. **向后兼容优于向前兼容**

> **详细规范**：请参考《扩展性设计详细规范.md》文档。

---

## 附录

### 附录 A：项目目录结构

```
novel-to-script/
├── README.md
├── docs/
│   ├── PRD.md
│   ├── architecture.md          # 本文档
│   ├── yaml-schema.md
│   └── prompt-design.md
├── src/
│   ├── __init__.py
│   ├── __main__.py              # 入口（双击 exe 默认启动 gui）
│   ├── core/                    # 核心转换逻辑（与 UI 无关）
│   │   ├── __init__.py
│   │   ├── pipeline.py          # 流水线编排 + Hook 机制
│   │   ├── steps/               # Pipeline 步骤（可插拔）
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # StepProtocol 定义
│   │   │   ├── character_extractor.py
│   │   │   ├── scene_splitter.py
│   │   │   ├── dialogue_parser.py
│   │   │   ├── emotion_tagger.py
│   │   │   └── yaml_generator.py
│   │   ├── text_segmenter.py
│   │   ├── merger.py
│   │   └── project_store.py     # ProjectStore Protocol + 默认实现
│   ├── schema.py                # Pydantic 数据模型（Tagged Union Beat）
│   ├── llm_client.py            # LLM 调用封装（LLMClientProtocol）
│   ├── config.py                # 配置管理（AppConfig）
│   ├── prompts/                 # Prompt 模板
│   │   ├── extract_characters.py
│   │   ├── merge_aliases.py
│   │   ├── split_scenes.py
│   │   ├── parse_dialogue.py
│   │   └── tag_emotions.py
│   ├── api/                     # FastAPI 后端
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── routes/
│   │   │   ├── v1/              # V1 版本路由
│   │   │   │   ├── __init__.py
│   │   │   │   ├── convert.py
│   │   │   │   ├── config.py
│   │   │   │   ├── files.py
│   │   │   │   ├── projects.py  # 项目管理 API
│   │   │   │   ├── editor.py    # 编辑器 API
│   │   │   │   └── skills.py
│   │   │   └── v2/              # V2 版本路由（未来）
│   │   │       └── __init__.py
│   │   └── sse.py
│   ├── skills/                  # Skill 系统
│   │   ├── __init__.py
│   │   ├── manager.py           # SkillManager
│   │   ├── fountain_export/
│   │   │   ├── skill.json
│   │   │   └── main.py
│   │   ├── character_report/
│   │   │   ├── skill.json
│   │   │   └── main.py
│   │   ├── dialogue_polish/
│   │   │   ├── skill.json
│   │   │   └── main.py
│   │   ├── style_adapter/
│   │   │   ├── skill.json
│   │   │   └── main.py
│   │   └── chapter_summary/
│   │       ├── skill.json
│   │       └── main.py
│   ├── desktop/                 # 桌面窗口模块
│   │   ├── __init__.py
│   │   └── window.py
│   ├── cli.py                   # CLI 入口（Typer）
│   └── web/                     # 前端静态文件
│       ├── index.html
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   ├── app.js
│       │   ├── api.js
│       │   ├── sse.js
│       │   ├── editor.js        # CodeMirror 6 编辑器初始化
│       │   ├── event-bus.js     # 编辑器事件总线
│       │   ├── beat-editors.js  # Beat 内联编辑器注册表
│       │   ├── scroll-sync.js   # 滚动联动
│       │   └── skills.js
│       └── components/
│           ├── file-upload.js
│           ├── progress.js
│           ├── settings.js
│           ├── project-list.js  # 项目列表组件
│           ├── project-editor.js # 项目编辑器组件
│           └── skill-panel.js
├── assets/
│   ├── icon.ico
│   └── icon.icns
├── examples/
│   ├── input/
│   └── output/
├── tests/
│   ├── test_pipeline.py
│   ├── test_segmenter.py
│   ├── test_merger.py
│   ├── test_project_store.py    # 项目管理测试
│   ├── test_editor_api.py       # 编辑器 API 测试
│   ├── test_skills.py
│   ├── test_api/
│   │   ├── test_convert.py
│   │   ├── test_config.py
│   │   ├── test_projects.py
│   │   └── test_skills.py
│   └── fixtures/
├── novel2script.spec            # PyInstaller 打包配置
├── requirements.txt
└── pyproject.toml
```

### 附录 B：API / CLI / SSE 速查表

#### API 端点（V1）

**项目管理**

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/projects` | 项目列表 |
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 |
| PUT | `/api/v1/projects/{id}/novel` | 保存小说原文（自动保存） |
| PUT | `/api/v1/projects/{id}/script` | 保存剧本 YAML（自动保存） |
| POST | `/api/v1/projects/{id}/beat/{beat_id}` | 更新单个 Beat |

**转换**

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/convert/start` | 启动转换 |
| GET | `/api/v1/convert/{task_id}/status` | 查询状态 |
| GET | `/api/v1/convert/{task_id}/events` | SSE 进度推送 |
| GET | `/api/v1/convert/{task_id}/result` | 下载结果 |
| POST | `/api/v1/convert/{task_id}/cancel` | 取消任务 |

**配置**

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/config` | 获取配置 |
| PUT | `/api/v1/config` | 更新配置 |
| POST | `/api/v1/config/test` | 测试连接 |

**文件**

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/files/upload` | 上传文件 |
| GET | `/api/v1/files/{file_id}` | 获取文件信息 |

**Skill**

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/skills` | 列出所有 Skill |
| POST | `/api/v1/skills/run` | 执行 Skill |
| POST | `/api/v1/skills/toggle` | 启用/禁用 Skill |
| POST | `/api/v1/skills/create` | 创建用户 Skill 模板 |
| POST | `/api/v1/skills/install` | 从路径安装 Skill |
| DELETE | `/api/v1/skills/{name}` | 卸载用户 Skill |
| GET | `/api/v1/skills/{name}/dir` | 获取 Skill 目录路径 |

#### CLI 命令

| 命令 | 功能 |
|------|------|
| `novel2script gui` | 启动桌面窗口模式（默认） |
| `novel2script serve` | 启动 Web UI（浏览器访问） |
| `novel2script convert <file>` | 转换小说为剧本 |
| `novel2script config` | 查看/修改配置 |
| `novel2script skill run <name>` | 运行指定 Skill |
| `novel2script skill list` | 列出所有 Skill |

#### SSE 事件类型

| 事件 | 触发时机 |
|------|---------|
| `step_start` | 步骤开始 |
| `step_progress` | 步骤内进度更新 |
| `step_complete` | 步骤完成 |
| `step_error` | 步骤出错 |
| `task_complete` | 任务完成 |
| `task_failed` | 任务失败 |
| `skill_start` | Skill 开始执行 |
| `skill_complete` | Skill 执行完成 |
| `skill_error` | Skill 执行出错 |
| `project_saved` | 项目保存成功 |

### 附录 C：扩展点总览表

| 模块 | 扩展点 | 扩展方向 | 接入方式 |
|------|--------|---------|---------|
| **启动层** | 入口分发 | 新增运行模式 | 注册新 CLI 子命令 |
| **启动层** | 回退机制 | 自定义回退链 | 添加 `except` 分支 |
| **API 层** | 版本化路由 | V2 新接口 | 创建 `routes/v2/` + 注册 |
| **API 层** | 路由扩展 | 新增 API 端点 | 在版本目录下新增路由文件 |
| **Pipeline** | Step 插件 | 新增转换步骤 | 实现 `StepProtocol` + `register_step()` |
| **Pipeline** | Hook 钩子 | 前后置处理、监控 | `pipeline.hook(event, callback)` |
| **Pipeline** | 增量接口 | 只转换指定章节 | `pipeline.run_chapters([2, 3])` |
| **Pipeline** | 步骤跳过 | 跳过不需要的步骤 | 配置 `skip_steps` |
| **LLM** | Client Protocol | 新 LLM 提供商 | 实现 `LLMClientProtocol` |
| **LLM** | 流式输出 | 流式响应 | 实现 `chat_stream()` |
| **Schema** | Beat Union | 新 Beat 类型 | 在 Union 中添加新模型 |
| **编辑器** | CM6 Extension | 批注/AI补全/diff | 新增 Extension 文件 |
| **编辑器** | 事件总线 | 撤销/批注 | 订阅编辑器事件 |
| **编辑器** | Beat 组件注册表 | 新 Beat 编辑器 | 注册新组件到 `beatEditorRegistry` |
| **编辑器** | 主题 | 自定义编辑器主题 | 新增 CM6 主题 Extension |
| **项目管理** | ProjectStore Protocol | SQLite 存储 | 新增实现类 + 配置切换 |
| **项目管理** | 快照 | 版本历史 | 扩展 ProjectStore 加 `create_snapshot()` |
| **Skill** | SkillProtocol | 流式/批量 Skill | 扩展 Protocol |
| **Skill** | SkillSource | 在线安装 | 新增 `OnlineSkillSource` |
| **Skill** | 生命周期钩子 | 日志/计费/缓存 | `add_hook()` 注册 |
| **Skill** | 依赖 | Skill 间依赖 | skill.json 加 `depends_on` |
| **配置** | 配置模型 | 新配置项/新配置源 | 扩展 `AppConfig` |
| **SSE** | 事件类型 | 新进度事件 | 添加新 event type |

---

> 本内容由 Coze AI 生成，请遵循相关法律法规及《人工智能生成合成内容标识办法》使用与传播。
