---
name: storyboard-gen
type: analyzer
description: 生成分镜参考描述（景别、角度、运动建议）
version: "1.0.0"
author: InkScript Team
priority: 16
enabled: true
---

# 分镜参考生成 Skill

根据剧本场景内容，生成分镜参考描述，帮助导演和摄影师规划拍摄。

## 功能说明

1. 从 YAML 剧本中提取场景信息
2. 使用 LLM 分析每个场景的视觉元素
3. 生成分镜建议（景别、角度、运动、构图）

## 输出格式

JSON 格式的分镜参考，包含：
- 场景列表及分镜建议
- 每个场景的镜头建议（景别、角度、运动）
- 关键画面描述

## 使用方法

在 Skills 管理页面点击"运行"按钮，或在编辑器中选择"生成分镜参考"。
