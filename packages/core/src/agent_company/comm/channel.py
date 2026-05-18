"""频道模型定义。

频道是消息的容器，管理成员与消息历史。
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from agent_company.comm.message import Message, Visibility


class Channel(BaseModel):
    """通信频道。

    每个频道拥有独立的成员列表和消息历史，
    支持按可见性进行访问控制。
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str = Field(..., description="频道名称，全局唯一")
    description: str = Field(default="", description="频道描述")
    visibility: Visibility = Field(default=Visibility.PUBLIC, description="频道可见性")
    members: set[str] = Field(default_factory=set, description="成员 Agent ID 集合")
    history: list[Message] = Field(default_factory=list, description="消息历史记录")

    def add_member(self, agent_id: str) -> None:
        """添加成员到频道。"""
        self.members.add(agent_id)

    def remove_member(self, agent_id: str) -> None:
        """从频道移除成员。"""
        self.members.discard(agent_id)

    def post(self, message: Message) -> None:
        """发布消息到频道。

        消息会被追加到历史记录中。
        """
        self.history.append(message)

    def get_history(self, limit: int | None = None) -> list[Message]:
        """获取频道消息历史。

        Args:
            limit: 返回的最大消息数，None 表示全部返回。

        Returns:
            消息列表，按时间升序排列。
        """
        if limit is None:
            return list(self.history)
        return list(self.history[-limit:])
