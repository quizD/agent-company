"""通信模块 - 消息、频道与消息总线。"""

from agent_company.comm.bus import MessageBus
from agent_company.comm.channel import Channel
from agent_company.comm.message import Message, MessageType, Priority, Visibility

__all__ = [
    "Message",
    "MessageType",
    "Priority",
    "Visibility",
    "Channel",
    "MessageBus",
]
