"""配置管理模块(AppConfig)
使用 pydantic-settings 实现类型安全的配置管理,
支持从 .env 文件、环境变量、JSON 配置文件加载.
"""

from pathlib import Path
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet
import base64
import os
import json


def _get_encryption_key() -> bytes:
    """获取或创建加密密钥"""
    key_file = Path.home() / ".novel2script" / ".key"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    
    if key_file.exists():
        return base64.urlsafe_b64decode(key_file.read_text().strip())
    else:
        key = Fernet.generate_key()
        key_file.write_text(base64.urlsafe_b64encode(key).decode())
        key_file.chmod(0o600)  # 只有用户可读写
        return key


def encrypt_api_key(api_key: str) -> str:
    """加密 API Key"""
    if not api_key:
        return ""
    
    key = _get_encryption_key()
    f = Fernet(base64.urlsafe_b64encode(key))
    encrypted = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key"""
    if not encrypted_key:
        return ""
    
    try:
        key = _get_encryption_key()
        f = Fernet(base64.urlsafe_b64encode(key))
        decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_key))
        return decrypted.decode()
    except Exception:
        return ""


class AppConfig(BaseSettings):
    """应用配置(类型安全,支持环境变量覆盖)"""

    model_config = SettingsConfigDict(
        env_prefix="INKSCRIPT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 基础配置 ────────────────────────────────────
    app_name: str = "InkScript"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── LLM 配置 ────────────────────────────────────
    llm_provider: str = "openai"  # openai, deepseek, anthropic, qwen, gemini, custom
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""  # 通过 cryptography 加密存储,此处仅为占位
    llm_model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(0.7, ge=0.0, le=2.0)
    llm_top_p: float = Field(1.0, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(4096, ge=1)
    llm_frequency_penalty: float = Field(0.0, ge=0.0, le=2.0)
    llm_presence_penalty: float = Field(0.0, ge=0.0, le=2.0)
    llm_request_timeout: float = Field(60.0, ge=1.0)
    llm_max_retries: int = Field(3, ge=0)
    llm_request_interval: float = Field(0.5, ge=0.0)

    # ── 项目配置 ────────────────────────────────────
    projects_dir: Path = Path.home() / ".novel2script" / "projects"
    max_novel_length: int = 100_000  # 支持的最大小说字数

    # ── 服务器配置 ──────────────────────────────────
    host: str = "127.0.0.1"
    port: int = Field(8000, ge=1024, le=65535)
    sse_heartbeat_interval: int = Field(15, ge=5, le=60)  # 秒

    # ── 日志配置 ────────────────────────────────────
    log_level: str = "INFO"

    # ── 校验器 ─────────────────────────────────────
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

    def save_api_key(self, api_key: str):
        """加密并保存 API Key"""
        encrypted = encrypt_api_key(api_key)
        self.llm_api_key = encrypted
        
        # 保存到配置文件
        config_file = Path.home() / ".novel2script" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {}
        if config_file.exists():
            config_data = json.loads(config_file.read_text(encoding="utf-8"))
        
        config_data["llm_api_key"] = encrypted
        config_file.write_text(
            json.dumps(config_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_decrypted_api_key(self) -> str:
        """获取解密的 API Key"""
        if not self.llm_api_key:
            return ""
        return decrypt_api_key(self.llm_api_key)


@lru_cache(maxsize=1)
# 获取单例配置(带缓存)
def get_config() -> AppConfig:
    """获取单例配置(带缓存)"""
    # 从配置文件加载加密的 API Key
    config_file = Path.home() / ".novel2script" / "config.json"
    if config_file.exists():
        config_data = json.loads(config_file.read_text(encoding="utf-8"))
        if "llm_api_key" in config_data:
            # 临时创建配置对象，然后设置加密的 API Key
            config = AppConfig()
            config.llm_api_key = config_data["llm_api_key"]
            return config
    
    return AppConfig()


def reload_config() -> AppConfig:
    """重新加载配置(清除缓存)"""
    get_config.cache_clear()
    return get_config()
