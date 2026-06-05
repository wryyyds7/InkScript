"""PyWebView 桌面窗口封装

负责创建桌面窗口,内嵌启动 FastAPI 后端,
并加载前端页面.
"""

from __future__ import annotations

import threading
import time
import webview

from novel2script.config import get_config


def _start_server(host: str, port: int) -> None:
    """在后台线程启动 FastAPI(关闭时 CTRL+C 退出)"""
    import uvicorn

    uvicorn.run(
        "novel2script.api.main:app",
        host=host,
        port=port,
        log_level="warning",
    )


def start_window(
    host: str | None = None,
    port: int | None = None,
    width: int = 1200,
    height: int = 800,
    title: str | None = None,
) -> None:
    """启动 PyWebView 桌面窗口

    Args:
        host: 后端绑定地址(默认读配置)
        port: 后端端口(默认读配置)
        width: 窗口宽度
        height: 窗口高度
        title: 窗口标题
    """
    cfg = get_config()
    host = host or cfg.host
    port = port or cfg.port
    title = title or cfg.app_name

    # 1. 启动 FastAPI 后端(后台线程)
    server_thread = threading.Thread(
        target=_start_server,
        args=(host, port),
        daemon=True,  # 主线程退出时自动结束
    )
    server_thread.start()

    # 2. 等待后端就绪(最多 10 秒)
    import urllib.request
    deadline = time.time() + 10
    ready = False
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://{host}:{port}/health")
            ready = True
            break
        except Exception:
            time.sleep(0.2)

    if not ready:
        raise RuntimeError("后端服务启动超时,请检查端口是否被占用")

    # 3. 创建 PyWebView 窗口
    url = f"http://{host}:{port}/"
    window = webview.create_window(
        title=title,
        url=url,
        width=width,
        height=height,
        min_size=(800, 600),
        resizable=True,
        text_select=True,
        confirm_close=True,  # 关闭前确认
    )

    # 4. 启动事件循环(阻塞,直到窗口关闭)
    webview.start(
        debug=cfg.debug,  # debug=True 时打开 DevTools
        gui=webview.guilib.DEFAULT,  # 自动选择可用 GUI 后端
    )
