"""全局配置管理"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM 配置"""

    default_model: str = "claude-sonnet-4-6"
    role_model_map: dict[str, str] = Field(default_factory=dict)
    api_keys: dict[str, str] = Field(default_factory=dict)  # provider → key


class BudgetConfig(BaseModel):
    """预算配置"""

    total_usd: float = 10.0
    strategy: str = "balanced"  # quality_first / cost_first / balanced
    allow_local_models: bool = True
    min_capability_for_lead: float = 85.0


class PerformanceConfig(BaseModel):
    """绩效配置"""

    review_interval: int = 5  # 每 N 个 tick 评审一次
    elimination_threshold: float = 60.0
    warning_threshold: float = 70.0
    bottom_elimination_ratio: float = 0.1  # 末位淘汰比例


class CompanyConfig(BaseModel):
    """公司配置"""

    name: str = "AI Company"
    mission: str = ""
    values: list[str] = Field(default_factory=list)
    governance_model: str = "hierarchical"  # hierarchical / voting / consensus
    escalation_path: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    """全局设置"""

    company: CompanyConfig = Field(default_factory=CompanyConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    # 路径配置
    templates_dir: str = "templates"
    pool_dir: str = "pool"
    output_dir: str = "output"

    @classmethod
    def from_yaml(cls, path: str | Path) -> Settings:
        """从 YAML 文件加载配置"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        """从字典创建配置"""
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        """保存配置到 YAML"""
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, default_flow_style=False)
