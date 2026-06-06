"""角色识别 Step

从小说文本中提取所有角色信息.
支持 Levenshtein 距离合并相似角色名(别名合并).
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher

from novel2script.core.steps.base import StepProtocol, register_step
from novel2script.llm_client import LLMClientProtocol
from novel2script.schema import Character, Script


def _levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的 Levenshtein 距离
    
    Args:
        s1: 字符串 1
        s2: 字符串 2
        
    Returns:
        编辑距离（越小越相似）
    """
    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1
    
    # 使用动态规划
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
        
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # 删除
                dp[i][j - 1] + 1,      # 插入
                dp[i - 1][j - 1] + cost  # 替换
            )
    
    return dp[len1][len2]


def _is_similar_name(name1: str, name2: str, threshold: float = 0.8) -> bool:
    """判断两个角色名是否相似（可能是同一个角色）
    
    Args:
        name1: 角色名 1
        name2: 角色名 2
        threshold: 相似度阈值（0-1，越大越严格）
        
    Returns:
        是否相似
    """
    # 1. 完全相同
    if name1 == name2:
        return True
    
    # 2. 一个包含另一个
    if name1 in name2 or name2 in name1:
        return True
    
    # 3. 计算编辑距离相似度
    max_len = max(len(name1), len(name2))
    if max_len == 0:
        return True
    
    distance = _levenshtein_distance(name1, name2)
    similarity = 1 - (distance / max_len)
    
    return similarity >= threshold


def _merge_similar_characters(characters: list[dict]) -> list[dict]:
    """合并相似角色（别名合并）
    
    Args:
        characters: 角色列表（每行包含 name、aliases 等）
        
    Returns:
        合并后的角色列表
    """
    if not characters:
        return []
    
    merged = []
    used = set()
    
    for i, char1 in enumerate(characters):
        if i in used:
            continue
            
        # 当前角色作为主角色
        main_char = char1.copy()
        main_char["aliases"] = main_char.get("aliases", []).copy()
        used.add(i)
        
        # 查找相似角色
        for j, char2 in enumerate(characters):
            if j in used or i == j:
                continue
                
            if _is_similar_name(char1["name"], char2["name"]):
                # 合并到主角色
                if char2["name"] not in main_char["aliases"]:
                    main_char["aliases"].append(char2["name"])
                # 合并 aliases
                for alias in char2.get("aliases", []):
                    if alias not in main_char["aliases"] and alias != main_char["name"]:
                        main_char["aliases"].append(alias)
                used.add(j)
        
        merged.append(main_char)
    
    return merged


_SYSTEM_PROMPT = """你是一个专业的剧本角色分析师.
从小说文本中识别所有有对白的角色,输出 JSON 数组.

每个角色包含:
- name: 角色名称(必需)
- aliases: 别名列表(可选)
- description: 简短描述(可选)

只输出 JSON,不要输出其他内容.
"""

_USER_PROMPT_TPL = """## 小说文本

{novel_text}

## 要求

1. 识别所有有对白的角色(至少说过一句话)
2. 合并同一角色的不同称呼(放入 aliases)
3. 输出 JSON 数组,格式:
```json
[
  {{"name": "李雷", "aliases": ["小李", "雷子"], "description": "男主角,高中生"}}
]
```
"""


@register_step("character_extractor")
class CharacterExtractorStep:
    """角色识别 Step"""

    @property
    def name(self) -> str:
        return "character_extractor"

    @property
    def description(self) -> str:
        return "识别小说中的角色"

    def run(
        self,
        script: Script,
        novel_text: str,
        llm: LLMClientProtocol,
        ctx: dict,
    ) -> Script:
        # 分段处理(防止超 Token)
        max_chars = 20_000
        segments = [
            novel_text[i : i + max_chars]
            for i in range(0, len(novel_text), max_chars)
        ]

        all_chars: list[dict] = []
        seen: set[str] = set()

        for seg in segments:
            prompt = _USER_PROMPT_TPL.format(novel_text=seg)
            raw = llm.chat_json(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "aliases": {"type": "array", "items": {"type": "string"}},
                            "description": {"type": "string"},
                        },
                        "required": ["name"],
                    },
                },
            )
            for c in raw:
                nm = c.get("name", "").strip()
                if nm and nm not in seen:
                    seen.add(nm)
                    all_chars.append(c)

        # 合并相似角色（别名合并）
        merged_chars = _merge_similar_characters(all_chars)

        # 写入 Script
        script.characters = [
            Character(
                name=c["name"],
                aliases=c.get("aliases", []),
                description=c.get("description", ""),
            )
            for c in merged_chars
        ]

        # 存入 ctx 供后续 Step 使用
        ctx["characters"] = [c.name for c in script.characters]
        return script
