"""十二维健康监控系统。

通过组织学、社会学、商业、心理学、伦理学、生态/系统论、
信息论/控制论、人类学/文化、政治学、时间、经济、学习
共 12 个维度全面评估 AI Agent 公司的运行健康度。
"""

from __future__ import annotations

from .dimensions import ALL_DIMENSIONS, DimensionScorer, HealthDimension
from .evolution import EvolutionEngine, OptimizationSuggestion
from .monitor import HealthMonitor, HealthReport

__all__ = [
    "ALL_DIMENSIONS",
    "DimensionScorer",
    "EvolutionEngine",
    "HealthDimension",
    "HealthMonitor",
    "HealthReport",
    "OptimizationSuggestion",
]
