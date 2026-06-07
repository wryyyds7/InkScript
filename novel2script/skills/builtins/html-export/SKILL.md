---
name: html-export
type: exporter
description: 将 YAML 剧本导出为自包含的 HTML 文件（可分享、无需安装 InkScript）
version: "1.0.0"
author: InkScript Team
priority: 12
enabled: true
---

# HTML 导出 Skill

将 YAML 格式的剧本导出为自包含的 HTML 文件，可在浏览器中直接查看。

## 功能说明

1. 将 YAML 剧本转换为格式化的 HTML 页面
2. 包含基础交互功能（点击角色名高亮该角色所有台词）
3. 包含情绪曲线可视化（内嵌 Chart.js）
4. 生成自包含 HTML 文件，无需安装 InkScript

## 输出格式

单个 HTML 文件，包含：
- 完整剧本内容（格式化显示）
- 内嵌 CSS 样式
- 内嵌 JavaScript（Chart.js CDN）
- 基础交互功能

## 使用方法

在编辑器中点击"导出"按钮，选择"HTML 格式"即可。
