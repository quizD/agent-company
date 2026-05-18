# -*- coding: utf-8 -*-
"""EliminationEngine 单元测试 — 验证淘汰规则和替补机制。"""

from __future__ import annotations

import pytest

from agent_company.performance.engine import ReviewResult
from agent_company.performance.elimination import EliminationEngine, Replacement
from agent_company.performance.scoring import PerformanceGrade, PerformanceScore
from agent_company.pool.profile import AgentProfile, ProjectRecord
from agent_company.pool.talent_pool import TalentPool


def _make_review(scores_data: list[dict]) -> ReviewResult:
    """辅助函数：快速构建 ReviewResult。

    scores_data: [{"id": ..., "name": ..., "role": ..., "score": ..., "grade": ..., "trend": ...}]
    """
    scores: dict[str, PerformanceScore] = {}
    for d in scores_data:
        ps = PerformanceScore(
            agent_id=d["id"],
            agent_name=d["name"],
            role=d.get("role", "通用"),
            total_score=d["score"],
            grade=PerformanceGrade(d["grade"]),
            trend=d.get("trend", "stable"),
        )
        scores[d["id"]] = ps

    rankings = sorted(scores.values(), key=lambda s: s.total_score, reverse=True)
    return ReviewResult(scores=scores, rankings=rankings)


def _make_pool_with_replacement() -> TalentPool:
    """创建包含替补候选人的人才池。"""
    pool = TalentPool()
    pool.register(
        AgentProfile(
            id="replacement-001",
            name="替补工程师",
            category="engineer",
            skills={"python": 0.85, "coding": 0.82},
            specializations=["后端开发"],
            reliability_score=0.88,
            collaboration_score=0.8,
            model_tier="A",
            project_history=[
                ProjectRecord(project_id="p1", role="开发", score=0.85, result="完成"),
            ],
        )
    )
    pool.register(
        AgentProfile(
            id="replacement-002",
            name="替补作者",
            category="writer",
            skills={"creative_writing": 0.88, "editing": 0.8},
            specializations=["创意写作"],
            reliability_score=0.85,
            collaboration_score=0.82,
            model_tier="A",
            project_history=[
                ProjectRecord(project_id="p2", role="作者", score=0.82, result="完成"),
            ],
        )
    )
    return pool


class TestSingleFElimination:
    """测试单次 F 评级立即淘汰。"""

    def test_single_f_elimination(self) -> None:
        """单次 F 评级应触发立即淘汰。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        review = _make_review([
            {"id": "bad-agent", "name": "差Agent", "role": "工程师", "score": 40, "grade": "F"},
            {"id": "good-agent", "name": "好Agent", "role": "工程师", "score": 85, "grade": "A"},
        ])

        engine.update_grades(review)
        eliminates = engine.determine_eliminations(review)

        assert "bad-agent" in eliminates
        assert "good-agent" not in eliminates

    def test_f_grade_replacement(self) -> None:
        """F 评级触发淘汰后应能从池中找到替补。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        review = _make_review([
            {"id": "bad-agent", "name": "差Agent", "role": "工程师", "score": 40, "grade": "F"},
        ])

        replacements = engine.process_eliminations(
            review,
            company_values=["代码质量"],
            current_agent_ids=["bad-agent"],
        )

        assert len(replacements) == 1
        assert replacements[0].removed_id == "bad-agent"
        assert replacements[0].reason == "单次绩效评级 F（不合格），触发立即淘汰"
        assert replacements[0].replaced_by_id == "replacement-001"


class TestConsecutiveDElimination:
    """测试连续 2 次 D 评级淘汰。"""

    def test_consecutive_d_elimination(self) -> None:
        """连续 2 次 D 评级应触发淘汰。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        # 第一次评审：D
        review1 = _make_review([
            {"id": "d-agent", "name": "D-Agent", "role": "工程师", "score": 55, "grade": "D"},
        ])
        engine.update_grades(review1)
        elim1 = engine.determine_eliminations(review1)
        assert "d-agent" not in elim1  # 第一次 D 不淘汰

        # 第二次评审：再次 D
        review2 = _make_review([
            {"id": "d-agent", "name": "D-Agent", "role": "工程师", "score": 52, "grade": "D"},
        ])
        engine.update_grades(review2)
        elim2 = engine.determine_eliminations(review2)
        assert "d-agent" in elim2  # 连续 2 次 D 触发淘汰

    def test_single_d_no_elimination(self) -> None:
        """仅单次 D 评级不应触发淘汰。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        review = _make_review([
            {"id": "d-agent", "name": "D-Agent", "role": "工程师", "score": 55, "grade": "D"},
        ])
        engine.update_grades(review)
        eliminates = engine.determine_eliminations(review)

        assert "d-agent" not in eliminates


class TestNoEliminationOnGoodGrades:
    """测试好成绩不会触发淘汰。"""

    def test_no_elimination_on_good_grades(self) -> None:
        """S/A/B 评级不应触发淘汰。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        review = _make_review([
            {"id": "s-agent", "name": "S-Agent", "role": "工程师", "score": 95, "grade": "S"},
            {"id": "a-agent", "name": "A-Agent", "role": "作者", "score": 82, "grade": "A"},
            {"id": "b-agent", "name": "B-Agent", "role": "分析师", "score": 72, "grade": "B"},
        ])
        engine.update_grades(review)
        eliminates = engine.determine_eliminations(review)

        assert len(eliminates) == 0

    def test_no_elimination_on_single_c(self) -> None:
        """单次或两次 C 评级不应触发淘汰。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        # 两次 C
        for _ in range(2):
            review = _make_review([
                {"id": "c-agent", "name": "C-Agent", "role": "工程师", "score": 63, "grade": "C"},
            ])
            engine.update_grades(review)

        review_final = _make_review([
            {"id": "c-agent", "name": "C-Agent", "role": "工程师", "score": 63, "grade": "C"},
        ])
        # 不再 update_grades，用当前状态判断
        eliminates = engine.determine_eliminations(review_final)
        # 只有 2 次 C 不够，需要 3 次
        assert "c-agent" not in eliminates


class TestReplacementFromPool:
    """测试淘汰后从人才池找替补。"""

    def test_replacement_from_pool(self) -> None:
        """淘汰后应从人才池中按角色匹配找到最佳替补。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        replacement = engine.find_replacement(
            role="engineer",
            company_values=[],
            exclude_ids=[],
        )

        assert replacement is not None
        assert replacement.id == "replacement-001"
        assert replacement.category == "engineer"

    def test_replacement_excludes_current_team(self) -> None:
        """替补搜索应排除当前团队成员。"""
        pool = _make_pool_with_replacement()
        engine = EliminationEngine(pool=pool)

        replacement = engine.find_replacement(
            role="engineer",
            company_values=[],
            exclude_ids=["replacement-001"],
        )

        # 排除了唯一的工程师替补，应找不到或找到其他类型
        if replacement is not None:
            assert replacement.id != "replacement-001"

    def test_no_replacement_available(self) -> None:
        """人才池无可用替补时返回 None。"""
        pool = TalentPool()  # 空池
        engine = EliminationEngine(pool=pool)

        replacement = engine.find_replacement(
            role="engineer",
            company_values=[],
            exclude_ids=[],
        )

        assert replacement is None
