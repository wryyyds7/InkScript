"""
人物小传生成 Skill - 为每个角色生成详细的人物小传
"""

import json
import yaml
from collections import defaultdict
from typing import Dict, Any, List


def generate_character_profiles(yaml_content: str, llm_client=None) -> Dict[str, Any]:
    """
    生成角色人物小传
    
    Args:
        yaml_content: YAML 格式的剧本内容
        llm_client: LLM 客户端实例
        
    Returns:
        人物小传生成结果
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return {"profiles": []}
    
    scenes = script_data.get('scenes', [])
    
    # 1. 提取角色统计数据
    character_stats = _extract_character_stats(scenes)
    
    # 2. 使用 LLM 生成人物小传
    profiles = []
    for character, stats in character_stats.items():
        if llm_client and stats['dialogue_count'] >= 3:  # 只为主要角色生成
            profile = _generate_profile_with_llm(character, stats, scenes, llm_client)
        else:
            profile = _generate_basic_profile(character, stats, scenes)
        
        profiles.append(profile)
    
    # 按台词量排序
    profiles.sort(key=lambda x: x['stats']['dialogue_count'], reverse=True)
    
    return {
        "profiles": profiles,
        "total_characters": len(profiles)
    }


def _extract_character_stats(scenes: List[dict]) -> Dict[str, dict]:
    """提取角色统计数据"""
    character_stats = defaultdict(lambda: {
        'appearances': 0,
        'dialogue_count': 0,
        'dialogue_length': 0,
        'emotions': defaultdict(int),
        'scenes': [],
        'key_scenes': []
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
                
                stats = character_stats[character]
                stats['appearances'] += 1
                stats['dialogue_count'] += 1
                stats['dialogue_length'] += len(content)
                stats['emotions'][emotion] += 1
                scene_characters.add(character)
        
        # 记录该场景出现的角色
        for character in scene_characters:
            character_stats[character]['scenes'].append(scene_heading)
    
    return dict(character_stats)


def _generate_basic_profile(character: str, stats: dict, scenes: List[dict]) -> dict:
    """生成基础人物小传（不使用 LLM）"""
    # 获取主要情绪
    top_emotions = sorted(stats['emotions'].items(), key=lambda x: x[1], reverse=True)[:3]
    top_emotions_str = '、'.join(e[0] for e in top_emotions)
    
    # 生成 Markdown 内容
    markdown = f"""# {character} - 人物小传

## 基本信息

- **出场次数**: {stats['appearances']} 次
- **台词数量**: {stats['dialogue_count']} 条
- **台词总长度**: {stats['dialogue_length']} 字
- **主要情绪**: {top_emotions_str}

## 性格分析

（需要 LLM 分析）

## 人物弧光

（需要 LLM 分析）

## 角色关系

（需要 LLM 分析）

## 出场场景

{chr(10).join(f"- {s}" for s in stats['scenes'][:10])}
"""
    
    return {
        "character": character,
        "stats": dict(stats),
        "profile_markdown": markdown,
        "needs_llm": True
    }


def _generate_profile_with_llm(character: str, stats: dict, scenes: List[dict], llm_client) -> dict:
    """使用 LLM 生成详细人物小传"""
    # 提取该角色的关键场景
    character_scenes = []
    for i, scene in enumerate(scenes):
        beats = scene.get('beats', [])
        character_beats = [b for b in beats if b.get('type') == 'dialogue' and b.get('character') == character]
        
        if character_beats:
            scene_info = {
                'heading': scene.get('heading', f'场景{i+1}'),
                'beats': character_beats
            }
            character_scenes.append(scene_info)
    
    # 构建 Prompt
    prompt = f"""你是专业的剧本角色分析师。请为以下角色生成详细的人物小传。

**角色名称**: {character}

**统计数据**:
- 出场次数: {stats['appearances']} 次
- 台词数量: {stats['dialogue_count']} 条
- 台词总长度: {stats['dialogue_length']} 字
- 情绪分布: {dict(stats['emotions'])}

**关键场景中的台词**（部分）:
"""
    
    # 添加部分关键场景
    for scene_info in character_scenes[:5]:
        prompt += f"\n场景: {scene_info['heading']}\n"
        for beat in scene_info['beats'][:3]:
            prompt += f"  {character}: {beat.get('content', '')} ({beat.get('emotion', '中性')})\n"
    
    prompt += """
请生成人物小传，输出 JSON 格式：
```json
{
  "character": "角色名",
  "personality": "性格分析（200字左右）",
  "character_arc": "人物弧光描述（角色的成长/变化轨迹，200字左右）",
  "relationships": [
    {"character": "其他角色名", "relation": "关系描述"}
  ],
  "key_scenes": ["关键场景1", "关键场景2"],
  "summary": "角色总结（100字左右）"
}
```

请只输出 JSON，不要有其他内容。
"""
    
    try:
        response = llm_client.complete(prompt, temperature=0.7)
        content = response.get("content", "")
        
        # 提取 JSON
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        llm_data = json.loads(content)
        
        # 生成 Markdown
        markdown = f"""# {character} - 人物小传

## 基本信息

- **出场次数**: {stats['appearances']} 次
- **台词数量**: {stats['dialogue_count']} 条
- **台词总长度**: {stats['dialogue_length']} 字

## 性格分析

{llm_data.get('personality', '（分析失败）')}

## 人物弧光

{llm_data.get('character_arc', '（分析失败）')}

## 角色关系

{chr(10).join(f"- **{r.get('character', '')}**: {r.get('relation', '')}" for r in llm_data.get('relationships', []))}

## 角色总结

{llm_data.get('summary', '（分析失败）')}

## 出场场景

{chr(10).join(f"- {s}" for s in stats['scenes'][:10])}
"""
        
        return {
            "character": character,
            "stats": dict(stats),
            "profile_markdown": markdown,
            "llm_data": llm_data,
            "needs_llm": False
        }
        
    except Exception as e:
        # LLM 失败，返回基础版本
        return _generate_basic_profile(character, stats, scenes)


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数
    
    Args:
        data: 输入数据，包含 YAML 剧本内容和风格参数
        config: 配置参数（包含 LLM 客户端）
        
    Returns:
        人物小传生成结果
    """
    yaml_content = data.get("yaml_content", "")
    
    if not yaml_content:
        return {
            "success": False,
            "error": "缺少 YAML 剧本内容"
        }
    
    llm_client = config.get("llm_client")
    if not llm_client:
        # 没有 LLM 也行，生成基础版本
        pass
    
    try:
        result = generate_character_profiles(yaml_content, llm_client)
        
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
    
    # 模拟 LLM 客户端
    class MockLLMClient:
        def complete(self, prompt, temperature=0.7):
            return {"content": json.dumps({
                "character": "Jack",
                "personality": "性格冲动，情绪化，容易相信别人但也容易失望",
                "character_arc": "从信任到失望，经历了情感上的巨大打击",
                "relationships": [
                    {"character": "Amy", "relation": "被欺骗的朋友/恋人"}
                ],
                "key_scenes": ["咖啡店 - 白天"],
                "summary": "Jack 是一个情感丰富但容易受伤的角色"
            }, ensure_ascii=False)}
    
    result = run(
        {"yaml_content": test_yaml},
        {"llm_client": MockLLMClient()}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
