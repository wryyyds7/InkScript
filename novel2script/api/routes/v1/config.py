"""配置管理的 API 路由（V1）"""

from __future__ import annotations

from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from novel2script.config import get_config, reload_config, AppConfig


router = APIRouter(prefix="/config", tags=["config"])


# ── 请求/响应模型 ────────────────────────────────
class ConfigUpdateReq(BaseModel):
    """配置更新请求（仅包含允许前端修改的字段）"""
    provider: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    timeout: float | None = None
    max_retries: int | None = None
    request_interval: float | None = None


class ConfigResp(BaseModel):
    """配置响应（不包含敏感信息）"""
    provider: str
    base_url: str
    model_name: str
    temperature: float
    top_p: float
    max_tokens: int
    frequency_penalty: float
    presence_penalty: float
    timeout: float
    max_retries: int
    request_interval: float
    has_api_key: bool


# ── 配置存储路径 ─────────────────────────────────
def _get_config_file() -> Path:
    cfg = get_config()
    return cfg.projects_dir.parent / "config.json"


# ── 路由 ──────────────────────────────────────────
@router.get("")
def get_config_api():
    """获取当前配置（不包含 API Key）"""
    cfg = get_config()
    return {
        "code": 0,
        "data": {
            "provider": cfg.llm_provider,
            "base_url": cfg.llm_base_url,
            "model_name": cfg.llm_model_name,
            "temperature": cfg.llm_temperature,
            "top_p": cfg.llm_top_p,
            "max_tokens": cfg.llm_max_tokens,
            "frequency_penalty": cfg.llm_frequency_penalty,
            "presence_penalty": cfg.llm_presence_penalty,
            "timeout": cfg.llm_request_timeout,
            "max_retries": cfg.llm_max_retries,
            "request_interval": cfg.llm_request_interval,
            "has_api_key": bool(cfg.llm_api_key),
        }
    }


@router.put("")
def update_config(body: ConfigUpdateReq):
    """更新配置（保存到本地配置文件）"""
    config_file = _get_config_file()
    
    # 读取现有配置
    existing = {}
    if config_file.exists():
        existing = json.loads(config_file.read_text(encoding="utf-8"))
    
    # 更新配置
    updates = body.model_dump(exclude_none=True)
    existing.update(updates)
    
    # 保存到文件
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # 重新加载配置
    reload_config()
    
    return {"code": 0, "message": "配置已更新"}


@router.post("/test")
def test_connection(body: dict):
    """测试 API 连接"""
    import asyncio
    from novel2script.llm_client import OpenAIClient
    
    try:
        client = OpenAIClient(
            base_url=body.get("base_url"),
            api_key=body.get("api_key"),
            model_name=body.get("model_name"),
        )
        # 发送一个简单的测试请求
        resp = client.chat(
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=10,
            timeout=10.0,
        )
        return {"code": 0, "data": {"success": True, "response": resp[:100]}}
    except Exception as exc:
        return {"code": -1, "message": f"连接失败: {str(exc)}"}
