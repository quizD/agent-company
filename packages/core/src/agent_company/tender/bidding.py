"""竞标流程 — 为候选人生成竞标方案。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_company.pool.profile import AgentProfile
from agent_company.tender.analyzer import RoleSpec


class BidProposal(BaseModel):
    """Agent 竞标方案"""

    agent_id: str = Field(description="Agent ID")
    role_name: str = Field(description="竞标角色名称")
    approach: str = Field(description="工作方案描述")
    estimated_quality: float = Field(
        default=0.8, ge=0.0, le=1.0, description="预估交付质量"
    )
    strengths: list[str] = Field(default_factory=list, description="核心优势")
    commitment: str = Field(default="", description="承诺声明")


class BiddingProcess:
    """管理竞标流程"""

    def generate_bid(
        self, profile: AgentProfile, role_spec: RoleSpec, project_desc: str
    ) -> BidProposal:
        """为 Agent 生成竞标方案（当前基于规则模板，后续可接入LLM）"""
        # 提取该 Agent 与角色匹配的技能
        matching_skills: list[str] = []
        for skill in role_spec.must_have_skills:
            skill_lower = skill.lower()
            for agent_skill in profile.skills:
                if skill_lower in agent_skill.lower() or agent_skill.lower() in skill_lower:
                    matching_skills.append(agent_skill)
                    break

        # 生成优势列表
        strengths: list[str] = []
        if matching_skills:
            strengths.append(f"具备核心技能: {', '.join(matching_skills)}")
        if profile.specializations:
            strengths.append(f"专业领域: {', '.join(profile.specializations[:3])}")
        if profile.reliability_score >= 0.9:
            strengths.append("高可靠性，历史交付稳定")
        if profile.collaboration_score >= 0.9:
            strengths.append("优秀的团队协作能力")
        if profile.performance_avg >= 0.85:
            strengths.append(f"历史绩效优异（{profile.performance_avg:.0%}）")

        # 生成工作方案描述
        approach_parts = [
            f"作为 {role_spec.name}，",
            f"我将凭借 {', '.join(matching_skills[:3]) if matching_skills else '综合能力'} 方面的专业能力，",
            f"以 {profile.work_style} 的工作方式，",
            f"采用 {profile.communication_style} 的沟通风格完成项目交付。",
        ]
        approach = "".join(approach_parts)

        # 预估交付质量
        quality = min(1.0, profile.performance_avg if profile.performance_avg > 0 else 0.7)

        # 承诺声明
        commitment = (
            f"承诺以 {profile.model_tier} 级模型能力，"
            f"保持 {profile.reliability_score:.0%} 的可靠性完成交付。"
        )

        return BidProposal(
            agent_id=profile.id,
            role_name=role_spec.name,
            approach=approach,
            estimated_quality=round(quality, 2),
            strengths=strengths,
            commitment=commitment,
        )

    def collect_bids(
        self,
        candidates: list[AgentProfile],
        role_spec: RoleSpec,
        project_desc: str,
    ) -> list[BidProposal]:
        """收集所有候选人的竞标方案"""
        return [
            self.generate_bid(profile, role_spec, project_desc)
            for profile in candidates
        ]
