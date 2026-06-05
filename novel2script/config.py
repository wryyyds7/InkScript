"""配置管理模块(AppConfig)

使用 pydantic-settings 实现类型安全的配置管理,
支持从 .env 文件、环境变量、JSON 配置文件加载.
"""

from pathlib import Path
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """应用配置(类型安全,支持环境变量覆盖)"""

    model_config = SettingsConfigDict(
        env_prefix="INKSCRIPT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 基础配置 ─────────────────────────────────────
    app_name: str = "InkScript"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── LLM 配置 ─────────────────────────────────────
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""  # 通过 keyring 加密存储,此处仅为占位
    llm_model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(0.3, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(4096, ge=1)
    llm_request_timeout: float = Field(60.0, ge=1.0)

    # ── 项目配置 ─────────────────────────────────────
    projects_dir: Path = Path.home() / ".novel2script" / "projects"
    max_novel_length: int = 100_000  # 支持的最大小说字数

    # ── 服务器配置 ───────────────────────────────────
    host: str = "127.0.0.1"
    port: int = Field(8000, ge=1024, le=65535)
    sse_heartbeat_interval: int = Field(15, ge=5, le=60)  # 秒

    # ── 日志配置 ─────────────────────────────────────
    log_level: str = "INFO"

    # ── 校验器 ───────────────────────────────────────
    @field_validator("projects_dir", mode="before")
    @classmethod
    def _ensure_projects_dir(cls, v):
        path = Path(v) if not isinstance(v, Path) else v
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("llm_base_url")
    @classmethod
    def _validate_base_url(cls, v):
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("llm_base_url 必须以 http:// 或 https:// 开头")
        return v.rstrip("/")


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """获取单例配置(带缓存)"""
    return AppConfig()


def reload_config() -> AppConfig:
    """重新加载配置(清除缓存)"""
    get_config.cache_clear()
    return get_config()
