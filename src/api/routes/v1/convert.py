"""转换任务 API 路由（含 SSE 进度推送）"""

from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette import EventSourceResponse

from novel2script.api.sse import sse_manager
from novel2script.core.project_store import FileSystemProjectStore
from novel2script.config import get_config


router = APIRouter(prefix="/convert", tags=["convert"])


# ── 依赖 ─────────────────────────────────────
def get_store() -> FileSystemProjectStore:
    cfg = get_config()
    return FileSystemProjectStore(cfg.projects_dir)


# ── 内存任务状态（V1 简化;V2 改用 Redis） ───
_task_status: dict[str, dict] = {}


# ── 路由 ───────────────────────────────────────
@router.post("/{project_id}")
def start_convert(
    project_id: str,
    body: dict | None = None,
    store: FileSystemProjectStore = Depends(get_store),
):
    """启动转换任务"""
    import uuid

    task_id = f"task_{uuid.uuid4().hex[:8]}"
    _task_status[task_id] = {
        "task_id": task_id,
        "project_id": project_id,
        "status": "running",
        "current_step": "",
        "percent": 0.0,
    }

    # 异步执行（后台）
    asyncio.create_task(_run_pipeline(task_id, project_id, store))

    return {
        "code": 0,
        "message": "转换任务已启动",
        "data": {
            "task_id": task_id,
            "sse_url": f"/api/v1/convert/{task_id}/progress",
        },
    }


@router.get("/{task_id}/progress")
def get_progress(
    task_id: str,
    last_event_ts: float = 0.0,
):
    """SSE 端点：获取转换进度

    last_event_ts：客户端上次收到事件的时间戳（用于重连补全）
    """

    async def event_generator():
        # 1. 补全缓存事件
        cached = sse_manager.get_cached_events(task_id, last_event_ts)
        for event in cached:
            yield event

        # 2. 注册客户端,等待新事件
        client_id = f"{task_id}_{int(time.time() * 1000)}"
        queue = await sse_manager.register_client(client_id, task_id)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event
                    # 如果任务完成/失败,结束流
                    if event.get("event") in ("task_complete", "task_failed"):
                        break
                except asyncio.TimeoutError:
                    heartbeat = {
                        "event": "heartbeat",
                        "data": json.dumps({"ts": time.time()}),
                    }
                    yield heartbeat
                    await sse_manager.push_event(task_id, heartbeat)
        finally:
            await sse_manager.unregister_client(client_id)

    return EventSourceResponse(event_generator())


# ── 后台任务 ──────────────────────────────────
async def _run_pipeline(
    task_id: str,
    project_id: str,
    store: FileSystemProjectStore,
):
    """后台执行 Pipeline,并通过 SSE 推送进度"""
    from novel2script.llm_client import OpenAIClient
    from novel2script.core.pipeline import build_pipeline
    from novel2script.schema import Script

    steps = ["角色识别", "场景分割", "对白解析", "情绪标注", "YAML 生成"]
    total = len(steps)

    try:
        # 加载数据
        novel_text = store.load_novel(project_id)
        script = Script()

        llm = OpenAIClient()
        pipeline = build_pipeline(llm=llm)

        # 注入进度 Hook
        async def _progress_hook(name: str):
            idx = list(pipeline.steps).index(next(s for s in pipeline.steps if s.name == name))
            pct = round((idx + 1) / total * 100, 1)
            _task_status[task_id]["percent"] = pct
            _task_status[task_id]["current_step"] = name
            await sse_manager.push_event(
                task_id,
                {
                    "event": "step_progress",
                    "data": json.dumps(
                        {"step": name, "detail": name, "percent": pct}, ensure_ascii=False
                    ),
                },
            )

        # 简化：直接同步执行（V1 不拆 async step）
        result_script = pipeline.run(script, novel_text)

        # 保存结果
        store.save_script(project_id, result_script)

        # 推送完成
        await sse_manager.push_event(
            task_id,
            {
                "event": "task_complete",
                "data": json.dumps(
                    {"result": {"project_id": project_id}}, ensure_ascii=False
                ),
            },
        )
        _task_status[task_id]["status"] = "completed"

    except Exception as exc:
        await sse_manager.push_event(
            task_id,
            {
                "event": "task_failed",
                "data": json.dumps(
                    {"error": str(exc)}, ensure_ascii=False
                ),
            },
        )
        _task_status[task_id]["status"] = "failed"
