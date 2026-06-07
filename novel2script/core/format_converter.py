"""格式转换器 — 将 Script/YAML 转换为各种格式（纯本地，不调 API）

支持的格式:
- yaml: Script → YAML 字符串
- txt: YAML → 纯文本剧本
- html: YAML → HTML 剧本页面
- fountain: YAML → Fountain 剧本格式
- json: Script → JSON
"""

from __future__ import annotations

import json as _json

from novel2script.schema import Script, to_yaml, from_yaml


def _get_title(script: Script) -> str:
    """获取剧本标题"""
    return getattr(script, 'title', None) or getattr(script.meta, 'title', None) or "未命名剧本"


def script_to_txt(script: Script) -> str:
    """将 Script 转换为纯文本剧本格式"""
    title = _get_title(script)
    lines = []
    lines.append(title)
    lines.append("=" * 40)
    lines.append("")

    if script.characters:
        lines.append("【角色列表】")
        for c in script.characters:
            aliases_str = f"（别名：{'、'.join(c.aliases)}）" if c.aliases else ""
            lines.append(f"  - {c.name}{aliases_str}")
        lines.append("")

    for scene in script.scenes:
        heading = scene.title or f"场景 {scene.scene_id}"
        loc_time = []
        if scene.location:
            loc_time.append(scene.location)
        if scene.time:
            loc_time.append(scene.time)
        if loc_time:
            heading += f" — {'，'.join(loc_time)}"

        lines.append(f"【{heading}】")
        lines.append("-" * 30)

        for beat in scene.beats:
            beat_type = getattr(beat, 'type', None)
            if beat_type == 'dialogue':
                character = getattr(beat, 'character', '未知')
                content = getattr(beat, 'content', '')
                emotion = getattr(beat, 'emotion', None)
                emo_str = f"（{emotion}）" if emotion else ""
                lines.append(f"  {character}{emo_str}：{content}")
            elif beat_type == 'action':
                content = getattr(beat, 'content', '')
                lines.append(f"  【动作】{content}")
            elif beat_type == 'narration':
                content = getattr(beat, 'content', '')
                lines.append(f"  【旁白】{content}")
            elif beat_type == 'heading':
                text = getattr(beat, 'text', '')
                lines.append(f"  {text}")
            else:
                content = getattr(beat, 'content', '') or ''
                lines.append(f"  {content}")

        lines.append("")

    return "\n".join(lines)


def script_to_html(script: Script) -> str:
    """将 Script 转换为 HTML 剧本页面"""
    title = _get_title(script)
    lines = []
    lines.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{ font-family: 'Noto Serif SC', serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; }}
h1 {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
.character-list {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
.character-list li {{ margin: 5px 0; }}
.scene {{ margin: 30px 0; border-left: 3px solid #4a90d9; padding-left: 15px; }}
.scene-heading {{ font-weight: bold; font-size: 1.1em; color: #4a90d9; margin-bottom: 10px; }}
.dialogue {{ margin: 8px 0; }}
.dialogue .speaker {{ font-weight: bold; color: #333; }}
.dialogue .emotion {{ color: #888; font-size: 0.9em; }}
.dialogue .content {{ margin-left: 10px; }}
.action {{ color: #555; font-style: italic; margin: 5px 0; }}
.narration {{ color: #666; margin: 5px 0; padding-left: 20px; border-left: 2px solid #ddd; }}
</style>
</head>
<body>
<h1>{title}</h1>
""".format(title=title))

    if script.characters:
        lines.append('<div class="character-list"><h3>角色列表</h3><ul>')
        for c in script.characters:
            aliases_str = f"（{'、'.join(c.aliases)}）" if c.aliases else ""
            desc = f" — {c.description}" if c.description else ""
            lines.append(f'<li><strong>{c.name}</strong>{aliases_str}{desc}</li>')
        lines.append('</ul></div>')

    for scene in script.scenes:
        heading = scene.title or f"场景 {scene.scene_id}"
        loc_time = []
        if scene.location:
            loc_time.append(scene.location)
        if scene.time:
            loc_time.append(scene.time)
        if loc_time:
            heading += f" — {'，'.join(loc_time)}"

        lines.append(f'<div class="scene"><div class="scene-heading">{heading}</div>')

        for beat in scene.beats:
            beat_type = getattr(beat, 'type', None)
            if beat_type == 'dialogue':
                character = getattr(beat, 'character', '未知')
                content = getattr(beat, 'content', '')
                emotion = getattr(beat, 'emotion', None)
                emo = f'<span class="emotion">（{emotion}）</span>' if emotion else ''
                lines.append(f'<div class="dialogue"><span class="speaker">{character}</span>{emo}<span class="content">：{content}</span></div>')
            elif beat_type == 'action':
                content = getattr(beat, 'content', '')
                lines.append(f'<div class="action">【动作】{content}</div>')
            elif beat_type == 'narration':
                content = getattr(beat, 'content', '')
                lines.append(f'<div class="narration">【旁白】{content}</div>')
            elif beat_type == 'heading':
                text = getattr(beat, 'text', '')
                lines.append(f'<div><strong>{text}</strong></div>')
            else:
                content = getattr(beat, 'content', '') or ''
                lines.append(f'<div>{content}</div>')

        lines.append('</div>')

    lines.append('</body></html>')
    return "\n".join(lines)


def script_to_fountain(script: Script) -> str:
    """将 Script 转换为 Fountain 剧本格式"""
    lines = []
    lines.append(f"Title: {_get_title(script)}")
    author = getattr(script, 'author', None) or getattr(script.meta, 'author', None)
    if author:
        lines.append(f"Author: {author}")
    lines.append("")

    for scene in script.scenes:
        heading = scene.title or f"Scene {scene.scene_id}"
        location_line = f"INT./EXT. {scene.location or 'UNKNOWN'} - {scene.time or 'DAY'}"
        lines.append(f".{heading.upper()}")
        lines.append(location_line)
        lines.append("")

        for beat in scene.beats:
            beat_type = getattr(beat, 'type', None)
            if beat_type == 'dialogue':
                character = getattr(beat, 'character', 'UNKNOWN').upper()
                content = getattr(beat, 'content', '')
                emotion = getattr(beat, 'emotion', None)
                lines.append(f"@{character}")
                if emotion:
                    lines.append(f"  ({emotion})")
                lines.append(f"  {content}")
                lines.append("")
            elif beat_type == 'action':
                content = getattr(beat, 'content', '')
                lines.append(content)
                lines.append("")
            elif beat_type == 'narration':
                content = getattr(beat, 'content', '')
                lines.append(f"= {content}")
                lines.append("")
            elif beat_type == 'heading':
                text = getattr(beat, 'text', '')
                lines.append(f".{text}")
                lines.append("")
            else:
                content = getattr(beat, 'content', '') or ''
                lines.append(content)
                lines.append("")

    return "\n".join(lines)


def yaml_to_txt(yaml_str: str) -> str:
    """YAML 字符串 → TXT"""
    script = from_yaml(yaml_str)
    return script_to_txt(script)


def yaml_to_html(yaml_str: str) -> str:
    """YAML 字符串 → HTML"""
    script = from_yaml(yaml_str)
    return script_to_html(script)


def yaml_to_fountain(yaml_str: str) -> str:
    """YAML 字符串 → Fountain"""
    script = from_yaml(yaml_str)
    return script_to_fountain(script)


def script_to_json_str(script: Script) -> str:
    """Script → JSON 字符串"""
    return _json.dumps(
        script.model_dump(exclude_none=True, mode="json"),
        ensure_ascii=False,
        indent=2,
    )


# 格式映射
CONVERTERS = {
    'yaml': to_yaml,
    'txt': script_to_txt,
    'html': script_to_html,
    'fountain': script_to_fountain,
    'json': script_to_json_str,
}
