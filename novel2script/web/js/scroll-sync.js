/**
 * scroll-sync.js — 滚动联动
 *
 * 功能：点击右侧剧本 YAML 中的 Beat → 左侧小说编辑器自动滚动到对应原文位置
 *
 * 原理：
 *   1. 解析 YAML 中每个 Beat 的 source_location 字段
 *   2. 根据 chapter_index + start_paragraph 计算小说原文中的字符偏移量
 *   3. 使用 CM6 的 scrollIntoView Effect 滚动到对应位置
 *   4. 用 Decoration 高亮对应行（短暂显示 2 秒后消失）
 */

import { EditorView, Decoration, ViewPlugin, WidgetType, ViewUpdate } from "@codemirror/view";
import { EditorSelection, StateEffect, StateField } from "@codemirror/state";
import { RangeSet } from "@codemirror/state";

// ── 高亮装饰器（黄色背景，2 秒后消失）────────

/**
 * 添加高亮装饰到指定位置
 * @param {EditorView} view
 * @param {number} from - 起始字符位置
 * @param {number} to   - 结束字符位置
 */
export function highlightRange(view, from, to) {
    const deco = Decoration.mark({ class: "cm-highlight-source" });
    const widgets = RangeSet.of([deco.range(from, to)]);

    // 通过 ViewPlugin 动态管理装饰
    const plugin = view.plugin(highlightPlugin);
    if (plugin) {
        plugin.updateHighlight(widgets);
    }
}

/**
 * 清除所有高亮
 * @param {EditorView} view
 */
export function clearHighlight(view) {
    const plugin = view.plugin(highlightPlugin);
    if (plugin) {
        plugin.clearHighlight();
    }
}

// ── ViewPlugin：管理高亮装饰────────

class HighlightPlugin {
    constructor(view) {
        this.decorations = RangeSet.empty;
        this.timer = null;
    }

    update(update) {
        // 内容变化时清除高亮
        if (update.docChanged) {
            this.clearHighlight();
        }
    }

    updateHighlight(decorations) {
        this.decorations = decorations;
        this.timer = setTimeout(() => {
            this.clearHighlight();
        }, 2000);  // 2 秒后自动消失
    }

    clearHighlight() {
        this.decorations = RangeSet.empty;
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    }

    destroy() {
        if (this.timer) clearTimeout(this.timer);
    }
}

const highlightPlugin = ViewPlugin.fromClass(HighlightPlugin, {
    decorations: (v) => v.decorations,
});

// ── 核心：滚动联动────────

/**
 * 根据 source_location 计算小说原文中的字符偏移量
 *
 * @param {string} novelText - 完整小说原文
 * @param {object} sourceLoc - source_location 对象
 *   { chapter_index, start_paragraph, end_paragraph, start_offset, end_offset }
 * @returns {{ from: number, to: number } | null}
 */
export function calcOffset(novelText, sourceLoc) {
    if (!sourceLoc || !novelText) return null;

    // 按双换行分段
    const paragraphs = novelText.split(/\n{2,}/);

    const startPara = Math.max(0, sourceLoc.start_paragraph ?? 0);
    const endPara = Math.min(paragraphs.length - 1, sourceLoc.end_paragraph ?? startPara);

    // 计算起始偏移
    let from = 0;
    for (let i = 0; i < startPara && i < paragraphs.length; i++) {
        from += paragraphs[i].length + 2;  // +2 是双换行的 \n\n
    }

    // 加上段落内偏移
    from += sourceLoc.start_offset ?? 0;

    // 计算结束偏移
    let to = from;
    for (let i = startPara; i <= endPara && i < paragraphs.length; i++) {
        to += paragraphs[i].length + 2;
    }
    to -= 2;  // 去掉最后一个多余的 \n\n
    to += sourceLoc.end_offset ?? 0;

    // 边界保护
    from = Math.min(from, novelText.length);
    to = Math.min(to, novelText.length);
    if (to <= from) to = Math.min(from + 10, novelText.length);

    return { from, to };
}

/**
 * 滚动小说编辑器到指定 Beat 的原文位置
 *
 * @param {EditorView} novelView   - 小说编辑器实例
 * @param {string}      novelText  - 小说原文
 * @param {object}      sourceLoc   - source_location 对象
 */
export function scrollToSource(novelView, novelText, sourceLoc) {
    const range = calcOffset(novelText, sourceLoc);
    if (!range || !novelView) return;

    const { from, to } = range;

    // 1. 滚动到对应位置（居中显示）
    novelView.dispatch({
        selection: EditorSelection.create([EditorSelection.range(from, to)]),
        effects: [EditorView.scrollIntoView(from, { y: "center" })],
    });

    // 2. 高亮对应文本
    highlightRange(novelView, from, to);
}

// ── YAML 解析：提取 Beat 列表（含 source_location）────────

/**
 * 从 YAML 字符串中提取所有 Beat 及其 source_location
 * 返回 Array<{ lineStart, lineEnd, type, character, content, source_location }>
 *
 * 这是一个简化解析器（不依赖 js-yaml），用于快速定位。
 * 如果需要完整解析，建议使用 yaml 库。
 */
export function parseBeatsFromYaml(yamlText) {
    if (!yamlText) return [];

    const lines = yamlText.split("\n");
    const beats = [];
    let currentBeat = null;
    let indentLevel = -1;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // 检测 Beat 开始（- type: dialogue 等）
        if (trimmed.startsWith("- type:")) {
            // 保存上一个 Beat
            if (currentBeat) {
                currentBeat.lineEnd = i - 1;
                beats.push(currentBeat);
            }
            // 开始新的 Beat
            const type = trimmed.split(":")[1]?.trim().replace(/['"]/g, "");
            currentBeat = {
                lineStart: i,
                lineEnd: i,
                type: type || "",
                character: "",
                content: "",
                source_location: null,
            };
            indentLevel = line.indexOf("-");
            continue;
        }

        // 在 Beat 内解析字段
        if (currentBeat) {
            if (trimmed.startsWith("character:") || trimmed.startsWith("character_id:")) {
                currentBeat.character = trimmed.split(":")[1]?.trim().replace(/['"]/g, "") || "";
            } else if (trimmed.startsWith("text:") || trimmed.startsWith("content:")) {
                let content = trimmed.split(":").slice(1).join(":").trim();
                // 处理多行内容（以 | 或 > 开头的块）
                if (content === "|" || content === "|-" || content === "|+") {
                    // 收集后续缩进行
                    const baseIndent = line.indexOf("content:") + 8;
                    let j = i + 1;
                    let multiContent = "";
                    while (j < lines.length) {
                        const nextLine = lines[j];
                        const nextTrimmed = nextLine.trim();
                        if (nextTrimmed.startsWith("- type:") || nextTrimmed.startsWith("beats:")) break;
                        if (nextLine.startsWith("      ") || nextLine.startsWith("\t")) {
                            multiContent += nextLine.trim() + "\n";
                            j++;
                        } else {
                            break;
                        }
                    }
                    currentBeat.content = multiContent.trim();
                    i = j - 1;
                } else {
                    currentBeat.content = content.replace(/^['"]|['"]$/g, "");
                }
            } else if (trimmed.startsWith("source_location:")) {
                // 开始解析嵌套的 source_location
                currentBeat.source_location = {};
                // 简单方式：收集下几行的缩进字段
                for (let j = i + 1; j < Math.min(i + 6, lines.length); j++) {
                    const subLine = lines[j];
                    const subTrimmed = subLine.trim();
                    if (subTrimmed.startsWith("- type:") || subTrimmed.startsWith("beats:") || subTrimmed.startsWith("type:")) break;
                    if (subTrimmed.includes(":")) {
                        const [key, ...vals] = subTrimmed.split(":");
                        const val = vals.join(":").trim();
                        if (["chapter_index", "start_paragraph", "end_paragraph", "start_offset", "end_offset"].includes(key.trim())) {
                            currentBeat.source_location[key.trim()] = parseInt(val, 10) || 0;
                        }
                    }
                }
            }
        }
    }

    // 保存最后一个 Beat
    if (currentBeat) {
        currentBeat.lineEnd = lines.length - 1;
        beats.push(currentBeat);
    }

    return beats;
}

/**
 * 根据 YAML 行号找到对应的 Beat 的 source_location
 * @param {string} yamlText - YAML 文本
 * @param {number} yamlLine - 点击位置所在行号（0-based）
 * @returns {object | null} source_location 对象
 */
export function findSourceLocationAtLine(yamlText, yamlLine) {
    const beats = parseBeatsFromYaml(yamlText);
    for (const beat of beats) {
        if (yamlLine >= beat.lineStart && yamlLine <= beat.lineEnd) {
            return beat.source_location;
        }
    }
    return null;
}

// ── 样式────────

export const scrollSyncTheme = EditorView.theme({
    ".cm-highlight-source": {
        backgroundColor: "#fef9c3",
        borderRadius: "2px",
        padding: "1px 0",
    },
});
