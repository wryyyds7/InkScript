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


# ── 路由 ──────────────────────────────────────────
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

    

    return {"code": 0, "message": "转换任务已启动", "data": {"task_id": task_id}}



@router.get("/{task_id}/sse")

async def get_sse_stream(

    task_id: str,

):

    """获取 SSE 事件流"""

    return EventSourceResponse(

        sse_manager.subscribe(task_id),

        ping=15,  # 每 15 秒发送一次心跳

    )



# ── 后台任务 ─────────────────────────────────────
async def _run_pipeline(task_id: str, project_id: str, store: FileSystemProjectStore):

    """运行转换流水线"""

    import os

    from novel2script.core.pipeline import build_pipeline

    

    try:

        # 更新任务状态

        _update_task_status(task_id, "running", "init", 0.0)

        

        # 加载项目数据

        novel_text = store.load_novel(project_id)

        if not novel_text:

            raise ValueError("小说原文为空")

        

        # 创建 LLM 客户端

        from novel2script.llm_client import OpenAIClient
        from novel2script.config import get_config
        cfg = get_config()
        llm = OpenAIClient(
            base_url=cfg.llm_base_url,
            api_key=cfg.get_decrypted_api_key(),
            model_name=cfg.llm_model_name,
        )

        # 创建 Pipeline 实例（使用默认 Step 列表）

        pipeline = build_pipeline(llm=llm)

        

        # 注册钩子函数（用于 SSE 进度推送）

        def _before_hook(pl, step_name, ctx):

            """步骤开始前推送事件"""

            _update_task_status(task_id, "running", step_name, 0.0)

            

            # 推送 step_start 事件

            asyncio.run_coroutine_threadsafe(

                sse_manager.push_event(

                    task_id,

                    {

                        "event": "step_start",

                        "data": json.dumps(

                            {

                                "step": step_name,

                                "message": f"开始执行步骤: {step_name}",

                            },

                            ensure_ascii=False,

                        ),

                    },

                ),

                asyncio.get_event_loop(),

            )

        

        def _after_hook(pl, step_name, ctx):

            """步骤完成后推送事件"""

            # 计算进度百分比

            total_steps = len(pl.steps)

            current_step_idx = pl.steps.index(step_name) if step_name in pl.steps else 0

            percent = (current_step_idx + 1) / total_steps * 100.0 if total_steps > 0 else 0.0

            

            _update_task_status(task_id, "running", step_name, percent)

            

            # 推送 step_complete 事件

            asyncio.run_coroutine_threadsafe(

                sse_manager.push_event(

                    task_id,

                    {

                        "event": "step_complete",

                        "data": json.dumps(

                            {

                                "step": step_name,

                                "message": f"步骤完成: {step_name}",

                                "percent": percent,

                            },

                            ensure_ascii=False,

                        ),

                    },

                ),

                asyncio.get_event_loop(),

            )

        

        def _error_hook(pl, step_name, ctx, error):

            """步骤失败时推送事件"""

            # 推送 step_error 事件

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

                asyncio.get_event_loop(),

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

                    asyncio.get_event_loop(),

                )

                

                # 记录 Skill 执行错误到日志文件

                _log_skill_error(step_name, error, ctx)

        

        # 注册钩子

        pipeline.register_before_hook(_before_hook)

        pipeline.register_after_hook(_after_hook)

        

        # 运行 Pipeline

        script = store.load_script(project_id)

        if not script:

            # 如果剧本不存在，创建一个新的

            from novel2script.schema import Script

            script = Script(title="未命名剧本", author="未知作者", scenes=[])

        

        # 运行转换

        result_script = pipeline.run(script, novel_text)

        

        # 保存结果

        store.save_script(project_id, result_script)

        

        # 更新任务状态

        _update_task_status(task_id, "completed", "complete", 100.0)

        

        # 推送 task_complete 事件

        asyncio.run_coroutine_threadsafe(

            sse_manager.push_event(

                task_id,

                {

                    "event": "task_complete",

                    "data": json.dumps(

                        {

                            "message": "转换任务完成",

                            "result": "success",

                        },

                        ensure_ascii=False,

                    ),

                },

            ),

            asyncio.get_event_loop(),

        )

        

    except Exception as e:

        # 更新任务状态

        _update_task_status(task_id, "failed", "error", 0.0, str(e))

        

        # 推送 task_failed 事件

        asyncio.run_coroutine_threadsafe(

            sse_manager.push_event(

                task_id,

                {

                    "event": "task_failed",

                    "data": json.dumps(

                        {

                            "message": f"转换任务失败: {str(e)}",

                            "error": str(e),

                        },

                        ensure_ascii=False,

                    ),

                },

            ),

            asyncio.get_event_loop(),

        )

        

        print(f"转换任务失败: {e}")

    

    finally:

        # 清理任务状态（延迟清理，让前端有时间接收最后的事件）

        asyncio.get_event_loop().call_later(60, lambda: _task_status.pop(task_id, None))

    

    return None



def _update_task_status(task_id: str, status: str, step: str, percent: float, error: str = None):

    """更新任务状态"""

    if task_id in _task_status:

        _task_status[task_id]["status"] = status

        _task_status[task_id]["current_step"] = step

        _task_status[task_id]["percent"] = percent

        

        if error:

            _task_status[task_id]["error"] = error

    

    

def _log_skill_error(skill_name: str, error: Exception, ctx: dict):

    """将 Skill 执行错误记录到日志文件"""

    import os

    from datetime import datetime

    from pathlib import Path

    

    # 构建日志文件路径

    # Skill 名称格式：builtin/skill_name 或 user/skill_name

    # 日志文件路径：novel2script/skills/builtin/skill_name/error.log

    # 或 novel2script/skills/user/skill_name/error.log

    skill_dir = Path(__file__).parent.parent.parent / "skills"

    

    # 清理 skill_name，提取实际的 Skill 目录名

    # 例如："builtin/character-analysis" -> "character-analysis"

    # 例如："user/my-skill" -> "my-skill"

    if "/" in skill_name:

        parts = skill_name.split("/")

        if len(parts) >= 2:

            skill_type = parts[0]  # builtin 或 user

            skill_name_only = parts[1]

            log_dir = skill_dir / skill_type / skill_name_only

        else:

            log_dir = skill_dir / "builtin" / skill_name

    else:

        log_dir = skill_dir / "builtin" / skill_name

    

    # 确保目录存在

    log_dir.mkdir(parents=True, exist_ok=True)

    

    # 日志文件路径

    log_file = log_dir / "error.log"

    

    # 构建日志条目

    timestamp = datetime.now().isoformat()

    log_entry = f"[{timestamp}] Skill: {skill_name}\n"

    log_entry += f"Error: {str(error)}\n"

    log_entry += f"Context: {ctx}\n"

    log_entry += "-" * 50 + "\n"

    

    # 追加写入日志文件

    with open(log_file, "a", encoding="utf-8") as f:

        f.write(log_entry)

    

# ── 辅助函数 ─────────────────────────────────────
def _create_version_snapshot(project_id: str, store: FileSystemProjectStore, description: str = "") -> dict:

    """

    创建版本快照（通用函数，可被多个端点调用）

    

    Args:

        project_id: 项目 ID

        store: 项目存储实例

        description: 快照描述

        

    Returns:

        快照数据字典

    """

    return store.create_version_snapshot(project_id, description)
