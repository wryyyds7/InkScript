"""测试 Pipeline 核心"""

from novel2script.core.pipeline import Pipeline
from novel2script.core.steps.base import StepProtocol
from novel2script.schema import Script


class FakeStep:
    """用于测试的假 Step"""

    name = "fake_step"
    description = "假步骤"

    def run(self, script, novel_text, llm, ctx):
        script.meta.total_beats += 1
        return script


class TestPipeline:
    """测试 Pipeline"""

    def test_run_single_step(self):
        pipeline = Pipeline(steps=[FakeStep()])
        script = Script()
        result = pipeline.run(script, "")
        assert result.meta.total_beats == 1

    def test_run_multiple_steps(self):
        pipeline = Pipeline(steps=[FakeStep(), FakeStep()])
        script = Script()
        result = pipeline.run(script, "")
        assert result.meta.total_beats == 2

    def test_before_hook(self):
        calls = []
        pipeline = Pipeline(steps=[FakeStep()])
        pipeline.register_before_hook(lambda p, n, c: calls.append(n))
        pipeline.run(Script(), "")
        assert "fake_step" in calls

    def test_after_hook(self):
        calls = []
        pipeline = Pipeline(steps=[FakeStep()])
        pipeline.register_after_hook(lambda p, n, c: calls.append(n))
        pipeline.run(Script(), "")
        assert "fake_step" in calls
