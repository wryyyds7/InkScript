"""场景分割 Step

将小说文本按场景切换分割成独立场景.
支持智能分章策略（正则匹配章标题）.
"""

from __future__ import annotations

import json
import re
from typing import Any, dict

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Script


def _split_by_chapters(text: str) -> list[tuple[str, str]]:
    """按章标题分割文本

    Args:
        text: 小说文本

    Returns:
        [(章节标题, 章节内容), ...]
    """
    # 匹配章标题的正则表达式
    chapter_patterns = [
        r"第[一二三四五六七八九十百千\d]+章[^\n]*",  # 第一章 xxx
        r"第[一二三四五六七八九十百千\d]+节[^\n]*",  # 第一节 xxx
        r"Chapter\s+\d+[^\n]*",  # Chapter 1 xxx
        r"第\d+章[^\n]*",  # 第1章 xxx
        r"【[^】]+】",  # 【章节标题】
        r"#+\s+.+",  # Markdown 标题
    ]

    # 尝试所有模式
    for pattern in chapter_patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if len(matches) >= 2:  # 至少 2 章才分割
            segments = []
            for i, match in enumerate(matches):
                title = match.group().strip()
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                content = text[start:end].strip()
                segments.append((title, content))
            return segments

    # 没有找到章节标题，返回整个文本
    return [("全文", text)]


def _smart_split_scenes(text: str, max_length: int = 5000) -> list[str]:
    """智能分割场景（无章标题时按字数/段落分割）

    Args:
        text: 章节文本
        max_length: 每个场景最大字数

    Returns:
        场景列表
    """
    scenes = []
    current_scene = ""
    
    # 按双换行分割段落
    paragraphs = text.split("\n\n")
    
    for para in paragraphs:
        if not para.strip():
            continue
            
        # 如果当前场景 + 新段落超过限制，保存当前场景
        if len(current_scene) + len(para) > max_length and current_scene:
            scenes.append(current_scene.strip())
            current_scene = para
        else:
            current_scene += "\n\n" + para if current_scene else para
    
    # 保存最后一个场景
    if current_scene:
        scenes.append(current_scene.strip())
    
    return scenes


_SYSTEM_PROMPT = """你是一个专业的剧本场景分析师.
将小说文本按场景切换(时间/地点变化)分割成独立场景,输出 JSON 数组.

每个场景包含:
- title: 场景标题(简短描述)
- location: 地点
- time: 时间
"""

_USER_PROMPT_TPL = """## 小说文本

{segment_text}

## 已有角色列表

{characters}

## 要求

1. 按场景切换分割(地点/时间变化即为新场景)
2. 每个场景编号自动分配(从 {start_id} 开始)
3. 输出 JSON 数组,格式:
```json
[
  {{"title": "教室课间", "location": "教室", "time": "白天"}}
]
```
"""


@register_step("scene_splitter")
class SceneSplitterStep:
    """场景分割 Step"""

    @property
    def name(self) -> str:
        return "scene_splitter"

    @property
    def description(self) -> str:
        return "分割场景"

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        characters = ctx.get("characters", [])
        char_str = "、".join(characters) if characters else "(暂无)"

        # 1. 尝试按章标题分割
        chapters = _split_by_chapters(novel_text)
        
        script.scenes = []
        scene_id = 1

        for chapter_title, chapter_content in chapters:
            # 2. 如果章节内容过长，智能分割场景
            if len(chapter_content) > 5000:
                scene_texts = _smart_split_scenes(chapter_content)
            else:
                scene_texts = [chapter_content]

            for scene_text in scene_texts:
                if not scene_text.strip():
                    continue

                prompt = _USER_PROMPT_TPL.format(
                    segment_text=scene_text[:5000],  # 每段最多 5000 字
                    characters=char_str,
                    start_id=scene_id,
                )
                raw = llm.chat_json(
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    schema={
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "location": {"type": "string"},
                                "time": {"type": "string"},
                            },
                        },
                    },
                )
                for s in raw:
                    script.scenes.append(
                        type(script).model_validate(  # type: ignore[attr-defined]
                            {
                                "scene_id": scene_id,
                                "title": s.get("title", "") or chapter_title,
                                "location": s.get("location", ""),
                                "time": s.get("time", ""),
                                "beats": [],
                            }
                        )
                    )
                    scene_id += 1

        return script
