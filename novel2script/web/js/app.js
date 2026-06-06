/** InkScript 前端主逻辑（Alpine.js） */

function app() {
    return {
        // ── 状态 ──────────────────────
        view: 'home',             // 'home' | 'projects' | 'editor' | 'config'
        previousView: null,        // 记录上一个视图，用于返回
        activeProject: null,       // 当前打开的项目 {id, name, ...}
        projects: [],              // 项目列表
        novelText: '',             // 编辑器中的小说原文（回退用）
        scriptYaml: '',            // 编辑器中的剧本 YAML（回退用）
        novelWordCount: 0,        // 小说字数
        scriptLineCount: 0,       // 剧本行数
        validationError: '',       // 校验错误提示
        converting: false,         // 是否正在转换
        progress: 0,               // 转换进度 0-100
        currentStep: '',           // 当前转换步骤名称
        taskId: '',                // 当前转换任务 ID
        eventSource: null,         // SSE 连接
        settingsTab: 'ai',         // 设置侧边栏当前选项
        config: {                  // 配置
            provider: 'openai',
            base_url: '',
            api_key: '',
            model_name: '',
            temperature: 0.7,
            top_p: 1.0,
            max_tokens: 4096,
            frequency_penalty: 0.0,
            presence_penalty: 0.0,
            timeout: 60,
            max_retries: 3,
            request_interval: 0.5,
        },

        // CodeMirror 6 实例（由 initEditors() 初始化）
        novelEditor: null,          // EditorView 实例（小说）
        scriptEditor: null,        // EditorView 实例（剧本）

        // 自动保存计时器
        _novelSaveTimer: null,
        _scriptSaveTimer: null,

        // 快捷键帮助 Modal 显示状态
        showShortcutsModal: false,

        // 项目搜索和排序
        projectSearch: '',       // 项目搜索关键词
        projectSortBy: 'updated_at',  // 排序字段：name|created_at|updated_at
        projectSortOrder: 'desc', // 排序方向：asc|desc

        // Skills 管理
        skills: [],              // 所有 Skills 列表
        builtinSkills: [],       // 内置 Skills
        userSkills: [],         // 用户自定义 Skills
        showCreateSkillModal: false,  // 是否显示创建 Skill 模态框
        newSkillName: '',       // 新 Skill 名称
        newSkillDescription: '', // 新 Skill 描述
        newSkillPrompt: '',     // 新 Skill Prompt 模板

        // 版本历史
        showVersionPanel: false,  // 是否显示版本历史面板
        versions: [],            // 版本列表
        currentVersion: null,    // 当前查看的版本详情

        // 回收站
        showTrash: false,        // 是否显示回收站
        trashItems: [],          // 回收站项目列表

        // 编辑器分栏拖拽
        leftPanelWidth: 50,        // 左侧面板宽度百分比（可拖拽调整）
        _dragStartX: 0,           // 拖拽起始位置
        _dragStartWidth: 0,       // 拖拽起始宽度
        _isDragging: false,        // 是否正在拖拽

        // ── 提供商默认配置 ─────────────────
        providers: {
            openai: {
                name: 'OpenAI',
                url: 'https://api.openai.com/v1',
                modelPlaceholder: 'gpt-4o, gpt-4-turbo, gpt-3.5-turbo',
                modelHint: 'OpenAI 模型：gpt-4o / gpt-4-turbo / gpt-3.5-turbo',
            },
            deepseek: {
                name: 'DeepSeek',
                url: 'https://api.deepseek.com',
                modelPlaceholder: 'deepseek-chat, deepseek-reasoner',
                modelHint: 'DeepSeek 模型：deepseek-chat / deepseek-reasoner',
            },
            anthropic: {
                name: 'Anthropic',
                url: 'https://api.anthropic.com',
                modelPlaceholder: 'claude-3-5-sonnet-20241022, claude-3-opus-20240229',
                modelHint: 'Claude 模型：claude-3-5-sonnet / claude-3-opus / claude-3-haiku',
            },
            qwen: {
                name: '通义千问',
                url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                modelPlaceholder: 'qwen-turbo, qwen-plus, qwen-max',
                modelHint: '通义千问模型：qwen-turbo / qwen-plus / qwen-max',
            },
            gemini: {
                name: 'Gemini',
                url: 'https://generativelanguage.googleapis.com/v1beta',
                modelPlaceholder: 'gemini-1.5-pro, gemini-1.5-flash',
                modelHint: 'Gemini 模型：gemini-1.5-pro / gemini-1.5-flash',
            },
            moonshot: {
                name: 'Moonshot',
                url: 'https://api.moonshot.cn/v1',
                modelPlaceholder: 'moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k',
                modelHint: 'Moonshot 模型：moonshot-v1-8k / moonshot-v1-32k / moonshot-v1-128k',
            },
            glm: {
                name: 'GLM-4',
                url: 'https://open.bigmodel.cn/api/paas/v4',
                modelPlaceholder: 'glm-4, glm-4-flash, glm-4-plus',
                modelHint: 'GLM-4 模型：glm-4 / glm-4-flash / glm-4-plus',
            },
            siliconflow: {
                name: 'SiliconFlow',
                url: 'https://api.siliconflow.cn/v1',
                modelPlaceholder: 'Qwen/Qwen2-7B-Instruct, meta-llama/Meta-Llama-3.1-8B-Instruct',
                modelHint: 'SiliconFlow 模型：Qwen/Qwen2-7B-Instruct / meta-llama/Meta-Llama-3.1-8B-Instruct',
            },
            custom: {
                name: '自定义',
                url: '',
                modelPlaceholder: '输入自定义模型名称',
                modelHint: '请输入兼容 OpenAI API 格式的地址和模型名称',
            },
        },

        // ── 生命周期 ────────────────────
        init() {
            this.loadProjects();
            this.loadConfig();
            this._initKeyboardShortcuts();
        },

        // ── 快捷键系统 ────────────────────
        _initKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                const isCtrlOrCmd = e.ctrlKey || e.metaKey;
                
                // Ctrl/Cmd + S：保存
                if (isCtrlOrCmd && e.key === 's') {
                    e.preventDefault();
                    if (this.activeProject) {
                        this.saveNovel();
                        this.saveScript();
                        this.showToast('已保存（Ctrl+S）');
                    }
                }
                
                // Escape：关闭弹出层 / 退出全屏
                if (e.key === 'Escape') {
                    // 关闭快捷键帮助 modal
                    if (this.showShortcutsModal) {
                        this.showShortcutsModal = false;
                    }
                    // 关闭 Beat 编辑器（通过事件）
                    window.dispatchEvent(new CustomEvent('close-beat-editor'));
                }
                
                // ?：显示快捷键帮助
                if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                    // 避免在输入框中触发
                    const tag = e.target.tagName.toLowerCase();
                    if (tag !== 'input' && tag !== 'textarea') {
                        e.preventDefault();
                        this.showShortcutsModal = true;
                    }
                }
            });
        },

        // ── 导航 ────────────────────────
        goHome() {
            this.previousView = this.view;
            this.view = 'home';
        },

        goBack() {
            if (this.previousView) {
                this.view = this.previousView;
                this.previousView = null;
            } else {
                this.view = 'home';
            }
        },

        // ── 提供商辅助方法 ─────────────────
        getProviderName() {
            return this.providers[this.config.provider]?.name || '';
        },

        getProviderUrl() {
            return this.providers[this.config.provider]?.url || '';
        },

        getModelPlaceholder() {
            return this.providers[this.config.provider]?.modelPlaceholder || '';
        },

        getModelHint() {
            return this.providers[this.config.provider]?.modelHint || '';
        },

        // ── 项目管理 ─────────────────────
        async loadProjects() {
            const params = new URLSearchParams();
            if (this.projectSearch) params.append('search', this.projectSearch);
            if (this.projectSortBy) params.append('sort_by', this.projectSortBy);
            if (this.projectSortOrder) params.append('order', this.projectSortOrder);
            
            const url = `/api/v1/projects${params.toString() ? '?' + params.toString() : ''}`;
            const res = await fetch(url);
            const data = await res.json();
            if (data.code === 0) {
                this.projects = data.data;
            }
        },

        /** 搜索项目 */
        async searchProjects() {
            await this.loadProjects();
        },

        /** 切换排序 */
        async changeSort(sortBy) {
            // 如果点击的是当前排序字段，则切换排序方向
            if (this.projectSortBy === sortBy) {
                this.projectSortOrder = this.projectSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                this.projectSortBy = sortBy;
                this.projectSortOrder = 'desc'; // 默认降序
            }
            await this.loadProjects();
        },

        async createProject() {
            const name = prompt('请输入项目名称：');
            if (!name) return;
            const res = await fetch('/api/v1/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            });
            const data = await res.json();
            if (data.code === 0) {
                await this.loadProjects();
                this.view = 'projects';
            }
        },

        async openProject(id) {
            const res = await fetch(`/api/v1/projects/${id}`);
            const data = await res.json();
            if (data.code === 0) {
                this.previousView = this.view;
                this.activeProject = data.data;
                this.view = 'editor';
                await this.loadNovel();
                await this.loadScript();
            }
        },

        async deleteProject(id) {
            if (!confirm('确认删除该项目？项目将进入回收站。')) return;
            await fetch(`/api/v1/projects/${id}`, { method: 'DELETE' });
            await this.loadProjects();
            this.showToast('项目已移动到回收站');
        },

        // ── 回收站管理 ─────────────────────
        async toggleTrash() {
            this.showTrash = !this.showTrash;
            if (this.showTrash) {
                await this.loadTrash();
            }
        },

        async loadTrash() {
            try {
                const res = await fetch('/api/v1/trash');
                const data = await res.json();
                if (data.code === 0) {
                    this.trashItems = data.data || [];
                }
            } catch (e) {
                console.error('加载回收站失败:', e);
            }
        },

        async restoreProject(projectId) {
            if (!confirm('确认恢复该项目？')) return;
            
            try {
                const res = await fetch(`/api/v1/trash/${projectId}/restore`, {
                    method: 'POST'
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast('项目已恢复');
                    await this.loadTrash();
                    await this.loadProjects();
                } else {
                    alert('恢复失败: ' + data.message);
                }
            } catch (e) {
                alert('恢复失败: ' + e.message);
            }
        },

        async permanentDelete(projectId) {
            if (!confirm('确认永久删除该项目？删除后不可恢复。')) return;
            
            try {
                const res = await fetch(`/api/v1/trash/${projectId}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast('项目已永久删除');
                    await this.loadTrash();
                } else {
                    alert('删除失败: ' + data.message);
                }
            } catch (e) {
                alert('删除失败: ' + e.message);
            }
        },

        // ── Skill 管理 ─────────────────────
        async loadSkills() {
            try {
                const res = await fetch('/api/v1/skills');
                const data = await res.json();
                if (data.code === 0) {
                    this.builtinSkills = data.data.builtin || [];
                    this.userSkills = data.data.user || [];
                    this.skills = [...this.builtinSkills, ...this.userSkills];
                }
            } catch (e) {
                console.error('加载 Skills 失败:', e);
            }
        },

        async toggleSkillEnable(skill) {
            try {
                const res = await fetch(`/api/v1/skills/${skill.id}/enable`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ enabled: !skill.enabled })
                });
                const data = await res.json();
                if (data.code === 0) {
                    await this.loadSkills();
                    this.showToast('Skill 状态已更新');
                } else {
                    alert('更新失败: ' + data.message);
                }
            } catch (e) {
                alert('更新失败: ' + e.message);
            }
        },

        async updateSkillPriority(skill, newPriority) {
            try {
                const res = await fetch(`/api/v1/skills/${skill.id}/priority`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ priority: parseInt(newPriority) })
                });
                const data = await res.json();
                if (data.code === 0) {
                    await this.loadSkills();
                    this.showToast('优先级已更新');
                } else {
                    alert('更新失败: ' + data.message);
                }
            } catch (e) {
                alert('更新失败: ' + e.message);
            }
        },

        async runSkill(skill) {
            const input = prompt('请输入 Skill 的输入内容:');
            if (!input) return;

            try {
                const res = await fetch(`/api/v1/skills/${skill.id}/run`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ input: input })
                });
                const data = await res.json();
                if (data.code === 0) {
                    alert('Skill 运行结果:\n\n' + JSON.stringify(data.data, null, 2));
                } else {
                    alert('运行失败: ' + data.message);
                }
            } catch (e) {
                alert('运行失败: ' + e.message);
            }
        },

        async deleteUserSkill(skill) {
            if (!confirm(`确认删除 Skill "${skill.name}"？`)) return;

            try {
                const res = await fetch(`/api/v1/skills/${skill.id}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast('Skill 已删除');
                    await this.loadSkills();
                } else {
                    alert('删除失败: ' + data.message);
                }
            } catch (e) {
                alert('删除失败: ' + e.message);
            }
        },

        async createSkill() {
            if (!this.newSkillName.trim()) {
                alert('请输入 Skill 名称');
                return;
            }

            try {
                const res = await fetch('/api/v1/skills', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: this.newSkillName.trim(),
                        description: this.newSkillDescription.trim(),
                        prompt: this.newSkillPrompt.trim()
                    })
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast('Skill 创建成功');
                    this.showCreateSkillModal = false;
                    this.newSkillName = '';
                    this.newSkillDescription = '';
                    this.newSkillPrompt = '';
                    await this.loadSkills();
                } else {
                    alert('创建失败: ' + data.message);
                }
            } catch (e) {
                alert('创建失败: ' + e.message);
            }
        },

        // ── 配置管理 ─────────────────────
        async loadConfig() {
            try {
                const res = await fetch('/api/v1/config');
                const data = await res.json();
                if (data.code === 0) {
                    const d = data.data;
                    this.config = {
                        provider: d.provider || 'openai',
                        base_url: d.base_url || '',
                        api_key: '',  // 不从后端读取 API Key（安全考虑）
                        model_name: d.model_name || '',
                        temperature: d.temperature ?? 0.7,
                        top_p: d.top_p ?? 1.0,
                        max_tokens: d.max_tokens || 4096,
                        frequency_penalty: d.frequency_penalty ?? 0.0,
                        presence_penalty: d.presence_penalty ?? 0.0,
                        timeout: d.timeout || 60,
                        max_retries: d.max_retries || 3,
                        request_interval: d.request_interval || 0.5,
                    };
                }
            } catch (e) {
                console.error('加载配置失败:', e);
            }
        },

        async saveConfig() {
            const payload = {
                provider: this.config.provider,
                base_url: this.config.base_url,
                model_name: this.config.model_name,
                temperature: parseFloat(this.config.temperature),
                top_p: parseFloat(this.config.top_p),
                max_tokens: parseInt(this.config.max_tokens),
                frequency_penalty: parseFloat(this.config.frequency_penalty),
                presence_penalty: parseFloat(this.config.presence_penalty),
                timeout: parseFloat(this.config.timeout),
                max_retries: parseInt(this.config.max_retries),
                request_interval: parseFloat(this.config.request_interval),
            };
            if (this.config.api_key) {
                payload.api_key = this.config.api_key;
            }
            
            try {
                const res = await fetch('/api/v1/config', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (data.code === 0) {
                    // 显示保存成功提示
                    const btn = event.target;
                    const originalText = btn.textContent;
                    btn.textContent = '已保存！';
                    btn.disabled = true;
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.disabled = false;
                    }, 1500);
                } else {
                    alert('保存失败: ' + data.message);
                }
            } catch (e) {
                alert('保存失败: ' + e.message);
            }
        },

        // ── 编辑器分栏拖拽 ─────────────────────
        
        /** 开始拖拽分隔条 */
        startDrag(event) {
            event.preventDefault();
            this._isDragging = true;
            this._dragStartX = event.clientX;
            this._dragStartWidth = this.leftPanelWidth;
            
            // 添加拖拽样式
            document.body.classList.add('dragging');
            const divider = event.target.closest('.editor-divider');
            if (divider) {
                divider.classList.add('dragging');
            }
            
            // 绑定全局鼠标事件
            this._onDragMove = this.doDrag.bind(this);
            this._onDragEnd = this.stopDrag.bind(this);
            document.addEventListener('mousemove', this._onDragMove);
            document.addEventListener('mouseup', this._onDragEnd);
        },
        
        /** 执行拖拽 */
        doDrag(event) {
            if (!this._isDragging) return;
            
            const container = document.querySelector('.editor-wrapper');
            if (!container) return;
            
            const containerWidth = container.offsetWidth;
            const deltaX = event.clientX - this._dragStartX;
            const deltaPercent = (deltaX / containerWidth) * 100;
            
            let newWidth = this._dragStartWidth + deltaPercent;
            
            // 限制最小和最大宽度（20% - 80%）
            newWidth = Math.max(20, Math.min(80, newWidth));
            
            this.leftPanelWidth = newWidth;
        },
        
        /** 停止拖拽 */
        stopDrag() {
            this._isDragging = false;
            
            // 移除拖拽样式
            document.body.classList.remove('dragging');
            const divider = document.querySelector('.editor-divider');
            if (divider) {
                divider.classList.remove('dragging');
            }
            
            // 移除全局鼠标事件
            document.removeEventListener('mousemove', this._onDragMove);
            document.removeEventListener('mouseup', this._onDragEnd);
            this._onDragMove = null;
            this._onDragEnd = null;
        },

        // ── 编辑器 ─────────────────────

        /** 初始化 CodeMirror 6 编辑器（editor 视图挂载后调用） */
        async initEditors() {
            // 动态导入 editor.js（因为是 type="importmap" 模块）
            const { initNovelEditor, initScriptEditor, getContent, setContent } = await import('/js/editor.js');

            const novelContainer = document.getElementById('novel-editor-container');
            const scriptContainer = document.getElementById('script-editor-container');

            if (!novelContainer || !scriptContainer) return;

            // 如果已初始化，先销毁
            if (this.novelEditor) this.novelEditor.destroy();
            if (this.scriptEditor) this.scriptEditor.destroy();

            // 初始化小说编辑器（可编辑）
            this.novelEditor = initNovelEditor(novelContainer, this.novelText || '', { readOnly: false });

            // 初始化剧本编辑器（可编辑）
            this.scriptEditor = initScriptEditor(scriptContainer, this.scriptYaml || '', { readOnly: false });

            // 启用小说编辑器的右键菜单（预处理功能 P1-7）
            this._initNovelContextMenu();

            // 启用 Beat 内联编辑（P0-3）
            this._initBeatEditing();

            // 监听内容变更事件（来自 editor.js 的 CustomEvent）
            window.addEventListener('novel-change', (e) => {
                this.novelText = e.detail.content;
                this.novelWordCount = this.countWords(e.detail.content);
                this.debounceSaveNovel();
            });

            window.addEventListener('script-change', (e) => {
                this.scriptYaml = e.detail.content;
                this.debounceSaveScript();
            });

            // 初始化字数统计
            this.novelWordCount = this.countWords(this.novelText || '');
        },

        /** 初始化小说编辑器右键菜单（预处理功能） */
        async _initNovelContextMenu() {
            if (!this.novelEditor) return;
            
            const { initNovelContextMenu, mergeParagraphs, insertMark } = await import('/js/editor.js');
            
            // 初始化右键菜单，并传入处理函数
            initNovelContextMenu(this.novelEditor, {
                onDelete: (view, from, to) => {
                    // 删除选中内容（先确认）
                    if (confirm('确认删除选中内容？此操作不可撤销。')) {
                        view.dispatch({
                            changes: { from, to, insert: '' }
                        });
                        this.showToast('已删除选中内容');
                        this.debounceSaveNovel();
                    }
                },
                onMerge: (view) => {
                    // 合并段落
                    mergeParagraphs(view);
                    this.showToast('已合并段落');
                    this.debounceSaveNovel();
                },
                onAddMark: (view, markType, noteText) => {
                    // 添加标记
                    insertMark(view, markType, noteText);
                    const markText = markType === 'note' ? `note: ${noteText}` : markType;
                    this.showToast(`已添加标记: ${markText}`);
                    this.debounceSaveNovel();
                }
            });
        },

        /** 初始化 Beat 内联编辑（P0-3） */
        async _initBeatEditing() {
            if (!this.scriptEditor) return;
            try {
                const { enableBeatEditing } = await import('/js/beat-editors.js');
                enableBeatEditing(this.scriptEditor, this.novelEditor, async (updatedYaml) => {
                    // 保存回调：更新编辑器内容并触发自动保存
                    this.scriptYaml = updatedYaml;
                    const { setContent } = await import('/js/editor.js');
                    setContent(this.scriptEditor, updatedYaml);
                    this.debounceSaveScript();
                    this.showToast('Beat 已更新');
                });

                // 添加滚动联动：点击剧本编辑器时，滚动到对应原文位置
                this._initScrollSync();
            } catch (e) {
                console.error('加载 Beat 编辑器失败:', e);
            }
        },

        /** 初始化滚动联动（P0-2） */
        async _initScrollSync() {
            if (!this.scriptEditor || !this.novelEditor) return;

            const { findSourceLocationAtLine, scrollToSource } = await import('/js/scroll-sync.js');

            // 监听 script-click 事件（由 editor.js 的 mouseEventListener 触发）
            window.addEventListener('script-click', async (e) => {
                const line = e.detail.line;
                const yamlText = await this._getScriptContent();
                const sourceLoc = findSourceLocationAtLine(yamlText, line);

                if (sourceLoc && this.novelEditor) {
                    const novelText = await this._getNovelContent();
                    scrollToSource(this.novelEditor, novelText, sourceLoc);
                }
            });
        },

        /** 获取小说编辑器内容 */
        async _getNovelContent() {
            const { getContent } = await import('/js/editor.js');
            return getContent(this.novelEditor);
        },

        /** 获取剧本编辑器内容 */
        async _getScriptContent() {
            const { getContent } = await import('/js/editor.js');
            return getContent(this.scriptEditor);
        },

        /** 计算字数（中文字符 + 英文单词） */
        countWords(text) {
            if (!text) return 0;
            const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
            const en = (text.match(/[a-zA-Z0-9]+/g) || []).length;
            return cn + en;
        },

        async loadNovel() {
            if (!this.activeProject) return;
            const res = await fetch(`/api/v1/projects/${this.activeProject.id}/novel`);
            const data = await res.json();
            const content = data.data?.content || '';
            this.novelText = content;
            this.novelWordCount = this.countWords(content);
            // 如果编辑器已初始化，同步内容
            if (this.novelEditor) {
                const { setContent } = await import('/js/editor.js');
                setContent(this.novelEditor, content);
            }
        },

        async saveNovel() {
            if (!this.activeProject) return;
            const content = this.novelEditor
                ? (await import('/js/editor.js')).getContent(this.novelEditor)
                : this.novelText;
            await fetch(`/api/v1/projects/${this.activeProject.id}/novel`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });
            this.showToast('小说已保存');
        },

        /** 自动保存防抖（2 秒） */
        debounceSaveNovel() {
            clearTimeout(this._novelSaveTimer);
            this._novelSaveTimer = setTimeout(() => {
                if (this.activeProject) this.saveNovel();
            }, 2000);
        },

        async startConvert() {
            if (!this.activeProject) return;

            // 先从 CM6 读取最新内容
            if (this.novelEditor) {
                const { getContent } = await import('/js/editor.js');
                this.novelText = getContent(this.novelEditor);
            }

            // 校验小说内容
            const text = (this.novelText || '').trim();
            const charCount = text.length;
            const cnCharCount = (text.match(/[\u4e00-\u9fff]/g) || []).length;
            const minChars = 300;

            if (!text) {
                this.validationError = '请先输入或上传小说内容，再开始转换。';
                return;
            }
            if (charCount < minChars && cnCharCount < minChars) {
                this.validationError = `小说内容过短（当前约 ${charCount} 字符），请至少输入 ${minChars} 字后再试。`;
                return;
            }
            this.validationError = '';

            this.converting = true;
            this.progress = 0;
            this.currentStep = '正在启动...';

            const res = await fetch(`/api/v1/convert/${this.activeProject.id}`, {
                method: 'POST',
            });
            const data = await res.json();
            if (data.code !== 0) {
                alert('启动失败：' + data.message);
                this.converting = false;
                return;
            }

            this.taskId = data.data.task_id;
            this.connectSSE(this.taskId);
        },

        connectSSE(taskId) {
            if (this.eventSource) this.eventSource.close();

            const url = `/api/v1/convert/${taskId}/progress`;
            this.eventSource = new EventSource(url);

            this.eventSource.addEventListener('step_progress', (e) => {
                const d = JSON.parse(e.data);
                this.progress = d.percent;
                this.currentStep = d.step;
            });

            this.eventSource.addEventListener('task_complete', () => {
                this.converting = false;
                this.progress = 100;
                this.currentStep = '完成';
                this.eventSource.close();
                this.loadScript();
                this.showToast('转换完成！');
            });

            this.eventSource.addEventListener('task_failed', (e) => {
                const d = JSON.parse(e.data);
                this.converting = false;
                this.currentStep = '失败';
                this.eventSource.close();
                alert('转换失败：' + d.error);
            });

            this.eventSource.onerror = () => {
                setTimeout(() => this.connectSSE(taskId), 1000);
            };
        },

        async loadScript() {
            if (!this.activeProject) return;
            const res = await fetch(`/api/v1/projects/${this.activeProject.id}/script`);
            const data = await res.json();
            const yaml = data.data?.yaml || '';
            this.scriptYaml = yaml;
            // 同步到 CM6 编辑器
            if (this.scriptEditor) {
                const { setContent } = await import('/js/editor.js');
                setContent(this.scriptEditor, yaml);
            }
        },

        async saveScript() {
            if (!this.activeProject) return;
            const yaml = this.scriptEditor
                ? (await import('/js/editor.js')).getContent(this.scriptEditor)
                : this.scriptYaml;
            await fetch(`/api/v1/projects/${this.activeProject.id}/script`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml }),
            });
            this.showToast('剧本已保存');
        },

        /** 自动保存防抖（2 秒） */
        debounceSaveScript() {
            clearTimeout(this._scriptSaveTimer);
            this._scriptSaveTimer = setTimeout(() => {
                if (this.activeProject) this.saveScript();
            }, 2000);
        },

        // ── 导出功能 ─────────────────────

        /** 导出为 .yaml 文件 */
        exportYaml() {
            const content = this.scriptEditor
                ? (async () => { const { getContent } = await import('/js/editor.js'); return getContent(this.scriptEditor); })()
                : this.scriptYaml;
            // 上面是异步的，改为同步获取
            this._doExport(this.scriptYaml, 'yaml', 'application/x-yaml');
        },

        /** 导出为 .txt 文件（YAML → 纯文本） */
        exportTxt() {
            const yaml = this.scriptYaml;
            if (!yaml) { alert('暂无剧本内容可导出'); return; }
            // 简单解析 YAML 剧本为纯文本
            const text = this.yamlToText(yaml);
            this._doExport(text, 'txt', 'text/plain');
        },

        /** 将剧本 YAML 转为纯文本格式 */
        yamlToText(yaml) {
            try {
                // 简单文本化：提取各 beat 的 content
                const lines = yaml.split('\n');
                const result = [];
                let inBeats = false;
                for (const line of lines) {
                    if (line.trim() === 'beats:') { inBeats = true; continue; }
                    if (inBeats && line.includes('content:')) {
                        const match = line.match(/content:\s*(.+)/);
                        if (match) result.push(match[1].trim());
                    }
                    if (inBeats && line.includes('character:')) {
                        const match = line.match(/character:\s*(.+)/);
                        if (match) result.push(`【${match[1].trim()}】`);
                    }
                }
                return result.join('\n');
            } catch {
                return yaml; // 解析失败，导出原始 YAML
            }
        },

        /** 导出 Fountain 格式（需后端 Skill 支持，当前提示） */
        exportFountain() {
            alert('Fountain 导出功能正在开发中，当前暂不可用。\n\n即将到来的版本将支持 .fountain 格式导出。');
        },

        /** 通用文件下载 */
        _doExport(content, ext, mimeType) {
            if (!content) { alert('暂无内容可导出'); return; }
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.activeProject?.name || 'script'}.${ext}`;
            a.click();
            URL.revokeObjectURL(url);
        },

        // ── Skills 管理 ─────────────────────

        /** 加载 Skills 列表（内置 + 用户） */
        async loadSkills() {
            try {
                const res = await fetch('/api/v1/skills');
                const data = await res.json();
                if (data.code === 0) {
                    const allSkills = data.data || [];
                    this.builtinSkills = allSkills.filter(s => !s.is_user);
                    this.userSkills = allSkills.filter(s => s.is_user);
                    this.skills = allSkills;
                }
            } catch (e) {
                console.error('加载 Skills 失败:', e);
            }
        },

        /** 切换 Skill 启用/禁用状态 */
        async toggleSkill(name) {
            try {
                const res = await fetch(`/api/v1/skills/${name}/toggle`, {
                    method: 'POST',
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast(`Skill "${name}" ${data.data.enabled ? '已启用' : '已禁用'}`);
                    await this.loadSkills();
                } else {
                    alert('操作失败: ' + data.message);
                }
            } catch (e) {
                alert('操作失败: ' + e.message);
            }
        },

        /** 运行指定 Skill */
        async runSkill(name) {
            if (!this.activeProject) {
                alert('请先打开一个项目');
                return;
            }

            try {
                const res = await fetch(`/api/v1/skills/${name}/run`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project_id: this.activeProject.id,
                    }),
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast(`Skill "${name}" 运行成功`);
                    // 如果是 exporter 类型，触发下载
                    if (data.data?.download_url) {
                        window.open(data.data.download_url, '_blank');
                    } else if (data.data?.result) {
                        alert(`运行结果:\n\n${JSON.stringify(data.data.result, null, 2)}`);
                    }
                } else {
                    alert('运行失败: ' + data.message);
                }
            } catch (e) {
                alert('运行失败: ' + e.message);
            }
        },

        /** 删除用户自定义 Skill */
        async deleteSkill(name) {
            if (!confirm(`确认删除 Skill "${name}"？删除后不可恢复。`)) return;
            
            try {
                const res = await fetch(`/api/v1/skills/${name}`, {
                    method: 'DELETE',
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast(`Skill "${name}" 已删除`);
                    await this.loadSkills();
                } else {
                    alert('删除失败: ' + data.message);
                }
            } catch (e) {
                alert('删除失败: ' + e.message);
            }
        },

        /** 创建新 Skill（生成模板） */
        createSkill() {
            const name = prompt('请输入 Skill 名称（小写英文字母+连字符）:');
            if (!name) return;
            
            const type = prompt('请输入 Skill 类型（pre_processor/post_processor/exporter/analyzer）:', 'post_processor');
            if (!type) return;

            const description = prompt('请输入 Skill 描述:', '我的自定义 Skill');
            if (!description) return;

            // 调用后端 API 创建 Skill
            fetch('/api/v1/skills', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    type,
                    description,
                    author: '用户',
                }),
            })
            .then(res => res.json())
            .then(data => {
                if (data.code === 0) {
                    this.showToast(`Skill "${name}" 创建成功！`);
                    this.loadSkills();
                } else {
                    alert('创建失败: ' + data.message);
                }
            })
            .catch(e => {
                alert('创建失败: ' + e.message);
            });
        },

        /** 安装 Skill（从本地路径） */
        installSkill() {
            const path = prompt('请输入 Skill 目录路径（含 skill.json 和 main.py）:');
            if (!path) return;

            fetch('/api/v1/skills/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path }),
            })
            .then(res => res.json())
            .then(data => {
                if (data.code === 0) {
                    this.showToast(`Skill 安装成功！`);
                    this.loadSkills();
                } else {
                    alert('安装失败: ' + data.message);
                }
            })
            .catch(e => {
                alert('安装失败: ' + e.message);
            });
        },

        // ── 配置快照功能 ─────────────────────
        async viewConfigSnapshot() {
            if (!this.activeProject) {
                alert('请先打开一个项目');
                return;
            }

            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/config-snapshot`);
                const data = await res.json();
                
                if (data.code === 0) {
                    const config = data.data;
                    let message = '📸 项目配置快照\n\n';
                    message += `提供商: ${config.llm_provider || '未设置'}\n`;
                    message += `模型: ${config.llm_model_name || '未设置'}\n`;
                    message += `温度: ${config.llm_temperature || '未设置'}\n`;
                    message += `Top P: ${config.llm_top_p || '未设置'}\n`;
                    message += `最大 Token: ${config.llm_max_tokens || '未设置'}\n`;
                    
                    if (config.note) {
                        message += `\n📝 ${config.note}\n`;
                    }
                    if (config.saved_at) {
                        message += `\n🕒 保存时间: ${config.saved_at}\n`;
                    }
                    
                    alert(message);
                } else {
                    alert('获取配置快照失败: ' + data.message);
                }
            } catch (e) {
                alert('获取配置快照失败: ' + e.message);
            }
        },

        // ── 版本历史功能 ─────────────────────
        async toggleVersionPanel() {
            this.showVersionPanel = !this.showVersionPanel;
            if (this.showVersionPanel && this.activeProject) {
                await this.loadVersions();
            }
        },

        async loadVersions() {
            if (!this.activeProject) return;
            
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/versions`);
                const data = await res.json();
                if (data.code === 0) {
                    this.versions = data.data || [];
                }
            } catch (e) {
                console.error('加载版本历史失败:', e);
            }
        },

        async viewVersion(versionId) {
            if (!this.activeProject) return;
            
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/versions/${versionId}`);
                const data = await res.json();
                if (data.code === 0) {
                    this.currentVersion = data.data;
                    // 显示版本预览
                    this.showToast(`查看版本: ${versionId}`);
                }
            } catch (e) {
                console.error('加载版本详情失败:', e);
                alert('加载版本详情失败: ' + e.message);
            }
        },

        async rollbackToVersion(versionId) {
            if (!this.activeProject) return;
            
            if (!confirm(`确认回滚到版本 ${versionId}？当前未保存的修改将会丢失。`)) {
                return;
            }
            
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/versions/${versionId}/rollback`, {
                    method: 'POST'
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast(`已回滚到版本 ${versionId}`);
                    // 重新加载剧本
                    await this.loadScript();
                    // 重新加载版本列表
                    await this.loadVersions();
                } else {
                    alert('回滚失败: ' + data.message);
                }
            } catch (e) {
                alert('回滚失败: ' + e.message);
            }
        },

        // ── 工具方法 ─────────────────────
        showToast(message) {
            const toast = document.createElement('div');
            toast.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-opacity';
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 2000);
        },
    };
}
