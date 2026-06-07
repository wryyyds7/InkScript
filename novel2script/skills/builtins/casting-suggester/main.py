"""
选角建议 Skill - 根据角色特征推荐演员
"""

import json
import yaml
from collections import defaultdict
from typing import Dict, Any, List


def suggest_casting(yaml_content: str, actor_library: List[dict] = None, llm_client=None) -> Dict[str, Any]:
    """
    生成选角建议
    
    Args:
        yaml_content: YAML 格式的剧本内容
        actor_library: 用户提供的演员库（可选）
        llm_client: LLM 客户端实例
        
    Returns:
        选角建议结果
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return {"casting": []}
    
    scenes = script_data.get('scenes', [])
    
    # 1. 提取角色特征
    character_profiles = _extract_character_profiles(scenes)
    
    # 2. 生成选角建议
    casting_suggestions = []
    for character, profile in character_profiles.items():
        if llm_client:
            suggestions = _suggest_with_llm(character, profile, actor_library, llm_client)
        else:
            suggestions = _suggest_basic(character, profile, actor_library)
        
        casting_suggestions.append({
            'character': character,
            'profile': profile,
            'suggestions': suggestions
        })
    
    # 按台词量排序
    casting_suggestions.sort(key=lambda x: x['profile']['dialogue_count'], reverse=True)
    
    return {
        "casting": casting_suggestions,
        "total_characters": len(casting_suggestions)
    }


def _extract_character_profiles(scenes: List[dict]) -> Dict[str, dict]:
    """提取角色特征"""
    character_profiles = defaultdict(lambda: {
        'dialogue_count': 0,
        'dialogue_length': 0,
        'emotions': defaultdict(int),
        'scenes': [],
        'sample_dialogues': []
    })
    
    for i, scene in enumerate(scenes):
        scene_heading = scene.get('heading', f'场景{i+1}')
        beats = scene.get('beats', [])
        
        scene_characters = set()
        for beat in beats:
            if beat.get('type') == 'dialogue':
                character = beat.get('character', 'unknown')
                content = beat.get('content', '')
                emotion = beat.get('emotion', '中性')
                
                profile = character_profiles[character]
                profile['dialogue_count'] += 1
                profile['dialogue_length'] += len(content)
                profile['emotions'][emotion] += 1
                scene_characters.add(character)
                
                # 保存样本对话（最多3条）
                if len(profile['sample_dialogues']) < 3:
                    profile['sample_dialogues'].append(content)
        
        for character in scene_characters:
            character_profiles[character]['scenes'].append(scene_heading)
    
    # 转换 defaultdict 为普通 dict
    result = {}
    for character, profile in character_profiles.items():
        result[character] = {
            'dialogue_count': profile['dialogue_count'],
            'dialogue_length': profile['dialogue_length'],
            'avg_dialogue_length': round(profile['dialogue_length'] / profile['dialogue_count'], 1) if profile['dialogue_count'] > 0 else 0,
            'emotions': dict(profile['emotions']),
            'scene_count': len(profile['scenes']),
            'scenes': profile['scenes'][:5],  # 只保留前5个场景
            'sample_dialogues': profile['sample_dialogues']
        }
    return result


def _suggest_basic(character: str, profile: dict, actor_library: List[dict] = None) -> List[dict]:
    """生成基础选角建议（不使用 LLM）"""
    suggestions = []
    
    if actor_library:
        # 根据演员库简单匹配
        for actor in actor_library[:3]:
            suggestions.append({
                'actor': actor.get('name', '未知演员'),
                'match_score': 0.7,  # 默认匹配度
                'reason': '基于演员库基础匹配'
            })
    else:
        # 没有演员库，生成描述性建议
        suggestions.append({
            'actor': f"建议选择具有丰富话剧经验的成熟演员",
            'match_score': 0.8,
            'reason': f"该角色有 {profile['dialogue_count']} 条台词，需要较强的台词功底"
        })
    
    return suggestions


def _suggest_with_llm(character: str, profile: dict, actor_library: List[dict], llm_client) -> List[dict]:
    """使用 LLM 生成选角建议"""
    # 构建 Prompt
    prompt = f"""你是专业的选角导演。请根据以下角色特征，推荐合适的演员。

**角色名称**: {character}

**角色特征**:
- 台词数量: {profile['dialogue_count']} 条
- 台词总长度: {profile['dialogue_length']} 字
- 平均台词长度: {profile['avg_dialogue_length']} 字
- 情绪分布: {profile['emotions']}
- 出场场景数: {profile['scene_count']} 个

**样本对话**:
"""
    
    for dialogue in profile['sample_dialogues']:
        prompt += f"- {dialogue}\n"
    
    if actor_library:
        prompt += f"\n**可选演员库**:\n"
        for actor in actor_library[:10]:
            prompt += f"- {actor.get('name', '')}: {actor.get('description', '')}\n"
    
    prompt += """
请推荐 3-5 位合适演员，输出 JSON 格式：
```json
[
  {{
    "actor": "演员姓名",
    "match_score": 0.95,
    "reason": "推荐理由（100字左右）",
    "role_type": "主角/配角/客串"
  }}
]
```

请只输出 JSON 数组，不要有其他内容。
"""
    
    try:
        response = llm_client.complete(prompt, temperature=0.7)
        content = response.get("content", "")
        
        # 提取 JSON
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        suggestions = json.loads(content)
        return suggestions if isinstance(suggestions, list) else _suggest_basic(character, profile, actor_library)
        
    except Exception as e:
        # LLM 失败，返回基础版本
        return _suggest_basic(character, profile, actor_library)


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数
    
    Args:
        data: 输入数据，包含 YAML 剧本内容和可选演员库
        config: 配置参数（包含 LLM 客户端）
        
    Returns:
        选角建议结果
    """
    yaml_content = data.get("yaml_content", "")
    actor_library = data.get("actor_library", None)
    
    if not yaml_content:
        return {
            "success": False,
            "error": "缺少 YAML 剧本内容"
        }
    
    llm_client = config.get("llm_client")
    # 即使没有 LLM 也行，会生成基础版本
    
    try:
        result = suggest_casting(yaml_content, actor_library, llm_client)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试代码
    test_yaml = """
title: 测试剧本
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
    
    # 模拟 LLM 客户端
    class MockLLMClient:
        def complete(self, prompt, temperature=0.7):
            return {"content": json.dumps([
                {
                    "actor": "建议选择演技精湛的成熟男演员",
                    "match_score": 0.9,
                    "reason": "Jack 角色情绪起伏大，需要能够驾驭愤怒、绝望等强烈情绪的演员",
                    "role_type": "主角"
                },
                {
                    "actor": "建议选择气质冷静的女演员",
                    "match_score": 0.85,
                    "reason": "Amy 角色情绪稳定，需要在对话中保持冷静，形成对比",
                    "role_type": "主角"
                }
            ], ensure_ascii=False)}
    
    result = run(
        {"yaml_content": test_yaml},
        {"llm_client": MockLLMClient()}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
