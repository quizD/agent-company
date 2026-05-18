"""价值观相关路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from agent_company_server.schemas import (
    ValueMatchResponse,
    ValuePrincipleResponse,
)

router = APIRouter(prefix="/api/values", tags=["values"])


def _get_vault(request: Request):
    """获取价值观库实例。"""
    vault = request.app.state.value_vault
    if vault is None:
        raise HTTPException(status_code=503, detail="价值观库尚未初始化")
    return vault


@router.get("", response_model=list[ValuePrincipleResponse])
async def get_all_values(request: Request):
    """获取全部价值观列表。"""
    vault = _get_vault(request)
    principles = vault.get_all()
    return [
        ValuePrincipleResponse(
            name=p.name,
            origin=p.origin,
            rule=p.rule,
            violation=p.violation,
            category=p.category,
        )
        for p in principles
    ]


@router.get("/categories", response_model=list[str])
async def get_value_categories():
    """获取价值观分类列表。"""
    from agent_company.values.vault import VALUE_CATEGORIES
    return VALUE_CATEGORIES


@router.get("/match", response_model=ValueMatchResponse)
async def match_values_for_task(
    request: Request,
    task_type: str = Query(description="任务类型，如 software_development, creative_writing 等"),
):
    """根据任务类型匹配价值观。"""
    from agent_company.values.matcher import ValueMatcher, TASK_VALUE_PROFILES

    vault = _get_vault(request)
    matcher = ValueMatcher(vault)

    weights = matcher.get_weighted_values(task_type)
    matched = matcher.match_for_task(task_type)

    return ValueMatchResponse(
        task_type=task_type,
        weights=weights,
        matched_values=[
            ValuePrincipleResponse(
                name=p.name,
                origin=p.origin,
                rule=p.rule,
                violation=p.violation,
                category=p.category,
            )
            for p in matched
        ],
    )
