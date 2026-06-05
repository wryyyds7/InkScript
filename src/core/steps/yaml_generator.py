"""YAML 生成 Step

将 Script 对象序列化为 YAML 字符串并写回 Script.meta。
"""

from __future__ import annotations

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Script, to_yaml


@register_step("yaml_generator")
class YamlGeneratorStep:
    """YAML 生成 Step（最终步骤）"""

    @property
    def name(self) -> str:
        return "yaml_generator"

    @property
    def description(self) -> str:
        return "生成最终 YAML 剧本"

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        # 更新元数据统计
        script.meta.generated_at = __import__("datetime").datetime.utcnow()
        script.meta.model_name = ctx.get("model_name", "unknown")

        # to_yaml() 已在 schema.py 中实现
        yaml_str = to_yaml(script)

        # 存入 ctx 供后续（SSE / 下载）使用
        ctx["yaml_output"] = yaml_str

        # 标记完成
        ctx["pipeline_status"] = "completed"
        return script
