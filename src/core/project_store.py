"""ProjectStore Protocol + FileSystemProjectStore 实现

定义项目持久化接口（Protocol），
默认提供基于文件系统的实现。
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable
from datetime import datetime

from novel2script.schema import Script, ScriptMeta
from novel2script.config import get_config


@runtime_checkable
class ProjectStore(Protocol):
    """项目持久化接口（可替换实现）"""

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
    """基于文件系统的 ProjectStore 实现（V1 默认）"""

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

    def _next_id(self) -> str:
        import uuid
        return f"proj_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"

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
            raise FileNotFoundError(f"项目不存在：{project_id}")
        meta.update(kwargs)
        meta["updated_at"] = datetime.now().isoformat()
        self._meta_path(project_id).write_text(
            __import__("json").dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return meta

    def delete_project(self, project_id: str) -> None:
        import shutil
        proj_dir = self._project_path(project_id)
        if proj_dir.exists():
            shutil.rmtree(proj_dir)

    # ── 内容读写 ──────────────────────────────
    def save_novel(self, project_id: str, text: str) -> None:
        self._novel_path(project_id).write_text(text, encoding="utf-8")

    def load_novel(self, project_id: str) -> str:
        p = self._novel_path(project_id)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def save_script(self, project_id: str, script: Script) -> None:
        from novel2script.schema import to_yaml
        self._script_path(project_id).write_text(
            to_yaml(script), encoding="utf-8"
        )

    def load_script(self, project_id: str) -> Script | None:
        from novel2script.schema import from_yaml
        p = self._script_path(project_id)
        if not p.exists():
            return None
        return from_yaml(p.read_text(encoding="utf-8"))
