"""Agent 记忆系统模块。

实现三层记忆架构：情景记忆、语义记忆、程序记忆，以及工作记忆。
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Episode(BaseModel):
    """情景记忆条目 — 记录具体事件。"""

    event_type: str = Field(description="事件类型，如 'message_received', 'task_completed'")
    content: str = Field(description="事件内容描述")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要性评分 0-1")


class Procedure(BaseModel):
    """程序记忆条目 — 记录习得的工作流程。"""

    name: str = Field(description="流程名称")
    steps: list[str] = Field(default_factory=list, description="流程步骤列表")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="历史成功率")


class AgentMemory(BaseModel):
    """Agent 记忆系统。

    三层记忆结构:
    - 情景记忆 (episodic): 具体事件记录
    - 语义记忆 (semantic): 事实与知识
    - 程序记忆 (procedural): 习得的工作流
    - 工作记忆 (working_memory): 当前上下文，容量有限
    """

    # 三层长期记忆
    episodic: list[Episode] = Field(default_factory=list, description="情景记忆")
    semantic: dict[str, Any] = Field(default_factory=dict, description="语义记忆")
    procedural: list[Procedure] = Field(default_factory=list, description="程序记忆")

    # 工作记忆
    working_memory: list[Any] = Field(default_factory=list, description="工作记忆")
    max_working_items: int = Field(default=20, description="工作记忆最大容量")

    # 情景记忆容量
    max_episodes: int = Field(default=1000, description="情景记忆最大条数")

    def remember(self, event: Episode) -> None:
        """将事件添加到情景记忆。

        当超出容量时，移除最旧且最不重要的记忆。
        """
        self.episodic.append(event)

        # 超出容量时淘汰
        if len(self.episodic) > self.max_episodes:
            # 按 importance 升序排列，移除最不重要的
            self.episodic.sort(key=lambda e: e.importance)
            self.episodic = self.episodic[len(self.episodic) - self.max_episodes :]

    def recall(self, query: str, k: int = 5) -> list[Episode]:
        """根据关键词从情景记忆中检索相关事件。

        当前使用简单关键词匹配，后续可替换为向量检索。
        """
        query_lower = query.lower()
        keywords = query_lower.split()

        scored: list[tuple[float, Episode]] = []
        for episode in self.episodic:
            content_lower = episode.content.lower()
            # 计算匹配的关键词数量作为相关性分数
            match_score = sum(1 for kw in keywords if kw in content_lower)
            if match_score > 0:
                # 综合考虑匹配度和重要性
                final_score = match_score * 0.7 + episode.importance * 0.3
                scored.append((final_score, episode))

        # 按分数降序，取 top-k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:k]]

    def learn_fact(self, key: str, value: Any) -> None:
        """学习一个新事实，存入语义记忆。"""
        self.semantic[key] = value

    def get_fact(self, key: str) -> Any:
        """从语义记忆中获取事实。"""
        return self.semantic.get(key)

    def learn_procedure(self, procedure: Procedure) -> None:
        """学习一个新流程。

        如果同名流程已存在，则更新。
        """
        for i, existing in enumerate(self.procedural):
            if existing.name == procedure.name:
                self.procedural[i] = procedure
                return
        self.procedural.append(procedure)

    def forget(self, decay_factor: float = 0.1) -> None:
        """遗忘机制 — 移除低重要性的旧记忆。

        将所有情景记忆的重要性衰减 decay_factor，
        然后移除重要性降至 0 以下的记忆。
        """
        for episode in self.episodic:
            episode.importance -= decay_factor

        # 移除重要性过低的记忆
        self.episodic = [ep for ep in self.episodic if ep.importance > 0.0]

    def get_context_summary(self) -> str:
        """汇总当前工作记忆，生成可用于 LLM 提示词的摘要。"""
        if not self.working_memory:
            return "当前工作记忆为空。"

        lines: list[str] = ["[当前工作记忆]"]
        for i, item in enumerate(self.working_memory, 1):
            lines.append(f"  {i}. {item}")

        # 附加最近的重要情景
        recent_important = sorted(
            self.episodic, key=lambda e: (e.importance, e.timestamp), reverse=True
        )[:3]
        if recent_important:
            lines.append("[近期重要事件]")
            for ep in recent_important:
                lines.append(f"  - [{ep.event_type}] {ep.content}")

        return "\n".join(lines)

    def add_to_working_memory(self, item: Any) -> None:
        """向工作记忆添加条目，超出容量时移除最旧的。"""
        self.working_memory.append(item)
        if len(self.working_memory) > self.max_working_items:
            self.working_memory = self.working_memory[-self.max_working_items :]
