"""Agent 人才池管理模块，提供注册、查询、持久化等功能。"""

from __future__ import annotations

import json
from pathlib import Path

from .profile import AgentProfile, ProjectRecord


class TalentPool:
    """人才池：管理所有可用 Agent 的注册、检索和绩效更新。"""

    def __init__(self) -> None:
        # 内部存储：agent_id -> AgentProfile
        self._agents: dict[str, AgentProfile] = {}

    @property
    def size(self) -> int:
        """当前池中 Agent 数量。"""
        return len(self._agents)

    def register(self, profile: AgentProfile) -> None:
        """注册一个新的 Agent 到人才池中。"""
        if profile.id in self._agents:
            raise ValueError(f"Agent {profile.id} 已存在于人才池中")
        self._agents[profile.id] = profile

    def remove(self, agent_id: str) -> None:
        """从人才池中移除指定 Agent。"""
        if agent_id not in self._agents:
            raise KeyError(f"Agent {agent_id} 不存在于人才池中")
        del self._agents[agent_id]

    def get(self, agent_id: str) -> AgentProfile:
        """根据 ID 获取 Agent 档案。"""
        if agent_id not in self._agents:
            raise KeyError(f"Agent {agent_id} 不存在于人才池中")
        return self._agents[agent_id]

    def query(
        self,
        role_match: str | None = None,
        min_performance: float = 0,
        values_match: list[str] | None = None,
        exclude_ids: list[str] | None = None,
        sort_by: str = "performance_avg",
        limit: int = 10,
    ) -> list[AgentProfile]:
        """按条件查询人才池中的 Agent。

        Args:
            role_match: 按专业领域/技能名称模糊匹配
            min_performance: 最低绩效门槛
            values_match: 需匹配的价值观列表（取交集）
            exclude_ids: 排除的 Agent ID 列表
            sort_by: 排序字段，支持 performance_avg / reliability_score / collaboration_score
            limit: 返回最大数量

        Returns:
            符合条件的 Agent 档案列表（按指定字段降序排列）
        """
        exclude_ids = exclude_ids or []
        values_match = values_match or []

        candidates = list(self._agents.values())

        # 过滤：排除指定 ID
        if exclude_ids:
            candidates = [a for a in candidates if a.id not in exclude_ids]

        # 过滤：角色/技能/分类匹配
        if role_match:
            keyword = role_match.lower()
            candidates = [
                a
                for a in candidates
                if keyword in a.category.lower()
                or keyword in " ".join(a.specializations).lower()
                or keyword in " ".join(a.skills.keys()).lower()
                or keyword in a.name.lower()
            ]

        # 过滤：最低绩效
        if min_performance > 0:
            candidates = [
                a for a in candidates if a.performance_avg >= min_performance
            ]

        # 过滤：价值观匹配
        if values_match:
            required = set(v.lower() for v in values_match)
            candidates = [
                a
                for a in candidates
                if required.issubset(set(v.lower() for v in a.values))
            ]

        # 排序
        def _sort_key(agent: AgentProfile) -> float:
            return getattr(agent, sort_by, 0.0)

        candidates.sort(key=_sort_key, reverse=True)

        return candidates[:limit]

    def update_performance(self, agent_id: str, project_record: ProjectRecord) -> None:
        """为指定 Agent 添加项目记录并更新绩效数据。"""
        agent = self.get(agent_id)
        agent.project_history.append(project_record)

    def save(self, path: str) -> None:
        """将人才池数据持久化到 JSON 文件。"""
        data = {
            agent_id: profile.model_dump(mode="json")
            for agent_id, profile in self._agents.items()
        }
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: str) -> None:
        """从 JSON 文件加载人才池数据（覆盖当前数据）。"""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        self._agents = {
            agent_id: AgentProfile.model_validate(profile_data)
            for agent_id, profile_data in raw.items()
        }
