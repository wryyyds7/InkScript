"""测试配置管理模块"""

from novel2script.config import AppConfig, get_config


class TestAppConfig:
    """测试 AppConfig"""

    def test_default_values(self):
        cfg = AppConfig(llm_api_key="test-key")
        assert cfg.app_name == "InkScript"
        assert cfg.llm_model_name == "gpt-4o-mini"
        assert cfg.port == 8000

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("INKSCRIPT_LLM_MODEL_NAME", "gpt-4")
        cfg = AppConfig(llm_api_key="test")
        assert cfg.llm_model_name == "gpt-4"

    def test_validate_base_url(self):
        from pydantic import ValidationError

        try:
            AppConfig(llm_base_url="ftp://example.com")
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass

    def test_get_config_singleton(self):
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2
