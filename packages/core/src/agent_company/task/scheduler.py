"""任务调度器 — 智能分配 Agent 到 SubTask"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_company.agent.base import BaseAgent
    from agent_company.org.company import Company
    from agent_company.task.task import SubTask


class Scheduler:
    """
    任务调度器

    分配策略（按优先级）：
    1. 角色匹配 — Agent 的角色是否匹配 SubTask 要求
    2. 能力匹配 — Agent 技能与任务需求的相关性
    3. 负载均衡 — 优先分配给负载较低的 Agent（心理学维度）
    4. 信任度 — 优先分配给历史绩效好的 Agent（社会学维度）
    """

    def __init__(self, company: Company):
        self.company = company

    def assign(self, subtask: SubTask) -> BaseAgent | None:
        """
        为子任务分配最合适的 Agent

        Returns:
            最合适的 Agent，如果没有合适的返回 None
        """
        candidates = self._get_candidates(subtask.assigned_role)
        if not candidates:
            return None

        # 按综合分数排序
        scored = [(agent, self._score_agent(agent, subtask)) for agent in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_agent = scored[0][0]
        subtask.assigned_agent_id = best_agent.id
        return best_agent

    def _get_candidates(self, role_name: str) -> list[BaseAgent]:
        """获取匹配角色的候选 Agent"""
        candidates = []
        for agent in self.company.agents.values():
            if hasattr(agent, "role_name") and agent.role_name == role_name:
                candidates.append(agent)
        return candidates

    def _score_agent(self, agent: BaseAgent, subtask: SubTask) -> float:
        """
        综合评分 Agent 对任务的适合度

        评分维度:
        - 负载因子 (40%): 负载越低越好
        - 历史绩效 (30%): 绩效越高越好
        - 可靠性 (20%): 按时交付率
        - 协作性 (10%): 协作评分
        """
        score = 0.0

        # 负载因子 — 负载越低分越高
        if hasattr(agent, "workload"):
            load = agent.workload.load_factor
            score += (1.0 - load) * 0.4
        else:
            score += 0.4  # 无负载信息时给满分

        # 历史绩效
        if hasattr(agent, "profile"):
            perf = agent.profile.performance_avg / 100.0
            score += perf * 0.3

            # 可靠性
            score += agent.profile.reliability_score * 0.2

            # 协作性
            score += agent.profile.collaboration_score * 0.1

        return score
