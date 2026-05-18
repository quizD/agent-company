"""公司模型定义。

Company 是整个 Agent 组织的顶层容器，
整合部门、Agent、通信和治理系统。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from agent_company.comm.bus import MessageBus
from agent_company.org.department import Department
from agent_company.org.governance import GovernanceSystem
from agent_company.org.role import Role

if TYPE_CHECKING:
    pass


class Company(BaseModel):
    """AI 公司 - 顶层组织容器。

    管理所有部门、Agent、通信总线和治理系统，
    提供人员管理和任务执行的统一接口。
    """

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="公司名称")
    mission: str = Field(default="", description="公司使命")
    values: list[str] = Field(default_factory=list, description="公司核心价值观")
    departments: dict[str, Department] = Field(
        default_factory=dict, description="部门名称 → 部门对象"
    )
    agents: dict[str, Any] = Field(
        default_factory=dict, description="Agent ID → Agent 实例"
    )
    message_bus: MessageBus = Field(default_factory=MessageBus, description="消息总线")
    governance: GovernanceSystem = Field(
        default_factory=GovernanceSystem, description="治理系统"
    )
    org_knowledge: dict[str, Any] = Field(
        default_factory=dict, description="共享知识库"
    )

    # ----------------------------------------------------------------
    # 工厂方法
    # ----------------------------------------------------------------

    @classmethod
    def from_template(cls, template_name: str) -> Company:
        """从预定义模板加载公司配置。

        Args:
            template_name: 模板名称（如 'startup', 'enterprise'）。

        Returns:
            初始化好的 Company 实例。

        Note:
            当前为占位实现，后续将支持从 YAML 文件加载。
        """
        # TODO: 从 YAML 模板文件加载配置
        return cls(name=f"Company<{template_name}>")

    @classmethod
    def from_config(cls, config: dict) -> Company:
        """从配置字典创建公司实例。

        Args:
            config: 包含公司完整配置的字典。

        Returns:
            初始化好的 Company 实例。
        """
        # 解析部门配置
        departments: dict[str, Department] = {}
        for dept_cfg in config.get("departments", []):
            roles = {}
            for role_cfg in dept_cfg.get("roles", []):
                role = Role(**role_cfg)
                roles[role.name] = role
            dept = Department(
                name=dept_cfg["name"],
                description=dept_cfg.get("description", ""),
                roles=roles,
                head_role=dept_cfg.get("head_role", ""),
            )
            departments[dept.name] = dept

        # 解析治理配置
        gov_cfg = config.get("governance", {})
        governance = GovernanceSystem(
            escalation_path=gov_cfg.get("escalation_path", []),
        )

        return cls(
            name=config.get("name", "Unnamed Company"),
            mission=config.get("mission", ""),
            values=config.get("values", []),
            departments=departments,
            governance=governance,
        )

    # ----------------------------------------------------------------
    # 人员管理
    # ----------------------------------------------------------------

    def hire(self, agent: Any, role: Role, department_name: str) -> None:
        """招聘 Agent 到指定部门和角色。

        Args:
            agent: Agent 实例（BaseAgent）。
            role: 分配的角色。
            department_name: 目标部门名称。

        Raises:
            KeyError: 如果部门不存在。
        """
        if department_name not in self.departments:
            self.departments[department_name] = Department(name=department_name)

        agent_id = getattr(agent, "id", str(id(agent)))
        # 注册到公司级别
        self.agents[agent_id] = agent
        # 注册到部门
        dept = self.departments[department_name]
        dept.add_role(role)
        dept.assign_agent(agent_id, agent)
        # 订阅角色配置的频道
        for channel_name in role.channels:
            if channel_name in self.message_bus.channels:
                self.message_bus.subscribe(agent_id, channel_name)

    def fire(self, agent_id: str) -> None:
        """解雇 Agent，从公司和部门中移除。

        Args:
            agent_id: 目标 Agent ID。
        """
        # 从所有部门中移除
        for dept in self.departments.values():
            dept.remove_agent(agent_id)
        # 取消所有频道订阅
        subscribed = self.message_bus.subscriptions.pop(agent_id, [])
        for ch_name in subscribed:
            if ch_name in self.message_bus.channels:
                self.message_bus.channels[ch_name].remove_member(agent_id)
        # 从公司注册表移除
        self.agents.pop(agent_id, None)

    def replace_agent(self, old_id: str, new_agent: Any) -> None:
        """替换现有 Agent。

        保持原有的部门归属和频道订阅不变。

        Args:
            old_id: 要替换的 Agent ID。
            new_agent: 新的 Agent 实例。
        """
        new_id = getattr(new_agent, "id", str(id(new_agent)))
        # 继承旧 Agent 的订阅关系
        old_subs = self.message_bus.subscriptions.pop(old_id, [])
        self.message_bus.subscriptions[new_id] = old_subs
        # 更新频道成员
        for ch_name in old_subs:
            ch = self.message_bus.channels.get(ch_name)
            if ch:
                ch.remove_member(old_id)
                ch.add_member(new_id)
        # 更新部门中的引用
        for dept in self.departments.values():
            if old_id in dept.agents:
                dept.remove_agent(old_id)
                dept.assign_agent(new_id, new_agent)
        # 更新公司注册表
        self.agents.pop(old_id, None)
        self.agents[new_id] = new_agent

    def get_agent(self, agent_id: str) -> Any:
        """根据 ID 获取 Agent 实例。

        Args:
            agent_id: 目标 Agent ID。

        Returns:
            Agent 实例。

        Raises:
            KeyError: 如果 Agent 不存在。
        """
        if agent_id not in self.agents:
            raise KeyError(f"Agent '{agent_id}' 不存在")
        return self.agents[agent_id]

    # ----------------------------------------------------------------
    # 任务执行
    # ----------------------------------------------------------------

    async def execute(self, task: Any) -> Any:
        """执行任务的主循环。

        Args:
            task: 待执行的任务对象（Task）。

        Returns:
            任务执行结果（TaskResult）。

        Note:
            当前为占位实现，后续将实现完整的任务分解、
            分配、执行与汇总流程。
        """
        # TODO: 实现完整的任务执行流程
        # 1. 任务分析与分解
        # 2. 根据治理规则分配到合适的 Agent
        # 3. Agent 间协作执行
        # 4. 结果汇总与质量检查
        raise NotImplementedError("任务执行流程尚未实现")
