# 🎬 InkScript — 小说智能转剧本

> 📺 **讲解视频**：[百度网盘下载](https://pan.baidu.com/s/1nrcyVrfKZSM1n8EFGi5CLg?pwd=1234) 提取码: 1234

> 粘贴小说 → AI 自动识别角色/场景/对白/情绪 → 生成带镜头指示的结构化剧本

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Status](https://img.shields.io/badge/status-V1%20ready-brightgreen)]()

---

## ✨ 为什么选择 InkScript？

| 优势 | 说明 |
|------|------|
| 🎬 **AI 生成镜头指示** | 自动添加（中景/近景/特写/闪回/叠化）等专业镜头语言 |
| 😊 **13 种情绪标注** | happy/sad/angry/calm/excited/fear/surprised 等，精准情绪分析 |
| 📊 **可视化分析** | 角色情绪雷达图 + 全局情绪曲线，一图看清水剧情感起伏 |
| 🔌 **11 个内置 Skills** | 角色分析/选角建议/HTML导出/分镜生成 等，插件式即开即用 |
| 📤 **4 种导出格式** | YAML / TXT / HTML / Fountain，一键导出 |
| ⚡ **容错不中断** | 单步 AI 调用失败自动跳过，宁可部分结果也不白等 |
| 💾 **纯本地存储** | 数据在 `~/.novel2script/`，完全离线可用 |
| 🖱️ **拖拽式节拍板** | 卡片式 Beat 编辑，SortableJS 拖拽排序 |

---

## 🚀 30 秒快速开始

```bash
git clone https://github.com/wryyyds7/InkScript.git
cd InkScript
pip install -e .
novel2script gui
```

浏览器自动打开 → 新建项目 → 粘贴小说 → 配置 API Key → 点击「开始转换」。

支持 **DeepSeek / OpenAI / Anthropic / 通义千问 / Gemini** 等所有 OpenAI 兼容 API。

---

## 🎯 核心功能

### AI 转换引擎 — 6 步自动转换

```
小说原文
  → 文本分段 (text_splitter)
  → AI 识别角色 (character_extractor) — 提取姓名/别名/外貌性格描述
  → AI 分割场景 (scene_splitter)     — 按地点/时间变化自动切分
  → AI 解析对白 (dialogue_parser)    — ⭐ 输出 dialogue/action/narration 三种 beat
  → AI 标注情绪 (emotion_tagger)     — 13 种情绪自动标注
  → 生成 YAML (yaml_generator)       — 结构化剧本 + 统计信息
```

### 编辑器 — CodeMirror 6 双面板

- **左侧**：小说原文编辑器（可编辑/导入 txt/docx/pdf）
- **右侧**：剧本 YAML 编辑器（语法高亮 + 实时 lint）
- **滚动联动**：点击右侧 beat → 左侧自动跳转到原文位置
- **节拍板**：卡片式 Beat 视图，拖拽排序
- **自动保存**：2 秒防抖，不丢数据

### 分析面板

- **角色雷达图** (Chart.js) — 六维情绪分布一目了然
- **情绪曲线** (折线图) — Beat 级 / 场景级粒度切换，点击数据点定位原文

### Skills 插件系统

11 个内置 Skill，可手动运行或集成到转换 Pipeline：

| Skill | 功能 |
|-------|------|
| `character-analysis` | 角色对白统计与情绪分布 |
| `character-profile` | 人物小传生成 |
| `chapter-summary` | 章节摘要 |
| `casting-suggester` | 选角建议（含匹配度） |
| `structure-analytics` | 剧本结构分析 |
| `storyboard-gen` | 分镜建议 |
| `fountain-export` | Fountain 格式导出 |
| `html-export` | 自包含 HTML 导出 |
| `dialogue-polish` | 对白润色 |
| `style-adapt` | 风格适配 |
| `props-list-gen` | 道具列表生成 |

---

## 📂 项目结构

```
InkScript/
├── novel2script/
│   ├── api/           # FastAPI 后端 + SSE
│   ├── core/          # Pipeline 引擎 + 格式转换 + 项目存储
│   │   └── steps/     # 6 个 Pipeline 步骤
│   ├── desktop/       # PyWebView 桌面窗口
│   ├── skills/        # 11 个内置 Skills
│   ├── web/           # 前端 (Alpine.js + CodeMirror 6)
│   ├── cli.py         # CLI 入口
│   ├── config.py      # 配置管理
│   ├── llm_client.py  # LLM 客户端封装
│   └── schema.py      # Pydantic 数据模型
├── docs/              # 设计文档
├── tests/             # 测试 (21 个全部通过)
└── pyproject.toml     # 项目配置
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / Uvicorn / Pydantic V2 |
| AI | OpenAI SDK (兼容 DeepSeek/OpenAI/Anthropic 等) |
| 桌面 | PyWebView |
| 前端 | Alpine.js / Tailwind CSS / CodeMirror 6 |
| 图表 | Chart.js / SortableJS |
| 存储 | 文件系统 (JSON + YAML) |

---

## 📚 文档

- **[InkScript项目详细文档.md](docs/InkScript项目详细文档.md)** — 综合项目文档（架构/流程/Skills/路线图）
- **[02-数据模型与API.md](docs/02-数据模型与API.md)** — 14 个数据模型 + 49 个 API 端点完整参考
- **[项目完整源码文档.md](docs/项目完整源码文档.md)** — 69 个文件完整源码

---

## 🧪 测试

```bash
pytest tests/ -v    # 21 个测试全部通过
```

---

## 📄 许可证

MIT License
