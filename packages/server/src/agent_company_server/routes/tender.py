"""招标相关路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from agent_company_server.schemas import (
    ProjectTemplate,
    TeamMemberResponse,
    TenderAnalyzeRequest,
    TenderResultResponse,
    TenderRunRequest,
    TenderSpecResponse,
    RoleSpecResponse,
)

router = APIRouter(prefix="/api/tender", tags=["tender"])


@router.post("/analyze", response_model=TenderSpecResponse)
async def analyze_requirement(request: Request, body: TenderAnalyzeRequest):
    """分析用户需求，返回结构化招标规格。"""
    from agent_company.tender.analyzer import RequirementAnalyzer

    analyzer = RequirementAnalyzer()
    spec = analyzer.analyze(body.user_request, budget=body.budget)

    return TenderSpecResponse(
        project_type=spec.project_type,
        description=spec.description,
        deliverables=spec.deliverables,
        required_roles=[
            RoleSpecResponse(
                name=r.name,
                count=r.count,
                must_have_skills=r.must_have_skills,
                nice_to_have=r.nice_to_have,
                priority=r.priority,
                min_model_tier=r.min_model_tier,
            )
            for r in spec.required_roles
        ],
        quality_standards=spec.quality_standards,
        estimated_complexity=spec.estimated_complexity,
        value_priorities=spec.value_priorities,
        budget_usd=spec.budget_usd,
    )


@router.post("/run", response_model=TenderResultResponse)
async def run_tender(request: Request, body: TenderRunRequest):
    """执行完整招标流程，返回团队组建结果。"""
    from agent_company.tender.analyzer import RequirementAnalyzer
    from agent_company.tender.engine import TenderEngine

    pool = request.app.state.pool
    if pool is None:
        raise HTTPException(status_code=503, detail="人才池尚未初始化")

    # 1. 分析需求
    analyzer = RequirementAnalyzer()
    spec = analyzer.analyze(body.user_request, budget=body.budget)

    # 2. 执行招标
    engine = TenderEngine(pool)
    result = engine.run_tender(spec)

    # 3. 保存当前公司到 app 状态
    request.app.state.current_company = result.company

    # 4. 构建响应
    team_members = []
    for member in result.selected_team:
        team_members.append(
            TeamMemberResponse(
                agent_id=member["profile"].id,
                agent_name=member["profile"].name,
                role_name=member["role"].name,
                role_priority=member["role"].priority,
                total_score=round(member["score"].total_score, 2),
            )
        )

    return TenderResultResponse(
        spec=TenderSpecResponse(
            project_type=spec.project_type,
            description=spec.description,
            deliverables=spec.deliverables,
            required_roles=[
                RoleSpecResponse(
                    name=r.name,
                    count=r.count,
                    must_have_skills=r.must_have_skills,
                    nice_to_have=r.nice_to_have,
                    priority=r.priority,
                    min_model_tier=r.min_model_tier,
                )
                for r in spec.required_roles
            ],
            quality_standards=spec.quality_standards,
            estimated_complexity=spec.estimated_complexity,
            value_priorities=spec.value_priorities,
            budget_usd=spec.budget_usd,
        ),
        selected_team=team_members,
        rejected_count=len(result.rejected),
        company_name=result.company.name if result.company else "",
        tender_log=result.tender_log,
    )


@router.get("/templates", response_model=list[ProjectTemplate])
async def get_templates():
    """获取项目类型模板列表。"""
    from agent_company.tender.analyzer import RequirementAnalyzer

    templates = []
    for key, tpl in RequirementAnalyzer.PROJECT_TEMPLATES.items():
        templates.append(
            ProjectTemplate(
                key=key,
                project_type=tpl["project_type"],
                deliverables=tpl["deliverables"],
                role_count=len(tpl["roles"]),
            )
        )
    return templates
