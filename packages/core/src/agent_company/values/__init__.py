"""价值观体系模块。

提供价值观库管理、行为注入、审计检测和任务匹配功能。
"""

from __future__ import annotations

from .matcher import TASK_VALUE_PROFILES, ValueMatcher
from .system import ValueAudit, ValueSystem
from .vault import VALUE_CATEGORIES, ValuePrinciple, ValueVault

__all__ = [
    "VALUE_CATEGORIES",
    "TASK_VALUE_PROFILES",
    "ValueAudit",
    "ValueMatcher",
    "ValuePrinciple",
    "ValueSystem",
    "ValueVault",
]
