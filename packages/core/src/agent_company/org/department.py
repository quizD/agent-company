"""部门模型定义。

部门是组织结构的中间层，管理一组角色和对应的 Agent。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from agent_company.org.role import Role

if TYPE_CHECKING:
    pass


class Department(BaseModel):
    """组织部门。

    部门包含若干角色定义和已分配的 Agent 实例，
    由部门负责人统筹管理。
    """

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="部门名称")
    description: str = Field(default="", description="部门职能描述")
    roles: dict[str, Role] = Field(default_factory=dict, description="角色名称 → 角色定义")
    agents: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent ID → Agent 实例（BaseAgent）",
    )
    head_role: str = Field(default="", description="部门负责人角色名称")

    def add_role(self, role: Role) -> None:
        """向部门添加角色定义。"""
        self.roles[role.name] = role

    def assign_agent(self, agent_id: str, agent: Any) -> None:
        """将 Agent 分配到部门。"""
        self.agents[agent_id] = agent

    def remove_agent(self, agent_id: str) -> None:
        """从部门移除 Agent。"""
        self.agents.pop(agent_id, None)

    def get_head(self) -> Any | None:
        """获取部门负责人 Agent 实例。"""
        for agent_id, agent in self.agents.items():
            if hasattr(agent, "role") and agent.role and agent.role.name == self.head_role:
                return agent
        return None
