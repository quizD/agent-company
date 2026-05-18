# -*- coding: utf-8 -*-
"""共享测试 Fixtures — 为 Agent Company 测试套件提供公共数据和对象。

包含:
- sample_profiles: 3-4 个 AgentProfile 实例
- sample_pool: 预填充的 TalentPool
- sample_company_data: 用于公司健康度相关测试的数据
"""

from __future__ import annotations

import pytest

from agent_company.pool.profile import AgentProfile, ProjectRecord
from agent_company.pool.talent_pool import TalentPool


@pytest.fixture
def sample_profiles() -> list[AgentProfile]:
    """创建 4 个覆盖不同职能的测试用 AgentProfile。"""
    return [
        AgentProfile(
            id="agent-writer-001",
            name="测试写手",
            category="writer",
            skills={"creative_writing": 0.9, "editing": 0.85, "research": 0.7},
            specializations=["创意写作", "技术文档"],
            tools_proficiency={"markdown": 0.9, "notion": 0.8},
            personality={
                "openness": 0.85,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.8,
                "neuroticism": 0.4,
            },
            values=["创意", "质量", "准确性"],
            work_style="independent",
            communication_style="diplomatic",
            reliability_score=0.88,
            collaboration_score=0.82,
            llm_model="gpt-4o",
            model_tier="A",
            system_prompt_base="你是一名测试写手。",
            project_history=[
                ProjectRecord(
                    project_id="proj-1",
                    role="作者",
                    score=0.85,
                    result="完成技术文档",
                ),
                ProjectRecord(
                    project_id="proj-2",
                    role="编辑",
                    score=0.9,
                    result="完成内容审核",
                ),
            ],
        ),
        AgentProfile(
            id="agent-engineer-001",
            name="测试工程师",
            category="engineer",
            skills={"python": 0.92, "coding": 0.88, "testing": 0.8, "architecture": 0.75},
            specializations=["后端开发", "Python", "系统架构"],
            tools_proficiency={"git": 0.95, "docker": 0.85},
            personality={
                "openness": 0.7,
                "conscientiousness": 0.9,
                "extraversion": 0.5,
                "agreeableness": 0.65,
                "neuroticism": 0.3,
            },
            values=["代码质量", "可维护性", "quality"],
            work_style="independent",
            communication_style="data_driven",
            reliability_score=0.93,
            collaboration_score=0.78,
            llm_model="claude-sonnet-4-20250514",
            model_tier="A",
            system_prompt_base="你是一名测试工程师。",
            project_history=[
                ProjectRecord(
                    project_id="proj-3",
                    role="开发",
                    score=0.92,
                    result="完成后端开发",
                ),
            ],
        ),
        AgentProfile(
            id="agent-analyst-001",
            name="测试分析师",
            category="analyst",
            skills={"data_analysis": 0.88, "statistics": 0.82, "visualization": 0.75},
            specializations=["数据分析", "市场分析"],
            tools_proficiency={"python": 0.85, "sql": 0.9},
            personality={
                "openness": 0.7,
                "conscientiousness": 0.85,
                "extraversion": 0.5,
                "agreeableness": 0.7,
                "neuroticism": 0.35,
            },
            values=["数据驱动", "客观", "insight"],
            work_style="collaborative",
            communication_style="data_driven",
            reliability_score=0.87,
            collaboration_score=0.8,
            llm_model="gpt-4o",
            model_tier="A",
            system_prompt_base="你是一名测试分析师。",
        ),
        AgentProfile(
            id="agent-junior-001",
            name="测试实习生",
            category="engineer",
            skills={"python": 0.5, "coding": 0.45, "testing": 0.4},
            specializations=["初级开发"],
            tools_proficiency={"git": 0.6},
            personality={
                "openness": 0.85,
                "conscientiousness": 0.6,
                "extraversion": 0.75,
                "agreeableness": 0.85,
                "neuroticism": 0.5,
            },
            values=["学习成长", "团队协作"],
            work_style="collaborative",
            communication_style="diplomatic",
            reliability_score=0.65,
            collaboration_score=0.85,
            llm_model="gpt-4o-mini",
            model_tier="C",
            system_prompt_base="你是一名测试实习生。",
        ),
    ]


@pytest.fixture
def sample_pool(sample_profiles: list[AgentProfile]) -> TalentPool:
    """创建预填充了 sample_profiles 的 TalentPool。"""
    pool = TalentPool()
    for profile in sample_profiles:
        pool.register(profile)
    return pool


@pytest.fixture
def sample_company_data() -> dict:
    """用于公司健康度测试的模拟数据。"""
    return {
        "company_name": "TestProject<软件开发>",
        "mission": "开发一个高质量的测试管理系统",
        "values": ["quality", "innovation", "collaboration"],
        "team_size": 4,
        "budget_usd": 50.0,
        "agent_ids": [
            "agent-writer-001",
            "agent-engineer-001",
            "agent-analyst-001",
            "agent-junior-001",
        ],
    }
