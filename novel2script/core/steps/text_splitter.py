"""长文本智能分段 Step

根据模型上下文长度自动计算阈值,
超出时分段处理,避免超出 LLM 上下文限制.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.schema import Script


@register_step("text_splitter")
class TextSplitterStep:
    """长文本智能分段 Step

    功能:
    1. 检测文本长度是否超出模型上下文限制
    2. 如果超出,按章节/段落智能分段
    3. 分段时保持语义完整性(优先在章节边界分割)
    """

    name = "text_splitter"
    description = "长文本智能分段"

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: Any = None,
        ctx: dict[str, Any] | None = None,
    ) -> Script:
        """执行长文本分段

        Args:
            script: 当前剧本状态
            novel_text: 小说原文
            llm: LLM 客户端(用于获取上下文长度)
            ctx: 上下文字典

        Returns:
            处理后的 Script
        """
        # 1. 获取模型上下文长度
        max_context = self._get_model_context_length(llm)

        # 2. 安全阈值：每个 segment 建议最大字符数
        #    保守估算：1 token ≈ 0.5 个中文字符
        safe_chars_per_segment = int(max_context * 0.5 * 0.7)  # 保留 30% 余量给 prompt 和输出

        # 3. 无论文本长短，都进行分段（保证后续 Step 能统一处理）
        segments = self._split_text_by_chapters_and_length(novel_text, safe_chars_per_segment)

        # 4. 将分段信息存入上下文(供后续 Step 使用)
        if ctx is not None:
            ctx["text_segments"] = segments
            ctx["is_long_text"] = len(segments) > 1
            ctx["segment_threshold"] = safe_chars_per_segment

        return script

    def _get_model_context_length(self, llm: Any) -> int:
        """获取模型上下文长度

        Returns:
            上下文长度(token 数)
        """
        # 默认使用 8K 上下文
        default_context = 8192

        if llm is None:
            return default_context

        # 尝试从 LLM 客户端获取模型信息
        try:
            model_name = getattr(llm, "model_name", "")
            
            # 常见模型的上下文长度映射
            context_map = {
                "gpt-4": 128000,
                "gpt-4o": 128000,
                "gpt-4-turbo": 128000,
                "gpt-3.5": 16384,
                "claude": 200000,
                "qwen": 32768,
                "gemini": 32768,
                "deepseek": 16384,
            }

            for key, value in context_map.items():
                if key in model_name.lower():
                    return value

        except Exception:
            pass

        return default_context

    def _split_text_by_chapters_and_length(
        self, text: str, max_chars_per_segment: int
    ) -> list[str]:
        """智能分段文本：优先在章节边界分割，保证语义完整

        策略：
        1. 先按章节标题分割
        2. 如果某章仍然超过 max_chars_per_segment，按段落进一步分割
        3. 如果某段落还是超长，按句子分割（兜底）

        Args:
            text: 待分段文本
            max_chars_per_segment: 每段最大字符数

        Returns:
            分段列表（保持语义完整性）
        """
        segments: list[str] = []

        # ── 策略1：按章节标题分割 ──
        chapter_patterns = [
            r"第[一二三四五六七八九十百千\d]+章[^\n]*",
            r"第[一二三四五六七八九十百千\d]+节[^\n]*",
            r"Chapter\s+\d+[^\n]*",
            r"第\d+章[^\n]*",
            r"【[^】]+】",
            r"#+\s+.+",  # Markdown 标题
        ]

        chapters: list[str] = [text]  # 默认整篇
        for pattern in chapter_patterns:
            parts = re.split(f"({pattern})", text)
            if len(parts) >= 3:  # 至少匹配到1个标题
                chapters = []
                current = ""
                for part in parts:
                    if not part:
                        continue
                    if re.match(pattern, part):
                        # 新章节开始
                        if current:
                            chapters.append(current)
                        current = part
                    else:
                        current += part
                if current:
                    chapters.append(current)
                break  # 使用第一个匹配到的模式

        # ── 策略2：对每章，按 max_chars 再分割 ──
        for chapter in chapters:
            if len(chapter) <= max_chars_per_segment:
                segments.append(chapter)
            else:
                # 按双换行分割段落
                sub_segments = self._split_by_paragraphs(
                    chapter, max_chars_per_segment
                )
                segments.extend(sub_segments)

        return segments

    def _split_by_paragraphs(
        self, text: str, max_chars: int
    ) -> list[str]:
        """按段落分割文本，每段不超过 max_chars

        Args:
            text: 待分割文本
            max_chars: 每段最大字符数

        Returns:
            段落分段列表
        """
        result: list[str] = []
        paragraphs = text.split("\n\n")
        current = ""

        for para in paragraphs:
            if not para.strip():
                continue

            # 如果当前段落本身超长，按句子分割
            if len(para) > max_chars:
                if current:
                    result.append(current)
                    current = ""
                sub = self._split_by_sentences(para, max_chars)
                result.extend(sub)
                continue

            if len(current) + len(para) + 2 > max_chars:
                if current:
                    result.append(current)
                current = para
            else:
                current = current + "\n\n" + para if current else para

        if current:
            result.append(current)

        return result

    def _split_by_sentences(
        self, text: str, max_chars: int
    ) -> list[str]:
        """按句子分割（兜底策略）

        Args:
            text: 待分割文本
            max_chars: 每段最大字符数

        Returns:
            句子分段列表
        """
        result: list[str] = []
        # 按句号、问号、感叹号、省略号分割
        sentences = re.split(r"(?<=[。！？…\.!\?])", text)
        current = ""

        for sent in sentences:
            if not sent.strip():
                continue

            # 单个句子超长，硬切
            if len(sent) > max_chars:
                if current:
                    result.append(current)
                    current = ""
                for i in range(0, len(sent), max_chars):
                    result.append(sent[i : i + max_chars])
                continue

            if len(current) + len(sent) > max_chars:
                if current:
                    result.append(current)
                current = sent
            else:
                current += sent

        if current:
            result.append(current)

        return result

    def _split_text(self, text: str, max_context: int) -> list[str]:
        """智能分段文本

        Args:
            text: 待分段文本
            max_context: 每段最大 token 数

        Returns:
            分段列表
        """
        # 计算每段最大字符数(保守估算:1 token ≈ 1.5 个中文字符)
        max_chars = int(max_context * 1.5)

        segments = []

        # 1. 尝试按章节分割
        chapter_pattern = r"第[一二三四五六七八九十百千\d]+章"
        chapters = re.split(f"({chapter_pattern})", text)

        current_segment = ""
        for i, part in enumerate(chapters):
            if not part:
                continue

            # 如果当前段加上新部分超出限制,先保存当前段
            if len(current_segment) + len(part) > max_chars:
                if current_segment:
                    segments.append(current_segment)
                current_segment = part
            else:
                current_segment += part

        # 保存最后一段
        if current_segment:
            segments.append(current_segment)

        # 2. 如果按章节分割后仍有超长段,按段落分割
        final_segments = []
        for segment in segments:
            if len(segment) <= max_chars:
                final_segments.append(segment)
            else:
                # 按双换行分割段落
                paragraphs = segment.split("\n\n")
                current_para = ""
                for para in paragraphs:
                    if len(current_para) + len(para) > max_chars:
                        if current_para:
                            final_segments.append(current_para)
                        current_para = para
                    else:
                        current_para += "\n\n" + para if current_para else para

                if current_para:
                    final_segments.append(current_para)

        return final_segments
