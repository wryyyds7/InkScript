# fix_yaml.py - 修复 yaml-schema.md 中的 source_location 问题
import re

path = r"D:\bianchenglianxi\project\InkScript\docs\yaml-schema.md"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 方案:用正则匹配 NarrationBeat 类定义,插入 source_location 字段
# 匹配:NarrationBeat 类定义到 TransitionBeat 之前的文本
pattern = r"(class NarrationBeat\(BaseModel\):.*?)(\nclass TransitionBeat)"

match = re.search(pattern, content, re.DOTALL)
if match:
    # 在 metadata 字段之前插入 source_location
    narration_block = match.group(1)
    # 在 source_text 字段之后、metadata 之前插入
    new_block = narration_block.replace(
        "    source_text: Optional[str] = None\n",
        "    source_text: Optional[str] = None\n    source_location: Optional[SourceLocation] = None  # 原文位置映射,用于滚动联动\n"
    )
    content = content[:match.start()] + new_block + match.group(2) + content[match.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK: NarrationBeat source_location 已补充")
else:
    print("FAIL: 未找到 NarrationBeat 类定义")

# 同时补充 SourceLocation 类定义(放在 TransitionBeat 之后、Beat union 之前)
location = '''class SourceLocation(BaseModel):
    """原文位置映射(用于滚动联动)"""
    chapter_index: int       # 章节序号(从 0 开始)
    start_paragraph: int    # 起始段落索引
    end_paragraph: int      # 结束段落索引
    start_offset: int       # 段落内起始字符偏移
    end_offset: int         # 段落内结束字符偏移\n\n'''

insert_before = "Beat = DialogueBeat | ActionBeat | NarrationBeat | TransitionBeat"
if insert_before in content and "class SourceLocation" not in content:
    content = content.replace(insert_before, location + insert_before, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK: SourceLocation 类已补充")
else:
    print("INFO: SourceLocation 已存在或未找到插入点")
