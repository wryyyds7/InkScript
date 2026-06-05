"""场景分割 Step

将小说文本按场景切换分割成独立场景。
"""

from __future__ import annotations

import json

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Script


_SYSTEM_PROMPT = """你是一个专业的剧本场景分析师。
将小说文本按场景切换（时间/地点变化）分割成独立场景，输出 JSON 数组。

每个场景包含：
- title: 场景标题（简短描述）
- location: 地点
- time: 时间
"""

_USER_PROMPT_TPL = """## 小说文本

{segment_text}

## 已有角色列表

{characters}

## 要求

1. 按场景切换分割（地点/时间变化即为新场景）
2. 每个场景编号自动分配（从 {start_id} 开始）
3. 输出 JSON 数组，格式：
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
        char_str = "、".join(characters) if characters else "（暂无）"

        # 简单按章节或双换行分段
        import re
        segments = re.split(r"\n{2,}", novel_text)
        segments = [s.strip() for s in segments if s.strip()]

        script.scenes = []
        scene_id = 1

        for seg in segments:
            if not seg:
                continue
            prompt = _USER_PROMPT_TPL.format(
                segment_text=seg[:5000],  # 每段最多 5000 字
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
                            "title": s.get("title", ""),
                            "location": s.get("location", ""),
                            "time": s.get("time", ""),
                            "beats": [],
                        }
                    )
                )
                scene_id += 1

        return script
