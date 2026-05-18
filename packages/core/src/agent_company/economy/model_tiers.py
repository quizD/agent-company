"""模型能力等级体系——定义模型规格、等级分类与注册表。"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ModelSpec(BaseModel):
    """单个模型的规格定义。"""

    id: str = Field(description="模型唯一标识，如 claude-opus-4-6")
    capability: float = Field(ge=0, le=100, description="模型能力分 (0-100)")
    cost_per_1k_input: float = Field(ge=0, description="每千 token 输入成本（美元）")
    cost_per_1k_output: float = Field(ge=0, description="每千 token 输出成本（美元）")
    strengths: list[str] = Field(default_factory=list, description="模型优势领域")


class ModelTier(BaseModel):
    """模型等级分类。"""

    tier: Literal["S", "A", "B", "C"] = Field(description="等级标识")
    models: list[ModelSpec] = Field(default_factory=list, description="该等级包含的模型列表")
    suitable_roles: list[str] = Field(default_factory=list, description="适合的角色列表")
    description: str = Field(default="", description="等级描述")


# ============================================================
# 内置默认模型等级数据（基于 2025 年实际定价）
# ============================================================

_DEFAULT_TIERS: list[dict] = [
    {
        "tier": "S",
        "description": "顶级模型，适合需要极致推理与创造力的核心岗位",
        "suitable_roles": ["CEO", "CTO", "首席架构师", "主编", "首席研究员"],
        "models": [
            {
                "id": "claude-opus-4-6",
                "capability": 98,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075,
                "strengths": ["复杂推理", "长程规划", "创意写作", "代码生成"],
            },
            {
                "id": "gpt-4o",
                "capability": 92,
                "cost_per_1k_input": 0.005,
                "cost_per_1k_output": 0.015,
                "strengths": ["多模态理解", "指令遵循", "知识广度"],
            },
        ],
    },
    {
        "tier": "A",
        "description": "高性能模型，适合需要较强能力但非最顶级的角色",
        "suitable_roles": ["项目经理", "高级工程师", "资深编辑", "数据分析师"],
        "models": [
            {
                "id": "claude-sonnet-4-6",
                "capability": 85,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015,
                "strengths": ["代码生成", "分析推理", "结构化输出"],
            },
            {
                "id": "gpt-4o-mini",
                "capability": 80,
                "cost_per_1k_input": 0.00015,
                "cost_per_1k_output": 0.0006,
                "strengths": ["快速响应", "性价比高", "日常任务"],
            },
        ],
    },
    {
        "tier": "B",
        "description": "中端模型，适合执行明确指令的常规岗位",
        "suitable_roles": ["初级工程师", "内容编辑", "校对", "测试员"],
        "models": [
            {
                "id": "claude-haiku-4-5",
                "capability": 70,
                "cost_per_1k_input": 0.0008,
                "cost_per_1k_output": 0.004,
                "strengths": ["快速响应", "简单任务", "批量处理"],
            },
            {
                "id": "ollama/qwen2.5-32b",
                "capability": 72,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "strengths": ["本地部署", "中文理解", "零成本"],
            },
        ],
    },
    {
        "tier": "C",
        "description": "轻量模型，适合简单重复性任务",
        "suitable_roles": ["实习生", "数据录入", "格式转换", "简单分类"],
        "models": [
            {
                "id": "ollama/qwen2.5-7b",
                "capability": 55,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "strengths": ["本地部署", "轻量快速", "零成本"],
            },
            {
                "id": "ollama/llama3.2-3b",
                "capability": 45,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "strengths": ["极致轻量", "边缘部署", "零成本"],
            },
        ],
    },
]


class ModelTierRegistry:
    """模型等级注册表，支持从 YAML 加载和内置默认值。"""

    def __init__(self, config_path: str | None = None) -> None:
        self._tiers: dict[str, ModelTier] = {}
        self._models: dict[str, ModelSpec] = {}
        self._model_to_tier: dict[str, str] = {}

        # 先加载内置默认数据
        self._load_defaults()

        # 如果提供了配置文件路径，尝试从 YAML 加载覆盖
        if config_path:
            self._load_from_yaml(config_path)

    def _load_defaults(self) -> None:
        """加载内置默认模型等级数据。"""
        for tier_data in _DEFAULT_TIERS:
            tier = ModelTier(**tier_data)
            self._tiers[tier.tier] = tier
            for model in tier.models:
                self._models[model.id] = model
                self._model_to_tier[model.id] = tier.tier

    def _load_from_yaml(self, config_path: str) -> None:
        """从 YAML 配置文件加载模型等级数据。"""
        path = Path(config_path)
        if not path.exists():
            return

        try:
            import yaml  # noqa: PLC0415

            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "tiers" not in data:
                return

            # 清空现有数据，用 YAML 数据替代
            self._tiers.clear()
            self._models.clear()
            self._model_to_tier.clear()

            for tier_data in data["tiers"]:
                tier = ModelTier(**tier_data)
                self._tiers[tier.tier] = tier
                for model in tier.models:
                    self._models[model.id] = model
                    self._model_to_tier[model.id] = tier.tier
        except Exception:  # noqa: BLE001
            # YAML 加载失败时保持默认数据
            if not self._tiers:
                self._load_defaults()

    def get_tier(self, tier: str) -> ModelTier:
        """获取指定等级的完整信息。"""
        if tier not in self._tiers:
            raise KeyError(f"未找到等级: {tier}")
        return self._tiers[tier]

    def get_model(self, model_id: str) -> ModelSpec | None:
        """根据模型 ID 获取模型规格，未找到返回 None。"""
        return self._models.get(model_id)

    def get_tier_for_model(self, model_id: str) -> str | None:
        """获取模型所属的等级。"""
        return self._model_to_tier.get(model_id)

    def get_models_by_tier(self, tier: str) -> list[ModelSpec]:
        """获取指定等级的所有模型。"""
        tier_obj = self._tiers.get(tier)
        if tier_obj is None:
            return []
        return tier_obj.models

    def get_cheapest_model(self, min_capability: float = 0) -> ModelSpec:
        """获取满足最低能力要求的最便宜模型。"""
        candidates = [
            m for m in self._models.values() if m.capability >= min_capability
        ]
        if not candidates:
            raise ValueError(f"没有能力分 >= {min_capability} 的模型")

        return min(
            candidates,
            key=lambda m: m.cost_per_1k_input + m.cost_per_1k_output,
        )

    @property
    def all_models(self) -> list[ModelSpec]:
        """获取所有已注册模型。"""
        return list(self._models.values())

    @property
    def all_tiers(self) -> list[ModelTier]:
        """获取所有等级。"""
        return list(self._tiers.values())
