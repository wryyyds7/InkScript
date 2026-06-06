"""
Fountain 导出 Skill - 将 YAML 剧本转换为 Fountain 格式
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any


def convert_yaml_to_fountain(yaml_content: str) -> str:
    """
    将 YAML 格式的剧本转换为 Fountain 格式
    
    Args:
        yaml_content: YAML 格式的剧本内容
        
    Returns:
        Fountain 格式的剧本内容
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return ""
    
    fountain_lines = []
    
    # 添加标题页
    fountain_lines.append(f"Title: {script_data.get('title', '未命名剧本')}")
    fountain_lines.append(f"Author: {script_data.get('author', '未知作者')}")
    fountain_lines.append("")
    fountain_lines.append("=" * 50)
    fountain_lines.append("")
    
    # 遍历场景
    for scene in script_data.get('scenes', []):
        # 场景标题
        scene_heading = scene.get('heading', '未命名场景')
        fountain_lines.append(scene_heading.upper())
        fountain_lines.append("")
        
        # 场景描述
        if scene.get('description'):
            fountain_lines.append(scene['description'])
            fountain_lines.append("")
        
        # 遍历 beats
        for beat in scene.get('beats', []):
            beat_type = beat.get('type', 'action')
            
            if beat_type == 'dialogue':
                # 对话
                character = beat.get('character', '')
                content = beat.get('content', '')
                emotion = beat.get('emotion', '')
                
                # 角色名（大写）
                fountain_lines.append(character.upper())
                
                # 情绪标注（括号）
                if emotion:
                    fountain_lines.append(f"({emotion})")
                
                # 对话内容
                fountain_lines.append(content)
                fountain_lines.append("")
                
            elif beat_type == 'action':
                # 动作描述
                content = beat.get('content', '')
                fountain_lines.append(content)
                fountain_lines.append("")
                
            elif beat_type == 'narration':
                # 旁白（V.O. 或 O.S.）
                character = beat.get('character', '')
                content = beat.get('content', '')
                
                fountain_lines.append(f"{character.upper()} (V.O.)")
                fountain_lines.append(content)
                fountain_lines.append("")
                
            elif beat_type == 'transition':
                # 转场
                content = beat.get('content', '')
                fountain_lines.append(content.upper())
                fountain_lines.append("")
        
        fountain_lines.append("")
    
    return "\n".join(fountain_lines)


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数
    
    Args:
        data: 输入数据，包含 YAML 剧本内容
        config: 配置参数
        
    Returns:
        转换结果
    """
    yaml_content = data.get('yaml_content', '')
    
    if not yaml_content:
        return {
            'success': False,
            'error': '缺少 YAML 剧本内容'
        }
    
    try:
        fountain_content = convert_yaml_to_fountain(yaml_content)
        
        return {
            'success': True,
            'data': {
                'format': 'fountain',
                'content': fountain_content,
                'filename': f"{data.get('project_name', 'script')}.fountain"
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # 测试代码
    test_yaml = """
title: 测试剧本
author: 测试作者
scenes:
  - heading: 咖啡店 - 白天
    description: 一家温馨的咖啡店。
    beats:
      - type: dialogue
        character: Jack
        content: 你竟然骗我！
        emotion: 愤怒
      - type: action
        content: Jack 猛地拍桌子。
      - type: dialogue
        character: Amy
        content: 这只是善意的谎言。
        emotion: 冷静
"""
    
    result = convert_yaml_to_fountain(test_yaml)
    print(result)
