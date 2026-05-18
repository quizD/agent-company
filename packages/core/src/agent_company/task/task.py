"""任务定义模块 — Task 是用户提交给公司的工作单元"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"  # 等待分配
    IN_PROGRESS = "in_progress"  # 执行中
    IN_REVIEW = "in_review"  # 审核中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class TaskPriority(str, Enum):
    """任务优先级"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Deliverable(BaseModel):
    """交付物定义"""

    name: str
    description: str = ""
    file_path: str | None = None  # 产出文件路径
    content: str | None = None  # 产出内容（文本类）
    quality_score: float | None = None  # 质量评分 (0-100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """用户提交的任务"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # 交付要求
    deliverables_spec: list[str] = Field(default_factory=list)  # 期望的交付物描述
    quality_standards: dict[str, str] = Field(default_factory=dict)  # 质量标准

    # 约束
    deadline: str | None = None  # 截止时间描述
    max_ticks: int = 50  # 最大模拟轮数
    budget_usd: float | None = None  # 预算限制

    # 用户偏好
    preferences: dict[str, Any] = Field(default_factory=dict)

    # 执行结果
    deliverables: list[Deliverable] = Field(default_factory=list)  # 实际交付物
    assigned_agents: list[str] = Field(default_factory=list)  # 分配的 Agent IDs

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        """标记任务开始"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, deliverables: list[Deliverable] | None = None) -> None:
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if deliverables:
            self.deliverables = deliverables

    def fail(self, reason: str = "") -> None:
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.preferences["failure_reason"] = reason


class SubTask(BaseModel):
    """子任务 — 由 Process 拆解出的执行单元"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_task_id: str
    title: str
    description: str = ""
    assigned_role: str  # 分配给哪个角色
    assigned_agent_id: str | None = None  # 实际执行的 Agent
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    # 执行约束
    depends_on: list[str] = Field(default_factory=list)  # 依赖的 SubTask IDs
    max_ticks: int = 10

    # 结果
    output: str | None = None
    artifacts: list[Deliverable] = Field(default_factory=list)
    quality_score: float | None = None

    # 时间
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def is_ready(self) -> bool:
        """是否可以开始（所有依赖已完成）"""
        # 实际检查需要在 Pipeline 层做
        return self.status == TaskStatus.PENDING

    def start(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, output: str = "", artifacts: list[Deliverable] | None = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.output = output
        if artifacts:
            self.artifacts = artifacts


class TaskResult(BaseModel):
    """任务执行结果"""

    task_id: str
    status: TaskStatus
    deliverables: list[Deliverable] = Field(default_factory=list)

    # 公司运行摘要
    company_summary: dict[str, Any] = Field(default_factory=dict)
    performance_report: dict[str, Any] = Field(default_factory=dict)
    eliminations: list[dict[str, Any]] = Field(default_factory=list)
    health_report: dict[str, Any] = Field(default_factory=dict)
    process_log: list[dict[str, Any]] = Field(default_factory=list)

    # 成本
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    total_ticks: int = 0

    # 时间
    duration_seconds: float = 0.0
