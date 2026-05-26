# -*- coding: utf-8 -*-
"""Agent 市场模块单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_company.marketplace import (
    AgentCard,
    CardMetadata,
    MarketplaceRegistry,
    PerformanceAttestation,
)
from agent_company.pool.profile import AgentProfile
from agent_company.pool.talent_pool import TalentPool


@pytest.fixture
def metadata() -> CardMetadata:
    return CardMetadata(
        card_id="alice/writer-pro",
        author="alice",
        description="一个高产的技术写手",
        tags=["writer", "technical"],
    )


@pytest.fixture
def attestation() -> PerformanceAttestation:
    return PerformanceAttestation(
        project_id="proj-x",
        project_type="publishing",
        role="作者",
        score=88.0,
        grade="A",
    )


def _profile() -> AgentProfile:
    return AgentProfile(
        name="WriterPro",
        category="writer",
        skills={"writing": 0.9},
        specializations=["技术写作"],
        model_tier="A",
    )


class TestAgentCard:
    def test_avg_score_empty(self, metadata: CardMetadata) -> None:
        card = AgentCard(metadata=metadata, profile=_profile())
        assert card.avg_score == 0.0
        assert card.project_count == 0

    def test_avg_score_with_attestations(
        self, metadata: CardMetadata, attestation: PerformanceAttestation
    ) -> None:
        att2 = attestation.model_copy(update={"score": 92.0})
        card = AgentCard(
            metadata=metadata,
            profile=_profile(),
            attestations=[attestation, att2],
        )
        assert card.avg_score == 90.0
        assert card.project_count == 2

    def test_fingerprint_stable(self, metadata: CardMetadata) -> None:
        c1 = AgentCard(metadata=metadata, profile=_profile())
        c2 = AgentCard(metadata=metadata, profile=_profile())
        assert c1.fingerprint == c2.fingerprint
        assert len(c1.fingerprint) == 16

    def test_fingerprint_changes_on_skill_change(self, metadata: CardMetadata) -> None:
        p1 = _profile()
        p2 = _profile()
        p2.skills["writing"] = 0.5
        c1 = AgentCard(metadata=metadata, profile=p1)
        c2 = AgentCard(metadata=metadata, profile=p2)
        assert c1.fingerprint != c2.fingerprint


class TestMarketplaceRegistry:
    def test_publish_and_get(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        card = registry.publish(_profile(), metadata)
        assert card.metadata.card_id == "alice/writer-pro"

        loaded = registry.get("alice/writer-pro")
        assert loaded.profile.name == "WriterPro"
        assert loaded.metadata.author == "alice"

    def test_publish_duplicate_raises(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata)
        with pytest.raises(FileExistsError):
            registry.publish(_profile(), metadata)

    def test_publish_overwrite(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata)
        new_meta = metadata.model_copy(update={"description": "更新的描述"})
        registry.publish(_profile(), new_meta, overwrite=True)
        assert registry.get("alice/writer-pro").metadata.description == "更新的描述"

    def test_invalid_card_id(self, tmp_path: Path) -> None:
        registry = MarketplaceRegistry(tmp_path)
        bad = CardMetadata(card_id="no-slash", author="alice")
        with pytest.raises(ValueError, match="author/name"):
            registry.publish(_profile(), bad)

    def test_list_agents(self, tmp_path: Path) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), CardMetadata(card_id="alice/w1", author="alice"))
        registry.publish(_profile(), CardMetadata(card_id="bob/w2", author="bob"))
        cards = registry.list_agents()
        assert len(cards) == 2
        ids = {c.metadata.card_id for c in cards}
        assert ids == {"alice/w1", "bob/w2"}

    def test_search_by_keyword(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata)
        registry.publish(
            _profile(),
            CardMetadata(card_id="bob/coder", author="bob", tags=["engineer"]),
        )

        # 命中描述
        assert len(registry.search("技术写手")) == 1
        # 命中 specialization
        assert len(registry.search("技术写作")) >= 1
        # 不匹配
        assert registry.search("不存在的关键词") == []

    def test_search_by_tags(self, tmp_path: Path) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(
            _profile(),
            CardMetadata(card_id="alice/a", author="alice", tags=["writer", "zh"]),
        )
        registry.publish(
            _profile(),
            CardMetadata(card_id="bob/b", author="bob", tags=["engineer"]),
        )
        assert len(registry.search(tags=["writer"])) == 1
        assert len(registry.search(tags=["writer", "zh"])) == 1
        assert len(registry.search(tags=["writer", "engineer"])) == 0

    def test_search_min_avg_score(
        self, tmp_path: Path, metadata: CardMetadata, attestation: PerformanceAttestation
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata, attestations=[attestation])
        registry.publish(
            _profile(),
            CardMetadata(card_id="bob/b", author="bob"),
        )
        # alice 88 分，bob 0 分
        results = registry.search(min_avg_score=80.0)
        assert len(results) == 1
        assert results[0].metadata.card_id == "alice/writer-pro"

    def test_install_to_pool(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata)
        pool = TalentPool()
        card = registry.install("alice/writer-pro", pool)
        assert pool.size == 1
        installed = pool.get(card.profile.id)
        assert installed.name == "WriterPro"

    def test_unpublish(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata)
        registry.unpublish("alice/writer-pro")
        with pytest.raises(KeyError):
            registry.get("alice/writer-pro")

    def test_attest_appends(
        self,
        tmp_path: Path,
        metadata: CardMetadata,
        attestation: PerformanceAttestation,
    ) -> None:
        registry = MarketplaceRegistry(tmp_path)
        registry.publish(_profile(), metadata)
        updated = registry.attest("alice/writer-pro", attestation)
        assert updated.project_count == 1
        # 重新加载也能看到
        reloaded = registry.get("alice/writer-pro")
        assert reloaded.project_count == 1
        assert reloaded.attestations[0].score == 88.0

    def test_yaml_roundtrip(
        self, tmp_path: Path, metadata: CardMetadata
    ) -> None:
        card = AgentCard(metadata=metadata, profile=_profile())
        path = tmp_path / "card.agent.yaml"
        MarketplaceRegistry.save_card_to_yaml(card, path)
        loaded = MarketplaceRegistry.load_card_from_yaml(path)
        assert loaded.fingerprint == card.fingerprint
