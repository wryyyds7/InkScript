"""对白解析 Step

将小说文本中的对白内容解析为 DialogueBeat。
"""

from __future__ import annotations

import json
import re

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import BeatType, DialogueBeat, Script


_SYSTEM_PROMPT = """你是一个专业的剧本对白解析师。
从小说文本中识别所有对白，输出 JSON 数组。

每个对白包含：
- character: 说话角色名称
- content: 对白内容
- emotion: 情绪（可选，如 happy/sad/angry/calm）
"""

_USER_PROMPT_TPL = """## 角色列表

{characters}

## 场景

{scene_title}（{scene_location}）

## 文本片段

{text}

## 要求

1. 只识别已知角色的对白
2. 中文引号「」""''内通常为对白
3. 输出 JSON 数组，格式：
```json
[
  {{"character": "李雷", "content": "你好", "emotion": "happy"}}
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

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        characters = ctx.get("characters", [c.name for c in script.characters])
        char_str = "、".join(characters) if characters else "（暂无）"

        for scene in script.scenes:
            # 取该场景对应的原文片段（简化：用场景标题在原文中定位）
            # V1 简化策略：直接把全文当作每个场景的输入
            text = novel_text[:3000]  # 防止超 Token

            prompt = _USER_PROMPT_TPL.format(
                characters=char_str,
                scene_title=scene.title or f"场景{scene.scene_id}",
                scene_location=scene.location or "未知",
                text=text,
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
                        },
                        "required": ["character", "content"],
                    },
                },
            )

            for item in raw:
                scene.beats.append(
                    DialogueBeat(
                        character=item["character"],
                        content=item["content"],
                        emotion=item.get("emotion"),
                    )
                )

        return script
