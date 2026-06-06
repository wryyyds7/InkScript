"""项目管理的 API 路由（V1）"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from novel2script.core.project_store import FileSystemProjectStore
from novel2script.config import get_config

router = APIRouter(prefix="/projects", tags=["projects"])


# ── 辅助函数：创建版本快照（用于小说原文或剧本）──────────────────────────────
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


# ── 依赖注入 ─────────────────────────────────────
def get_store() -> FileSystemProjectStore:
    cfg = get_config()
    return FileSystemProjectStore(cfg.projects_dir)


# ── 请求/响应模型 ────────────────────────────────
class ProjectCreateReq(BaseModel):
    name: str


class ProjectUpdateReq(BaseModel):
    name: str | None = None


# ── 路由 ──────────────────────────────────────────
@router.get("", name="list_projects")
def list_projects(
    search: str = "",
    sort_by: str = "updated_at",
    order: str = "desc",
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取项目列表（支持搜索和排序）"""
    projects = store.list_projects()
    
    # 搜索过滤
    if search:
        search_lower = search.lower()
        projects = [
            p for p in projects
            if search_lower in p.get("name", "").lower()
        ]
    
    # 排序
    reverse = order == "desc"
    if sort_by in ("name", "created_at", "updated_at"):
        projects.sort(
            key=lambda p: p.get(sort_by, ""),
            reverse=reverse,
        )
    
    return {"code": 0, "data": projects}


@router.post("", name="create_project")
def create_project(
    body: ProjectCreateReq,
    store: FileSystemProjectStore = Depends(get_store),
):
    """创建项目"""
    import json
    from datetime import datetime

    meta = store.create_project(body.name, "")
    return {"code": 0, "data": meta}


@router.get("/{project_id}")
def get_project(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取项目详情"""
    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"code": 0, "data": meta}


@router.put("/{project_id}")
def update_project(
    project_id: str,
    body: ProjectUpdateReq,
    store: FileSystemProjectStore = Depends(get_store),
):
    """更新项目（仅 name）"""
    import json
    from datetime import datetime

    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    if body.name is not None:
        meta["name"] = body.name
    meta["updated_at"] = datetime.utcnow().isoformat()
    store._meta_path(project_id).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"code": 0, "data": meta}


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    permanent: bool = False,
    store: FileSystemProjectStore = Depends(get_store),
):
    """删除项目（默认软删除到回收站）"""
    store.delete_project(project_id, soft_delete=not permanent)
    return {"code": 0, "message": "已删除" if permanent else "已移动到回收站"}


# ── 回收站 API ──────────────────────────────

@router.get("/trash")
def list_trash(
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取回收站中的所有项目"""
    items = store.list_trash()
    return {"code": 0, "data": items}


@router.post("/trash/{project_id}/restore")
def restore_from_trash(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """从回收站恢复项目"""
    success = store.restore_from_trash(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="回收站中未找到该项目")
    return {"code": 0, "message": "已恢复"}


@router.delete("/trash/{project_id}")
def permanent_delete(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """从回收站永久删除项目"""
    success = store.permanent_delete(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="回收站中未找到该项目")
    return {"code": 0, "message": "已永久删除"}


@router.get("/{project_id}/novel")
def get_novel(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取小说原文"""
    text = store.load_novel(project_id)
    return {"code": 0, "data": {"content": text}}


@router.put("/{project_id}/novel")
def save_novel(
    project_id: str,
    body: dict,
    store: FileSystemProjectStore = Depends(get_store),
):
    """保存小说原文"""
    content = body.get("content", "")
    store.save_novel(project_id, content)
    return {"code": 0, "message": "已保存"}


@router.get("/{project_id}/script")
def get_script(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取剧本 YAML"""
    script = store.load_script(project_id)
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    from novel2script.schema import to_yaml
    return {"code": 0, "data": {"yaml": to_yaml(script)}}


@router.put("/{project_id}/script")
def save_script(
    project_id: str,
    body: dict,
    store: FileSystemProjectStore = Depends(get_store),
):
    """保存剧本 YAML"""
    yaml_str = body.get("yaml", "")
    from novel2script.schema import from_yaml
    script = from_yaml(yaml_str)
    store.save_script(project_id, script)
    return {"code": 0, "message": "已保存"}


@router.get("/{project_id}/download")
def download_project(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """下载项目文件（剧本 YAML）"""
    from fastapi.responses import FileResponse
    script_path = store._script_path(project_id)
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="剧本文件不存在")
    return FileResponse(
        path=str(script_path),
        filename=f"{project_id}.yaml",
        media_type="application/x-yaml",
    )


# ── 版本历史 API ──────────────────────────────

@router.get("/{project_id}/versions")
def list_versions(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取项目的版本历史列表"""
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    versions = store.list_versions(project_id)
    return {"code": 0, "data": versions}


@router.get("/{project_id}/versions/{version_id}")
def get_version(
    project_id: str,
    version_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取指定版本的详情"""
    version_data = store.get_version(project_id, version_id)
    if not version_data:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return {"code": 0, "data": version_data}


@router.post("/{project_id}/novel-snapshot")
def create_novel_snapshot(
    project_id: str,
    body: dict | None = None,
    store: FileSystemProjectStore = Depends(get_store),
):
    """创建小说原文版本快照（用于预处理操作前）"""
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取描述
    description = body.get("description", "预处理操作前快照") if body else "预处理操作前快照"
    
    # 创建小说原文快照
    snapshot_data = store.create_novel_snapshot(project_id, description)
    
    if not snapshot_data:
        raise HTTPException(status_code=500, detail="创建快照失败")
    
    return {"code": 0, "message": "快照创建成功", "data": snapshot_data}


@router.post("/{project_id}/versions/{version_id}/rollback")
def rollback_version(
    project_id: str,
    version_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """回滚到指定版本"""
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 执行回滚
    success = store.rollback_version(project_id, version_id)
    if not success:
        raise HTTPException(status_code=404, detail="回滚失败，版本不存在")
    
    return {"code": 0, "message": "回滚成功"}


# ── 配置快照 API ─────────────────────────────

@router.get("/{project_id}/config-snapshot")
def get_config_snapshot(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取项目转换时使用的配置快照"""
    # 检查项目是否存在
    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 读取配置快照文件
    config_snapshot_path = store._project_dir(project_id) / "config_snapshot.json"
    
    if not config_snapshot_path.exists():
        # 如果没有配置快照，返回当前配置
        from novel2script.config import get_config
        cfg = get_config()
        config_data = {
            "llm_provider": cfg.llm_provider,
            "llm_base_url": cfg.llm_base_url,
            "llm_model_name": cfg.llm_model_name,
            "llm_temperature": cfg.llm_temperature,
            "llm_top_p": cfg.llm_top_p,
            "llm_max_tokens": cfg.llm_max_tokens,
            "llm_frequency_penalty": cfg.llm_frequency_penalty,
            "llm_presence_penalty": cfg.llm_presence_penalty,
            "note": "当前配置（项目未保存配置快照）"
        }
        return {"code": 0, "data": config_data}
    
    # 返回保存的配置快照
    import json
    config_data = json.loads(config_snapshot_path.read_text(encoding="utf-8"))
    return {"code": 0, "data": config_data}


@router.post("/{project_id}/config-snapshot")
def save_config_snapshot(
    project_id: str,
    body: dict,
    store: FileSystemProjectStore = Depends(get_store),
):
    """保存项目转换时的配置快照"""
    # 检查项目是否存在
    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 保存配置快照
    import json
    from datetime import datetime
    
    config_snapshot_path = store._project_dir(project_id) / "config_snapshot.json"
    snapshot_data = body.get("config", {})
    snapshot_data["saved_at"] = datetime.utcnow().isoformat()
    
    config_snapshot_path.write_text(
        json.dumps(snapshot_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return {"code": 0, "message": "配置快照已保存"}


# ── EditMeta API ─────────────────────
@router.get("/{project_id}/edit-meta")
def get_edit_meta(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取项目编辑器元数据"""
    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    edit_meta = store.load_edit_meta(project_id)
    return {"code": 0, "data": edit_meta}


@router.put("/{project_id}/edit-meta")
def update_edit_meta(
    project_id: str,
    body: dict,
    store: FileSystemProjectStore = Depends(get_store),
):
    """更新项目编辑器元数据"""
    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 合并更新（只更新 body 中提供的字段）
    current_meta = store.load_edit_meta(project_id)
    current_meta.update(body)
    
    store.save_edit_meta(project_id, current_meta)
    return {"code": 0, "message": "编辑器元数据已更新", "data": current_meta}

