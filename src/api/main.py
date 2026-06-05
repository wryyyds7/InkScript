"""FastAPI 应用入口

创建 FastAPI app，注册路由，配置中间件和生命周期事件。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from novel2script.api.routes.v1 import router as v1_router
from novel2script.config import get_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期（启动/关闭逻辑）"""
    cfg = get_config()
    cfg.projects_dir.mkdir(parents=True, exist_ok=True)
    yield  # 应用运行期间


def create_app() -> FastAPI:
    """工厂函数：创建 FastAPI 应用"""
    cfg = get_config()

    app = FastAPI(
        title="InkScript API",
        description="将小说自动转换为结构化剧本",
        version=cfg.app_version,
        lifespan=lifespan,
    )

    # CORS（开发阶段允许所有来源）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(v1_router)

    # 挂载前端静态文件（如果存在）
    web_dir = Path(__file__).resolve().parent.parent / "web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    # 健康检查
    @app.get("/health")
    def health_check():
        return {"status": "ok", "version": cfg.app_version}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    cfg = get_config()
    uvicorn.run(
        "novel2script.api.main:app",
        host=cfg.host,
        port=cfg.port,
        reload=cfg.debug,
    )
