"""长文本智能分段 Step

根据模型上下文长度自动计算阈值,
超出时分段处理,避免超出 LLM 上下文限制.
"""

from __future__ import annotations

import re
from typing import Any, dict

from novel2script.core.steps.base import BaseStep, register_step
from novel2script.schema import Script


@register_step("text_splitter")
class TextSplitterStep(BaseStep):
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
            处理后的 Script(如果文本不长,直接返回原 Script)
        """
        # 1. 获取模型上下文长度
        max_context = self._get_model_context_length(llm)

        # 2. 计算当前文本 token 数(粗略估算:1 个中文字符 ≈ 2 个 token)
        estimated_tokens = len(novel_text) * 2

        # 3. 如果未超出限制,直接返回
        if estimated_tokens <= max_context * 0.8:  # 保留 20% 余量
            return script

        # 4. 超出限制,进行智能分段
        segments = self._split_text(novel_text, max_context)

        # 5. 将分段信息存入上下文(供后续 Step 使用)
        if ctx is not None:
            ctx["text_segments"] = segments
            ctx["is_long_text"] = True

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
