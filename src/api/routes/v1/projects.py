"""项目管理的 API 路由（V1）"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from novel2script.core.project_store import FileSystemProjectStore
from novel2script.config import get_config

router = APIRouter(prefix="/projects", tags=["projects"])

# ── 依赖注入 ─────────────────────────────────────
def get_store() -> FileSystemProjectStore:
    cfg = get_config()
    return FileSystemProjectStore(cfg.projects_dir)


# ── 请求/响应模型 ─────────────────────────────────
class ProjectCreateReq(BaseModel):
    name: str


class ProjectUpdateReq(BaseModel):
    name: str | None = None


# ── 路由 ──────────────────────────────────────────
@router.get("/")
def list_projects(store: FileSystemProjectStore = Depends(get_store)):
    """获取项目列表"""
    return {"code": 0, "data": store.list_projects()}


@router.post("/")
def create_project(
    body: ProjectCreateReq,
    store: FileSystemProjectStore = Depends(get_store),
):
    """创建项目"""
    import uuid
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    meta = {
        "id": project_id,
        "name": body.name,
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
        "updated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "status": "draft",
    }
    proj_dir = store._project_path(project_id)
    proj_dir.mkdir(parents=True, exist_ok=True)
    import json
    (proj_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
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
    meta = store.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="项目不存在")
    if body.name is not None:
        meta["name"] = body.name
    import json
    from datetime import datetime
    meta["updated_at"] = datetime.utcnow().isoformat()
    store._meta_path(project_id).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"code": 0, "data": meta}


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """删除项目"""
    import shutil
    proj_dir = store._project_path(project_id)
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
    return {"code": 0, "message": "已删除"}


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
