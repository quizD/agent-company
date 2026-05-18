"""评审评分矩阵 — 多维度对候选人进行量化评分。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_company.pool.profile import AgentProfile
from agent_company.tender.analyzer import RoleSpec


class BidScore(BaseModel):
    """候选人评分结果"""

    agent_id: str = Field(description="Agent ID")
    agent_name: str = Field(description="Agent 名称")
    role_name: str = Field(description="竞标角色名称")
    skill_match: float = Field(default=0.0, description="技能匹配度 0-100")
    performance: float = Field(default=0.0, description="历史绩效 0-100")
    value_alignment: float = Field(default=0.0, description="价值观契合度 0-100")
    team_compatibility: float = Field(default=0.0, description="团队兼容性 0-100")
    model_efficiency: float = Field(default=0.0, description="模型效率得分 0-100")
    total_score: float = Field(default=0.0, description="加权总分")


class ScoringMatrix:
    """评审评分矩阵"""

    WEIGHTS: dict[str, float] = {
        "skill_match": 0.30,
        "performance": 0.25,
        "value_alignment": 0.20,
        "team_compatibility": 0.15,
        "model_efficiency": 0.10,
    }

    # 模型等级对应的效率分（越低等级完成同样任务 = 效率越高）
    _TIER_EFFICIENCY: dict[str, float] = {
        "S": 60.0,
        "A": 75.0,
        "B": 90.0,
        "C": 100.0,
    }

    # 模型等级排序（用于最低等级门槛检查）
    _TIER_ORDER: dict[str, int] = {"S": 4, "A": 3, "B": 2, "C": 1}

    def score_candidate(
        self,
        profile: AgentProfile,
        role_spec: RoleSpec,
        project_values: list[str],
        existing_team: list[AgentProfile],
    ) -> BidScore:
        """对单个候选人打分"""
        skill_match = self._calc_skill_match(profile, role_spec)
        performance = self._calc_performance(profile)
        value_alignment = self._calc_value_alignment(profile, project_values)
        team_compatibility = self._calc_team_compatibility(profile, existing_team)
        model_efficiency = self._calc_model_efficiency(profile, role_spec)

        total = (
            skill_match * self.WEIGHTS["skill_match"]
            + performance * self.WEIGHTS["performance"]
            + value_alignment * self.WEIGHTS["value_alignment"]
            + team_compatibility * self.WEIGHTS["team_compatibility"]
            + model_efficiency * self.WEIGHTS["model_efficiency"]
        )

        return BidScore(
            agent_id=profile.id,
            agent_name=profile.name,
            role_name=role_spec.name,
            skill_match=round(skill_match, 2),
            performance=round(performance, 2),
            value_alignment=round(value_alignment, 2),
            team_compatibility=round(team_compatibility, 2),
            model_efficiency=round(model_efficiency, 2),
            total_score=round(total, 2),
        )

    def rank_candidates(self, scores: list[BidScore]) -> list[BidScore]:
        """按总分排名"""
        return sorted(scores, key=lambda s: s.total_score, reverse=True)

    # ------------------------------------------------------------------
    # 私有评分方法
    # ------------------------------------------------------------------

    def _calc_skill_match(self, profile: AgentProfile, role_spec: RoleSpec) -> float:
        """计算技能匹配度（0-100）"""
        if not role_spec.must_have_skills:
            return 50.0

        # 必备技能匹配（占 70%）
        must_have_score = 0.0
        for skill in role_spec.must_have_skills:
            skill_lower = skill.lower()
            # 精确匹配技能名
            matched = False
            for agent_skill, proficiency in profile.skills.items():
                if skill_lower in agent_skill.lower() or agent_skill.lower() in skill_lower:
                    must_have_score += proficiency
                    matched = True
                    break
            # 检查 specializations
            if not matched:
                for spec in profile.specializations:
                    if skill_lower in spec.lower() or spec.lower() in skill_lower:
                        must_have_score += 0.7
                        matched = True
                        break

        must_have_pct = (must_have_score / len(role_spec.must_have_skills)) * 100

        # 加分技能匹配（占 30%）
        nice_score = 0.0
        if role_spec.nice_to_have:
            for skill in role_spec.nice_to_have:
                skill_lower = skill.lower()
                for agent_skill, proficiency in profile.skills.items():
                    if skill_lower in agent_skill.lower() or agent_skill.lower() in skill_lower:
                        nice_score += proficiency
                        break
            nice_pct = (nice_score / len(role_spec.nice_to_have)) * 100
        else:
            nice_pct = 50.0

        return min(100.0, must_have_pct * 0.7 + nice_pct * 0.3)

    def _calc_performance(self, profile: AgentProfile) -> float:
        """计算历史绩效得分（0-100）"""
        # 综合 performance_avg 和 reliability_score
        perf = profile.performance_avg * 100 if profile.performance_avg > 0 else 60.0
        reliability = profile.reliability_score * 100
        return min(100.0, perf * 0.7 + reliability * 0.3)

    def _calc_value_alignment(
        self, profile: AgentProfile, project_values: list[str]
    ) -> float:
        """计算价值观契合度（0-100）"""
        if not project_values:
            return 70.0

        agent_values = {v.lower() for v in profile.values}
        required_values = {v.lower() for v in project_values}

        if not required_values:
            return 70.0

        overlap = len(agent_values & required_values)
        return min(100.0, (overlap / len(required_values)) * 100)

    def _calc_team_compatibility(
        self, profile: AgentProfile, existing_team: list[AgentProfile]
    ) -> float:
        """计算团队兼容性（0-100）"""
        if not existing_team:
            # 没有已选队员，基于自身协作分
            return profile.collaboration_score * 100

        # 计算与已有团队成员的互补性和协作兼容性
        compat_scores: list[float] = []

        for teammate in existing_team:
            score = 0.0

            # 协作风格互补
            if profile.work_style != teammate.work_style:
                score += 30.0  # 多样性加分
            else:
                score += 20.0  # 相同风格也不差

            # 沟通风格兼容
            if profile.communication_style == teammate.communication_style:
                score += 25.0
            else:
                score += 15.0

            # 性格互补（大五人格）
            if profile.personality and teammate.personality:
                # agreeableness 高 = 好相处
                agree_avg = (
                    profile.personality.get("agreeableness", 0.5)
                    + teammate.personality.get("agreeableness", 0.5)
                ) / 2
                score += agree_avg * 45.0
            else:
                score += 30.0

            compat_scores.append(min(100.0, score))

        return sum(compat_scores) / len(compat_scores)

    def _calc_model_efficiency(
        self, profile: AgentProfile, role_spec: RoleSpec
    ) -> float:
        """计算模型效率得分（0-100）

        满足最低要求的前提下，低等级模型 = 更高效率（节省成本）。
        不满足最低要求则大幅扣分。
        """
        agent_tier_rank = self._TIER_ORDER.get(profile.model_tier, 2)
        min_tier_rank = self._TIER_ORDER.get(role_spec.min_model_tier, 2)

        # 不满足最低模型等级要求
        if agent_tier_rank < min_tier_rank:
            return 20.0

        return self._TIER_EFFICIENCY.get(profile.model_tier, 75.0)
