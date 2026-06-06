---
name: dialogue-polish
type: post_processor
description: LLM 润色台词，可选风格（写实/戏剧化/幽默）
version: "1.0.0"
author: InkScript Team
priority: 30
enabled: true
---

# 对白润色 Skill

使用 LLM 润色剧本对白，支持多种风格。

## 功能说明

- 写实风格：更自然、日常的对白
- 戏剧化风格：更富有张力和情感
- 幽默风格：加入喜剧元素

## 使用方法

选择风格后运行，输出润色后的 YAML 剧本。

## Prompt 模板

根据选择的风格，使用不同的 Prompt 模板调用 LLM。
