"""
角色分析报告 Skill - 分析剧本中的角色数据
"""

import yaml
from collections import defaultdict
from typing import Dict, List, Any


def analyze_characters(yaml_content: str) -> Dict[str, Any]:
    """
    分析剧本中的角色数据
    
    Args:
        yaml_content: YAML 格式的剧本内容
        
    Returns:
        角色分析结果
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return {}
    
    # 统计数据
    character_stats = defaultdict(lambda: {
        'appearances': 0,
        'dialogue_count': 0,
        'dialogue_length': 0,
        'emotions': defaultdict(int),
        'scenes': set()
    })
    
    total_dialogue = 0
    
    # 遍历场景
    for scene in script_data.get('scenes', []):
        scene_id = scene.get('heading', 'unknown')
        
        for beat in scene.get('beats', []):
            if beat.get('type') == 'dialogue':
                character = beat.get('character', 'unknown')
                content = beat.get('content', '')
                emotion = beat.get('emotion', 'neutral')
                
                # 更新统计
                stats = character_stats[character]
                stats['appearances'] += 1
                stats['dialogue_count'] += 1
                stats['dialogue_length'] += len(content)
                stats['emotions'][emotion] += 1
                stats['scenes'].add(scene_id)
                
                total_dialogue += 1
    
    # 计算对白占比
    result = {
        'total_dialogue_beats': total_dialogue,
        'characters': []
    }
    
    for character, stats in character_stats.items():
        dialogue_ratio = stats['dialogue_count'] / total_dialogue if total_dialogue > 0 else 0
        
        result['characters'].append({
            'name': character,
            'appearances': stats['appearances'],
            'dialogue_count': stats['dialogue_count'],
            'dialogue_length': stats['dialogue_length'],
            'dialogue_ratio': round(dialogue_ratio, 3),
            'emotion_distribution': dict(stats['emotions']),
            'scenes_count': len(stats['scenes'])
        })
    
    # 按对白数量排序
    result['characters'].sort(key=lambda x: x['dialogue_count'], reverse=True)
    
    return result


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数
    
    Args:
        data: 输入数据，包含 YAML 剧本内容
        config: 配置参数
        
    Returns:
        分析结果
    """
    yaml_content = data.get('yaml_content', '')
    
    if not yaml_content:
        return {
            'success': False,
            'error': '缺少 YAML 剧本内容'
        }
    
    try:
        analysis_result = analyze_characters(yaml_content)
        
        return {
            'success': True,
            'data': analysis_result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # 测试代码
    test_yaml = """
scenes:
  - heading: 咖啡店 - 白天
    beats:
      - type: dialogue
        character: Jack
        content: 你竟然骗我！
        emotion: 愤怒
      - type: dialogue
        character: Amy
        content: 这只是善意的谎言。
        emotion: 冷静
      - type: dialogue
        character: Jack
        content: 我再也不相信你了。
        emotion: 绝望
"""
    
    result = analyze_characters(test_yaml)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
