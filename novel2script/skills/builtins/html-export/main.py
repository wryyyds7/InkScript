"""
HTML 导出 Skill - 将 YAML 剧本导出为自包含 HTML 文件
"""

import json
import yaml
from typing import Dict, Any


def export_html(yaml_content: str) -> Dict[str, Any]:
    """
    将 YAML 剧本导出为 HTML
    
    Args:
        yaml_content: YAML 格式的剧本内容
        
    Returns:
        导出的 HTML 内容
    """
    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")
    
    if not script_data:
        return {'html': '<html><body><p>空剧本</p></body></html>'}
    
    title = script_data.get('title', '未命名剧本')
    scenes = script_data.get('scenes', [])
    
    # 生成 HTML
    html = _generate_html(title, scenes)
    
    return {
        'html': html,
        'filename': f"{title}.html"
    }


def _generate_html(title: str, scenes: list) -> str:
    """生成完整 HTML 页面"""
    # 生成剧本内容 HTML
    script_html = _generate_script_html(scenes)
    
    # 生成情绪曲线数据
    emotion_data = _generate_emotion_data(scenes)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 剧本</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }}
        
        h1 {{
            text-align: center;
            color: #ffffff;
            margin-bottom: 30px;
            font-size: 24px;
        }}
        
        .scene {{
            margin-bottom: 30px;
            page-break-inside: avoid;
        }}
        
        .scene-heading {{
            font-weight: bold;
            color: #4fc3f7;
            margin-bottom: 15px;
            font-size: 16px;
            text-transform: uppercase;
        }}
        
        .beat {{
            margin-bottom: 10px;
            padding-left: 20px;
        }}
        
        .beat-dialogue {{
            margin-bottom: 10px;
        }}
        
        .character-name {{
            font-weight: bold;
            color: #81c784;
            cursor: pointer;
            display: inline-block;
            min-width: 120px;
        }}
        
        .character-name:hover {{
            background: #333333;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        
        .character-name.highlighted {{
            background: #4fc3f7;
            color: #000000;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        
        .dialogue-content {{
            color: #e0e0e0;
            margin-left: 120px;
        }}
        
        .beat-action {{
            color: #ffb74d;
            font-style: italic;
            padding: 5px 0;
        }}
        
        .beat-narration {{
            color: #ce93d8;
            padding: 5px 0;
        }}
        
        .emotion-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-left: 10px;
            background: #424242;
            color: #b0b0b0;
        }}
        
        .chart-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            height: 200px;
            background: #2a2a2a;
            border: 1px solid #444444;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }}
        
        .chart-container h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #ffffff;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div id="script-content">
        {script_html}
    </div>
    
    <div class="chart-container">
        <h3>情绪曲线</h3>
        <canvas id="emotionChart"></canvas>
    </div>
    
    <script>
        // 情绪曲线数据
        const emotionData = {json.dumps(emotion_data, ensure_ascii=False)};
        
        // 角色高亮功能
        let highlightedCharacter = null;
        
        document.querySelectorAll('.character-name').forEach(el => {{
            el.addEventListener('click', function() {{
                const character = this.dataset.character;
                
                if (highlightedCharacter === character) {{
                    // 取消高亮
                    highlightedCharacter = null;
                    document.querySelectorAll('.character-name').forEach(e => e.classList.remove('highlighted'));
                }} else {{
                    // 高亮该角色
                    highlightedCharacter = character;
                    document.querySelectorAll('.character-name').forEach(e => {{
                        if (e.dataset.character === character) {{
                            e.classList.add('highlighted');
                        }} else {{
                            e.classList.remove('highlighted');
                        }}
                    }});
                }}
            }});
        }});
        
        // 情绪曲线图表
        const ctx = document.getElementById('emotionChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: emotionData.labels,
                datasets: [{{
                    label: '情绪强度',
                    data: emotionData.values,
                    borderColor: '#4fc3f7',
                    backgroundColor: 'rgba(79, 195, 247, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5,
                        ticks: {{
                            color: '#b0b0b0'
                        }},
                        grid: {{
                            color: '#333333'
                        }}
                    }},
                    x: {{
                        ticks: {{
                            color: '#b0b0b0',
                            maxRotation: 45
                        }},
                        grid: {{
                            color: '#333333'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#b0b0b0'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    return html


def _generate_script_html(scenes: list) -> str:
    """生成剧本内容 HTML"""
    html_parts = []
    
    for scene in scenes:
        heading = scene.get('heading', '')
        beats = scene.get('beats', [])
        
        scene_part = f'<div class="scene">\n'
        scene_part += f'    <div class="scene-heading">{heading}</div>\n'
        
        for beat in beats:
            beat_type = beat.get('type', '')
            
            if beat_type == 'dialogue':
                character = beat.get('character', '')
                content = beat.get('content', '')
                emotion = beat.get('emotion', '')
                
                scene_part += f'    <div class="beat beat-dialogue">\n'
                scene_part += f'        <span class="character-name" data-character="{character}">{character}</span>\n'
                scene_part += f'        <span class="dialogue-content">{content}</span>\n'
                if emotion:
                    scene_part += f'        <span class="emotion-badge">{emotion}</span>\n'
                scene_part += f'    </div>\n'
            
            elif beat_type == 'action':
                content = beat.get('content', '')
                scene_part += f'    <div class="beat beat-action">{content}</div>\n'
            
            elif beat_type == 'narration':
                content = beat.get('content', '')
                scene_part += f'    <div class="beat beat-narration">{content}</div>\n'
        
        scene_part += '</div>\n'
        html_parts.append(scene_part)
    
    return '\n'.join(html_parts)


def _generate_emotion_data(scenes: list) -> dict:
    """生成情绪曲线数据"""
    emotion_values = {
        '平静': 1, '中性': 2, '开心': 3, '兴奋': 4, '愤怒': 4,
        '悲伤': 2, '恐惧': 3, '冷静': 2, '绝望': 1, '紧张': 3
    }
    
    labels = []
    values = []
    
    for i, scene in enumerate(scenes):
        beats = scene.get('beats', [])
        dialogues = [b for b in beats if b.get('type') == 'dialogue']
        
        if dialogues:
            avg_emotion = sum(emotion_values.get(b.get('emotion', '中性'), 2) for b in dialogues) / len(dialogues)
        else:
            avg_emotion = 2
        
        labels.append(f"场景{i+1}")
        values.append(round(avg_emotion, 1))
    
    return {
        'labels': labels,
        'values': values
    }


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数
    
    Args:
        data: 输入数据，包含 YAML 剧本内容
        config: 配置参数
        
    Returns:
        导出的 HTML 内容
    """
    yaml_content = data.get('yaml_content', '')
    
    if not yaml_content:
        return {
            'success': False,
            'error': '缺少 YAML 剧本内容'
        }
    
    try:
        result = export_html(yaml_content)
        
        return {
            'success': True,
            'data': result
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
    
    result = export_html(test_yaml)
    print(result['html'])
