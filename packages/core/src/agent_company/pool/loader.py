"""Agent 人才池 YAML 加载器。

从 YAML 配置文件加载 Agent 档案，支持用户自定义 Agent 性格、技能和模型。
若配置文件不存在，自动降级到内置预设。
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml

from .profile import AgentProfile
from .talent_pool import TalentPool


def load_agents_from_yaml(path: str | Path) -> list[AgentProfile]:
    """从 YAML 文件加载 Agent 列表。

    Args:
        path: YAML 文件路径。

    Returns:
        AgentProfile 列表。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: YAML 格式不合法。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Agent 配置文件不存在: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "agents" not in data:
        raise ValueError(f"无效的 Agent 配置文件格式: {path}")

    agents: list[AgentProfile] = []
    for entry in data["agents"]:
        profile = _parse_agent_entry(entry)
        agents.append(profile)

    return agents


def _parse_agent_entry(entry: dict[str, Any]) -> AgentProfile:
    """解析单个 Agent YAML 条目为 AgentProfile。"""
    return AgentProfile(
        id=entry.get("id", str(uuid.uuid4())),
        name=entry["name"],
        category=entry.get("category", ""),
        skills=entry.get("skills", {}),
        specializations=entry.get("specializations", []),
        tools_proficiency=entry.get("tools_proficiency", {}),
        personality=entry.get("personality", {}),
        values=entry.get("values", []),
        work_style=entry.get("work_style", "independent"),
        communication_style=entry.get("communication_style", "direct"),
        reliability_score=entry.get("reliability_score", 0.8),
        collaboration_score=entry.get("collaboration_score", 0.75),
        llm_model=entry.get("llm_model", "gpt-4o-mini"),
        model_tier=entry.get("model_tier", "B"),
        system_prompt_base=entry.get("system_prompt_base", ""),
    )


def create_pool_from_yaml(path: str | Path) -> TalentPool:
    """从 YAML 创建人才池，失败则降级到内置预设。

    Args:
        path: YAML 配置文件路径。

    Returns:
        填充好的 TalentPool。
    """
    try:
        agents = load_agents_from_yaml(path)
        pool = TalentPool()
        for agent in agents:
            pool.register(agent)
        return pool
    except (FileNotFoundError, ValueError):
        from .presets import create_default_pool
        return create_default_pool()
