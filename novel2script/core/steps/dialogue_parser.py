"""对白解析 Step
将小说文本中的对白内容解析为 DialogueBeat.
"""

from __future__ import annotations

import json
import re

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import BeatType, DialogueBeat, Script, SourceLocation


_SYSTEM_PROMPT = """你是一个专业的剧本对白解析师。
从小说文本中识别所有对白，输出 JSON 数组。

每个对白包含:
- character: 说话角色名称
- content: 对白内容
- emotion: 情绪(可选,如 happy/sad/angry/calm)
- source_start: 对白在原文中的**起始段落索引**（从 0 开始，按双换行分段）
- source_end: 对白在原文中的**结束段落索引**（通常与 start 相同，除非对白跨多段）

只输出 JSON，不要输出其他内容。
"""

_USER_PROMPT_TPL = """## 角色列表

{characters}

## 场景

{scene_title}({scene_location})

## 文本片段（已按段落编号）

{text_with_paragraph_numbers}

## 要求

1. 只识别已知角色的对白
2. 中文引号「」"" 内通常为对白
3. 为每个对白标注它在原文中的段落范围（source_start / source_end）
4. 输出 JSON 数组,格式:
```json
[
  {{"character": "李雷", "content": "你好", "emotion": "happy", "source_start": 3, "source_end": 3}}
]
```
"""


@register_step("dialogue_parser")
class DialogueParserStep:
    """对白解析 Step"""

    @property
    def name(self) -> str:
        return "dialogue_parser"

    @property
    def description(self) -> str:
        return "解析对白"

    def _add_paragraph_numbers(self, text: str) -> str:
        """给每个段落加上编号，帮助 LLM 定位 source_location"""
        paragraphs = re.split(r"\n{2,}", text)
        numbered = []
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if para:
                numbered.append(f"[段落 {i}] {para}")
        return "\n\n".join(numbered)

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        print(f"[dialogue_parser] script.characters: {len(script.characters)}, scenes: {len(script.scenes)}")
        characters = ctx.get("characters", [c.name for c in script.characters])
        print(f"[dialogue_parser] characters: {characters}")
        char_str = "、".join(characters) if characters else "(暂无)"

        if not characters and not script.characters:
            print("[dialogue_parser] 无角色，跳过对白解析")
            return script

        # 预分段，用于计算全局段落索引
        all_paragraphs = re.split(r"\n{2,}", novel_text)
        all_paragraphs = [p for p in all_paragraphs if p.strip()]

        for scene in script.scenes:
            print(f"[dialogue_parser] 处理场景: id={scene.scene_id}, title={scene.title}, location={scene.location}")
            # 取该场景对应的原文片段（简化：用场景标题在原文中定位）
            # V1 简化策略：直接把全文当作每个场景的输入
            text = novel_text[:3000]  # 防止超 Token

            text_with_numbers = self._add_paragraph_numbers(text)

            prompt = _USER_PROMPT_TPL.format(
                characters=char_str,
                scene_title=scene.title or f"场景{scene.scene_id}",
                scene_location=scene.location or "未知",
                text_with_paragraph_numbers=text_with_numbers,
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
                            "character": {"type": "string"},
                            "content": {"type": "string"},
                            "emotion": {"type": "string"},
                            "source_start": {"type": "integer"},
                            "source_end": {"type": "integer"},
                        },
                        "required": ["character", "content"],
                    },
                },
            )
            print(f"[dialogue_parser] LLM 返回 {len(raw)} 条对白: {raw}")

            for item in raw:
                print(f"[dialogue_parser] 处理 item: {item}, type={type(item).__name__}")
                # 构造 source_location
                source_loc = None
                start = item.get("source_start")
                end = item.get("source_end")
                if start is not None:
                    source_loc = SourceLocation(
                        chapter_index=0,  # V1 暂不区分章节
                        start_paragraph=int(start),
                        end_paragraph=int(end or start),
                        start_offset=0,
                        end_offset=0,
                    )

                scene.beats.append(
                    DialogueBeat(
                        character=item["character"],
                        content=item["content"],
                        emotion=item.get("emotion"),
                        source_location=source_loc,
                    )
                )

        return script
