"""Agent 人才档案模型定义。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class ProjectRecord(BaseModel):
    """项目履历记录。"""

    project_id: str = Field(description="项目唯一标识")
    role: str = Field(description="在项目中担任的角色")
    score: float = Field(ge=0.0, le=1.0, description="项目表现评分（0-1）")
    result: str = Field(description="项目成果描述")
    timestamp: datetime = Field(default_factory=datetime.now, description="记录时间戳")


class AgentProfile(BaseModel):
    """Agent 人才档案，包含能力、性格、履历等完整画像。"""

    # 基本信息
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="唯一标识")
    name: str = Field(description="Agent 名称")

    # 能力维度
    skills: dict[str, float] = Field(
        default_factory=dict, description="技能及其熟练度（0-1）"
    )
    specializations: list[str] = Field(
        default_factory=list, description="专业领域标签"
    )
    tools_proficiency: dict[str, float] = Field(
        default_factory=dict, description="工具使用熟练度（0-1）"
    )

    # 性格维度（大五人格）
    personality: dict[str, float] = Field(
        default_factory=dict,
        description="大五人格特质评分：openness/conscientiousness/extraversion/agreeableness/neuroticism",
    )

    # 分类标签（用于查询匹配）
    category: str = Field(default="", description="职能分类：writer/engineer/analyst/designer/manager")

    # 价值观与工作风格
    values: list[str] = Field(default_factory=list, description="核心价值观")
    work_style: Literal["independent", "collaborative", "leadership"] = Field(
        default="collaborative", description="工作风格偏好"
    )
    communication_style: Literal["direct", "diplomatic", "data_driven"] = Field(
        default="direct", description="沟通风格"
    )

    # 项目履历
    project_history: list[ProjectRecord] = Field(
        default_factory=list, description="历史项目记录"
    )

    # 综合评价指标
    reliability_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="可靠性评分"
    )
    collaboration_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="协作能力评分"
    )

    # 模型配置
    llm_model: str = Field(default="gpt-4o", description="使用的 LLM 模型")
    model_tier: Literal["S", "A", "B", "C"] = Field(
        default="B", description="模型能力等级"
    )
    system_prompt_base: str = Field(
        default="", description="基础系统提示词"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def performance_avg(self) -> float:
        """根据项目履历自动计算平均绩效得分。"""
        if not self.project_history:
            return 0.0
        return sum(r.score for r in self.project_history) / len(self.project_history)
