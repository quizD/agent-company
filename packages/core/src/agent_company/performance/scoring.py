"""绩效评分标准模块。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PerformanceGrade(str, Enum):
    """绩效等级"""

    S = "S"  # 90-100 卓越
    A = "A"  # 80-89  优秀
    B = "B"  # 70-79  良好
    C = "C"  # 60-69  合格
    D = "D"  # 50-59  待改进
    F = "F"  # <50    不合格


class PerformanceScore(BaseModel):
    """绩效评分结果"""

    agent_id: str
    agent_name: str
    role: str
    kpi_scores: dict[str, float] = Field(default_factory=dict, description="各项KPI得分")
    total_score: float = Field(default=0.0, description="综合分(0-100)")
    grade: PerformanceGrade = PerformanceGrade.C
    rank: int = 0
    trend: str = "stable"  # up/down/stable
    feedback: str = ""  # 改进建议


def compute_grade(score: float) -> PerformanceGrade:
    """分数 -> 等级映射"""
    if score >= 90:
        return PerformanceGrade.S
    elif score >= 80:
        return PerformanceGrade.A
    elif score >= 70:
        return PerformanceGrade.B
    elif score >= 60:
        return PerformanceGrade.C
    elif score >= 50:
        return PerformanceGrade.D
    else:
        return PerformanceGrade.F


def generate_feedback(score: PerformanceScore) -> str:
    """根据得分生成反馈建议"""
    parts: list[str] = []

    if score.grade in (PerformanceGrade.S, PerformanceGrade.A):
        parts.append(f"{score.agent_name} 表现优异，综合得分 {score.total_score:.1f}。")
        # 找出最高分 KPI 进行表扬
        if score.kpi_scores:
            best_kpi = max(score.kpi_scores, key=score.kpi_scores.get)  # type: ignore[arg-type]
            parts.append(f"尤其在「{best_kpi}」方面表现突出。")
        parts.append("建议继续保持并带动团队提升。")
    elif score.grade == PerformanceGrade.B:
        parts.append(f"{score.agent_name} 表现良好，综合得分 {score.total_score:.1f}。")
        # 找出最低分 KPI 给出建议
        if score.kpi_scores:
            worst_kpi = min(score.kpi_scores, key=score.kpi_scores.get)  # type: ignore[arg-type]
            parts.append(f"建议在「{worst_kpi}」方面进一步提升。")
    elif score.grade == PerformanceGrade.C:
        parts.append(f"{score.agent_name} 表现合格但有提升空间，综合得分 {score.total_score:.1f}。")
        if score.kpi_scores:
            weak_kpis = [k for k, v in score.kpi_scores.items() if v < 60]
            if weak_kpis:
                parts.append(f"需重点改进：{'、'.join(weak_kpis)}。")
        parts.append("请制定具体改进计划。")
    elif score.grade == PerformanceGrade.D:
        parts.append(f"⚠️ {score.agent_name} 表现待改进，综合得分 {score.total_score:.1f}。")
        if score.kpi_scores:
            weak_kpis = [k for k, v in score.kpi_scores.items() if v < 50]
            if weak_kpis:
                parts.append(f"严重不足项：{'、'.join(weak_kpis)}。")
        parts.append("如持续低于标准将面临淘汰风险。")
    else:  # F
        parts.append(f"❌ {score.agent_name} 表现不合格，综合得分 {score.total_score:.1f}。")
        parts.append("已触发淘汰条件，建议立即替换。")

    # 趋势信息
    if score.trend == "up":
        parts.append("趋势向好，继续努力。")
    elif score.trend == "down":
        parts.append("近期趋势下滑，需引起重视。")

    return " ".join(parts)
