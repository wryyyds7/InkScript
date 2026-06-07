"""
剧本结构分析 Skill - 幕次均衡、节奏分析、角色戏份分析
"""

import json
import yaml
from collections import defaultdict
from typing import Dict, Any, List


def analyze_structure(yaml_content: str) -> Dict[str, Any]:
    """
    分析剧本结构
    
    Args:
        yaml_content: YAML 格式的剧本内容
        
    Returns:
        结构分析结果
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return {}
    
    scenes = script_data.get('scenes', [])
    
    # ── 1. 幕次均衡分析 ──────────────────────
    act_analysis = _analyze_act_balance(scenes)
    
    # ── 2. 节奏分析 ──────────────────────
    pace_analysis = _analyze_pace(scenes)
    
    # ── 3. 角色戏份分析 ──────────────────────
    character_analysis = _analyze_character_screen_time(scenes)
    
    result = {
        'act_balance': act_analysis,
        'pace_analysis': pace_analysis,
        'character_analysis': character_analysis,
        'total_scenes': len(scenes),
        'total_dialogues': sum(len(s.get('beats', [])) for s in scenes)
    }
    
    return result


def _analyze_act_balance(scenes: List[dict]) -> Dict[str, Any]:
    """幕次均衡分析"""
    # 简单按场景数平分到3幕
    total_scenes = len(scenes)
    if total_scenes == 0:
        return {'acts': [], 'suggestions': []}
    
    act_size = total_scenes // 3
    acts = []
    
    for i in range(3):
        start = i * act_size
        end = (i + 1) * act_size if i < 2 else total_scenes
        act_scenes = scenes[start:end]
        
        # 计算该幕的台词量
        dialogue_count = sum(
            len([b for b in s.get('beats', []) if b.get('type') == 'dialogue'])
            for s in act_scenes
        )
        
        acts.append({
            'act_num': i + 1,
            'scene_count': len(act_scenes),
            'dialogue_count': dialogue_count,
            'scenes': [s.get('heading', '') for s in act_scenes]
        })
    
    # 生成建议
    suggestions = []
    dialogue_counts = [a['dialogue_count'] for a in acts]
    avg_dialogue = sum(dialogue_counts) / len(dialogue_counts) if dialogue_counts else 0
    
    for act in acts:
        if act['dialogue_count'] < avg_dialogue * 0.7:
            suggestions.append(f"第 {act['act_num']} 幕台词量偏少（{act['dialogue_count']} 条），建议增加对话或合并到其他幕")
        elif act['dialogue_count'] > avg_dialogue * 1.3:
            suggestions.append(f"第 {act['act_num']} 幕台词量偏多（{act['dialogue_count']} 条），建议拆分或删减")
    
    return {
        'acts': acts,
        'avg_dialogue_per_act': round(avg_dialogue, 1),
        'suggestions': suggestions
    }


def _analyze_pace(scenes: List[dict]) -> Dict[str, Any]:
    """节奏分析"""
    # 将情绪转换为数值
    emotion_values = {
        '平静': 1, '中性': 2, '开心': 3, '兴奋': 4, '愤怒': 4,
        '悲伤': 2, '恐惧': 3, '冷静': 2, '绝望': 1, '紧张': 3
    }
    
    scene_emotions = []
    for i, scene in enumerate(scenes):
        beats = scene.get('beats', [])
        emotions = [b.get('emotion', '中性') for b in beats if b.get('type') == 'dialogue']
        
        if emotions:
            avg_emotion = sum(emotion_values.get(e, 2) for e in emotions) / len(emotions)
        else:
            avg_emotion = 2  # 默认中性
        
        scene_emotions.append({
            'scene_index': i,
            'heading': scene.get('heading', ''),
            'avg_emotion': round(avg_emotion, 1),
            'beat_count': len(beats)
        })
    
    # 标记情绪平淡区（连续3个场景情绪强度 < 2）
    flat_areas = []
    for i in range(len(scene_emotions) - 2):
        if all(s['avg_emotion'] < 2 for s in scene_emotions[i:i+3]):
            flat_areas.append({
                'start_scene': scene_emotions[i]['scene_index'],
                'end_scene': scene_emotions[i+2]['scene_index'],
                'start_heading': scene_emotions[i]['heading'],
                'end_heading': scene_emotions[i+2]['heading']
            })
    
    # 标记情绪过山车区（连续3个场景情绪强度变化 > 3）
    roller_coaster = []
    for i in range(len(scene_emotions) - 2):
        emotions = [s['avg_emotion'] for s in scene_emotions[i:i+3]]
        if max(emotions) - min(emotions) > 3:
            roller_coaster.append({
                'start_scene': scene_emotions[i]['scene_index'],
                'end_scene': scene_emotions[i+2]['scene_index'],
                'start_heading': scene_emotions[i]['heading'],
                'end_heading': scene_emotions[i+2]['heading'],
                'emotion_range': f"{min(emotions):.1f} - {max(emotions):.1f}"
            })
    
    return {
        'scene_emotions': scene_emotions,
        'flat_areas': flat_areas,
        'roller_coaster_areas': roller_coaster,
        'flat_area_count': len(flat_areas),
        'roller_coaster_count': len(roller_coaster)
    }


def _analyze_character_screen_time(scenes: List[dict]) -> Dict[str, Any]:
    """角色戏份分析"""
    character_dialogues = defaultdict(int)
    total_dialogues = 0
    
    for scene in scenes:
        for beat in scene.get('beats', []):
            if beat.get('type') == 'dialogue':
                character = beat.get('character', 'unknown')
                character_dialogues[character] += 1
                total_dialogues += 1
    
    # 计算占比
    character_ratios = []
    for character, count in character_dialogues.items():
        ratio = count / total_dialogues if total_dialogues > 0 else 0
        character_ratios.append({
            'name': character,
            'dialogue_count': count,
            'ratio': round(ratio, 3),
            'ratio_percent': round(ratio * 100, 1)
        })
    
    # 排序
    character_ratios.sort(key=lambda x: x['dialogue_count'], reverse=True)
    
    # 标记戏份过少/过多的角色
    low_screen_time = [c for c in character_ratios if c['ratio'] < 0.05]
    high_screen_time = [c for c in character_ratios if c['ratio'] > 0.4]
    
    suggestions = []
    if low_screen_time:
        suggestions.append(f"以下角色戏份过少（占比 < 5%）：{', '.join(c['name'] for c in low_screen_time)}，建议增加戏份或删除")
    if high_screen_time:
        suggestions.append(f"以下角色戏份过多（占比 > 40%）：{', '.join(c['name'] for c in high_screen_time)}，建议适当减少戏份")
    
    return {
        'characters': character_ratios,
        'total_dialogues': total_dialogues,
        'low_screen_time': low_screen_time,
        'high_screen_time': high_screen_time,
        'suggestions': suggestions
    }


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
        analysis_result = analyze_structure(yaml_content)
        
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
  - heading: 公园 - 傍晚
    beats:
      - type: dialogue
        character: Jack
        content: 这里真安静。
        emotion: 平静
      - type: dialogue
        character: Amy
        content: 我们应该好好谈谈。
        emotion: 冷静
"""
    
    result = analyze_structure(test_yaml)
    print(json.dumps(result, indent=2, ensure_ascii=False))
