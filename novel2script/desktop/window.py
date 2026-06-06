"""PyWebView 桌面窗口封装

负责创建桌面窗口,内嵌启动 FastAPI 后端,
并加载前端页面.
如果 PyWebView 不可用,自动回退到系统浏览器.
支持单实例运行(通过 socket 检测).
"""

from __future__ import annotations

import socket
import threading
import time
import webbrowser
from pathlib import Path

from novel2script.config import get_config

# 尝试导入 PyWebView,如果失败则标记为不可用
try:
    import webview
    _PYWEBVIEW_AVAILABLE = True
except ImportError:
    _PYWEBVIEW_AVAILABLE = False
    print("[警告] PyWebView 未安装,将使用系统浏览器模式")

# 单实例锁(socket)
_SINGLE_INSTANCE_PORT = 12345  # 用于检测单实例的端口
_single_instance_socket = None


def _acquire_single_instance() -> bool:
    """尝试获取单实例锁
    
    Returns:
        bool: 如果成功获取锁(第一个实例),返回 True;否则返回 False
    """
    global _single_instance_socket
    
    try:
        _single_instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _single_instance_socket.bind(("127.0.0.1", _SINGLE_INSTANCE_PORT))
        _single_instance_socket.listen(1)
        return True
    except OSError:
        # 端口已被占用,说明已有实例在运行
        return False


def _release_single_instance():
    """释放单实例锁"""
    global _single_instance_socket
    if _single_instance_socket:
        try:
            _single_instance_socket.close()
        except Exception:
            pass
        _single_instance_socket = None


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
    single_instance: bool = True,
) -> None:
    """启动桌面窗口(PyWebView 或浏览器回退)

    Args:
        host: 后端绑定地址(默认读配置)
        port: 后端端口(默认读配置)
        width: 窗口宽度
        height: 窗口高度
        title: 窗口标题
        single_instance: 是否启用单实例模式(默认 True)
    """
    # 检查单实例
    if single_instance and not _acquire_single_instance():
        print("[警告] 已有 InkScript 实例在运行中,将焦点转移到已有窗口")
        # TODO: 将来可以实现激活已有窗口的功能
        return

    try:
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

        # 3. 根据 PyWebView 可用性选择窗口模式
        url = f"http://{host}:{port}/"

        if _PYWEBVIEW_AVAILABLE:
            # 使用 PyWebView 创建桌面窗口
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

            # 启动事件循环(阻塞,直到窗口关闭)
            webview.start(
                debug=cfg.debug,  # debug=True 时打开 DevTools
            )
        else:
            # PyWebView 不可用,回退到系统浏览器
            print(f"[信息] PyWebView 未安装,正在打开系统浏览器...")
            print(f"[信息] 访问地址: <ADDRESS_REMOVED>
            webbrowser.open(url)

            # 保持主线程运行,直到用户手动退出
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[信息] 正在退出...")
                return

    finally:
        # 释放单实例锁
        _release_single_instance()
