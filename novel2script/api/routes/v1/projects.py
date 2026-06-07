"""项目管理的 API 路由（V1）"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from novel2script.core.project_store import FileSystemProjectStore
from novel2script.config import get_config
from novel2script.schema import Script, DialogueBeat

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
    if not yaml_str:
        raise HTTPException(status_code=400, detail="剧本内容不能为空")
    
    from novel2script.schema import from_yaml
    try:
        script = from_yaml(yaml_str)
        store.save_script(project_id, script)
        return {"code": 0, "message": "已保存"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")


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


# ── 操作日志 API（逐句修改历史）────────────────────
@router.get("/{project_id}/operations")
def list_operations(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """获取项目的操作日志列表"""
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    operations = store.load_operations(project_id)
    return {"code": 0, "data": operations}


@router.post("/{project_id}/operations")
def add_operation(
    project_id: str,
    body: dict,
    store: FileSystemProjectStore = Depends(get_store),
):
    """添加一条操作日志"""
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 保存操作日志
    success = store.save_operation_log(project_id, body)
    if not success:
        raise HTTPException(status_code=500, detail="保存操作日志失败")
    
    return {"code": 0, "message": "操作日志已保存"}


@router.delete("/{project_id}/operations")
def clear_operations(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """清空项目的操作日志"""
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 清空操作日志
    edit_meta = store.load_edit_meta(project_id)
    edit_meta["operation_log"] = []
    store.save_edit_meta(project_id, edit_meta)
    
    return {"code": 0, "message": "操作日志已清空"}


# ── 角色情绪分布 API ─────────────────────────────
# 动态从剧本 YAML 中解析角色列表和情绪分布（不写死数据）
EMOTION_MAPPING = {
    "高兴": "happy",
    "开心": "happy",
    "快乐": "happy",
    "悲伤": "sad",
    "伤心": "sad",
    "愤怒": "angry",
    "生气": "angry",
    "平静": "calm",
    "冷静": "calm",
    "兴奋": "excited",
    "激动": "excited",
    "恐惧": "fear",
    "害怕": "fear",
}

DEFAULT_EMOTION_DIST = {
    "happy": 0.2,
    "sad": 0.1,
    "angry": 0.1,
    "calm": 0.3,
    "excited": 0.2,
    "fear": 0.1,
}


@router.get("/{project_id}/characters")
def list_characters(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """
    获取项目的角色列表（含情绪分布）
    
    动态从剧本 YAML 中解析角色和情绪分布，不写死数据。
    逻辑：
    1. 如果剧本中已有角色列表，且情绪分布不为空，则直接返回
    2. 否则，遍历所有场景、所有 Beat，动态计算角色和情绪分布
    """
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 加载剧本
    script = store.load_script(project_id)
    if not script:
        return {"code": 0, "data": []}
    
    # 如果剧本中已有角色列表，且情绪分布不为空，则直接返回
    if script.characters:
        all_have_emotion_dist = all(
            char.emotion_distribution for char in script.characters
        )
        if all_have_emotion_dist:
            return {
                "code": 0,
                "data": [char.model_dump() for char in script.characters]
            }
    
    # 动态计算角色列表和情绪分布
    # 1. 收集所有 DialogueBeat，按 character 分组
    character_beats = {}
    for scene in script.scenes:
        for beat in scene.beats:
            if isinstance(beat, DialogueBeat):
                char_name = beat.character
                if char_name not in character_beats:
                    character_beats[char_name] = []
                character_beats[char_name].append(beat)
    
    # 2. 为每个角色计算情绪分布
    characters = []
    for char_name, beats in character_beats.items():
        # 统计情绪频率
        emotion_counts = {}
        for beat in beats:
            emotion = beat.emotion
            if emotion:
                # 映射到英文键
                emotion_key = EMOTION_MAPPING.get(emotion, emotion)
                # 确保是有效的情绪键
                if emotion_key not in DEFAULT_EMOTION_DIST:
                    # 如果不在默认键中，则跳过或添加到分布中
                    # 这里选择添加到分布中（保持灵活性）
                    pass
                emotion_counts[emotion_key] = emotion_counts.get(emotion_key, 0) + 1
        
        # 归一化为概率分布
        total = sum(emotion_counts.values())
        emotion_distribution = {}
        if total > 0:
            for key, count in emotion_counts.items():
                emotion_distribution[key] = round(count / total, 2)
        else:
            # 如果没有情绪数据，则使用默认值
            emotion_distribution = DEFAULT_EMOTION_DIST.copy()
        
        characters.append({
            "name": char_name,
            "dialogue_count": len(beats),
            "emotion_distribution": emotion_distribution,
        })
    
    return {"code": 0, "data": characters}


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


# ── 文件导入 API ──────────────────────────────────

@router.post("/{project_id}/import-file")
async def import_file(
    project_id: str,
    file: UploadFile,
    store: FileSystemProjectStore = Depends(get_store),
):
    """
    导入文件（支持 .txt, .docx, .pdf）
    
    流程：
    1. 接收上传的文件
    2. 根据文件类型解析内容
    3. 返回提取的文本内容
    4. 前端将内容写入小说编辑器并自动保存
    """
    # 检查项目是否存在
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查文件类型
    filename = file.filename or ""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in (".txt", ".docx", ".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{file_ext}，仅支持 .txt, .docx, .pdf"
        )
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 根据文件类型解析
        if file_ext == ".txt":
            text = content.decode("utf-8", errors="ignore")
            
        elif file_ext == ".docx":
            # 使用 python-docx 解析
            from docx import Document
            from io import BytesIO
            
            doc = Document(BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
            
        elif file_ext == ".pdf":
            # 使用 PyPDF2 解析
            from PyPDF2 import PdfReader
            from io import BytesIO
            
            reader = PdfReader(BytesIO(content))
            pages = [page.extract_text() for page in reader.pages]
            text = "\n".join(pages)
            
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 检查文本长度
        if len(text) < 500:
            raise HTTPException(
                status_code=400,
                detail=f"文件内容太短（仅 {len(text)} 字），最少需要 500 字"
            )
        
        # 返回提取的文本
        return {
            "code": 0,
            "data": {
                "filename": filename,
                "text": text,
                "char_count": len(text),
                "word_count": len([c for c in text if '\u4e00' <= c <= '\u9fff']) + len(text.split()),
            }
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请确保文件是 UTF-8 编码")
    except Exception as e:
        import traceback
        print(f"[ERROR] 文件导入失败: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"文件解析失败：{str(e)}")


# ── 文件管理 API ─────────────────────────────

@router.get("/{project_id}/files")
def list_project_files(
    project_id: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """列出项目目录中的所有文件"""
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project_dir = store._project_path(project_id)
    
    if not project_dir.exists():
        return {"code": 0, "data": []}
    
    files = []
    for file_path in project_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(project_dir)
            files.append({
                "name": file_path.name,
                "path": str(relative_path),
                "size": file_path.stat().st_size,
                "modified_at": file_path.stat().st_mtime,
            })
    
    return {"code": 0, "data": files}


@router.get("/{project_id}/files/download")
def download_project_file(
    project_id: str,
    file_path: str,
    store: FileSystemProjectStore = Depends(get_store),
):
    """下载项目中的文件"""
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 安全检查：防止路径遍历攻击
    project_dir = store._project_path(project_id)
    full_path = (project_dir / file_path).resolve()
    
    if not str(full_path).startswith(str(project_dir.resolve())):
        raise HTTPException(status_code=403, detail="禁止访问项目目录外的文件")
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type='application/octet-stream'
    )




