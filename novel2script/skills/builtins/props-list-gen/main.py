"""
道具清单生成 Skill - 从剧本中提取道具，生成道具清单（CSV 格式）
"""

import json
import yaml
import csv
import io
from collections import defaultdict
from typing import Dict, Any, List


def generate_props_list(yaml_content: str, llm_client=None) -> Dict[str, Any]:
    """
    从 YAML 剧本中提取道具，生成道具清单

    Args:
        yaml_content: YAML 格式的剧本内容
        llm_client: LLM 客户端实例（可选，用于增强道具描述）

    Returns:
        道具清单生成结果
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")

    if not script_data:
        return {"props": [], "csv": ""}

    scenes = script_data.get('scenes', [])

    # 1. 从 action beats 中提取道具
    props_data = _extract_props(scenes)

    # 2. 生成 CSV
    csv_content = _generate_csv(props_data)

    # 3. 可选：使用 LLM 增强道具描述
    if llm_client:
        props_data = _enhance_with_llm(props_data, llm_client)

    return {
        "props": props_data,
        "csv": csv_content,
        "total_props": len(props_data)
    }


def _extract_props(scenes: List[dict]) -> List[dict]:
    """从场景中提取道具信息"""
    # 常见道具关键词
    prop_keywords = [
        '杯', '咖啡', '茶', '水', '酒', '手机', '电话', '钥匙', '包',
        '枪', '刀', '书', '信', '照片', '花', '礼物', '衣服', '帽子',
        '眼镜', '烟', '火', '灯', '门', '窗', '桌子', '椅子',
        '杯子', '瓶子', '盒子', '袋子', '文件', '笔', '纸', '地图',
        '剑', '盾', '魔法', '药', '食物', '水果', '花', '戒指'
    ]

    props_count = defaultdict(lambda: {
        'scenes': set(),
        'count': 0,
        'keywords': set()
    })

    for i, scene in enumerate(scenes):
        scene_heading = scene.get('heading', f'场景{i+1}')
        beats = scene.get('beats', [])

        for beat in beats:
            if beat.get('type') == 'action':
                content = beat.get('content', '')

                # 简单匹配道具关键词
                for keyword in prop_keywords:
                    if keyword in content:
                        prop_name = keyword
                        props_count[prop_name]['scenes'].add(scene_heading)
                        props_count[prop_name]['count'] += 1

                # 尝试提取带量词的道具（如"一杯咖啡"）
                import re
                prop_patterns = [
                    r'一\w*?([\u4e00-\u9fa5]{1,3})',  # 一杯咖啡 -> 咖啡
                    r'几\w*?([\u4e00-\u9fa5]{1,3})',  # 几朵花 -> 花
                ]
                for pattern in prop_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if len(match) >= 1:
                            props_count[match]['scenes'].add(scene_heading)
                            props_count[match]['count'] += 1

    # 转换为列表
    props_list = []
    for prop_name, data in props_count.items():
        props_list.append({
            'name': prop_name,
            'scene_count': len(data['scenes']),
            'total_count': data['count'],
            'scenes': list(data['scenes']),
            'suggested_quantity': max(data['count'], 1) * 2  # 建议准备数量 = 出现次数 * 2
        })

    # 按出现次数排序
    props_list.sort(key=lambda x: x['total_count'], reverse=True)

    return props_list


def _generate_csv(props_data: List[dict]) -> str:
    """生成 CSV 内容"""
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(['道具名称', '出现场景数', '出现次数', '建议准备数量', '出现场景', '备注'])

    # 写入数据
    for prop in props_data:
        writer.writerow([
            prop['name'],
            prop['scene_count'],
            prop['total_count'],
            prop['suggested_quantity'],
            '、'.join(prop['scenes'][:5]),  # 只显示前5个场景
            ''  # 备注留空
        ])

    return output.getvalue()


def _enhance_with_llm(props_data: List[dict], llm_client) -> List[dict]:
    """使用 LLM 增强道具描述"""
    if not props_data:
        return props_data

    # 构建 Prompt
    props_names = '、'.join([p['name'] for p in props_data[:10]])

    prompt = f"""你是专业的道具师。请为以下道具补充简短描述和使用建议。

**道具列表**: {props_names}

请为每个道具输出一行 JSON，格式：
{{"name": "道具名", "description": "道具描述（20字左右）", "usage": "使用建议"}}

请只输出 JSON 数组，不要有其他内容。
"""

    try:
        response = llm_client.complete(prompt, temperature=0.3)
        content = response.get("content", "")

        # 提取 JSON
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        enhancements = json.loads(content)

        # 合并增强信息
        enh_map = {e['name']: e for e in enhancements if 'name' in e}
        for prop in props_data:
            if prop['name'] in enh_map:
                prop['description'] = enh_map[prop['name']].get('description', '')
                prop['usage'] = enh_map[prop['name']].get('usage', '')

    except Exception as e:
        # LLM 失败，返回原始数据
        pass

    return props_data


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数

    Args:
        data: 输入数据，包含 YAML 剧本内容
        config: 配置参数（包含 LLM 客户端）

    Returns:
        道具清单生成结果
    """
    yaml_content = data.get("yaml_content", "")

    if not yaml_content:
        return {
            "success": False,
            "error": "缺少 YAML 剧本内容"
        }

    llm_client = config.get("llm_client")

    try:
        result = generate_props_list(yaml_content, llm_client)

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
      - type: action
        content: Jack 拿起咖啡杯，喝了一口。
      - type: dialogue
        character: Jack
        content: 这咖啡真难喝。
        emotion: 不满
      - type: action
        content: Amy 拿出手机，看了一眼时间。
  - heading: 公园 - 傍晚
    beats:
      - type: action
        content: Jack 坐在长椅上，从包里拿出一瓶水。
      - type: dialogue
        character: Amy
        content: 你还带着水？
        emotion: 惊讶
"""

    result = generate_props_list(test_yaml, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
