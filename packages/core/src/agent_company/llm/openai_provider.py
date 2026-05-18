"""OpenAI 模型提供者实现."""

import os
import time
from typing import Any

from .provider import LLMProvider, LLMProviderError, LLMResponse

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

# 各模型的定价（美元 / 百万 token）
_OPENAI_PRICING: dict[str, tuple[float, float]] = {
    # (输入价格, 输出价格) per million tokens
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-2024-11-20": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4o-mini-2024-07-18": (0.15, 0.6),
}


class OpenAIProvider(LLMProvider):
    """OpenAI GPT 系列模型提供者.

    支持 GPT-4o、GPT-4o-mini 等模型。
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        """初始化 OpenAI 提供者.

        Args:
            model: 模型标识，默认使用 gpt-4o-mini
            api_key: API 密钥，为空时从环境变量 OPENAI_API_KEY 读取

        Raises:
            LLMProviderError: 当 openai 库未安装或 API 密钥缺失时抛出
        """
        if openai is None:
            raise LLMProviderError(
                "需要安装 openai 库: pip install openai",
                provider="openai",
            )

        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise LLMProviderError(
                "缺少 OpenAI API 密钥，请设置环境变量 OPENAI_API_KEY 或在初始化时传入 api_key",
                provider="openai",
            )

        self._client = openai.AsyncOpenAI(api_key=self._api_key)

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
        """调用 OpenAI API 获取补全结果.

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
        start_time = time.perf_counter()

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except openai.RateLimitError as e:
            raise LLMProviderError(
                f"OpenAI 速率限制: {e}",
                provider="openai",
                retryable=True,
            ) from e
        except openai.AuthenticationError as e:
            raise LLMProviderError(
                f"OpenAI 认证失败，请检查 API 密钥: {e}",
                provider="openai",
                retryable=False,
            ) from e
        except openai.APIError as e:
            raise LLMProviderError(
                f"OpenAI API 错误: {e}",
                provider="openai",
                retryable=True,
            ) from e
        except Exception as e:
            raise LLMProviderError(
                f"调用 OpenAI 时发生未知错误: {e}",
                provider="openai",
                retryable=False,
            ) from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 提取响应内容
        choice = response.choices[0]
        content = choice.message.content or ""

        input_tokens = response.usage.input_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
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
        # 查找匹配的定价，未知模型默认使用 gpt-4o-mini 价格
        pricing = _OPENAI_PRICING.get(self._model, (0.15, 0.6))
        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost
