/**
 * emotion-curve.js — 情绪曲线可视化
 *
 * 功能：在剧本编辑器中显示情绪曲线图表
 * 依赖：Chart.js（CDN 引入）、scroll-sync.js（解析 Beat）
 */

import { getContent } from "/js/editor.js";
import { parseBeatsFromYaml } from "/js/scroll-sync.js";

// 情绪到数值的映射
const EMOTION_INTENSITY = {
    'happy': 5,      // 高兴
    'excited': 4,    // 兴奋
    'calm': 3,       // 平静
    'sad': 2,        // 悲伤
    'fear': 1,       // 恐惧
    'angry': 0,      // 愤怒
};

// 情绪到颜色的映射
const EMOTION_COLOR = {
    'happy': '#10b981',    // 绿色
    'excited': '#8b5cf6',  // 紫色
    'calm': '#f59e0b',    // 黄色
    'sad': '#3b82f6',     // 蓝色
    'fear': '#6b7280',    // 灰色
    'angry': '#ef4444',    // 红色
};

// Chart.js 实例
let emotionChart = null;

/**
 * 初始化情绪曲线图表
 * @param {object} app - Alpine.js app 实例
 */
export function initEmotionCurveChart(app) {
    const canvas = document.getElementById('emotionCurveChart');
    if (!canvas) {
        console.error('找不到 emotionCurveChart canvas');
        return;
    }

    // 获取剧本 YAML 文本
    const scriptEditor = app.scriptEditor;
    if (!scriptEditor) {
        console.error('剧本编辑器未初始化');
        return;
    }

    const yamlText = getContent(scriptEditor);
    const granularity = app.emotionCurveGranularity || 'beat';

    // 准备数据
    const chartData = prepareEmotionData(yamlText, granularity);

    // 如果已存在图表，先销毁
    if (emotionChart) {
        emotionChart.destroy();
    }

    // 创建新图表
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('无法获取 canvas 2d context');
        return;
    }
    try {
        emotionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: '情绪强度',
                data: chartData.intensities,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: chartData.colors,
                pointBorderColor: chartData.colors,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5,
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            const emotionMap = {
                                0: '愤怒',
                                1: '恐惧',
                                2: '悲伤',
                                3: '平静',
                                4: '兴奋',
                                5: '高兴'
                            };
                            return emotionMap[value] || value;
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    handleChartClick(app, index, granularity, yamlText);
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const idx = context.dataIndex;
                            const emotion = chartData.emotions[idx];
                            const intensity = chartData.intensities[idx];
                            return `情绪: ${emotion || '未知'} (${intensity}/5)`;
                        }
                    }
                }
            }
        }
    });
    } catch (e) {
        console.warn('情绪曲线图表初始化失败（非关键错误）:', e.message);
        return;
    }

    // 保存图表实例到 app
    app.emotionCurveChart = emotionChart;
}

/**
 * 准备情绪数据
 * @param {string} yamlText - 剧本 YAML 文本
 * @param {string} granularity - 粒度：'beat' 或 'scene'
 * @returns {object} - {labels, intensities, emotions, colors}
 */
function prepareEmotionData(yamlText, granularity) {
    const beats = parseBeatsFromYaml(yamlText);

    if (granularity === 'beat') {
        // Beat 级：每个 Beat 一个点
        const labels = beats.map((beat, idx) => `Beat ${idx + 1}`);
        const emotions = beats.map(beat => beat.emotion || '');
        const intensities = beats.map(beat => {
            const emotion = beat.emotion || '';
            return EMOTION_INTENSITY[emotion] !== undefined
                ? EMOTION_INTENSITY[emotion]
                : 3; // 默认平静
        });
        const colors = beats.map(beat => {
            const emotion = beat.emotion || '';
            return EMOTION_COLOR[emotion] || '#6b7280';
        });

        return { labels, intensities, emotions, colors };
    } else {
        // 场景级：每个场景一个点（取平均情绪）
        const sceneMap = new Map();

        beats.forEach((beat, idx) => {
            const sceneId = beat.scene_id || 'unknown';
            if (!sceneMap.has(sceneId)) {
                sceneMap.set(sceneId, []);
            }
            sceneMap.get(sceneId).push(idx);
        });

        const labels = [];
        const intensities = [];
        const emotions = [];
        const colors = [];

        sceneMap.forEach((beatIndices, sceneId) => {
            labels.push(`场景 ${sceneId}`);

            // 计算平均情绪强度
            let totalIntensity = 0;
            let emotionCount = {};

            beatIndices.forEach(idx => {
                const beat = beats[idx];
                const emotion = beat.emotion || '';
                const intensity = EMOTION_INTENSITY[emotion] !== undefined
                    ? EMOTION_INTENSITY[emotion]
                    : 3;

                totalIntensity += intensity;

                if (!emotionCount[emotion]) {
                    emotionCount[emotion] = 0;
                }
                emotionCount[emotion]++;
            });

            const avgIntensity = totalIntensity / beatIndices.length;

            // 找出出现最多的情绪
            let maxCount = 0;
            let dominantEmotion = '';
            Object.entries(emotionCount).forEach(([emotion, count]) => {
                if (count > maxCount) {
                    maxCount = count;
                    dominantEmotion = emotion;
                }
            });

            intensities.push(avgIntensity);
            emotions.push(dominantEmotion);
            colors.push(EMOTION_COLOR[dominantEmotion] || '#6b7280');
        });

        return { labels, intensities, emotions, colors };
    }
}

/**
 * 处理图表点击事件
 * @param {object} app - Alpine.js app 实例
 * @param {number} index - 点击的数据点索引
 * @param {string} granularity - 粒度
 * @param {string} yamlText - 剧本 YAML 文本
 */
function handleChartClick(app, index, granularity, yamlText) {
    const beats = parseBeatsFromYaml(yamlText);

    if (granularity === 'beat') {
        // 选中 Beat
        app.selectedEmotionPoint = {
            type: 'beat',
            index: index,
            emotion: beats[index]?.emotion || '未知',
            intensity: EMOTION_INTENSITY[beats[index]?.emotion] || 3
        };
    } else {
        // 选中场景
        const sceneMap = new Map();
        beats.forEach((beat, idx) => {
            const sceneId = beat.scene_id || 'unknown';
            if (!sceneMap.has(sceneId)) {
                sceneMap.set(sceneId, []);
            }
            sceneMap.get(sceneId).push(idx);
        });

        const sceneIds = Array.from(sceneMap.keys());
        const sceneId = sceneIds[index];

        app.selectedEmotionPoint = {
            type: 'scene',
            sceneId: sceneId,
            emotion: '', // 会从 prepareEmotionData 计算
            intensity: 0
        };
    }
}

// 导出给全局使用
window.initEmotionCurveChart = initEmotionCurveChart;
