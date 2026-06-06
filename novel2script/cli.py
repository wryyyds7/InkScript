"""CLI 入口(Typer + Rich)

支持三种子命令:
- gui  :启动 PyWebView 桌面窗口(默认)
- serve:启动 FastAPI Web 服务
- convert:CLI 模式直接转换
"""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="novel2script",
    help="Novel2Script:将小说自动转换为结构化剧本",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="显示版本号"),
):
    """默认行为:无参数时等价于 `novel2script gui`"""
    if version:
        from novel2script import __version__
        console.print(f"Novel2Script v{__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        gui()


@app.command()
def gui(
    port: int = typer.Option(8000, "--port", "-p", help="后端端口"),
):
    """启动 PyWebView 桌面窗口(默认命令)"""
    from novel2script.desktop.window import start_window
    from novel2script.config import get_config

    cfg = get_config()
    cfg.port = port

    console.print("[bold green]启动桌面窗口...[/bold green]")
    start_window(host=cfg.host, port=cfg.port)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="绑定地址"),
    port: int = typer.Option(8000, "--port", "-p", help="监听端口"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="是否自动打开浏览器"),
):
    """启动 FastAPI Web 服务(Browser 模式)"""
    import uvicorn

    console.print(f"[bold green]启动 Web 服务:http://{host}:{port}[/bold green]")
    if open_browser:
        webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(
        "novel2script.api.main:app",
        host=host,
        port=port,
        reload=False,
    )


@app.command()
def convert(
    input_file: Path = typer.Argument(..., exists=True, help="输入小说文件(.txt / .md)"),
    output_file: Path = typer.Argument(..., help="输出 YAML 文件路径"),
    model: str = typer.Option("", "--model", "-m", help="LLM 模型名称"),
):
    """CLI 模式:直接转换小说为剧本 YAML"""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from novel2script.llm_client import OpenAIClient
    from novel2script.core.pipeline import build_pipeline
    from novel2script.schema import Script, to_yaml

    console.print(f"[bold]输入[/bold]:{input_file}")
    console.print(f"[bold]输出[/bold]:{output_file}")

    novel_text = input_file.read_text(encoding="utf-8")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("正在转换...", total=None)

        llm = OpenAIClient(model_name=model or None)
        pipeline = build_pipeline(llm=llm)
        script = pipeline.run(Script(), novel_text)

        output_file.write_text(to_yaml(script), encoding="utf-8")

    console.print("[bold green]✓ 转换完成！[/bold green]")


@app.command()
def validate(
    file: Path = typer.Argument(..., exists=True, help="YAML 文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细错误信息"),
):
    """校验 YAML 剧本文件格式"""
    from novel2script.schema import Script
    from novel2script.core.steps.yaml_generator import yaml_to_script

    console.print(f"[bold]校验文件[/bold]: {file}")

    try:
        yaml_text = file.read_text(encoding="utf-8")
        script = yaml_to_script(yaml_text)

        # 统计信息
        total_beats = sum(len(scene.beats) for scene in script.scenes)
        total_dialogues = sum(
            len([b for b in scene.beats if b.type == "dialogue"])
            for scene in script.scenes
        )

        # 显示结果
        table = Table(title="校验结果")
        table.add_column("项目", style="cyan")
        table.add_column("数值", style="green")
        table.add_row("场景数", str(len(script.scenes)))
        table.add_row("总 Beat 数", str(total_beats))
        table.add_row("对白 Beat 数", str(total_dialogues))
        table.add_row("角色数", str(len(script.characters)))
        console.print(table)

        console.print("[bold green]✓ YAML 格式正确！[/bold green]")

    except Exception as e:
        console.print(f"[bold red]✗ 校验失败[/bold red]: {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def skill(
    action: str = typer.Argument(..., help="操作: list/run/info"),
    skill_name: str = typer.Argument(None, help="Skill 名称(运行/查看时需要)"),
    project_id: str = typer.Option(None, "--project", "-p", help="项目 ID(运行 Skill 时需要)"),
):
    """Skill 管理命令
    
    Actions:
    - list: 列出所有可用 Skill
    - run <skill_name>: 运行指定 Skill
    - info <skill_name>: 查看 Skill 详细信息
    """
    import requests

    # 获取 API 地址
    from novel2script.config import get_config
    cfg = get_config()
    api_base = f"http://{cfg.host}:{cfg.port}"

    if action == "list":
        # 列出所有 Skill
        try:
            response = requests.get(f"{api_base}/api/v1/skills", timeout=5)
            if response.status_code == 200:
                skills = response.json()
                if not skills:
                    console.print("[yellow]没有可用的 Skill[/yellow]")
                    return

                table = Table(title="可用 Skill")
                table.add_column("名称", style="cyan")
                table.add_column("类型", style="green")
                table.add_column("描述", style="white")
                table.add_column("状态", style="yellow")
                for skill in skills:
                    status = "✓ 启用" if skill.get("enabled", True) else "✗ 禁用"
                    table.add_row(
                        skill["name"],
                        skill.get("type", "unknown"),
                        skill.get("description", ""),
                        status,
                    )
                console.print(table)
            else:
                console.print(f"[red]获取 Skill 列表失败: {response.status_code}[/red]")
        except requests.exceptions.ConnectionError:
            console.print("[red]错误: 无法连接到后端服务,请先启动 InkScript[/red]")
            console.print(f"[yellow]提示: 运行 `novel2script serve` 启动服务[/yellow]")

    elif action == "run":
        # 运行 Skill
        if not skill_name:
            console.print("[red]错误: 请指定要运行的 Skill 名称[/red]")
            raise typer.Exit(1)

        if not project_id:
            console.print("[red]错误: 请指定项目 ID (--project)[/red]")
            raise typer.Exit(1)

        try:
            response = requests.post(
                f"{api_base}/api/v1/skills/{skill_name}/run",
                json={"project_id": project_id},
                timeout=30,
            )
            if response.status_code == 200:
                result = response.json()
                console.print("[bold green]✓ Skill 运行成功[/bold green]")
                console.print(result.get("result", ""))
            else:
                console.print(f"[red]Skill 运行失败: {response.status_code}[/red]")
                console.print(response.text)
        except requests.exceptions.ConnectionError:
            console.print("[red]错误: 无法连接到后端服务[/red]")

    elif action == "info":
        # 查看 Skill 详细信息
        if not skill_name:
            console.print("[red]错误: 请指定要查看的 Skill 名称[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Skill info 功能正在开发中...[/yellow]")
        console.print(f"[cyan]Skill 名称: {skill_name}[/cyan]")

    else:
        console.print(f"[red]未知操作: {action}[/red]")
        console.print("[yellow]支持的操作: list, run, info[/yellow]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
