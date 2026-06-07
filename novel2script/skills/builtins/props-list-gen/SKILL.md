---
name: props-list-gen
type: exporter
description: 生成道具清单（从剧本中提取道具，导出为 CSV 格式）
version: "1.0.0"
author: InkScript Team
priority: 19
enabled: true
---

# 道具清单生成 Skill

从 YAML 剧本中提取所有道具，生成道具清单，可导出为 CSV 格式。

## 功能说明

1. 从 YAML 剧本的 action 类型 beat 中提取道具信息
2. 统计每个道具的出现场景和出现次数
3. 生成道具清单（CSV 格式，可用 Excel 打开）
4. 可选：使用 LLM 补充道具描述和建议数量

## 输出格式

CSV 格式的道具清单，包含：
- 道具名称
- 出现场景
- 出现次数
- 建议准备数量
- 备注

## 使用方法

在 Skills 管理页面点击"运行"按钮，或在编辑器中选择"生成道具清单"。
