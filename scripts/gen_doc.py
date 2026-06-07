"""生成项目完整源码文档"""
from pathlib import Path

root = Path(__file__).parent.parent
out = root / "docs" / "项目完整源码文档.md"

exts = {".py", ".js", ".html", ".css", ".json", ".toml", ".txt"}
exclude = {"__pycache__", ".git", ".codebuddy", "node_modules", "dist", "build"}
skip_files = {"novel2script.spec", "build.spec", "convert_fixed.py", "convert_new.py"}

ext_map = {
    "py": "python", "js": "javascript", "html": "html", "css": "css",
    "json": "json", "toml": "toml", "txt": "text",
}

# 功能描述
descriptions = {
    "cli.py": "命令行入口，提供 gui/serve/convert/validate/skill 等子命令",
    "config.py": "配置管理，支持环境变量和 config.json 多层覆盖，API Key 加密存储",
    "llm_client.py": "LLM 客户端封装，统一 OpenAI/DeepSeek 等 API 调用",
    "schema.py": "Pydantic 数据模型，定义 Script/Scene/Beat/Character/DialogueBeat 等",
    "pipeline.py": "Pipeline 编排器，按顺序执行 Step 并触发 Hook，支持容错跳过",
    "project_store.py": "项目文件系统存储，CRUD + 版本快照 + 回收站软删除",
    "format_converter.py": "格式转换器，Script → TXT/HTML/Fountain（纯本地运算）",
    "sse.py": "SSE 事件管理器，支持客户端订阅、事件缓存和心跳",
    "window.py": "PyWebView 桌面窗口，单实例运行 + 端口占用检测 + 浏览器回退",
    "index.html": "主页面，包含所有 UI 组件（编辑器/角色面板/情绪曲线/Skills）",
    "app.js": "Alpine.js 主逻辑，集中状态管理 + 全部 API 调用 + 事件处理",
    "editor.js": "CodeMirror 6 编辑器封装，初始化小说/剧本编辑器",
    "scroll-sync.js": "滚动联动 + YAML Beat 解析器",
    "beat-board.js": "节拍板可视化编辑，卡片式 UI + SortableJS 拖拽排序",
    "beat-editors.js": "Beat 内联编辑器，点击对白/情绪标签/角色名直接编辑",
    "emotion-curve.js": "情绪曲线图表，Chart.js 折线图 + 点击定位",
    "yaml-linter.js": "YAML Schema 实时校验，CodeMirror 6 linter Extension",
    "app.css": "全局样式表",
    "projects.py": "项目管理 API 路由（CRUD/回收站/文件导入）",
    "convert.py": "转换任务 API 路由（SSE 进度推送 + Pipeline 后台执行）",
    "skills.py": "Skills 管理 API 路由（列表/启用/运行/创建/删除）",
    "config.py.route": "配置管理 API 路由（读取/保存/测试连接）",
    "base.py": "StepProtocol 接口定义 + Step 注册表 + 动态加载",
    "character_extractor.py": "角色识别 Step，AI 提取角色 + Levenshtein 别名合并",
    "scene_splitter.py": "场景分割 Step，智能分章 + 超长章节二次分割",
    "dialogue_parser.py": "对白解析 Step，输出 dialogue/action/narration 三种 beat",
    "emotion_tagger.py": "情绪标注 Step，二次校验补全情绪标签",
    "text_splitter.py": "文本分段 Step，将长文本按 2 万字切分",
    "yaml_generator.py": "YAML 生成 Step，自定义 Dumper + 统计信息计算",
}

lines = []
lines.append("# InkScript 完整项目源码文档\n")
lines.append("> 生成时间：2026-06-08 | 文件总数：63\n")

# 收集文件
all_files = []
for p in sorted(root.rglob("*")):
    if any(e in p.parts for e in exclude):
        continue
    if p.name in skip_files:
        continue
    if p.suffix in exts or p.name in ("requirements.txt", "README.md"):
        all_files.append(p)

# 分组
by_dir = {}
for f in all_files:
    rel = str(f.relative_to(root)).replace("\\", "/")
    parts = rel.split("/")
    if parts[0] in ("pyproject.toml", "requirements.txt", "README.md"):
        key = "根目录"
    elif "api/routes" in rel:
        key = "API 路由"
    elif "api" in rel:
        key = "API 层"
    elif "core/steps" in rel:
        key = "Pipeline 步骤"
    elif "core" in rel:
        key = "核心逻辑"
    elif "skills" in rel:
        key = "Skills 技能"
    elif "web" in rel:
        key = "Web 前端"
    elif "desktop" in rel:
        key = "桌面窗口"
    else:
        key = "核心模块"
    if key not in by_dir:
        by_dir[key] = []
    by_dir[key].append(f)

order = ["根目录", "核心模块", "API 层", "API 路由", "核心逻辑", "Pipeline 步骤", "桌面窗口", "Web 前端", "Skills 技能"]

n = 1
for cat in order:
    if cat not in by_dir:
        continue
    lines.append(f"## {cat}\n")
    for f in by_dir[cat]:
        rel = str(f.relative_to(root)).replace("\\", "/")
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            content = "[二进制或编码错误]"

        lines.append(f"### {n}. `{rel}`\n")

        # 描述
        desc_key = f.name
        if "routes" in rel and "config" in rel:
            desc_key = "config.py.route"
        elif "skills" in rel and f.name == "main.py":
            desc_key = f"skills/{f.parent.name}/main.py"
        if desc_key in descriptions:
            lines.append(f"**功能**: {descriptions[desc_key]}\n")

        ext = ext_map.get(f.suffix.lstrip("."), "")
        lines.append(f"```{ext}")
        lines.append(content.rstrip())
        lines.append("```\n---\n")
        n += 1

# 索引
lines.append("## 文件索引\n")
for f in all_files:
    lines.append(f"- `{str(f.relative_to(root)).replace(chr(92), '/')}`")

lines.append(f"\n> 共 {len(all_files)} 个文件")
out.write_text("\n".join(lines), encoding="utf-8")
print(f"Done! {len(all_files)} files -> {out.stat().st_size / 1024:.1f} KB")
