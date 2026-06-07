"""Steps package: Pipeline Step 插件目录 — 自动注册"""

from novel2script.core.steps.character_extractor import CharacterExtractorStep
from novel2script.core.steps.scene_splitter import SceneSplitterStep
from novel2script.core.steps.dialogue_parser import DialogueParserStep
from novel2script.core.steps.emotion_tagger import EmotionTaggerStep
from novel2script.core.steps.yaml_generator import YamlGeneratorStep
from novel2script.core.steps.base import STEP_REGISTRY

# 自动注册所有 Step
STEP_REGISTRY["character_extractor"] = CharacterExtractorStep
STEP_REGISTRY["scene_splitter"] = SceneSplitterStep
STEP_REGISTRY["dialogue_parser"] = DialogueParserStep
STEP_REGISTRY["emotion_tagger"] = EmotionTaggerStep
STEP_REGISTRY["yaml_generator"] = YamlGeneratorStep
