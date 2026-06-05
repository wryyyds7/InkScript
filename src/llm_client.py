"""LLM 客户端封装（LLMClientProtocol）

统一 LLM 调用接口，支持重试、超时、错误处理。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from datetime import datetime

from openai import OpenAI
from novel2script.config import get_config


@runtime_checkable
class LLMClientProtocol(Protocol):
    """LLM 客户端接口（可替换为 Mock / 其他实现）"""

    def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str: ...
    def chat_json(
        self,
        messages: list[dict[str, str]],
        schema: dict,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict: ...


class OpenAIClient:
    """基于 openai SDK 的 LLM 客户端实现"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout: float | None = None,
    ):
        cfg = get_config()
        self.model_name = model_name or cfg.llm_model_name
        self.timeout = timeout or cfg.llm_request_timeout
        self._client = OpenAI(
            base_url=base_url or cfg.llm_base_url,
            api_key=api_key or cfg.llm_api_key or "sk-placeholder",
            timeout=self.timeout,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        cfg = get_config()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else cfg.llm_temperature,
            "max_tokens": max_tokens or cfg.llm_max_tokens,
            "timeout": timeout or self.timeout,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = self._client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        return content

    def chat_json(
        self,
        messages: list[dict[str, str]],
        schema: dict,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """调用 LLM 并要求返回符合 JSON Schema 的 JSON 字符串"""
        import json

        # 构造 system prompt 注入 JSON Schema 约束
        schema_str = json.dumps(schema, ensure_ascii=False)
        constrained_messages = list(messages)
        if constrained_messages and constrained_messages[0]["role"] == "system":
            constrained_messages[0]["content"] += (
                f"\n\n你必须严格按照以下 JSON Schema 返回 JSON：\n{schema_str}"
            )
        else:
            constrained_messages.insert(
                0,
                {
                    "role": "system",
                    "content": f"你必须严格按照以下 JSON Schema 返回 JSON：\n{schema_str}",
                },
            )

        raw = self.chat(
            constrained_messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 尝试提取 JSON（防止 LLM 返回 markdown 代码块）
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)


def get_llm_client() -> OpenAIClient:
    """工厂函数：获取 LLM 客户端实例"""
    return OpenAIClient()
