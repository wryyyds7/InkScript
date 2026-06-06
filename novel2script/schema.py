"""Pydantic 数据模型(Tagged Union Beat)

定义剧本 YAML 的 Python 表示,
使用 Pydantic V2 做类型校验和序列化.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────
# BeatType:Beat 类型枚举(字符串字面量)
# ─────────────────────────────────────────────
class BeatType:
    DIALOGUE = "dialogue"
    ACTION = "action"
    NARRATION = "narration"


# ─────────────────────────────────────────────
# 基础 Beat(内部使用,不直接暴露)
# ─────────────────────────────────────────────
class SourceLocation(BaseModel):
    """原文位置映射（用于滚动联动）"""

    model_config = {"extra": "forbid"}

    chapter_index: int = Field(..., description="章节序号（从 0 开始）")
    start_paragraph: int = Field(..., description="起始段落索引（按双换行切分）")
    end_paragraph: int = Field(..., description="结束段落索引")
    start_offset: int = Field(0, description="段落内起始字符偏移")
    end_offset: int = Field(0, description="段落内结束字符偏移")


class BaseBeat(BaseModel):
    """所有 Beat 的基类(不直接使用)"""

    model_config = {"extra": "forbid"}

    source_location: SourceLocation | None = Field(
        None,
        description="原文定位：chapter_index + paragraph range + offset",
    )


# ─────────────────────────────────────────────
# 3 种 Beat(Tagged Union 成员)
# ─────────────────────────────────────────────
class DialogueBeat(BaseBeat):
    """对白 Beat:角色说话内容"""

    type: Literal[BeatType.DIALOGUE] = BeatType.DIALOGUE
    character: str = Field(..., description="角色名称,必须存在于角色列表中")
    content: str = Field(..., description="对白内容")
    emotion: str | None = Field(None, description="情绪标签(可选)")

    # V1 扩展字段(可选)
    volume: str | None = Field(None, description="音量:whisper | normal | shout")
    speed: str | None = Field(None, description="语速:slow | normal | fast")

    # 自动设置 type 默认值
    @model_validator(mode="before")
    @classmethod
    def _set_default_type(cls, data: dict) -> dict:
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.DIALOGUE
        return data


class ActionBeat(BaseBeat):
    """动作 Beat:描述动作、表情、场景变化"""

    type: Literal[BeatType.ACTION] = BeatType.ACTION
    content: str = Field(..., description="动作描述")
    duration: float | None = Field(None, description="预估持续时间(秒)")

    @model_validator(mode="before")
    @classmethod
    def _set_default_type(cls, data: dict) -> dict:
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.ACTION
        return data


class NarrationBeat(BaseBeat):
    """旁白 Beat:描述场景、氛围、心理活动"""

    type: Literal[BeatType.NARRATION] = BeatType.NARRATION
    content: str = Field(..., description="旁白内容")
    speaker: str | None = Field(None, description="旁白配音角色(可选)")

    @model_validator(mode="before")
    @classmethod
    def _set_default_type(cls, data: dict) -> dict:
        if isinstance(data, dict) and "type" not in data:
            data["type"] = BeatType.NARRATION
        return data


# ─────────────────────────────────────────────
# Beat Union(Tagged Union,YAML 靠 `type` 字段分发)
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
    voice_profile: str | None = Field(None, description="声音配置(TTS 用)")
    emotion_distribution: dict[str, float] = Field(default_factory=dict, description="情绪分布（用于雷达图）：happy/sad/angry/calm/excited/fear -> 0.0-1.0")


# ─────────────────────────────────────────────
# 场景模型
# ─────────────────────────────────────────────
class Scene(BaseModel):
    """场景信息"""

    model_config = {"extra": "ignore"}

    scene_id: int = Field(..., description="场景编号(从 1 开始)")
    title: str = Field("", description="场景标题")
    location: str = Field("", description="场景地点")
    time: str = Field("", description="场景时间")
    beats: list[Beat] = Field(default_factory=list, description="场景内的 Beat 列表")


# ─────────────────────────────────────────────
# 编辑元数据（编辑器状态）
# ─────────────────────────────────────────────
class OperationLog(BaseModel):
    """操作日志：记录每次编辑操作（用于逐句修改历史）"""

    model_config = {"extra": "forbid"}

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="操作时间")
    user: str = Field("user", description="操作用户（预留多人协作）")
    action: str = Field(..., description="操作类型：create_beat | update_beat | delete_beat | update_novel")
    beat_id: str | None = Field(None, description="关联的 Beat ID（如果是 Beat 操作）")
    field: str | None = Field(None, description="修改的字段名（如 character, content, emotion）")
    old_value: str | None = Field(None, description="修改前的值")
    new_value: str | None = Field(None, description="修改后的值")
    scene_id: str | None = Field(None, description="关联的场景 ID")


class EditMeta(BaseModel):
    """编辑器元数据：保存用户编辑器的滚动位置、展开状态等"""

    model_config = {"extra": "ignore"}

    # 编辑器滚动位置
    novel_scroll_top: float = Field(0.0, description="小说编辑器滚动位置")
    script_scroll_top: float = Field(0.0, description="剧本编辑器滚动位置")

    # 光标位置
    novel_cursor_pos: int | None = Field(None, description="小说编辑器光标位置")
    script_cursor_pos: int | None = Field(None, description="剧本编辑器光标位置")

    # UI 状态
    left_panel_visible: bool = Field(True, description="左面板是否可见")
    right_panel_visible: bool = Field(True, description="右面板是否可见")
    panel_ratio: float = Field(50.0, description="左右分栏比例（左侧占比%）")

    # 当前激活的面板
    active_panel: str = Field("novel", description="当前激活的面板（novel/script）")

    # 展开/折叠状态
    guide_expanded: bool = Field(True, description="使用指南是否展开")
    version_panel_visible: bool = Field(False, description="版本历史面板是否可见")
    skill_panel_visible: bool = Field(False, description="Skill 面板是否可见")

    # 操作日志（逐句修改历史）
    operation_log: list[OperationLog] = Field(default_factory=list, description="操作日志列表")

    # 最后更新时间
    last_updated: datetime | None = Field(None, description="最后更新时间")


# ─────────────────────────────────────────────
# 剧本元数据
# ─────────────────────────────────────────────
class ScriptMeta(BaseModel):
    """剧本元数据(向前兼容:extra=ignore)"""

    model_config = {"extra": "ignore", "protected_namespaces": ()}

    version: str = "1.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_name: str = ""  # 使用的 LLM 模型
    source_location_enabled: bool = True

    # 统计信息
    total_beats: int = 0
    dialogue_count: int = 0
    action_count: int = 0
    narration_count: int = 0

    # 角色列表(去重)
    characters: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# 完整剧本
# ─────────────────────────────────────────────
class Script(BaseModel):
    """完整剧本(YAML 根对象)"""

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

    # 自定义表示:让 type 字段排在最前面
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
