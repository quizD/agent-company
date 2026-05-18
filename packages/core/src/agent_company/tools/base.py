"""Agent 工具基类 — 定义工具的统一接口"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具执行结果"""

    success: bool
    output: str = ""
    error: str | None = None
    metadata: dict[str, Any] = {}


class BaseTool(ABC):
    """
    Agent 工具基类

    所有工具必须实现 execute 方法。
    工具是 Agent 与外部世界交互的接口。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（用于 Agent 理解工具用途）"""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """执行工具"""
        ...

    def to_schema(self) -> dict:
        """导出工具 schema（用于 LLM function calling）"""
        return {
            "name": self.name,
            "description": self.description,
        }


class CodeExecutor(BaseTool):
    """代码执行工具（沙箱环境）"""

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return "在沙箱中执行 Python 代码并返回结果"

    async def execute(self, code: str = "", language: str = "python", **kwargs: Any) -> ToolResult:
        """执行代码（当前为占位实现）"""
        # TODO: 集成真实的代码沙箱（如 e2b, modal, 或本地 subprocess）
        return ToolResult(
            success=True,
            output=f"[CodeExecutor] 已接收代码（{len(code)} 字符），语言: {language}",
            metadata={"language": language, "code_length": len(code)},
        )


class FileSystem(BaseTool):
    """文件系统操作工具"""

    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "读写文件系统中的文件"

    async def execute(
        self,
        action: str = "read",
        path: str = "",
        content: str = "",
        **kwargs: Any,
    ) -> ToolResult:
        """文件操作（当前为占位实现）"""
        # TODO: 集成真实的文件系统操作（含权限控制）
        if action == "read":
            return ToolResult(
                success=True,
                output=f"[FileSystem] 读取文件: {path}",
            )
        elif action == "write":
            return ToolResult(
                success=True,
                output=f"[FileSystem] 写入文件: {path} ({len(content)} 字符)",
            )
        else:
            return ToolResult(success=False, error=f"未知操作: {action}")


class WebSearch(BaseTool):
    """网络搜索工具"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "搜索互联网获取信息"

    async def execute(self, query: str = "", **kwargs: Any) -> ToolResult:
        """搜索（当前为占位实现）"""
        # TODO: 集成真实搜索 API（如 Tavily, Serper, Exa）
        return ToolResult(
            success=True,
            output=f"[WebSearch] 搜索: {query}",
            metadata={"query": query},
        )
