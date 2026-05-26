"""Agent 市场注册表：发布、检索、安装 AgentCard。

MVP 实现：基于本地文件系统的注册表，每张卡片存为一个 .agent.yaml 文件。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from .card import AgentCard, CardMetadata, PerformanceAttestation

if TYPE_CHECKING:
    from ..pool.profile import AgentProfile
    from ..pool.talent_pool import TalentPool


class MarketplaceRegistry:
    """本地 Agent 市场注册表。

    目录结构::

        marketplace/
        ├── alice/writer-pro.agent.yaml
        ├── bob/coder-x.agent.yaml
        └── ...

    card_id 形如 ``author/agent-name``，对应路径 ``{root}/{author}/{name}.agent.yaml``。
    """

    CARD_SUFFIX = ".agent.yaml"

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ── 路径辅助 ──────────────────────────────────────────

    def _card_path(self, card_id: str) -> Path:
        if "/" not in card_id:
            raise ValueError(f"card_id 必须为 'author/name' 格式，收到: {card_id}")
        author, name = card_id.split("/", 1)
        return self.root / author / f"{name}{self.CARD_SUFFIX}"

    # ── 序列化 ───────────────────────────────────────────

    @staticmethod
    def load_card_from_yaml(path: str | Path) -> AgentCard:
        """从 YAML 文件加载一张卡片。"""
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return AgentCard.model_validate(raw)

    @staticmethod
    def save_card_to_yaml(card: AgentCard, path: str | Path) -> None:
        """将卡片序列化到 YAML 文件。"""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            yaml.safe_dump(
                card.to_dict(),
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            ),
            encoding="utf-8",
        )

    # ── 核心 API ─────────────────────────────────────────

    def list_agents(self) -> list[AgentCard]:
        """列出市场中所有 Agent 卡片。"""
        cards: list[AgentCard] = []
        for path in sorted(self.root.rglob(f"*{self.CARD_SUFFIX}")):
            try:
                cards.append(self.load_card_from_yaml(path))
            except Exception:  # noqa: BLE001 — 损坏的卡片跳过
                continue
        return cards

    def get(self, card_id: str) -> AgentCard:
        """按 card_id 获取一张卡片。"""
        path = self._card_path(card_id)
        if not path.exists():
            raise KeyError(f"卡片不存在: {card_id}")
        return self.load_card_from_yaml(path)

    def search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        min_avg_score: float = 0.0,
    ) -> list[AgentCard]:
        """搜索卡片。

        Args:
            query: 关键词，匹配 name/description/skills/specializations
            tags: 标签集合，需全部命中
            min_avg_score: 认证绩效平均分门槛
        """
        keyword = query.lower().strip()
        required_tags = set(tags or [])

        results: list[AgentCard] = []
        for card in self.list_agents():
            if card.avg_score < min_avg_score:
                continue
            if required_tags and not required_tags.issubset(set(card.metadata.tags)):
                continue
            if keyword:
                haystack = " ".join(
                    [
                        card.profile.name,
                        card.metadata.description,
                        " ".join(card.profile.skills.keys()),
                        " ".join(card.profile.specializations),
                        " ".join(card.metadata.tags),
                    ]
                ).lower()
                if keyword not in haystack:
                    continue
            results.append(card)

        # 按平均分降序，未认证的排最后
        results.sort(key=lambda c: (c.project_count > 0, c.avg_score), reverse=True)
        return results

    def publish(
        self,
        profile: AgentProfile,
        metadata: CardMetadata,
        attestations: list[PerformanceAttestation] | None = None,
        overwrite: bool = False,
    ) -> AgentCard:
        """发布一个 AgentProfile 为市场卡片。"""
        path = self._card_path(metadata.card_id)
        if path.exists() and not overwrite:
            raise FileExistsError(f"卡片已存在: {metadata.card_id}（使用 overwrite=True 覆盖）")

        card = AgentCard(
            metadata=metadata,
            profile=profile,
            attestations=attestations or [],
        )
        self.save_card_to_yaml(card, path)
        return card

    def unpublish(self, card_id: str) -> None:
        """从市场移除卡片。"""
        path = self._card_path(card_id)
        if not path.exists():
            raise KeyError(f"卡片不存在: {card_id}")
        path.unlink()

    def install(self, card_id: str, pool: TalentPool) -> AgentCard:
        """将市场卡片安装到本地人才池。"""
        card = self.get(card_id)
        # 复制 profile，避免共享引用
        installed_profile = card.profile.model_copy(deep=True)
        pool.register(installed_profile)
        return card

    def attest(
        self,
        card_id: str,
        attestation: PerformanceAttestation,
    ) -> AgentCard:
        """为已发布卡片追加一条认证绩效记录。"""
        card = self.get(card_id)
        card.attestations.append(attestation)
        self.save_card_to_yaml(card, self._card_path(card_id))
        return card
