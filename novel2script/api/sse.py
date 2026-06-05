"""SSE 事件推送管理

实现 SSE 事件缓存和客户端管理,
防止网络中断丢失事件.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from typing import Any, Dict, List, Optional


class SSEManager:
    """SSE 事件管理器(含事件缓存)"""

    def __init__(self, max_cache_size: int = 100):
        self.clients: Dict[str, asyncio.Queue] = {}
        self.event_cache: deque = deque(maxlen=max_cache_size)
        self._lock = asyncio.Lock()

    async def push_event(self, task_id: str, event: dict) -> None:
        """推送事件给所有订阅该任务的客户端,并缓存"""
        cached_event = {
            "task_id": task_id,
            "event": event,
            "ts": time.time(),
        }
        async with self._lock:
            self.event_cache.append(cached_event)
            dead = []
            for client_id, queue in self.clients.items():
                if client_id.startswith(task_id):
                    try:
                        queue.put_nowait(event)
                    except asyncio.QueueFull:
                        dead.append(client_id)
            for cid in dead:
                self.clients.pop(cid, None)

    def get_cached_events(self, task_id: str, since_ts: float) -> List[dict]:
        """获取自某个时间戳以来的缓存事件"""
        events: List[dict] = []
        for item in self.event_cache:
            if item["task_id"] == task_id and item["ts"] > since_ts:
                events.append(item["event"])
        return events

    async def register_client(self, client_id: str, task_id: str) -> asyncio.Queue:
        """注册客户端,返回事件队列"""
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.clients[client_id] = queue
        return queue

    async def unregister_client(self, client_id: str) -> None:
        """注销客户端"""
        self.clients.pop(client_id, None)


# 全局单例
sse_manager = SSEManager()
