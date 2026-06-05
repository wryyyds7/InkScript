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

        // ── 生命周期 ────────────────────
        init() {
            this.loadProjects();
        },

        // ── 项目管理 ─────────────────────
        async loadProjects() {
            const res = await fetch('/api/v1/projects');
            const data = await res.json();
            if (data.code === 0) {
                this.projects = data.data;
            }
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
