"""任务类型与价值观组合匹配模块。

根据不同任务类型自动匹配合适的价值观权重组合。
"""

from __future__ import annotations

import random

from .vault import ValuePrinciple, ValueVault

# 不同任务类型对应的价值观权重配置
# 每个任务类型对7大分类设置不同的权重（总和为1.0）
TASK_VALUE_PROFILES: dict[str, dict[str, float]] = {
    "creative_writing": {
        "excellence": 0.30,
        "transparency": 0.10,
        "ownership": 0.15,
        "decision_making": 0.05,
        "learning": 0.20,
        "collaboration": 0.10,
        "long_termism": 0.10,
    },
    "software_development": {
        "excellence": 0.20,
        "transparency": 0.15,
        "ownership": 0.20,
        "decision_making": 0.15,
        "learning": 0.15,
        "collaboration": 0.10,
        "long_termism": 0.05,
    },
    "consulting": {
        "excellence": 0.15,
        "transparency": 0.20,
        "ownership": 0.10,
        "decision_making": 0.25,
        "learning": 0.10,
        "collaboration": 0.10,
        "long_termism": 0.10,
    },
    "crisis_response": {
        "excellence": 0.10,
        "transparency": 0.25,
        "ownership": 0.25,
        "decision_making": 0.25,
        "learning": 0.05,
        "collaboration": 0.05,
        "long_termism": 0.05,
    },
    "research": {
        "excellence": 0.20,
        "transparency": 0.15,
        "ownership": 0.10,
        "decision_making": 0.15,
        "learning": 0.25,
        "collaboration": 0.05,
        "long_termism": 0.10,
    },
    "project_management": {
        "excellence": 0.10,
        "transparency": 0.15,
        "ownership": 0.20,
        "decision_making": 0.20,
        "learning": 0.05,
        "collaboration": 0.20,
        "long_termism": 0.10,
    },
    "strategy": {
        "excellence": 0.15,
        "transparency": 0.10,
        "ownership": 0.10,
        "decision_making": 0.20,
        "learning": 0.10,
        "collaboration": 0.05,
        "long_termism": 0.30,
    },
}

# 默认权重（用于未定义的任务类型）
_DEFAULT_WEIGHTS: dict[str, float] = {
    "excellence": 0.20,
    "transparency": 0.15,
    "ownership": 0.15,
    "decision_making": 0.15,
    "learning": 0.15,
    "collaboration": 0.10,
    "long_termism": 0.10,
}


class ValueMatcher:
    """任务类型到价值观组合的匹配器。"""

    def __init__(self, vault: ValueVault) -> None:
        """初始化匹配器。

        Args:
            vault: 价值观库实例。
        """
        self._vault = vault

    def get_weighted_values(self, task_type: str) -> dict[str, float]:
        """返回任务类型对应的价值观权重。

        Args:
            task_type: 任务类型标识。

        Returns:
            分类名称到权重的映射字典。
        """
        return TASK_VALUE_PROFILES.get(task_type, _DEFAULT_WEIGHTS)

    def match_for_task(
        self, task_type: str, custom_weights: dict[str, float] | None = None
    ) -> list[ValuePrinciple]:
        """根据任务类型选择合适的价值观组合。

        基于权重按比例从各分类中抽取价值观。权重越高的分类抽取越多。

        Args:
            task_type: 任务类型标识。
            custom_weights: 自定义权重覆盖（可选）。

        Returns:
            匹配的价值观列表（通常 5-8 条）。
        """
        weights = custom_weights if custom_weights else self.get_weighted_values(task_type)

        # 总共抽取的目标数量
        total_count = 7
        result: list[ValuePrinciple] = []

        # 按权重分配每个分类的抽取数量
        sorted_categories = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        remaining = total_count
        for category, weight in sorted_categories:
            if remaining <= 0:
                break
            # 根据权重计算此分类应抽取的数量（至少 0，最多剩余数量）
            count = max(1, round(weight * total_count))
            count = min(count, remaining)

            pool = self._vault.get_by_category(category)
            if pool:
                actual_count = min(count, len(pool))
                result.extend(random.sample(pool, actual_count))
                remaining -= actual_count

        return result
