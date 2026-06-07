---
name: character-profile
type: analyzer
description: 生成角色人物小传（性格分析、人物弧光、角色关系）
version: "1.0.0"
author: InkScript Team
priority: 18
enabled: true
---

# 人物小传生成 Skill

根据剧本内容，为每个主要角色生成详细的人物小传。

## 功能说明

1. 从 YAML 剧本中提取角色信息
2. 使用 LLM 分析角色性格、人物弧光
3. 分析角色与其他角色的关系
4. 生成 Markdown 格式的人物小传

## 输出格式

Markdown 格式的人物小传，包含：
- 角色基本信息（姓名、出场次数、台词量）
- 性格分析
- 人物弧光（角色成长轨迹）
- 与其他角色的关系
- 关键场景列表

## 使用方法

在 Skills 管理页面点击"运行"按钮，或在编辑器中选择"生成人物小传"。
