"""Pipeline 核心编排 + Hook 机制

负责按顺序执行 Step,并在每个 Step 前后
触发 Hook(用于 Skill 注入、日志、进度推送等).
"""

from __future__ import annotations

from typing import Any, Callable, List

from novel2script.core.steps.base import StepProtocol
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Script


# ── Hook 类型定义 ─────────────────────────────────────
HookFn = Callable[["Pipeline", str, dict[str, Any]], None]
"""Hook 函数签名:
    pipeline -> step_name -> ctx -> None, """


class Pipeline:
    """Pipeline 编排器

    按顺序执行 Step 列表,支持:
    - before_step / after_step Hook
    - ctx 在 Step 之间共享
    - 错误中断
    """

    def __init__(
        self,
        steps: list[StepProtocol] | None = None,
        llm: LLMClientProtocol | None = None,
    ):
        self.steps = steps or []
        self.llm = llm
        self.ctx: dict[str, Any] = {}  # Step 间共享上下文
        self._before_hooks: list[HookFn] = []
        self._after_hooks: list[HookFn] = []

    # ── Hook 注册 ──────────────────────────────
    def register_before_hook(self, fn: HookFn) -> None:
        """注册 Step 执行前 Hook"""
        self._before_hooks.append(fn)

    def register_after_hook(self, fn: HookFn) -> None:
        """注册 Step 执行后 Hook"""
        self._after_hooks.append(fn)

    def clear_hooks(self) -> None:
        """清除所有 Hook(主要用于测试)"""
        self._before_hooks.clear()
        self._after_hooks.clear()

    # ── Step 管理 ──────────────────────────────
    def add_step(self, step: StepProtocol) -> None:
        """追加 Step"""
        self.steps.append(step)

    def insert_step(self, index: int, step: StepProtocol) -> None:
        """在指定位置插入 Step"""
        self.steps.insert(index, step)

    def remove_step(self, name: str) -> None:
        """按名称移除 Step"""
        self.steps = [s for s in self.steps if s.name != name]

    # ── 执行 ──────────────────────────────────
    def run(self, script: Script, novel_text: str) -> Script:
        """执行完整 Pipeline

        Args:
            script: 初始剧本状态
            novel_text: 原始小说文本

        Returns:
            处理完成的 Script

        Raises:
            RuntimeError: 任意 Step 执行失败时抛出
        """
        current = script

        for step in self.steps:
            print(f"[Pipeline] 执行步骤: {step.name}")
            # before hooks
            for hook in self._before_hooks:
                try:
                    hook(self, step.name, self.ctx)
                except Exception as e:
                    print(f"[Pipeline] before_hook 失败: {e}")

            # 执行 step
            try:
                current = step.run(
                    script=current,
                    novel_text=novel_text,
                    llm=self.llm,
                    ctx=self.ctx,
                )
                print(f"[Pipeline] 步骤 {step.name} 完成")
            except Exception as exc:
                print(f"[Pipeline] 步骤 {step.name} 失败（跳过继续）: {exc}")
                # 失败时调用 error hooks 但继续执行后续步骤
                for hook in self._after_hooks:
                    try:
                        hook(self, step.name, self.ctx)
                    except Exception as e:
                        print(f"[Pipeline] after_hook 失败: {e}")
                continue

            # after hooks
            for hook in self._after_hooks:
                try:
                    hook(self, step.name, self.ctx)
                except Exception as e:
                    print(f"[Pipeline] after_hook 失败: {e}")

        return current

    async def run_async(self, script: Script, novel_text: str) -> Script:
        """异步执行 Pipeline(SSE 进度推送用)

        Step.run 仍是同步的(LLM 调用可异步),
        此处用 asyncio.to_thread 包装以释放事件循环.
        """
        import asyncio

        return await asyncio.to_thread(self.run, script, novel_text)


# ─────────────────────────────────────────────
# 工厂函数:根据 Step 名称列表构建 Pipeline
# ─────────────────────────────────────────────
def build_pipeline(
    step_names: list[str] | None = None,
    llm: LLMClientProtocol | None = None,
) -> Pipeline:
    """根据注册的 Step 类构建 Pipeline

    Args:
        step_names: Step 名称列表(按顺序);
                   为 None 时使用默认 Pipeline.
        llm: LLM 客户端实例.
    """
    from novel2script.core.steps.base import STEP_REGISTRY

    if step_names is None:
        step_names = [
            "text_splitter",          # 第一步：长文本智能分段
            "character_extractor",
            "scene_splitter",
            "dialogue_parser",
            "emotion_tagger",
            "yaml_generator",
        ]

    missing = [n for n in step_names if n not in STEP_REGISTRY]
    if missing:
        raise KeyError(f"以下 Step 未注册:{missing}")

    pipeline = Pipeline(llm=llm)
    for name in step_names:
        step_cls = STEP_REGISTRY[name]
        pipeline.add_step(step_cls())

    return pipeline
