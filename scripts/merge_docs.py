"""合并 docs 文档为一个"""
import re
from pathlib import Path

root = Path(r"D:\bianchenglianxi\project\InkScript\docs")

# 要合并的文件（按顺序）
files = [
    ("00-项目概述.md", "## 一、项目概述"),
    ("01-架构设计.md", "## 二、架构设计"),
    ("03-技术选型与配置.md", "## 三、技术选型与配置"),
    ("04-功能流程与实现状态.md", "## 四、功能流程与实现状态"),
    ("05-项目结构与代码指南.md", "## 五、项目结构与代码指南"),
    ("09-功能详解与使用指南.md", "## 六、功能详解与使用指南"),
    ("07-竞品调研与功能规划.md", "## 七、竞品调研与功能规划"),
    ("08-开发进度与计划.md", "## 八、开发进度与计划"),
    ("10-总结与路线图.md", "## 九、总结与路线图"),
]

out = []
out.append("# InkScript 项目详细文档\n")
out.append("> **版本**：V3 | **更新**：2026-06-08 | **状态**：V1 核心功能已完成 (88%)\n")
out.append("> **相关文档**：[数据模型与API](02-数据模型与API.md) | [完整源码](项目完整源码文档.md)\n")
out.append("\n---\n")

for fname, heading in files:
    fpath = root / fname
    if not fpath.exists():
        continue
    content = fpath.read_text(encoding="utf-8")
    
    # 去掉文件头部的标题行（# xxx），替换为新的二级标题
    content = re.sub(r'^#\s+.+\n+', '', content, count=1)
    
    # 把所有 # 降一级（# → ##, ## → ###，但只对行首的标题）
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            line = '#' + line
        new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # 去掉文档元数据/版本信息行
    content = re.sub(r'> \*\*版本\*\*.*\n', '', content)
    content = re.sub(r'> 更新时间.*\n', '', content)
    content = re.sub(r'> \*\*前置文档\*\*.*\n', '', content)
    content = re.sub(r'> 文档编号.*\n', '', content)
    
    out.append(heading)
    out.append("")
    out.append(content.strip())
    out.append("\n\n---\n")

# 写入合并文档
merged = root / "InkScript项目详细文档.md"
merged.write_text("\n".join(out), encoding="utf-8")
print(f"Merged {len(files)} files → {merged.stat().st_size / 1024:.0f} KB")
