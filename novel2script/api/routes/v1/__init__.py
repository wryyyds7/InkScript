"""V1 API 路由聚合"""

from fastapi import APIRouter

from novel2script.api.routes.v1 import projects, convert, config, skills  # noqa: E402, F401

router = APIRouter(prefix="/api/v1")
router.include_router(projects.router)
router.include_router(convert.router)
router.include_router(config.router)
router.include_router(skills.router)
