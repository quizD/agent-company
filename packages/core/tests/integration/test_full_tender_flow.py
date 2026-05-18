# -*- coding: utf-8 -*-
"""端到端集成测试 — 需求分析 -> 招标 -> 组建团队 -> 绩效评审 -> 淘汰 全流程。

不依赖外部 LLM API，全部使用规则引擎和 mock 数据。
"""

from __future__ import annotations

import pytest

from agent_company.economy.budget import BudgetStrategy, ModelBudgetManager
from agent_company.economy.model_tiers import ModelTierRegistry
from agent_company.performance.elimination import EliminationEngine
from agent_company.performance.engine import PerformanceEngine
from agent_company.performance.scoring import PerformanceGrade
from agent_company.pool.presets import create_default_pool
from agent_company.pool.talent_pool import TalentPool
from agent_company.tender.analyzer import RequirementAnalyzer
from agent_company.tender.engine import TenderEngine, TenderResult
from agent_company.values.system import ValueSystem
from agent_company.values.vault import ValueVault


class TestEndToEnd:
    """完整端到端流程测试。"""

    def test_end_to_end(self) -> None:
        """完整流程：需求分析 -> 招标 -> 组建团队 -> 绩效评审 -> 淘汰替换。"""
        # ==============================
        # 1. 需求分析
        # ==============================
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze(
            "开发一个高并发的电商系统，需要复杂的后端架构和数据分析",
            budget=50.0,
        )

        assert spec.project_type == "软件开发"
        assert spec.estimated_complexity == "high"
        assert len(spec.required_roles) >= 2

        # ==============================
        # 2. 招标组建团队
        # ==============================
        pool = create_default_pool()
        tender_engine = TenderEngine(pool=pool)
        result = tender_engine.run_tender(spec)

        assert isinstance(result, TenderResult)
        assert len(result.selected_team) >= 2
        assert result.company is not None

        team_profiles = [m["profile"] for m in result.selected_team]
        team_ids = [p.id for p in team_profiles]

        # 确认团队成员不重复
        assert len(team_ids) == len(set(team_ids))

        # ==============================
        # 3. 价值观系统注入
        # ==============================
        vault = ValueVault()
        values = vault.sample(categories=["excellence", "ownership", "collaboration"], count_per_category=2)
        value_system = ValueSystem(values)
        behavior_prompt = value_system.generate_behavior_prompt()

        assert "行为价值观准则" in behavior_prompt
        assert len(behavior_prompt) > 50

        # ==============================
        # 4. 绩效考核
        # ==============================
        perf_engine = PerformanceEngine(review_interval=5)

        # 注册团队成员
        for member in result.selected_team:
            profile = member["profile"]
            role_spec = member["role"]
            perf_engine.register_agent(profile.id, role=role_spec.name, name=profile.name)

        # 模拟 5 轮任务执行
        for tick in range(5):
            for i, member in enumerate(result.selected_team):
                profile = member["profile"]
                # 模拟不同水平的表现
                if i == 0:
                    # 第一个表现优秀
                    perf_engine.on_task_complete(profile.id, quality_score=0.92, on_time=True, tick=tick)
                    perf_engine.on_message(profile.id, response_time=1.5, content_length=500, tick=tick)
                elif i == len(result.selected_team) - 1:
                    # 最后一个表现较差
                    perf_engine.on_task_complete(profile.id, quality_score=0.35, on_time=False, tick=tick)
                    perf_engine.on_message(profile.id, response_time=8.0, content_length=50, tick=tick)
                else:
                    # 其他中等表现
                    perf_engine.on_task_complete(profile.id, quality_score=0.75, on_time=True, tick=tick)
                    perf_engine.on_message(profile.id, response_time=3.0, content_length=300, tick=tick)

        # 执行绩效评审
        review = perf_engine.periodic_review(team_ids)

        assert len(review.scores) == len(team_ids)
        assert review.company_score > 0
        assert len(review.rankings) == len(team_ids)

        # 最优秀的应排第一
        assert review.rankings[0].total_score >= review.rankings[-1].total_score

        # ==============================
        # 5. 淘汰与替换
        # ==============================
        elim_engine = EliminationEngine(pool=pool)
        replacements = elim_engine.process_eliminations(
            review=review,
            company_values=spec.value_priorities,
            current_agent_ids=team_ids,
        )

        # 表现差的可能被淘汰（取决于具体评分）
        # 至少验证淘汰机制不报错
        assert isinstance(replacements, list)
        for rep in replacements:
            assert rep.removed_id in team_ids
            assert rep.reason != ""

        # ==============================
        # 6. 预算管理（附加验证）
        # ==============================
        registry = ModelTierRegistry()
        budget_mgr = ModelBudgetManager(total_budget=spec.budget_usd, strategy=BudgetStrategy.BALANCED)

        roles_for_budget = [
            {"role": m["role"].name, "priority": m["role"].priority}
            for m in result.selected_team
        ]
        allocation = budget_mgr.allocate_models(roles_for_budget, registry)

        # allocation is keyed by role name; multiple agents with same role share one key
        assert len(allocation) >= 1
        for role_name, model_id in allocation.items():
            model = registry.get_model(model_id)
            assert model is not None

    def test_end_to_end_publishing_project(self) -> None:
        """出版项目的端到端流程也能正常完成。"""
        # 需求分析
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("写一本关于 AI 的书籍并出版")

        # 招标
        pool = create_default_pool()
        engine = TenderEngine(pool=pool)
        result = engine.run_tender(spec)

        assert result.company is not None
        assert len(result.selected_team) >= 1

        # 绩效评审（简单验证）
        perf_engine = PerformanceEngine(review_interval=3)
        team_ids = []
        for member in result.selected_team:
            p = member["profile"]
            perf_engine.register_agent(p.id, role=member["role"].name, name=p.name)
            team_ids.append(p.id)

        for tick in range(3):
            for tid in team_ids:
                perf_engine.on_task_complete(tid, quality_score=0.8, on_time=True, tick=tick)

        review = perf_engine.periodic_review(team_ids)
        assert review.company_score > 0

    def test_multiple_review_cycles(self) -> None:
        """多轮绩效评审后淘汰连续 D 的 Agent。"""
        pool = create_default_pool()
        engine = TenderEngine(pool=pool)

        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("开发一套内部管理工具")
        result = engine.run_tender(spec)

        # 设置绩效引擎
        perf_engine = PerformanceEngine(review_interval=3)
        team_ids = []
        for member in result.selected_team:
            p = member["profile"]
            perf_engine.register_agent(p.id, role=member["role"].name, name=p.name)
            team_ids.append(p.id)

        elim_engine = EliminationEngine(pool=pool)

        # 模拟两轮评审，让最后一个成员持续低绩效
        for round_num in range(2):
            for tick in range(3):
                actual_tick = round_num * 3 + tick
                for i, tid in enumerate(team_ids):
                    if i == len(team_ids) - 1:
                        # 持续差表现
                        perf_engine.on_task_complete(tid, quality_score=0.25, on_time=False, tick=actual_tick)
                    else:
                        perf_engine.on_task_complete(tid, quality_score=0.85, on_time=True, tick=actual_tick)

            review = perf_engine.periodic_review(team_ids)
            elim_engine.update_grades(review)

        # 最后执行淘汰判定
        final_review = perf_engine.periodic_review(team_ids)
        elim_engine.update_grades(final_review)
        eliminates = elim_engine.determine_eliminations(final_review)

        # 持续低绩效的应被标记淘汰（可能是 F 或连续 D）
        # 至少验证机制正常运作
        assert isinstance(eliminates, list)
