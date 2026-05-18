"""绩效考核系统模块。"""

from .elimination import EliminationEngine, Replacement
from .engine import PerformanceEngine, ReviewResult
from .kpi import ROLE_KPI_TEMPLATES, KPIDefinition, KPIRecord, KPITracker
from .scoring import PerformanceGrade, PerformanceScore, compute_grade, generate_feedback

__all__ = [
    "PerformanceEngine",
    "ReviewResult",
    "EliminationEngine",
    "Replacement",
    "KPIDefinition",
    "KPIRecord",
    "KPITracker",
    "ROLE_KPI_TEMPLATES",
    "PerformanceGrade",
    "PerformanceScore",
    "compute_grade",
    "generate_feedback",
]
