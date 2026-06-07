/**
 * yaml-linter.js — YAML Schema 校验（CodeMirror 6 linter Extension）
 *
 * 功能：编辑 YAML 时实时校验，错误标红、警告标黄
 * 基于 CodeMirror 6 的 linter() API
 */

import { linter } from "@codemirror/lint";
import { yaml as yamlParse } from "yaml";

// ── Script YAML Schema 定义 ────────────────────────────────────────────

/**
 * 校验 Script YAML 的完整结构
 * 返回 Diagnostic[] 数组
 */
export function lintScriptYaml(text) {
    const diagnostics = [];

    if (!text || !text.trim()) {
        return diagnostics;  // 空文件不报错
    }

    // 1. 解析 YAML（捕获解析错误）
    let doc;
    try {
        doc = yamlParse.parse(text, { keepSourceTokens: true });
    } catch (e) {
        // YAML 语法错误
        const msg = e.message || "YAML 解析错误";
        const line = extractLineFromYamlError(msg) || 1;
        diagnostics.push({
            from: lineColToPos(text, line, 1),
            to: lineColToPos(text, line, 100),
            severity: "error",
            message: `YAML 语法错误：${msg}`,
        });
        return diagnostics;
    }

    if (!doc || typeof doc !== "object") {
        diagnostics.push({
            from: 0,
            to: Math.min(10, text.length),
            severity: "error",
            message: "YAML 内容必须是一个对象（顶层应为 mapping）",
        });
        return diagnostics;
    }

    // 2. 校验顶层字段
    diagnostics.push(...validateTopLevel(doc, text));

    // 3. 校验 characters 数组
    if (doc.characters && Array.isArray(doc.characters)) {
        doc.characters.forEach((char, idx) => {
            diagnostics.push(...validateCharacter(char, idx, text));
        });
    }

    // 4. 校验 scenes 数组
    if (doc.scenes && Array.isArray(doc.scenes)) {
        doc.scenes.forEach((scene, sIdx) => {
            diagnostics.push(...validateScene(scene, sIdx, text));
        });
    }

    return diagnostics;
}

// ── 顶层字段校验 ─────────────────────────────────────────────────────────────

function validateTopLevel(doc, text) {
    const diags = [];
    const required = ["script_id", "title", "characters", "scenes"];
    const optional = ["genre", "logline", "source_location", "version"];

    // 检查必需字段
    for (const field of required) {
        if (!(field in doc)) {
            diags.push({
                from: 0,
                to: 50,
                severity: "warning",
                message: `缺少推荐字段：${field}`,
            });
        }
    }

    // 检查未知字段
    const allowed = [...required, ...optional];
    for (const key of Object.keys(doc)) {
        if (!allowed.includes(key)) {
            diags.push({
                from: 0,
                to: 50,
                severity: "info",
                message: `未知字段：${key}（将被忽略）`,
            });
        }
    }

    return diags;
}

// ── Character 校验 ────────────────────────────────────────────────────

function validateCharacter(char, idx, text) {
    const diags = [];
    const prefix = `characters[${idx}]`;

    if (!char || typeof char !== "object") {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix} 必须是一个对象`,
        });
        return diags;
    }

    // name 必需
    if (!char.name || typeof char.name !== "string") {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix}.name 是必需字段（字符串）`,
        });
    }

    // role 枚举检查
    if (char.role && !["protagonist", "supporting", "minor"].includes(char.role)) {
        diags.push({
            from: 0,
            to: 50,
            severity: "warning",
            message: `${prefix}.role 应是 protagonist/supporting/minor 之一`,
        });
    }

    return diags;
}

// ── Scene + Beats 校验 ──────────────────────────────────────────────────────

function validateScene(scene, sIdx, text) {
    const diags = [];
    const prefix = `scenes[${sIdx}]`;

    if (!scene || typeof scene !== "object") {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix} 必须是一个对象`,
        });
        return diags;
    }

    // scene_id 必需
    if (scene.scene_id === undefined || scene.scene_id === null) {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix}.scene_id 是必需字段`,
        });
    }

    // beats 必需且为数组
    if (!scene.beats || !Array.isArray(scene.beats)) {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix}.beats 必须是数组`,
        });
        return diags;
    }

    // 校验每个 Beat
    scene.beats.forEach((beat, bIdx) => {
        diags.push(...validateBeat(beat, sIdx, bIdx, text));
    });

    return diags;
}

// ── Beat 校验 ────────────────────────────────────────────────────────────────

const VALID_BEAT_TYPES = ["dialogue", "action", "narration", "transition", "heading"];

function validateBeat(beat, sIdx, bIdx, text) {
    const diags = [];
    const prefix = `scenes[${sIdx}].beats[${bIdx}]`;

    if (!beat || typeof beat !== "object") {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix} 必须是一个对象`,
        });
        return diags;
    }

    // type 必需且必须合法
    if (!beat.type) {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix}.type 是必需字段`,
        });
    } else if (!VALID_BEAT_TYPES.includes(beat.type)) {
        diags.push({
            from: 0,
            to: 50,
            severity: "warning",
            message: `${prefix}.type="${beat.type}" 不是标准类型，应为 ${VALID_BEAT_TYPES.join("/")}`,
        });
    }

    // 根据类型校验字段
    switch (beat.type) {
        case "dialogue":
            diags.push(...validateDialogueBeat(beat, prefix));
            break;
        case "action":
            diags.push(...validateActionBeat(beat, prefix));
            break;
        case "narration":
            diags.push(...validateNarrationBeat(beat, prefix));
            break;
        case "heading":
            diags.push(...validateHeadingBeat(beat, prefix));
            break;
    }

    // 校验 source_location（如果存在）
    if (beat.source_location && typeof beat.source_location === "object") {
        diags.push(...validateSourceLocation(beat.source_location, prefix));
    }

    return diags;
}

function validateDialogueBeat(beat, prefix) {
    const diags = [];
    if (!beat.character && !beat.character_id) {
        diags.push({
            from: 0,
            to: 50,
            severity: "error",
            message: `${prefix}: dialogue 类型必须有 character 或 character_id 字段`,
        });
    }
    if (!beat.content) {
        diags.push({
            from: 0,
            to: 50,
            severity: "warning",
            message: `${prefix}: dialogue 类型建议有 content 字段`,
        });
    }
    return diags;
}

function validateActionBeat(beat, prefix) {
    const diags = [];
    if (!beat.content) {
        diags.push({
            from: 0,
            to: 50,
            severity: "warning",
            message: `${prefix}: action 类型建议有 content 字段`,
        });
    }
    return diags;
}

function validateNarrationBeat(beat, prefix) {
    const diags = [];
    if (!beat.content) {
        diags.push({
            from: 0,
            to: 50,
            severity: "warning",
            message: `${prefix}: narration 类型建议有 content 字段`,
        });
    }
    return diags;
}

function validateHeadingBeat(beat, prefix) {
    const diags = [];
    if (!beat.text) {
        diags.push({
            from: 0,
            to: 50,
            severity: "warning",
            message: `${prefix}: heading 类型建议有 text 字段`,
        });
    }
    return diags;
}

function validateSourceLocation(sl, prefix) {
    const diags = [];
    const validKeys = ["chapter_index", "start_paragraph", "end_paragraph", "start_offset", "end_offset"];
    for (const key of Object.keys(sl)) {
        if (!validKeys.includes(key)) {
            diags.push({
                from: 0,
                to: 50,
                severity: "info",
                message: `${prefix}.source_location.${key} 是未知字段`,
            });
        }
        if (typeof sl[key] !== "number") {
            diags.push({
                from: 0,
                to: 50,
                severity: "warning",
                message: `${prefix}.source_location.${key} 应是整数`,
            });
        }
    }
    return diags;
}

// ── 工具函数 ─────────────────────────────────────────────────────────────────

/** 从 YAML 错误消息中提取行号（简单启发式） */
function extractLineFromYamlError(msg) {
    const m = msg.match(/line (\d+)/i);
    return m ? parseInt(m[1], 10) : null;
}

/**
 * 将行号+列号转换为 CM6 的 offset 位置
 * （简化版：按 \n 分段计算）
 */
function lineColToPos(text, line, col) {
    const lines = text.split("\n");
    let pos = 0;
    for (let i = 1; i < line && i <= lines.length; i++) {
        pos += lines[i - 1].length + 1; // +1 for \n
    }
    return pos + (col - 1);
}

// ── CodeMirror 6 linter Extension ─────────────────────────────────────
// 导出给 editor.js 使用

/**
 * 创建 YAML Schema linter Extension
 * 用法：在 EditorState.extensions 中加入 yamlSchemaLinter
 */
export const yamlSchemaLinter = linter((view) => {
    const text = view.state.doc.toString();
    try {
        return lintScriptYaml(text);
    } catch (e) {
        console.error("YAML lint error:", e);
        return [];
    }
});
