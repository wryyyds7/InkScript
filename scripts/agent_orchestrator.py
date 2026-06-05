#!/usr/bin/env python3, """
InkScript Agent 协作编排脚本

功能:
1. 一键启动当前阶段的 Agent
2. 自动执行任务(调用 Skills)
3. 每个任务完成后,自动 GitHub 提交
4. 等待用户确认(Human-in-the-loop)
5. 用户确认后,自动启动下一阶段的 Agent

使用方法:
    python agent_orchestrator.py --phase 1          # 启动阶段 1
    python agent_orchestrator.py --phase 1 --task 1.1  # 启动阶段 1 的任务 1.1
    python agent_orchestrator.py --list             # 列出所有阶段和任务
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
GITHUB_REPO = "https://github.com/wryyyds7/InkScript"


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def print_task(text: str):
    """打印任务"""
    print(f"{Colors.CYAN}[TASK] {text}{Colors.ENDC}")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}[SUCCESS] {text}{Colors.ENDC}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}[WARNING] {text}{Colors.ENDC}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.ENDC}")


def ask_confirmation(prompt: str = "是否继续？") -> bool:
    """询问用户确认"""
    while True:
        response = input(f"{Colors.YELLOW}{prompt} (y/n): {Colors.ENDC}").strip().lower()
        if response in ['y', 'yes', '是']:
            return True
        elif response in ['n', 'no', '否']:
            return False
        else:
            print_warning("请输入 y/yes/是 或 n/no/否")


def ask_input(prompt: str) -> str:
    """询问用户输入"""
    return input(f"{Colors.CYAN}{prompt}: {Colors.ENDC}").strip()


def run_command(cmd: str, cwd: Optional[Path] = None) -> bool:
    """运行命令"""
    try:
        print(f"{Colors.BLUE}运行命令: {cmd}{Colors.ENDC}")
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"命令执行失败: {e}")
        print_error(f"错误输出: {e.stderr}")
        return False


def git_commit_and_push(message: str) -> bool:
    """Git 提交并推送"""
    print_task("Git 提交并推送...")
    
    # 检查是否有变更
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if not result.stdout.strip():
        print_warning("没有变更需要提交")
        return True
    
    # Git add
    if not run_command("git add -A"):
        return False
    
    # Git commit
    if not run_command(f'git commit -m "{message}"'):
        return False
    
    # Git push
    if not run_command("git push origin main"):
        print_warning("Git push 失败,请手动推送")
        return False
    
    print_success("Git 提交并推送成功")
    return True


def call_skill(skill_name: str, input_file: Optional[str] = None, **kwargs) -> str:
    """
    调用 Skill(模拟)
    
    注意:这里只是模拟调用 Skill,实际使用时需要替换为真实的 Skill 调用逻辑
    """
    print_task(f"调用 Skill: {skill_name}")
    
    if input_file:
        print_task(f"输入文件: {input_file}")
    
    # 模拟 Skill 调用(实际使用时需要替换为真实的调用逻辑)
    # 这里只是返回模拟输出
    output = f"[Skill {skill_name} 的输出]\n"
    
    for key, value in kwargs.items():
        output += f"{key}: {value}\n"
    
    return output


class Phase1:
    """阶段 1:需求分析"""
    
    def __init__(self):
        self.phase_name = "需求分析"
        self.agent_name = "business-analyst"
    
    def run(self):
        """运行阶段 1"""
        print_header(f"阶段 1:{self.phase_name}(负责人:{self.agent_name})")
        
        # 任务 1.1:深度质询 PRD
        self.task_1_1()
        
        # 任务 1.2:调研同类产品
        self.task_1_2()
        
        # 任务 1.3:编写需求规格说明书
        self.task_1_3()
        
        # 任务 1.4:更新 PRD.md
        self.task_1_4()
        
        print_success(f"阶段 1({self.phase_name})完成！")
    
    def task_1_1(self):
        """任务 1.1:深度质询 PRD(使用 Grill Me Skill)"""
        print_header("任务 1.1:深度质询 PRD(使用 Grill Me Skill)")
        
        # 调用 Grill Me Skill
        print_task("启动 Grill Me Skill...")
        output = call_skill(
            "Grill Me",
            input_file=str(DOCS_DIR / "PRD.md"),
            task="深度质询 PRD,发现需求漏洞"
        )
        
        # 生成《PRD 质询报告.md》
        output_file = DOCS_DIR / "PRD-grill-report.md"
        print_task(f"生成文件: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# PRD 质询报告\n\n")
            f.write(output)
        
        # Human-in-the-loop
        print_warning("Grill Me 质询过程中,AI 会提出很多问题")
        print_warning("请回答这些问题,完善需求")
        print_warning("编辑完成后,请继续")
        
        if not ask_confirmation("是否已回答所有质询问题,并更新 PRD-grill-report.md？"):
            print_error("任务 1.1 中止")
            sys.exit(1)
        
        # Git 提交
        if not git_commit_and_push("docs: 添加 PRD 质询报告(Grill Me 输出)"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 1.1 完成！")
    
    def task_1_2(self):
        """任务 1.2:调研同类产品(使用 Deep Research Skill)"""
        print_header("任务 1.2:调研同类产品(使用 Deep Research Skill)")
        
        # 调用 Deep Research Skill
        print_task("启动 Deep Research Skill...")
        output = call_skill(
            "Deep Research",
            query="Final Draft, WriterDuet, Celtx 功能对比、用户体验、技术架构"
        )
        
        # 生成《同类产品调研报告.md》
        output_file = DOCS_DIR / "competitor-research.md"
        print_task(f"生成文件: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# 同类产品调研报告\n\n")
            f.write(output)
        
        # Human-in-the-loop
        print_warning("是否需要深入调研某个特定产品？")
        
        if ask_confirmation("是否需要深入调研某个特定产品？"):
            product = ask_input("请输入产品名称(如 Final Draft)")
            print_task(f"深入调研: {product}")
            # 这里可以再次调用 Deep Research Skill
        
        # Git 提交
        if not git_commit_and_push("docs: 添加同类产品调研报告(Deep Research 输出)"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 1.2 完成！")
    
    def task_1_3(self):
        """任务 1.3:编写需求规格说明书"""
        print_header("任务 1.3:编写需求规格说明书")
        
        # 读取输入文件
        print_task("读取输入文件...")
        # 这里可以调用提示词工程专家 Skill 来优化需求描述
        
        # 生成《需求规格说明书.md》
        output_file = DOCS_DIR / "requirements-spec.md"
        print_task(f"生成文件: {output_file}")
        
        # 模拟生成内容
        content = """# 需求规格说明书

## 1. 功能需求

### 1.1 项目管理
- 创建项目
- 打开项目
- 保存项目
- 导出项目

### 1.2 小说编辑
- 导入小说文本
- 编辑小说文本
- 自动保存

### 1.3 剧本转换
- 一键转换
- 实时进度推送
- 错误重试

## 2. 非功能需求

### 2.1 性能
- 支持 50 章小说
- 转换时间 < 5 分钟

### 2.2 可用性
- 一键安装
- 零配置启动

## 3. 用例

### 用例 1:创建新项目
- **参与者**:用户
- **前置条件**:应用已启动
- **步骤**:
  1. 用户点击"新建项目"
  2. 用户输入项目名称
  3. 用户点击"创建"
- **后置条件**:项目已创建,进入编辑器界面

## 4. 用户故事

### 用户故事 1:作为用户,我想导入小说文本,以便转换为剧本
- **优先级**:高
- **估算**:3 故事点
"""
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Human-in-the-loop
        print_warning("请审查需求规格说明书")
        
        if ask_confirmation("是否需要调整需求优先级？"):
            print_task("请手动编辑 docs/requirements-spec.md")
            input(f"{Colors.CYAN}编辑完成后,按 Enter 继续...{Colors.ENDC}")
        
        # Git 提交
        if not git_commit_and_push("docs: 添加需求规格说明书"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 1.3 完成！")
    
    def task_1_4(self):
        """任务 1.4:更新 PRD.md"""
        print_header("任务 1.4:更新 PRD.md")
        
        print_task("根据质询报告,完善 PRD.md...")
        
        # Human-in-the-loop
        print_warning("请手动编辑 docs/PRD.md,补充遗漏的需求")
        input(f"{Colors.CYAN}编辑完成后,按 Enter 继续...{Colors.ENDC}")
        
        # Git 提交
        if not git_commit_and_push("docs: 更新 PRD(根据 Grill Me 质询结果)"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 1.4 完成！")


class Phase2:
    """阶段 2:架构设计"""
    
    def __init__(self):
        self.phase_name = "架构设计"
        self.agent_name = "system-architect"
    
    def run(self):
        """运行阶段 2"""
        print_header(f"阶段 2:{self.phase_name}(负责人:{self.agent_name})")
        
        # 任务 2.1:技术选型调研
        self.task_2_1()
        
        # 任务 2.2:系统架构设计
        self.task_2_2()
        
        # 任务 2.3:质询架构设计
        self.task_2_3()
        
        # 任务 2.4:更新架构设计文档
        self.task_2_4()
        
        print_success(f"阶段 2({self.phase_name})完成！")
    
    def task_2_1(self):
        """任务 2.1:技术选型调研(使用 Deep Research Skill)"""
        print_header("任务 2.1:技术选型调研(使用 Deep Research Skill)")
        
        # 调用 Deep Research Skill
        print_task("启动 Deep Research Skill...")
        output = call_skill(
            "Deep Research",
            query="PyWebView vs Electron vs Tauri 对比,CodeMirror 6 vs Monaco Editor 对比,FastAPI vs Flask vs Django 对比"
        )
        
        # 生成《技术选型对比报告.md》
        output_file = DOCS_DIR / "tech-selection-report.md"
        print_task(f"生成文件: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# 技术选型对比报告\n\n")
            f.write(output)
        
        # Human-in-the-loop
        print_warning("是否需要考虑某个特定的技术选型？")
        
        if ask_confirmation("是否需要考虑某个特定的技术选型？"):
            tech = ask_input("请输入技术名称(如 Tauri)")
            print_task(f"深入调研: {tech}")
            # 这里可以再次调用 Deep Research Skill
        
        # Git 提交
        if not git_commit_and_push("docs: 添加技术选型对比报告(Deep Research 输出)"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 2.1 完成！")
    
    def task_2_2(self):
        """任务 2.2:系统架构设计"""
        print_header("任务 2.2:系统架构设计")
        
        # 读取输入文件
        print_task("读取输入文件...")
        
        # 生成《系统架构设计.md》
        output_file = DOCS_DIR / "system-architecture.md"
        print_task(f"生成文件: {output_file}")
        
        # 模拟生成内容
        content = """# 系统架构设计

## 1. 系统架构图

```
┌─────────────────────────────────────────────────────┐
│                    PyWebView 桌面壳                  │
├─────────────────────────────────────────────────────┤
│                     前端界面                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ 项目管理  │  │  编辑器   │  │  Skill   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│       ↑              ↑              ↑              │
│  ──────┴──────────────┴──────────────┴──────        │
│                     Alpine.js                       │
├─────────────────────────────────────────────────────┤
│                     FastAPI 后端                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Project │  │ Pipeline │  │  Skill   │         │
│  │  Store   │  │          │  │  Manager │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│       ↑              ↑              ↑              │
│  ──────┴──────────────┴──────────────┴──────        │
│                   LLM 客户端                        │
└─────────────────────────────────────────────────────┘
```

## 2. 模块划分

### 2.1 前端模块
- `projectList`:项目管理组件
- `editor`:编辑器组件
- `skillPanel`:Skill 面板组件

### 2.2 后端模块
- `config`:配置管理
- `schema`:数据模型
- `core/pipeline`:Pipeline 核心
- `core/steps`:Pipeline 步骤
- `skills/manager`:Skill 管理器
- `api/routes`:API 路由

## 3. 数据流向

1. 用户导入小说文本 → 前端 → API → `NovelService` → 文件系统
2. 用户点击"转换" → 前端 → API → `Pipeline` → LLM → 文件系统
3. 用户编辑剧本 → CodeMirror → 前端 → API → `ScriptService` → 文件系统
"""
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Human-in-the-loop
        print_warning("请审查系统架构设计")
        
        if ask_confirmation("是否需要调整模块划分？"):
            print_task("请手动编辑 docs/system-architecture.md")
            input(f"{Colors.CYAN}编辑完成后,按 Enter 继续...{Colors.ENDC}")
        
        # Git 提交
        if not git_commit_and_push("docs: 添加系统架构设计文档"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 2.2 完成！")
    
    def task_2_3(self):
        """任务 2.3:质询架构设计(使用 Grill Me Skill)"""
        print_header("任务 2.3:质询架构设计(使用 Grill Me Skill)")
        
        # 调用 Grill Me Skill
        print_task("启动 Grill Me Skill...")
        output = call_skill(
            "Grill Me",
            input_file=str(DOCS_DIR / "system-architecture.md"),
            task="质询架构设计的可扩展性、性能、安全性"
        )
        
        # 生成《架构设计质询报告.md》
        output_file = DOCS_DIR / "architecture-grill-report.md"
        print_task(f"生成文件: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# 架构设计质询报告\n\n")
            f.write(output)
        
        # Human-in-the-loop
        print_warning("Grill Me 质询过程中,AI 会提出很多问题")
        print_warning("请回答这些问题,完善架构设计")
        print_warning("编辑完成后,请继续")
        
        if not ask_confirmation("是否已回答所有质询问题,并更新 architecture-grill-report.md？"):
            print_error("任务 2.3 中止")
            sys.exit(1)
        
        # Git 提交
        if not git_commit_and_push("docs: 添加架构设计质询报告(Grill Me 输出)"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 2.3 完成！")
    
    def task_2_4(self):
        """任务 2.4:更新架构设计文档"""
        print_header("任务 2.4:更新架构设计文档")
        
        print_task("根据质询报告,完善架构设计...")
        
        # Human-in-the-loop
        print_warning("请手动编辑 docs/system-architecture.md 和 docs/architecture.md")
        input(f"{Colors.CYAN}编辑完成后,按 Enter 继续...{Colors.ENDC}")
        
        # Git 提交
        if not git_commit_and_push("docs: 更新架构设计文档(根据 Grill Me 质询结果)"):
            print_warning("Git 提交失败,请手动提交")
        
        print_success("任务 2.4 完成！")


def list_phases():
    """列出所有阶段和任务"""
    print_header("Agent 协作计划 - 阶段列表")
    
    phases = [
        {
            "phase": 1,
            "name": "需求分析",
            "agent": "business-analyst",
            "tasks": [
                "1.1 深度质询 PRD(使用 Grill Me Skill)",
                "1.2 调研同类产品(使用 Deep Research Skill)",
                "1.3 编写需求规格说明书",
                "1.4 更新 PRD.md"
            ]
        },
        {
            "phase": 2,
            "name": "架构设计",
            "agent": "system-architect",
            "tasks": [
                "2.1 技术选型调研(使用 Deep Research Skill)",
                "2.2 系统架构设计",
                "2.3 质询架构设计(使用 Grill Me Skill)",
                "2.4 更新架构设计文档"
            ]
        },
        {
            "phase": 3,
            "name": "详细设计",
            "agent": "design-engineer",
            "tasks": [
                "3.1 API 接口详细设计",
                "3.2 数据模型详细设计",
                "3.3 Prompt 模板详细设计",
                "3.4 质询详细设计(使用 Grill Me Skill)",
                "3.5 更新详细设计文档"
            ]
        },
        {
            "phase": 4,
            "name": "代码实现",
            "agent": "dev-team(backend-dev + frontend-dev + fullstack-dev)",
            "tasks": [
                "4.1 项目脚手架搭建",
                "4.2 后端核心代码实现(使用 TDD Skill)",
                "4.3 前端核心代码实现(使用前端开发 Skill)",
                "4.4 PyWebView 集成(使用全栈开发 Skill)",
                "4.5 代码审查(使用 Grill Me Skill)"
            ]
        },
        {
            "phase": 5,
            "name": "测试验证",
            "agent": "qa-team(test-engineer + performance-engineer + security-engineer)",
            "tasks": [
                "5.1 编写集成测试",
                "5.2 性能测试(使用 Web Performance Audit Skill)",
                "5.3 安全审计(使用 Grill Me Skill)",
                "5.4 Bug 修复"
            ]
        },
        {
            "phase": 6,
            "name": "文档编写",
            "agent": "technical-writer",
            "tasks": [
                "6.1 编写用户手册",
                "6.2 编写开发者指南",
                "6.3 生成 API 参考文档"
            ]
        },
        {
            "phase": 7,
            "name": "部署发布",
            "agent": "devops-engineer",
            "tasks": [
                "7.1 编写 PyInstaller 打包配置",
                "7.2 编写自动化构建脚本",
                "7.3 执行打包",
                "7.4 编写发布说明"
            ]
        }
    ]
    
    for p in phases:
        print(f"\n{Colors.BOLD}阶段 {p['phase']}:{p['name']}{Colors.ENDC}")
        print(f"  负责人:{p['agent']}")
        print(f"  任务:")
        for task in p['tasks']:
            print(f"    - {task}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='InkScript Agent 协作编排脚本')
    parser.add_argument('--phase', type=int, help='启动指定阶段(1-7)')
    parser.add_argument('--task', type=str, help='启动指定任务(如 1.1)')
    parser.add_argument('--list', action='store_true', help='列出所有阶段和任务')
    
    args = parser.parse_args()
    
    if args.list:
        list_phases()
        return
    
    if args.phase:
        if args.phase == 1:
            phase = Phase1()
            phase.run()
        elif args.phase == 2:
            phase = Phase2()
            phase.run()
        # TODO: 添加阶段 3-7
        else:
            print_error(f"阶段 {args.phase} 尚未实现")
            sys.exit(1)
    else:
        print_warning("请指定 --phase 或 --list")
        parser.print_help()


if __name__ == "__main__":
    main()
