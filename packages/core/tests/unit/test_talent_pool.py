# -*- coding: utf-8 -*-
"""TalentPool 单元测试 — 验证人才池的注册、查询、删除等核心功能。"""

from __future__ import annotations

import pytest

from agent_company.pool.profile import AgentProfile
from agent_company.pool.presets import create_default_pool
from agent_company.pool.talent_pool import TalentPool


class TestTalentPoolAddAgent:
    """测试 Agent 注册到人才池的功能。"""

    def test_add_agent(self, sample_profiles: list[AgentProfile]) -> None:
        """注册单个 Agent 后池中数量增加，且可通过 ID 获取。"""
        pool = TalentPool()
        profile = sample_profiles[0]
        pool.register(profile)

        assert pool.size == 1
        assert pool.get(profile.id) is profile

    def test_add_duplicate_raises(self, sample_profiles: list[AgentProfile]) -> None:
        """重复注册同 ID 的 Agent 应抛出 ValueError。"""
        pool = TalentPool()
        profile = sample_profiles[0]
        pool.register(profile)

        with pytest.raises(ValueError, match="已存在"):
            pool.register(profile)

    def test_add_multiple_agents(self, sample_profiles: list[AgentProfile]) -> None:
        """注册多个 Agent 后池的 size 正确。"""
        pool = TalentPool()
        for p in sample_profiles:
            pool.register(p)
        assert pool.size == len(sample_profiles)


class TestTalentPoolQuery:
    """测试人才池的查询功能。"""

    def test_query_by_skills(self, sample_pool: TalentPool) -> None:
        """通过技能关键词查询能命中对应 Agent。"""
        results = sample_pool.query(role_match="python")
        # 应至少命中 engineer 和 junior
        ids = [a.id for a in results]
        assert "agent-engineer-001" in ids

    def test_query_by_category(self, sample_pool: TalentPool) -> None:
        """通过 category 查询能筛选到正确分类的 Agent。"""
        writers = sample_pool.query(role_match="writer")
        assert all(a.category == "writer" for a in writers)
        assert len(writers) == 1

        engineers = sample_pool.query(role_match="engineer")
        assert len(engineers) == 2  # engineer-001 和 junior-001

    def test_query_with_min_performance(self, sample_pool: TalentPool) -> None:
        """设置 min_performance 可过滤掉绩效不达标的 Agent。"""
        results = sample_pool.query(min_performance=0.5)
        # 只有有项目记录的 agent 才有 performance_avg > 0
        for agent in results:
            assert agent.performance_avg >= 0.5

    def test_query_with_values_match(self, sample_pool: TalentPool) -> None:
        """使用 values_match 可筛选出价值观匹配的 Agent。"""
        results = sample_pool.query(values_match=["质量"])
        # 只有 writer 有 "质量" 这个价值观
        assert any(a.id == "agent-writer-001" for a in results)

    def test_query_with_exclude_ids(self, sample_pool: TalentPool) -> None:
        """exclude_ids 可以排除指定 Agent。"""
        results = sample_pool.query(exclude_ids=["agent-writer-001", "agent-junior-001"])
        ids = [a.id for a in results]
        assert "agent-writer-001" not in ids
        assert "agent-junior-001" not in ids

    def test_query_limit(self, sample_pool: TalentPool) -> None:
        """limit 限制返回数量。"""
        results = sample_pool.query(limit=2)
        assert len(results) <= 2


class TestTalentPoolGetById:
    """测试按 ID 获取 Agent。"""

    def test_get_agent_by_id(self, sample_pool: TalentPool) -> None:
        """正确 ID 能获取到对应 Agent。"""
        agent = sample_pool.get("agent-engineer-001")
        assert agent.name == "测试工程师"
        assert agent.category == "engineer"

    def test_get_nonexistent_raises(self, sample_pool: TalentPool) -> None:
        """不存在的 ID 应抛出 KeyError。"""
        with pytest.raises(KeyError, match="不存在"):
            sample_pool.get("nonexistent-id")


class TestPresetsLoaded:
    """测试预设人才池加载。"""

    def test_presets_loaded(self) -> None:
        """默认人才池应包含 17 个预设 Agent（文档说18但docstring说17，按实际计数）。"""
        pool = create_default_pool()
        # 4 writers + 5 engineers + 3 analysts + 2 designers + 3 managers = 17
        assert pool.size == 17

    def test_presets_categories(self) -> None:
        """预设人才池应覆盖所有 5 种职能分类。"""
        pool = create_default_pool()
        all_agents = pool.query(limit=50)
        categories = {a.category for a in all_agents}
        assert categories == {"writer", "engineer", "analyst", "designer", "manager"}


class TestTalentPoolRemove:
    """测试从人才池删除 Agent。"""

    def test_remove_agent(self, sample_pool: TalentPool) -> None:
        """删除 Agent 后池大小减少，且无法再获取。"""
        original_size = sample_pool.size
        sample_pool.remove("agent-writer-001")

        assert sample_pool.size == original_size - 1
        with pytest.raises(KeyError):
            sample_pool.get("agent-writer-001")

    def test_remove_nonexistent_raises(self, sample_pool: TalentPool) -> None:
        """删除不存在的 Agent 应抛出 KeyError。"""
        with pytest.raises(KeyError, match="不存在"):
            sample_pool.remove("nonexistent-id")
