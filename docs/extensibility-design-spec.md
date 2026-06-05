# Novel2Script 扩展性设计详细规范

> 版本：V1.0 | 日期：2026-06-05 | 状态：设计规范阶段
>
> 核心目标：**后续功能开发尽可能不动源码**

---

## 目录

1. [概述](#1-概述)
2. [插件式架构设计](#2-插件式架构设计)
3. [数据层隔离设计](#3-数据层隔离设计)
4. [前端组件化设计](#4-前端组件化设计)
5. [API 版本化设计](#5-api-版本化设计)
6. [配置驱动设计](#6-配置驱动设计)
7. [Skill 系统扩展设计](#7-skill-系统扩展设计)
8. [编辑器扩展设计](#8-编辑器扩展设计)
9. [Pipeline 扩展设计](#9-pipeline-扩展设计)
10. [附录：扩展性检查清单](#10-附录扩展性检查清单)

---

## 1. 概述

### 1.1 设计原则

**核心思想**：**开放-封闭原则（OCP）** —— 对扩展开放，对修改封闭。

| 原则 | 说明 | 技术方案 |
|------|------|---------|
| **插件式架构** | 所有新功能通过插件接入，不修改核心代码 | Hook 机制 + Step 插件 + Skill 系统 |
| **数据层隔离** | 业务逻辑不直接操作数据，通过接口访问 | ProjectStore Protocol + 依赖注入 |
| **前端组件化** | 新功能 = 新组件 + 注册，不修改现有组件 | Alpine.js 组件 + EventBus + CodeMirror 6 Extension |
| **API 版本化** | 新版本 API 不影响旧版本客户端 | `/api/v1/` `/api/v2/` 路由分离 |
| **配置驱动** | 功能开关通过配置控制，不硬编码 | pydantic-settings + features 字段 |

### 1.2 技术栈与扩展性映射

| 技术 | 扩展性机制 | 不改源码的扩展方式 |
|------|---------|---------|
| **FastAPI** | Router 机制 + 依赖注入 | 新增 Router 文件，注册到 app（不改现有 Router） |
| **PyWebView** | 窗口壳隔离 | 替换窗口实现类，前端代码零改动 |
| **Alpine.js** | 组件注册 + 事件总线 | 新增 `Alpine.data('newComponent', ...)`（不改现有组件） |
| **CodeMirror 6** | Extension 系统 | 新增 Extension 文件，注册到 EditorState（不改现有 Extension） |
| **Pydantic V2** | Tagged Union + 模型继承 | 新增模型类到 Union（不改现有模型） |
| **Typer** | 子命令组 | 新增子命令函数，注册到 app（不改现有命令） |
| **PyInstaller** | hook 脚本 | 新增 hook 文件（不改 spec 文件） |
| **pydantic-settings** | 模型继承 | 新增配置字段到 AppConfig（不改现有配置） |

---

## 2. 插件式架构设计

### 2.1 Pipeline Hook 机制

**目标**：允许外部代码在 Pipeline 执行过程的关键节点注入自定义逻辑。

#### 2.1.1 Hook 接口定义

```python
# src/core/pipeline.py

from typing import Protocol, Callable, Any, runtime_checkable

@runtime_checkable
class PipelineHook(Protocol):
    """Pipeline Hook 协议
    
    所有 Hook 回调函数必须实现此协议
    """
    async def __call__(
        self, 
        context: "PipelineContext", 
        **kwargs: Any
    ) -> "PipelineContext | None":
        """Hook 回调函数
        
        Args:
            context: Pipeline 执行上下文
            **kwargs: 事件特定参数（如 step_name, error 等）
            
        Returns:
            - 返回 PipelineContext：修改后的上下文，继续执行后续 Hook
            - 返回 None：上下文未修改，继续执行后续 Hook
            - 抛出异常：终止 Pipeline 执行，进入错误处理流程
        """
        ...

# Hook 回调函数类型别名
HookCallback = Callable[["PipelineContext"], "PipelineContext | None"]
```

#### 2.1.2 Hook 事件类型

| 事件类型 | 触发时机 | 参数 | 用途 |
|---------|---------|------|------|
| `before_convert` | Pipeline 执行前 | 无 | Skill 执行、配置校验、资源初始化 |
| `after_convert` | Pipeline 执行后 | 无 | Skill 执行、结果后处理、资源清理 |
| `before_step` | 每个 Step 执行前 | `step_name: str` | 步骤跳过判断、参数修改 |
| `after_step` | 每个 Step 执行后 | `step_name: str, result: Any` | 结果缓存、日志记录、中间结果处理 |
| `on_error` | 任何步骤出错时 | `step_name: str, error: Exception` | 错误恢复、通知、日志记录 |

#### 2.1.3 Hook 注册机制

**方案**：通过 `Pipeline.hook()` 方法注册，支持多次注册，按注册顺序执行。

```python
# src/core/pipeline.py

class Pipeline:
    def __init__(self):
        self._steps: dict[str, "StepProtocol"] = {}
        self._step_order: list[str] = []
        self._hooks: dict[str, list[PipelineHook]] = {}
        
    def hook(self, event: str, callback: PipelineHook) -> None:
        """注册 Hook
        
        Args:
            event: 事件类型（见 2.1.2）
            callback: Hook 回调函数
            
        Example:
            >>> pipeline = Pipeline()
            >>> pipeline.hook("before_convert", my_preprocessor)
            >>> pipeline.hook("after_step", my_logger)
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
        
    async def _fire_hook(self, event: str, context: "PipelineContext", **kwargs: Any) -> "PipelineContext":
        """触发 Hook
        
        按顺序执行所有注册的 Hook，如果某个 Hook 返回新的 context，则后续 Hook 使用新的 context
        """
        current_context = context
        for callback in self._hooks.get(event, []):
            try:
                result = await callback(current_context, **kwargs)
                if result is not None:
                    current_context = result
            except Exception as e:
                # Hook 失败不终止 Pipeline，只记录日志
                logger.warning(f"Hook '{event}' 执行失败: {e}")
                
        return current_context
```

#### 2.1.4 Hook 执行顺序保证

**方案**：按注册顺序执行，先注册先执行。

**扩展**：如果后续需要优先级控制，可以在 `hook()` 方法中加 `priority: int` 参数。

```python
# V2 扩展：支持优先级
def hook(self, event: str, callback: PipelineHook, priority: int = 0) -> None:
    """注册 Hook（支持优先级）
    
    Args:
        event: 事件类型
        callback: Hook 回调函数
        priority: 优先级（数值越大越先执行，默认 0）
    """
    if event not in self._hooks:
        self._hooks[event] = []
    self._hooks[event].append((priority, callback))
    # 按优先级排序
    self._hooks[event].sort(key=lambda x: x[0], reverse=True)
```

#### 2.1.5 Hook 异常处理策略

| 场景 | 处理策略 | 配置项 |
|------|---------|---------|
| Hook 返回 None | 继续执行后续 Hook | - |
| Hook 返回新 context | 使用新 context 继续执行 | - |
| Hook 抛出非致命异常 | 记录警告日志，继续执行后续 Hook | - |
| Hook 抛出致命异常 | 终止 Pipeline，进入错误处理流程 | `hook_error_strategy: "abort" | "ignore"` |

```python
# 配置项
class AppConfig(BaseSettings):
    # ... 其他配置 ...
    
    # Hook 错误处理策略
    hook_error_strategy: Literal["abort", "ignore"] = "ignore"
```

#### 2.1.6 用户 Skill 如何零代码注册 Hook？

**方案**：通过 `skill.json` 声明 Hook 注册需求，SkillManager 自动注册。

```json
// skill.json 示例
{
  "name": "my-preprocessor",
  "type": "pre_processor",
  "version": "1.0.0",
  "description": "我的自定义预处理器",
  "author": "用户名",
  "hooks": [
    {
      "event": "before_convert",
      "function": "on_before_convert",
      "priority": 10
    },
    {
      "event": "after_step",
      "function": "on_after_step",
      "priority": 0
    }
  ]
}
```

**SkillManager 自动注册逻辑**：

```python
# src/skills/manager.py

class SkillManager:
    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline
        self._skills: dict[str, SkillMeta] = {}
        
    async def load(self, name: str) -> None:
        """加载 Skill 并自动注册 Hook"""
        skill = self._load_skill(name)
        
        # 检查 skill.json 中是否声明了 hooks
        if "hooks" in skill.meta:
            for hook_declaration in skill.meta["hooks"]:
                event = hook_declaration["event"]
                func_name = hook_declaration["function"]
                priority = hook_declaration.get("priority", 0)
                
                # 获取 Hook 函数
                hook_fn = getattr(skill.module, func_name, None)
                if hook_fn is None:
                    logger.warning(f"Skill '{name}' 声明的 Hook 函数 '{func_name}' 不存在")
                    continue
                    
                # 注册 Hook
                self._pipeline.hook(event, hook_fn, priority=priority)
                logger.info(f"Skill '{name}' 注册 Hook: {event} -> {func_name}")
```

**用户 Skill 代码示例**：

```python
# my-preprocessor/main.py

async def on_before_convert(context, **kwargs):
    """Hook 函数：在 Pipeline 执行前预处理文本"""
    # 示例：将文本中的全角标点转换为半角
    context.novel_text = context.novel_text.replace("，", ",").replace("。", ".")
    return context
    
async def on_after_step(context, **kwargs):
    """Hook 函数：在每个 Step 执行后记录日志"""
    step_name = kwargs.get("step_name")
    logger.info(f"Step '{step_name}' 执行完成")
    return context
```

---

### 2.2 Step 插件机制

**目标**：允许外部代码新增 Pipeline 步骤，无需修改 `pipeline.py`。

#### 2.2.1 Step 接口定义

```python
# src/core/steps/base.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class StepProtocol(Protocol):
    """Pipeline Step 协议
    
    所有 Pipeline 步骤必须实现此协议
    """
    
    @property
    def name(self) -> str:
        """步骤名称（唯一标识）"""
        ...
        
    async def run(self, context: "PipelineContext") -> "PipelineContext":
        """执行步骤
        
        Args:
            context: Pipeline 执行上下文
            
        Returns:
            修改后的上下文
            
        Raises:
            StepError: 步骤执行失败
        """
        ...
        
    async def validate(self, context: "PipelineContext") -> bool:
        """验证步骤输入是否合法
        
        可选实现，默认返回 True
        """
        return True
```

#### 2.2.2 Step 注册机制

**方案**：通过 `Pipeline.register_step()` 方法注册，支持指定插入位置。

```python
# src/core/pipeline.py

class Pipeline:
    def register_step(
        self, 
        name: str, 
        step: StepProtocol, 
        after: str | None = None
    ) -> None:
        """注册步骤
        
        Args:
            name: 步骤名称（唯一标识）
            step: 步骤实例
            after: 插入到哪个步骤之后（None 表示追加到末尾）
            
        Example:
            >>> pipeline = Pipeline()
            >>> pipeline.register_step("character_extractor", CharacterExtractor())
            >>> pipeline.register_step("foreshadow_detector", ForeshadowDetector(), after="emotion_tagger")
        """
        self._steps[name] = step
        
        if after is None:
            # 追加到末尾
            self._step_order.append(name)
        else:
            # 插入到指定步骤之后
            if after not in self._step_order:
                raise ValueError(f"步骤 '{after}' 不存在")
            idx = self._step_order.index(after)
            self._step_order.insert(idx + 1, name)
```

#### 2.2.3 Step 执行顺序控制

| 控制方式 | 实现方案 | 示例 |
|---------|---------|------|
| 指定插入位置 | `register_step(name, step, after="xxx")` | 插入到 "emotion_tagger" 之后 |
| 调整执行顺序 | `reorder_steps(["step1", "step2", ...])` | 完全自定义执行顺序 |
| 跳过指定步骤 | `skip_steps(["step1", "step2"])` | 配置驱动的跳过 |

```python
# 调整执行顺序
pipeline.reorder_steps([
    "character_extractor",
    "scene_splitter", 
    "dialogue_parser",
    "emotion_tagger",
    "foreshadow_detector",  # 新增的步骤
    "yaml_generator"
])

# 跳过指定步骤
pipeline.skip_steps(["emotion_tagger"])
```

#### 2.2.4 Step 依赖管理

**方案**：Step 可以声明依赖的其他 Step，Pipeline 执行前校验依赖是否满足。

```python
# src/core/steps/base.py

class StepProtocol(Protocol):
    """Pipeline Step 协议（扩展版）"""
    
    @property
    def name(self) -> str: ...
        
    @property
    def depends_on(self) -> list[str]:
        """依赖的其他 Step 名称"""
        return []
        
    async def run(self, context: "PipelineContext") -> "PipelineContext": ...
```

**Pipeline 依赖校验**：

```python
# src/core/pipeline.py

class Pipeline:
    def _validate_dependencies(self) -> None:
        """校验所有 Step 的依赖是否满足"""
        for name, step in self._steps.items():
            for dep in step.depends_on:
                if dep not in self._steps:
                    raise DependencyError(f"Step '{name}' 依赖的 Step '{dep}' 未注册")
                    
    async def run(self, context: "PipelineContext") -> "PipelineContext":
        """执行 Pipeline"""
        # 1. 校验依赖
        self._validate_dependencies()
        
        # 2. 执行步骤
        for step_name in self._step_order:
            step = self._steps[step_name]
            
            # 检查是否跳过
            if step_name in self._skip_steps:
                logger.info(f"跳过步骤: {step_name}")
                continue
                
            # 执行步骤
            context = await step.run(context)
            
        return context
```

#### 2.2.5 新增 Step 示例

**场景**：V2 需要新增"伏笔检测"步骤。

**无需修改源码**，只需：

1. 创建新 Step 类：

```python
# src/core/steps/foreshadow_detector.py

from src.core.steps.base import StepProtocol

class ForeshadowDetector:
    """伏笔检测 Step"""
    
    @property
    def name(self) -> str:
        return "foreshadow_detector"
        
    @property
    def depends_on(self) -> list[str]:
        # 依赖 emotion_tagger 的输出
        return ["emotion_tagger"]
        
    async def run(self, context: PipelineContext) -> PipelineContext:
        """检测伏笔"""
        # 实现逻辑...
        return context
```

2. 注册 Step：

```python
# 在 Skill 的 main.py 中注册
from src.core.pipeline import Pipeline
from src.core.steps.foreshadow_detector import ForeshadowDetector

async def on_load(pipeline: Pipeline):
    """Skill 加载时注册 Step"""
    pipeline.register_step(
        "foreshadow_detector", 
        ForeshadowDetector(),
        after="emotion_tagger"
    )
```

---

## 3. 数据层隔离设计

### 3.1 ProjectStore 接口定义

**目标**：业务逻辑不直接操作文件系统，通过 `ProjectStore` 接口访问数据。

#### 3.1.1 ProjectStore Protocol

```python
# src/core/project_store.py

from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class ProjectStore(Protocol):
    """项目数据访问层协议
    
    所有项目数据操作必须通过此接口，不直接操作文件系统
    """
    
    # ========== 项目生命周期 ==========
    
    async def create_project(
        self, 
        title: str, 
        novel_text: str = "",
        config: dict | None = None
    ) -> Project:
        """创建新项目
        
        Args:
            title: 项目标题
            novel_text: 小说原文（可选）
            config: 项目配置（可选）
            
        Returns:
            创建的项目对象
        """
        ...
        
    async def get_project(self, project_id: str) -> Project:
        """获取项目详情
        
        Raises:
            ProjectNotFoundError: 项目不存在
        """
        ...
        
    async def list_projects(
        self, 
        search: str | None = None,
        sort_by: str = "updated_at",
        order: Literal["asc", "desc"] = "desc"
    ) -> list[ProjectMeta]:
        """列出所有项目（支持搜索和排序）"""
        ...
        
    async def update_project(
        self, 
        project_id: str, 
        updates: dict[str, Any]
    ) -> Project:
        """更新项目元信息
        
        Args:
            updates: 要更新的字段（如 title, status 等）
        """
        ...
        
    async def delete_project(self, project_id: str) -> bool:
        """删除项目（软删除，移到回收站）"""
        ...
        
    # ========== 内容读写 ==========
    
    async def get_novel(self, project_id: str) -> str:
        """获取项目的小说原文"""
        ...
        
    async def save_novel(self, project_id: str, content: str) -> None:
        """保存项目的小说原文"""
        ...
        
    async def get_script(self, project_id: str) -> str:
        """获取项目的 YAML 剧本"""
        ...
        
    async def save_script(self, project_id: str, content: str) -> None:
        """保存项目的 YAML 剧本"""
        ...
        
    # ========== Beat 级操作 ==========
    
    async def update_beat(
        self, 
        project_id: str, 
        beat_id: str, 
        changes: dict[str, Any]
    ) -> None:
        """更新单个 Beat"""
        ...
        
    # ========== 元信息 ==========
    
    async def get_meta(self, project_id: str) -> ProjectMeta:
        """获取项目元信息"""
        ...
        
    async def update_meta(self, project_id: str, **kwargs: Any) -> None:
        """更新项目元信息"""
        ...
```

#### 3.1.2 FileSystemProjectStore 实现（V1 默认）

```python
# src/core/project_store.py

class FileSystemProjectStore:
    """基于文件系统的 ProjectStore 实现"""
    
    PROJECTS_DIR = Path.home() / ".novel2script" / "projects"
    
    async def create_project(
        self, 
        title: str, 
        novel_text: str = "",
        config: dict | None = None
    ) -> Project:
        project_id = f"proj_{uuid4().hex}"  # 完整 hex，避免碰撞
        project_dir = self.PROJECTS_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入小说原文
        (project_dir / "novel.txt").write_text(novel_text, encoding="utf-8")
        
        # 初始化空剧本
        (project_dir / "script.yaml").write_text("", encoding="utf-8")
        
        # 写入元信息
        meta = ProjectMeta(
            id=project_id, 
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="draft",
            novel_word_count=len(novel_text),
        )
        (project_dir / "meta.json").write_text(
            meta.model_dump_json(indent=2), 
            encoding="utf-8"
        )
        
        # 保存配置快照
        config_snapshot = config or load_config().model_dump()
        (project_dir / "config_snapshot.json").write_text(
            json.dumps(config_snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        return Project(id=project_id, meta=meta, novel=novel_text, script="")
```

#### 3.1.3 SQLiteProjectStore 实现（V2 扩展）

**无需修改业务代码**，只需：

1. 新增 `SQLiteProjectStore` 类：

```python
# src/core/project_store_sqlite.py

class SQLiteProjectStore:
    """基于 SQLite 的 ProjectStore 实现"""
    
    def __init__(self, db_path: str = "~/.novel2script/projects.db"):
        self._db_path = Path(db_path).expanduser()
        self._init_db()
        
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self._db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                novel_word_count INTEGER DEFAULT 0,
                script_beat_count INTEGER DEFAULT 0,
                config_snapshot TEXT
            );
            
            CREATE TABLE IF NOT EXISTS project_content (
                project_id TEXT NOT NULL,
                type TEXT NOT NULL,  -- 'novel' or 'script'
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (project_id, type),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
        """)
        conn.commit()
        conn.close()
        
    async def create_project(
        self, 
        title: str, 
        novel_text: str = "",
        config: dict | None = None
    ) -> Project:
        # 实现逻辑...
        pass
        
    # ... 其他接口实现 ...
```

2. 在配置中切换实现：

```python
# config.json
{
  "project_store_type": "sqlite",  # 'filesystem' 或 'sqlite'
  "project_store_sqlite_path": "~/.novel2script/projects.db"
}
```

```python
# src/core/project_store_factory.py

def create_project_store(config: AppConfig) -> ProjectStore:
    """根据配置创建 ProjectStore 实例"""
    if config.project_store_type == "sqlite":
        return SQLiteProjectStore(config.project_store_sqlite_path)
    else:
        return FileSystemProjectStore()
```

#### 3.1.4 数据模型版本兼容性设计

**问题**：V2 给 `Project` 模型加了 `snapshots` 字段，V1 的代码读取 V2 的数据会出错吗？

**方案**：
1. **新增字段用 `Optional` + 默认值**
2. **V1 代码忽略不认识的字段**
3. **数据迁移脚本**（可选）

```python
# V1 Project 模型
class Project(BaseModel):
    id: str
    title: str
    status: Literal["empty", "converting", "editing", "completed"]
    created_at: datetime
    updated_at: datetime
    novel_file: str
    script_file: str
    config_snapshot: dict
    edit_meta: EditMeta
    
# V2 扩展（向后兼容）
class ProjectV2(Project):
    snapshots: list[SnapshotMeta] | None = None  # 可选字段，V1 代码忽略
    annotations: list[Annotation] | None = None  # 可选字段，V1 代码忽略
```

**读取 V2 数据时，V1 代码的行为**：
- Pydantic V2 默认忽略未知字段（`extra='ignore'`）
- 新增的字段不会被解析，但不影响已有字段

---

## 4. 前端组件化设计

### 4.1 Alpine.js 组件注册机制

**目标**：新功能 = 新组件 + 注册，不修改现有组件。

#### 4.1.1 组件注册接口

```javascript
// src/web/js/app.js

// 全局组件注册表
const componentRegistry = {};

function registerComponent(name, factory) {
    """注册 Alpine.js 组件
    
    Args:
        name: 组件名称
        factory: 组件工厂函数（返回 Alpine.js 组件定义）
    """
    componentRegistry[name] = factory;
    Alpine.data(name, factory);
}

// 使用示例：注册新组件
registerComponent('myNewFeature', () => ({
    // Alpine.js 组件定义
    init() {
        // 组件初始化
    },
    // ... 其他属性和方法 ...
}));
```

#### 4.1.2 路由注册机制

**方案**：路由表配置化，新增页面只需加配置。

```javascript
// src/web/js/app.js

// 路由表
const routes = {
    '/': 'projectList',
    '/editor/:projectId': 'projectEditor',
    '/settings': 'settings',
    // V2 扩展：新增路由无需修改现有代码
    '/snapshots/:projectId': 'snapshotList',
};

// 路由注册函数
function registerRoute(path, componentName) {
    """注册新路由
    
    Args:
        path: URL 路径（支持参数，如 '/snapshots/:projectId'）
        componentName: 组件名称
    """
    routes[path] = componentName;
}

// 路由匹配和渲染
function renderRoute() {
    const path = window.location.pathname;
    
    // 匹配路由
    for (const [routePath, componentName] of Object.entries(routes)) {
        if (matchRoute(path, routePath)) {
            // 渲染组件
            renderComponent(componentName);
            return;
        }
    }
    
    // 404
    renderComponent('notFound');
}
```

#### 4.1.3 组件通信规范

**强制通过 EventBus 通信**，不允许直接引用其他组件。

```javascript
// src/web/js/event-bus.js

class EventBus {
    constructor() {
        this._listeners = {};
    }
    
    on(event, callback) {
        """订阅事件"""
        if (!this._listeners[event]) {
            this._listeners[event] = [];
        }
        this._listeners[event].push(callback);
    }
    
    off(event, callback) {
        """取消订阅"""
        if (this._listeners[event]) {
            this._listeners[event] = this._listeners[event].filter(cb => cb !== callback);
        }
    }
    
    emit(event, data) {
        """发布事件"""
        for (const callback of (this._listeners[event] || [])) {
            try {
                callback(data);
            } catch (e) {
                console.error(`EventBus: 事件 '${event}' 的回调函数执行失败:`, e);
            }
        }
    }
}

// 全局 EventBus 实例
const eventBus = new EventBus();
```

**组件通信示例**：

```javascript
// 组件 A：发布事件
registerComponent('componentA', () => ({
    init() {
        // 发布事件
        eventBus.emit('beat:updated', { beatId: 'beat_001', changes: {...} });
    }
}));

// 组件 B：订阅事件
registerComponent('componentB', () => ({
    init() {
        // 订阅事件
        eventBus.on('beat:updated', (data) => {
            console.log('收到 beat:updated 事件:', data);
            // 处理事件...
        });
    }
}));
```

#### 4.1.4 组件生命周期钩子

```javascript
// Alpine.js 组件生命周期钩子
registerComponent('myComponent', () => ({
    // 组件初始化（类似 mounted）
    init() {
        console.log('组件初始化');
    },
    
    // 组件销毁（类似 beforeUnmount）
    destroy() {
        console.log('组件销毁');
        // 清理事件监听器
        eventBus.off('beat:updated', this.onBeatUpdated);
    },
    
    // 自定义方法
    onBeatUpdated(data) {
        // 处理事件...
    }
}));
```

---

## 5. API 版本化设计

### 5.1 版本化路由注册

**目标**：V2 新接口不影响 V1 客户端。

#### 5.1.1 路由目录结构

```
src/api/routes/
├── v1/              # V1 版本路由
│   ├── __init__.py
│   ├── convert.py
│   ├── config.py
│   ├── projects.py
│   ├── editor.py
│   └── skills.py
└── v2/              # V2 版本路由（未来）
    ├── __init__.py
    ├── convert.py    # V2 新增增量转换接口
    ├── projects.py   # V2 新增快照接口
    └── ...
```

#### 5.1.2 路由注册代码

```python
# src/api/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    yield
    
app = FastAPI(title="Novel2Script", lifespan=lifespan)

# V1 版本路由
from src.api.routes.v1 import (
    convert_router,
    config_router,
    projects_router,
    editor_router,
    skills_router,
)

app.include_router(convert_router, prefix="/api/v1/convert", tags=["v1-convert"])
app.include_router(config_router, prefix="/api/v1/config", tags=["v1-config"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["v1-projects"])
app.include_router(editor_router, prefix="/api/v1/editor", tags=["v1-editor"])
app.include_router(skills_router, prefix="/api/v1/skills", tags=["v1-skills"])

# V2 版本路由（未来扩展）
# from src.api.routes.v2 import ...
# app.include_router(v2_convert_router, prefix="/api/v2/convert", tags=["v2-convert"])
```

#### 5.1.3 版本弃用策略

| 规则 | 说明 |
|------|------|
| **新增字段** | 允许（必须有默认值），V1 客户端忽略不认识的字段 |
| **删除字段** | 禁止（走新版本） |
| **修改语义** | 禁止（走新版本） |
| **新增端点** | 走新版本（如 `/api/v2/...`） |
| **老版本保留周期** | 至少保留 2 个版本（如 V3 发布后，V1 仍可继续使用） |

---

## 6. 配置驱动设计

### 6.1 功能开关配置

**目标**：新功能通过配置开关控制，不硬编码。

#### 6.1.1 配置模型

```python
# src/config.py

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="N2S_",
        json_file="~/.novel2script/config.json",
        json_file_encoding="utf-8",
    )
    
    # ========== LLM 配置 ==========
    api_key: str = ""
    api_endpoint: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 4096
    
    # ========== Pipeline 配置 ==========
    max_concurrent: int = 3
    segment_threshold: int = 6000
    enable_emotion_tag: bool = True
    
    # ========== 功能开关 ==========
    features: dict[str, bool] = Field(default_factory=lambda: {
        "emotion_tag": True,           # V1: 情绪标注
        "version_snapshot": False,     # V2: 版本快照
        "incremental_convert": False,  # V2: 增量转换
        "annotation": False,           # V2: 批注
        "ai_rewrite": False,           # V3: AI 改写
        "character_consistency": False  # V3: 角色一致性
    })
    
    # ========== 项目管理 ==========
    projects_dir: str = "~/.novel2script/projects"
    
    # ========== Skill 配置 ==========
    skills_dir: str = "~/.novel2script/skills"
    enabled_skills: list[str] = Field(default_factory=list)
    
    # ========== 服务配置 ==========
    host: str = "127.0.0.1"
    port: int = 8765
```

#### 6.1.2 功能开关使用

**后端使用**：

```python
# src/core/pipeline.py

class Pipeline:
    async def run(self, context: PipelineContext) -> PipelineContext:
        config = context.config
        
        # 检查功能开关
        if config.features.get("emotion_tag", True):
            # 执行情绪标注
            context = await self._steps["emotion_tagger"].run(context)
        else:
            logger.info("情绪标注功能已禁用，跳过")
            
        return context
```

**前端使用**：

```javascript
// 前端根据功能开关显示/隐藏 UI 元素
registerComponent('featureAwareComponent', () => ({
    init() {
        // 从 API 获取配置
        this.loadConfig();
    },
    
    async loadConfig() {
        const response = await fetch('/api/v1/config');
        const config = await response.json();
        this.features = config.features;
    },
    
    // 根据功能开关显示/隐藏
    showAiRewrite() {
        return this.features?.ai_rewrite ?? false;
    }
}));
```

#### 6.1.3 功能依赖管理

**方案**：在 `features` 配置中声明依赖关系。

```json
// config.json
{
  "features": {
    "emotion_tag": true,
    "version_snapshot": false,
    "ai_rewrite": false,
    "character_consistency": false
  },
  "feature_dependencies": {
    "ai_rewrite": {
      "depends_on": ["version_snapshot"],
      "message": "AI 改写功能依赖版本快照功能，请先启用版本快照"
    },
    "character_consistency": {
      "depends_on": ["ai_rewrite"],
      "message": "角色一致性检查依赖 AI 改写功能"
    }
  }
}
```

**依赖校验逻辑**：

```python
# src/config.py

def validate_feature_dependencies(config: AppConfig) -> list[str]:
    """校验功能依赖关系
    
    Returns:
        错误信息列表（为空表示校验通过）
    """
    errors = []
    dependencies = config.feature_dependencies
    
    for feature, dep_info in dependencies.items():
        if not getattr(config.features, feature, False):
            continue  # 功能未启用，无需校验
            
        # 检查依赖的功能是否启用
        for dep_feature in dep_info["depends_on"]:
            if not getattr(config.features, dep_feature, False):
                errors.append(dep_info["message"])
                
    return errors
```

---

## 7. Skill 系统扩展设计

### 7.1 Skill 依赖管理

**目标**：Skill 可以声明依赖的其他 Skill，SkillManager 自动处理执行顺序。

#### 7.1.1 skill.json 依赖声明

```json
// skill.json 示例
{
  "name": "character-consistency-checker",
  "type": "analyzer",
  "version": "1.0.0",
  "description": "角色一致性检查",
  "author": "用户名",
  "dependencies": [
    {
      "name": "character-analysis",
      "version": ">=1.0.0"
    }
  ]
}
```

#### 7.1.2 SkillManager 依赖解析

```python
# src/skills/manager.py

class SkillManager:    async def execute(self, name: str, data: dict, config: dict) -> dict:
        """执行单个 Skill，根据 requires_llm 决定是否传递 llm_client"""
        meta = self._registry.get(name)
        if not meta:
            raise SkillNotFoundError(f"Skill '{name}' 未找到")

        # 处理 requires_llm 字段
        requires_llm = meta.get("requires_llm", True)
        if not requires_llm:
            # 不需要 LLM 的 Skill，从 config 中移除 llm_client
            config = {k: v for k, v in config.items() if k != "llm_client"}

        # 加载并调用 Skill
        module = self._load_module(name)
        return await module.run(data, config)

    async def execute_safe(self, name: str, data: dict, config: dict) -> SkillResult:
        """安全执行 Skill，异常不会传播到调用者"""
        start = time.monotonic()
        try:
            result = await self.execute(name, data, config)
            return SkillResult(
                skill_name=name, success=True, data=result,
                duration_seconds=time.monotonic() - start
            )
        except Exception as e:
            logger.error(f"Skill '{name}' 执行失败: {e}", exc_info=True)
            return SkillResult(
                skill_name=name, success=False,
                error=str(e), duration_seconds=time.monotonic() - start
            )


    async def resolve_dependencies(self, skill_name: str) -> list[str]:
        """解析 Skill 依赖，返回执行顺序
        
        Returns:
            按执行顺序排列的 Skill 名称列表
        """
        visited = set()
        order = []
        
        async def dfs(name):
            if name in visited:
                return
            visited.add(name)
            
            # 获取 Skill 元数据
            meta = self._registry.get(name)
            if not meta:
                raise SkillNotFoundError(f"Skill '{name}' 未找到")
                
            # 递归解析依赖
            for dep in meta.get("dependencies", []):
                dep_name = dep["name"]
                await dfs(dep_name)
                
            order.append(name)
            
        await dfs(skill_name)
        return order
        
    async def execute_with_dependencies(self, name: str, data: dict, config: dict) -> dict:
        """执行 Skill 及其依赖"""
        execution_order = await self.resolve_dependencies(name)
        
        results = {}
        for skill_name in execution_order:
            logger.info(f"执行 Skill: {skill_name}")
            result = await self.execute(skill_name, data, config)
            results[skill_name] = result
            
            # 将依赖的结果传递给下一个 Skill
            data = {**data, "dependencies": results}
            
        return results[name]  # 返回原始 Skill 的结果
```

### 7.2 Skill 配置管理

**目标**：每个 Skill 可以有自己的配置，不影响全局配置。

#### 7.2.1 Skill 配置存储

**方案**：在 `~/.novel2script/skill_configs/` 目录下存储每个 Skill 的配置。

```
~/.novel2script/
├── config.json              # 全局配置
├── skill_configs/          # Skill 配置目录
│   ├── character-analysis.json
│   ├── dialogue-polish.json
│   └── my-custom-skill.json
├── projects/
└── skills/
```

#### 7.2.2 Skill 配置读取

```python
# src/skills/manager.py

class SkillManager:
    SKILL_CONFIG_DIR = Path.home() / ".novel2script" / "skill_configs"
    
    async def get_skill_config(self, skill_name: str) -> dict:
        """获取 Skill 配置"""
        config_path = self.SKILL_CONFIG_DIR / f"{skill_name}.json"
        
        if not config_path.exists():
            return {}
            
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    async def save_skill_config(self, skill_name: str, config: dict) -> None:
        """保存 Skill 配置"""
        self.SKILL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_path = self.SKILL_CONFIG_DIR / f"{skill_name}.json"
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
```

#### 7.2.3 Skill 运行时配置传递

```python
# Skill 的 main.py 可以读取配置
async def run(data: dict, config: dict) -> dict:
    """Skill 入口函数
    
    Args:
        data: 输入数据
        config: Skill 配置（由 SkillManager 自动传递）
    """
    # 读取配置
    style = config.get("style", "realistic")
    
    # 实现逻辑...
    return {"result": "..."}
```

### 7.3 Skill 沙箱隔离

**目标**：用户 Skill 运行在沙箱中，异常不影响主程序。

#### 7.3.1 沙箱实现方案

**方案**：使用 `subprocess` + `resource limits` 实现进程级隔离。

```python
# src/skills/sandbox.py

import subprocess
import resource
import json

class SkillSandbox:
    """Skill 沙箱"""
    
    @staticmethod
    async def run_in_sandbox(
        skill_path: str, 
        data: dict, 
        config: dict,
        timeout: int = 30
    ) -> dict:
        """在沙箱中运行 Skill
        
        Args:
            skill_path: Skill 的 main.py 路径
            data: 输入数据
            config: Skill 配置
            timeout: 超时时间（秒）
            
        Returns:
            Skill 执行结果
        """
        # 准备输入数据
        input_data = {
            "data": data,
            "config": config
        }
        
        # 启动子进程
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            skill_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # 设置资源限制（在子进程中）
        def set_resource_limits():
            # 限制内存使用（100MB）
            resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, -1))
            # 限制 CPU 时间（30 秒）
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, -1))
            
        process.pre_exec = set_resource_limits
        
        # 传递输入数据
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=json.dumps(input_data).encode("utf-8")),
            timeout=timeout
        )
        
        if process.returncode != 0:
            raise SkillExecutionError(f"Skill 执行失败: {stderr.decode('utf-8')}")
            
        # 解析输出结果
        result = json.loads(stdout.decode("utf-8"))
        return result
```

#### 7.3.2 Skill 主入口适配

**用户 Skill 的 main.py 需要适配沙箱环境**：

```python
# my-skill/main.py

import json
import sys

async def run(data: dict, config: dict) -> dict:
    """Skill 入口函数"""
    # 实现逻辑...
    return {"result": "..."}

if __name__ == "__main__":
    # 沙箱模式：从 stdin 读取输入，向 stdout 输出结果
    input_data = json.loads(sys.stdin.read())
    data = input_data["data"]
    config = input_data["config"]
    
    result = await run(data, config)
    print(json.dumps(result))
```

---

## 8. 编辑器扩展设计

### 8.1 CodeMirror 6 Extension 注册机制

**目标**：新编辑器功能 = 新 Extension + 注册，不修改现有 Extension。

#### 8.1.1 Extension 注册接口

```javascript
// src/web/js/editor.js

// 全局 Extension 注册表
const extensionRegistry = {};

function registerExtension(name, factory) {
    """注册 CodeMirror 6 Extension
    
    Args:
        name: Extension 名称
        factory: Extension 工厂函数（返回 CodeMirror Extension）
    """
    extensionRegistry[name] = factory;
}

function getExtensions(enabledFeatures) {
    """根据启用的功能获取 Extension 列表"""
    const extensions = [
        lineNumbers(),
        highlightActiveLine(),
        // ... 基础 Extension ...
    ];
    
    // 根据功能开关动态加载 Extension
    if (enabledFeatures.annotation) {
        extensions.push(extensionRegistry["annotation"]());
    }
    
    if (enabledFeatures.diffHighlight) {
        extensions.push(extensionRegistry["diffHighlight"]());
    }
    
    return extensions;
}

// 使用示例：注册新 Extension
registerExtension('annotation', () => {
    // 返回 CodeMirror Extension
    return annotationExtension({
        // 配置...
    });
});
```

#### 8.1.2 新增 Extension 示例

**场景**：V2 需要新增"批注"功能。

**无需修改源码**，只需：

1. 创建新 Extension 文件：

```javascript
// src/web/js/extensions/annotation-extension.js

export function annotationExtension(options) {
    """批注 Extension"""
    
    return ViewPlugin.define(view => {
        return {
            decorations: computeAnnotations(view, options),
            
            update(update) {
                // 更新批注...
            }
        };
    });
}
```

2. 注册 Extension：

```javascript
// src/web/js/editor.js

import { annotationExtension } from './extensions/annotation-extension.js';

// 注册 Extension
registerExtension('annotation', annotationExtension);
```

---

## 9. Pipeline 扩展设计

### 9.1 增量转换接口

**目标**：支持只转换指定章节，无需重新转换整个项目。

#### 9.1.1 增量转换接口定义

```python
# src/core/pipeline.py

class Pipeline:
    async def run_chapters(
        self, 
        project_id: str,
        chapter_indices: list[int]
    ) -> PipelineContext:
        """增量转换：只处理指定章节
        
        Args:
            project_id: 项目 ID
            chapter_indices: 要转换的章节索引列表（从 0 开始）
            
        Returns:
            更新后的 PipelineContext
        """
        # 1. 读取项目数据
        project = await self._project_store.get_project(project_id)
        novel_text = await self._project_store.get_novel(project_id)
        script = await self._project_store.get_script(project_id)
        
        # 2. 解析章节
        chapters = self._preprocessor.split_chapters(novel_text)
        
        # 3. 只处理指定章节
        context = PipelineContext(
            novel_text=novel_text,
            chapters=[chapters[i] for i in chapter_indices],
            config=load_config()
        )
        
        context = await self.run(context)
        
        # 4. 合并结果到原剧本
        script_obj = yaml.safe_load(script)
        self._merge_chapters(script_obj, context.script_obj, chapter_indices)
        
        # 5. 保存更新后的剧本
        updated_script = yaml.dump(script_obj, allow_unicode=True)
        await self._project_store.save_script(project_id, updated_script)
        
        return context
        
    def _merge_chapters(
        self, 
        original: dict, 
        new: dict, 
        chapter_indices: list[int]
    ) -> None:
        """将新转换的章节合并到原剧本"""
        for i, chapter_idx in enumerate(chapter_indices):
            original["chapters"][chapter_idx] = new["chapters"][i]
```

#### 9.1.2 增量转换 API 端点

```python
# src/api/routes/v1/projects.py

@router.post("/{project_id}/convert-partial")
async def convert_partial(
    project_id: str,
    request: PartialConvertRequest
):
    """增量转换指定章节"""
    pipeline = get_pipeline()
    context = await pipeline.run_chapters(project_id, request.chapter_indices)
    
    return {
        "status": "success",
        "updated_chapters": request.chapter_indices
    }
```

---

## 10. 附录：扩展性检查清单

### 10.1 新增功能时检查清单

| 检查项 | 说明 | 是否满足 |
|-------|------|---------|
| **是否新增了文件，而非修改现有文件？** | 新增功能应该通过新增文件实现（如新增 Step 类、新增 Extension 等） | ✅ / ❌ |
| **是否通过注册机制接入，而非修改核心代码？** | 新增功能应该通过注册机制（如 `register_step()`, `hook()`, `registerComponent()` 等）接入 | ✅ / ❌ |
| **是否通过配置开关控制，而非硬编码？** | 新增功能应该有对应的配置开关（如 `features.new_feature`） | ✅ / ❌ |
| **是否保持了向后兼容性？** | 新增字段应该用 `Optional` + 默认值，不修改已有字段的语义 | ✅ / ❌ |
| **是否编写了单元测试？** | 新增功能应该有对应的单元测试 | ✅ / ❌ |
| **是否更新了文档？** | 新增功能应该更新 PRD、架构设计文档、API 文档等 | ✅ / ❌ |

### 10.2 扩展性设计原则总结

1. **对扩展开放，对修改封闭**（OCP 原则）
2. **依赖抽象接口，不依赖具体实现**（DIP 原则）
3. **单一职责原则**（SRP 原则）
4. **接口隔离原则**（ISP 原则）
5. **配置优于硬编码**
6. **约定优于配置**（提供合理的默认值）
7. **向后兼容优于向前兼容**

---

> **文档版本**：V1.0
> **最后更新**：2026-06-05
> **维护者**：Novel2Script 开发团队
