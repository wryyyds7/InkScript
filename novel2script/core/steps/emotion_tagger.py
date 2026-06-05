"""情绪标注 Step

对已有 Beat 做情绪标注(补充 emotion 字段).
"""

from __future__ import annotations

import json

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import DialogueBeat, Script


_SYSTEM_PROMPT = """你是一个专业的剧本情绪分析 师.
对给定的对白内容,标注说话者的情绪.

情绪类别(可选):
happy / sad / angry / calm / excited / scared / surprised / sad
如果无法确定,返回 null.
"""

_USER_PROMPT_TPL = """## 对白内容

{content}

## 角色

{character}

## 要求

只输出一个 JSON 对象:{{"emotion": "happy"}} 或 {{"emotion": null}}
"""


@register_step("emotion_tagger")
class EmotionTaggerStep:
    """情绪标注 Step"""

    @property
    def name(self) -> str:
        return "emotion_tagger"

    @property
    def description(self) -> str:
        return "标注对白情绪"

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        for scene in script.scenes:
            for i, beat in enumerate(scene.beats):
                if isinstance(beat, DialogueBeat) and not beat.emotion:
                    prompt = _USER_PROMPT_TPL.format(
                        content=beat.content[:500],
                        character=beat.character,
                    )
                    raw = llm.chat_json(
                        messages=[
                            {"role": "system", "content": _SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        schema={
                            "type": "object",
                            "properties": {
                                "emotion": {
                                    "type": ["string", "null"],
                                    "enum": [
                                        "happy",
                                        "sad",
                                        "angry",
                                        "calm",
                                        "excited",
                                        "scared",
                                        "surprised",
                                        "sad",
                                        None,
                                    ],
                                }
                            },
                        },
                    )
                    emotion = raw.get("emotion")
                    if emotion:
                        beat.emotion = emotion

        return script
