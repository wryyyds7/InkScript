"""Skill 管理的 API 路由（V1）"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from novel2script.config import get_config

router = APIRouter(prefix="/skills", tags=["skills"])

# ── Skill 目录 ─────────────────────────────────────
BUILTIN_SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "builtins"
USER_SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "user"


# ── 依赖注入 ─────────────────────────────────────
def get_skills_dir() -> tuple[Path, Path]:
    """返回（内置 Skill 目录，用户 Skill 目录）"""
    cfg = get_config()
    builtin_dir = BUILTIN_SKILLS_DIR
    user_dir = cfg.projects_dir.parent / "skills" / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    return builtin_dir, user_dir


# ── 请求/响应模型 ────────────────────────────────
class SkillEnableReq(BaseModel):
    enabled: bool


class SkillPriorityReq(BaseModel):
    priority: int


class SkillCreateReq(BaseModel):
    name: str
    description: str
    prompt: str


# ── 辅助函数 ─────────────────────────────────────
def _load_skill_metadata(skill_dir: Path) -> dict | None:
    """加载 Skill 的 metadata.json 或 SKILL.md"""
    metadata_file = skill_dir / "metadata.json"
    skill_md_file = skill_dir / "SKILL.md"

    if metadata_file.exists():
        return json.loads(metadata_file.read_text(encoding="utf-8"))

    if skill_md_file.exists():
        # 从 SKILL.md 解析元数据（简单的 YAML front matter）
        content = skill_md_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            import yaml
            try:
                yaml_str = content.split("---", 2)[1]
                metadata = yaml.safe_load(yaml_str)
                metadata["_source"] = "SKILL.md"
                return metadata
            except Exception:
                pass

    return None


def _list_skills_in_dir(skill_dir: Path, source: str) -> list[dict]:
    """列出指定目录中的所有 Skill"""
    if not skill_dir.exists():
        return []

    skills = []
    for d in skill_dir.iterdir():
        if not d.is_dir():
            continue

        metadata = _load_skill_metadata(d)
        if metadata:
            metadata["id"] = d.name
            metadata["source"] = source
            metadata["path"] = str(d)
            skills.append(metadata)

    return skills


# ── 路由 ──────────────────────────────────────────
@router.get("")
def list_skills(
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """列出所有 Skill（内置 + 用户自定义）"""
    builtin_dir, user_dir = builtin_dir

    builtin_skills = _list_skills_in_dir(builtin_dir, "builtin")
    user_skills = _list_skills_in_dir(user_dir, "user")

    return {"code": 0, "data": {"builtin": builtin_skills, "user": user_skills}}


@router.get("/{skill_name}")
def get_skill(
    skill_name: str,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """获取指定 Skill 的详情"""
    builtin_dir, user_dir = builtin_dir

    # 先搜索内置 Skill
    skill_dir = builtin_dir / skill_name
    if skill_dir.exists():
        metadata = _load_skill_metadata(skill_dir)
        if metadata:
            metadata["id"] = skill_name
            metadata["source"] = "builtin"
            metadata["path"] = str(skill_dir)

            # 读取 SKILL.md 内容
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                metadata["content"] = skill_md.read_text(encoding="utf-8")

            return {"code": 0, "data": metadata}

    # 再搜索用户 Skill
    skill_dir = user_dir / skill_name
    if skill_dir.exists():
        metadata = _load_skill_metadata(skill_dir)
        if metadata:
            metadata["id"] = skill_name
            metadata["source"] = "user"
            metadata["path"] = str(skill_dir)

            # 读取 SKILL.md 内容
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                metadata["content"] = skill_md.read_text(encoding="utf-8")

            return {"code": 0, "data": metadata}

    raise HTTPException(status_code=404, detail="Skill 不存在")


@router.post("/{skill_name}/enable")
def enable_skill(
    skill_name: str,
    body: SkillEnableReq,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """启用/禁用 Skill"""
    builtin_dir, user_dir = builtin_dir

    # 查找 Skill
    skill_dir = None
    for d in [builtin_dir, user_dir]:
        if (d / skill_name).exists():
            skill_dir = d / skill_name
            break

    if not skill_dir:
        raise HTTPException(status_code=404, detail="Skill 不存在")

    # 更新 metadata.json
    metadata_file = skill_dir / "metadata.json"
    skill_md_file = skill_dir / "SKILL.md"

    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    elif skill_md_file.exists():
        # 从 SKILL.md 创建 metadata.json
        metadata = _load_skill_metadata(skill_dir) or {}
    else:
        metadata = {}

    metadata["enabled"] = body.enabled

    # 保存回 metadata.json
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {"code": 0, "message": "已更新"}


@router.post("/{skill_name}/priority")
def update_skill_priority(
    skill_name: str,
    body: SkillPriorityReq,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """更新 Skill 优先级"""
    builtin_dir, user_dir = builtin_dir

    # 查找 Skill
    skill_dir = None
    for d in [builtin_dir, user_dir]:
        if (d / skill_name).exists():
            skill_dir = d / skill_name
            break

    if not skill_dir:
        raise HTTPException(status_code=404, detail="Skill 不存在")

    # 更新 metadata.json
    metadata_file = skill_dir / "metadata.json"
    skill_md_file = skill_dir / "SKILL.md"

    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    elif skill_md_file.exists():
        metadata = _load_skill_metadata(skill_dir) or {}
    else:
        metadata = {}

    metadata["priority"] = body.priority

    # 保存回 metadata.json
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {"code": 0, "message": "已更新"}


@router.post("/{skill_name}/run")
def run_skill(
    skill_name: str,
    body: dict,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """运行 Skill"""
    builtin_dir, user_dir = builtin_dir

    # 查找 Skill
    skill_dir = None
    for d in [builtin_dir, user_dir]:
        if (d / skill_name).exists():
            skill_dir = d / skill_name
            break

    if not skill_dir:
        raise HTTPException(status_code=404, detail="Skill 不存在")

    # 读取 SKILL.md
    skill_md_file = skill_dir / "SKILL.md"
    if not skill_md_file.exists():
        raise HTTPException(status_code=400, detail="Skill 缺少 SKILL.md 文件")

    skill_content = skill_md_file.read_text(encoding="utf-8")

    # TODO: 实际运行 Skill（调用 LLM）
    # 这里先返回模拟结果
    return {
        "code": 0,
        "data": {
            "skill_name": skill_name,
            "input": body.get("input", ""),
            "output": "Skill 运行结果（待实现）",
            "status": "pending"
        }
    }


@router.get("/{skill_name}/errors")
def get_skill_errors(
    skill_name: str,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """获取 Skill 的错误日志"""
    # TODO: 实现错误日志读取
    return {
        "code": 0,
        "data": {
            "skill_name": skill_name,
            "errors": []
        }
    }


@router.post("")
def create_skill(
    body: SkillCreateReq,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """创建用户自定义 Skill"""
    _, user_dir = builtin_dir

    skill_dir = user_dir / body.name
    if skill_dir.exists():
        raise HTTPException(status_code=400, detail="Skill 已存在")

    # 创建 Skill 目录
    skill_dir.mkdir(parents=True, exist_ok=True)

    # 创建 SKILL.md
    skill_md_content = f"""---
name: {body.name}
description: {body.description}
---

# {body.name}

{body.description}

## Prompt

{body.prompt}
"""

    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    # 创建 metadata.json
    metadata = {
        "name": body.name,
        "description": body.description,
        "enabled": True,
        "priority": 0,
        "created_at": __import__("datetime").datetime.now().isoformat()
    }

    (skill_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {"code": 0, "message": "Skill 创建成功", "data": {"id": body.name}}


@router.delete("/{skill_name}")
def delete_skill(
    skill_name: str,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """删除用户自定义 Skill（不能删除内置 Skill）"""
    _, user_dir = builtin_dir

    skill_dir = user_dir / skill_name
    if not skill_dir.exists():
        raise HTTPException(status_code=404, detail="Skill 不存在或为内置 Skill")

    import shutil
    shutil.rmtree(skill_dir)

    return {"code": 0, "message": "Skill 已删除"}
