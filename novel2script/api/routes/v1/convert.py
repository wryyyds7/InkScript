"""转换任务 API 路由(含 SSE 进度推送)"""



from __future__ import annotations



import asyncio

import json

import time

from typing import AsyncGenerator



from fastapi import APIRouter, Depends

from sse_starlette import EventSourceResponse



from novel2script.api.sse import sse_manager

from novel2script.core.project_store import FileSystemProjectStore

from novel2script.config import get_config



router = APIRouter(prefix="/convert", tags=["convert"])





# ── 依赖 ─────────────────────────────────────

def get_store() -> FileSystemProjectStore:

    cfg = get_config()

    return FileSystemProjectStore(cfg.projects_dir)





# ── 内存任务状态(V1 简化;V2 改用 Redis) ───

_task_status: dict[str, dict] = {}





# ── 路由 ───────────────────────────────────────

@router.post("/{project_id}")

async def start_convert(

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



    # 使用 asyncio.create_task 在事件循环中调度后台任务

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

async def get_progress(

    task_id: str,

    last_event_ts: float = 0.0,

):

    """SSE 端点:获取转换进度



    last_event_ts:客户端上次收到事件的时间戳(用于重连补全)

    """



    async def event_generator() -> AsyncGenerator[dict, None]:

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

                        "data": json.dumps({"ts": time.time()}, ensure_ascii=False),

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



    steps = ["character_extractor", "scene_splitter", "dialogue_parser",

             "emotion_tagger", "yaml_generator"]

    total = len(steps)



    try:

        # 加载数据

        novel_text = store.load_novel(project_id)

        script = Script()



        llm = OpenAIClient()

        pipeline = build_pipeline(llm=llm)



        # 注入 before Hook（步骤开始时推送 step_start 事件）

        def _before_hook(pl, step_name, ctx):

            idx = next(

                i for i, s in enumerate(pl.steps) if s.name == step_name

            )

            pct = round((idx + 1) / total * 100, 1)

            _task_status[task_id]["percent"] = pct

            _task_status[task_id]["current_step"] = step_name

            

            # 推送 step_start 事件

            try:

                loop = asyncio.get_running_loop()

                asyncio.run_coroutine_threadsafe(

                    sse_manager.push_event(

                        task_id,

                        {

                            "event": "step_start",

                            "data": json.dumps(

                                {

                                    "step": step_name,

                                    "total_steps": total,

                                    "current": idx + 1,

                                },

                                ensure_ascii=False,

                            ),

                        },

                    ),

                    loop,

                )

            except RuntimeError:

                pass



        # 注入 after Hook（步骤完成时推送 step_complete 事件）

        def _after_hook(pl, step_name, ctx, result):

            idx = next(

                i for i, s in enumerate(pl.steps) if s.name == step_name

            )

            pct = round((idx + 1) / total * 100, 1)

            

            # 推送 step_complete 事件

            try:

                loop = asyncio.get_running_loop()

                asyncio.run_coroutine_threadsafe(

                    sse_manager.push_event(

                        task_id,

                        {

                            "event": "step_complete",

                            "data": json.dumps(

                                {

                                    "step": step_name,

                                    "result_summary": f"步骤 {step_name} 完成",

                                    "percent": pct,

                                },

                                ensure_ascii=False,

                            ),

                        },

                    ),

                    loop,

                )

            except RuntimeError:

                pass



        # 注入 error Hook（步骤失败时推送 step_error 事件）

        def _error_hook(pl, step_name, ctx, error):

            # 推送 step_error 事件

            try:

                loop = asyncio.get_running_loop()

                asyncio.run_coroutine_threadsafe(

                    sse_manager.push_event(

                        task_id,

                        {

                            "event": "step_error",

                            "data": json.dumps(

                                {

                                    "step": step_name,

                                    "error": str(error),

                                },

                                ensure_ascii=False,

                            ),

                        },

                    ),

                    loop,
                )
                # 如果是 Skill 相关步骤，额外推送 skill_error 事件
                if "skill" in step_name.lower():
                    asyncio.run_coroutine_threadsafe(
                        sse_manager.push_event(
                            task_id,
                            {
                                "event": "skill_error",
                                "data": json.dumps(
                                    {
                                        "skill": step_name,
                                        "error": str(error),
                                        "message": f"Skill 执行失败: {step_name}",
                                    },
                                    ensure_ascii=False,
                                ),
                            },
                        ),
                    ),
                    loop,
                )



            except RuntimeError:

                pass



        pipeline.register_before_hook(_before_hook)

        pipeline.register_after_hook(_after_hook)

        pipeline.register_error_hook(_error_hook)



        # 执行 Pipeline（同步调用，但在 async 函数中运行）

        result_script = pipeline.run(script, novel_text)



        # 保存结果

        store.save_script(project_id, result_script)



        # 推送完成

        await sse_manager.push_event(

            task_id,

            {

                "event": "task_complete",

                "data": json.dumps(

                    {

                        "result": {

                            "project_id": project_id,

                            "beat_count": len(result_script.beats) if result_script.beats else 0,

                        },

                    },

                    ensure_ascii=False,

                ),

            },

        )

        _task_status[task_id]["status"] = "completed"



    except Exception as exc:

        # 推送失败事件

        await sse_manager.push_event(

            task_id,

            {

                "event": "task_failed",

                "data": json.dumps(

                    {"error": str(exc)},

                    ensure_ascii=False,

                ),

            },

        )

        _task_status[task_id]["status"] = "failed"

