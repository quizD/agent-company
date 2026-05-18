"""工作流程定义 — Process 定义了一组有序的 Step"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepType(str, Enum):
    """步骤类型"""

    ACTION = "action"  # 执行动作
    DECISION = "decision"  # 需要决策
    REVIEW = "review"  # 审核
    PARALLEL = "parallel"  # 并行执行


class Step(BaseModel):
    """工作流程中的单个步骤"""

    role: str  # 负责的角色名称
    action: str  # 需要执行的动作描述
    step_type: StepType = StepType.ACTION
    decision: bool = False  # 是否是决策点
    parallel: bool = False  # 是否可并行
    condition: str | None = None  # 条件执行 (如 "rejected" 时才执行)
    max_ticks: int = 5  # 此步骤最大轮数
    expected_output: str | None = None  # 期望产出描述
    metadata: dict[str, Any] = Field(default_factory=dict)


class Process(BaseModel):
    """工作流程 — 定义任务的执行步骤"""

    name: str
    description: str = ""
    trigger: str = ""  # 触发条件描述
    steps: list[Step] = Field(default_factory=list)

    # 流程配置
    max_iterations: int = 3  # 流程最大迭代次数（如返工循环）
    require_final_review: bool = True  # 是否需要最终审核

    def get_roles_needed(self) -> set[str]:
        """获取此流程需要的所有角色"""
        return {step.role for step in self.steps}

    def get_parallel_groups(self) -> list[list[Step]]:
        """获取可并行执行的步骤组"""
        groups: list[list[Step]] = []
        current_group: list[Step] = []

        for step in self.steps:
            if step.parallel:
                current_group.append(step)
            else:
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([step])

        if current_group:
            groups.append(current_group)

        return groups


class ProcessTemplate(BaseModel):
    """流程模板 — 可复用的流程定义"""

    name: str
    industry: str  # 适用行业
    description: str = ""
    processes: list[Process] = Field(default_factory=list)

    @classmethod
    def software_development(cls) -> ProcessTemplate:
        """软件开发流程模板"""
        return cls(
            name="software-development",
            industry="software",
            description="标准软件开发流程",
            processes=[
                Process(
                    name="feature-development",
                    trigger="新需求输入",
                    steps=[
                        Step(role="product-manager", action="分析需求，输出 PRD"),
                        Step(
                            role="tech-lead",
                            action="技术方案评审",
                            step_type=StepType.DECISION,
                            decision=True,
                        ),
                        Step(
                            role="software-engineer",
                            action="编码实现",
                            parallel=True,
                            max_ticks=10,
                        ),
                        Step(role="qa-engineer", action="测试验证"),
                        Step(
                            role="tech-lead",
                            action="代码审查",
                            step_type=StepType.REVIEW,
                            decision=True,
                        ),
                        Step(role="devops", action="部署上线"),
                    ],
                ),
                Process(
                    name="bug-fix",
                    trigger="Bug 报告",
                    steps=[
                        Step(role="qa-engineer", action="复现并定级"),
                        Step(role="tech-lead", action="分配负责人", decision=True),
                        Step(role="software-engineer", action="修复", max_ticks=5),
                        Step(role="qa-engineer", action="验证修复"),
                    ],
                ),
            ],
        )

    @classmethod
    def content_publishing(cls) -> ProcessTemplate:
        """内容出版流程模板"""
        return cls(
            name="content-publishing",
            industry="publishing",
            description="图书/内容出版流程",
            processes=[
                Process(
                    name="book-writing",
                    trigger="出书需求",
                    steps=[
                        Step(role="chief-editor", action="制定大纲和章节规划"),
                        Step(
                            role="chief-editor",
                            action="大纲评审",
                            step_type=StepType.DECISION,
                            decision=True,
                        ),
                        Step(
                            role="writer",
                            action="撰写章节内容",
                            parallel=True,
                            max_ticks=15,
                        ),
                        Step(role="editor", action="统稿润色，统一风格", max_ticks=8),
                        Step(
                            role="chief-editor",
                            action="内容终审",
                            step_type=StepType.REVIEW,
                            decision=True,
                        ),
                        Step(role="designer", action="封面设计和排版"),
                        Step(role="proofreader", action="全书校对"),
                        Step(
                            role="chief-editor",
                            action="终版审批",
                            step_type=StepType.DECISION,
                            decision=True,
                        ),
                    ],
                ),
            ],
        )

    @classmethod
    def consulting_engagement(cls) -> ProcessTemplate:
        """咨询项目流程模板"""
        return cls(
            name="consulting-engagement",
            industry="consulting",
            description="咨询项目流程",
            processes=[
                Process(
                    name="consulting-project",
                    trigger="咨询需求",
                    steps=[
                        Step(role="partner", action="理解客户需求，拆解子课题"),
                        Step(
                            role="analyst",
                            action="执行调研和数据分析",
                            parallel=True,
                            max_ticks=10,
                        ),
                        Step(role="consultant", action="整合分析结果，撰写方案"),
                        Step(
                            role="partner",
                            action="审核方案质量",
                            step_type=StepType.REVIEW,
                            decision=True,
                        ),
                        Step(role="consultant", action="交付最终报告"),
                    ],
                ),
            ],
        )
