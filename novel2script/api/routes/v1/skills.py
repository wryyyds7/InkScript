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
    import sys
    import importlib.util

    builtin_dir, user_dir = builtin_dir

    # 查找 Skill
    skill_dir = None
    skill_source = None
    for d, source in [(builtin_dir, "builtin"), (user_dir, "user")]:
        if (d / skill_name).exists():
            skill_dir = d / skill_name
            skill_source = source
            break

    if not skill_dir:
        raise HTTPException(status_code=404, detail="Skill 不存在")

    # 检查是否有 main.py
    main_py = skill_dir / "main.py"
    if not main_py.exists():
        raise HTTPException(status_code=400, detail="Skill 缺少 main.py 文件")

    try:
        # 动态加载 main.py
        spec = importlib.util.spec_from_file_location(f"skill_{skill_name}", main_py)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 检查是否有 run 函数
        if not hasattr(module, "run"):
            raise HTTPException(status_code=400, detail="Skill 的 main.py 缺少 run() 函数")

        # 准备配置（注入 LLM 客户端）
        from novel2script.llm_client import OpenAIClient
        llm_client = OpenAIClient()

        config = {
            "llm_client": llm_client
        }

        # 调用 run 函数
        result = module.run(body, config)

        return {
            "code": 0,
            "data": {
                "skill_name": skill_name,
                "result": result
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill 运行失败: {str(e)}")


@router.get("/{skill_name}/errors")
def get_skill_errors(
    skill_name: str,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """获取 Skill 的错误日志"""
    import os
    
    builtin_dir_path, user_dir_path = builtin_dir
    
    # 构建日志文件路径
    # skill_name 格式：builtin/skill_name 或 user/skill_name 或直接是 skill_name
    if "/" in skill_name:
        parts = skill_name.split("/")
        if len(parts) >= 2:
            skill_type = parts[0]  # builtin 或 user
            skill_name_only = parts[1]
            if skill_type == "builtin":
                log_dir = builtin_dir_path / skill_name_only
            else:
                log_dir = user_dir_path / skill_name_only
        else:
            log_dir = builtin_dir_path / skill_name
    else:
        # 默认在 builtin 目录中查找
        log_dir = builtin_dir_path / skill_name
    
    log_file = log_dir / "error.log"
    
    errors = []
    
    # 读取错误日志文件
    if log_file.exists():
        try:
            content = log_file.read_text(encoding="utf-8")
            # 解析日志条目（每个条目以 "[" 开头，以 "-"*50 结尾）
            entries = content.split("-" * 50)
            
            for entry in entries:
                if not entry.strip():
                    continue
                
                # 解析日志条目
                lines = entry.strip().split("\n")
                error_obj = {
                    "timestamp": "",
                    "skill": skill_name,
                    "error": "",
                    "context": "",
                    "raw": entry.strip()
                }
                
                for line in lines:
                    if line.startswith("[") and "]" in line:
                        # 提取时间戳
                        end_bracket = line.find("]")
                        error_obj["timestamp"] = line[1:end_bracket]
                        # 提取 Skill 名称
                        if "Skill:" in line:
                            error_obj["skill"] = line[end_bracket+1:].split("Skill:")[1].strip()
                    elif line.startswith("Error:"):
                        error_obj["error"] = line[6:].strip()
                    elif line.startswith("Context:"):
                        error_obj["context"] = line[8:].strip()
                
                errors.append(error_obj)
                
        except Exception as e:
            # 如果读取失败，返回错误信息
            errors.append({
                "timestamp": "",
                "skill": skill_name,
                "error": f"读取错误日志失败: {str(e)}",
                "context": "",
                "raw": ""
            })
    
    # 按时间戳倒序排列（最新的在前面）
    errors.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "code": 0,
        "data": {
            "skill_name": skill_name,
            "errors": errors
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


@router.post("/install")
def install_skill(
    body: dict,
    builtin_dir: tuple[Path, Path] = Depends(get_skills_dir),
):
    """从本地路径安装 Skill"""
    _, user_dir = builtin_dir

    path = body.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="缺少 path 参数")

    import shutil
    from pathlib import Path as PathObj
    src_path = PathObj(path)
    if not src_path.exists():
        raise HTTPException(status_code=404, detail="路径不存在")

    # 读取 Skill 元数据
    metadata_file = src_path / "metadata.json"
    skill_md_file = src_path / "SKILL.md"

    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    elif skill_md_file.exists():
        # 从 SKILL.md 解析元数据
        content = skill_md_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            import yaml
            try:
                yaml_str = content.split("---", 2)[1]
                metadata = yaml.safe_load(yaml_str)
            except Exception:
                metadata = {}
        else:
            metadata = {}
    else:
        raise HTTPException(status_code=400, detail="Skill 缺少 metadata.json 或 SKILL.md 文件")

    skill_name = metadata.get("name", src_path.name)
    dest_dir = user_dir / skill_name

    if dest_dir.exists():
        raise HTTPException(status_code=400, detail="Skill 已存在")

    # 复制 Skill 目录
    shutil.copytree(src_path, dest_dir)

    return {"code": 0, "message": "Skill 安装成功", "data": {"id": skill_name}}


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
