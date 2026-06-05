"""Pydantic 数据模型（Tagged Union Beat）

定义剧本 YAML 的 Python 表示，
使用 Pydantic V2 做类型校验和序列化。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────
# BeatType：Beat 类型枚举（字符串字面量）
# ─────────────────────────────────────────────
class BeatType:
    DIALOGUE = "dialogue"
    ACTION = "action"
    NARRATION = "narration"


# ─────────────────────────────────────────────
# 基础 Beat（内部使用，不直接暴露）
# ─────────────────────────────────────────────
class BaseBeat(BaseModel):
    """所有 Beat 的基类（不直接使用）"""

    model_config = {"extra": "forbid"}

    source_location: dict[str, Any] | None = Field(
        None,
        description="原文定位：{chapter, paragraph, sentence}",
    )


# ─────────────────────────────────────────────
# 3 种 Beat（Tagged Union 成员）
# ─────────────────────────────────────────────
class DialogueBeat(BaseBeat):
    """对白 Beat：角色说话内容"""

    type: Literal[BeatType.DIALOGUE] = BeatType.DIALOGUE
    character: str = Field(..., description="角色名称，必须存在于角色列表中")
    content: str = Field(..., description="对白内容")
    emotion: str | None = Field(None, description="情绪标签（可选）")

    # V1 扩展字段（可选）
    volume: str | None = Field(None, description="音量：whisper | normal | shout")
    speed: str | None = Field(None, description="语速：slow | normal | fast")

    # 自动设置 type 默认值
    @model_validator(mode="before")
    @classmethod
    def _set_default_type(cls, data: dict) -> dict:
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.DIALOGUE
        return data


class ActionBeat(BaseBeat):
    """动作 Beat：描述动作、表情、场景变化"""

    type: Literal[BeatType.ACTION] = BeatType.ACTION
    content: str = Field(..., description="动作描述")
    duration: float | None = Field(None, description="预估持续时间（秒）")

    @model_validator(mode="before")
    @classmethod
    def _set_default_type(cls, data: dict) -> dict:
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.ACTION
        return data


class NarrationBeat(BaseBeat):
    """旁白 Beat：描述场景、氛围、心理活动"""

    type: Literal[BeatType.NARRATION] = BeatType.NARRATION
    content: str = Field(..., description="旁白内容")
    speaker: str | None = Field(None, description="旁白配音角色（可选）")

    @model_validator(mode="before")
    @classmethod
    def _set_default_type(cls, data: dict) -> dict:
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.NARRATION
        return data


# ─────────────────────────────────────────────
# Beat Union（Tagged Union，YAML 靠 `type` 字段分发）
# ─────────────────────────────────────────────
Beat = Union[DialogueBeat, ActionBeat, NarrationBeat]


# ─────────────────────────────────────────────
# 角色模型
# ─────────────────────────────────────────────
class Character(BaseModel):
    """角色信息"""

    model_config = {"extra": "ignore"}

    name: str = Field(..., description="角色名称")
    aliases: list[str] = Field(default_factory=list, description="别名列表")
    description: str = Field("", description="角色描述")
    voice_profile: str | None = Field(None, description="声音配置（TTS 用）")


# ─────────────────────────────────────────────
# 场景模型
# ─────────────────────────────────────────────
class Scene(BaseModel):
    """场景信息"""

    model_config = {"extra": "ignore"}

    scene_id: int = Field(..., description="场景编号（从 1 开始）")
    title: str = Field("", description="场景标题")
    location: str = Field("", description="场景地点")
    time: str = Field("", description="场景时间")
    beats: list[Beat] = Field(default_factory=list, description="场景内的 Beat 列表")


# ─────────────────────────────────────────────
# 剧本元数据
# ─────────────────────────────────────────────
class ScriptMeta(BaseModel):
    """剧本元数据（向前兼容：extra=ignore）"""

    model_config = {"extra": "ignore"}

    version: str = "1.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_name: str = ""  # 使用的 LLM 模型
    source_location_enabled: bool = True

    # 统计信息
    total_beats: int = 0
    dialogue_count: int = 0
    action_count: int = 0
    narration_count: int = 0

    # 角色列表（去重）
    characters: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# 完整剧本
# ─────────────────────────────────────────────
class Script(BaseModel):
    """完整剧本（YAML 根对象）"""

    model_config = {"extra": "ignore"}

    meta: ScriptMeta = Field(default_factory=ScriptMeta)
    characters: list[Character] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """初始化后自动计算统计信息"""
        self._update_stats()

    def _update_stats(self) -> None:
        """更新统计信息"""
        beats: list[Beat] = []
        for scene in self.scenes:
            beats.extend(scene.beats)

        self.meta.total_beats = len(beats)
        self.meta.dialogue_count = sum(1 for b in beats if isinstance(b, DialogueBeat))
        self.meta.action_count = sum(1 for b in beats if isinstance(b, ActionBeat))
        self.meta.narration_count = sum(1 for b in beats if isinstance(b, NarrationBeat))
        self.meta.characters = list({b.character for b in beats if isinstance(b, DialogueBeat)})


# ─────────────────────────────────────────────
# YAML 辅助函数
# ─────────────────────────────────────────────
def to_yaml(script: Script) -> str:
    """将 Script 序列化为 YAML 字符串"""
    import yaml

    # 自定义表示：让 type 字段排在最前面
    class _TaggedDumper(yaml.SafeDumper):
        pass

    def _repr_beat(dumper: _TaggedDumper, beat: BaseModel) -> yaml.MappingNode:
        data = beat.model_dump(exclude_none=True, mode="json")
        # type 排第一
        ordered = {"type": data.pop("type")} | data
        return dumper.represent_mapping("tag:yaml.org,2002:map", ordered)

    for cls in (DialogueBeat, ActionBeat, NarrationBeat):
        _TaggedDumper.add_representer(cls, _repr_beat)  # type: ignore[arg-type]

    return yaml.dump(
        script.model_dump(exclude_none=True, mode="json"),
        Dumper=_TaggedDumper,
        allow_unicode=True,
        sort_keys=False,
    )


def from_yaml(yaml_str: str) -> Script:
    """从 YAML 字符串解析 Script"""
    import yaml

    raw = yaml.safe_load(yaml_str)
    return Script.model_validate(raw)
