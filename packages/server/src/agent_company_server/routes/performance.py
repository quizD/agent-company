"""绩效评审相关路由。"""

from __future__ import annotations

import random

from fastapi import APIRouter, HTTPException, Request

from agent_company_server.schemas import (
    PerformanceReviewRequest,
    PerformanceScoreResponse,
    PerformanceSimulateRequest,
    ReviewResultResponse,
)

router = APIRouter(prefix="/api/performance", tags=["performance"])


def _get_engine(request: Request):
    """获取绩效引擎实例。"""
    engine = request.app.state.performance_engine
    if engine is None:
        raise HTTPException(status_code=503, detail="绩效引擎尚未初始化")
    return engine


def _score_to_response(ps) -> PerformanceScoreResponse:
    """将 PerformanceScore 转换为响应 schema。"""
    return PerformanceScoreResponse(
        agent_id=ps.agent_id,
        agent_name=ps.agent_name,
        role=ps.role,
        total_score=ps.total_score,
        grade=ps.grade,
        trend=ps.trend,
        rank=ps.rank,
        kpi_scores=ps.kpi_scores,
        feedback=ps.feedback or "",
    )


@router.post("/review", response_model=ReviewResultResponse)
async def run_review(request: Request, body: PerformanceReviewRequest):
    """执行绩效评审。"""
    engine = _get_engine(request)

    # 确定要评审的 Agent 列表
    agent_ids = body.agent_ids if body.agent_ids else list(engine.trackers.keys())

    if not agent_ids:
        raise HTTPException(
            status_code=400,
            detail="没有已注册的 Agent，请先执行招标或模拟注册"
        )

    result = engine.periodic_review(agent_ids)

    return ReviewResultResponse(
        scores=[_score_to_response(s) for s in result.scores.values()],
        rankings=[_score_to_response(s) for s in result.rankings],
        eliminations=[_score_to_response(s) for s in result.eliminations],
        warnings=[_score_to_response(s) for s in result.warnings],
        company_score=result.company_score,
    )


@router.get("/history", response_model=list[ReviewResultResponse])
async def get_review_history(request: Request):
    """获取评审历史记录。"""
    engine = _get_engine(request)

    history = []
    for result in engine.review_history:
        history.append(
            ReviewResultResponse(
                scores=[_score_to_response(s) for s in result.scores.values()],
                rankings=[_score_to_response(s) for s in result.rankings],
                eliminations=[_score_to_response(s) for s in result.eliminations],
                warnings=[_score_to_response(s) for s in result.warnings],
                company_score=result.company_score,
            )
        )
    return history


@router.post("/simulate", response_model=ReviewResultResponse)
async def simulate_performance(request: Request, body: PerformanceSimulateRequest):
    """模拟绩效数据（用于演示），注册 Agent 并生成随机绩效记录后执行评审。"""
    engine = _get_engine(request)
    pool = request.app.state.pool

    if pool is None:
        raise HTTPException(status_code=503, detail="人才池尚未初始化")

    # 从人才池取前 N 个 Agent 注册到绩效引擎
    agents = pool.query(limit=body.agent_count)
    if not agents:
        raise HTTPException(status_code=400, detail="人才池中没有 Agent")

    role_names = ["主编", "开发工程师", "分析师", "设计师", "项目经理"]

    for i, agent in enumerate(agents):
        role = role_names[i % len(role_names)]
        # 避免重复注册
        if agent.id not in engine.trackers:
            engine.register_agent(agent.id, role, agent.name)

    # 模拟若干 tick 的绩效数据
    agent_ids = [a.id for a in agents]
    for tick in range(body.tick_count):
        for agent_id in agent_ids:
            # 模拟消息响应
            engine.on_message(
                agent_id,
                response_time=random.uniform(0.5, 5.0),
                content_length=random.randint(100, 2000),
                tick=tick,
            )
            # 模拟任务完成
            engine.on_task_complete(
                agent_id,
                quality_score=random.uniform(0.5, 1.0),
                on_time=random.random() > 0.3,
                tick=tick,
            )

    # 执行评审
    result = engine.periodic_review(agent_ids)

    return ReviewResultResponse(
        scores=[_score_to_response(s) for s in result.scores.values()],
        rankings=[_score_to_response(s) for s in result.rankings],
        eliminations=[_score_to_response(s) for s in result.eliminations],
        warnings=[_score_to_response(s) for s in result.warnings],
        company_score=result.company_score,
    )
