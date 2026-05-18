"""基于健康报告生成优化建议的进化引擎。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .monitor import HealthReport


class OptimizationSuggestion(BaseModel):
    """单条优化建议。"""

    dimension: str = Field(description="相关维度名称")
    priority: str = Field(description="优先级：high/medium/low")
    suggestion: str = Field(description="建议内容")
    expected_improvement: float = Field(
        default=0.0, ge=0.0, le=30.0, description="预期改善分数"
    )


class EvolutionEngine:
    """基于健康报告生成优化建议的进化引擎。"""

    # 每个维度对应的具体优化方案
    _OPTIMIZATION_MAP: dict[str, list[dict]] = {
        "organizational": [
            {"suggestion": "为未定义角色的 Agent 分配明确职责", "improvement": 10.0},
            {"suggestion": "建立清晰的汇报关系和层级结构", "improvement": 8.0},
            {"suggestion": "制定并完善治理规则", "improvement": 7.0},
        ],
        "sociological": [
            {"suggestion": "设立定期跨部门沟通会议", "improvement": 10.0},
            {"suggestion": "建立冲突升级和解决流程", "improvement": 8.0},
            {"suggestion": "增加团队协作任务比重", "improvement": 6.0},
        ],
        "business": [
            {"suggestion": "引入任务质量审查环节", "improvement": 12.0},
            {"suggestion": "优化任务优先级排序和调度策略", "improvement": 10.0},
            {"suggestion": "设定明确的交付标准和验收条件", "improvement": 8.0},
        ],
        "psychological": [
            {"suggestion": "重新分配任务以平衡各 Agent 负载", "improvement": 12.0},
            {"suggestion": "设置单 Agent 最大并发任务上限", "improvement": 8.0},
            {"suggestion": "引入工作轮换机制", "improvement": 6.0},
        ],
        "ethical": [
            {"suggestion": "定义并公示公司核心价值观", "improvement": 10.0},
            {"suggestion": "建立任务分配的公平性审计机制", "improvement": 8.0},
            {"suggestion": "所有重大决策需记录理由和影响", "improvement": 7.0},
        ],
        "ecological": [
            {"suggestion": "为关键角色培养备份 Agent", "improvement": 10.0},
            {"suggestion": "优化资源使用率至 60%-85% 区间", "improvement": 8.0},
            {"suggestion": "建立资源预警机制", "improvement": 6.0},
        ],
        "information": [
            {"suggestion": "设定消息响应时间 SLA", "improvement": 10.0},
            {"suggestion": "建立信息广播机制减少信息孤岛", "improvement": 9.0},
            {"suggestion": "简化决策审批流程", "improvement": 7.0},
        ],
        "cultural": [
            {"suggestion": "建立每周回顾仪式", "improvement": 10.0},
            {"suggestion": "创建知识库并定期更新", "improvement": 9.0},
            {"suggestion": "设立价值观践行奖励机制", "improvement": 7.0},
        ],
        "political": [
            {"suggestion": "下放部分决策权至执行层", "improvement": 10.0},
            {"suggestion": "建立规则执行的监督和反馈机制", "improvement": 8.0},
            {"suggestion": "扩大决策参与范围", "improvement": 7.0},
        ],
        "temporal": [
            {"suggestion": "引入迭代式交付节奏", "improvement": 10.0},
            {"suggestion": "建立需求变更影响评估流程", "improvement": 8.0},
            {"suggestion": "设置里程碑检查点", "improvement": 7.0},
        ],
        "economic": [
            {"suggestion": "建立成本预警机制，超预算时自动提醒", "improvement": 10.0},
            {"suggestion": "分析高成本任务，寻找降本方案", "improvement": 9.0},
            {"suggestion": "定期评估投入产出比", "improvement": 7.0},
        ],
        "learning": [
            {"suggestion": "建立错误复盘机制，每次失败后总结教训", "improvement": 12.0},
            {"suggestion": "设定知识增长目标和衡量指标", "improvement": 8.0},
            {"suggestion": "引入 A/B 测试持续优化工作流程", "improvement": 7.0},
        ],
    }

    def analyze(self, report: HealthReport) -> list[OptimizationSuggestion]:
        """分析健康报告，生成优化建议。优先处理低分维度。"""
        suggestions: list[OptimizationSuggestion] = []

        # 按得分从低到高排序
        sorted_dims = sorted(report.dimensions, key=lambda d: d.score)

        for dim in sorted_dims:
            if dim.score >= 85:
                continue  # 高分维度不需要优化

            priority = self._determine_priority(dim.score)
            optimizations = self._OPTIMIZATION_MAP.get(dim.name, [])

            for opt in optimizations:
                suggestions.append(
                    OptimizationSuggestion(
                        dimension=dim.name,
                        priority=priority,
                        suggestion=opt["suggestion"],
                        expected_improvement=opt["improvement"],
                    )
                )

        # 按优先级排序：high > medium > low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))

        return suggestions

    def compare_reports(
        self, before: HealthReport, after: HealthReport
    ) -> dict:
        """对比两次健康报告，显示改善/退步。"""
        before_map = {d.name: d for d in before.dimensions}
        after_map = {d.name: d for d in after.dimensions}

        comparison: dict = {
            "overall_change": round(after.overall_score - before.overall_score, 1),
            "grade_change": f"{before.grade} -> {after.grade}",
            "improved": [],
            "declined": [],
            "stable": [],
        }

        for name, after_dim in after_map.items():
            before_dim = before_map.get(name)
            if not before_dim:
                continue

            diff = round(after_dim.score - before_dim.score, 1)
            entry = {
                "dimension": name,
                "display_name": after_dim.display_name,
                "before": before_dim.score,
                "after": after_dim.score,
                "change": diff,
            }

            if diff > 5:
                comparison["improved"].append(entry)
            elif diff < -5:
                comparison["declined"].append(entry)
            else:
                comparison["stable"].append(entry)

        return comparison

    @staticmethod
    def _determine_priority(score: float) -> str:
        """根据分数确定优化优先级。"""
        if score < 40:
            return "high"
        elif score < 60:
            return "medium"
        else:
            return "low"
