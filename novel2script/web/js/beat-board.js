/**
 * beat-board.js — Beat 可视化编辑（节拍板）
 *
 * 功能：以卡片式 UI 展示和编辑 Beat，支持拖拽排序
 * 依赖：Alpine.js（响应式）、Tailwind CSS（样式）、SortableJS（拖拽，CDN 引入）
 * 设计原则：低耦合、独立模块、与现有编辑器共存
 */

import { getContent, setContent } from "/js/editor.js";
import { parseBeatsFromYaml } from "/js/scroll-sync.js";

/**
 * 初始化节拍板
 * @param {object} app - Alpine.js app 实例
 */
export function initBeatBoard(app) {
    if (!app || !app.scriptEditor) {
        console.error('节拍板初始化失败：剧本编辑器未就绪');
        return;
    }

    // 解析 YAML 获取 Beat 数据
    const yamlText = getContent(app.scriptEditor);
    const beats = parseBeatsFromYaml(yamlText);

    // 按场景分组
    const scenes = groupBeatsByScene(beats);

    // 保存数据到 app
    app.beatBoardScenes = scenes;
    app.beatBoardBeats = beats;

    // 渲染节拍板
    renderBeatBoard(app);

    // 初始化拖拽排序
    initDragAndDrop(app);
}

/**
 * 按场景分组 Beat
 * @param {array} beats - 解析后的 Beat 列表
 * @returns {array} - 按场景分组的数组 [{sceneId, sceneTitle, beats}]
 */
function groupBeatsByScene(beats) {
    const sceneMap = new Map();

    beats.forEach((beat, index) => {
        const sceneId = beat.scene_id || 'unknown';
        const sceneTitle = beat.scene_title || `场景 ${sceneId}`;

        if (!sceneMap.has(sceneId)) {
            sceneMap.set(sceneId, {
                sceneId: sceneId,
                sceneTitle: sceneTitle,
                beats: []
            });
        }

        // 添加索引，用于拖拽后更新 YAML
        beat._index = index;
        sceneMap.get(sceneId).beats.push(beat);
    });

    return Array.from(sceneMap.values());
}

/**
 * 渲染节拍板 UI
 * @param {object} app - Alpine.js app 实例
 */
function renderBeatBoard(app) {
    const container = document.getElementById('beat-board-container');
    if (!container) {
        console.error('找不到节拍板容器 #beat-board-container');
        return;
    }

    // 清空容器
    container.innerHTML = '';

    // 如果没有 Beat
    if (!app.beatBoardScenes || app.beatBoardScenes.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <p class="text-lg font-medium">暂无 Beat 数据</p>
                <p class="text-sm mt-2">请先转换小说或手动添加 Beat</p>
            </div>
        `;
        return;
    }

    // 渲染每个场景
    app.beatBoardScenes.forEach((scene, sceneIndex) => {
        const sceneElement = createSceneElement(scene, sceneIndex, app);
        container.appendChild(sceneElement);
    });
}

/**
 * 创建场景元素
 * @param {object} scene - 场景数据
 * @param {number} sceneIndex - 场景索引
 * @param {object} app - Alpine.js app 实例
 * @returns {HTMLElement} - 场景 DOM 元素
 */
function createSceneElement(scene, sceneIndex, app) {
    const sceneDiv = document.createElement('div');
    sceneDiv.className = 'beat-board-scene mb-6';
    sceneDiv.setAttribute('data-scene-id', scene.sceneId);

    // 场景标题（可折叠）
    const sceneHeader = document.createElement('div');
    sceneHeader.className = 'flex items-center justify-between mb-3 cursor-pointer hover:bg-gray-50 p-2 rounded-lg';
    sceneHeader.innerHTML = `
        <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-gray-500 toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
            <h3 class="text-lg font-bold text-gray-900">${scene.sceneTitle}</h3>
            <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">${scene.beats.length} 个 Beat</span>
        </div>
        <button class="btn-nav-sm text-xs" onclick="window._beatBoardAddBeat('${scene.sceneId}')">
            添加 Beat
        </button>
    `;

    // 点击折叠/展开
    sceneHeader.addEventListener('click', (e) => {
        if (e.target.closest('button')) return; // 不阻止按钮点击
        toggleSceneCollapse(sceneDiv);
    });

    sceneDiv.appendChild(sceneHeader);

    // Beat 卡片容器（可拖拽）
    const beatsContainer = document.createElement('div');
    beatsContainer.className = 'beat-cards-container pl-8 space-y-2';
    beatsContainer.setAttribute('data-scene-id', scene.sceneId);

    scene.beats.forEach((beat, beatIndex) => {
        const beatCard = createBeatCard(beat, beatIndex, app);
        beatsContainer.appendChild(beatCard);
    });

    sceneDiv.appendChild(beatsContainer);

    return sceneDiv;
}

/**
 * 创建 Beat 卡片元素
 * @param {object} beat - Beat 数据
 * @param {number} beatIndex - Beat 在场景中的索引
 * @param {object} app - Alpine.js app 实例
 * @returns {HTMLElement} - Beat 卡片 DOM 元素
 */
function createBeatCard(beat, beatIndex, app) {
    const card = document.createElement('div');
    card.className = 'beat-card p-3 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer';
    card.setAttribute('data-beat-index', beat._index);
    card.setAttribute('data-beat-id', beat.id || '');

    // 根据 Beat 类型设置颜色
    const typeColorMap = {
        'dialogue': 'border-l-4 border-l-blue-500',
        'action': 'border-l-4 border-l-yellow-500',
        'narration': 'border-l-4 border-l-green-500'
    };
    card.classList.add(...(typeColorMap[beat.type] || 'border-l-4 border-l-gray-500').split(' '));

    // 卡片内容
    let cardContent = '';

    if (beat.type === 'dialogue') {
        // 对白 Beat：显示角色名 + 内容 + 情绪标签
        const emotionColor = getEmotionColor(beat.emotion);
        cardContent = `
            <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-bold text-blue-600">${beat.character || '未知角色'}</span>
                ${beat.emotion ? `<span class="text-xs px-2 py-0.5 rounded-full ${emotionColor}">${beat.emotion}</span>` : ''}
            </div>
            <p class="text-sm text-gray-700 line-clamp-2">${beat.content || ''}</p>
        `;
    } else if (beat.type === 'action') {
        // 动作 Beat：显示内容
        cardContent = `
            <div class="flex items-center gap-1 mb-1">
                <span class="text-xs font-semibold text-yellow-600">动作</span>
            </div>
            <p class="text-sm text-gray-700 line-clamp-2">${beat.content || ''}</p>
        `;
    } else if (beat.type === 'narration') {
        // 旁白 Beat：显示内容
        cardContent = `
            <div class="flex items-center gap-1 mb-1">
                <span class="text-xs font-semibold text-green-600">旁白</span>
            </div>
            <p class="text-sm text-gray-700 line-clamp-2">${beat.content || ''}</p>
        `;
    }

    card.innerHTML = cardContent;

    // 点击卡片 → 定位到 YAML 对应位置
    card.addEventListener('click', () => {
        scrollToBeatInYaml(beat._index, app);
    });

    // 双击卡片 → 打开编辑器
    card.addEventListener('dblclick', () => {
        openBeatEditor(beat._index, app);
    });

    return card;
}

/**
 * 获取情绪对应的颜色类名
 * @param {string} emotion - 情绪标签
 * @returns {string} - Tailwind 颜色类名
 */
function getEmotionColor(emotion) {
    const colorMap = {
        'happy': 'bg-green-100 text-green-700',
        'excited': 'bg-purple-100 text-purple-700',
        'calm': 'bg-yellow-100 text-yellow-700',
        'sad': 'bg-blue-100 text-blue-700',
        'fear': 'bg-gray-100 text-gray-500',
        'angry': 'bg-red-100 text-red-700'
    };
    return colorMap[emotion] || 'bg-gray-100 text-gray-500';
}

/**
 * 折叠/展开场景
 * @param {HTMLElement} sceneDiv - 场景 DOM 元素
 */
function toggleSceneCollapse(sceneDiv) {
    const beatsContainer = sceneDiv.querySelector('.beat-cards-container');
    const toggleIcon = sceneDiv.querySelector('.toggle-icon');

    if (!beatsContainer || !toggleIcon) return;

    const isCollapsed = beatsContainer.style.display === 'none';

    if (isCollapsed) {
        beatsContainer.style.display = 'block';
        toggleIcon.style.transform = 'rotate(0deg)';
    } else {
        beatsContainer.style.display = 'none';
        toggleIcon.style.transform = 'rotate(-90deg)';
    }
}

/**
 * 初始化拖拽排序（使用 SortableJS）
 * @param {object} app - Alpine.js app 实例
 */
function initDragAndDrop(app) {
    // 检查 SortableJS 是否已加载
    if (typeof Sortable === 'undefined') {
        console.warn('SortableJS 未加载，拖拽功能不可用');
        return;
    }

    // 为每个场景的 Beat 容器初始化 Sortable
    const containers = document.querySelectorAll('.beat-cards-container');
    containers.forEach(container => {
        new Sortable(container, {
            group: 'beats',  // 允许跨场景拖拽
            animation: 150,
            ghostClass: 'beat-card-ghost',
            chosenClass: 'beat-card-chosen',
            dragClass: 'beat-card-drag',

            onEnd: (evt) => {
                // 拖拽结束后，更新 YAML 中的顺序
                handleDragEnd(app);
            }
        });
    });
}

/**
 * 处理拖拽结束事件
 * @param {object} app - Alpine.js app 实例
 */
function handleDragEnd(app) {
    // 重新读取所有 Beat 的顺序
    const newOrder = [];
    const containers = document.querySelectorAll('.beat-cards-container');

    containers.forEach(container => {
        const cards = container.querySelectorAll('.beat-card');
        cards.forEach(card => {
            const beatIndex = parseInt(card.getAttribute('data-beat-index'));
            newOrder.push(beatIndex);
        });
    });

    // 更新 YAML（重新排序）
    updateYamlOrder(newOrder, app);
}

/**
 * 更新 YAML 中 Beat 的顺序
 * @param {array} newOrder - 新的顺序（Beat 索引数组）
 * @param {object} app - Alpine.js app 实例
 */
function updateYamlOrder(newOrder, app) {
    if (!app.scriptEditor) return;

    const yamlText = getContent(app.scriptEditor);
    const beats = parseBeatsFromYaml(yamlText);

    // 按新顺序重新排列 Beat
    const newBeats = newOrder.map(idx => beats[idx]);

    // 重新生成 YAML（简化版：直接替换 beats 部分）
    // 注意：这里需要完整的 YAML 重建逻辑，建议使用 schema.py 的 to_yaml()
    console.log('拖拽排序完成，新顺序：', newOrder);

    // TODO: 调用 API 保存新顺序，或直接在前端重建 YAML
    app.showToast('Beat 顺序已更新（需保存）');
}

/**
 * 在 YAML 编辑器中定位到指定 Beat
 * @param {number} beatIndex - Beat 索引
 * @param {object} app - Alpine.js app 实例
 */
function scrollToBeatInYaml(beatIndex, app) {
    if (!app.scriptEditor) return;

    const yamlText = getContent(app.scriptEditor);
    const beats = parseBeatsFromYaml(yamlText);

    if (beatIndex < 0 || beatIndex >= beats.length) return;

    const beat = beats[beatIndex];
    if (!beat || !beat.lineStart) return;

    // 滚动到对应行
    const line = beat.lineStart;
    app.scriptEditor.dispatch({
        selection: { anchor: app.scriptEditor.state.doc.line(line).from },
        scrollIntoView: true
    });

    app.showToast(`已定位到 Beat #${beatIndex + 1}`);
}

/**
 * 打开 Beat 编辑器（双击卡片时）
 * @param {number} beatIndex - Beat 索引
 * @param {object} app - Alpine.js app 实例
 */
function openBeatEditor(beatIndex, app) {
    // 触发 beat-editors.js 中的编辑事件
    window.dispatchEvent(new CustomEvent('edit-beat', {
        detail: { beatIndex: beatIndex }
    }));
}

/**
 * 添加新 Beat 到指定场景
 * @param {string} sceneId - 场景 ID
 */
window._beatBoardAddBeat = function(sceneId) {
    console.log('添加 Beat 到场景：', sceneId);
    // TODO: 实现添加 Beat 逻辑
    alert('添加 Beat 功能待实现');
};

/**
 * 刷新节拍板（YAML 变化后调用）
 * @param {object} app - Alpine.js app 实例
 */
export function refreshBeatBoard(app) {
    initBeatBoard(app);
}

// 导出给全局使用
window.initBeatBoard = initBeatBoard;
window.refreshBeatBoard = refreshBeatBoard;
