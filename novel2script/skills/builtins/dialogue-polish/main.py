"""
对白润色 Skill - 使用 LLM 润色剧本对白
"""

import json
import yaml
from typing import Dict, Any, List


def polish_dialogues(yaml_content: str, style: str = "写实", llm_client=None) -> Dict[str, Any]:
    """
    使用 LLM 润色剧本对白

    Args:
        yaml_content: YAML 格式的剧本内容
        style: 润色风格（写实/戏剧化/幽默）
        llm_client: LLM 客户端实例

    Returns:
        润色后的结果
    """
    if not llm_client:
        raise ValueError("需要 LLM 客户端")

    try:
        script_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失败: {e}")

    if not script_data:
        return {"polished_script": yaml_content}

    # 构建 Prompt
    style_prompts = {
        "写实": "更自然、日常的对白，符合真实人物性格和说话习惯",
        "戏剧化": "更富有张力和情感，增强冲突和戏剧效果",
        "幽默": "加入喜剧元素，让对白轻松有趣"
    }

    style_desc = style_prompts.get(style, style_prompts["写实"])

    prompt = f"""你是专业的剧本对白润色师。请润色以下剧本的对白部分，风格要求：{style_desc}

**注意**：
1. 只修改 dialogue 类型 beat 的 content 字段
2. 保持角色名称不变
3. 保持 YAML 格式正确
4. 保持场景结构不变
5. 对白要符合角色性格

**输入剧本（YAML 格式）**：
```yaml
{yaml_content}
```

**输出格式**：请直接输出润色后的完整 YAML，不要添加任何解释。
"""

    # 调用 LLM
    try:
        response = llm_client.complete(prompt, temperature=0.8)
        polished_yaml = response.get("content", yaml_content)

        # 验证输出是有效 YAML
        try:
            yaml.safe_load(polished_yaml)
            return {
                "polished_script": polished_yaml,
                "style": style
            }
        except yaml.YAMLError:
            # 如果输出不是有效 YAML，返回原始内容
            return {
                "polished_script": yaml_content,
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
        润色结果
    """
    yaml_content = data.get("yaml_content", "")
    style = data.get("style", "写实")

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
        result = polish_dialogues(yaml_content, style, llm_client)

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
        {"yaml_content": test_yaml, "style": "写实"},
        {"llm_client": MockLLMClient()}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
