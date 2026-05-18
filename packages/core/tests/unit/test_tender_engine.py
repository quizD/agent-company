# -*- coding: utf-8 -*-
"""TenderEngine 单元测试 — 验证需求分析、评分矩阵、完整招标流程。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent_company.pool.profile import AgentProfile
from agent_company.pool.presets import create_default_pool
from agent_company.pool.talent_pool import TalentPool
from agent_company.tender.analyzer import RequirementAnalyzer, RoleSpec, TenderSpec
from agent_company.tender.scoring import BidScore, ScoringMatrix
from agent_company.tender.engine import TenderEngine, TenderResult


class TestRequirementAnalysis:
    """测试需求分析模块。"""

    def test_analyze_software_project(self) -> None:
        """软件开发需求应识别为 software 类型并生成正确的 TenderSpec。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("开发一个用户管理系统的 API 接口", budget=20.0)

        assert spec.project_type == "软件开发"
        assert spec.budget_usd == 20.0
        assert len(spec.required_roles) > 0
        assert any(r.name == "技术负责人" for r in spec.required_roles)
        assert "源代码" in spec.deliverables

    def test_analyze_publishing_project(self) -> None:
        """写作/出版需求应识别为 publishing 类型。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("写一本关于 AI 的技术书籍，需要编辑审核")

        assert spec.project_type == "内容出版"
        assert any(r.name == "主编" for r in spec.required_roles)
        assert any(r.name == "作者" for r in spec.required_roles)

    def test_analyze_consulting_project(self) -> None:
        """咨询类需求应识别为 consulting 类型。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("我需要一份市场分析报告和竞争策略咨询")

        assert spec.project_type == "咨询项目"
        assert any(r.name == "分析师" for r in spec.required_roles)

    def test_analyze_design_project(self) -> None:
        """设计类需求应识别为 design 类型。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("设计一套全新的品牌 UI 界面")

        assert spec.project_type == "设计项目"
        assert any(r.name == "设计总监" for r in spec.required_roles)

    def test_complexity_detection_high(self) -> None:
        """包含复杂度关键词应识别为 high。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("开发一个大规模分布式系统")
        assert spec.estimated_complexity == "high"

    def test_complexity_detection_low(self) -> None:
        """包含简单关键词应识别为 low。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("写一个简单的原型 app")
        assert spec.estimated_complexity == "low"

    def test_default_project_type(self) -> None:
        """无法识别类型时默认为 software。"""
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("做一件很酷的事情")
        assert spec.project_type == "软件开发"


class TestScoringMatrix:
    """测试评分矩阵计算。"""

    def test_score_candidate_basic(self, sample_profiles: list[AgentProfile]) -> None:
        """基本评分流程应返回有效的 BidScore。"""
        matrix = ScoringMatrix()
        engineer = sample_profiles[1]  # 测试工程师
        role_spec = RoleSpec(
            name="开发工程师",
            must_have_skills=["python", "coding"],
            nice_to_have=["testing"],
            priority="core",
            min_model_tier="B",
        )

        score = matrix.score_candidate(
            profile=engineer,
            role_spec=role_spec,
            project_values=["代码质量"],
            existing_team=[],
        )

        assert isinstance(score, BidScore)
        assert score.agent_id == engineer.id
        assert score.agent_name == engineer.name
        assert score.total_score > 0
        assert 0 <= score.skill_match <= 100
        assert 0 <= score.performance <= 100
        assert 0 <= score.value_alignment <= 100
        assert 0 <= score.team_compatibility <= 100
        assert 0 <= score.model_efficiency <= 100

    def test_skill_match_higher_for_matching_skills(
        self, sample_profiles: list[AgentProfile]
    ) -> None:
        """技能匹配度高的 Agent 应获得更高的 skill_match 分。"""
        matrix = ScoringMatrix()
        engineer = sample_profiles[1]  # 有 python 技能
        junior = sample_profiles[3]  # python 技能较低

        role_spec = RoleSpec(
            name="Python工程师",
            must_have_skills=["python"],
            priority="core",
            min_model_tier="C",
        )

        score_engineer = matrix.score_candidate(engineer, role_spec, [], [])
        score_junior = matrix.score_candidate(junior, role_spec, [], [])

        assert score_engineer.skill_match > score_junior.skill_match

    def test_rank_candidates(self, sample_profiles: list[AgentProfile]) -> None:
        """rank_candidates 应按总分降序排列。"""
        matrix = ScoringMatrix()
        role_spec = RoleSpec(
            name="开发",
            must_have_skills=["coding"],
            priority="core",
            min_model_tier="C",
        )

        scores = [
            matrix.score_candidate(p, role_spec, [], [])
            for p in sample_profiles
        ]

        ranked = matrix.rank_candidates(scores)
        for i in range(len(ranked) - 1):
            assert ranked[i].total_score >= ranked[i + 1].total_score

    def test_team_compatibility_with_existing_team(
        self, sample_profiles: list[AgentProfile]
    ) -> None:
        """有已有团队成员时，团队兼容性评分应反映互补性。"""
        matrix = ScoringMatrix()
        candidate = sample_profiles[0]  # writer, independent
        existing_team = [sample_profiles[1]]  # engineer, independent

        role_spec = RoleSpec(
            name="写手",
            must_have_skills=["creative_writing"],
            priority="core",
            min_model_tier="B",
        )

        score_alone = matrix.score_candidate(candidate, role_spec, [], [])
        score_with_team = matrix.score_candidate(candidate, role_spec, [], existing_team)

        # 两种情况下都应返回有效分数
        assert score_alone.team_compatibility > 0
        assert score_with_team.team_compatibility > 0

    def test_model_efficiency_below_threshold(self) -> None:
        """模型等级不满足最低要求时效率分应大幅扣分。"""
        matrix = ScoringMatrix()
        low_tier_agent = AgentProfile(
            id="low-tier",
            name="低配Agent",
            category="engineer",
            skills={"coding": 0.9},
            model_tier="C",
        )
        role_spec = RoleSpec(
            name="架构师",
            must_have_skills=["coding"],
            priority="critical",
            min_model_tier="A",  # 要求 A 级
        )

        score = matrix.score_candidate(low_tier_agent, role_spec, [], [])
        assert score.model_efficiency == 20.0  # 不满足时固定为 20


class TestRunTender:
    """测试完整招标流程。"""

    def test_run_tender_with_preset_pool(self) -> None:
        """使用预设人才池执行完整招标流程应成功组建团队。"""
        pool = create_default_pool()
        engine = TenderEngine(pool=pool)

        spec = TenderSpec(
            project_type="软件开发",
            description="开发一个内容管理系统",
            deliverables=["源代码", "文档"],
            required_roles=[
                RoleSpec(
                    name="技术负责人",
                    must_have_skills=["architecture", "python"],
                    priority="critical",
                    min_model_tier="A",
                ),
                RoleSpec(
                    name="开发工程师",
                    count=2,
                    must_have_skills=["coding", "python"],
                    priority="core",
                    min_model_tier="B",
                ),
            ],
            value_priorities=["代码质量", "质量"],
            budget_usd=30.0,
        )

        result = engine.run_tender(spec)

        assert isinstance(result, TenderResult)
        assert len(result.selected_team) > 0
        assert result.company is not None
        assert len(result.tender_log) > 0
        # 确保没有重复选入同一个 Agent
        selected_ids = [m["profile"].id for m in result.selected_team]
        assert len(selected_ids) == len(set(selected_ids))

    def test_run_tender_publishing(self) -> None:
        """出版类招标也能正常完成。"""
        pool = create_default_pool()
        engine = TenderEngine(pool=pool)

        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze("出版一本 AI 技术书籍，需要高质量的内容和严格编辑")

        result = engine.run_tender(spec)

        assert isinstance(result, TenderResult)
        assert result.company is not None
        assert "招标启动" in result.tender_log[0]
