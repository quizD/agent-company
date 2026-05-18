"""需求分析模块 — 将用户需求文本转化为结构化招标书。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RoleSpec(BaseModel):
    """角色需求规格"""

    name: str = Field(description="角色名称，如 '主编'")
    count: int = Field(default=1, description="需要人数")
    must_have_skills: list[str] = Field(description="必备技能列表")
    nice_to_have: list[str] = Field(default_factory=list, description="加分技能列表")
    priority: Literal["critical", "core", "support"] = Field(
        default="core", description="角色重要性等级"
    )
    min_model_tier: str = Field(default="B", description="最低模型等级要求")


class TenderSpec(BaseModel):
    """招标需求书"""

    project_type: str = Field(description="项目类型，如 '内容出版'")
    description: str = Field(description="项目描述")
    deliverables: list[str] = Field(description="交付物清单")
    required_roles: list[RoleSpec] = Field(description="所需角色列表")
    quality_standards: dict[str, str] = Field(
        default_factory=dict, description="质量标准"
    )
    estimated_complexity: Literal["low", "medium", "high"] = Field(
        default="medium", description="预估复杂度"
    )
    value_priorities: list[str] = Field(
        default_factory=list, description="需要的价值观倾向"
    )
    budget_usd: float = Field(default=10.0, description="预算（美元）")


class RequirementAnalyzer:
    """分析用户需求，输出结构化招标书。当前为规则基础实现，后续可接入LLM。"""

    # 内置项目类型模板
    PROJECT_TEMPLATES: dict[str, dict] = {
        "software": {
            "project_type": "软件开发",
            "deliverables": ["源代码", "技术文档", "测试报告"],
            "quality_standards": {
                "代码覆盖率": "≥80%",
                "文档完整性": "API 文档齐全",
                "性能指标": "响应时间 < 200ms",
            },
            "roles": [
                RoleSpec(
                    name="技术负责人",
                    must_have_skills=["architecture", "code_review"],
                    priority="critical",
                    min_model_tier="A",
                ),
                RoleSpec(
                    name="开发工程师",
                    count=2,
                    must_have_skills=["coding", "testing"],
                    nice_to_have=["devops"],
                    priority="core",
                ),
                RoleSpec(
                    name="测试工程师",
                    must_have_skills=["testing", "quality_assurance"],
                    priority="support",
                ),
            ],
            "value_priorities": ["quality", "innovation", "collaboration"],
        },
        "publishing": {
            "project_type": "内容出版",
            "deliverables": ["文章/书稿", "编辑审核报告", "排版终稿"],
            "quality_standards": {
                "内容准确性": "事实核查通过率 100%",
                "文笔质量": "专业编辑审核通过",
                "按时交付": "不超过截止日期",
            },
            "roles": [
                RoleSpec(
                    name="主编",
                    must_have_skills=["editing", "content_strategy"],
                    priority="critical",
                    min_model_tier="A",
                ),
                RoleSpec(
                    name="作者",
                    count=2,
                    must_have_skills=["writing", "research"],
                    nice_to_have=["seo"],
                    priority="core",
                ),
                RoleSpec(
                    name="校对",
                    must_have_skills=["proofreading", "fact_checking"],
                    priority="support",
                ),
            ],
            "value_priorities": ["quality", "creativity", "accuracy"],
        },
        "consulting": {
            "project_type": "咨询项目",
            "deliverables": ["调研报告", "解决方案", "实施建议"],
            "quality_standards": {
                "分析深度": "数据驱动、有理有据",
                "方案可行性": "可落地执行",
                "客户满意度": "≥4/5 评分",
            },
            "roles": [
                RoleSpec(
                    name="项目经理",
                    must_have_skills=["project_management", "communication"],
                    priority="critical",
                    min_model_tier="A",
                ),
                RoleSpec(
                    name="分析师",
                    count=2,
                    must_have_skills=["data_analysis", "research"],
                    nice_to_have=["visualization"],
                    priority="core",
                ),
                RoleSpec(
                    name="领域专家",
                    must_have_skills=["domain_expertise", "consulting"],
                    priority="core",
                ),
            ],
            "value_priorities": ["professionalism", "insight", "collaboration"],
        },
        "design": {
            "project_type": "设计项目",
            "deliverables": ["设计稿", "设计规范", "素材资源包"],
            "quality_standards": {
                "视觉一致性": "符合品牌规范",
                "用户体验": "可用性测试通过",
                "交付规范": "切图标注齐全",
            },
            "roles": [
                RoleSpec(
                    name="设计总监",
                    must_have_skills=["design_thinking", "art_direction"],
                    priority="critical",
                    min_model_tier="A",
                ),
                RoleSpec(
                    name="UI 设计师",
                    count=2,
                    must_have_skills=["ui_design", "prototyping"],
                    nice_to_have=["animation"],
                    priority="core",
                ),
                RoleSpec(
                    name="UX 研究员",
                    must_have_skills=["user_research", "usability_testing"],
                    priority="support",
                ),
            ],
            "value_priorities": ["creativity", "user_focus", "aesthetics"],
        },
    }

    # 关键词 → 项目类型映射
    _TYPE_KEYWORDS: dict[str, list[str]] = {
        "software": [
            "开发", "编程", "代码", "软件", "系统", "API", "应用",
            "app", "web", "software", "code", "develop", "program",
        ],
        "publishing": [
            "写作", "出版", "文章", "书", "内容", "编辑", "博客",
            "write", "publish", "article", "book", "content", "blog",
        ],
        "consulting": [
            "咨询", "分析", "调研", "报告", "策略", "方案",
            "consult", "analysis", "research", "report", "strategy",
        ],
        "design": [
            "设计", "UI", "UX", "界面", "视觉", "品牌", "logo",
            "design", "interface", "visual", "brand",
        ],
    }

    def analyze(self, user_request: str, budget: float = 10.0) -> TenderSpec:
        """分析用户需求文本，返回招标书。

        使用关键词匹配判断项目类型，选择对应模板生成 RoleSpec。
        """
        project_type = self._detect_project_type(user_request)
        complexity = self._estimate_complexity(user_request)
        template = self.PROJECT_TEMPLATES[project_type]

        return TenderSpec(
            project_type=template["project_type"],
            description=user_request,
            deliverables=template["deliverables"],
            required_roles=template["roles"],
            quality_standards=template["quality_standards"],
            estimated_complexity=complexity,
            value_priorities=template["value_priorities"],
            budget_usd=budget,
        )

    def _detect_project_type(self, text: str) -> str:
        """关键词检测项目类型"""
        text_lower = text.lower()
        scores: dict[str, int] = {k: 0 for k in self._TYPE_KEYWORDS}

        for ptype, keywords in self._TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[ptype] += 1

        # 返回匹配度最高的类型，默认为 software
        best = max(scores, key=lambda k: scores[k])
        if scores[best] == 0:
            return "software"
        return best

    def _estimate_complexity(self, text: str) -> Literal["low", "medium", "high"]:
        """估算项目复杂度"""
        high_indicators = [
            "复杂", "大规模", "企业级", "高并发", "分布式",
            "complex", "large-scale", "enterprise", "distributed",
        ]
        low_indicators = [
            "简单", "小型", "快速", "原型", "MVP",
            "simple", "small", "quick", "prototype",
        ]

        text_lower = text.lower()

        high_count = sum(1 for w in high_indicators if w in text_lower)
        low_count = sum(1 for w in low_indicators if w in text_lower)

        if high_count > low_count:
            return "high"
        elif low_count > high_count:
            return "low"
        return "medium"
