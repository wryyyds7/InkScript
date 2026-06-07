"""对白解析 Step
将小说文本中的对白内容解析为 DialogueBeat.
支持长文本分段处理,逐段调用 LLM 并合并结果.
"""

from __future__ import annotations

import json
import re

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import BeatType, DialogueBeat, Script, SourceLocation




_SYSTEM_PROMPT = """你是一个专业的剧本解析师，需要将小说文本转换为结构化剧本。
你需要识别所有对白、动作描述、情绪变化，并标注镜头指示。

## 输出格式
输出一个 JSON 数组，每个元素是剧本中的一个 beat（节拍）。

## Beat 类型
- "dialogue": 角色对白（包含说话人、内容、情绪）
- "action": 动作/场景描述（包含镜头指示和动作内容）
- "narration": 旁白/内心独白

## 镜头指示（放在 action beat 的 content 中）
- 远景/中景/近景/特写/大特写
- 固定机位/缓慢推进/微仰角
- 叠化转场/闪回/淡出
- 冷色调/暖色调

## 情绪标注
从以下选择：happy/sad/angry/calm/excited/fear/surprised/confident/firm/cold/curious/mock/embarrassed

## 示例
输入文本：
```
荻原明靠在吊椅上，悠闲地翘着腿，温和帅气的脸上挂着浅笑。
荻原明：（微笑）怎么，决定好了吗，霞之丘小姐。
诗羽暗暗咬了咬牙，手指不自觉抓紧腿部内侧。
霞之丘诗羽：（低头，诚恳）抱歉，荻原先生，我反悔了。
```

输出：
```json
[
  {{"type": "action", "content": "（中景）荻原明靠在吊椅上，悠闲地翘着腿，手在藤椅扶手边缘轻敲，温和帅气的脸上挂着浅笑。"}},
  {{"type": "dialogue", "character": "荻原明", "content": "怎么，决定好了吗，霞之丘小姐。", "emotion": "calm", "source_start": 1, "source_end": 1}},
  {{"type": "action", "content": "（特写·手部）诗羽暗暗咬了咬牙，手指不自觉抓紧腿部内侧，指节发白。"}},
  {{"type": "dialogue", "character": "霞之丘诗羽", "content": "抱歉，荻原先生，我反悔了。", "emotion": "embarrassed", "source_start": 3, "source_end": 3}}
]
```

## 规则
1. 每个对话前后如有动作描述，单独提取为 action beat
2. 情绪从角色的动作和上下文推断，不要全部标 calm
3. 动作描述要包含原文中的细节（身体动作、表情变化等）
4. 中文引号「」"" 内通常为对白
5. source_start/source_end 标注对白在段落列表中的索引（从0开始）

只输出 JSON，不要输出其他内容。
"""

_USER_PROMPT_TPL = """## 角色列表

{characters}

## 场景

{scene_title}({scene_location})

## 文本片段（已按段落编号）

{text_with_paragraph_numbers}

## 要求

解析以上文本，输出 JSON 数组。每个元素是剧本中的一个 beat。
对白用 dialogue 类型，动作描述用 action 类型，内心独白用 narration 类型。
动作描述要包含原文中的细节和镜头指示（中景/近景/特写等）。
情绪要准确推断，不要全部标 calm。
"""

# 每个片段最大字符数（确保不会超出 LLM 上下文）
MAX_CHARS_PER_CHUNK = 8000


@register_step("dialogue_parser")
class DialogueParserStep:
    """对白解析 Step"""

    @property
    def name(self) -> str:
        return "dialogue_parser"

    @property
    def description(self) -> str:
        return "解析对白"

    def _add_paragraph_numbers(self, text: str, offset: int = 0) -> str:
        """给每个段落加上编号，帮助 LLM 定位 source_location

        Args:
            text: 文本
            offset: 段落编号偏移（用于多段处理时保持全局编号一致）

        Returns:
            编号后的文本
        """
        paragraphs = re.split(r"\n{2,}", text)
        numbered = []
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if para:
                numbered.append(f"[段落 {offset + i}] {para}")
        return "\n\n".join(numbered)

    def _count_paragraphs(self, text: str) -> int:
        """计算文本中的段落数"""
        paragraphs = re.split(r"\n{2,}", text)
        return len([p for p in paragraphs if p.strip()])

    def _split_text_into_chunks(self, text: str, max_chars: int) -> list[str]:
        """将文本分割成不超过 max_chars 的片段，尽量在段落边界分割

        Args:
            text: 待分割文本
            max_chars: 每段最大字符数

        Returns:
            文本片段列表
        """
        chunks: list[str] = []
        paragraphs = re.split(r"\n{2,}", text)
        paragraphs = [p for p in paragraphs if p.strip()]

        current = ""
        for para in paragraphs:
            if len(para) > max_chars:
                # 单个段落超长，先保存当前段，再分割超长段落
                if current:
                    chunks.append(current)
                    current = ""
                # 按句子分割超长段落
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i : i + max_chars])
                continue

            if len(current) + len(para) + 2 > max_chars:
                if current:
                    chunks.append(current)
                current = para
            else:
                current = current + "\n\n" + para if current else para

        if current:
            chunks.append(current)

        return chunks

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

        # 获取 text_splitter 的分段信息（如果存在）
        text_segments = ctx.get("text_segments", [novel_text])
        print(f"[dialogue_parser] 文本共 {len(text_segments)} 个分段")

        for scene in script.scenes:
            print(f"[dialogue_parser] 处理场景: id={scene.scene_id}, title={scene.title}, location={scene.location}")

            # 对该场景的所有文本分段逐一处理
            for seg_idx, segment_text in enumerate(text_segments):
                if not segment_text.strip():
                    continue

                # 如果该分段仍然很长，进一步切分
                chunks = self._split_text_into_chunks(segment_text, MAX_CHARS_PER_CHUNK)
                print(f"[dialogue_parser] 分段{seg_idx} 被切为 {len(chunks)} 个子块")

                paragraph_offset = 0  # 全局段落编号偏移
                for chunk_idx, chunk in enumerate(chunks):
                    if not chunk.strip():
                        continue

                    text_with_numbers = self._add_paragraph_numbers(
                        chunk, offset=paragraph_offset
                    )

                    prompt = _USER_PROMPT_TPL.format(
                        characters=char_str,
                        scene_title=scene.title or f"场景{scene.scene_id}",
                        scene_location=scene.location or "未知",
                        text_with_paragraph_numbers=text_with_numbers,
                    )

                    print(f"[dialogue_parser] 场景{scene.scene_id} 分段{seg_idx} 子块{chunk_idx} 调用LLM ({len(chunk)}字)...")
                    try:
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
                                        "type": {"type": "string", "enum": ["dialogue", "action", "narration"]},
                                        "character": {"type": "string"},
                                        "content": {"type": "string"},
                                        "emotion": {"type": "string"},
                                        "source_start": {"type": "integer"},
                                        "source_end": {"type": "integer"},
                                    },
                                    "required": ["type", "content"],
                                },
                            },
                        )
                    except Exception as e:
                        print(f"[dialogue_parser] LLM 调用失败: {e}，跳过该子块")
                        continue

                    print(f"[dialogue_parser] LLM 返回 {len(raw)} 条 beat")

                    for item in raw:
                        beat_type = item.get("type", "dialogue")

                        # 构造 source_location
                        source_loc = None
                        start = item.get("source_start")
                        end = item.get("source_end")
                        if start is not None:
                            source_loc = SourceLocation(
                                chapter_index=seg_idx,
                                start_paragraph=int(start),
                                end_paragraph=int(end or start),
                                start_offset=0,
                                end_offset=0,
                            )

                        if beat_type == "action":
                            from novel2script.schema import ActionBeat
                            scene.beats.append(
                                ActionBeat(
                                    content=item["content"],
                                    source_location=source_loc,
                                )
                            )
                        elif beat_type == "narration":
                            from novel2script.schema import NarrationBeat
                            scene.beats.append(
                                NarrationBeat(
                                    content=item["content"],
                                    source_location=source_loc,
                                )
                            )
                        else:
                            scene.beats.append(
                                DialogueBeat(
                                    character=item.get("character", "未知"),
                                    content=item["content"],
                                    emotion=item.get("emotion"),
                                    source_location=source_loc,
                                )
                            )

                    # 更新段落偏移

                    # 更新段落偏移
                    paragraph_offset += self._count_paragraphs(chunk)

        total_beats = sum(len(scene.beats) for scene in script.scenes)
        print(f"[dialogue_parser] 解析完成，共 {total_beats} 条对白")
        return script
