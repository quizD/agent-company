"""PerformanceEngine 核心引擎：实时绩效追踪 + 定期评审。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .kpi import ROLE_KPI_TEMPLATES, KPIDefinition, KPITracker
from .scoring import PerformanceScore, compute_grade, generate_feedback


class ReviewResult(BaseModel):
    """评审结果"""

    scores: dict[str, PerformanceScore] = Field(default_factory=dict, description="agent_id -> score")
    rankings: list[PerformanceScore] = Field(default_factory=list, description="按分数排序")
    eliminations: list[PerformanceScore] = Field(default_factory=list, description="需淘汰的")
    warnings: list[PerformanceScore] = Field(default_factory=list, description="需警告的")
    company_score: float = Field(default=0.0, description="公司整体分")


class PerformanceEngine:
    """实时绩效追踪 + 定期评审"""

    def __init__(
        self,
        review_interval: int = 5,
        elimination_threshold: float = 60.0,
        warning_threshold: float = 70.0,
        bottom_ratio: float = 0.1,
    ) -> None:
        self.trackers: dict[str, KPITracker] = {}
        self._agent_roles: dict[str, str] = {}
        self._agent_names: dict[str, str] = {}
        self.review_interval = review_interval
        self.elimination_threshold = elimination_threshold
        self.warning_threshold = warning_threshold
        self.bottom_ratio = bottom_ratio
        self._review_history: list[ReviewResult] = []
        self._last_review_tick: int = 0

    def register_agent(self, agent_id: str, role: str, name: str = "") -> None:
        """注册 Agent，根据角色分配 KPI 模板"""
        self._agent_roles[agent_id] = role
        self._agent_names[agent_id] = name or agent_id

        # 合并通用 KPI 和角色专属 KPI
        definitions: list[KPIDefinition] = list(ROLE_KPI_TEMPLATES.get("通用", []))
        role_specific = ROLE_KPI_TEMPLATES.get(role, [])
        definitions.extend(role_specific)

        self.trackers[agent_id] = KPITracker(agent_id=agent_id, definitions=definitions)

    def unregister_agent(self, agent_id: str) -> None:
        """注销 Agent"""
        self.trackers.pop(agent_id, None)
        self._agent_roles.pop(agent_id, None)
        self._agent_names.pop(agent_id, None)

    # ---- 信号采集方法 ----

    def on_message(self, agent_id: str, response_time: float, content_length: int, tick: int = 0) -> None:
        """消息响应信号：记录响应时间和产出量"""
        tracker = self.trackers.get(agent_id)
        if not tracker:
            return
        tracker.record("响应性", response_time, tick=tick)
        # 如果有产出量 KPI，记录内容长度
        if "产出量" in tracker.definitions:
            tracker.record("产出量", float(content_length), tick=tick)

    def on_task_complete(self, agent_id: str, quality_score: float, on_time: bool, tick: int = 0) -> None:
        """任务完成信号：记录质量和时效"""
        tracker = self.trackers.get(agent_id)
        if not tracker:
            return
        if "内容质量" in tracker.definitions:
            tracker.record("内容质量", quality_score, tick=tick)
        if "按时交付" in tracker.definitions:
            tracker.record("按时交付", 1.0 if on_time else 0.0, tick=tick)
        if "代码质量" in tracker.definitions:
            tracker.record("代码质量", quality_score, tick=tick)
        if "交付速度" in tracker.definitions:
            tracker.record("交付速度", 1.0 if on_time else 0.5, tick=tick)
        # 通用协作贡献
        tracker.record("协作贡献", 1.0, tick=tick)

    def on_decision(self, agent_id: str, decision_rounds: int, was_escalated: bool, tick: int = 0) -> None:
        """决策信号：记录决策效率"""
        tracker = self.trackers.get(agent_id)
        if not tracker:
            return
        if "决策效率" in tracker.definitions:
            tracker.record("决策效率", float(decision_rounds), tick=tick)
        if "自主性" in tracker.definitions:
            # 未升级 = 自主决策
            tracker.record("自主性", 0.0 if was_escalated else 1.0, tick=tick)

    # ---- 定期评审 ----

    def should_review(self, current_tick: int) -> bool:
        """是否到了评审时间"""
        return (current_tick - self._last_review_tick) >= self.review_interval

    def periodic_review(self, agent_ids: list[str]) -> ReviewResult:
        """执行定期绩效评审"""
        scores: dict[str, PerformanceScore] = {}

        for agent_id in agent_ids:
            tracker = self.trackers.get(agent_id)
            if not tracker:
                continue

            # 1. 汇总每个 Agent 的 KPI 数据
            kpi_scores = tracker.evaluate()

            # 2. 计算综合分（加权平均）
            total_weight = 0.0
            weighted_sum = 0.0
            for kpi_name, kpi_score in kpi_scores.items():
                definition = tracker.definitions.get(kpi_name)
                weight = definition.weight if definition else 1.0
                weighted_sum += kpi_score * weight
                total_weight += weight

            total_score = weighted_sum / max(total_weight, 1.0)

            # 判定总体趋势
            trends = [tracker.get_trend(name) for name in tracker.definitions]
            up_count = trends.count("up")
            down_count = trends.count("down")
            if up_count > down_count:
                trend = "up"
            elif down_count > up_count:
                trend = "down"
            else:
                trend = "stable"

            ps = PerformanceScore(
                agent_id=agent_id,
                agent_name=self._agent_names.get(agent_id, agent_id),
                role=self._agent_roles.get(agent_id, "通用"),
                kpi_scores=kpi_scores,
                total_score=round(total_score, 2),
                grade=compute_grade(total_score),
                trend=trend,
            )
            scores[agent_id] = ps

        # 3. 排名
        rankings = sorted(scores.values(), key=lambda s: s.total_score, reverse=True)
        for i, ps in enumerate(rankings):
            ps.rank = i + 1

        # 4. 判定淘汰和警告
        eliminations: list[PerformanceScore] = []
        warnings: list[PerformanceScore] = []

        for ps in rankings:
            if ps.total_score < self.elimination_threshold:
                eliminations.append(ps)
            elif ps.total_score < self.warning_threshold:
                warnings.append(ps)

        # 5. 生成反馈
        for ps in rankings:
            ps.feedback = generate_feedback(ps)

        # 公司整体分
        company_score = sum(ps.total_score for ps in rankings) / max(len(rankings), 1)

        result = ReviewResult(
            scores=scores,
            rankings=rankings,
            eliminations=eliminations,
            warnings=warnings,
            company_score=round(company_score, 2),
        )

        self._review_history.append(result)
        self._last_review_tick += self.review_interval

        return result

    @property
    def review_history(self) -> list[ReviewResult]:
        """获取历史评审结果"""
        return self._review_history
