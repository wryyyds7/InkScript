---
name: fountain-export
type: exporter
description: 将 YAML 剧本导出为 Fountain 格式（好莱坞标准剧本格式）
version: "1.0.0"
author: InkScript Team
priority: 10
enabled: true
---

# Fountain 导出 Skill

将 YAML 格式的剧本转换为 Fountain 格式，这是好莱坞通用的剧本格式。

## 功能说明

- 支持对话、动作、角色表情/语气标注
- 自动转换场景标题、转场
- 保留情绪标注作为备注

## 使用方法

在编辑器中点击"导出"按钮，选择"Fountain 格式"即可。

## 输出格式示例

```fountain
INT. 咖啡店 - 白天

JACK
（愤怒）
你竟然骗我！

AMY
（冷静）
这只是善意的谎言。
```

## Prompt 模板

（此 Skill 为纯文本转换，无需 LLM 调用）
