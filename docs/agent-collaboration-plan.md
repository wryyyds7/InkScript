# InkScript Agent 协作计划

> **项目仓库**：https://github.com/wryyyds7/InkScript
> 
> **设计目标**：充分利用现有 Skills，考虑 Human-in-the-loop，覆盖开发全周期，每个阶段包含 GitHub 提交。

---

## 📋 总览

### 协作流程

```
需求分析 → 架构设计 → 详细设计 → 代码实现 → 测试验证 → 文档编写 → 部署发布
   ↓          ↓          ↓          ↓          ↓          ↓          ↓
 GitHub     GitHub     GitHub     GitHub     GitHub     GitHub     GitHub
 提交       提交       提交       提交       提交       提交       提交
```

### Agent 团队结构

| Agent 角色 | 名称 | 职责 | 使用的 Skills |
|-----------|------|------|--------------|
| 业务分析师 | `business-analyst` | 需求分析、用例编写 | Grill Me、Deep Research |
| 系统架构师 | `system-architect` | 架构设计、技术选型 | Deep Research、提示词工程专家 |
| 详细设计工程师 | `design-engineer` | 详细设计、接口设计 | 提示词工程专家、Grill Me |
| 后端开发工程师 | `backend-dev` | 后端代码实现 | 全栈开发、TDD |
| 前端开发工程师 | `frontend-dev` | 前端代码实现 | 前端开发、React Native 开发（Alpine.js 部分） |
| 全栈开发工程师 | `fullstack-dev` | PyWebView 集成、前后端联调 | 全栈开发 |
| 测试工程师 | `test-engineer` | 单元测试、集成测试 | TDD、Diagnose |
| 性能工程师 | `performance-engineer` | 性能测试、优化 | Web Performance Audit |
| 安全工程师 | `security-engineer` | 安全审计 | Grill Me（安全审查） |
| 技术文档工程师 | `technical-writer` | 用户手册、开发者文档 | 去 AI 味、内容分发 |
| 运维工程师 | `devops-engineer` | 打包、部署 | - |

---

## 🎯 阶段 1：需求分析（business-analyst）

### 负责人：`business-analyst` Agent

### 使用的 Skills
- **Grill Me**：深度质询 PRD，发现需求漏洞
- **Deep Research**：调研同类产品（Final Draft、WriterDuet 等）
- **提示词工程专家**：优化需求描述的可执行性

### 任务清单

#### 任务 1.1：深度质询 PRD（使用 Grill Me Skill）
**输入**：`docs/PRD.md`

**步骤**：
1. 启动 Grill Me Skill
2. 质询《PRD.md》中的所有功能需求
3. 发现需求漏洞、边界情况、未考虑的细节
4. 生成《PRD 质询报告.md》

**输出**：`docs/PRD-grill-report.md`

**Human-in-the-loop**：
- ❓ 质询过程中，AI 会提出很多问题（如"如果用户小说有 100 章怎么办？"）
- ✅ 你需要回答这些问题，完善需求
- 🔄 循环直到所有分支都覆盖

**GitHub 提交**：
```bash
git add docs/PRD-grill-report.md
git commit -m "docs: 添加 PRD 质询报告（Grill Me 输出）"
git push origin main
```

---

#### 任务 1.2：调研同类产品（使用 Deep Research Skill）
**输入**：无

**步骤**：
1. 启动 Deep Research Skill
2. 调研同类产品（Final Draft、WriterDuet、Celtx 等）
3. 对比功能、用户体验、技术架构
4. 生成《同类产品调研报告.md》

**输出**：`docs/competitor-research.md`

**Human-in-the-loop**：
- ❓ 是否需要深入调研某个特定产品？
- ✅ 你选择需要深入调研的产品

**GitHub 提交**：
```bash
git add docs/competitor-research.md
git commit -m "docs: 添加同类产品调研报告（Deep Research 输出）"
git push origin main
```

---

#### 任务 1.3：编写需求规格说明书
**输入**：`docs/PRD.md` + `docs/PRD-grill-report.md` + `docs/competitor-research.md`

**步骤**：
1. 提炼功能需求、非功能需求、约束条件
2. 编写用例（Use Case）
3. 编写用户故事（User Story）
4. 生成《需求规格说明书.md》

**输出**：`docs/requirements-spec.md`

**Human-in-the-loop**：
- ❓ 是否需要调整需求优先级？
- ✅ 你确认需求规格说明书

**GitHub 提交**：
```bash
git add docs/requirements-spec.md
git commit -m "docs: 添加需求规格说明书"
git push origin main
```

---

#### 任务 1.4：更新 PRD.md
**输入**：`docs/PRD.md` + `docs/PRD-grill-report.md`

**步骤**：
1. 根据质询报告，完善 PRD.md
2. 补充遗漏的需求
3. 明确边界情况的处理策略

**输出**：更新后的 `docs/PRD.md`

**GitHub 提交**：
```bash
git add docs/PRD.md
git commit -m "docs: 更新 PRD（根据 Grill Me 质询结果）"
git push origin main
```

---

### 阶段 1 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| PRD 质询报告 | `docs/PRD-grill-report.md` | Grill Me 输出 |
| 同类产品调研报告 | `docs/competitor-research.md` | Deep Research 输出 |
| 需求规格说明书 | `docs/requirements-spec.md` | 详细需求文档 |
| 更新后的 PRD | `docs/PRD.md` | 完善后的 PRD |

**GitHub 提交次数**：4 次

**预估时间**：2-3 小时（包含 Human-in-the-loop 时间）

---

## 🏗️ 阶段 2：架构设计（system-architect）

### 负责人：`system-architect` Agent

### 使用的 Skills
- **Deep Research**：调研技术方案（PyWebView vs Electron vs Tauri）
- **提示词工程专家**：设计技术文档模板
- **Grill Me**：质询架构设计

### 任务清单

#### 任务 2.1：技术选型调研（使用 Deep Research Skill）
**输入**：`docs/requirements-spec.md`

**步骤**：
1. 启动 Deep Research Skill
2. 调研桌面应用技术选型（PyWebView vs Electron vs Tauri）
3. 调研 CodeMirror 6 vs Monaco Editor
4. 调研 FastAPI vs Flask vs Django
5. 生成《技术选型对比报告.md》

**输出**：`docs/tech-selection-report.md`

**Human-in-the-loop**：
- ❓ 是否需要考虑某个特定的技术选型？
- ✅ 你确认技术选型

**GitHub 提交**：
```bash
git add docs/tech-selection-report.md
git commit -m "docs: 添加技术选型对比报告（Deep Research 输出）"
git push origin main
```

---

#### 任务 2.2：系统架构设计
**输入**：`docs/requirements-spec.md` + `docs/tech-selection-report.md`

**步骤**：
1. 设计系统架构（前端、后端、桌面壳）
2. 设计数据流向
3. 设计模块划分
4. 生成《系统架构设计.md》

**输出**：`docs/system-architecture.md`

**Human-in-the-loop**：
- ❓ 是否需要调整模块划分？
- ✅ 你确认系统架构设计

**GitHub 提交**：
```bash
git add docs/system-architecture.md
git commit -m "docs: 添加系统架构设计文档"
git push origin main
```

---

#### 任务 2.3：质询架构设计（使用 Grill Me Skill）
**输入**：`docs/system-architecture.md`

**步骤**：
1. 启动 Grill Me Skill
2. 质询架构设计的可扩展性、性能、安全性
3. 发现架构缺陷
4. 生成《架构设计质询报告.md》

**输出**：`docs/architecture-grill-report.md`

**Human-in-the-loop**：
- ❓ 质询过程中，AI 会提出很多问题（如"如果 100 个用户同时编辑怎么办？"）
- ✅ 你需要回答这些问题，完善架构设计

**GitHub 提交**：
```bash
git add docs/architecture-grill-report.md
git commit -m "docs: 添加架构设计质询报告（Grill Me 输出）"
git push origin main
```

---

#### 任务 2.4：更新架构设计文档
**输入**：`docs/system-architecture.md` + `docs/architecture-grill-report.md`

**步骤**：
1. 根据质询报告，完善架构设计
2. 补充遗漏的设计决策

**输出**：更新后的 `docs/system-architecture.md` + 更新后的 `docs/architecture.md`

**GitHub 提交**：
```bash
git add docs/system-architecture.md docs/architecture.md
git commit -m "docs: 更新架构设计文档（根据 Grill Me 质询结果）"
git push origin main
```

---

### 阶段 2 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| 技术选型对比报告 | `docs/tech-selection-report.md` | Deep Research 输出 |
| 系统架构设计 | `docs/system-architecture.md` | 架构设计文档 |
| 架构设计质询报告 | `docs/architecture-grill-report.md` | Grill Me 输出 |
| 更新后的架构文档 | `docs/architecture.md` | 完善后的架构文档 |

**GitHub 提交次数**：4 次

**预估时间**：3-4 小时（包含 Human-in-the-loop 时间）

---

## 📐 阶段 3：详细设计（design-engineer）

### 负责人：`design-engineer` Agent

### 使用的 Skills
- **提示词工程专家**：设计 Prompt 模板、API 文档
- **Grill Me**：质询详细设计
- **Deep Research**：调研最佳实践

### 任务清单

#### 任务 3.1：API 接口详细设计
**输入**：`docs/system-architecture.md` + `docs/requirements-spec.md`

**步骤**：
1. 设计 RESTful API 端点（路径、方法、请求/响应格式）
2. 设计 SSE 端点（进度推送）
3. 设计错误码规范
4. 生成《API 接口设计文档.md》

**输出**：`docs/api-design.md`

**Human-in-the-loop**：
- ❓ 是否需要调整某个 API 端点的设计？
- ✅ 你确认 API 设计

**GitHub 提交**：
```bash
git add docs/api-design.md
git commit -m "docs: 添加 API 接口设计文档"
git push origin main
```

---

#### 任务 3.2：数据模型详细设计
**输入**：`docs/system-architecture.md` + `docs/yaml-schema.md`

**步骤**：
1. 设计 Pydantic 数据模型
2. 设计数据库表结构（如果 V2 需要）
3. 设计 YAML Schema 校验规则
4. 生成《数据模型设计文档.md》

**输出**：`docs/data-model-design.md`

**Human-in-the-loop**：
- ❓ 是否需要调整某个数据模型？
- ✅ 你确认数据模型设计

**GitHub 提交**：
```bash
git add docs/data-model-design.md
git commit -m "docs: 添加数据模型设计文档"
git push origin main
```

---

#### 任务 3.3：Prompt 模板详细设计
**输入**：`docs/prompt-design.md` + `docs/requirements-spec.md`

**步骤**：
1. 设计每个 Pipeline 步骤的 Prompt 模板
2. 设计 few-shot 示例
3. 设计错误处理策略
4. 生成《Prompt 模板设计文档.md》

**输出**：`docs/prompt-template-design.md`

**Human-in-the-loop**：
- ❓ 是否需要调整某个 Prompt 模板？
- ✅ 你确认 Prompt 设计

**GitHub 提交**：
```bash
git add docs/prompt-template-design.md
git commit -m "docs: 添加 Prompt 模板设计文档"
git push origin main
```

---

#### 任务 3.4：质询详细设计（使用 Grill Me Skill）
**输入**：`docs/api-design.md` + `docs/data-model-design.md` + `docs/prompt-template-design.md`

**步骤**：
1. 启动 Grill Me Skill
2. 质询详细设计的可实现性、可测试性
3. 发现设计漏洞
4. 生成《详细设计质询报告.md》

**输出**：`docs/detailed-design-grill-report.md`

**Human-in-the-loop**：
- ❓ 质询过程中，AI 会提出很多问题（如"如果 API 超时怎么办？"）
- ✅ 你需要回答这些问题，完善详细设计

**GitHub 提交**：
```bash
git add docs/detailed-design-grill-report.md
git commit -m "docs: 添加详细设计质询报告（Grill Me 输出）"
git push origin main
```

---

#### 任务 3.5：更新详细设计文档
**输入**：所有详细设计文档 + `docs/detailed-design-grill-report.md`

**步骤**：
1. 根据质询报告，完善详细设计
2. 补充遗漏的设计细节

**输出**：更新后的所有详细设计文档

**GitHub 提交**：
```bash
git add docs/api-design.md docs/data-model-design.md docs/prompt-template-design.md
git commit -m "docs: 更新详细设计文档（根据 Grill Me 质询结果）"
git push origin main
```

---

### 阶段 3 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| API 接口设计文档 | `docs/api-design.md` | 详细的 API 设计 |
| 数据模型设计文档 | `docs/data-model-design.md` | 详细的数据模型设计 |
| Prompt 模板设计文档 | `docs/prompt-template-design.md` | 详细的 Prompt 设计 |
| 详细设计质询报告 | `docs/detailed-design-grill-report.md` | Grill Me 输出 |

**GitHub 提交次数**：5 次

**预估时间**：4-5 小时（包含 Human-in-the-loop 时间）

---

## 💻 阶段 4：代码实现（dev-team）

### 负责人：`backend-dev` + `frontend-dev` + `fullstack-dev` Agent

### 使用的 Skills
- **全栈开发**：后端 + 前端 + 数据库 + API
- **前端开发**：Alpine.js + CodeMirror 6
- **TDD**：测试驱动开发
- **Grill Me**：代码审查
- **Diagnose**：调试

### 任务清单

#### 任务 4.1：项目脚手架搭建
**负责人**：`fullstack-dev`

**步骤**：
1. 创建项目目录结构
2. 初始化 Python 虚拟环境
3. 创建 `pyproject.toml` 和 `requirements.txt`
4. 创建前端目录结构
5. 配置 PyInstaller

**输出**：项目脚手架

**GitHub 提交**：
```bash
git add -A
git commit -m "chore: 初始化项目脚手架"
git push origin main
```

---

#### 任务 4.2：后端核心代码实现（使用 TDD Skill）
**负责人**：`backend-dev`

**使用的 Skills**：
- **TDD**：测试驱动开发
- **全栈开发**：FastAPI + Pydantic + SSE

**子任务**：

##### 4.2.1 实现配置管理模块
**输入**：`docs/data-model-design.md`

**步骤**：
1. 编写配置管理模块的单元测试（TDD 红阶段）
2. 实现配置管理模块（TDD 绿阶段）
3. 重构（TDD 重构阶段）

**输出**：`src/config.py` + `tests/test_config.py`

**GitHub 提交**：
```bash
git add src/config.py tests/test_config.py
git commit -m "feat: 实现配置管理模块"
git push origin main
```

---

##### 4.2.2 实现数据模型模块
**输入**：`docs/data-model-design.md` + `docs/yaml-schema.md`

**步骤**：
1. 编写数据模型模块的单元测试
2. 实现 Pydantic 数据模型
3. 实现 YAML Schema 校验

**输出**：`src/schema.py` + `tests/test_schema.py`

**GitHub 提交**：
```bash
git add src/schema.py tests/test_schema.py
git commit -m "feat: 实现数据模型模块"
git push origin main
```

---

##### 4.2.3 实现 ProjectStore 模块
**输入**：`docs/data-model-design.md` + `docs/extensibility-design-spec.md`

**步骤**：
1. 编写 ProjectStore 的单元测试
2. 实现 `ProjectStore` Protocol
3. 实现 `FileSystemProjectStore`

**输出**：`src/core/project_store.py` + `tests/test_project_store.py`

**GitHub 提交**：
```bash
git add src/core/project_store.py tests/test_project_store.py
git commit -m "feat: 实现 ProjectStore 模块"
git push origin main
```

---

##### 4.2.4 实现 LLM 客户端模块
**输入**：`docs/prompt-template-design.md`

**步骤**：
1. 编写 LLM 客户端的单元测试
2. 实现 `LLMClient` 类
3. 实现重试、超时、错误处理

**输出**：`src/llm_client.py` + `tests/test_llm_client.py`

**GitHub 提交**：
```bash
git add src/llm_client.py tests/test_llm_client.py
git commit -m "feat: 实现 LLM 客户端模块"
git push origin main
```

---

##### 4.2.5 实现 Pipeline 核心模块
**输入**：`docs/extensibility-design-spec.md` + `docs/prompt-template-design.md`

**步骤**：
1. 编写 Pipeline 的单元测试
2. 实现 `Pipeline` 类
3. 实现 Hook 机制
4. 实现 Step 插件机制

**输出**：`src/core/pipeline.py` + `tests/test_pipeline.py`

**GitHub 提交**：
```bash
git add src/core/pipeline.py tests/test_pipeline.py
git commit -m "feat: 实现 Pipeline 核心模块"
git push origin main
```

---

##### 4.2.6 实现各 Pipeline Step
**输入**：`docs/prompt-template-design.md`

**步骤**：
1. 编写每个 Step 的单元测试
2. 实现 `CharacterStep`
3. 实现 `SceneStep`
4. 实现 `DialogueStep`
5. 实现 `EmotionStep`

**输出**：`src/core/steps/` 目录 + `tests/test_steps.py`

**GitHub 提交**：
```bash
git add src/core/steps/ tests/test_steps.py
git commit -m "feat: 实现各 Pipeline Step"
git push origin main
```

---

##### 4.2.7 实现 Skill 系统
**输入**：`docs/extensibility-design-spec.md`

**步骤**：
1. 编写 Skill 系统的单元测试
2. 实现 `SkillManager`
3. 实现 Skill 加载、注册、执行

**输出**：`src/skills/manager.py` + `tests/test_skill_manager.py`

**GitHub 提交**：
```bash
git add src/skills/manager.py tests/test_skill_manager.py
git commit -m "feat: 实现 Skill 系统"
git push origin main
```

---

##### 4.2.8 实现 FastAPI 路由
**输入**：`docs/api-design.md`

**步骤**：
1. 编写 API 端点的单元测试
2. 实现 `/api/v1/projects` 路由
3. 实现 `/api/v1/convert` 路由
4. 实现 `/api/v1/skills` 路由
5. 实现 SSE 进度推送

**输出**：`src/api/routes/v1/` 目录 + `tests/test_api.py`

**Human-in-the-loop**：
- ❓ 是否需要调整某个 API 端点的行为？
- ✅ 你确认 API 实现

**GitHub 提交**：
```bash
git add src/api/ tests/test_api.py
git commit -m "feat: 实现 FastAPI 路由"
git push origin main
```

---

#### 任务 4.3：前端核心代码实现（使用前端开发 Skill）
**负责人**：`frontend-dev`

**使用的 Skills**：
- **前端开发**：Alpine.js + CodeMirror 6
- **提示词工程专家**：设计前端组件规范

**子任务**：

##### 4.3.1 实现 Alpine.js 组件系统
**输入**：`docs/system-architecture.md` + `docs/extensibility-design-spec.md`

**步骤**：
1. 实现事件总线（EventBus）
2. 实现组件注册机制
3. 实现路由注册机制

**输出**：`frontend/js/app.js` + `frontend/js/components/`

**GitHub 提交**：
```bash
git add frontend/js/app.js frontend/js/components/
git commit -m "feat: 实现 Alpine.js 组件系统"
git push origin main
```

---

##### 4.3.2 实现 CodeMirror 6 编辑器
**输入**：`docs/yaml-schema.md` + `docs/extensibility-design-spec.md`

**步骤**：
1. 集成 CodeMirror 6
2. 实现 YAML 语法高亮
3. 实现 Schema 校验
4. 实现自动补全

**输出**：`frontend/js/editor.js` + `frontend/css/editor.css`

**GitHub 提交**：
```bash
git add frontend/js/editor.js frontend/css/editor.css
git commit -m "feat: 实现 CodeMirror 6 编辑器"
git push origin main
```

---

##### 4.3.3 实现项目管理界面
**输入**：`docs/api-design.md`

**步骤**：
1. 实现项目列表页面
2. 实现项目创建/编辑/删除功能
3. 实现项目导入/导出功能

**输出**：`frontend/pages/projects.html` + `frontend/js/components/projectList.js`

**GitHub 提交**：
```bash
git add frontend/pages/projects.html frontend/js/components/projectList.js
git commit -m "feat: 实现项目管理界面"
git push origin main
```

---

##### 4.3.4 实现编辑器界面
**输入**：`docs/api-design.md`

**步骤**：
1. 实现双栏编辑器布局
2. 实现 Beat 卡片展示
3. 实现实时预览

**输出**：`frontend/pages/editor.html` + `frontend/js/components/editor.js`

**Human-in-the-loop**：
- ❓ 是否需要调整编辑器界面布局？
- ✅ 你确认前端界面

**GitHub 提交**：
```bash
git add frontend/pages/editor.html frontend/js/components/editor.js
git commit -m "feat: 实现编辑器界面"
git push origin main
```

---

#### 任务 4.4：PyWebView 集成（使用全栈开发 Skill）
**负责人**：`fullstack-dev`

**使用的 Skills**：
- **全栈开发**：PyWebView + FastAPI 集成

**子任务**：

##### 4.4.1 实现 PyWebView 桌面壳
**输入**：`docs/system-architecture.md`

**步骤**：
1. 实现 PyWebView 窗口管理
2. 实现回退检测逻辑
3. 实现浏览器模式回退

**输出**：`src/desktop/app.py` + `src/desktop/window.py`

**GitHub 提交**：
```bash
git add src/desktop/app.py src/desktop/window.py
git commit -m "feat: 实现 PyWebView 桌面壳"
git push origin main
```

---

##### 4.4.2 前后端联调
**输入**：所有前后端代码

**步骤**：
1. 启动 FastAPI 后端
2. 启动 PyWebView 桌面壳
3. 测试所有功能
4. 修复 Bug

**输出**：可运行的应用程序

**Human-in-the-loop**：
- ❓ 是否发现 Bug？
- ✅ 你确认应用程序可运行

**GitHub 提交**：
```bash
git add -A
git commit -m "fix: 前后端联调，修复 Bug"
git push origin main
```

---

#### 任务 4.5：代码审查（使用 Grill Me Skill）
**负责人**：`backend-dev` + `frontend-dev`

**步骤**：
1. 启动 Grill Me Skill
2. 质询代码的质量、可维护性、安全性
3. 发现代码缺陷
4. 生成《代码审查报告.md》

**输出**：`docs/code-review-report.md`

**GitHub 提交**：
```bash
git add docs/code-review-report.md
git commit -m "docs: 添加代码审查报告（Grill Me 输出）"
git push origin main
```

---

### 阶段 4 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| 后端代码 | `src/` | FastAPI + Pipeline + Skill 系统 |
| 前端代码 | `frontend/` | Alpine.js + CodeMirror 6 |
| 桌面壳代码 | `src/desktop/` | PyWebView 集成 |
| 单元测试 | `tests/` | 所有模块的单元测试 |
| 代码审查报告 | `docs/code-review-report.md` | Grill Me 输出 |

**GitHub 提交次数**：约 15-20 次

**预估时间**：10-15 小时（包含 Human-in-the-loop 时间）

---

## 🧪 阶段 5：测试验证（qa-team）

### 负责人：`test-engineer` + `performance-engineer` + `security-engineer` Agent

### 使用的 Skills
- **TDD**：测试驱动开发
- **Diagnose**：调试
- **Web Performance Audit**：性能测试
- **Grill Me**：安全审查

### 任务清单

#### 任务 5.1：编写集成测试
**负责人**：`test-engineer`

**步骤**：
1. 编写 API 集成测试
2. 编写前后端集成测试
3. 编写端到端（E2E）测试

**输出**：`tests/integration/` 目录

**GitHub 提交**：
```bash
git add tests/integration/
git commit -m "test: 添加集成测试"
git push origin main
```

---

#### 任务 5.2：性能测试（使用 Web Performance Audit Skill）
**负责人**：`performance-engineer`

**步骤**：
1. 启动 Web Performance Audit Skill
2. 测试页面加载性能
3. 测试长文本处理性能
4. 测试并发性能
5. 生成《性能测试报告.md》

**输出**：`docs/performance-test-report.md`

**Human-in-the-loop**：
- ❓ 是否需要优化某个性能指标？
- ✅ 你确认性能测试结果

**GitHub 提交**：
```bash
git add docs/performance-test-report.md
git commit -m "docs: 添加性能测试报告（Web Performance Audit 输出）"
git push origin main
```

---

#### 任务 5.3：安全审计（使用 Grill Me Skill）
**负责人**：`security-engineer`

**步骤**：
1. 启动 Grill Me Skill（安全审查模式）
2. 审计 Skill 沙箱安全性
3. 审计 API 安全性
4. 审计数据安全性
5. 生成《安全审计报告.md》

**输出**：`docs/security-audit-report.md`

**GitHub 提交**：
```bash
git add docs/security-audit-report.md
git commit -m "docs: 添加安全审计报告（Grill Me 输出）"
git push origin main
```

---

#### 任务 5.4：Bug 修复
**负责人**：`backend-dev` + `frontend-dev`

**步骤**：
1. 根据测试报告，修复 Bug
2. 重新运行测试
3. 确保全部通过

**输出**：修复后的代码

**GitHub 提交**：
```bash
git add -A
git commit -m "fix: 根据测试报告修复 Bug"
git push origin main
```

---

### 阶段 5 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| 集成测试 | `tests/integration/` | API + 前后端集成测试 |
| 性能测试报告 | `docs/performance-test-report.md` | Web Performance Audit 输出 |
| 安全审计报告 | `docs/security-audit-report.md` | Grill Me 输出 |
| 修复后的代码 | `src/` + `frontend/` | Bug 修复 |

**GitHub 提交次数**：约 5-8 次

**预估时间**：5-8 小时（包含 Human-in-the-loop 时间）

---

## 📚 阶段 6：文档编写（technical-writer）

### 负责人：`technical-writer` Agent

### 使用的 Skills
- **去 AI 味**：优化文档可读性
- **内容分发**：生成多平台文档

### 任务清单

#### 任务 6.1：编写用户手册
**输入**：所有代码 + 所有需求文档

**步骤**：
1. 编写安装指南
2. 编写快速入门
3. 编写功能详解
4. 编写常见问题（FAQ）

**输出**：`docs/user-manual.md`

**Human-in-the-loop**：
- ❓ 是否需要调整文档结构？
- ✅ 你确认用户手册

**GitHub 提交**：
```bash
git add docs/user-manual.md
git commit -m "docs: 添加用户手册"
git push origin main
```

---

#### 任务 6.2：编写开发者指南
**输入**：所有代码 + 所有设计文档

**步骤**：
1. 编写项目结构说明
2. 编写代码规范
3. 编写扩展开发指南（如何开发新 Skill、新 Step）
4. 编写贡献指南

**输出**：`docs/developer-guide.md`

**GitHub 提交**：
```bash
git add docs/developer-guide.md
git commit -m "docs: 添加开发者指南"
git push origin main
```

---

#### 任务 6.3：生成 API 参考文档
**输入**：`docs/api-design.md` + 代码

**步骤**：
1. 使用 FastAPI 的 `/docs` 界面生成 OpenAPI Schema
2. 转换为 Markdown 格式
3. 优化可读性（使用"去 AI 味"Skill）

**输出**：`docs/api-reference.md`

**GitHub 提交**：
```bash
git add docs/api-reference.md
git commit -m "docs: 添加 API 参考文档"
git push origin main
```

---

### 阶段 6 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| 用户手册 | `docs/user-manual.md` | 面向最终用户 |
| 开发者指南 | `docs/developer-guide.md` | 面向后续开发者 |
| API 参考文档 | `docs/api-reference.md` | API 文档 |

**GitHub 提交次数**：3 次

**预估时间**：3-4 小时（包含 Human-in-the-loop 时间）

---

## 🚀 阶段 7：部署发布（devops-engineer）

### 负责人：`devops-engineer` Agent

### 任务清单

#### 任务 7.1：编写 PyInstaller 打包配置
**输入**：项目代码

**步骤**：
1. 编写 `novel2script.spec` 文件
2. 配置依赖打包
3. 配置文件打包
4. 测试打包

**输出**：`build/novel2script.spec`

**GitHub 提交**：
```bash
git add build/novel2script.spec
git commit -m "build: 添加 PyInstaller 打包配置"
git push origin main
```

---

#### 任务 7.2：编写自动化构建脚本
**输入**：`build/novel2script.spec`

**步骤**：
1. 编写 `scripts/build.ps1`（Windows）
2. 编写 `scripts/build.sh`（macOS/Linux）
3. 测试构建脚本

**输出**：`scripts/build.ps1` + `scripts/build.sh`

**GitHub 提交**：
```bash
git add scripts/build.ps1 scripts/build.sh
git commit -m "build: 添加自动化构建脚本"
git push origin main
```

---

#### 任务 7.3：执行打包
**输入**：所有代码

**步骤**：
1. 运行构建脚本
2. 生成安装包
3. 测试安装包

**输出**：`dist/` 目录下的安装包

**Human-in-the-loop**：
- ❓ 是否需要调整打包配置？
- ✅ 你确认安装包可运行

**GitHub 提交**：
```bash
git add dist/
git commit -m "build: 添加打包后的安装包"
git push origin main
```

---

#### 任务 7.4：编写发布说明
**输入**：所有文档

**步骤**：
1. 编写 `CHANGELOG.md`
2. 编写 `README.md`
3. 编写发布说明

**输出**：`CHANGELOG.md` + `README.md`

**GitHub 提交**：
```bash
git add CHANGELOG.md README.md
git commit -m "docs: 添加 CHANGELOG 和 README"
git push origin main
```

---

### 阶段 7 交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| PyInstaller 配置 | `build/novel2script.spec` | 打包配置 |
| 构建脚本 | `scripts/build.ps1` + `scripts/build.sh` | 自动化构建 |
| 安装包 | `dist/` | 最终产物 |
| 发布说明 | `CHANGELOG.md` + `README.md` | 发布文档 |

**GitHub 提交次数**：4 次

**预估时间**：2-3 小时（包含 Human-in-the-loop 时间）

---

## 🔄 Human-in-the-loop 汇总

### 需要你参与决策的时刻

| 阶段 | 时刻 | 你的决策 |
|------|------|---------|
| 需求分析 | Grill Me 质询过程中 | 回答质询问题，完善需求 |
| 架构设计 | 技术选型时 | 确认技术选型 |
| 详细设计 | API 设计评审时 | 确认 API 设计 |
| 代码实现 | API 实现完成后 | 确认 API 行为是否符合预期 |
| 代码实现 | 前端界面完成后 | 确认界面布局是否合理 |
| 测试验证 | 性能测试完成后 | 确认性能是否达标 |
| 文档编写 | 用户手册完成后 | 确认文档是否清晰 |
| 部署发布 | 安装包生成后 | 确认安装包是否可运行 |

### 如何回答 AI 的询问

**示例 1：Grill Me 质询**
```
AI：如果用户小说有 100 章怎么办？
你：V1 限制为 50 章，V2 支持无限章节（通过分段处理）。
AI：如果分段后上下文丢失怎么办？
你：使用 200 字上下文窗口（见 PRD 中的"长文本智能分段"）。
```

**示例 2：技术选型**
```
AI：建议使用 Tauri 而不是 PyWebView，因为性能更好。
你：坚持使用 PyWebView，因为开发效率更高，且 V1 不追求极致性能。
```

**示例 3：API 设计**
```
AI：建议将 /api/v1/convert 改为 /api/v1/pipeline，因为更通用。
你：坚持使用 /api/v1/convert，因为更符合用户心智模型。
```

---

## 📊 GitHub 提交规范

### 提交信息格式

```
<type>: <subject>

<body>

<footer>
```

**Type**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**：
```bash
git commit -m "feat: 实现配置管理模块

- 添加 AppConfig 模型
- 添加配置加载逻辑
- 添加配置校验逻辑

Closes #1"
```

### 分支策略

| 分支 | 说明 |
|------|------|
| `main` | 主分支，保护分支，只能合并不能直推 |
| `develop` | 开发分支，所有功能分支合并到这里 |
| `feature/*` | 功能分支，如 `feature/pipeline` |
| `bugfix/*` | Bug 修复分支，如 `bugfix/api-timeout` |
| `release/*` | 发布分支，如 `release/v1.0.0` |

**工作流程**：
1. 从 `develop` 创建功能分支：`git checkout -b feature/pipeline`
2. 在功能分支上开发、提交
3. 完成后，合并到 `develop`：`git checkout develop && git merge feature/pipeline`
4. 删除功能分支：`git branch -d feature/pipeline`
5. 发布时，从 `develop` 创建 `release/v1.0.0` 分支
6. 在 `release` 分支上修复 Bug
7. 完成后，合并到 `main` 和 `develop`

---

## 🎯 总结

### 总 GitHub 提交次数
- 阶段 1（需求分析）：4 次
- 阶段 2（架构设计）：4 次
- 阶段 3（详细设计）：5 次
- 阶段 4（代码实现）：15-20 次
- 阶段 5（测试验证）：5-8 次
- 阶段 6（文档编写）：3 次
- 阶段 7（部署发布）：4 次

**总计**：约 40-48 次提交

### 总预估时间
- 阶段 1：2-3 小时
- 阶段 2：3-4 小时
- 阶段 3：4-5 小时
- 阶段 4：10-15 小时
- 阶段 5：5-8 小时
- 阶段 6：3-4 小时
- 阶段 7：2-3 小时

**总计**：约 29-42 小时（包含 Human-in-the-loop 时间）

---

## 🚀 下一步

**你想要我**：

**选项 A**：立即启动 **阶段 1（需求分析）**，开始执行 `business-analyst` Agent 的任务？

**选项 B**：我先帮你**创建一个 GitHub Project 看板**，将每个任务作为 Issue 管理？

**选项 C**：我先帮你**编写 GitHub Actions 自动化工作流**，实现自动测试、自动打包？

**选项 D**：我帮你**编写一个启动脚本**，一键启动所有 Agent？

请告诉我你的选择！