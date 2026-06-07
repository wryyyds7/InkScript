---
name: casting-suggester
type: analyzer
description: 根据角色特征推荐演员（匹配度评分）
version: "1.0.0"
author: InkScript Team
priority: 17
enabled: true
---

# 选角建议 Skill

根据角色特征（年龄、性别、性格、台词风格），推荐合适的演员。

## 功能说明

1. 从 YAML 剧本中提取角色信息
2. 分析角色特征（年龄、性别、性格、台词量）
3. 使用 LLM 推荐演员（或根据用户提供的演员库匹配）
4. 生成选角建议报告（JSON 格式，含匹配度评分）

## 输出格式

JSON 格式的选角建议，包含：
- 角色列表及特征分析
- 推荐演员列表（含匹配度评分、理由）
- 选角总结

## 使用方法

在 Skills 管理页面点击"运行"按钮，或在编辑器中选择"选角建议"。
