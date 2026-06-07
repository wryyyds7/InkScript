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
            max_tokens: 8192,
            frequency_penalty: 0.0,
            presence_penalty: 0.0,
            timeout: 60,
            max_retries: 3,
            request_interval: 0.5,
        },

        // CodeMirror 6 实例（由 initEditors() 初始化）
        novelEditor: null,          // EditorView 实例（小说）
        scriptEditor: null,        // EditorView 实例（剧本）

        // Loading 状态
        loadingProjects: false,    // 项目列表加载中
        loadingNovel: false,       // 小说内容加载中
        loadingScript: false,      // 剧本内容加载中
        savingNovel: false,        // 保存小说中
        savingScript: false,       // 保存剧本中

        // 自动保存计时器
        _novelSaveTimer: null,
        _scriptSaveTimer: null,

        // 快捷键帮助 Modal 显示状态
        showShortcutsModal: false,

        // 通用输入对话框状态（替换 prompt()）
        showInputModal: false,
        inputModalTitle: '',
        inputModalMessage: '',
        inputModalPlaceholder: '',
        inputModalValue: '',
        inputModalResolve: null,
        inputModalReject: null,

        // 通用确认对话框状态（替换 confirm()）
        showConfirmModal: false,
        confirmModalTitle: '',
        confirmModalMessage: '',
        confirmModalResolve: null,

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

        // 版本历史（快照）
        showVersionPanel: false,  // 是否显示版本历史面板
        versions: [],            // 版本列表
        currentVersion: null,    // 当前查看的版本详情

        // 操作日志（逐句修改历史）
        showOperationLog: false,  // 是否显示操作日志面板
        operations: [],           // 操作日志列表
        currentOperation: null,   // 当前查看的操作详情
        operationFilter: 'all',  // 操作过滤器：all|create_beat|update_beat|delete_beat|update_novel

        // 情绪曲线可视化
        showEmotionCurve: false,  // 是否显示情绪曲线面板
        emotionCurveGranularity: 'beat',  // 粒度：beat|scene
        selectedEmotionPoint: null,  // 选中的情绪点
        emotionCurveChart: null,  // Chart.js 实例

        // 角色情绪分布雷达图
        showCharacterPanel: false,  // 是否显示角色面板
        characters: [],  // 角色列表
        selectedCharacter: null,  // 当前选中的角色
        characterRadarChart: null,  // 雷达图 Chart.js 实例

        // ── Beat 可视化编辑（节拍板）────────
        viewMode: 'yaml',        // 视图模式：'yaml' | 'beat-board'
        beatBoardScenes: [],    // 节拍板数据（按场景分组）
        beatBoardBeats: [],     // 节拍板所有 Beat 列表
        beatBoardVisible: false, // 节拍板是否可见

        // 回收站
        showTrash: false,        // 是否显示回收站
        trashItems: [],          // 回收站项目列表

        // 文件管理
        showFileManager: false,  // 是否显示文件管理面板
        projectFiles: [],        // 项目文件列表
        downloadingFile: false,  // 是否正在下载文件

        // 编辑器分栏拖拽
        leftPanelWidth: 50,        // 左侧面板宽度百分比（可拖拽调整）
        _dragStartX: 0,           // 拖拽起始位置
        _dragStartWidth: 0,       // 拖拽起始宽度
        _isDragging: false,        // 是否正在拖拽

        // 使用指南折叠
        showGuide: true,           // 是否显示使用指南

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
            this._loadGuideState();  // 初始化使用指南状态
            this._initKeyboardShortcuts();
            this._initOperationLogListener();  // 初始化操作日志监听
            this._initAutoSave();  // 初始化自动保存
        },

        // ── 自动保存功能 ────────────────────
        _initAutoSave() {
            // 监听页面卸载事件，自动保存
            window.addEventListener('beforeunload', (e) => {
                if (this.activeProject) {
                    // 同步保存（最佳实践是在 beforeunload 中使用同步请求）
                    // 但由于我们的 API 是异步的，这里使用一个标志来提示用户
                    const novelContent = this.novelEditor ? getContent(this.novelEditor) : this.novelText;
                    const scriptContent = this.scriptEditor ? getContent(this.scriptEditor) : this.scriptYaml;
                    
                    // 如果内容有变化，提示用户
                    if (novelContent !== this.novelText || scriptContent !== this.scriptYaml) {
                        // 尝试异步保存（大多数现代浏览器会等待一小段时间）
                        this.saveNovel();
                        this.saveScript();
                        
                        // 标准方式：提示用户
                        e.preventDefault();
                        e.returnValue = '检测到未保存的更改，确定要离开吗？';
                    }
                }
            });

            // 监听视图切换，自动保存
            this.$watch('view', (newView, oldView) => {
                if (oldView === 'editor' && this.activeProject) {
                    // 离开编辑器时自动保存
                    this.saveNovel();
                    this.saveScript();
                }
            });
        },

        // ── 通用 API 调用包装器（带错误处理）────────────────────
        /**
         * 通用的 fetch 包装器，自动处理错误和用户反馈
         * @param {string} url - API 地址
         * @param {object} options - fetch 选项
         * @param {string} errorMessage - 自定义错误信息
         * @returns {Promise<object>} - 解析后的响应数据
         */
        async apiCall(url, options = {}, errorMessage = '操作失败') {
            try {
                const res = await fetch(url, options);
                
                // 检查 HTTP 状态
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                
                const data = await res.json();
                
                // 检查业务状态码
                if (data.code !== 0) {
                    throw new Error(data.message || errorMessage);
                }
                
                return data;
            } catch (error) {
                // 显示错误提示
                const errorMsg = error.message || errorMessage;
                this.showToast(`❌ ${errorMsg}`, 'error');
                console.error('[API Call Error]', { url, options, error });
                
                // 重新抛出错误，让调用者可以处理
                throw error;
            }
        },

        // ── 通用对话框方法（替换 prompt()/confirm()）────────────────────
        
        /**
         * 显示输入对话框（替换 prompt()）
         * @param {string} title - 对话框标题
         * @param {string} message - 提示信息
         * @param {string} placeholder - 输入框占位符
         * @param {string} defaultValue - 默认值
         * @returns {Promise<string|null>} - 用户输入的值，或 null（取消）
         */
        showInputDialog(title, message = '', placeholder = '', defaultValue = '') {
            return new Promise((resolve) => {
                this.inputModalTitle = title;
                this.inputModalMessage = message;
                this.inputModalPlaceholder = placeholder;
                this.inputModalValue = defaultValue;
                this.inputModalResolve = resolve;
                this.showInputModal = true;
                
                // 自动聚焦到输入框
                this.$nextTick(() => {
                    if (this.$refs.inputModal) {
                        this.$refs.inputModal.focus();
                    }
                });
            });
        },

        confirmInputModal() {
            if (this.inputModalResolve) {
                this.inputModalResolve(this.inputModalValue);
                this.inputModalResolve = null;
            }
            this.showInputModal = false;
        },

        cancelInputModal() {
            if (this.inputModalResolve) {
                this.inputModalResolve(null);
                this.inputModalResolve = null;
            }
            this.showInputModal = false;
        },

        /**
         * 显示确认对话框（替换 confirm()）
         * @param {string} title - 对话框标题
         * @param {string} message - 确认信息
         * @returns {Promise<boolean>} - 用户是否确认
         */
        showConfirmDialog(title, message = '确定要执行此操作吗？') {
            return new Promise((resolve) => {
                this.confirmModalTitle = title;
                this.confirmModalMessage = message;
                this.confirmModalResolve = resolve;
                this.showConfirmModal = true;
            });
        },

        confirmConfirmModal() {
            if (this.confirmModalResolve) {
                this.confirmModalResolve(true);
                this.confirmModalResolve = null;
            }
            this.showConfirmModal = false;
        },

        cancelConfirmModal() {
            if (this.confirmModalResolve) {
                this.confirmModalResolve(false);
                this.confirmModalResolve = null;
            }
            this.showConfirmModal = false;
        },

        // ── 操作日志事件监听 ────────────────────
        _initOperationLogListener() {
            // 监听 Beat 操作事件
            window.addEventListener('beat-operation', (event) => {
                if (!this.activeProject) return;

                const { action, beatId, field, oldValue, newValue, sceneId } = event.detail;

                // 调用 logOperation 方法记录操作
                this.logOperation(action, {
                    beatId: beatId,
                    field: field,
                    oldValue: oldValue,
                    newValue: newValue,
                    sceneId: sceneId
                });
            });
        },

        // ── 快捷键系统 ────────────────────
        _initKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                const isCtrlOrCmd = e.ctrlKey || e.metaKey;
                
                // Ctrl/Cmd + S：保存
                if (isCtrlOrCmd && e.key === 's') {
                    e.preventDefault();
                    if (this.activeProject) {
                        // 手动保存时显示提示
                        this.saveNovel(true);
                        this.saveScript(true);
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

        /** 切换 AI 提供商时，自动填入该提供商的默认 API Base URL */
        onProviderChange() {
            const provider = this.config.provider;
            // custom 类型不自动填 URL，让用户自己填
            if (provider === 'custom') return;
            const defaultUrl = this.providers[provider]?.url || '';
            if (defaultUrl) {
                this.config.base_url = defaultUrl;
            }
        },

        getModelPlaceholder() {
            return this.providers[this.config.provider]?.modelPlaceholder || '';
        },

        getModelHint() {
            return this.providers[this.config.provider]?.modelHint || '';
        },

        // ── 编辑器辅助功能 ─────────────────
        
        /** 切换使用指南显示/隐藏 */
        toggleGuide() {
            this.showGuide = !this.showGuide;
            // 保存状态到 localStorage
            try {
                localStorage.setItem('inkscript_show_guide', this.showGuide ? '1' : '0');
            } catch (e) {
                // localStorage 不可用时忽略
            }
        },
        
        /** 初始化时读取使用指南状态 */
        _loadGuideState() {
            try {
                const saved = localStorage.getItem('inkscript_show_guide');
                if (saved !== null) {
                    this.showGuide = saved === '1';
                }
            } catch (e) {
                // localStorage 不可用时忽略
            }
        },

        // ── 项目管理 ─────────────────────
        async loadProjects() {
            this.loadingProjects = true;
            
            const params = new URLSearchParams();
            if (this.projectSearch) params.append('search', this.projectSearch);
            if (this.projectSortBy) params.append('sort_by', this.projectSortBy);
            if (this.projectSortOrder) params.append('order', this.projectSortOrder);
            
            const url = `/api/v1/projects${params.toString() ? '?' + params.toString() : ''}`;
            
            try {
                const data = await this.apiCall(url, {}, '加载项目列表失败');
                this.projects = data.data;
            } catch (error) {
                // apiCall 已经显示了错误提示，这里只需要处理特定的回滚逻辑（如果有）
                this.projects = [];
            } finally {
                this.loadingProjects = false;
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
            // 使用自定义输入对话框替换 prompt()
            const name = await this.showInputDialog(
                '创建项目',
                '请输入项目名称：',
                '项目名称',
                ''
            );
            
            if (!name || !name.trim()) return;
            
            try {
                const data = await this.apiCall('/api/v1/projects', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name.trim() }),
                }, '创建项目失败');
                
                await this.loadProjects();
                this.view = 'projects';
                this.showToast('✅ 项目创建成功');
            } catch (error) {
                // 错误已经在 apiCall() 中处理了
            }
        },

        async openProject(id) {
            try {
                const data = await this.apiCall(`/api/v1/projects/${id}`, {}, '打开项目失败');
                
                this.previousView = this.view;
                this.activeProject = data.data;
                this.view = 'editor';
                
                // 等待 DOM 更新后再初始化编辑器
                await this.$nextTick();
                
                // 分步加载，每一步都单独处理错误
                try {
                    await this.loadNovel();
                } catch (e) {
                    console.error('加载小说失败:', e);
                    this.showToast('⚠️ 加载小说失败，将使用空内容');
                }
                
                try {
                    await this.loadScript();
                } catch (e) {
                    console.error('加载剧本失败:', e);
                    // 剧本可能不存在，这是正常的
                }
                
                // 加载编辑器元数据（恢复滚动位置、面板状态等）
                try {
                    await this.loadEditMeta();
                } catch (e) {
                    console.error('加载编辑器元数据失败:', e);
                }
                
                // 初始化 CodeMirror 编辑器
                await this.initEditors();
                
                this.showToast(`已打开项目：${this.activeProject.name}`);
            } catch (error) {
                // ⚠️ 不再强制回退到项目列表，而是显示错误提示
                console.error('打开项目失败:', error);
                this.showToast(`⚠️ 打开项目失败：${error.message || '未知错误'}`);
                // 不再设置 this.view = 'projects'，让用户留在当前页面查看错误
            }
        },

        async deleteProject(id) {
            // 使用自定义确认对话框替换 confirm()
            const confirmed = await this.showConfirmDialog(
                '删除项目',
                '确认删除该项目？项目将进入回收站。'
            );
            
            if (!confirmed) return;
            
            try {
                await this.apiCall(`/api/v1/projects/${id}`, { 
                    method: 'DELETE' 
                }, '删除项目失败');
                
                await this.loadProjects();
                this.showToast('✅ 项目已移动到回收站');
            } catch (error) {
                // 错误已经在 apiCall() 中处理了
            }
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
            const confirmed = await this.showConfirmDialog(
                '恢复项目',
                '确认恢复该项目？'
            );
            
            if (!confirmed) return;
            
            try {
                await this.apiCall(`/api/v1/trash/${projectId}/restore`, {
                    method: 'POST'
                }, '恢复项目失败');
                
                this.showToast('✅ 项目已恢复');
                await this.loadTrash();
                await this.loadProjects();
            } catch (error) {
                // 错误已经在 apiCall() 中处理了
            }
        },

        async permanentDelete(projectId) {
            const confirmed = await this.showConfirmDialog(
                '永久删除',
                '确认永久删除该项目？删除后不可恢复。'
            );
            
            if (!confirmed) return;
            
            try {
                await this.apiCall(`/api/v1/trash/${projectId}`, {
                    method: 'DELETE'
                }, '永久删除项目失败');
                
                this.showToast('✅ 项目已永久删除');
                await this.loadTrash();
            } catch (error) {
                // 错误已经在 apiCall() 中处理了
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
                    this.showToast('设置已保存！');
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

        // ── 分栏折叠 ────────────────────

        /** 左栏是否全屏 */
        get isLeftPanelFullscreen() {
            return this.leftPanelWidth >= 99;
        },

        /** 右栏是否全屏 */
        get isRightPanelFullscreen() {
            return this.leftPanelWidth <= 1;
        },

        /** 切换左栏全屏（折叠右栏） */
        toggleLeftPanel() {
            if (this.isLeftPanelFullscreen) {
                // 恢复之前的比例（默认 50:50）
                this.leftPanelWidth = 50;
            } else {
                // 左栏全屏
                this.leftPanelWidth = 99;
            }
        },

        /** 切换右栏全屏（折叠左栏） */
        toggleRightPanel() {
            if (this.isRightPanelFullscreen) {
                // 恢复之前的比例（默认 50:50）
                this.leftPanelWidth = 50;
            } else {
                // 右栏全屏
                this.leftPanelWidth = 1;
            }
        },

        // ── 编辑器 ─────────────────────

        /** 初始化 CodeMirror 6 编辑器（editor 视图挂载后调用） */
        async initEditors() {
            // 动态导入 editor.js（因为是 type="importmap" 模块）
            const { initNovelEditor, initScriptEditor, getContent, setContent } = await import('/js/editor.js');

            // 等待编辑器容器出现（Alpine 可能需要多个 tick 才能完全渲染）
            let novelContainer = document.getElementById('novel-editor-container');
            let scriptContainer = document.getElementById('script-editor-container');
            
            // 重试最多 10 次，每次等待一个 tick
            let retries = 0;
            while ((!novelContainer || !scriptContainer) && retries < 10) {
                await new Promise(resolve => setTimeout(resolve, 50)); // 等待 50ms
                await this.$nextTick();
                novelContainer = document.getElementById('novel-editor-container');
                scriptContainer = document.getElementById('script-editor-container');
                retries++;
            }
            
            if (!novelContainer || !scriptContainer) {
                console.error('编辑器容器未找到，无法初始化编辑器');
                this.showToast('⚠️ 编辑器初始化失败，请重试');
                return;
            }

            // 如果已初始化，先销毁
            if (this.novelEditor) this.novelEditor.destroy();
            if (this.scriptEditor) this.scriptEditor.destroy();

            // 初始化小说编辑器（可编辑）
            this.novelEditor = initNovelEditor(novelContainer, this.novelText || '', { readOnly: false });

            // 初始化剧本编辑器（可编辑）
            this.scriptEditor = initScriptEditor(scriptContainer, this.scriptYaml || '', { readOnly: false });

            // 启用小说编辑器的右键菜单（预处理功能 P1-7）
            // 添加错误处理，避免因为右键菜单初始化失败导致整个编辑器无法使用
            try {
                this._initNovelContextMenu();
            } catch (error) {
                console.error('右键菜单初始化失败:', error);
            }

            // 启用 Beat 内联编辑（P0-3）
            // 添加错误处理，避免因为 Beat 编辑功能失败导致整个编辑器无法使用
            try {
                this._initBeatEditing();
            } catch (error) {
                console.error('Beat 编辑功能初始化失败:', error);
            }

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
                onDelete: async (view, from, to) => {
                    // 数据校验：确保有选中内容
                    if (from >= to) {
                        this.showToast('请先选中要删除的内容');
                        return;
                    }
                    
                    // 提交逻辑：先创建版本快照
                    await this._createNovelSnapshot('删除操作前快照');
                    
                    // 删除选中内容（先确认）
                    if (confirm('确认删除选中内容？此操作可以回滚。')) {
                        view.dispatch({
                            changes: { from, to, insert: '' }
                        });
                        this.showToast('已删除选中内容');
                        this.debounceSaveNovel();
                    }
                },
                onMerge: async (view) => {
                    // 数据校验：确保有选中内容
                    const { state } = view;
                    const selection = state.selection.main;
                    if (selection.empty) {
                        this.showToast('请先选中要合并的段落');
                        return;
                    }
                    
                    // 提交逻辑：先创建版本快照
                    await this._createNovelSnapshot('合并段落操作前快照');
                    
                    // 合并段落
                    mergeParagraphs(view);
                    this.showToast('已合并段落');
                    this.debounceSaveNovel();
                },
                onAddMark: async (view, markType, noteText) => {
                    // 数据校验：确保有选中内容
                    const { state } = view;
                    const selection = state.selection.main;
                    if (selection.empty && markType !== 'note') {
                        this.showToast('请先选中要标记的位置');
                        return;
                    }
                    
                    // 提交逻辑：先创建版本快照
                    await this._createNovelSnapshot(`添加标记 ${markType} 前快照`);
                    
                    // 添加标记
                    insertMark(view, markType, noteText);
                    const markText = markType === 'note' ? `note: ${noteText}` : markType;
                    this.showToast(`已添加标记: ${markText}`);
                    this.debounceSaveNovel();
                }
            });
        },
        
        /** 创建小说原文版本快照（提交逻辑） */
        async _createNovelSnapshot(description) {
            if (!this.activeProject) return;
            
            try {
                const response = await fetch(`/api/v1/projects/${this.activeProject.id}/novel-snapshot`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description })
                });
                
                const result = await response.json();
                if (result.code === 0) {
                    console.log('版本快照创建成功:', result.data);
                } else {
                    console.error('版本快照创建失败:', result.message);
                }
            } catch (error) {
                console.error('版本快照创建失败:', error);
            }
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

        // ── 撤销/重做 ─────────────────────

        /** 获取当前获得焦点的编辑器 */
        _getFocusedEditor() {
            if (this.scriptEditor && this.scriptEditor.hasFocus) return 'script';
            if (this.novelEditor && this.novelEditor.hasFocus) return 'novel';
            return 'script'; // 默认操作剧本编辑器
        },

        /** 撤销 */
        async undo() {
            const editorType = this._getFocusedEditor();
            const editor = editorType === 'novel' ? this.novelEditor : this.scriptEditor;
            if (!editor) return;
            try {
                const { undo } = await import('@codemirror/commands');
                undo(editor);
                this.showToast('已撤销');
            } catch (e) {
                console.error('撤销失败:', e);
            }
        },

        /** 重做 */
        async redo() {
            const editorType = this._getFocusedEditor();
            const editor = editorType === 'novel' ? this.novelEditor : this.scriptEditor;
            if (!editor) return;
            try {
                const { redo } = await import('@codemirror/commands');
                redo(editor);
                this.showToast('已重做');
            } catch (e) {
                console.error('重做失败:', e);
            }
        },

        /** 检查当前编辑器是否可以撤销 */
        get canUndo() {
            // Alpine.js 不支持复杂的 getter，用方法代替
            return false;
        },

        /** 检查当前编辑器是否可以重做 */
        get canRedo() {
            return false;
        },

        async loadNovel() {
            if (!this.activeProject) return;
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/novel`);
                
                // 检查响应状态
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                
                const data = await res.json();
                const content = data.data?.content || '';
                this.novelText = content;
                this.novelWordCount = this.countWords(content);
                // 如果编辑器已初始化，同步内容
                if (this.novelEditor) {
                    const { setContent } = await import('/js/editor.js');
                    setContent(this.novelEditor, content);
                }
            } catch (error) {
                console.error('加载小说失败:', error);
                // 不抛出错误，使用空内容
                this.novelText = '';
                this.novelWordCount = 0;
                this.showToast('⚠️ 加载小说失败，将使用空内容');
            }
        },

        async saveNovel(showNotice = false) {
            if (!this.activeProject) return;
            const content = this.novelEditor
                ? (await import('/js/editor.js')).getContent(this.novelEditor)
                : this.novelText;
            await fetch(`/api/v1/projects/${this.activeProject.id}/novel`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });
            // 只在手动保存时显示提示
            if (showNotice) {
                this.showToast('小说已保存');
            }
            // 保存编辑器元数据
            await this.saveEditMeta();
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

            const url = `/api/v1/convert/${taskId}/sse`;
            this.eventSource = new EventSource(url);

            this.eventSource.addEventListener('step_start', (e) => {
                const d = JSON.parse(e.data);
                this.currentStep = d.step;
            });

            this.eventSource.addEventListener('step_complete', (e) => {
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

            this.eventSource.addEventListener('warning', (e) => {
                const d = JSON.parse(e.data);
                this.showToast(d.message, 'warning');
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
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/script`);
                
                // 检查响应状态
                if (!res.ok) {
                    if (res.status === 404) {
                        // 剧本不存在，这是正常情况（新项目还没有剧本）
                        console.log('剧本不存在，将使用空内容');
                        this.scriptYaml = '';
                        return;
                    }
                    throw new Error(`HTTP ${res.status}`);
                }
                
                const data = await res.json();
                const yaml = data.data?.yaml || '';
                this.scriptYaml = yaml;
                // 同步到 CM6 编辑器
                if (this.scriptEditor) {
                    const { setContent } = await import('/js/editor.js');
                    setContent(this.scriptEditor, yaml);
                }
            } catch (error) {
                console.error('加载剧本失败:', error);
                // 不抛出错误，让调用者决定如何处理
                this.scriptYaml = '';
            }
        },

        async saveScript(showNotice = false) {
            if (!this.activeProject) return;
            const yaml = this.scriptEditor
                ? (await import('/js/editor.js')).getContent(this.scriptEditor)
                : this.scriptYaml;
            await fetch(`/api/v1/projects/${this.activeProject.id}/script`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml }),
            });
            // 只在手动保存时显示提示
            if (showNotice) {
                this.showToast('剧本已保存');
            }
            // 保存编辑器元数据
            await this.saveEditMeta();
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
            if (!this.activeProject) {
                this.showToast('请先打开一个项目');
                return;
            }
            
            // 数据校验：确保有剧本数据
            const scriptYaml = this.scriptEditor ? this.scriptEditor.state.doc.toString() : '';
            if (!scriptYaml || scriptYaml.trim() === '') {
                this.showToast('当前没有剧本数据，无法导出');
                return;
            }
            
            // 状态管理：显示导出进度
            this.converting = true;
            this.currentStep = '正在导出 Fountain...';
            this.progress = 0;
            
            // 提交逻辑：调用 fountain-export Skill
            this._submitFountainExport(scriptYaml);
        },
        
        async _submitFountainExport(scriptYaml) {
            try {
                // 数据提交：调用后端 Skill
                const response = await fetch('/api/v1/skills/fountain-export/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        data: {
                            yaml_content: scriptYaml,
                            project_name: this.activeProject.name || 'script'
                        },
                        config: {}
                    })
                });
                
                const result = await response.json();
                
                if (result.code === 0 && result.data && result.data.success) {
                    // 处理成功结果：下载 .fountain 文件
                    const fountainContent = result.data.data.content;
                    const filename = result.data.data.filename || 'script.fountain';
                    
                    this._downloadFile(fountainContent, filename, 'text/plain');
                    this.showToast('Fountain 导出成功');
                } else {
                    // 处理失败结果
                    throw new Error(result.message || result.data?.error || '导出失败');
                }
            } catch (error) {
                console.error('Fountain 导出失败:', error);
                alert('Fountain 导出失败: ' + error.message);
            } finally {
                // 状态重置
                this.converting = false;
                this.currentStep = '';
                this.progress = 0;
            }
        },
        
        _downloadFile(content, filename, mimeType) {
            // 创建 Blob 并触发下载
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
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

        /** 安装 Skill（从本地路径） */
        async installSkill() {
            const path = prompt('请输入 Skill 目录路径（含 metadata.json 或 SKILL.md）:');
            if (!path) return;

            try {
                const res = await fetch('/api/v1/skills/install', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path }),
                });
                const data = await res.json();
                if (data.code === 0) {
                    this.showToast(`Skill 安装成功！`);
                    await this.loadSkills();
                } else {
                    alert('安装失败: ' + data.message);
                }
            } catch (e) {
                alert('安装失败: ' + e.message);
            }
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

        // ── 操作日志功能（逐句修改历史）─────────────────────
        async toggleOperationLog() {
            this.showOperationLog = !this.showOperationLog;
            if (this.showOperationLog && this.activeProject) {
                await this.loadOperations();
            }
        },

        async loadOperations() {
            if (!this.activeProject) return;
            
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/operations`);
                const data = await res.json();
                if (data.code === 0) {
                    this.operations = data.data || [];
                }
            } catch (e) {
                console.error('加载操作日志失败:', e);
            }
        },

        /** 根据过滤器筛选操作日志 */
        get filteredOperations() {
            if (this.operationFilter === 'all') {
                return this.operations;
            }
            return this.operations.filter(op => op.action === this.operationFilter);
        },

        /** 格式化操作类型 */
        formatAction(action) {
            const actionMap = {
                'create_beat': '创建 Beat',
                'update_beat': '更新 Beat',
                'delete_beat': '删除 Beat',
                'update_novel': '更新小说'
            };
            return actionMap[action] || action;
        },

        /** 格式化时间戳 */
        formatTimestamp(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },

        /** 查看操作详情 */
        viewOperation(operation) {
            this.currentOperation = operation;
        },

        /** 关闭操作详情 */
        closeOperationDetail() {
            this.currentOperation = null;
        },

        /** 回滚到某次操作 */
        async rollbackToOperation(operationIndex) {
            if (!this.activeProject) return;
            
            if (!confirm(`确认回滚到该操作？之后的操作将被撤销，此操作不可撤销。`)) {
                return;
            }
            
            try {
                // 获取该操作之前的所有操作
                const operationsToKeep = this.operations.slice(0, operationIndex + 1);
                
                // 清空操作日志
                await fetch(`/api/v1/projects/${this.activeProject.id}/operations`, {
                    method: 'DELETE'
                });
                
                // 重新应用操作（这里需要后端支持，暂时先清空）
                this.showToast('回滚功能需要后端支持，正在开发中');
                
                // 重新加载操作日志
                await this.loadOperations();
            } catch (e) {
                alert('回滚失败: ' + e.message);
            }
        },

        /** 记录操作日志 */
        async logOperation(action, details) {
            if (!this.activeProject) return;
            
            const operation = {
                action: action,
                beat_id: details.beatId || null,
                field: details.field || null,
                old_value: details.oldValue || null,
                new_value: details.newValue || null,
                scene_id: details.sceneId || null,
                timestamp: new Date().toISOString()
            };
            
            try {
                await fetch(`/api/v1/projects/${this.activeProject.id}/operations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(operation)
                });
            } catch (e) {
                console.error('记录操作日志失败:', e);
            }
        },

        // ── 情绪曲线可视化 ────────────────────
        async toggleEmotionCurve() {
            this.showEmotionCurve = !this.showEmotionCurve;
            if (this.showEmotionCurve && this.activeProject) {
                // 延迟初始化图表，等待 DOM 更新
                setTimeout(() => {
                    if (window.initEmotionCurveChart) {
                        window.initEmotionCurveChart(this);
                    }
                }, 100);
            }
        },

        /** 滚动到选中的情绪点对应的 Beat */
        scrollToEmotionPoint() {
            if (!this.selectedEmotionPoint || !this.scriptEditor) return;

            // 获取剧本 YAML 文本
            const yamlText = getContent(this.scriptEditor);
            const beats = parseBeatsFromYaml(yamlText);

            if (this.selectedEmotionPoint.type === 'beat') {
                // 定位到对应的 Beat
                const beatIdx = this.selectedEmotionPoint.index;
                if (beatIdx >= 0 && beatIdx < beats.length) {
                    const beat = beats[beatIdx];
                    // 滚动到对应行
                    this.scriptEditor.dispatch({
                        selection: { anchor: this.scriptEditor.state.doc.line(beat.lineStart + 1).from },
                        scrollIntoView: true
                    });
                    this.showToast(`已定位到 Beat #${beatIdx + 1}`);
                }
            } else if (this.selectedEmotionPoint.type === 'scene') {
                // 定位到场景的第一个 Beat
                const sceneId = this.selectedEmotionPoint.sceneId;
                const firstBeat = beats.find(b => b.scene_id === sceneId);
                if (firstBeat) {
                    this.scriptEditor.dispatch({
                        selection: { anchor: this.scriptEditor.state.doc.line(firstBeat.lineStart + 1).from },
                        scrollIntoView: true
                    });
                    this.showToast(`已定位到场景 ${sceneId}`);
                }
            }

            // 关闭面板
            this.showEmotionCurve = false;
        },

        // ── 角色情绪分布雷达图 ────────────────────
        
        /** 切换角色面板显示/隐藏 */
        async toggleCharacterPanel() {
            this.showCharacterPanel = !this.showCharacterPanel;
            if (this.showCharacterPanel && this.activeProject) {
                await this.loadCharacters();
                // 延迟初始化雷达图，等待 DOM 更新
                setTimeout(() => {
                    if (this.selectedCharacter) {
                        this.initCharacterRadarChart();
                    }
                }, 100);
            }
        },

        /** 加载角色列表 */
        async loadCharacters() {
            if (!this.activeProject) return;
            
            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/characters`);
                const data = await res.json();
                if (data.code === 0) {
                    this.characters = data.data || [];
                    // 如果有角色且未选中，默认选中第一个
                    if (this.characters.length > 0 && !this.selectedCharacter) {
                        this.selectCharacter(this.characters[0]);
                    }
                }
            } catch (e) {
                console.error('加载角色列表失败:', e);
                // 如果后端API不存在，从剧本YAML中解析角色
                this.parseCharactersFromScript();
            }
        },

        /** 从剧本YAML中解析角色列表 */
        parseCharactersFromScript() {
            if (!this.scriptYaml) return;
            
            try {
                // 简单解析：提取所有 dialogue beat 的 character 字段
                const lines = this.scriptYaml.split('\n');
                const characterMap = {};
                
                let currentCharacter = null;
                for (const line of lines) {
                    const charMatch = line.match(/^\s+character:\s*(.+)$/);
                    if (charMatch) {
                        currentCharacter = charMatch[1].trim();
                        if (!characterMap[currentCharacter]) {
                            characterMap[currentCharacter] = {
                                name: currentCharacter,
                                dialogue_count: 0,
                                emotion_distribution: {
                                    happy: 0.2,
                                    sad: 0.1,
                                    angry: 0.1,
                                    calm: 0.3,
                                    excited: 0.2,
                                    fear: 0.1
                                }
                            };
                        }
                    }
                    
                    const typeMatch = line.match(/^\s+type:\s*dialogue$/);
                    if (typeMatch && currentCharacter) {
                        characterMap[currentCharacter].dialogue_count++;
                    }
                }
                
                this.characters = Object.values(characterMap);
                
                // 如果有角色且未选中，默认选中第一个
                if (this.characters.length > 0 && !this.selectedCharacter) {
                    this.selectCharacter(this.characters[0]);
                }
            } catch (e) {
                console.error('解析角色列表失败:', e);
            }
        },

        // ── Beat 可视化编辑（节拍板）─────────

        /** 切换视图模式（YAML / 节拍板） */
        toggleViewMode() {
            this.viewMode = this.viewMode === 'yaml' ? 'beat-board' : 'yaml';
            
            if (this.viewMode === 'beat-board' && this.activeProject) {
                // 切换到节拍板视图，初始化
                this.initBeatBoard();
            } else {
                // 切换回 YAML 视图
                this.beatBoardVisible = false;
            }
        },

        /** 初始化节拍板 */
        async initBeatBoard() {
            if (!this.activeProject || !this.scriptEditor) {
                this.showToast('请先打开项目并加载剧本');
                this.viewMode = 'yaml';
                return;
            }

            try {
                // 调用 beat-board.js 中的初始化函数
                if (window.initBeatBoard) {
                    window.initBeatBoard(this);
                    this.beatBoardVisible = true;
                } else {
                    console.error('beat-board.js 未加载');
                    this.showToast('节拍板模块加载失败');
                    this.viewMode = 'yaml';
                }
            } catch (e) {
                console.error('初始化节拍板失败:', e);
                this.showToast('初始化节拍板失败');
                this.viewMode = 'yaml';
            }
        },

        /** 刷新节拍板（YAML 变化后调用） */
        refreshBeatBoard() {
            if (this.viewMode === 'beat-board' && window.refreshBeatBoard) {
                window.refreshBeatBoard(this);
            }
        },

        /** 选择角色 */
        selectCharacter(character) {
            this.selectedCharacter = character;
            // 初始化雷达图
            setTimeout(() => {
                this.initCharacterRadarChart();
            }, 100);
        },

        /** 初始化角色雷达图 */
        initCharacterRadarChart() {
            if (!this.selectedCharacter) return;
            
            const canvas = document.getElementById('characterRadarChart');
            if (!canvas) {
                console.error('找不到雷达图 canvas 元素');
                return;
            }
            
            const ctx = canvas.getContext('2d');
            if (!ctx) return;
            
            // 销毁之前的图表
            if (this.characterRadarChart) {
                this.characterRadarChart.destroy();
            }
            
            // 准备数据
            const emotions = ['happy', 'sad', 'angry', 'calm', 'excited', 'fear'];
            const emotionLabels = {
                happy: '快乐',
                sad: '悲伤',
                angry: '愤怒',
                calm: '平静',
                excited: '兴奋',
                fear: '恐惧'
            };
            
            const distribution = this.selectedCharacter.emotion_distribution || {};
            const data = emotions.map(e => distribution[e] || 0);
            
            // 创建雷达图
            this.characterRadarChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: emotions.map(e => emotionLabels[e]),
                    datasets: [{
                        label: this.selectedCharacter.name,
                        data: data,
                        backgroundColor: 'rgba(99, 102, 241, 0.2)',
                        borderColor: 'rgba(99, 102, 241, 1)',
                        borderWidth: 2,
                        pointBackgroundColor: 'rgba(99, 102, 241, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 1,
                            ticks: {
                                stepSize: 0.2
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw;
                                    return `${context.label}: ${(value * 100).toFixed(1)}%`;
                                }
                            }
                        }
                    }
                }
            });
        },

        /** 定位到角色台词 */
        async scrollToCharacterDialogues() {
            if (!this.selectedCharacter || !this.scriptEditor) return;
            
            const characterName = this.selectedCharacter.name;
            const yamlText = await this._getScriptContent();
            const lines = yamlText.split('\n');
            
            // 找到该角色的第一个对话beat
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                if (line.includes('character:') && line.includes(characterName)) {
                    // 找到角色，滚动到这一行
                    this.scriptEditor.dispatch({
                        selection: { anchor: this.scriptEditor.state.doc.line(i + 1).from },
                        scrollIntoView: true
                    });
                    this.showToast(`已定位到 ${characterName} 的台词`);
                    break;
                }
            }
        },

        // ── 配置快照查看 ────────────────────

        /** 查看项目配置快照 */
        async viewConfigSnapshot() {
            if (!this.activeProject) return;

            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/config-snapshot`);
                const data = await res.json();
                if (data.code === 0) {
                    // 显示配置快照（弹窗或侧边栏）
                    const config = data.data;
                    let message = '项目配置快照：\n\n';
                    message += `提供商: ${config.provider || '未设置'}\n`;
                    message += `模型: ${config.model_name || '未设置'}\n`;
                    message += `温度: ${config.temperature ?? '未设置'}\n`;
                    message += `Max Tokens: ${config.max_tokens || '未设置'}\n`;
                    message += `Base URL: ${config.base_url || '默认'}\n`;
                    alert(message);
                } else {
                    alert('获取配置快照失败: ' + data.message);
                }
            } catch (e) {
                alert('获取配置快照失败: ' + e.message);
            }
        },

        // ── 工具方法 ─────────────────────
        showToast(message, type = 'success') {
            const toast = document.createElement('div');
            const colors = {
                success: 'bg-green-600',
                warning: 'bg-yellow-500 text-black',
                error: 'bg-red-600',
            };
            toast.className = `fixed bottom-4 right-4 ${colors[type] || colors.success} text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-opacity duration-300`;
            toast.setAttribute('aria-live', 'polite');
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        },

        // ── EditMeta 编辑器元数据 ─────────────────────
        /** 保存编辑器元数据 */
        async saveEditMeta() {
            if (!this.activeProject) return;

            // 收集当前编辑器状态
            const meta = {
                novel_scroll_top: this.novelEditor ? this.novelEditor.scrollDOM ? this.novelEditor.scrollDOM.scrollTop : 0 : 0,
                script_scroll_top: this.scriptEditor ? this.scriptEditor.scrollDOM ? this.scriptEditor.scrollDOM.scrollTop : 0 : 0,
                left_panel_visible: this.leftPanelVisible !== false,
                right_panel_visible: this.rightPanelVisible !== false,
                panel_ratio: this.panelRatio || 50,
                guide_expanded: this.guideExpanded !== false,
                version_panel_visible: this.showVersionPanel === true,
                skill_panel_visible: this.showSkillPanel === true,
            };

            try {
                await fetch(`/api/v1/projects/${this.activeProject.id}/edit-meta`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(meta),
                });
            } catch (e) {
                console.error('保存编辑器元数据失败:', e);
            }
        },

        /** 加载编辑器元数据 */
        async loadEditMeta() {
            if (!this.activeProject) return;

            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/edit-meta`);
                const data = await res.json();
                if (data.code === 0) {
                    const meta = data.data;
                    // 恢复面板状态
                    if (this.leftPanelVisible !== undefined) this.leftPanelVisible = meta.left_panel_visible !== false;
                    if (this.rightPanelVisible !== undefined) this.rightPanelVisible = meta.right_panel_visible !== false;
                    if (this.panelRatio !== undefined) this.panelRatio = meta.panel_ratio || 50;
                    if (this.guideExpanded !== undefined) this.guideExpanded = meta.guide_expanded !== false;

                    // 恢复滚动位置（延迟执行，等编辑器初始化完成）
                    setTimeout(() => {
                        if (this.novelEditor && this.novelEditor.scrollDOM && meta.novel_scroll_top) {
                            this.novelEditor.scrollDOM.scrollTop = meta.novel_scroll_top;
                        }
                        if (this.scriptEditor && this.scriptEditor.scrollDOM && meta.script_scroll_top) {
                            this.scriptEditor.scrollDOM.scrollTop = meta.script_scroll_top;
                        }
                    }, 500);
                }
            } catch (e) {
                console.error('加载编辑器元数据失败:', e);
            }
        },

        // ── 文件导入功能 ─────────────────────

        /** 触发文件选择对话框 */
        triggerFileImport() {
            if (!this.activeProject) {
                this.showToast('请先打开一个项目');
                return;
            }
            const fileInput = document.getElementById('file-import-input');
            if (fileInput) fileInput.click();
        },

        /** 处理文件导入 */
        async importFile(event) {
            const file = event.target.files[0];
            if (!file) return;

            // 验证文件类型
            const allowedTypes = ['.txt', '.docx', '.pdf'];
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!allowedTypes.includes(fileExt)) {
                alert(`不支持的文件类型：${fileExt}\n仅支持 ${allowedTypes.join(', ')}`);
                event.target.value = '';
                return;
            }

            // 验证文件大小（最大 50MB）
            const maxSize = 50 * 1024 * 1024;
            if (file.size > maxSize) {
                alert(`文件太大：${(file.size / 1024 / 1024).toFixed(2)}MB\n最大支持 50MB`);
                event.target.value = '';
                return;
            }

            this.showToast(`正在导入文件：${file.name}...`);

            try {
                // 创建 FormData
                const formData = new FormData();
                formData.append('file', file);

                // 调用后端 API
                const response = await fetch(`/api/v1/projects/${this.activeProject.id}/import-file`, {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (result.code === 0) {
                    const { text, char_count } = result.data;

                    // 问题5：检查字数限制（最小500字）
                    if (char_count < 500) {
                        alert(`文件内容太短（仅 ${char_count} 字），最少需要 500 字`);
                        event.target.value = '';
                        return;
                    }

                    // 问题4：简单过滤（移除多余空行和特殊字符）
                    this.showToast('正在过滤内容...');
                    const filteredText = text
                        .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '') // 移除控制字符
                        .replace(/\n{3,}/g, '\n\n') // 合并多余空行
                        .trim();

                    // 问题5：如果内容超过最大限制，提示用户
                    const MAX_CHARS = 50000; // 单次最大字符数
                    let finalText = filteredText || text;

                    if (finalText.length > MAX_CHARS) {
                        if (!confirm(`内容较长（${finalText.length} 字），将超过单次处理限制。\n点击"确定"分批处理，点击"取消"仅加载前 ${MAX_CHARS} 字。`)) {
                            finalText = finalText.substring(0, MAX_CHARS);
                        }
                    }

                    // 写入编辑器
                    if (this.novelEditor) {
                        const { setContent } = await import('/js/editor.js');
                        setContent(this.novelEditor, finalText);
                    }

                    // 自动保存
                    await this.debounceSaveNovel();

                    this.showToast(`导入成功！共 ${char_count} 字，过滤后为 ${finalText.length} 字`);
                } else {
                    alert('导入失败：' + result.message);
                }
            } catch (error) {
                console.error('文件导入失败:', error);
                alert('文件导入失败：' + error.message);
            } finally {
                // 清空文件输入，允许重复选择同一文件
                event.target.value = '';
            }
        },

        /** 防抖保存小说 */
        debounceSaveNovel() {
            clearTimeout(this._novelSaveTimer);
            this._novelSaveTimer = setTimeout(() => {
                if (this.activeProject) this.saveNovel();
            }, 2000);
        },

        // ── 保存位置提示功能（问题6）─────────────────────

        /** 显示保存位置信息 */
        showSaveLocation(type = 'novel') {
            const projectDir = `projects/${this.activeProject.id}`;
            const filename = type === 'novel' ? 'novel.txt' : 'script.yaml';
            const fullPath = `${projectDir}/${type}/${filename}`;
            this.showToast(`已保存！文件位置：${fullPath}`);
        },

        /** 保存小说（重写以支持命名） */
        async saveNovelWithNotice() {
            if (!this.activeProject) return;
            const content = this.novelEditor
                ? (await import('/js/editor.js')).getContent(this.novelEditor)
                : this.novelText;  // 修复：原来是 this.novelYaml（错误）

            // 让用户命名文件（可选）
            const customName = prompt('请输入文件名（留空使用项目名称）:', this.activeProject.name || 'novel');
            if (customName === null) return; // 用户取消
            
            // 调用原有保存逻辑（带提示）
            await this.saveNovel(true);
            
            // 显示保存位置
            this.showSaveLocation('novel');
        },

        /** 保存剧本（重写以支持命名） */
        async saveScriptWithNotice() {
            if (!this.activeProject) return;
            const yaml = this.scriptEditor
                ? (await import('/js/editor.js')).getContent(this.scriptEditor)
                : this.scriptYaml;

            // 让用户命名文件（可选）
            const customName = prompt('请输入文件名（留空使用项目名称）:', this.activeProject.name || 'script');
            if (customName === null) return; // 用户取消
            
            // 调用原有保存逻辑（带提示）
            await this.saveScript(true);
            
            // 显示保存位置
            this.showSaveLocation('script');
        },

        /** 在页面卸载前保存元数据 */
        setupBeforeUnload() {
            window.addEventListener('beforeunload', () => {
                this.saveEditMeta();
            });
        },

        // ── 文件管理功能 ─────────────────────

        /** 切换文件管理面板 */
        async toggleFileManager() {
            this.showFileManager = !this.showFileManager;
            if (this.showFileManager && this.activeProject) {
                await this.loadProjectFiles();
            }
        },

        /** 加载项目文件列表 */
        async loadProjectFiles() {
            if (!this.activeProject) return;

            try {
                const res = await fetch(`/api/v1/projects/${this.activeProject.id}/files`);
                const data = await res.json();
                if (data.code === 0) {
                    this.projectFiles = data.data || [];
                }
            } catch (e) {
                console.error('加载项目文件失败:', e);
            }
        },

        /** 下载文件到用户下载文件夹（C:\Users\用户名\Downloads） */
        async downloadFile(file) {
            if (!this.activeProject) return;

            try {
                this.downloadingFile = true;
                const url = `/api/v1/projects/${this.activeProject.id}/files/download?file_path=${encodeURIComponent(file.path)}`;
                
                // 方法1：使用 fetch 下载并创建 Blob 触发下载（更可靠）
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`下载失败: ${response.statusText}`);
                }
                
                const blob = await response.blob();
                const blobUrl = URL.createObjectURL(blob);
                
                // 创建下载链接并触发下载
                const a = document.createElement('a');
                a.href = blobUrl;
                a.download = file.name;  // 设置下载文件名
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                
                // 清理
                setTimeout(() => {
                    document.body.removeChild(a);
                    URL.revokeObjectURL(blobUrl);
                }, 100);
                
                this.showToast(`正在下载：${file.name}`);
            } catch (e) {
                console.error('下载文件失败:', e);
                alert('下载失败：' + e.message);
            } finally {
                this.downloadingFile = false;
            }
        },

        /** 格式化文件大小 */
        formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        /** 格式化修改时间 */
        formatFileTime(timestamp) {
            const date = new Date(timestamp * 1000);
            return date.toLocaleString('zh-CN');
        },
    };
}

// 页面加载完成后，初始化元数据保存
document.addEventListener('alpine:init', () => {
    // Alpine 初始化后，获取组件实例并加载元数据
    setTimeout(() => {
        const appComponent = Alpine.$data(document.body);
        if (appComponent && appComponent.loadEditMeta) {
            // 延迟加载，等项目加载完成
            setTimeout(() => {
                appComponent.loadEditMeta();
                appComponent.setupBeforeUnload();
            }, 1000);
        }
    }, 500);
});
