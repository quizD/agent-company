"""Agent 实际能力计算——基础技能 × 模型乘数。"""

from __future__ import annotations

from agent_company.economy.model_tiers import ModelSpec


class AgentCapability:
    """Agent 的实际能力 = 基础技能 × 模型乘数。

    类比现实：一个人的产出 = 个人能力 × 所用工具的放大效果。
    """

    def __init__(self, base_skills: dict[str, float], model_spec: ModelSpec) -> None:
        """初始化 Agent 能力计算器。

        Args:
            base_skills: 基础技能字典，键为技能名称，值为熟练度 (0-1)
            model_spec: 所使用模型的规格
        """
        self._base_skills = base_skills
        self._model_spec = model_spec

    @property
    def base_skills(self) -> dict[str, float]:
        """基础技能字典。"""
        return self._base_skills

    @property
    def model_spec(self) -> ModelSpec:
        """当前使用的模型规格。"""
        return self._model_spec

    @property
    def effective_skills(self) -> dict[str, float]:
        """实际能力 = base_skill × (model_capability / 100)。

        模型能力作为乘数，决定了 Agent 能发挥出多少基础技能。
        """
        multiplier = self._model_spec.capability / 100.0
        return {
            skill: round(value * multiplier, 4)
            for skill, value in self._base_skills.items()
        }

    @property
    def avg_capability(self) -> float:
        """平均有效能力分。"""
        skills = self.effective_skills
        if not skills:
            return 0.0
        return sum(skills.values()) / len(skills)

    def estimate_hourly_cost(
        self,
        avg_tokens_per_call: int = 1000,
        calls_per_hour: int = 10,
    ) -> float:
        """估算每小时成本（美元）。

        Args:
            avg_tokens_per_call: 每次调用的平均 token 数（输入+输出各半计算）
            calls_per_hour: 每小时调用次数

        Returns:
            预估每小时美元成本
        """
        # 假设输入输出各占一半 token
        input_tokens = avg_tokens_per_call // 2
        output_tokens = avg_tokens_per_call // 2

        cost_per_call = (
            self._model_spec.cost_per_1k_input * input_tokens / 1000
            + self._model_spec.cost_per_1k_output * output_tokens / 1000
        )
        return cost_per_call * calls_per_hour
