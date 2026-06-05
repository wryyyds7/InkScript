"""角色识别 Step

从小说文本中提取所有角色信息.
"""

from __future__ import annotations

import json
import re

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Character, Script


_SYSTEM_PROMPT = """你是一个专业的剧本角色分析师.
从小说文本中识别所有有对白的角色,输出 JSON 数组.

每个角色包含:
- name: 角色名称(必需)
- aliases: 别名列表(可选)
- description: 简短描述(可选)

只输出 JSON,不要输出其他内容.
"""

_USER_PROMPT_TPL = """## 小说文本

{novel_text}

## 要求

1. 识别所有有对白的角色(至少说过一句话)
2. 合并同一角色的不同称呼(放入 aliases)
3. 输出 JSON 数组,格式:
```json
[
  {{"name": "李雷", "aliases": ["小李", "雷子"], "description": "男主角,高中生"}}
]
```
"""


@register_step("character_extractor")
class CharacterExtractorStep:
    """角色识别 Step"""

    @property
    def name(self) -> str:
        return "character_extractor"

    @property
    def description(self) -> str:
        return "识别小说中的角色"

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        # 分段处理(防止超 Token)
        max_chars = 20_000
        segments = [
            novel_text[i : i + max_chars]
            for i in range(0, len(novel_text), max_chars)
        ]

        all_chars: list[dict] = []
        seen: set[str] = set()

        for seg in segments:
            prompt = _USER_PROMPT_TPL.format(novel_text=seg)
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
                            "name": {"type": "string"},
                            "aliases": {"type": "array", "items": {"type": "string"}},
                            "description": {"type": "string"},
                        },
                        "required": ["name"],
                    },
                },
            )
            for c in raw:
                nm = c.get("name", "").strip()
                if nm and nm not in seen:
                    seen.add(nm)
                    all_chars.append(c)

        # 写入 Script
        script.characters = [
            Character(
                name=c["name"],
                aliases=c.get("aliases", []),
                description=c.get("description", ""),
            )
            for c in all_chars
        ]

        # 存入 ctx 供后续 Step 使用
        ctx["characters"] = [c.name for c in script.characters]
        return script
