"""CLI 入口（Typer + Rich）

支持三种子命令：
- gui  ：启动 PyWebView 桌面窗口（默认）
- serve：启动 FastAPI Web 服务
- convert：CLI 模式直接转换
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
    help="Novel2Script：将小说自动转换为结构化剧本",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="显示版本号"),
):
    """默认行为：无参数时等价于 `novel2script gui`"""
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
    """启动 PyWebView 桌面窗口（默认命令）"""
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
    """启动 FastAPI Web 服务（Browser 模式）"""
    import uvicorn

    console.print(f"[bold green]启动 Web 服务：http://{host}:{port}[/bold green]")
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
    input_file: Path = typer.Argument(..., exists=True, help="输入小说文件（.txt / .md）"),
    output_file: Path = typer.Argument(..., help="输出 YAML 文件路径"),
    model: str = typer.Option("", "--model", "-m", help="LLM 模型名称"),
):
    """CLI 模式：直接转换小说为剧本 YAML"""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from novel2script.llm_client import OpenAIClient
    from novel2script.core.pipeline import build_pipeline
    from novel2script.schema import Script, to_yaml

    console.print(f"[bold]输入[/bold]：{input_file}")
    console.print(f"[bold]输出[/bold]：{output_file}")

    novel_text = input_file.read_text(encoding="utf-8")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("正在转换...", total=None)

        llm = OpenAIClient(model_name=model or None)
        pipeline = build_pipeline(llm=llm)
        script = pipeline.run(Script(), novel_text)

        output_file.write_text(to_yaml(script), encoding="utf-8")

    console.print("[bold green]✓ 转换完成！[/bold green]")


if __name__ == "__main__":
    app()
