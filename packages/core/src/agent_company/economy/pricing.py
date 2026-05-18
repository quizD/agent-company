"""模型定价与成本计算工具。"""

from __future__ import annotations

from agent_company.economy.model_tiers import ModelTierRegistry


def calculate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    registry: ModelTierRegistry,
) -> float:
    """计算单次调用成本（美元）。

    Args:
        model_id: 模型 ID
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        registry: 模型等级注册表

    Returns:
        调用成本（美元）

    Raises:
        ValueError: 模型未在注册表中找到
    """
    model = registry.get_model(model_id)
    if model is None:
        raise ValueError(f"模型 '{model_id}' 未在注册表中找到")

    cost = (
        model.cost_per_1k_input * input_tokens / 1000
        + model.cost_per_1k_output * output_tokens / 1000
    )
    return round(cost, 8)


def estimate_project_cost(
    team_roles: dict[str, str],
    estimated_calls: int,
    registry: ModelTierRegistry,
    avg_input_tokens: int = 800,
    avg_output_tokens: int = 400,
) -> float:
    """估算项目总成本。

    Args:
        team_roles: 角色到模型 ID 的映射，如 {"主编": "claude-opus-4-6", "校对": "claude-haiku-4-5"}
        estimated_calls: 预估每个角色的总调用次数
        registry: 模型等级注册表
        avg_input_tokens: 每次调用平均输入 token 数
        avg_output_tokens: 每次调用平均输出 token 数

    Returns:
        预估项目总成本（美元）
    """
    total_cost = 0.0
    for _role, model_id in team_roles.items():
        cost_per_call = calculate_cost(model_id, avg_input_tokens, avg_output_tokens, registry)
        total_cost += cost_per_call * estimated_calls

    return round(total_cost, 6)
