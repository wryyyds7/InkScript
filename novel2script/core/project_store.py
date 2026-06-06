"""ProjectStore Protocol + FileSystemProjectStore 实现

定义项目持久化接口(Protocol),
默认提供基于文件系统的实现.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable
from datetime import datetime

from novel2script.schema import Script, ScriptMeta
from novel2script.config import get_config


@runtime_checkable
class ProjectStore(Protocol):
    """项目持久化接口(可替换实现)"""

    def list_projects(self) -> list[dict]: ...
    def get_project(self, project_id: str) -> dict | None: ...
    def create_project(self, name: str, novel_text: str) -> dict: ...
    def update_project(self, project_id: str, **kwargs) -> dict: ...
    def delete_project(self, project_id: str) -> None: ...
    def save_novel(self, project_id: str, text: str) -> None: ...
    def load_novel(self, project_id: str) -> str: ...
    def save_script(self, project_id: str, script: Script) -> None: ...
    def load_script(self, project_id: str) -> Script | None: ...


class FileSystemProjectStore:
    """基于文件系统的 ProjectStore 实现(V1 默认)"""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or get_config().projects_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ── 辅助方法 ──────────────────────────────
    def _project_path(self, project_id: str) -> Path:
        return self.base_dir / project_id

    def _meta_path(self, project_id: str) -> Path:
        return self._project_path(project_id) / "meta.json"

    def _novel_path(self, project_id: str) -> Path:
        return self._project_path(project_id) / "novel.txt"

    def _script_path(self, project_id: str) -> Path:
        return self._project_path(project_id) / "script.yaml"

    def _edit_meta_path(self, project_id: str) -> Path:
        """返回 edit_meta.json 路径"""
        return self._project_path(project_id) / "edit_meta.json"

    def _versions_dir(self, project_id: str) -> Path:
        return self._project_path(project_id) / "versions"

    def _version_path(self, project_id: str, version_id: str) -> Path:
        return self._versions_dir(project_id) / f"{version_id}.yaml"

    def _next_id(self) -> str:
        import uuid
        return f"proj_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"

    def _next_version_id(self) -> str:
        """生成版本 ID（时间戳）"""
        return f"v{datetime.now():%Y%m%d_%H%M%S}"
    
    def create_novel_snapshot(self, project_id: str, description: str = "") -> dict:
        """创建小说原文版本快照（在预处理操作前自动调用）"""
        import json
        
        # 确保版本目录存在
        versions_dir = self._versions_dir(project_id)
        versions_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取当前小说原文内容
        novel_text = self.load_novel(project_id)
        if not novel_text:
            return None
        
        # 生成版本 ID
        version_id = self._next_version_id()
        
        # 保存版本快照
        version_data = {
            "version_id": version_id,
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "type": "novel",  # 标记为小说原文快照
            "novel_text": novel_text
        }
        
        version_file = self._version_path(project_id, version_id)
        version_file.write_text(
            json.dumps(version_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 清理旧版本（最多保留 10 个）
        self._cleanup_old_versions(project_id, keep=10)
        
        return version_data

    # ── 版本管理功能 ──────────────────────────────
    def create_version_snapshot(self, project_id: str, description: str = "") -> dict:
        """创建版本快照（在保存前自动调用）"""
        import json
        
        # 确保版本目录存在
        versions_dir = self._versions_dir(project_id)
        versions_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取当前剧本内容
        script = self.load_script(project_id)
        if not script:
            return None
        
        # 生成版本 ID
        version_id = self._next_version_id()
        
        # 保存版本快照
        from novel2script.schema import to_yaml
        version_data = {
            "version_id": version_id,
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "script_yaml": to_yaml(script)
        }
        
        version_file = self._version_path(project_id, version_id)
        version_file.write_text(
            json.dumps(version_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 清理旧版本（最多保留 10 个）
        self._cleanup_old_versions(project_id, keep=10)
        
        return version_data

    def _cleanup_old_versions(self, project_id: str, keep: int = 10):
        """清理旧版本，只保留最近 keep 个"""
        
        versions_dir = self._versions_dir(project_id)
        if not versions_dir.exists():
            return
        
        # 获取所有版本文件
        version_files = sorted(
            versions_dir.glob("v*.yaml"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 删除超出数量的旧版本
        for old_file in version_files[keep:]:
            old_file.unlink()

    def list_versions(self, project_id: str) -> list[dict]:
        """列出项目的所有版本快照"""
        import json
        
        versions_dir = self._versions_dir(project_id)
        if not versions_dir.exists():
            return []
        
        versions = []
        for version_file in sorted(
            versions_dir.glob("v*.yaml"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ):
            try:
                data = json.loads(version_file.read_text(encoding="utf-8"))
                versions.append({
                    "version_id": data.get("version_id"),
                    "created_at": data.get("created_at"),
                    "description": data.get("description", ""),
                })
            except Exception:
                continue
        
        return versions

    def get_version(self, project_id: str, version_id: str) -> dict | None:
        """获取指定版本的详情"""
        import json
        
        version_file = self._version_path(project_id, version_id)
        if not version_file.exists():
            return None
        
        return json.loads(version_file.read_text(encoding="utf-8"))

    def rollback_version(self, project_id: str, version_id: str) -> bool:
        """回滚到指定版本"""
        import json
        from novel2script.schema import from_yaml
        
        # 获取版本数据
        version_data = self.get_version(project_id, version_id)
        if not version_data:
            return False
        
        # 在回滚前，先创建当前状态的快照（以便可以撤销回滚）
        self.create_version_snapshot(project_id, description=f"回滚前快照（即将回滚到 {version_id}）")
        
        # 恢复版本数据
        script_yaml = version_data.get("script_yaml", "")
        script = from_yaml(script_yaml)
        
        # 保存到当前剧本
        self.save_script(project_id, script)
        
        return True

    # ── CRUD ──────────────────────────────────
    def list_projects(self) -> list[dict]:
        projects = []
        for d in sorted(self.base_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            meta_file = d / "meta.json"
            if meta_file.exists():
                import json
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                projects.append(meta)
        return projects

    def get_project(self, project_id: str) -> dict | None:
        meta_file = self._meta_path(project_id)
        if not meta_file.exists():
            return None
        import json
        return json.loads(meta_file.read_text(encoding="utf-8"))

    def create_project(self, name: str, novel_text: str) -> dict:
        project_id = self._next_id()
        proj_dir = self._project_path(project_id)
        proj_dir.mkdir(parents=True, exist_ok=True)

        # 保存小说原文
        proj_dir.mkdir(parents=True, exist_ok=True)
        self._novel_path(project_id).write_text(novel_text, encoding="utf-8")

        meta = {
            "id": project_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "draft",
        }
        self._meta_path(project_id).write_text(
            __import__("json").dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return meta

    def update_project(self, project_id: str, **kwargs) -> dict:
        meta = self.get_project(project_id)
        if not meta:
            raise FileNotFoundError(f"项目不存在:{project_id}")
        meta.update(kwargs)
        meta["updated_at"] = datetime.now().isoformat()
        self._meta_path(project_id).write_text(
            __import__("json").dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return meta

    def delete_project(self, project_id: str, soft_delete: bool = True) -> None:
        """删除项目（支持软删除）"""
        import shutil
        
        proj_dir = self._project_path(project_id)
        if not proj_dir.exists():
            return
        
        if soft_delete:
            # 软删除：移动到 trash 目录
            self._move_to_trash(proj_dir, project_id)
        else:
            # 硬删除：直接删除
            shutil.rmtree(proj_dir)

    def _move_to_trash(self, proj_dir: Path, project_id: str) -> None:
        """将项目移动到回收站"""
        import shutil
        from datetime import datetime
        
        # 创建 trash 目录
        trash_dir = self.base_dir.parent / "trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成回收站中的项目名称（添加删除时间戳）
        deleted_at = f"{datetime.now():%Y%m%d_%H%M%S}"
        trash_name = f"{project_id}_deleted_{deleted_at}"
        trash_path = trash_dir / trash_name
        
        # 移动项目到回收站
        shutil.move(str(proj_dir), str(trash_path))
        
        # 记录删除信息
        delete_info = {
            "project_id": project_id,
            "original_name": self.get_project_info(project_id, proj_dir),
            "deleted_at": datetime.now().isoformat(),
            "trash_path": str(trash_path)
        }
        
        info_file = trash_path / "delete_info.json"
        info_file.write_text(
            __import__("json").dumps(delete_info, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_project_info(self, project_id: str, proj_dir: Path = None) -> dict:
        """获取项目信息（用于回收站显示）"""
        if not proj_dir:
            proj_dir = self._project_path(project_id)
        
        meta_file = proj_dir / "meta.json"
        if meta_file.exists():
            import json
            return json.loads(meta_file.read_text(encoding="utf-8"))
        return {"id": project_id, "name": "未知项目"}

    def list_trash(self) -> list[dict]:
        """列出回收站中的所有项目"""
        import json
        
        trash_dir = self.base_dir.parent / "trash"
        if not trash_dir.exists():
            return []
        
        trash_items = []
        for item in trash_dir.iterdir():
            if not item.is_dir():
                continue
            
            # 读取删除信息
            info_file = item / "delete_info.json"
            if info_file.exists():
                try:
                    info = json.loads(info_file.read_text(encoding="utf-8"))
                    trash_items.append(info)
                except Exception:
                    # 如果没有 delete_info.json，尝试读取 meta.json
                    meta = self.get_project_info("", item)
                    trash_items.append({
                        "project_id": meta.get("id", item.name),
                        "original_name": meta.get("name", "未知项目"),
                        "deleted_at": "未知时间"
                    })
            else:
                # 如果没有 delete_info.json，尝试读取 meta.json
                meta = self.get_project_info("", item)
                trash_items.append({
                    "project_id": meta.get("id", item.name),
                    "original_name": meta.get("name", "未知项目"),
                    "deleted_at": "未知时间"
                })
        
        # 按删除时间倒序排序
        trash_items.sort(key=lambda x: x.get("deleted_at", ""), reverse=True)
        return trash_items

    def _get_project_info_from_path(self, proj_dir: Path) -> dict:
        """从项目目录路径获取项目信息（用于回收站显示）"""
        meta_file = proj_dir / "meta.json"
        if meta_file.exists():
            import json
            return json.loads(meta_file.read_text(encoding="utf-8"))
        return {"id": proj_dir.name, "name": "未知项目"}

    def restore_from_trash(self, project_id: str) -> bool:
        """从回收站恢复项目"""
        import shutil
        
        trash_dir = self.base_dir.parent / "trash"
        if not trash_dir.exists():
            return False
        
        # 查找回收站中的项目
        for item in trash_dir.iterdir():
            if not item.is_dir():
                continue
            
            info_file = item / "delete_info.json"
            if info_file.exists():
                import json
                info = json.loads(info_file.read_text(encoding="utf-8"))
                if info.get("project_id") == project_id:
                    # 恢复项目
                    target_path = self._project_path(project_id)
                    if target_path.exists():
                        # 如果目标位置已存在，先删除
                        shutil.rmtree(str(target_path))
                    
                    shutil.move(str(item), str(target_path))
                    return True
        
        return False

    def permanent_delete(self, project_id: str) -> bool:
        """从回收站永久删除项目"""
        import shutil
        
        trash_dir = self.base_dir.parent / "trash"
        if not trash_dir.exists():
            return False
        
        # 查找回收站中的项目
        for item in trash_dir.iterdir():
            if not item.is_dir():
                continue
            
            info_file = item / "delete_info.json"
            if info_file.exists():
                import json
                info = json.loads(info_file.read_text(encoding="utf-8"))
                if info.get("project_id") == project_id:
                    # 永久删除
                    shutil.rmtree(str(item))
                    return True
        
        return False

    # ── 内容读写 ──────────────────────────────
    def save_novel(self, project_id: str, text: str) -> None:
        self._novel_path(project_id).write_text(text, encoding="utf-8")

    def load_novel(self, project_id: str) -> str:
        p = self._novel_path(project_id)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def save_script(self, project_id: str, script: Script) -> None:
        """保存剧本（自动创建版本快照）"""
        import json
        from novel2script.schema import to_yaml
        
        # 在保存前创建版本快照
        self.create_version_snapshot(project_id, description="自动保存快照")
        
        # 保存剧本
        self._script_path(project_id).write_text(
            to_yaml(script), encoding="utf-8"
        )

    def load_script(self, project_id: str) -> Script | None:
        from novel2script.schema import from_yaml
        p = self._script_path(project_id)
        if not p.exists():
            return None
        return from_yaml(p.read_text(encoding="utf-8"))

    # ── EditMeta 读写 ──────────────────────
    def save_edit_meta(self, project_id: str, edit_meta: dict) -> None:
        """保存编辑器元数据"""
        import json
        from datetime import datetime

        edit_meta["last_updated"] = datetime.now().isoformat()
        self._edit_meta_path(project_id).write_text(
            json.dumps(edit_meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def save_operation_log(self, project_id: str, operation: dict) -> None:
        """保存操作日志到 EditMeta"""
        import json
        from novel2script.schema import OperationLog, EditMeta
        
        # 加载当前 EditMeta
        edit_meta_dict = self.load_edit_meta(project_id)
        
        # 创建 OperationLog 对象并验证
        try:
            op_log = OperationLog(**operation)
            op_dict = json.loads(op_log.model_dump_json(ensure_ascii=False))
            
            # 添加到 operation_log 列表
            if "operation_log" not in edit_meta_dict:
                edit_meta_dict["operation_log"] = []
            
            edit_meta_dict["operation_log"].append(op_dict)
            
            # 保存回文件
            self.save_edit_meta(project_id, edit_meta_dict)
            return True
        except Exception as e:
            print(f"保存操作日志失败: {e}")
            return False

    def load_operations(self, project_id: str) -> list[dict]:
        """从 EditMeta 加载操作日志"""
        import json
        from novel2script.schema import EditMeta
        
        edit_meta_dict = self.load_edit_meta(project_id)
        
        if not edit_meta_dict:
            return []
        
        operation_log = edit_meta_dict.get("operation_log", [])
        return operation_log

    def load_edit_meta(self, project_id: str) -> dict:
        """加载编辑器元数据（返回字典，如果不存在则返回默认值）"""
        import json
        from novel2script.schema import EditMeta

        p = self._edit_meta_path(project_id)
        if not p.exists():
            # 返回默认元数据
            default_meta = EditMeta()
            return json.loads(default_meta.model_dump_json(ensure_ascii=False))

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # 验证数据
            validated = EditMeta(**data)
            return json.loads(validated.model_dump_json(ensure_ascii=False))
        except Exception:
            # 如果数据无效，返回默认值
            default_meta = EditMeta()
            return json.loads(default_meta.model_dump_json(ensure_ascii=False))
