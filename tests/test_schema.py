"""测试 Pydantic 数据模型"""

from novel2script.schema import (
    DialogueBeat,
    ActionBeat,
    NarrationBeat,
    Character,
    Scene,
    Script,
    to_yaml,
    from_yaml,
)


class TestBeats:
    """测试 Beat 模型"""

    def test_dialogue_beat(self):
        b = DialogueBeat(character="李雷", content="你好")
        assert b.type == "dialogue"
        assert b.character == "李雷"

    def test_action_beat(self):
        b = ActionBeat(content="走进教室")
        assert b.type == "action"

    def test_narration_beat(self):
        b = NarrationBeat(content="阳光洒进教室")
        assert b.type == "narration"


class TestScript:
    """测试 Script 序列化和反序列化"""

    def test_to_yaml_roundtrip(self):
        script = Script(
            characters=[Character(name="李雷")],
            scenes=[
                Scene(
                    scene_id=1,
                    title="教室",
                    beats=[DialogueBeat(character="李雷", content="你好")],
                )
            ],
        )
        yaml_str = to_yaml(script)
        script2 = from_yaml(yaml_str)
        assert script2.meta.total_beats == 1
        assert script2.scenes[0].beats[0].content == "你好"

    def test_stats_calculation(self):
        script = Script(
            scenes=[
                Scene(
                    scene_id=1,
                    beats=[
                        DialogueBeat(character="A", content="hi"),
                        ActionBeat(content="walk"),
                        NarrationBeat(content="sunny"),
                    ],
                )
            ]
        )
        assert script.meta.dialogue_count == 1
        assert script.meta.action_count == 1
        assert script.meta.narration_count == 1
