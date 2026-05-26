"""Agent 市场卡片数据模型。

AgentCard = AgentProfile + 发布元数据 + 认证绩效履历。
作为社区贡献 Agent 的标准交换格式（YAML/JSON）。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..pool.profile import AgentProfile


class PerformanceAttestation(BaseModel):
    """认证绩效记录。

    每条记录由发布者签名，证明 Agent 在某次真实项目中的表现。
    """

    project_id: str = Field(description="项目唯一标识")
    project_type: str = Field(description="项目类型，如 software_dev / publishing")
    role: str = Field(description="承担的角色")
    score: float = Field(ge=0.0, le=100.0, description="绩效得分（0-100）")
    grade: str = Field(description="评级 S/A/B/C/D/F")
    completed_at: datetime = Field(default_factory=datetime.now)
    attested_by: str = Field(default="self", description="背书方（self/community/verified）")


class CardMetadata(BaseModel):
    """卡片元数据。"""

    card_id: str = Field(description="卡片唯一标识，建议格式 author/agent-name")
    version: str = Field(default="0.1.0", description="语义化版本")
    author: str = Field(description="作者署名")
    description: str = Field(default="", description="一句话描述")
    tags: list[str] = Field(default_factory=list, description="标签，便于检索")
    license: str = Field(default="Apache-2.0")
    homepage: str = Field(default="", description="主页或仓库链接")
    created_at: datetime = Field(default_factory=datetime.now)


class AgentCard(BaseModel):
    """Agent 市场卡片：可分享、可安装的 Agent 包。"""

    metadata: CardMetadata
    profile: AgentProfile
    attestations: list[PerformanceAttestation] = Field(
        default_factory=list, description="认证绩效履历"
    )

    @property
    def avg_score(self) -> float:
        """所有认证绩效的平均分。"""
        if not self.attestations:
            return 0.0
        return sum(a.score for a in self.attestations) / len(self.attestations)

    @property
    def project_count(self) -> int:
        """认证项目数。"""
        return len(self.attestations)

    @property
    def fingerprint(self) -> str:
        """内容指纹（用于检测篡改）。基于 metadata + profile 核心字段。"""
        payload = {
            "card_id": self.metadata.card_id,
            "version": self.metadata.version,
            "name": self.profile.name,
            "skills": self.profile.skills,
            "model_tier": self.profile.model_tier,
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """导出为可序列化的字典。"""
        return self.model_dump(mode="json")
