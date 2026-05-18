"""角色模型定义。

角色描述了 Agent 在组织中的职位、职责、权限与考核指标。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Role(BaseModel):
    """组织角色。

    每个 Agent 在公司中扮演特定角色，角色定义了其职责范围、
    汇报关系、决策权限以及可访问的通信频道。
    """

    name: str = Field(..., description="角色名称，如 'CTO'、'产品经理'")
    department: str = Field(..., description="所属部门名称")
    reports_to: str | None = Field(default=None, description="上级角色名称")
    direct_reports: list[str] = Field(default_factory=list, description="直属下级角色名称列表")
    responsibilities: list[str] = Field(default_factory=list, description="职责描述列表")
    authorities: list[str] = Field(
        default_factory=list,
        description="决策权限列表，描述该角色可以做出哪些决定",
    )
    kpis: list[dict] = Field(
        default_factory=list,
        description="绩效考核指标，每项包含 name/measure/target/weight",
    )
    channels: list[str] = Field(default_factory=list, description="可访问的频道名称列表")
    system_prompt_template: str = Field(
        default="",
        description="角色专属的系统提示词模板，用于初始化 Agent 的行为",
    )
