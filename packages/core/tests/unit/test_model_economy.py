# -*- coding: utf-8 -*-
"""ModelEconomy 单元测试 — 验证模型等级注册、预算策略、能力计算、成本估算。"""

from __future__ import annotations

import pytest

from agent_company.economy.model_tiers import ModelSpec, ModelTier, ModelTierRegistry
from agent_company.economy.budget import BudgetStrategy, CostRecord, ModelBudgetManager
from agent_company.economy.capability import AgentCapability


class TestTierRegistry:
    """测试模型等级注册表。"""

    def test_four_tiers_registered(self) -> None:
        """默认应注册 S/A/B/C 四个等级。"""
        registry = ModelTierRegistry()
        tiers = registry.all_tiers

        assert len(tiers) == 4
        tier_names = {t.tier for t in tiers}
        assert tier_names == {"S", "A", "B", "C"}

    def test_get_tier(self) -> None:
        """按等级名获取应返回正确的 ModelTier。"""
        registry = ModelTierRegistry()

        s_tier = registry.get_tier("S")
        assert isinstance(s_tier, ModelTier)
        assert s_tier.tier == "S"
        assert len(s_tier.models) >= 1

    def test_get_tier_invalid(self) -> None:
        """请求不存在的等级应抛出 KeyError。"""
        registry = ModelTierRegistry()
        with pytest.raises(KeyError, match="未找到等级"):
            registry.get_tier("X")

    def test_get_model(self) -> None:
        """按模型 ID 获取应返回正确的 ModelSpec。"""
        registry = ModelTierRegistry()
        model = registry.get_model("gpt-4o")

        assert model is not None
        assert isinstance(model, ModelSpec)
        assert model.capability > 0
        assert model.cost_per_1k_input >= 0

    def test_get_model_not_found(self) -> None:
        """不存在的模型 ID 应返回 None。"""
        registry = ModelTierRegistry()
        assert registry.get_model("nonexistent-model") is None

    def test_get_tier_for_model(self) -> None:
        """获取模型所属等级应正确。"""
        registry = ModelTierRegistry()
        assert registry.get_tier_for_model("claude-opus-4-6") == "S"
        assert registry.get_tier_for_model("gpt-4o-mini") == "A"

    def test_get_models_by_tier(self) -> None:
        """按等级获取模型列表应返回该等级的所有模型。"""
        registry = ModelTierRegistry()
        b_models = registry.get_models_by_tier("B")

        assert len(b_models) >= 1
        for m in b_models:
            assert isinstance(m, ModelSpec)

    def test_get_cheapest_model(self) -> None:
        """获取最便宜模型应返回成本最低的。"""
        registry = ModelTierRegistry()
        cheapest = registry.get_cheapest_model(min_capability=0)

        assert isinstance(cheapest, ModelSpec)
        # 本地模型成本为 0
        assert cheapest.cost_per_1k_input + cheapest.cost_per_1k_output == 0.0

    def test_get_cheapest_model_with_min_capability(self) -> None:
        """设置最低能力要求后应筛除低能力模型。"""
        registry = ModelTierRegistry()
        model = registry.get_cheapest_model(min_capability=80)

        assert model.capability >= 80

    def test_all_models_property(self) -> None:
        """all_models 属性应返回所有注册模型。"""
        registry = ModelTierRegistry()
        all_models = registry.all_models

        # S(2) + A(2) + B(2) + C(2) = 8 个模型
        assert len(all_models) == 8


class TestBudgetStrategies:
    """测试三种预算分配策略。"""

    def _get_roles(self) -> list[dict]:
        """标准测试角色列表。"""
        return [
            {"role": "主编", "priority": "critical"},
            {"role": "开发工程师", "priority": "medium"},
            {"role": "校对", "priority": "support"},
        ]

    def test_quality_first_strategy(self) -> None:
        """质量优先策略应为高优先级角色分配顶级模型。"""
        registry = ModelTierRegistry()
        manager = ModelBudgetManager(total_budget=100.0, strategy=BudgetStrategy.QUALITY_FIRST)
        roles = self._get_roles()

        allocation = manager.allocate_models(roles, registry)

        assert len(allocation) == 3
        # critical 角色应得到 S 级模型
        critical_model = registry.get_model(allocation["主编"])
        assert critical_model is not None
        s_tier = registry.get_tier("S")
        assert critical_model.id in [m.id for m in s_tier.models]

    def test_cost_first_strategy(self) -> None:
        """成本优先策略应为所有角色分配最便宜的模型。"""
        registry = ModelTierRegistry()
        manager = ModelBudgetManager(total_budget=10.0, strategy=BudgetStrategy.COST_FIRST)
        roles = self._get_roles()

        allocation = manager.allocate_models(roles, registry)

        # 所有角色应分配同一个最便宜的模型
        model_ids = set(allocation.values())
        assert len(model_ids) == 1  # 全部相同

        cheapest = registry.get_cheapest_model()
        assert list(model_ids)[0] == cheapest.id

    def test_balanced_strategy(self) -> None:
        """平衡策略应根据优先级分配合理等级。"""
        registry = ModelTierRegistry()
        manager = ModelBudgetManager(total_budget=50.0, strategy=BudgetStrategy.BALANCED)
        roles = self._get_roles()

        allocation = manager.allocate_models(roles, registry)

        assert len(allocation) == 3
        # critical 应得到 S 级
        critical_tier = registry.get_tier_for_model(allocation["主编"])
        assert critical_tier == "S"

    def test_budget_tracking(self) -> None:
        """记录成本后能正确追踪花费和余额。"""
        manager = ModelBudgetManager(total_budget=100.0, strategy=BudgetStrategy.BALANCED)

        assert manager.get_spent() == 0.0
        assert manager.get_remaining() == 100.0

        manager.record_cost(CostRecord(
            agent_id="a1",
            model_id="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
        ))
        manager.record_cost(CostRecord(
            agent_id="a2",
            model_id="gpt-4o-mini",
            input_tokens=2000,
            output_tokens=1000,
            cost_usd=0.01,
        ))

        assert manager.get_spent() == pytest.approx(0.06)
        assert manager.get_remaining() == pytest.approx(99.94)

    def test_get_cost_by_agent(self) -> None:
        """按 Agent 查询累计花费应正确。"""
        manager = ModelBudgetManager(total_budget=100.0, strategy=BudgetStrategy.BALANCED)

        manager.record_cost(CostRecord(
            agent_id="a1", model_id="m1", input_tokens=100, output_tokens=50, cost_usd=0.03,
        ))
        manager.record_cost(CostRecord(
            agent_id="a1", model_id="m1", input_tokens=200, output_tokens=100, cost_usd=0.05,
        ))
        manager.record_cost(CostRecord(
            agent_id="a2", model_id="m2", input_tokens=100, output_tokens=50, cost_usd=0.02,
        ))

        assert manager.get_cost_by_agent("a1") == pytest.approx(0.08)
        assert manager.get_cost_by_agent("a2") == pytest.approx(0.02)

    def test_can_upgrade(self) -> None:
        """绩效优秀且预算充足时 can_upgrade 返回 True。"""
        manager = ModelBudgetManager(total_budget=100.0, strategy=BudgetStrategy.BALANCED)
        assert manager.can_upgrade("a1", current_performance=90) is True
        assert manager.can_upgrade("a1", current_performance=70) is False

    def test_should_downgrade(self) -> None:
        """绩效差时 should_downgrade 返回 True。"""
        manager = ModelBudgetManager(total_budget=100.0, strategy=BudgetStrategy.BALANCED)
        assert manager.should_downgrade("a1", current_performance=50) is True
        assert manager.should_downgrade("a1", current_performance=75) is False

    def test_budget_report(self) -> None:
        """预算报告应包含关键字段。"""
        manager = ModelBudgetManager(total_budget=100.0, strategy=BudgetStrategy.BALANCED)
        manager.record_cost(CostRecord(
            agent_id="a1", model_id="gpt-4o", input_tokens=1000, output_tokens=500, cost_usd=0.05,
        ))

        report = manager.get_budget_report()

        assert report["total_budget"] == 100.0
        assert report["spent"] == 0.05
        assert report["strategy"] == "balanced"
        assert "a1" in report["cost_by_agent"]
        assert "gpt-4o" in report["cost_by_model"]


class TestCapabilityCalculation:
    """测试 Agent 能力分计算。"""

    def test_effective_skills(self) -> None:
        """实际能力 = base × (model_capability / 100)。"""
        model = ModelSpec(
            id="test-model",
            capability=80,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
        )
        cap = AgentCapability(
            base_skills={"python": 0.9, "coding": 0.8},
            model_spec=model,
        )

        effective = cap.effective_skills
        assert effective["python"] == pytest.approx(0.9 * 0.8, abs=0.001)
        assert effective["coding"] == pytest.approx(0.8 * 0.8, abs=0.001)

    def test_effective_skills_with_full_capability(self) -> None:
        """capability=100 时实际能力 = 基础技能原值。"""
        model = ModelSpec(
            id="perfect-model",
            capability=100,
            cost_per_1k_input=0.05,
            cost_per_1k_output=0.15,
        )
        cap = AgentCapability(
            base_skills={"writing": 0.95},
            model_spec=model,
        )

        effective = cap.effective_skills
        assert effective["writing"] == pytest.approx(0.95, abs=0.001)

    def test_avg_capability(self) -> None:
        """平均有效能力分应为所有技能的均值。"""
        model = ModelSpec(id="m", capability=80, cost_per_1k_input=0, cost_per_1k_output=0)
        cap = AgentCapability(
            base_skills={"a": 1.0, "b": 0.5},
            model_spec=model,
        )

        # effective: a=0.8, b=0.4 => avg=0.6
        assert cap.avg_capability == pytest.approx(0.6, abs=0.01)

    def test_avg_capability_empty_skills(self) -> None:
        """空技能字典时平均能力应为 0。"""
        model = ModelSpec(id="m", capability=80, cost_per_1k_input=0, cost_per_1k_output=0)
        cap = AgentCapability(base_skills={}, model_spec=model)

        assert cap.avg_capability == 0.0


class TestCostEstimation:
    """测试成本估算。"""

    def test_estimate_hourly_cost(self) -> None:
        """每小时成本估算应基于 token 用量和模型定价。"""
        model = ModelSpec(
            id="test-model",
            capability=85,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        )
        cap = AgentCapability(base_skills={"coding": 0.9}, model_spec=model)

        # avg_tokens_per_call=1000, calls_per_hour=10
        # 每次: input=500 tokens, output=500 tokens
        # cost_per_call = 0.003 * 500/1000 + 0.015 * 500/1000 = 0.0015 + 0.0075 = 0.009
        # hourly = 0.009 * 10 = 0.09
        cost = cap.estimate_hourly_cost(avg_tokens_per_call=1000, calls_per_hour=10)
        assert cost == pytest.approx(0.09, abs=0.001)

    def test_estimate_hourly_cost_free_model(self) -> None:
        """免费本地模型的每小时成本应为 0。"""
        model = ModelSpec(
            id="local-model",
            capability=70,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        )
        cap = AgentCapability(base_skills={"coding": 0.8}, model_spec=model)

        cost = cap.estimate_hourly_cost()
        assert cost == 0.0

    def test_estimate_hourly_cost_scaling(self) -> None:
        """调用次数增加应线性增加成本。"""
        model = ModelSpec(
            id="test-model",
            capability=85,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
        )
        cap = AgentCapability(base_skills={"coding": 0.9}, model_spec=model)

        cost_10 = cap.estimate_hourly_cost(calls_per_hour=10)
        cost_20 = cap.estimate_hourly_cost(calls_per_hour=20)

        assert cost_20 == pytest.approx(cost_10 * 2, abs=0.0001)
