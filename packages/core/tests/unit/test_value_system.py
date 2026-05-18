# -*- coding: utf-8 -*-
"""ValueSystem 单元测试 — 验证价值观库加载、行为提示词生成、消息审计。"""

from __future__ import annotations

import pytest

from agent_company.values.vault import ValuePrinciple, ValueVault, VALUE_CATEGORIES
from agent_company.values.system import ValueSystem, ValueAudit


class TestVaultLoad:
    """测试价值观库加载。"""

    def test_vault_load_defaults(self) -> None:
        """默认加载应产生一批有效的价值观原则。"""
        vault = ValueVault()
        all_values = vault.get_all()

        # 内置默认数据中有：3+2+2+2+2+2+2 = 15 条（根据 _DEFAULT_VALUES 计算）
        assert len(all_values) >= 15

    def test_vault_load_all_are_value_principles(self) -> None:
        """加载的每条都应是 ValuePrinciple 实例且字段不为空。"""
        vault = ValueVault()
        for vp in vault.get_all():
            assert isinstance(vp, ValuePrinciple)
            assert vp.name != ""
            assert vp.origin != ""
            assert vp.rule != ""
            assert vp.violation != ""
            assert vp.category in VALUE_CATEGORIES

    def test_vault_get_by_category(self) -> None:
        """按分类查询应只返回对应分类的原则。"""
        vault = ValueVault()
        excellence = vault.get_by_category("excellence")
        assert len(excellence) >= 1
        assert all(vp.category == "excellence" for vp in excellence)

    def test_vault_get_by_origin(self) -> None:
        """按来源模糊查询应命中对应数据。"""
        vault = ValueVault()
        amazon_values = vault.get_by_origin("Amazon")
        assert len(amazon_values) >= 1
        assert all("amazon" in vp.origin.lower() for vp in amazon_values)

    def test_vault_sample(self) -> None:
        """sample 方法应返回指定数量的价值观。"""
        vault = ValueVault()
        sampled = vault.sample(
            categories=["excellence", "transparency"],
            count_per_category=2,
        )
        # 每类最多2条，共2类 = 最多4条
        assert len(sampled) <= 4
        assert len(sampled) >= 2  # 至少每类1条


class TestValueCategories:
    """测试 7 个价值观分类。"""

    def test_value_categories_count(self) -> None:
        """应有 7 个价值观分类。"""
        assert len(VALUE_CATEGORIES) == 7

    def test_value_categories_names(self) -> None:
        """分类名称应正确。"""
        expected = {
            "excellence",
            "transparency",
            "ownership",
            "decision_making",
            "learning",
            "collaboration",
            "long_termism",
        }
        assert set(VALUE_CATEGORIES) == expected

    def test_vault_covers_all_categories(self) -> None:
        """默认加载的价值观应覆盖全部 7 个分类。"""
        vault = ValueVault()
        all_values = vault.get_all()
        covered_categories = {vp.category for vp in all_values}
        assert covered_categories == set(VALUE_CATEGORIES)


class TestGenerateBehaviorPrompt:
    """测试行为提示词生成。"""

    def test_generate_behavior_prompt(self) -> None:
        """生成的提示词应包含关键结构元素。"""
        vault = ValueVault()
        values = vault.get_all()
        system = ValueSystem(values)

        prompt = system.generate_behavior_prompt()

        assert "行为价值观准则" in prompt
        assert "自我检查" in prompt
        assert "绝不允许" in prompt
        assert len(prompt) > 100  # 不应是空字符串

    def test_generate_behavior_prompt_includes_rules(self) -> None:
        """提示词应包含具体的行为准则文本。"""
        vault = ValueVault()
        values = vault.get_by_category("excellence")
        system = ValueSystem(values)

        prompt = system.generate_behavior_prompt()

        # 应包含 excellence 分类的模板内容
        assert "最高质量" in prompt or "EXCELLENCE" in prompt

    def test_generate_behavior_prompt_with_subset(self) -> None:
        """仅使用部分价值观也能正常生成。"""
        values = [
            ValuePrinciple(
                name="测试原则",
                origin="测试来源",
                rule="这是一条测试准则",
                violation="违反示例",
                category="excellence",
            ),
        ]
        system = ValueSystem(values)
        prompt = system.generate_behavior_prompt()

        assert "测试准则" in prompt
        assert "违反示例" in prompt


class TestAuditMessage:
    """测试消息审计功能。"""

    def test_audit_compliant_message(self) -> None:
        """正常消息应通过审计，得到高合规分。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        audit = system.audit_message("我已经完成了详细的数据分析报告，包含所有关键指标的对比。")

        assert isinstance(audit, ValueAudit)
        assert audit.score == 1.0
        assert len(audit.violations) == 0

    def test_audit_dismissive_message(self) -> None:
        """敷衍态度的消息应检出违规。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        audit = system.audit_message("差不多就行了，能用就行，随便吧。")

        assert audit.score < 1.0
        assert len(audit.violations) > 0
        assert any("敷衍" in v for v in audit.violations)

    def test_audit_evasive_message(self) -> None:
        """推卸责任的消息应检出违规。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        audit = system.audit_message("这不是我的问题，不关我的事。")

        assert audit.score < 1.0
        assert len(audit.violations) > 0

    def test_audit_hiding_message(self) -> None:
        """隐瞒信息的消息应检出违规。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        audit = system.audit_message("这个先不说吧，别让老板知道。")

        assert audit.score < 1.0
        assert len(audit.violations) >= 1

    def test_audit_vague_message(self) -> None:
        """含糊表述应检出违规。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        audit = system.audit_message("大概是这样的，应该没问题，不太确定。")

        assert audit.score < 1.0
        assert len(audit.violations) >= 1

    def test_audit_negative_message(self) -> None:
        """消极抵抗的消息应检出违规。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        audit = system.audit_message("做不到，不可能的，没什么意义。")

        assert audit.score < 1.0
        assert len(audit.violations) >= 1

    def test_audit_score_floor(self) -> None:
        """即使有多个违规，分数最低也不低于 0。"""
        vault = ValueVault()
        system = ValueSystem(vault.get_all())

        # 包含大量违规关键词
        audit = system.audit_message(
            "差不多就行了，随便吧，不是我的问题，先不说，"
            "大概是吧，做不到，不可能的，算了吧。"
        )

        assert audit.score >= 0.0
