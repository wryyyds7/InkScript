"""
章节概要 Skill - 生成章节概要
"""

import json
import yaml
from typing import Dict, Any, List


def generate_chapter_summary(content: str, llm_client=None) -> Dict[str, Any]:
    """
    使用 LLM 生成章节概要

    Args:
        content: 剧本或小说内容（YAML 或纯文本）
        llm_client: LLM 客户端实例

    Returns:
        章节概要结果
    """
    if not llm_client:
        raise ValueError("需要 LLM 客户端")

    # 尝试解析 YAML
    try:
        script_data = yaml.safe_load(content)
        is_yaml = True
    except yaml.YAMLError:
        is_yaml = False
        script_data = None

    # 构建 Prompt
    if is_yaml and script_data:
        # YAML 格式：按场景分组
        prompt = f"""你是专业的文学编辑，擅长总结章节内容。请为以下剧本生成章节概要。

**要求**：
1. 识别所有场景（每个 scene 作为一个章节）
2. 为每个章节生成 100-200 字的概要
3. 提取章节关键事件
4. 分析章节情感走向

**输出格式**（JSON）：
```json
{{
  "chapters": [
    {{
      "chapter_id": "场景 ID 或序号",
      "title": "场景标题（heading）",
      "summary": "章节内容概要（100-200 字）",
      "key_events": ["关键事件 1", "关键事件 2"],
      "emotion_trend": "情感走向描述"
    }}
  ],
  "overall_summary": "整部作品的总体概要"
}}
```

**输入剧本（YAML 格式）**：
```yaml
{content}
```

**重要**：请只输出 JSON，不要添加任何解释或 markdown 标记。
"""
    else:
        # 纯文本格式：尝试按章节分割
        prompt = f"""你是专业的文学编辑，擅长总结章节内容。请为以下内容生成章节概要。

**要求**：
1. 识别所有章节（如果没有明确分章，按场景或段落自动分章，每 500-1000 字为一个章节）
2. 为每个章节生成 100-200 字的概要
3. 提取章节关键事件
4. 分析章节情感走向

**输出格式**（JSON）：
```json
{{
  "chapters": [
    {{
      "chapter_id": "章节序号",
      "title": "章节标题（如果有）",
      "summary": "章节内容概要（100-200 字）",
      "key_events": ["关键事件 1", "关键事件 2"],
      "emotion_trend": "情感走向描述"
    }}
  ],
  "overall_summary": "整部作品的总体概要"
}}
```

**输入内容**：
```
{content[:4000]}  # 限制长度
```

**重要**：请只输出 JSON，不要添加任何解释或 markdown 标记。
"""

    # 调用 LLM
    try:
        response = llm_client.complete(prompt, temperature=0.3)
        response_text = response.get("content", "")

        # 提取 JSON（可能包含在 markdown 代码块中）
        json_match = response_text.strip()
        if json_match.startswith("```json"):
            json_match = json_match[7:]
        if json_match.endswith("```"):
            json_match = json_match[:-3]
        json_match = json_match.strip()

        try:
            result = json.loads(json_match)
            return result
        except json.JSONDecodeError:
            # 如果解析失败，返回原始文本
            return {
                "chapters": [],
                "overall_summary": response_text,
                "warning": "JSON 解析失败，返回原始文本"
            }

    except Exception as e:
        raise RuntimeError(f"LLM 调用失败: {e}")


def run(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 主入口函数

    Args:
        data: 输入数据，包含剧本/小说内容
        config: 配置参数（包含 LLM 客户端）

    Returns:
        章节概要结果
    """
    content = data.get("content", "")
    if not content:
        content = data.get("yaml_content", "")

    if not content:
        return {
            "success": False,
            "error": "缺少内容"
        }

    llm_client = config.get("llm_client")
    if not llm_client:
        return {
            "success": False,
            "error": "缺少 LLM 客户端配置"
        }

    try:
        result = generate_chapter_summary(content, llm_client)

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
            return {"content": '{"chapters": [], "overall_summary": "测试概要"}'}

    result = run(
        {"yaml_content": test_yaml},
        {"llm_client": MockLLMClient()}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
