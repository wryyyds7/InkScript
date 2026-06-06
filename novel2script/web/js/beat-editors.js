/**
 * beat-editors.js — Beat 内联编辑
 *
 * 功能：点击剧本 YAML 中的 Beat → 弹出内联编辑器
 * 支持编辑：character、content、emotion
 * 支持：类型切换、新增 Beat、删除 Beat
 *
 * 依赖：editor.js（CodeMirror 实例）、scroll-sync.js（解析 Beat 位置）
 */

import { getContent, setContent } from "/js/editor.js";
import { parseBeatsFromYaml } from "/js/scroll-sync.js";

// ── Beat 编辑器管理器 ────────────────────────────────────────────────────

class BeatEditorManager {
    constructor() {
        this.activeEditor = null;   // 当前打开的编辑器 DOM
        this.activeBeatIdx = -1;   // 当前编辑的 Beat 索引
    }

    /**
     * 在指定位置弹出 Beat 编辑器
     * @param {EditorView} scriptView - 剧本编辑器实例
     * @param {number} yamlLine - 点击位置的行号（0-based）
     * @param {function} onSave - 保存回调（接收更新后的 YAML 文本）
     */
    openEditor(scriptView, yamlLine, onSave) {
        const yamlText = getContent(scriptView);
        const beats = parseBeatsFromYaml(yamlText);

        // 找到点击位置对应的 Beat
        let targetBeat = null;
        let beatIdx = -1;
        for (let i = 0; i < beats.length; i++) {
            if (yamlLine >= beats[i].lineStart && yamlLine <= beats[i].lineEnd) {
                targetBeat = beats[i];
                beatIdx = i;
                break;
            }
        }

        if (!targetBeat) return;  // 点击位置不在 Beat 内

        this.activeBeatIdx = beatIdx;
        this._showEditorPopup(scriptView, targetBeat, beatIdx, beats.length, yamlText, onSave);
    }

    /**
     * 显示编辑器弹出层（支持 beatIdx 和 totalBeats）
     */
    _showEditorPopup(scriptView, beat, beatIdx, totalBeats, yamlText, onSave) {
        // 关闭已有编辑器
        this.closeEditor();

        const popup = document.createElement("div");
        popup.className = "beat-editor-popup";
        popup.innerHTML = this._renderEditorHTML(beat, beatIdx, totalBeats);

        document.body.appendChild(popup);
        this.activeEditor = popup;

        // 绑定事件（传递 beatIdx 和 totalBeats）
        this._bindEditorEvents(popup, scriptView, beat, beatIdx, totalBeats, onSave);

        // 点击外部关闭
        setTimeout(() => {
            const closeHandler = (e) => {
                if (!popup.contains(e.target)) {
                    this.closeEditor();
                    document.removeEventListener("click", closeHandler);
                }
            };
            document.addEventListener("click", closeHandler);
        }, 100);
    }

    /**
     * 渲染编辑器 HTML（支持类型切换 + 新增/删除）
     */
    _renderEditorHTML(beat, beatIdx, totalBeats) {
        const typeLabelMap = {
            "dialogue": "对白",
            "action": "动作",
            "narration": "旁白",
            "heading": "标题",
            "transition": "转场",
        };

        // 类型选项
        const typeOptions = ["dialogue", "action", "narration", "heading", "transition"]
            .map(t => `<option value="${t}" ${t === beat.type ? "selected" : ""}>${typeLabelMap[t] || t}</option>`)
            .join("");

        let html = `
        <div class="beat-editor-header">
            <span class="beat-type-badge beat-type-${beat.type}">${typeLabelMap[beat.type] || beat.type}</span>
            <div class="flex gap-2">
                <button class="beat-editor-btn beat-editor-delete" title="删除此 Beat">🗑 删除</button>
                <button class="beat-editor-close" title="关闭">&times;</button>
            </div>
        </div>
        <div class="beat-editor-body">
            <!-- 类型切换 -->
            <div class="beat-field">
                <label>类型</label>
                <select class="beat-input-type">
                    ${typeOptions}
                </select>
            </div>
        `;

        // character（对话类型）
        if (beat.type === "dialogue") {
            html += `
            <div class="beat-field">
                <label>角色</label>
                <input type="text" class="beat-input-character" value="${this._esc(beat.character || "")}" placeholder="角色名称" />
            </div>
            <div class="beat-field">
                <label>情绪</label>
                <select class="beat-input-emotion">
                    <option value="">-- 无 --</option>
                    <option value="happy" ${beat.emotion === "happy" ? "selected" : ""}>😊 高兴</option>
                    <option value="sad" ${beat.emotion === "sad" ? "selected" : ""}>😢 悲伤</option>
                    <option value="angry" ${beat.emotion === "angry" ? "selected" : ""}>😠 愤怒</option>
                    <option value="calm" ${beat.emotion === "calm" ? "selected" : ""}>😌 平静</option>
                    <option value="excited" ${beat.emotion === "excited" ? "selected" : ""}>🤩 兴奋</option>
                    <option value="fear" ${beat.emotion === "fear" ? "selected" : ""}>😨 恐惧</option>
                </select>
            </div>
            `;
        }

        // content（所有类型都有）
        html += `
            <div class="beat-field">
                <label>内容</label>
                <textarea class="beat-input-content" rows="3" placeholder="输入内容...">${this._esc(beat.content || "")}</textarea>
            </div>
        `;

        // 新增 Beat 按钮区域
        html += `
            <div class="beat-editor-actions">
                <button class="beat-editor-btn beat-editor-add-above">⬆ 在上方新增</button>
                <button class="beat-editor-btn beat-editor-add-below">⬇ 在下方新增</button>
            </div>
        `;

        html += `
        </div>
        <div class="beat-editor-footer">
            <button class="beat-editor-cancel">取消</button>
            <button class="beat-editor-save">保存</button>
        </div>
        `;

        return html;
    }

    /**
     * 绑定编辑器事件（支持类型切换 + 新增/删除）
     */
    _bindEditorEvents(popup, scriptView, beat, beatIdx, totalBeats, onSave) {
        // 关闭按钮
        popup.querySelector(".beat-editor-close").addEventListener("click", () => {
            this.closeEditor();
        });

        // 取消按钮
        popup.querySelector(".beat-editor-cancel").addEventListener("click", () => {
            this.closeEditor();
        });

        // 删除按钮
        const deleteBtn = popup.querySelector(".beat-editor-delete");
        if (deleteBtn) {
            deleteBtn.addEventListener("click", () => {
                if (confirm("确认删除此 Beat？")) {
                    const yamlText = getContent(scriptView);
                    const updated = this._deleteBeat(yamlText, beat);
                    if (onSave && updated) {
                        onSave(updated);
                    }
                    this.closeEditor();
                }
            });
        }

        // 新增 Beat 按钮（上方）
        const addAboveBtn = popup.querySelector(".beat-editor-add-above");
        if (addAboveBtn) {
            addAboveBtn.addEventListener("click", () => {
                const yamlText = getContent(scriptView);
                const updated = this._addBeat(yamlText, beatIdx, "above");
                if (onSave && updated) {
                    onSave(updated);
                }
                this.closeEditor();
            });
        }

        // 新增 Beat 按钮（下方）
        const addBelowBtn = popup.querySelector(".beat-editor-add-below");
        if (addBelowBtn) {
            addBelowBtn.addEventListener("click", () => {
                const yamlText = getContent(scriptView);
                const updated = this._addBeat(yamlText, beatIdx, "below");
                if (onSave && updated) {
                    onSave(updated);
                }
                this.closeEditor();
            });
        }

        // 类型切换
        const typeSelect = popup.querySelector(".beat-input-type");
        if (typeSelect) {
            typeSelect.addEventListener("change", (e) => {
                const yamlText = getContent(scriptView);
                const newType = e.target.value;
                const updated = this._changeBeatType(yamlText, beat, newType);
                if (onSave && updated) {
                    onSave(updated);
                }
                this.closeEditor();
            });
        }

        // 保存按钮（普通字段更新）
        popup.querySelector(".beat-editor-save").addEventListener("click", () => {
            const yamlText = getContent(scriptView);
            const updated = this._collectUpdates(popup, beat, yamlText);
            if (onSave && updated) {
                onSave(updated);
            }
            this.closeEditor();
        });
    }

    /**
     * 删除指定 Beat
     */
    _deleteBeat(yamlText, beat) {
        const lines = yamlText.split("\n");
        const { lineStart, lineEnd } = beat;

        // 删除 Beat 对应的行（包括前后的空行）
        let start = lineStart;
        let end = lineEnd;

        // 向前删除空行
        while (start > 0 && lines[start - 1].trim() === "") {
            start--;
        }

        // 向后删除空行
        while (end < lines.length - 1 && lines[end + 1].trim() === "") {
            end++;
        }

        lines.splice(start, end - start + 1);
        return lines.join("\n");
    }

    /**
     * 在指定位置新增 Beat
     * @param {string} position - "above" 或 "below"
     */
    _addBeat(yamlText, beatIdx, position) {
        const lines = yamlText.split("\n");

        // 构造新 Beat 的 YAML 文本
        const newBeatLines = [
            "",
            "  - type: dialogue",
            "    character: 新角色",
            "    content: 新对白",
            "    emotion: ",
            "    source_location:",
            "      source_start: 0",
            "      source_end: 0",
        ];

        // 找到插入位置
        const currentBeat = this._getBeatByIndex(yamlText, beatIdx);
        if (!currentBeat) return yamlText;

        if (position === "above") {
            // 在当前 Beat 之前插入
            lines.splice(currentBeat.lineStart, 0, ...newBeatLines);
        } else {
            // 在当前 Beat 之后插入
            lines.splice(currentBeat.lineEnd + 1, 0, ...newBeatLines);
        }

        return lines.join("\n");
    }

    /**
     * 根据索引获取 Beat 信息（简化版，直接从 YAML 解析）
     */
    _getBeatByIndex(yamlText, idx) {
        const beats = parseBeatsFromYaml(yamlText);
        return beats[idx] || null;
    }

    /**
     * 切换 Beat 类型
     */
    _changeBeatType(yamlText, beat, newType) {
        const lines = yamlText.split("\n");
        const { lineStart, lineEnd } = beat;

        // 更新 type 字段
        for (let i = lineStart; i <= lineEnd && i < lines.length; i++) {
            if (lines[i].includes("type:")) {
                lines[i] = lines[i].replace(/type:\s*\w+/, `type: ${newType}`);
                break;
            }
        }

        return lines.join("\n");
    }

    /**
     * 收集编辑结果，更新 YAML 文本
     */
    _collectUpdates(popup, beat, yamlText) {
        const lines = yamlText.split("\n");
        const characterInput = popup.querySelector(".beat-input-character");
        const emotionInput = popup.querySelector(".beat-input-emotion");
        const contentInput = popup.querySelector(".beat-input-content");

        // 找到 Beat 对应的行范围，逐行更新
        const { lineStart, lineEnd } = beat;

        if (characterInput) {
            const newChar = characterInput.value.trim();
            this._updateFieldInLines(lines, lineStart, lineEnd, "character", newChar);
            this._updateFieldInLines(lines, lineStart, lineEnd, "character_id", newChar);
        }

        if (emotionInput) {
            const newEmotion = emotionInput.value;
            this._updateFieldInLines(lines, lineStart, lineEnd, "emotion", newEmotion);
        }

        if (contentInput) {
            const newContent = contentInput.value;
            this._updateContentField(lines, lineStart, lineEnd, newContent);
        }

        return lines.join("\n");
    }

    /**
     * 更新简单字段（character、emotion 等）
     */
    _updateFieldInLines(lines, start, end, fieldName, newValue) {
        for (let i = start; i <= end && i < lines.length; i++) {
            const line = lines[i];
            if (line.includes(`${fieldName}:`)) {
                if (newValue) {
                    lines[i] = line.replace(
                        new RegExp(`${fieldName}:\\s*.+`),
                        `${fieldName}: ${newValue}`
                    );
                } else {
                    lines[i] = line.replace(
                        new RegExp(`${fieldName}:\\s*.+`),
                        `${fieldName}:`
                    );
                }
                break;
            }
        }
    }

    /**
     * 更新 content 字段（支持多行）
     */
    _updateContentField(lines, start, end, newContent) {
        let contentKey = null;
        let contentLineIdx = -1;

        // 找到 content: 或 text: 字段所在行
        for (let i = start; i <= end && i < lines.length; i++) {
            if (lines[i].includes("content:") || lines[i].includes("text:")) {
                contentKey = lines[i].includes("content:") ? "content:" : "text:";
                contentLineIdx = i;
                break;
            }
        }

        if (contentLineIdx === -1) return;

        const indent = lines[contentLineIdx].match(/^(\s*)/)[1];
        const contentIndent = indent + "  ";  // 内容缩进多 2 空格

        if (!newContent.includes("\n")) {
            // 单行内容
            lines[contentLineIdx] = `${indent}${contentKey} ${newContent}`;
            // 删除旧的多行内容（如果有）
            let j = contentLineIdx + 1;
            while (j <= end && lines[j].startsWith(contentIndent)) {
                lines.splice(j, 1);
                end--;
            }
        } else {
            // 多行内容（使用 YAML 多行字符串 |）
            lines[contentLineIdx] = `${indent}${contentKey} |`;
            const contentLines = newContent.split("\n");
            let insertIdx = contentLineIdx + 1;
            for (const cl of contentLines) {
                lines.splice(insertIdx, 0, `${contentIndent}${cl}`);
                insertIdx++;
                end++;
            }
            // 删除旧的多行内容
            let j = insertIdx;
            while (j <= end && lines[j].startsWith(contentIndent)) {
                lines.splice(j, 1);
                end--;
            }
        }
    }

    /**
     * 关闭编辑器
     */
    closeEditor() {
        if (this.activeEditor) {
            this.activeEditor.remove();
            this.activeEditor = null;
            this.activeBeatIdx = -1;
        }
    }

    /**
     * HTML 转义
     */
    _esc(str) {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
}

// 单例导出
const beatEditorManager = new BeatEditorManager();

export default beatEditorManager;

/**
 * 在剧本编辑器中启用 Beat 点击编辑
 * @param {EditorView} scriptView
 * @param {EditorView} novelView
 * @param {function} onSave - 保存回调
 */
export function enableBeatEditing(scriptView, novelView, onSave) {
    // 监听 script editor 的点击事件
    scriptView.dom.addEventListener("click", (event) => {
        const pos = scriptView.posAtCoords({ x: event.clientX, y: event.clientY });
        if (pos === null) return;

        const line = scriptView.state.doc.lineAt(pos);
        beatEditorManager.openEditor(scriptView, line.number - 1, onSave);
    });
}

export { beatEditorManager };
