"""招标引擎 — 从人才池筛选、竞标、评审到组建团队的核心流程。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agent_company.org.company import Company
from agent_company.org.role import Role
from agent_company.pool.profile import AgentProfile
from agent_company.pool.talent_pool import TalentPool
from agent_company.tender.analyzer import RoleSpec, TenderSpec
from agent_company.tender.bidding import BiddingProcess
from agent_company.tender.scoring import BidScore, ScoringMatrix


class TenderResult(BaseModel):
    """招标结果"""

    model_config = {"arbitrary_types_allowed": True}

    spec: TenderSpec = Field(description="招标需求书")
    selected_team: list[dict] = Field(
        default_factory=list,
        description="选中的团队成员列表 [{'profile': AgentProfile, 'role': RoleSpec, 'score': BidScore}]",
    )
    rejected: list[dict] = Field(
        default_factory=list,
        description="未选中的候选人列表",
    )
    company: Any = Field(default=None, description="组建的 Company 实例")
    tender_log: list[str] = Field(
        default_factory=list, description="招标过程日志"
    )


class TenderEngine:
    """从人才池中筛选、竞标、组建团队的核心引擎"""

    def __init__(self, pool: TalentPool, scoring: ScoringMatrix | None = None):
        self.pool = pool
        self.scoring = scoring or ScoringMatrix()
        self.bidding = BiddingProcess()

    def run_tender(self, spec: TenderSpec) -> TenderResult:
        """执行完整招标流程:
        1. 初筛 - 按技能和分类从人才池筛选候选人
        2. 竞标 - 候选人提交工作方案
        3. 评审打分 - 多维度评分
        4. 团队组建 - 选择最佳组合（考虑团队兼容性）
        5. 公司创建 - 组建 Company 实例
        """
        log: list[str] = []
        log.append(f"=== 招标启动: {spec.project_type} ===")
        log.append(f"项目描述: {spec.description[:80]}...")
        log.append(f"预算: ${spec.budget_usd}")
        log.append(f"需要角色: {len(spec.required_roles)} 个")

        # 1. 初筛
        shortlisted = self._shortlist(spec)
        for role_name, candidates in shortlisted.items():
            log.append(f"[初筛] {role_name}: {len(candidates)} 位候选人")

        # 2. 竞标
        log.append("--- 竞标阶段 ---")
        all_bids: dict[str, list] = {}
        for role_spec in spec.required_roles:
            candidates = shortlisted.get(role_spec.name, [])
            if candidates:
                bids = self.bidding.collect_bids(candidates, role_spec, spec.description)
                all_bids[role_spec.name] = bids
                log.append(f"[竞标] {role_spec.name}: 收到 {len(bids)} 份方案")

        # 3. 评审打分
        log.append("--- 评审阶段 ---")
        all_scores: dict[str, list[BidScore]] = {}
        for role_spec in spec.required_roles:
            candidates = shortlisted.get(role_spec.name, [])
            scores: list[BidScore] = []
            for profile in candidates:
                # 暂时传空团队，后续在 _select_team 中考虑兼容性
                score = self.scoring.score_candidate(
                    profile, role_spec, spec.value_priorities, []
                )
                scores.append(score)
            ranked = self.scoring.rank_candidates(scores)
            all_scores[role_spec.name] = ranked
            if ranked:
                log.append(
                    f"[评审] {role_spec.name}: 最高分 {ranked[0].total_score:.1f} "
                    f"({ranked[0].agent_name})"
                )

        # 4. 团队组建
        log.append("--- 组队阶段 ---")
        selected = self._select_team(all_scores, spec)
        rejected: list[dict] = []

        # 收集未选中的候选人
        selected_ids = {m["profile"].id for m in selected}
        for role_name, scores in all_scores.items():
            for score in scores:
                if score.agent_id not in selected_ids:
                    rejected.append({"agent_id": score.agent_id, "role": role_name, "score": score})

        for member in selected:
            log.append(
                f"[选中] {member['profile'].name} → {member['role'].name} "
                f"(得分: {member['score'].total_score:.1f})"
            )

        # 5. 组建公司
        log.append("--- 公司组建 ---")
        company = self._form_company(selected, spec)
        log.append(f"[完成] 公司 '{company.name}' 组建成功，共 {len(company.agents)} 名成员")

        return TenderResult(
            spec=spec,
            selected_team=selected,
            rejected=rejected,
            company=company,
            tender_log=log,
        )

    def _shortlist(self, spec: TenderSpec) -> dict[str, list[AgentProfile]]:
        """初筛：每个角色返回候选人列表"""
        result: dict[str, list[AgentProfile]] = {}

        for role_spec in spec.required_roles:
            # 使用技能关键词查询人才池
            candidates: list[AgentProfile] = []
            seen_ids: set[str] = set()

            # 按每个必备技能搜索
            for skill in role_spec.must_have_skills:
                found = self.pool.query(
                    role_match=skill,
                    limit=20,
                )
                for agent in found:
                    if agent.id not in seen_ids:
                        candidates.append(agent)
                        seen_ids.add(agent.id)

            # 如果技能搜索结果不足，再按分类搜索
            if len(candidates) < role_spec.count * 3:
                category_map = {
                    "主编": "writer",
                    "作者": "writer",
                    "校对": "writer",
                    "技术负责人": "engineer",
                    "开发工程师": "engineer",
                    "测试工程师": "engineer",
                    "项目经理": "manager",
                    "分析师": "analyst",
                    "设计总监": "designer",
                    "UI 设计师": "designer",
                    "UX 研究员": "designer",
                    "领域专家": "analyst",
                }
                category = category_map.get(role_spec.name, "")
                if category:
                    found = self.pool.query(role_match=category, limit=20)
                    for agent in found:
                        if agent.id not in seen_ids:
                            candidates.append(agent)
                            seen_ids.add(agent.id)

            # 过滤：模型等级门槛
            tier_order = {"S": 4, "A": 3, "B": 2, "C": 1}
            min_rank = tier_order.get(role_spec.min_model_tier, 2)
            candidates = [
                c for c in candidates
                if tier_order.get(c.model_tier, 2) >= min_rank
            ]

            result[role_spec.name] = candidates

        return result

    def _select_team(
        self, all_scores: dict[str, list[BidScore]], spec: TenderSpec
    ) -> list[dict]:
        """选择最佳团队组合

        贪心算法：按角色优先级排序，依次选择得分最高的候选人。
        同一个 Agent 不能被选入多个角色。
        """
        selected: list[dict] = []
        used_ids: set[str] = set()
        selected_profiles: list[AgentProfile] = []

        # 按角色优先级排序
        priority_order = {"critical": 0, "core": 1, "support": 2}
        sorted_roles = sorted(
            spec.required_roles,
            key=lambda r: priority_order.get(r.priority, 1),
        )

        for role_spec in sorted_roles:
            scores = all_scores.get(role_spec.name, [])
            needed = role_spec.count
            picked = 0

            # 如果已有团队成员，重新计算考虑团队兼容性的得分
            if selected_profiles:
                rescored: list[BidScore] = []
                for score in scores:
                    if score.agent_id in used_ids:
                        continue
                    # 获取 profile 重新打分
                    try:
                        profile = self.pool.get(score.agent_id)
                        new_score = self.scoring.score_candidate(
                            profile, role_spec, spec.value_priorities, selected_profiles
                        )
                        rescored.append(new_score)
                    except KeyError:
                        continue
                scores = self.scoring.rank_candidates(rescored)
            else:
                scores = [s for s in scores if s.agent_id not in used_ids]

            for score in scores:
                if picked >= needed:
                    break
                if score.agent_id in used_ids:
                    continue

                try:
                    profile = self.pool.get(score.agent_id)
                except KeyError:
                    continue

                selected.append({
                    "profile": profile,
                    "role": role_spec,
                    "score": score,
                })
                used_ids.add(score.agent_id)
                selected_profiles.append(profile)
                picked += 1

        return selected

    def _form_company(self, team: list[dict], spec: TenderSpec) -> Company:
        """组建公司实例，创建角色、部门、消息频道"""
        company = Company(
            name=f"Project<{spec.project_type}>",
            mission=spec.description[:200],
            values=spec.value_priorities,
        )

        # 创建通用频道
        company.message_bus.create_channel("general", description="全体频道")
        company.message_bus.create_channel("announcements", description="公告频道")

        # 根据角色优先级分配部门
        dept_mapping: dict[str, str] = {
            "critical": "管理层",
            "core": "执行层",
            "support": "支持层",
        }

        for member in team:
            profile: AgentProfile = member["profile"]
            role_spec: RoleSpec = member["role"]

            dept_name = dept_mapping.get(role_spec.priority, "执行层")

            # 创建 Role 对象
            role = Role(
                name=role_spec.name,
                department=dept_name,
                responsibilities=[f"负责 {skill}" for skill in role_spec.must_have_skills],
                channels=["general", "announcements"],
            )

            # 创建轻量 Agent 代理对象（仅用于注册，不启动 LLM）
            agent_stub = _AgentStub(
                id=profile.id,
                name=profile.name,
                profile=profile,
            )

            company.hire(agent_stub, role, dept_name)

        return company


class _AgentStub:
    """轻量 Agent 占位对象，仅用于公司注册。

    真正的 BaseAgent 实例应在后续任务执行时创建。
    """

    def __init__(self, id: str, name: str, profile: AgentProfile):
        self.id = id
        self.name = name
        self.profile = profile

    def __repr__(self) -> str:
        return f"AgentStub(id={self.id!r}, name={self.name!r})"
