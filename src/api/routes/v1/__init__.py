"""V1 API 路由聚合"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")
from novel2script.api.routes.v1 import projects, convert  # noqa: E402, F401

router.include_router(projects.router)
router.include_router(convert.router)
