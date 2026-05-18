"""LLM 抽象层 — 提供统一的大模型调用接口."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """大模型调用响应结果."""

    content: str = Field(description="模型生成的文本内容")
    input_tokens: int = Field(description="输入 token 数量")
    output_tokens: int = Field(description="输出 token 数量")
    model: str = Field(description="实际使用的模型标识")
    latency_ms: float = Field(description="请求耗时（毫秒）")
    cost: float = Field(default=0.0, description="本次调用的估算费用（美元）")


class LLMProvider(ABC):
    """大模型提供者抽象基类.

    所有具体的模型提供者（Anthropic、OpenAI 等）都必须实现此接口。
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """返回当前模型的唯一标识."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """发送消息列表并获取模型补全结果.

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 采样温度，越高越随机
            max_tokens: 最大生成 token 数
            **kwargs: 额外参数，传递给底层 API

        Returns:
            LLMResponse 实例

        Raises:
            LLMProviderError: 当调用失败时抛出
        """
        ...

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """根据 token 数量估算费用（美元）.

        Args:
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量

        Returns:
            估算费用（美元）
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model_id}>"


class LLMProviderError(Exception):
    """LLM 调用过程中发生的错误."""

    def __init__(self, message: str, provider: str = "", retryable: bool = False):
        self.provider = provider
        self.retryable = retryable
        super().__init__(message)
