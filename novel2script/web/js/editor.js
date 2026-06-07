/**
 * InkScript Editor - CodeMirror 6 封装
 * 提供 initNovelEditor / initScriptEditor 两个工厂函数
 */

import { EditorState, StateEffect } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { indentOnInput, syntaxHighlighting, defaultHighlightStyle, bracketMatching, foldGutter, indentUnit } from "@codemirror/language";
import { oneDark } from "@codemirror/theme-one-dark";
import { yaml } from "@codemirror/lang-yaml";
import { autocompletion } from "@codemirror/autocomplete";
import { scrollToSource, findSourceLocationAtLine, parseBeatsFromYaml, scrollSyncTheme } from "/js/scroll-sync.js";
import { yamlSchemaLinter } from "/js/yaml-linter.js";

// ── 小说编辑器：无语法高亮，支持行号、折叠、历史记录 ─────────

/**
 * 初始化小说原文编辑器
 * @param {HTMLElement} container - 挂载容器（div#novel-editor-container）
 * @param {string} content - 初始文本
 * @param {object} opts - 可选配置
 * @returns {EditorView}
 */
export function initNovelEditor(container, content = "", opts = {}) {
    const readOnly = opts.readOnly ?? false;

    const state = EditorState.create({
        doc: content,
        extensions: [
            lineNumbers(),
            highlightActiveLineGutter(),
            highlightActiveLine(),
            drawSelection(),
            indentOnInput(),
            bracketMatching(),
            foldGutter(),
            history(),
            indentUnit.of("    "),              // 小说缩进 4 空格

            keymap.of([...defaultKeymap, ...historyKeymap]),

            EditorView.editable.of(!readOnly),
            EditorView.lineWrapping,

            // 基础样式
            EditorView.theme({
                "&": { height: "100%", fontSize: "13px" },
                ".cm-scroller": { overflow: "auto" },
                ".cm-content": { fontFamily: "'Fira Code', 'Courier New', monospace" },
                ".cm-gutters": { backgroundColor: "#f9fafb", borderRight: "1px solid #e5e7eb" },
            }),

            // 发出内容变更事件（供 Alpine 监听）
            EditorView.updateListener.of((update) => {
                if (update.docChanged) {
                    const content = update.state.doc.toString();
                    window.dispatchEvent(new CustomEvent("novel-change", { detail: { content } }));
                }
            }),
        ],
    });

    const view = new EditorView({ state, parent: container });
    container._cmView = view;  // 方便调试
    return view;
}

// ── 剧本 YAML 编辑器：YAML 语法高亮 + lint + 行号 ─────────

/**
 * 初始化剧本 YAML 编辑器
 * @param {HTMLElement} container - 挂载容器（div#script-editor-container）
 * @param {string} content - 初始 YAML 文本
 * @param {object} opts - 可选配置
 * @returns {EditorView}
 */
export function initScriptEditor(container, content = "", opts = {}) {
    const readOnly = opts.readOnly ?? false;

    const state = EditorState.create({
        doc: content,
        extensions: [
            lineNumbers(),
            highlightActiveLineGutter(),
            highlightActiveLine(),
            drawSelection(),
            indentOnInput(),
            bracketMatching(),
            foldGutter(),
            history(),
            yaml(),                              // YAML 语法高亮
            syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
            autocompletion(),
            yamlSchemaLinter,                  // YAML Schema 实时校验
            indentUnit.of("  "),               // YAML 缩进 2 空格

            keymap.of([...defaultKeymap, ...historyKeymap]),

            EditorView.editable.of(!readOnly),
            EditorView.lineWrapping,

            // 基础样式
            EditorView.theme({
                "&": { height: "100%", fontSize: "13px" },
                ".cm-scroller": { overflow: "auto" },
                ".cm-content": { fontFamily: "'Fira Code', 'Courier New', monospace" },
                ".cm-gutters": { backgroundColor: "#f9fafb", borderRight: "1px solid #e5e7eb" },
                ".cm-activeLine": { backgroundColor: "#eff6ff" },
                ".cm-activeLineGutter": { backgroundColor: "#dbeafe" },
            }),

            // 发出内容变更事件
            EditorView.updateListener.of((update) => {
                if (update.docChanged) {
                    const content = update.state.doc.toString();
                    window.dispatchEvent(new CustomEvent("script-change", { detail: { content } }));
                }
            }),

            // ── 点击 Beat 滚动联动 ─────────
            EditorView.domEventHandlers({
                click: (event, view) => {
                    const pos = view.posAtCoords({ x: event.clientX, y: event.clientY });
                    if (pos !== null) {
                        const line = view.state.doc.lineAt(pos);
                        // 通过 CustomEvent 通知 app.js 处理滚动联动
                        window.dispatchEvent(new CustomEvent("script-click", {
                            detail: { line: line.number, pos },
                        }));
                    }
                    return false;
                },
            }),
        ],
    });

    const view = new EditorView({ state, parent: container });
    container._cmView = view;
    return view;
}

// ── 工具函数 ─────────

/** 获取 EditorView 的当前文档内容 */
export function getContent(view) {
    return view?.state.doc.toString() ?? "";
}

/** 设置 EditorView 的内容（不触发变更事件） */
export function setContent(view, content) {
    if (!view) return;
    view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: content ?? "" },
    });
}

/** 滚动到指定行 */
export function scrollToLine(view, line) {
    if (!view) return;
    const pos = view.state.doc.line(line).from;
    view.dispatch({ effects: EditorView.scrollIntoView(pos, { y: "center" }) });
}

// ── 小说预处理功能 ─────────

/** 在指定位置添加删除线标记（章节删除） */
export function markTextDeleted(view, from, to) {
    if (!view) return;
    view.dispatch({
        changes: [
            { from, insert: '<del>' },
            { from: to, insert: '</del>' }
        ]
    });
}

/** 合并选中的多个段落（用换行符连接） */
export function mergeParagraphs(view) {
    if (!view) return;
    const { state } = view;
    const selection = state.selection.main;
    if (selection.empty) return;

    const selectedText = state.doc.sliceString(selection.from, selection.to);
    // 用单个换行符替换多个换行符（合并段落）
    const mergedText = selectedText.replace(/\n\s*\n+/g, '\n');
    
    view.dispatch({
        changes: { from: selection.from, to: selection.to, insert: mergedText }
    });
}

/** 在选中位置插入标记 */
export function insertMark(view, markType, noteText = '') {
    if (!view) return;
    const { state } = view;
    const selection = state.selection.main;
    
    let mark = '';
    switch (markType) {
        case 'keep':
            mark = '<!-- keep -->';
            break;
        case 'skip':
            mark = '<!-- skip -->';
            break;
        case 'note':
            mark = `<!-- note: ${noteText} -->`;
            break;
        default:
            return;
    }
    
    view.dispatch({
        changes: { from: selection.from, insert: mark + ' ' }
    });
}

/** 初始化小说编辑器的右键菜单（预处理功能） */
export function initNovelContextMenu(view, handlers = {}) {
    if (!view) return;
    
    const contextMenu = document.createElement('div');
    contextMenu.className = 'novel-context-menu';
    contextMenu.style.cssText = 'position:fixed;background:white;border:1px solid #ccc;box-shadow:2px 2px 5px rgba(0,0,0,0.1);z-index:1000;display:none;';
    contextMenu.innerHTML = `
        <div class="menu-item" data-action="delete" style="padding:8px 12px;cursor:pointer;font-size:13px;">🗑️ 删除选中内容</div>
        <div class="menu-item" data-action="merge" style="padding:8px 12px;cursor:pointer;font-size:13px;">📎 合并段落</div>
        <div class="menu-item" data-action="mark-keep" style="padding:8px 12px;cursor:pointer;font-size:13px;">🏷️ 添加标记: keep</div>
        <div class="menu-item" data-action="mark-skip" style="padding:8px 12px;cursor:pointer;font-size:13px;">⏭️ 添加标记: skip</div>
        <div class="menu-item" data-action="mark-note" style="padding:8px 12px;cursor:pointer;font-size:13px;">📝 添加标记: note</div>
    `;
    
    document.body.appendChild(contextMenu);
    
    // 右键菜单点击事件
    contextMenu.addEventListener('click', (e) => {
        const item = e.target.closest('.menu-item');
        if (!item) return;
        
        const action = item.dataset.action;
        const { state } = view;
        const selection = state.selection.main;
        
        switch (action) {
            case 'delete':
                if (!selection.empty && handlers.onDelete) {
                    handlers.onDelete(view, selection.from, selection.to);
                }
                break;
            case 'merge':
                if (handlers.onMerge) {
                    handlers.onMerge(view);
                } else {
                    mergeParagraphs(view);
                }
                break;
            case 'mark-keep':
                if (handlers.onAddMark) {
                    handlers.onAddMark(view, 'keep');
                } else {
                    insertMark(view, 'keep');
                }
                break;
            case 'mark-skip':
                if (handlers.onAddMark) {
                    handlers.onAddMark(view, 'skip');
                } else {
                    insertMark(view, 'skip');
                }
                break;
            case 'mark-note':
                const noteText = prompt('请输入注释内容：');
                if (noteText && handlers.onAddMark) {
                    handlers.onAddMark(view, 'note', noteText);
                } else if (noteText) {
                    insertMark(view, 'note', noteText);
                }
                break;
        }
        
        contextMenu.style.display = 'none';
    });
    
    // 显示右键菜单
    view.dom.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        
        // 检查是否有选中内容
        const { state } = view;
        const selection = state.selection.main;
        if (selection.empty) return; // 没有选中内容时不显示菜单
        
        contextMenu.style.left = `${e.clientX}px`;
        contextMenu.style.top = `${e.clientY}px`;
        contextMenu.style.display = 'block';
    });
    
    // 点击其他地方隐藏菜单
    document.addEventListener('click', () => {
        contextMenu.style.display = 'none';
    });
    
    return contextMenu;
}