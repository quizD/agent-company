"""Agent 状态管理模块。

定义 Agent 的运行状态枚举和工作负载模型。
"""

from enum import Enum

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Agent 运行状态枚举。"""

    IDLE = "idle"  # 空闲，等待任务
    THINKING = "thinking"  # 正在推理/思考
    COMMUNICATING = "communicating"  # 正在与其他 Agent 通信
    EXECUTING = "executing"  # 正在执行动作


class AgentWorkload(BaseModel):
    """Agent 工作负载模型，用于衡量当前资源使用情况。"""

    current_tasks: int = Field(default=0, description="当前正在处理的任务数")
    max_tasks: int = Field(default=5, description="最大并行任务数")
    context_tokens_used: int = Field(default=0, description="已使用的上下文 token 数")
    context_tokens_limit: int = Field(default=128000, description="上下文 token 上限")

    @property
    def is_overloaded(self) -> bool:
        """判断 Agent 是否过载。

        当任务数达到上限或 token 使用超过 90% 时视为过载。
        """
        return (
            self.current_tasks >= self.max_tasks
            or self.context_tokens_used >= self.context_tokens_limit * 0.9
        )

    @property
    def load_factor(self) -> float:
        """计算负载因子，范围 0-1。

        取任务负载和 token 负载的较大值。
        """
        task_load = self.current_tasks / self.max_tasks if self.max_tasks > 0 else 0.0
        token_load = (
            self.context_tokens_used / self.context_tokens_limit
            if self.context_tokens_limit > 0
            else 0.0
        )
        return min(max(task_load, token_load), 1.0)
