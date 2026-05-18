"""治理系统定义。

定义决策类型、决策模型以及组织治理规则，
用于规范 Agent 间的决策流程和权限验证。
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """决策类型枚举。"""

    OPERATIONAL = "operational"  # 操作性决策 - 日常执行层面
    TACTICAL = "tactical"  # 战术性决策 - 项目/迭代层面
    STRATEGIC = "strategic"  # 战略性决策 - 公司方向层面


class DecisionModel(str, Enum):
    """决策模型枚举。"""

    HIERARCHICAL = "hierarchical"  # 层级制 - 上级直接决策
    VOTING = "voting"  # 投票制 - 多数表决
    CONSENSUS = "consensus"  # 共识制 - 全员达成一致
    DELEGATED = "delegated"  # 委托制 - 授权给特定角色


class GovernanceRule(BaseModel):
    """治理规则。

    将决策类型映射到对应的决策模型，并指定参与决策的角色。
    """

    decision_type: DecisionType = Field(..., description="适用的决策类型")
    decision_model: DecisionModel = Field(..., description="采用的决策模型")
    participating_roles: list[str] = Field(
        default_factory=list,
        description="参与决策的角色列表",
    )
    description: str = Field(default="", description="规则说明")


class GovernanceSystem:
    """治理系统。

    管理组织的决策规则和升级路径，
    提供决策模型查询和权限验证功能。
    """

    def __init__(
        self,
        rules: list[GovernanceRule] | None = None,
        escalation_path: list[str] | None = None,
    ) -> None:
        """初始化治理系统。

        Args:
            rules: 治理规则列表。
            escalation_path: 升级路径，角色名称从低到高排列。
        """
        self.rules: list[GovernanceRule] = rules or []
        self.escalation_path: list[str] = escalation_path or []
        # 权限映射缓存：角色名 → 允许的操作列表
        self._authority_cache: dict[str, list[str]] = {}

    def get_decision_model(self, decision_type: DecisionType) -> DecisionModel:
        """根据决策类型获取对应的决策模型。

        Args:
            decision_type: 决策类型。

        Returns:
            对应的决策模型。如果没有匹配的规则，默认返回层级制。
        """
        for rule in self.rules:
            if rule.decision_type == decision_type:
                return rule.decision_model
        # 默认使用层级制决策
        return DecisionModel.HIERARCHICAL

    def validate_authority(self, agent_role: str, action: str) -> bool:
        """验证角色是否有权执行指定操作。

        通过检查治理规则中的参与角色来判断权限。

        Args:
            agent_role: Agent 的角色名称。
            action: 待验证的操作/决策描述。

        Returns:
            True 表示有权限，False 表示无权限。
        """
        # 检查所有规则中是否包含该角色
        for rule in self.rules:
            if agent_role in rule.participating_roles:
                return True
        # 如果角色在升级路径中，且位置越高权限越大
        if agent_role in self.escalation_path:
            return True
        return False

    def register_authority(self, role_name: str, authorities: list[str]) -> None:
        """注册角色的权限列表。

        Args:
            role_name: 角色名称。
            authorities: 允许的操作列表。
        """
        self._authority_cache[role_name] = authorities

    def get_escalation_target(self, current_role: str) -> str | None:
        """获取当前角色的升级目标。

        Args:
            current_role: 当前角色名称。

        Returns:
            升级路径中的上一级角色名称，如果已是最高级则返回 None。
        """
        if current_role not in self.escalation_path:
            return self.escalation_path[0] if self.escalation_path else None
        idx = self.escalation_path.index(current_role)
        if idx + 1 < len(self.escalation_path):
            return self.escalation_path[idx + 1]
        return None
