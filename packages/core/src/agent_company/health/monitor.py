"""十二维健康监控器主类。"""

from __future__ import annotations

import time
from copy import deepcopy

from pydantic import BaseModel, Field

from .dimensions import ALL_DIMENSIONS, DimensionScorer, HealthDimension


class HealthReport(BaseModel):
    """健康度报告。"""

    timestamp: float = Field(default_factory=time.time, description="报告生成时间戳")
    dimensions: list[HealthDimension] = Field(default_factory=list, description="12 维度得分")
    overall_score: float = Field(default=0.0, description="加权总分 (0-100)")
    grade: str = Field(default="C", description="等级：S/A/B/C/D/F")
    strengths: list[str] = Field(default_factory=list, description="优势维度")
    weaknesses: list[str] = Field(default_factory=list, description="弱项维度")
    recommendations: list[str] = Field(default_factory=list, description="改善建议")
    radar_data: dict[str, float] = Field(default_factory=dict, description="雷达图数据")


class HealthMonitor:
    """十二维健康度监控器。"""

    def __init__(self) -> None:
        self.scorer = DimensionScorer()
        self._history: list[HealthReport] = []

    # 维度名 -> 评分方法的映射
    _SCORE_METHODS = {
        "organizational": DimensionScorer.score_organizational,
        "sociological": DimensionScorer.score_sociological,
        "business": DimensionScorer.score_business,
        "psychological": DimensionScorer.score_psychological,
        "ethical": DimensionScorer.score_ethical,
        "ecological": DimensionScorer.score_ecological,
        "information": DimensionScorer.score_information,
        "cultural": DimensionScorer.score_cultural,
        "political": DimensionScorer.score_political,
        "temporal": DimensionScorer.score_temporal,
        "economic": DimensionScorer.score_economic,
        "learning": DimensionScorer.score_learning,
    }

    def evaluate(self, company_data: dict) -> HealthReport:
        """执行全面健康评估。

        company_data 包含:
        - agents: list[dict] — 每个 Agent 的信息
        - departments: list[dict] — 部门信息
        - messages: list[dict] — 通信记录
        - tasks: list[dict] — 任务状态
        - performance_scores: dict — 绩效数据
        - budget_info: dict — 预算数据
        - governance_rules: list — 治理规则
        - values: list[str] — 公司价值观
        """
        scored_dimensions: list[HealthDimension] = []
        total_weighted_score = 0.0
        total_weight = 0.0

        for dim_template in ALL_DIMENSIONS:
            dim = deepcopy(dim_template)
            score_method = self._SCORE_METHODS.get(dim.name)
            if score_method:
                dim.score = score_method(company_data)
            scored_dimensions.append(dim)
            total_weighted_score += dim.score * dim.weight
            total_weight += dim.weight

        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # 确定等级
        grade = self._calculate_grade(overall_score)

        # 确定优势和弱项
        sorted_dims = sorted(scored_dimensions, key=lambda d: d.score, reverse=True)
        strengths = [f"{d.display_name}({d.score:.0f})" for d in sorted_dims[:3] if d.score >= 70]
        weaknesses = [f"{d.display_name}({d.score:.0f})" for d in sorted_dims[-3:] if d.score < 60]

        # 生成建议
        recommendations = self._generate_recommendations(scored_dimensions)

        # 雷达图数据
        radar_data = {d.display_name: d.score for d in scored_dimensions}

        report = HealthReport(
            timestamp=time.time(),
            dimensions=scored_dimensions,
            overall_score=round(overall_score, 1),
            grade=grade,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            radar_data=radar_data,
        )

        self._history.append(report)
        return report

    def get_trend(self) -> dict[str, str]:
        """各维度趋势：up/down/stable。需要至少 2 次评估记录。"""
        if len(self._history) < 2:
            return {dim.name: "stable" for dim in ALL_DIMENSIONS}

        current = self._history[-1]
        previous = self._history[-2]

        trend: dict[str, str] = {}
        current_map = {d.name: d.score for d in current.dimensions}
        previous_map = {d.name: d.score for d in previous.dimensions}

        for dim_name in current_map:
            diff = current_map[dim_name] - previous_map.get(dim_name, 0)
            if diff > 5:
                trend[dim_name] = "up"
            elif diff < -5:
                trend[dim_name] = "down"
            else:
                trend[dim_name] = "stable"

        return trend

    def print_report(self, report: HealthReport) -> str:
        """生成可打印的文本报告。"""
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("          十二维健康度评估报告")
        lines.append("=" * 60)
        lines.append(f"  综合评分: {report.overall_score:.1f}/100  等级: {report.grade}")
        lines.append("-" * 60)
        lines.append("  各维度得分:")
        lines.append("")

        for dim in report.dimensions:
            bar_len = int(dim.score / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {dim.display_name:<8} [{bar}] {dim.score:.1f}")

        lines.append("")
        lines.append("-" * 60)

        if report.strengths:
            lines.append("  优势: " + ", ".join(report.strengths))
        if report.weaknesses:
            lines.append("  弱项: " + ", ".join(report.weaknesses))

        if report.recommendations:
            lines.append("")
            lines.append("  改善建议:")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"    {i}. {rec}")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def _calculate_grade(score: float) -> str:
        """根据分数计算等级。"""
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    @staticmethod
    def _generate_recommendations(dimensions: list[HealthDimension]) -> list[str]:
        """基于弱项维度生成改善建议。"""
        recommendations: list[str] = []
        suggestion_map = {
            "organizational": "完善组织架构，确保每个 Agent 都有明确的角色定义和汇报关系",
            "sociological": "加强团队沟通，鼓励跨部门协作，建立冲突解决机制",
            "business": "关注任务交付质量和效率，建立质量检查流程",
            "psychological": "平衡工作负载，避免个别 Agent 过载，关注满意度",
            "ethical": "明确并践行价值观，确保任务分配公平，决策过程透明",
            "ecological": "优化资源利用率，确保系统可持续运行，为关键角色建立备份",
            "information": "改善信息流通效率，缩短响应时间，提高决策速度",
            "cultural": "培养团队文化仪式，建立知识管理体系，促进知识传承",
            "political": "优化权力分配，确保治理规则被有效执行，提高参与度",
            "temporal": "加强进度管理，保持稳定的工作节奏，提高变更适应力",
            "economic": "控制成本，优化预算利用率，提高投入产出比",
            "learning": "建立错误修正机制，促进知识积累，持续改进工作流程",
        }

        for dim in sorted(dimensions, key=lambda d: d.score):
            if dim.score < 60 and dim.name in suggestion_map:
                recommendations.append(suggestion_map[dim.name])

        return recommendations[:5]  # 最多返回5条建议
