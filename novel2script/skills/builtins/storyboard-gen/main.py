"""
分镜参考生成 Skill - 为每个场景生成分镜建议
"""

import json
import yaml
from typing import Dict, Any, List


def generate_storyboard(yaml_content: str, llm_client=None) -> Dict[str, Any]:
    """
    生成分镜参考
    
    Args:
        yaml_content: YAML 格式的剧本内容
        llm_client: LLM 客户端实例
        
    Returns:
        分镜参考生成结果
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return {"storyboard": []}
    
    scenes = script_data.get('scenes', [])
    
    storyboard = []
    for i, scene in enumerate(scenes):
        heading = scene.get('heading', f'场景{i+1}')
        beats = scene.get('beats', [])
        
        # 提取场景信息
        scene_info = {
            'scene_index': i + 1,
            'heading': heading,
            'beat_count': len(beats),
            'has_dialogue': any(b.get('type') == 'dialogue' for b in beats)
        }
        
        # 使用 LLM 生成分镜建议
        if llm_client:
            shot_suggestions = _generate_shots_with_llm(scene_info, beats, llm_client)
        else:
            shot_suggestions = _generate_basic_shots(scene_info, beats)
        
        storyboard.append({
            'scene': scene_info,
            'shots': shot_suggestions
        })
    
    return {
        "storyboard": storyboard,
        "total_scenes": len(scenes)
    }


def _generate_basic_shots(scene_info: dict, beats: List[dict]) -> List[dict]:
    """生成基础分镜建议（不使用 LLM）"""
    shots = []
    
    # 根据场景类型生成基础建议
    heading = scene_info.get('heading', '').lower()
    
    if '内景' in heading or 'int' in heading.lower():
        shots.append({
            'shot_type': '中景',
            'angle': '平视',
            'movement': '固定或缓慢推近',
            'description': '内景通常使用中景展示人物对话'
        })
    elif '外景' in heading or 'ext' in heading.lower():
        shots.append({
            'shot_type': '全景',
            'angle': '平视或俯视',
            'movement': '摇镜头或轨道',
            'description': '外景适合用全景展示环境'
        })
    else:
        shots.append({
            'shot_type': '中景',
            'angle': '平视',
            'movement': '固定',
            'description': '通用镜头'
        })
    
    # 如果有对话，添加特写建议
    if scene_info.get('has_dialogue'):
        shots.append({
            'shot_type': '特写',
            'angle': '平视',
            'movement': '固定',
            'description': '对话时切入角色特写，捕捉表情'
        })
    
    return shots


def _generate_shots_with_llm(scene_info: dict, beats: List[dict], llm_client) -> List[dict]:
    """使用 LLM 生成分镜建议"""
    # 构建场景描述
    scene_desc = f"场景: {scene_info.get('heading', '')}\n"
    scene_desc += f"节拍数: {len(beats)}\n\n"
    
    for beat in beats[:5]:  # 只取前5个 beat
        beat_type = beat.get('type', '')
        if beat_type == 'dialogue':
            scene_desc += f"对白 - {beat.get('character', '')}: {beat.get('content', '')[:50]}...\n"
        elif beat_type == 'action':
            scene_desc += f"动作: {beat.get('content', '')[:50]}...\n"
        elif beat_type == 'narration':
            scene_desc += f"旁白: {beat.get('content', '')[:50]}...\n"
    
    prompt = f"""你是专业的分镜师。请根据以下场景信息，生成分镜建议。

{scene_desc}

请生成 2-4 个镜头建议，每个镜头包含：
1. 景别（全景/中景/近景/特写/大特写）
2. 角度（平视/俯视/仰视/倾斜）
3. 运动（固定/推/拉/摇/移/跟）
4. 描述（为什么这样拍）

输出 JSON 格式：
```json
[
  {{
    "shot_type": "景别",
    "angle": "角度",
    "movement": "运动方式",
    "description": "描述"
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
        
        shots = json.loads(content)
        return shots if isinstance(shots, list) else _generate_basic_shots(scene_info, beats)
        
    except Exception as e:
        # LLM 失败，返回基础版本
        return _generate_basic_shots(scene_info, beats)


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数
    
    Args:
        data: 输入数据，包含 YAML 剧本内容
        config: 配置参数（包含 LLM 客户端）
        
    Returns:
        分镜参考生成结果
    """
    yaml_content = data.get("yaml_content", "")
    
    if not yaml_content:
        return {
            "success": False,
            "error": "缺少 YAML 剧本内容"
        }
    
    llm_client = config.get("llm_client")
    # 即使没有 LLM 也行，会生成基础版本
    
    try:
        result = generate_storyboard(yaml_content, llm_client)
        
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
  - heading: 咖啡店 - 内景 - 白天
    beats:
      - type: dialogue
        character: Jack
        content: 你竟然骗我！
        emotion: 愤怒
      - type: dialogue
        character: Amy
        content: 这只是善意的谎言。
        emotion: 冷静
      - type: action
        content: Jack 站起来，走到窗边。
  - heading: 公园 - 外景 - 傍晚
    beats:
      - type: dialogue
        character: Jack
        content: 这里真安静。
        emotion: 平静
"""
    
    # 模拟 LLM 客户端
    class MockLLMClient:
        def complete(self, prompt, temperature=0.7):
            return {"content": json.dumps([
                {
                    "shot_type": "中景",
                    "angle": "平视",
                    "movement": "固定",
                    "description": "展示两人对话场面"
                },
                {
                    "shot_type": "特写",
                    "angle": "平视",
                    "movement": "缓慢推近",
                    "description": "捕捉 Amy 说话时的表情"
                }
            ], ensure_ascii=False)}
    
    result = run(
        {"yaml_content": test_yaml},
        {"llm_client": MockLLMClient()}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
