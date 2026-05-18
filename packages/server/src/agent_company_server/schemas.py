"""API 请求/响应 Pydantic Schema 定义。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ==================== Pool ====================

class AgentSummary(BaseModel):
    """Agent 摘要信息"""
    id: str
    name: str
    category: str
    skills: dict[str, float]
    specializations: list[str]
    model_tier: str
    reliability_score: float
    collaboration_score: float
    performance_avg: float


class AgentDetail(BaseModel):
    """Agent 详情"""
    id: str
    name: str
    category: str
    skills: dict[str, float]
    specializations: list[str]
    tools_proficiency: dict[str, float]
    personality: dict[str, float]
    values: list[str]
    work_style: str
    communication_style: str
    reliability_score: float
    collaboration_score: float
    performance_avg: float
    llm_model: str
    model_tier: str
    system_prompt_base: str
    project_history: list[dict[str, Any]] = Field(default_factory=list)


class PoolStats(BaseModel):
    """人才池统计"""
    total_agents: int
    by_category: dict[str, int]
    by_model_tier: dict[str, int]
    avg_reliability: float
    avg_collaboration: float


class PoolQueryParams(BaseModel):
    """人才池查询参数"""
    category: str | None = None
    min_performance: float = 0.0
    values_match: list[str] | None = None
    sort_by: str = "performance_avg"
    limit: int = 10


# ==================== Tender ====================

class TenderAnalyzeRequest(BaseModel):
    """需求分析请求"""
    user_request: str = Field(description="用户需求描述文本")
    budget: float = Field(default=10.0, description="预算（美元）")


class RoleSpecResponse(BaseModel):
    """角色规格响应"""
    name: str
    count: int
    must_have_skills: list[str]
    nice_to_have: list[str]
    priority: str
    min_model_tier: str


class TenderSpecResponse(BaseModel):
    """招标规格响应"""
    project_type: str
    description: str
    deliverables: list[str]
    required_roles: list[RoleSpecResponse]
    quality_standards: dict[str, str]
    estimated_complexity: str
    value_priorities: list[str]
    budget_usd: float


class TenderRunRequest(BaseModel):
    """招标执行请求"""
    user_request: str = Field(description="用户需求描述文本")
    budget: float = Field(default=10.0, description="预算（美元）")


class TeamMemberResponse(BaseModel):
    """团队成员响应"""
    agent_id: str
    agent_name: str
    role_name: str
    role_priority: str
    total_score: float


class TenderResultResponse(BaseModel):
    """招标结果响应"""
    spec: TenderSpecResponse
    selected_team: list[TeamMemberResponse]
    rejected_count: int
    company_name: str
    tender_log: list[str]


class ProjectTemplate(BaseModel):
    """项目类型模板"""
    key: str
    project_type: str
    deliverables: list[str]
    role_count: int


# ==================== Performance ====================

class PerformanceReviewRequest(BaseModel):
    """绩效评审请求"""
    agent_ids: list[str] = Field(default_factory=list, description="要评审的 Agent ID 列表，为空则评审所有已注册的")


class PerformanceScoreResponse(BaseModel):
    """绩效评分响应"""
    agent_id: str
    agent_name: str
    role: str
    total_score: float
    grade: str
    trend: str
    rank: int = 0
    kpi_scores: dict[str, float] = Field(default_factory=dict)
    feedback: str = ""


class ReviewResultResponse(BaseModel):
    """评审结果响应"""
    scores: list[PerformanceScoreResponse]
    rankings: list[PerformanceScoreResponse]
    eliminations: list[PerformanceScoreResponse]
    warnings: list[PerformanceScoreResponse]
    company_score: float


class PerformanceSimulateRequest(BaseModel):
    """模拟绩效数据请求"""
    agent_count: int = Field(default=5, ge=1, le=20, description="模拟的 Agent 数量")
    tick_count: int = Field(default=10, ge=1, le=50, description="模拟的 tick 数量")


# ==================== Health ====================

class HealthEvaluateRequest(BaseModel):
    """健康评估请求"""
    company_data: dict[str, Any] = Field(
        default_factory=dict,
        description="公司数据，包含 agents/departments/messages/tasks 等"
    )


class HealthDimensionResponse(BaseModel):
    """健康维度响应"""
    name: str
    display_name: str
    description: str
    weight: float
    score: float
    indicators: list[str]


class HealthReportResponse(BaseModel):
    """健康报告响应"""
    overall_score: float
    grade: str
    dimensions: list[HealthDimensionResponse]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    radar_data: dict[str, float]


class EvolutionRequest(BaseModel):
    """优化建议请求"""
    company_data: dict[str, Any] = Field(
        default_factory=dict,
        description="公司数据"
    )


class OptimizationSuggestionResponse(BaseModel):
    """优化建议响应"""
    dimension: str
    priority: str
    suggestion: str
    expected_improvement: float


# ==================== Values ====================

class ValuePrincipleResponse(BaseModel):
    """价值观响应"""
    name: str
    origin: str
    rule: str
    violation: str
    category: str


class ValueMatchRequest(BaseModel):
    """价值观匹配请求"""
    task_type: str = Field(description="任务类型")


class ValueMatchResponse(BaseModel):
    """价值观匹配响应"""
    task_type: str
    weights: dict[str, float]
    matched_values: list[ValuePrincipleResponse]
