"""模型路由器 — 根据角色和任务类型智能分配模型."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .provider import LLMProvider, LLMProviderError, LLMResponse

logger = logging.getLogger(__name__)


class ModelRouter:
    """模型路由器.

    根据 Agent 角色或任务类型，自动将请求路由到最合适的模型提供者。
    支持回退机制和费用追踪。
    """

    def __init__(self, config: dict | None = None):
        """初始化模型路由器.

        Args:
            config: 可选配置字典，包含 role_model_map、task_model_map 等
        """
        self.role_model_map: dict[str, str] = {}
        self.task_model_map: dict[str, str] = {}
        self.providers: dict[str, LLMProvider] = {}
        self.fallback_model: str = ""
        self.total_cost: float = 0.0

        # 每个模型的费用追踪
        self._model_costs: dict[str, float] = defaultdict(float)
        self._model_call_counts: dict[str, int] = defaultdict(int)

        if config:
            self._apply_config(config)

    def register_provider(self, model_id: str, provider: LLMProvider) -> None:
        """注册模型提供者.

        Args:
            model_id: 模型标识
            provider: LLMProvider 实例
        """
        self.providers[model_id] = provider
        logger.info(f"已注册模型提供者: {model_id}")

        # 如果还没有回退模型，自动设为第一个注册的
        if not self.fallback_model:
            self.fallback_model = model_id

    def get_provider(
        self, role: str | None = None, task_type: str | None = None
    ) -> LLMProvider:
        """根据角色或任务类型获取对应的模型提供者.

        优先级：task_type > role > fallback

        Args:
            role: Agent 角色名称
            task_type: 任务类型

        Returns:
            匹配的 LLMProvider 实例

        Raises:
            LLMProviderError: 当无法找到合适的提供者时抛出
        """
        model_id = None

        # 任务类型优先
        if task_type and task_type in self.task_model_map:
            model_id = self.task_model_map[task_type]
        elif role and role in self.role_model_map:
            model_id = self.role_model_map[role]
        else:
            model_id = self.fallback_model

        if not model_id:
            raise LLMProviderError(
                "未配置任何模型提供者，请先调用 register_provider()",
                provider="router",
            )

        if model_id not in self.providers:
            # 尝试回退
            if self.fallback_model and self.fallback_model in self.providers:
                logger.warning(
                    f"模型 {model_id} 未注册，回退到 {self.fallback_model}"
                )
                model_id = self.fallback_model
            else:
                raise LLMProviderError(
                    f"模型 {model_id} 未注册且无可用回退模型",
                    provider="router",
                )

        return self.providers[model_id]

    async def complete(
        self,
        messages: list[dict],
        role: str | None = None,
        task_type: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """路由请求到合适的模型并获取补全结果.

        Args:
            messages: 消息列表
            role: Agent 角色名称（用于路由）
            task_type: 任务类型（用于路由）
            **kwargs: 传递给底层 provider.complete() 的额外参数

        Returns:
            LLMResponse 实例

        Raises:
            LLMProviderError: 当所有提供者都调用失败时抛出
        """
        provider = self.get_provider(role=role, task_type=task_type)

        try:
            response = await provider.complete(messages, **kwargs)
        except LLMProviderError as e:
            # 如果可重试且有回退模型，尝试回退
            if e.retryable and self.fallback_model and provider.model_id != self.fallback_model:
                logger.warning(
                    f"模型 {provider.model_id} 调用失败，尝试回退到 {self.fallback_model}"
                )
                fallback_provider = self.providers[self.fallback_model]
                response = await fallback_provider.complete(messages, **kwargs)
            else:
                raise

        # 更新费用追踪
        self.total_cost += response.cost
        self._model_costs[response.model] += response.cost
        self._model_call_counts[response.model] += 1

        return response

    def get_cost_summary(self) -> dict[str, Any]:
        """获取费用统计摘要.

        Returns:
            包含总费用和各模型明细的字典
        """
        per_model: list[dict[str, Any]] = []
        for model_id, cost in self._model_costs.items():
            per_model.append({
                "model": model_id,
                "cost": round(cost, 6),
                "calls": self._model_call_counts[model_id],
            })

        return {
            "total_cost": round(self.total_cost, 6),
            "per_model": sorted(per_model, key=lambda x: x["cost"], reverse=True),
        }

    @classmethod
    def from_config(cls, config: dict) -> ModelRouter:
        """从配置字典创建 ModelRouter 实例.

        配置格式示例::

            {
                "fallback_model": "gpt-4o-mini",
                "role_model_map": {
                    "ceo": "claude-sonnet-4-6",
                    "developer": "gpt-4o",
                    "intern": "gpt-4o-mini",
                },
                "task_model_map": {
                    "planning": "claude-sonnet-4-6",
                    "coding": "gpt-4o",
                    "summarization": "gpt-4o-mini",
                },
                "providers": {
                    "claude-sonnet-4-6": {
                        "type": "anthropic",
                        "api_key": "sk-...",  # 可选，默认读环境变量
                    },
                    "gpt-4o": {
                        "type": "openai",
                    },
                    "gpt-4o-mini": {
                        "type": "openai",
                    },
                }
            }

        Args:
            config: 配置字典

        Returns:
            配置好的 ModelRouter 实例
        """
        router = cls(config=config)

        # 根据 providers 配置自动创建并注册提供者
        providers_config = config.get("providers", {})
        for model_id, provider_config in providers_config.items():
            provider_type = provider_config.get("type", "")
            api_key = provider_config.get("api_key")

            try:
                provider = _create_provider(provider_type, model_id, api_key)
                router.register_provider(model_id, provider)
            except LLMProviderError as e:
                logger.warning(f"创建模型提供者 {model_id} 失败: {e}")

        return router

    def _apply_config(self, config: dict) -> None:
        """应用配置字典到路由器.

        Args:
            config: 配置字典
        """
        if "role_model_map" in config:
            self.role_model_map.update(config["role_model_map"])
        if "task_model_map" in config:
            self.task_model_map.update(config["task_model_map"])
        if "fallback_model" in config:
            self.fallback_model = config["fallback_model"]


def _create_provider(
    provider_type: str, model_id: str, api_key: str | None = None
) -> LLMProvider:
    """根据类型创建模型提供者实例.

    Args:
        provider_type: 提供者类型（"anthropic" 或 "openai"）
        model_id: 模型标识
        api_key: 可选 API 密钥

    Returns:
        LLMProvider 实例

    Raises:
        LLMProviderError: 当类型不支持时抛出
    """
    if provider_type == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=model_id, api_key=api_key)
    elif provider_type == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(model=model_id, api_key=api_key)
    else:
        raise LLMProviderError(
            f"不支持的模型提供者类型: {provider_type}，目前支持: anthropic, openai",
            provider="router",
        )
