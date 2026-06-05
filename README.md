# InkScript (Novel2Script)

> 将小说自动转换为结构化剧本的桌面应用

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

---

## 📖 简介

InkScript 是一款本地安装的桌面级应用，用于将小说文本自动转换为结构化剧本 YAML。支持双启动模式（桌面应用 / Web 服务），内置编辑器，项目管理，以及可扩展的 Skill 系统。

### 核心特性

- ✅ **自动转换**：基于 LLM 的智能转换（角色识别、场景分割、对白解析、情绪标注）
- ✅ **双启动模式**：桌面应用（PyWebView）或 Web 服务（FastAPI）
- ✅ **内置编辑器**：小说原文和剧本 YAML 双面板编辑
- ✅ **项目管理**：创建、保存、加载项目
- ✅ **Skill 系统**：可扩展的插件系统
- ✅ **SSE 进度推送**：实时显示转换进度
- ✅ **用户自选 AI**：支持 OpenAI API 及兼容服务

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/wryyyds7/InkScript.git
cd InkScript

# 安装依赖
pip install -e ".[dev]"

# 配置 API Key
novel2script config
```

### 使用

#### 1. 桌面模式（默认）

```bash
novel2script gui
```

启动 PyWebView 桌面窗口，内置编辑器。

#### 2. Web 服务模式

```bash
novel2script serve --port 8000
```

启动 FastAPI Web 服务，在浏览器中打开 `http://127.0.0.1:8000`。

#### 3. CLI 直接转换

```bash
novel2script convert input.txt output.yaml --model gpt-4
```

直接在命令行中转换小说为剧本 YAML。

---

## 📂 项目结构

```
InkScript/
├── novel2script/              # 主包
│   ├── api/                  # FastAPI 后端
│   ├── core/                 # 核心转换逻辑
│   ├── desktop/              # 桌面窗口（PyWebView）
│   ├── skills/               # Skill 系统
│   ├── web/                  # 前端静态文件
│   ├── cli.py                # CLI 入口
│   ├── config.py             # 配置管理
│   └── schema.py             # Pydantic 数据模型
├── tests/                    # 测试
├── docs/                     # 设计文档
├── scripts/                  # 脚本
├── pyproject.toml           # 项目配置
└── README.md                # 本文件
```

---

## 🧩 核心功能

### 1. 项目管理

- 创建项目
- 保存/加载小说原文
- 保存/加载剧本 YAML
- 删除项目

### 2. 转换 Pipeline

转换过程分为 5 个步骤：

1. **角色识别** (`character_extractor`)：从小说中提取所有角色
2. **场景分割** (`scene_splitter`)：按时空变化分割场景
3. **对白解析** (`dialogue_parser`)：识别对白、动作、旁白
4. **情绪标注** (`emotion_tagger`)：为每个 Beat 标注情绪
5. **YAML 生成** (`yaml_generator`)：生成结构化剧本 YAML

### 3. Skill 系统

可扩展的插件系统，支持：

- `pre_processor`：转换前处理
- `post_processor`：转换后处理
- `exporter`：导出功能
- `analyzer`：分析功能

内置 Skill：

- `fountain_export`：YAML → Fountain 导出
- `character_report`：角色分析
- `dialogue_polish`：对白润色
- `style_adapter`：风格适配
- `chapter_summary`：章节概要

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_pipeline.py -v
pytest tests/integration/test_api.py -v
```

当前测试覆盖：

- ✅ 单元测试：17 个
- ✅ 集成测试：4 个
- ✅ 总计：21 个（全部通过）

---

## 📚 文档

设计文档位于 `docs/` 目录：

- `PRD.md` - 产品需求文档
- `architecture.md` - 系统架构设计
- `api-design.md` - API 接口设计
- `yaml-schema.md` - 剧本 YAML Schema 设计
- `extensibility-design-spec.md` - 扩展性设计详细规范
- `prompt-design.md` - Prompt 工程设计
- `agent-collaboration-plan.md` - Agent 协作计划

---

## 🛠️ 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端语言 |
| FastAPI | 0.110+ | Web 框架 |
| Pydantic | 2.5+ | 数据验证 |
| PyWebView | 5.0+ | 桌面窗口 |
| Alpine.js | 3.x | 前端框架 |
| CodeMirror 6 | - | 代码编辑器 |
| PyInstaller | - | 打包工具 |

---

## 📝 开发计划

### V1（当前版本）

- ✅ 核心转换功能
- ✅ 双启动模式
- ✅ 内置编辑器
- ✅ 项目管理
- 🚧 前端编辑器完善（进行中）
- 📝 用户手册编写
- 📦 PyInstaller 打包

### V2（计划中）

- 章节管理
- 角色关系图谱
- 对白润色 Skill
- 风格适配 Skill

### V3（计划中）

- 多人协作
- 云端同步
- 移动端支持

---

## 🤝 贡献

欢迎贡献！请查看 `docs/developer-guide.md`（待编写）了解如何贡献代码。

---

## 📄 许可证

MIT License

---

## 📧 联系

- 项目仓库：https://github.com/wryyyds7/InkScript
- 问题反馈：https://github.com/wryyyds7/InkScript/issues

---

**最后更新**：2026-06-05
