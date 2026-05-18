"""消息模型定义。

定义消息类型、可见性、优先级以及消息数据模型。
"""

from __future__ import annotations

import time
import uuid
from enum import Enum

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """消息类型枚举。"""

    DIRECTIVE = "directive"  # 指令 - 上级对下级的任务分配
    REPORT = "report"  # 汇报 - 下级对上级的工作反馈
    PROPOSAL = "proposal"  # 提案 - 需要决策的建议
    QUESTION = "question"  # 问题 - 请求信息或澄清
    FEEDBACK = "feedback"  # 反馈 - 对工作成果的评价
    INFORMAL = "informal"  # 非正式 - 自由讨论


class Visibility(str, Enum):
    """消息可见性枚举。"""

    PUBLIC = "public"  # 全公司可见
    DEPARTMENT = "department"  # 部门内可见
    PRIVATE = "private"  # 仅发送者与接收者可见
    EXECUTIVE = "executive"  # 仅管理层可见


class Priority(str, Enum):
    """消息优先级枚举。"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Message(BaseModel):
    """消息数据模型。

    所有 Agent 间的通信都通过消息对象进行。
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    sender_id: str = Field(..., description="发送者 Agent ID")
    sender_role: str = Field(..., description="发送者角色名称")
    channel: str = Field(..., description="目标频道名称")
    content: str = Field(..., description="消息正文")
    message_type: MessageType = Field(default=MessageType.INFORMAL, description="消息类型")
    visibility: Visibility = Field(default=Visibility.PUBLIC, description="可见性")
    priority: Priority = Field(default=Priority.NORMAL, description="优先级")
    references: list[str] = Field(default_factory=list, description="引用的消息 ID 列表")
    timestamp: float = Field(default_factory=time.time, description="消息时间戳")
    metadata: dict = Field(default_factory=dict, description="附加元数据")
