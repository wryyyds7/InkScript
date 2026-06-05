"""StepProtocol：Pipeline Step 接口定义

所有 Pipeline Step 必须实现此 Protocol，
支持插件式扩展（importlib 动态加载）。
"""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Beat, Character, Scene, Script


@runtime_checkable
class StepProtocol(Protocol):
    """Pipeline Step 接口

    每个 Step 负责 Pipeline 中的一个处理阶段，
    输入中间状态（Script），输出更新后的 Script。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Step 名称（唯一标识，如 character_extractor）"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Step 描述（用于 UI 展示）"""
        ...

    @abstractmethod
    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict[str, Any],
    ) -> Script:
        """执行 Step

        Args:
            script: 当前剧本状态（可被修改或返回新对象）
            novel_text: 原始小说文本
            llm: LLM 客户端（调用 AI 用）
            ctx: 上下文（各 Step 之间共享数据）

        Returns:
            更新后的 Script
        """
        ...


# ─────────────────────────────────────────────
# Step 注册表（运行时动态注册）
# ─────────────────────────────────────────────
STEP_REGISTRY: dict[str, type[StepProtocol]] = {}


def register_step(name: str):
    """装饰器：注册 Step 类

    Usage:
        @register_step("character_extractor")
        class CharacterExtractorStep:
            ...
    """

    def decorator(cls: type[StepProtocol]) -> type[StepProtocol]:
        STEP_REGISTRY[name] = cls
        return cls

    return decorator


def load_step_from_file(filepath: Path) -> type[StepProtocol] | None:
    """从 Python 文件动态加载 Step 类

    规则：
    - 文件名作为 Step 名称（如 character_extractor.py → character_extractor）
    - 文件中必须有一个名为 `<ClassName>Step` 的类
    """
    import importlib.util, sys

    name = filepath.stem
    spec = importlib.util.spec_from_file_location(name, filepath)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    # 查找实现了 StepProtocol 的类
    for attr in dir(module):
        obj = getattr(module, attr)
        if (
            isinstance(obj, type)
            and hasattr(obj, "name")
            and hasattr(obj, "run")
        ):
            return obj  # type: ignore[return-value]
    return None
