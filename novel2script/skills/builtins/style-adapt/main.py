"""
风格适配 Skill - 调整剧本风格
"""

import json
import yaml
from typing import Dict, Any


def adapt_style(yaml_content: str, style: str = "现代", llm_client=None) -> Dict[str, Any]:
    """
    使用 LLM 调整剧本风格

    Args:
        yaml_content: YAML 格式的剧本内容
        style: 目标风格（古风/现代/科幻/悬疑/喜剧）
        llm_client: LLM 客户端实例

    Returns:
        风格调整后的结果
    """
    if not llm_client:
        raise ValueError("需要 LLM 客户端")

    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")

    if not script_data:
        return {"adapted_script": yaml_content}

    # 风格要求
    style_requirements = {
        "古风": """用词文雅，对白符合古代习惯，添加适当的称谓（公子、姑娘、大人等）
- 动作描述要有古典韵味
- 旁白语气要符合古风叙事风格""",
        "现代": """用词现代，对白自然，符合当代口语习惯
- 动作描述简洁明了
- 可以适当加入流行语（符合角色身份）""",
        "科幻": """加入科技感词汇，对白简洁有力，适当使用科技术语
- 动作描述可以包含未来科技元素
- 旁白要有科幻叙事感""",
        "悬疑": """营造紧张氛围，对白简洁，暗示多于直述
- 动作描述要增强悬疑感
- 旁白要有心理描写和气氛渲染""",
        "喜剧": """对白幽默，适当加入俏皮话和笑点
- 动作描述可以夸张一些
- 旁白可以加入搞笑评论"""
    }

    style_req = style_requirements.get(style, style_requirements["现代"])

    prompt = f"""你是专业的剧本风格调整师，擅长将剧本调整为特定风格。请将以下剧本调整为 **{style}** 风格。

**风格要求**：
{style_req}

**注意**：
1. 主要修改 dialogue 的 content（对白内容）
2. 修改 action 的描述（舞台指示）
3. 修改 narration 的语气（旁白）
4. 保持 YAML 格式正确
5. 保持角色名称不变
6. 保持场景结构不变

**输入剧本（YAML 格式）**：
```yaml
{yaml_content}
```

**输出格式**：请直接输出调整风格后的完整 YAML，不要添加任何解释。
"""

    # 调用 LLM
    try:
        response = llm_client.complete(prompt, temperature=0.7)
        adapted_yaml = response.get("content", yaml_content)

        # 验证输出是有效 YAML
        try:
            yaml.safe_load(adapted_yaml)
            return {
                "adapted_script": adapted_yaml,
                "style": style
            }
        except yaml.YAMLError:
            # 如果输出不是有效 YAML，返回原始内容
            return {
                "adapted_script": yaml_content,
                "style": style,
                "warning": "LLM 输出格式错误，返回原始内容"
            }

    except Exception as e:
        raise RuntimeError(f"LLM 调用失败: {e}")


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数

    Args:
        data: 输入数据，包含 YAML 剧本内容和风格参数
        config: 配置参数（包含 LLM 客户端）

    Returns:
        风格调整结果
    """
    yaml_content = data.get("yaml_content", "")
    style = data.get("style", "现代")

    if not yaml_content:
        return {
            "success": False,
            "error": "缺少 YAML 剧本内容"
        }

    llm_client = config.get("llm_client")
    if not llm_client:
        return {
            "success": False,
            "error": "缺少 LLM 客户端配置"
        }

    try:
        result = adapt_style(yaml_content, style, llm_client)

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
"""

    # 模拟 LLM 客户端
    class MockLLMClient:
        def complete(self, prompt, temperature=0.7):
            return {"content": test_yaml}

    result = run(
        {"yaml_content": test_yaml, "style": "古风"},
        {"llm_client": MockLLMClient()}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
