# -*- coding: utf-8 -*-
"""PerformanceEngine 单元测试 — 验证注册、信号采集、定期评审功能。"""

from __future__ import annotations

import pytest

from agent_company.performance.engine import PerformanceEngine, ReviewResult
from agent_company.performance.scoring import PerformanceGrade, compute_grade


class TestRegisterAgent:
    """测试 Agent 注册到绩效引擎。"""

    def test_register_agent(self) -> None:
        """注册后 tracker 中应包含该 Agent。"""
        engine = PerformanceEngine()
        engine.register_agent("agent-001", role="工程师", name="张三")

        assert "agent-001" in engine.trackers
        assert engine._agent_roles["agent-001"] == "工程师"
        assert engine._agent_names["agent-001"] == "张三"

    def test_register_multiple_agents(self) -> None:
        """注册多个 Agent 后均能正常追踪。"""
        engine = PerformanceEngine()
        engine.register_agent("a1", role="作者", name="A")
        engine.register_agent("a2", role="工程师", name="B")
        engine.register_agent("a3", role="项目经理", name="C")

        assert len(engine.trackers) == 3

    def test_unregister_agent(self) -> None:
        """注销 Agent 后不再追踪。"""
        engine = PerformanceEngine()
        engine.register_agent("agent-001", role="作者", name="X")
        engine.unregister_agent("agent-001")

        assert "agent-001" not in engine.trackers
        assert "agent-001" not in engine._agent_roles


class TestOnTaskComplete:
    """测试任务完成信号处理。"""

    def test_on_task_complete(self) -> None:
        """任务完成信号应记录到 KPI tracker 中。"""
        engine = PerformanceEngine()
        engine.register_agent("agent-001", role="工程师", name="测试")

        engine.on_task_complete("agent-001", quality_score=0.9, on_time=True, tick=1)

        tracker = engine.trackers["agent-001"]
        # 工程师角色有 "代码质量" KPI
        assert tracker.get_latest("代码质量") == 0.9
        assert tracker.get_latest("交付速度") == 1.0
        # 通用 KPI "协作贡献" 也应记录
        assert tracker.get_latest("协作贡献") == 1.0

    def test_on_task_complete_late(self) -> None:
        """任务延迟完成时 on_time=False 应记录较低的交付分。"""
        engine = PerformanceEngine()
        engine.register_agent("agent-001", role="工程师", name="测试")

        engine.on_task_complete("agent-001", quality_score=0.7, on_time=False, tick=1)

        tracker = engine.trackers["agent-001"]
        assert tracker.get_latest("交付速度") == 0.5

    def test_on_task_complete_unknown_agent(self) -> None:
        """对未注册的 Agent 发送信号不应抛出异常。"""
        engine = PerformanceEngine()
        # 不应报错
        engine.on_task_complete("unknown-agent", quality_score=0.8, on_time=True)


class TestPeriodicReview:
    """测试定期评审功能。"""

    def _setup_engine_with_data(self) -> tuple[PerformanceEngine, list[str]]:
        """辅助方法：设置引擎并灌入数据。"""
        engine = PerformanceEngine(review_interval=5)
        agents = ["a1", "a2", "a3"]

        engine.register_agent("a1", role="工程师", name="优秀工程师")
        engine.register_agent("a2", role="作者", name="普通作者")
        engine.register_agent("a3", role="工程师", name="差劲工程师")

        # a1: 高绩效
        for tick in range(5):
            engine.on_task_complete("a1", quality_score=0.95, on_time=True, tick=tick)
            engine.on_message("a1", response_time=1.0, content_length=500, tick=tick)

        # a2: 中等绩效
        for tick in range(5):
            engine.on_task_complete("a2", quality_score=0.7, on_time=True, tick=tick)
            engine.on_message("a2", response_time=3.0, content_length=300, tick=tick)

        # a3: 低绩效
        for tick in range(5):
            engine.on_task_complete("a3", quality_score=0.3, on_time=False, tick=tick)
            engine.on_message("a3", response_time=8.0, content_length=100, tick=tick)

        return engine, agents

    def test_periodic_review_returns_result(self) -> None:
        """定期评审应返回有效的 ReviewResult。"""
        engine, agents = self._setup_engine_with_data()
        result = engine.periodic_review(agents)

        assert isinstance(result, ReviewResult)
        assert len(result.scores) == 3
        assert len(result.rankings) == 3
        assert result.company_score > 0

    def test_periodic_review_ranking_order(self) -> None:
        """评审排名应按总分降序。"""
        engine, agents = self._setup_engine_with_data()
        result = engine.periodic_review(agents)

        for i in range(len(result.rankings) - 1):
            assert result.rankings[i].total_score >= result.rankings[i + 1].total_score

    def test_periodic_review_assigns_ranks(self) -> None:
        """评审应为每个 Agent 分配名次。"""
        engine, agents = self._setup_engine_with_data()
        result = engine.periodic_review(agents)

        ranks = [ps.rank for ps in result.rankings]
        assert ranks == [1, 2, 3]

    def test_periodic_review_generates_feedback(self) -> None:
        """评审应为每个 Agent 生成反馈。"""
        engine, agents = self._setup_engine_with_data()
        result = engine.periodic_review(agents)

        for ps in result.rankings:
            assert ps.feedback != ""

    def test_should_review(self) -> None:
        """should_review 应在达到 review_interval 时返回 True。"""
        engine = PerformanceEngine(review_interval=5)
        assert engine.should_review(0) is False  # 0 - 0 = 0, not >= 5
        assert engine.should_review(3) is False  # 3 - 0 = 3, not >= 5
        assert engine.should_review(5) is True   # 5 - 0 = 5, >= 5


class TestGradeDistribution:
    """测试评级分布和评分等级。"""

    def test_grade_s(self) -> None:
        """分数 >= 90 应评为 S。"""
        assert compute_grade(95) == PerformanceGrade.S
        assert compute_grade(90) == PerformanceGrade.S

    def test_grade_a(self) -> None:
        """分数 80-89 应评为 A。"""
        assert compute_grade(85) == PerformanceGrade.A
        assert compute_grade(80) == PerformanceGrade.A

    def test_grade_b(self) -> None:
        """分数 70-79 应评为 B。"""
        assert compute_grade(75) == PerformanceGrade.B
        assert compute_grade(70) == PerformanceGrade.B

    def test_grade_c(self) -> None:
        """分数 60-69 应评为 C。"""
        assert compute_grade(65) == PerformanceGrade.C
        assert compute_grade(60) == PerformanceGrade.C

    def test_grade_d(self) -> None:
        """分数 50-59 应评为 D。"""
        assert compute_grade(55) == PerformanceGrade.D
        assert compute_grade(50) == PerformanceGrade.D

    def test_grade_f(self) -> None:
        """分数 < 50 应评为 F。"""
        assert compute_grade(49) == PerformanceGrade.F
        assert compute_grade(0) == PerformanceGrade.F
