"""末位淘汰引擎：低绩效淘汰 + 从人才池补充替代者。"""

from __future__ import annotations

from pydantic import BaseModel

from agent_company.pool.profile import AgentProfile
from agent_company.pool.talent_pool import TalentPool

from .engine import ReviewResult
from .scoring import PerformanceGrade


class Replacement(BaseModel):
    """替换记录"""

    removed_id: str
    removed_name: str
    reason: str
    score: float
    grade: str
    replaced_by_id: str
    replaced_by_name: str


class EliminationEngine:
    """末位淘汰 + 从人才池补充替代者"""

    def __init__(self, pool: TalentPool, bottom_ratio: float = 0.1) -> None:
        self.pool = pool
        self.bottom_ratio = bottom_ratio
        self._consecutive_grades: dict[str, list[str]] = {}  # agent_id -> 连续评级记录

    def update_grades(self, review: ReviewResult) -> None:
        """更新连续评级记录"""
        for agent_id, score in review.scores.items():
            if agent_id not in self._consecutive_grades:
                self._consecutive_grades[agent_id] = []
            self._consecutive_grades[agent_id].append(score.grade.value)

    def determine_eliminations(self, review: ReviewResult) -> list[str]:
        """判定需淘汰的 Agent IDs:
        - 单次 F -> 立即淘汰
        - 连续 2 次 D -> 淘汰
        - 连续 3 次 C 且无上升趋势 -> 淘汰警告（也执行淘汰）
        - 末位 bottom_ratio（最少1人）-> 进入观察期（本轮不直接淘汰，仅记录）
        """
        to_eliminate: list[str] = []

        for agent_id, score in review.scores.items():
            grades = self._consecutive_grades.get(agent_id, [])

            # 单次 F -> 立即淘汰
            if score.grade == PerformanceGrade.F:
                if agent_id not in to_eliminate:
                    to_eliminate.append(agent_id)
                continue

            # 连续 2 次 D -> 淘汰
            if len(grades) >= 2 and all(g == "D" for g in grades[-2:]):
                if agent_id not in to_eliminate:
                    to_eliminate.append(agent_id)
                continue

            # 连续 3 次 C 且无上升趋势 -> 淘汰
            if len(grades) >= 3 and all(g == "C" for g in grades[-3:]):
                if score.trend != "up":
                    if agent_id not in to_eliminate:
                        to_eliminate.append(agent_id)
                    continue

        return to_eliminate

    def find_replacement(
        self,
        role: str,
        company_values: list[str],
        exclude_ids: list[str],
    ) -> AgentProfile | None:
        """从人才池找替补：同角色历史绩效最高 + 价值观契合"""
        candidates = self.pool.query(
            role_match=role,
            min_performance=0.0,
            values_match=company_values if company_values else None,
            exclude_ids=exclude_ids,
            sort_by="performance_avg",
            limit=1,
        )
        # 如果价值观匹配找不到，放宽条件
        if not candidates and company_values:
            candidates = self.pool.query(
                role_match=role,
                min_performance=0.0,
                exclude_ids=exclude_ids,
                sort_by="performance_avg",
                limit=1,
            )
        return candidates[0] if candidates else None

    def process_eliminations(
        self,
        review: ReviewResult,
        company_values: list[str],
        current_agent_ids: list[str],
    ) -> list[Replacement]:
        """执行淘汰流程，返回替换记录列表"""
        # 先更新评级记录
        self.update_grades(review)

        # 判定需淘汰的
        eliminate_ids = self.determine_eliminations(review)

        replacements: list[Replacement] = []
        used_replacement_ids: list[str] = list(current_agent_ids)

        for agent_id in eliminate_ids:
            score = review.scores.get(agent_id)
            if not score:
                continue

            # 构建淘汰原因
            reason = self._build_reason(agent_id, score.grade)

            # 寻找替补
            replacement = self.find_replacement(
                role=score.role,
                company_values=company_values,
                exclude_ids=used_replacement_ids,
            )

            replaced_by_id = replacement.id if replacement else ""
            replaced_by_name = replacement.name if replacement else "（人才池无可用替补）"

            if replacement:
                used_replacement_ids.append(replacement.id)

            replacements.append(
                Replacement(
                    removed_id=agent_id,
                    removed_name=score.agent_name,
                    reason=reason,
                    score=score.total_score,
                    grade=score.grade.value,
                    replaced_by_id=replaced_by_id,
                    replaced_by_name=replaced_by_name,
                )
            )

        return replacements

    def _build_reason(self, agent_id: str, grade: PerformanceGrade) -> str:
        """构建淘汰原因说明"""
        grades = self._consecutive_grades.get(agent_id, [])

        if grade == PerformanceGrade.F:
            return "单次绩效评级 F（不合格），触发立即淘汰"

        if len(grades) >= 2 and all(g == "D" for g in grades[-2:]):
            return f"连续 {len([g for g in grades[-2:] if g == 'D'])} 次绩效评级 D（待改进），触发淘汰"

        if len(grades) >= 3 and all(g == "C" for g in grades[-3:]):
            return "连续 3 次绩效评级 C（合格）且无上升趋势，触发淘汰"

        return f"绩效不达标（评级 {grade.value}）"
