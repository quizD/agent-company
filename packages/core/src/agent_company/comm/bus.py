"""消息总线 - 全局消息路由与分发。

MessageBus 负责管理所有频道、订阅关系，以及消息的发布与路由。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent_company.comm.channel import Channel
from agent_company.comm.message import Message, Visibility


class MessageBus:
    """消息总线。

    作为公司级别的通信基础设施，管理频道创建、
    Agent 订阅以及消息的异步发布与分发。
    """

    def __init__(self) -> None:
        # 频道名称 → 频道对象
        self.channels: dict[str, Channel] = {}
        # Agent ID → 订阅的频道名称列表
        self.subscriptions: dict[str, list[str]] = {}
        # 全局消息历史
        self.history: list[Message] = []
        # 拦截器回调列表（用于监控、评估等）
        self.interceptors: list[Callable[..., Any]] = []

    def create_channel(
        self,
        name: str,
        visibility: Visibility = Visibility.PUBLIC,
        description: str = "",
    ) -> Channel:
        """创建新的通信频道。

        Args:
            name: 频道名称，需全局唯一。
            visibility: 频道可见性级别。
            description: 频道描述。

        Returns:
            新创建的 Channel 对象。

        Raises:
            ValueError: 如果频道名称已存在。
        """
        if name in self.channels:
            raise ValueError(f"频道 '{name}' 已存在")
        channel = Channel(name=name, visibility=visibility, description=description)
        self.channels[name] = channel
        return channel

    def subscribe(self, agent_id: str, channel_name: str) -> None:
        """订阅 Agent 到指定频道。

        Args:
            agent_id: Agent ID。
            channel_name: 目标频道名称。

        Raises:
            KeyError: 如果频道不存在。
        """
        if channel_name not in self.channels:
            raise KeyError(f"频道 '{channel_name}' 不存在")
        # 注册订阅关系
        if agent_id not in self.subscriptions:
            self.subscriptions[agent_id] = []
        if channel_name not in self.subscriptions[agent_id]:
            self.subscriptions[agent_id].append(channel_name)
        # 将 Agent 加入频道成员列表
        self.channels[channel_name].add_member(agent_id)

    def unsubscribe(self, agent_id: str, channel_name: str) -> None:
        """取消 Agent 对指定频道的订阅。

        Args:
            agent_id: Agent ID。
            channel_name: 目标频道名称。
        """
        if agent_id in self.subscriptions:
            self.subscriptions[agent_id] = [
                ch for ch in self.subscriptions[agent_id] if ch != channel_name
            ]
        if channel_name in self.channels:
            self.channels[channel_name].remove_member(agent_id)

    async def publish(self, message: Message) -> None:
        """发布消息到指定频道。

        消息会被路由到目标频道，同时触发所有拦截器回调。

        Args:
            message: 待发布的消息对象。

        Raises:
            KeyError: 如果目标频道不存在。
        """
        channel_name = message.channel
        if channel_name not in self.channels:
            raise KeyError(f"频道 '{channel_name}' 不存在")

        # 路由到目标频道
        self.channels[channel_name].post(message)
        # 记录全局历史
        self.history.append(message)

        # 通知所有拦截器
        for interceptor in self.interceptors:
            try:
                result = interceptor(message)
                # 支持异步拦截器
                if hasattr(result, "__await__"):
                    await result
            except Exception:
                # 拦截器异常不应阻断消息传递
                pass

    def get_messages_for(
        self, agent_id: str, since_timestamp: float = 0.0
    ) -> list[Message]:
        """获取指定 Agent 可见的消息。

        根据 Agent 订阅的频道，返回时间戳之后的所有消息。

        Args:
            agent_id: 目标 Agent ID。
            since_timestamp: 起始时间戳，仅返回该时间之后的消息。

        Returns:
            符合条件的消息列表，按时间升序排列。
        """
        subscribed_channels = self.subscriptions.get(agent_id, [])
        messages: list[Message] = []
        for ch_name in subscribed_channels:
            channel = self.channels.get(ch_name)
            if channel is None:
                continue
            for msg in channel.history:
                if msg.timestamp > since_timestamp:
                    messages.append(msg)
        # 按时间排序
        messages.sort(key=lambda m: m.timestamp)
        return messages

    def add_interceptor(self, callback: Callable[..., Any]) -> None:
        """注册消息拦截器。

        拦截器会在每条消息发布时被调用，可用于监控、日志、评估等。

        Args:
            callback: 接收 Message 参数的回调函数（支持同步和异步）。
        """
        self.interceptors.append(callback)
