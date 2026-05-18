"""Ollama 本地模型提供者实现。

支持通过 Ollama 运行本地大模型（如 Qwen、LLaMA 等），
零 API 成本，适合 B/C 级 Agent 使用。
"""

from __future__ import annotations

import time
from typing import Any

from .provider import LLMProvider, LLMProviderError, LLMResponse

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]


class OllamaProvider(LLMProvider):
    """Ollama 本地模型提供者。

    通过 Ollama REST API 调用本地部署的大模型，
    支持 Qwen、LLaMA、Mistral 等开源模型。
    成本为零（仅本地电力消耗）。
    """

    def __init__(
        self,
        model: str = "qwen2.5:32b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        """初始化 Ollama 提供者。

        Args:
            model: 模型名称（Ollama 中注册的名称）。
            base_url: Ollama 服务地址。
            timeout: 请求超时时间（秒）。
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def model_id(self) -> str:
        """返回当前模型标识。"""
        return f"ollama/{self._model}"

    async def complete(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """调用 Ollama API 获取补全结果。

        使用 Ollama 的 /api/chat 端点，兼容 OpenAI 消息格式。

        Args:
            messages: 消息列表，支持 system/user/assistant 角色。
            temperature: 采样温度。
            max_tokens: 最大生成 token 数。
            **kwargs: 额外参数。

        Returns:
            LLMResponse 实例。

        Raises:
            LLMProviderError: 调用失败时抛出。
        """
        if httpx is None:
            raise LLMProviderError(
                "需要安装 httpx 库: pip install httpx",
                provider="ollama",
            )

        url = f"{self._base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as e:
            raise LLMProviderError(
                f"无法连接到 Ollama 服务 ({self._base_url})。"
                "请确认 Ollama 已启动: ollama serve",
                provider="ollama",
                retryable=True,
            ) from e
        except httpx.TimeoutException as e:
            raise LLMProviderError(
                f"Ollama 请求超时 ({self._timeout}s)，"
                "模型可能正在加载或推理过慢",
                provider="ollama",
                retryable=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Ollama API 错误: {e.response.status_code} {e.response.text}",
                provider="ollama",
                retryable=e.response.status_code >= 500,
            ) from e
        except Exception as e:
            raise LLMProviderError(
                f"调用 Ollama 时发生未知错误: {e}",
                provider="ollama",
                retryable=False,
            ) from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 解析响应
        message_data = data.get("message", {})
        content = message_data.get("content", "")

        # Ollama 返回的 token 统计
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model_id,
            latency_ms=latency_ms,
            cost=0.0,  # 本地模型零成本
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """本地模型成本为零。

        Args:
            input_tokens: 输入 token 数量。
            output_tokens: 输出 token 数量。

        Returns:
            始终返回 0.0。
        """
        return 0.0

    async def list_models(self) -> list[str]:
        """列出 Ollama 中已安装的模型。

        Returns:
            模型名称列表。

        Raises:
            LLMProviderError: 无法连接时抛出。
        """
        if httpx is None:
            raise LLMProviderError(
                "需要安装 httpx 库: pip install httpx",
                provider="ollama",
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            raise LLMProviderError(
                f"无法获取 Ollama 模型列表: {e}",
                provider="ollama",
            ) from e

    async def is_available(self) -> bool:
        """检查 Ollama 服务是否可用。

        Returns:
            True 表示服务可用。
        """
        if httpx is None:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
