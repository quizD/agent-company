"""人才池相关路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from agent_company_server.schemas import (
    AgentDetail,
    AgentSummary,
    PoolStats,
)

router = APIRouter(prefix="/api/pool", tags=["pool"])


def _get_pool(request: Request):
    """获取人才池实例。"""
    pool = request.app.state.pool
    if pool is None:
        raise HTTPException(status_code=503, detail="人才池尚未初始化")
    return pool


@router.get("/stats", response_model=PoolStats)
async def get_pool_stats(request: Request):
    """获取人才池统计信息。"""
    pool = _get_pool(request)
    all_agents = pool.query(limit=999)

    by_category: dict[str, int] = {}
    by_model_tier: dict[str, int] = {}
    total_reliability = 0.0
    total_collaboration = 0.0

    for agent in all_agents:
        by_category[agent.category] = by_category.get(agent.category, 0) + 1
        by_model_tier[agent.model_tier] = by_model_tier.get(agent.model_tier, 0) + 1
        total_reliability += agent.reliability_score
        total_collaboration += agent.collaboration_score

    count = len(all_agents) or 1
    return PoolStats(
        total_agents=len(all_agents),
        by_category=by_category,
        by_model_tier=by_model_tier,
        avg_reliability=round(total_reliability / count, 3),
        avg_collaboration=round(total_collaboration / count, 3),
    )


@router.get("/query", response_model=list[AgentSummary])
async def query_agents(
    request: Request,
    category: str | None = Query(default=None, description="按分类过滤"),
    min_performance: float = Query(default=0.0, description="最低绩效"),
    sort_by: str = Query(default="reliability_score", description="排序字段"),
    limit: int = Query(default=10, ge=1, le=100, description="返回数量"),
):
    """按条件查询人才池。"""
    pool = _get_pool(request)
    agents = pool.query(
        role_match=category,
        min_performance=min_performance,
        sort_by=sort_by,
        limit=limit,
    )
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            category=a.category,
            skills=a.skills,
            specializations=a.specializations,
            model_tier=a.model_tier,
            reliability_score=a.reliability_score,
            collaboration_score=a.collaboration_score,
            performance_avg=a.performance_avg,
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent_detail(request: Request, agent_id: str):
    """获取指定 Agent 详情。"""
    pool = _get_pool(request)
    try:
        agent = pool.get(agent_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} 不存在")

    return AgentDetail(
        id=agent.id,
        name=agent.name,
        category=agent.category,
        skills=agent.skills,
        specializations=agent.specializations,
        tools_proficiency=agent.tools_proficiency,
        personality=agent.personality,
        values=agent.values,
        work_style=agent.work_style,
        communication_style=agent.communication_style,
        reliability_score=agent.reliability_score,
        collaboration_score=agent.collaboration_score,
        performance_avg=agent.performance_avg,
        llm_model=agent.llm_model,
        model_tier=agent.model_tier,
        system_prompt_base=agent.system_prompt_base,
        project_history=[r.model_dump(mode="json") for r in agent.project_history],
    )


@router.get("", response_model=list[AgentSummary])
async def list_all_agents(request: Request):
    """列出所有 Agent。"""
    pool = _get_pool(request)
    agents = pool.query(limit=999)
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            category=a.category,
            skills=a.skills,
            specializations=a.specializations,
            model_tier=a.model_tier,
            reliability_score=a.reliability_score,
            collaboration_score=a.collaboration_score,
            performance_avg=a.performance_avg,
        )
        for a in agents
    ]
