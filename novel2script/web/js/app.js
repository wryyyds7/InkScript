/** InkScript 前端主逻辑（Alpine.js） */

function app() {
    return {
        // ── 状态 ──────────────────────
        view: 'projects',          // 'projects' | 'editor' | 'config'
        activeProject: null,        // 当前打开的项目 {id, name, ...}
        projects: [],               // 项目列表
        novelText: '',              // 编辑器中的小说原文
        scriptYaml: '',            // 编辑器中的剧本 YAML
        converting: false,         // 是否正在转换
        progress: 0,              // 转换进度 0-100
        taskId: '',                // 当前转换任务 ID
        eventSource: null,         // SSE 连接
        config: {                  // 配置
            base_url: '',
            api_key: '',
            model_name: '',
            temperature: 0.7,
        },

        // ── 生命周期 ────────────────────
        init() {
            this.loadProjects();
            this.loadConfig();
        },

        // ── 项目管理 ─────────────────────
        async loadProjects() {
            const res = await fetch('/api/v1/projects');
            const data = await res.json();
            if (data.code === 0) {
                this.projects = data.data;
                // 渲染项目列表
                this.renderProjectList();
            }
        },
        
        renderProjectList() {
            const container = document.getElementById('project-list');
            if (!container) return;
            
            container.innerHTML = this.projects.map(p => `
                <div class="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
                    <div>
                        <h3 class="font-medium">${p.name}</h3>
                        <p class="text-sm text-gray-500">创建时间：${new Date(p.created_at).toLocaleString()}</p>
                    </div>
                    <div class="flex gap-2">
                        <button @click="openProject('${p.id}')" class="btn">打开</button>
                        <button @click="deleteProject('${p.id}')" class="btn text-red-600">删除</button>
                    </div>
                </div>
            `).join('') || '<p class="text-gray-500">暂无项目，点击"新建项目"创建。</p>';
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
            }
        },

        async openProject(id) {
            const res = await fetch(`/api/v1/projects/${id}`);
            const data = await res.json();
            if (data.code === 0) {
                this.activeProject = data.data;
                this.view = 'editor';
                await this.loadNovel();
            }
        },

        async deleteProject(id) {
            if (!confirm('确认删除该项目？')) return;
            await fetch(`/api/v1/projects/${id}`, { method: 'DELETE' });
            await this.loadProjects();
        },
        
        // ── 配置管理 ─────────────────────
        async loadConfig() {
            // 这里应该从后端加载配置，暂时使用 localStorage
            const saved = localStorage.getItem('inkscript_config');
            if (saved) {
                this.config = JSON.parse(saved);
            }
        },
        
        async saveConfig() {
            // 保存到 localStorage
            localStorage.setItem('inkscript_config', JSON.stringify(this.config));
            alert('配置已保存！');
        },

        // ── 编辑器 ─────────────────────
        async loadNovel() {
            if (!this.activeProject) return;
            const res = await fetch(`/api/v1/projects/${this.activeProject.id}/novel`);
            const data = await res.json();
            this.novelText = data.data?.content || '';
        },

        async saveNovel() {
            if (!this.activeProject) return;
            await fetch(`/api/v1/projects/${this.activeProject.id}/novel`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: this.novelText }),
            });
        },

        async startConvert() {
            if (!this.activeProject) return;
            this.converting = true;
            this.progress = 0;

            const res = await fetch(`/api/v1/projects/${this.activeProject.id}/convert`, {
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
            });

            this.eventSource.addEventListener('task_complete', () => {
                this.converting = false;
                this.progress = 100;
                this.eventSource.close();
                this.loadScript();
                alert('转换完成！');
            });

            this.eventSource.addEventListener('task_failed', (e) => {
                const d = JSON.parse(e.data);
                this.converting = false;
                this.eventSource.close();
                alert('转换失败：' + d.error);
            });

            this.eventSource.onerror = () => {
                // 自动重连
                setTimeout(() => this.connectSSE(taskId), 1000);
            };
        },

        async loadScript() {
            if (!this.activeProject) return;
            const res = await fetch(`/api/v1/projects/${this.activeProject.id}/script`);
            const data = await res.json();
            this.scriptYaml = data.data?.yaml || '';
        },

        async saveScript() {
            if (!this.activeProject) return;
            await fetch(`/api/v1/projects/${this.activeProject.id}/script`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: this.scriptYaml }),
            });
        },
    };
}
