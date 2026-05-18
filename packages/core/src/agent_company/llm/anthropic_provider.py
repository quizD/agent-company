"""Anthropic (Claude) 模型提供者实现."""

import os
import time
from typing import Any

from .provider import LLMProvider, LLMProviderError, LLMResponse

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

# 各模型的定价（美元 / 百万 token）
_ANTHROPIC_PRICING: dict[str, tuple[float, float]] = {
    # (输入价格, 输出价格) per million tokens
    "claude-opus-4-6": (15.0, 75.0),
    "claude-opus-4-20250514": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-3-5-sonnet-20241022": (3.0, 15.0),
    "claude-3-5-haiku-20241022": (0.25, 1.25),
    "claude-3-haiku-20240307": (0.25, 1.25),
}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude 系列模型提供者.

    支持 Claude Opus、Sonnet、Haiku 等模型。
    """

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        """初始化 Anthropic 提供者.

        Args:
            model: 模型标识，默认使用 claude-sonnet-4-6
            api_key: API 密钥，为空时从环境变量 ANTHROPIC_API_KEY 读取

        Raises:
            LLMProviderError: 当 anthropic 库未安装或 API 密钥缺失时抛出
        """
        if anthropic is None:
            raise LLMProviderError(
                "需要安装 anthropic 库: pip install anthropic",
                provider="anthropic",
            )

        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise LLMProviderError(
                "缺少 Anthropic API 密钥，请设置环境变量 ANTHROPIC_API_KEY 或在初始化时传入 api_key",
                provider="anthropic",
            )

        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    @property
    def model_id(self) -> str:
        """返回当前模型标识."""
        return self._model

    async def complete(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """调用 Anthropic API 获取补全结果.

        Args:
            messages: 消息列表，支持 system/user/assistant 角色
            temperature: 采样温度
            max_tokens: 最大生成 token 数
            **kwargs: 额外参数传递给 API

        Returns:
            LLMResponse 实例

        Raises:
            LLMProviderError: 调用失败时抛出，包含是否可重试信息
        """
        # 从消息列表中提取 system 消息
        system_message = ""
        api_messages: list[dict] = []
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg["content"]
            else:
                api_messages.append(msg)

        start_time = time.perf_counter()

        try:
            create_kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": api_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }
            if system_message:
                create_kwargs["system"] = system_message

            response = await self._client.messages.create(**create_kwargs)

        except anthropic.RateLimitError as e:
            raise LLMProviderError(
                f"Anthropic 速率限制: {e}",
                provider="anthropic",
                retryable=True,
            ) from e
        except anthropic.AuthenticationError as e:
            raise LLMProviderError(
                f"Anthropic 认证失败，请检查 API 密钥: {e}",
                provider="anthropic",
                retryable=False,
            ) from e
        except anthropic.APIError as e:
            raise LLMProviderError(
                f"Anthropic API 错误: {e}",
                provider="anthropic",
                retryable=True,
            ) from e
        except Exception as e:
            raise LLMProviderError(
                f"调用 Anthropic 时发生未知错误: {e}",
                provider="anthropic",
                retryable=False,
            ) from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 提取响应内容
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = self.estimate_cost(input_tokens, output_tokens)

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            latency_ms=latency_ms,
            cost=cost,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """根据模型定价估算费用.

        Args:
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量

        Returns:
            估算费用（美元）
        """
        # 查找匹配的定价，未知模型默认使用 sonnet 价格
        pricing = _ANTHROPIC_PRICING.get(self._model, (3.0, 15.0))
        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost
