"""KPI 定义与追踪模块。"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field


class KPIDefinition(BaseModel):
    """KPI 指标定义"""

    name: str = Field(description="指标名称")
    measure: str = Field(description="度量方式")
    target: str = Field(description="目标值表达式，如 '>=2000'")
    weight: float = Field(default=1.0, description="权重")
    lower_is_better: bool = Field(default=False, description="是否越低越好")


class KPIRecord(BaseModel):
    """单次 KPI 度量记录"""

    kpi_name: str
    value: float
    timestamp: float = Field(default_factory=time.time)
    tick: int = 0


class KPITracker:
    """追踪单个 Agent 的 KPI 数据"""

    def __init__(self, agent_id: str, definitions: list[KPIDefinition]) -> None:
        self.agent_id = agent_id
        self.definitions = {d.name: d for d in definitions}
        self._records: dict[str, list[KPIRecord]] = {d.name: [] for d in definitions}

    def record(self, kpi_name: str, value: float, tick: int = 0) -> None:
        """记录一次 KPI 度量值"""
        if kpi_name not in self._records:
            self._records[kpi_name] = []
        self._records[kpi_name].append(
            KPIRecord(kpi_name=kpi_name, value=value, tick=tick)
        )

    def get_latest(self, kpi_name: str) -> float | None:
        """获取某项 KPI 最新值"""
        records = self._records.get(kpi_name, [])
        if not records:
            return None
        return records[-1].value

    def get_average(self, kpi_name: str) -> float:
        """获取某项 KPI 的平均值"""
        records = self._records.get(kpi_name, [])
        if not records:
            return 0.0
        return sum(r.value for r in records) / len(records)

    def get_trend(self, kpi_name: str) -> str:
        """获取某项 KPI 的趋势：up / down / stable"""
        records = self._records.get(kpi_name, [])
        if len(records) < 3:
            return "stable"
        # 取最近5条记录判断趋势
        recent = records[-5:]
        first_half = recent[: len(recent) // 2]
        second_half = recent[len(recent) // 2 :]
        avg_first = sum(r.value for r in first_half) / len(first_half)
        avg_second = sum(r.value for r in second_half) / len(second_half)
        diff = avg_second - avg_first
        threshold = max(abs(avg_first) * 0.05, 0.01)  # 5% 变化阈值
        if diff > threshold:
            return "up"
        elif diff < -threshold:
            return "down"
        return "stable"

    def evaluate(self) -> dict[str, float]:
        """对所有 KPI 进行评分，返回 kpi_name -> 0-100 得分"""
        scores: dict[str, float] = {}
        for name, definition in self.definitions.items():
            avg = self.get_average(name)
            score = self._score_kpi(definition, avg)
            scores[name] = score
        return scores

    def _score_kpi(self, definition: KPIDefinition, value: float) -> float:
        """根据 KPI 定义和实际值计算得分（0-100）"""
        target_str = definition.target.strip()
        # 解析目标值
        if target_str.startswith(">="):
            target_val = float(target_str[2:])
            if definition.lower_is_better:
                # 越低越好，但目标是下限 — 不常见，按比例算
                score = max(0, min(100, (target_val / max(value, 0.001)) * 100))
            else:
                score = max(0, min(100, (value / max(target_val, 0.001)) * 100))
        elif target_str.startswith("<="):
            target_val = float(target_str[2:])
            if definition.lower_is_better:
                score = max(0, min(100, (target_val / max(value, 0.001)) * 100))
            else:
                score = max(0, min(100, (1 - (value - target_val) / max(target_val, 0.001)) * 100))
        elif target_str.startswith("=="):
            target_val = float(target_str[2:])
            deviation = abs(value - target_val) / max(target_val, 0.001)
            score = max(0, (1 - deviation) * 100)
        else:
            # 默认当作 >= 处理
            try:
                target_val = float(target_str)
                score = max(0, min(100, (value / max(target_val, 0.001)) * 100))
            except ValueError:
                score = 50.0  # 无法解析时给中等分
        return round(score, 2)


# 预定义 KPI 模板（按角色）
ROLE_KPI_TEMPLATES: dict[str, list[KPIDefinition]] = {
    "通用": [
        KPIDefinition(name="响应性", measure="avg_response_time", target="<=5.0", weight=1.0, lower_is_better=True),
        KPIDefinition(name="协作贡献", measure="collaboration_actions", target=">=5", weight=1.0),
        KPIDefinition(name="自主性", measure="autonomous_decisions", target=">=3", weight=0.8),
        KPIDefinition(name="学习能力", measure="skill_improvement_rate", target=">=0.1", weight=0.8),
    ],
    "主编": [
        KPIDefinition(name="方向把控", measure="direction_alignment_score", target=">=0.8", weight=1.5),
        KPIDefinition(name="决策效率", measure="decision_rounds_avg", target="<=3", weight=1.2, lower_is_better=True),
        KPIDefinition(name="团队协调", measure="team_coordination_score", target=">=0.7", weight=1.3),
    ],
    "作者": [
        KPIDefinition(name="产出量", measure="word_count_per_tick", target=">=2000", weight=1.0),
        KPIDefinition(name="内容质量", measure="content_quality_score", target=">=0.8", weight=1.5),
        KPIDefinition(name="按时交付", measure="on_time_delivery_rate", target=">=0.9", weight=1.2),
    ],
    "编辑": [
        KPIDefinition(name="问题发现率", measure="issue_detection_rate", target=">=0.7", weight=1.3),
        KPIDefinition(name="反馈质量", measure="feedback_quality_score", target=">=0.8", weight=1.2),
        KPIDefinition(name="周转速度", measure="turnaround_time", target="<=2.0", weight=1.0, lower_is_better=True),
    ],
    "工程师": [
        KPIDefinition(name="代码质量", measure="code_quality_score", target=">=0.85", weight=1.5),
        KPIDefinition(name="交付速度", measure="delivery_speed", target=">=0.8", weight=1.0),
        KPIDefinition(name="bug率", measure="bug_rate", target="<=0.1", weight=1.3, lower_is_better=True),
    ],
    "设计师": [
        KPIDefinition(name="方案多样性", measure="design_variety_score", target=">=0.7", weight=1.2),
        KPIDefinition(name="修改次数", measure="revision_count", target="<=3", weight=1.0, lower_is_better=True),
    ],
    "项目经理": [
        KPIDefinition(name="进度把控", measure="schedule_adherence", target=">=0.85", weight=1.5),
        KPIDefinition(name="风险管理", measure="risk_mitigation_score", target=">=0.7", weight=1.2),
        KPIDefinition(name="团队满意度", measure="team_satisfaction", target=">=0.75", weight=1.0),
    ],
}
