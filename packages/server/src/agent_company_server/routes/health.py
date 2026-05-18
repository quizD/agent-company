"""健康评估相关路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from agent_company_server.schemas import (
    EvolutionRequest,
    HealthDimensionResponse,
    HealthEvaluateRequest,
    HealthReportResponse,
    OptimizationSuggestionResponse,
)

router = APIRouter(prefix="/api/health", tags=["health"])


def _get_monitor(request: Request):
    """获取健康监控器实例。"""
    monitor = request.app.state.health_monitor
    if monitor is None:
        raise HTTPException(status_code=503, detail="健康监控器尚未初始化")
    return monitor


@router.post("/evaluate", response_model=HealthReportResponse)
async def evaluate_health(request: Request, body: HealthEvaluateRequest):
    """执行健康评估，返回12维度报告。"""
    monitor = _get_monitor(request)

    # 如果没有提供数据，使用默认模拟数据
    company_data = body.company_data
    if not company_data:
        company_data = _default_company_data()

    report = monitor.evaluate(company_data)

    return HealthReportResponse(
        overall_score=report.overall_score,
        grade=report.grade,
        dimensions=[
            HealthDimensionResponse(
                name=d.name,
                display_name=d.display_name,
                description=d.description,
                weight=d.weight,
                score=d.score,
                indicators=d.indicators,
            )
            for d in report.dimensions
        ],
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        recommendations=report.recommendations,
        radar_data=report.radar_data,
    )


@router.get("/dimensions", response_model=list[HealthDimensionResponse])
async def get_dimensions():
    """获取12维度定义信息。"""
    from agent_company.health.dimensions import ALL_DIMENSIONS

    return [
        HealthDimensionResponse(
            name=d.name,
            display_name=d.display_name,
            description=d.description,
            weight=d.weight,
            score=0.0,
            indicators=d.indicators,
        )
        for d in ALL_DIMENSIONS
    ]


@router.post("/evolution", response_model=list[OptimizationSuggestionResponse])
async def get_evolution_suggestions(request: Request, body: EvolutionRequest):
    """基于健康报告生成优化建议。"""
    from agent_company.health.evolution import EvolutionEngine

    monitor = _get_monitor(request)

    # 先执行评估
    company_data = body.company_data
    if not company_data:
        company_data = _default_company_data()

    report = monitor.evaluate(company_data)

    # 生成优化建议
    evolution = EvolutionEngine()
    suggestions = evolution.analyze(report)

    return [
        OptimizationSuggestionResponse(
            dimension=s.dimension,
            priority=s.priority,
            suggestion=s.suggestion,
            expected_improvement=s.expected_improvement,
        )
        for s in suggestions
    ]


def _default_company_data() -> dict:
    """提供默认模拟公司数据，用于演示。"""
    return {
        "agents": [
            {"id": "agent_1", "name": "张三", "role": "开发工程师", "reports_to": "leader_1"},
            {"id": "agent_2", "name": "李四", "role": "设计师", "reports_to": "leader_1"},
            {"id": "agent_3", "name": "王五", "role": "分析师", "reports_to": None},
            {"id": "leader_1", "name": "赵六", "role": "项目经理", "reports_to": None},
        ],
        "departments": [
            {"name": "工程部", "head": "leader_1", "members": ["agent_1"]},
            {"name": "设计部", "head": "leader_1", "members": ["agent_2"]},
        ],
        "messages": [
            {"from": "agent_1", "to": "agent_2", "channel": "general"},
            {"from": "leader_1", "to": "agent_1", "channel": "general"},
        ],
        "tasks": [
            {"id": "t1", "status": "completed", "assignee": "agent_1"},
            {"id": "t2", "status": "in_progress", "assignee": "agent_2"},
        ],
        "performance_scores": {
            "agent_1": 0.85,
            "agent_2": 0.78,
            "agent_3": 0.65,
        },
        "budget_info": {
            "total": 100.0,
            "spent": 45.0,
        },
        "governance_rules": [
            "所有决策需记录",
            "代码必须经过审查",
            "每日站会",
        ],
        "values": ["quality", "collaboration", "transparency"],
    }
