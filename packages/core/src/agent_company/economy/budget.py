"""预算管理——像真实公司的薪资预算一样管理模型调用支出。"""

from __future__ import annotations

import time
from enum import Enum

from pydantic import BaseModel, Field

from agent_company.economy.model_tiers import ModelTierRegistry


class BudgetStrategy(str, Enum):
    """预算分配策略。"""

    QUALITY_FIRST = "quality_first"  # 质量优先：尽量用好模型
    COST_FIRST = "cost_first"  # 成本优先：尽量省钱
    BALANCED = "balanced"  # 平衡策略：在预算内追求最优性价比


class CostRecord(BaseModel):
    """单次调用的成本记录。"""

    agent_id: str = Field(description="Agent 唯一标识")
    model_id: str = Field(description="使用的模型 ID")
    input_tokens: int = Field(ge=0, description="输入 token 数")
    output_tokens: int = Field(ge=0, description="输出 token 数")
    cost_usd: float = Field(ge=0, description="本次调用成本（美元）")
    timestamp: float = Field(default_factory=time.time, description="记录时间戳")


# 角色优先级到权重的映射
_PRIORITY_WEIGHTS: dict[str, float] = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "support": 0.25,
    "low": 0.15,
}


class ModelBudgetManager:
    """项目预算管理器——像真实公司的薪资预算。

    根据策略在预算约束下为角色分配最优模型，并跟踪开支。
    """

    def __init__(
        self,
        total_budget: float,
        strategy: BudgetStrategy = BudgetStrategy.BALANCED,
    ) -> None:
        """初始化预算管理器。

        Args:
            total_budget: 项目总预算（美元）
            strategy: 预算分配策略
        """
        self._total_budget = total_budget
        self._strategy = strategy
        self._records: list[CostRecord] = []

    @property
    def total_budget(self) -> float:
        """总预算。"""
        return self._total_budget

    @property
    def strategy(self) -> BudgetStrategy:
        """当前策略。"""
        return self._strategy

    def allocate_models(
        self,
        roles: list[dict],
        registry: ModelTierRegistry,
    ) -> dict[str, str]:
        """在预算内为每个角色分配最优模型。

        Args:
            roles: 角色列表，每项包含 role（角色名）和 priority（优先级）
                   例: [{"role": "主编", "priority": "critical"}, {"role": "校对", "priority": "support"}]
            registry: 模型等级注册表

        Returns:
            角色到模型 ID 的映射字典
        """
        allocation: dict[str, str] = {}

        if self._strategy == BudgetStrategy.COST_FIRST:
            # 成本优先：所有角色都用最便宜的模型
            cheapest = registry.get_cheapest_model(min_capability=0)
            for role_info in roles:
                allocation[role_info["role"]] = cheapest.id
            return allocation

        if self._strategy == BudgetStrategy.QUALITY_FIRST:
            # 质量优先：按优先级分配最好的模型
            tier_map = {"critical": "S", "high": "S", "medium": "A", "support": "B", "low": "C"}
            for role_info in roles:
                priority = role_info.get("priority", "medium")
                target_tier = tier_map.get(priority, "B")
                models = registry.get_models_by_tier(target_tier)
                if models:
                    # 选能力最高的
                    best = max(models, key=lambda m: m.capability)
                    allocation[role_info["role"]] = best.id
                else:
                    allocation[role_info["role"]] = registry.get_cheapest_model().id
            return allocation

        # 平衡策略：根据优先级权重分配合理等级
        tier_map_balanced = {"critical": "S", "high": "A", "medium": "B", "support": "B", "low": "C"}
        for role_info in roles:
            priority = role_info.get("priority", "medium")
            target_tier = tier_map_balanced.get(priority, "B")
            models = registry.get_models_by_tier(target_tier)
            if models:
                # 平衡策略下选性价比最高的（能力/成本比）
                best = max(
                    models,
                    key=lambda m: m.capability / max(m.cost_per_1k_input + m.cost_per_1k_output, 0.0001),
                )
                allocation[role_info["role"]] = best.id
            else:
                allocation[role_info["role"]] = registry.get_cheapest_model().id

        return allocation

    def record_cost(self, record: CostRecord) -> None:
        """记录一次调用的成本。"""
        self._records.append(record)

    def get_spent(self) -> float:
        """获取已花费总额。"""
        return sum(r.cost_usd for r in self._records)

    def get_remaining(self) -> float:
        """获取剩余预算。"""
        return self._total_budget - self.get_spent()

    def get_cost_by_agent(self, agent_id: str) -> float:
        """获取某个 Agent 的累计花费。"""
        return sum(r.cost_usd for r in self._records if r.agent_id == agent_id)

    def can_upgrade(self, agent_id: str, current_performance: float) -> bool:
        """判断是否可以升级模型。

        条件：绩效优秀 (>=85) 且剩余预算充足 (>30%)。
        """
        budget_ratio = self.get_remaining() / max(self._total_budget, 0.01)
        return current_performance >= 85 and budget_ratio > 0.3

    def should_downgrade(self, agent_id: str, current_performance: float) -> bool:
        """判断是否应该降级模型。

        条件：绩效差 (<60)，降级可以节省预算给其他角色。
        """
        return current_performance < 60

    def get_budget_report(self) -> dict:
        """返回预算使用报告。"""
        spent = self.get_spent()
        remaining = self.get_remaining()

        # 按 Agent 汇总
        agent_costs: dict[str, float] = {}
        for record in self._records:
            agent_costs[record.agent_id] = agent_costs.get(record.agent_id, 0.0) + record.cost_usd

        # 按模型汇总
        model_costs: dict[str, float] = {}
        for record in self._records:
            model_costs[record.model_id] = model_costs.get(record.model_id, 0.0) + record.cost_usd

        return {
            "total_budget": self._total_budget,
            "spent": round(spent, 6),
            "remaining": round(remaining, 6),
            "usage_ratio": round(spent / max(self._total_budget, 0.01), 4),
            "strategy": self._strategy.value,
            "total_records": len(self._records),
            "cost_by_agent": agent_costs,
            "cost_by_model": model_costs,
        }
