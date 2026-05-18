"""Agent 基类模块。

定义 BaseAgent — 所有 Agent 的执行引擎基类，
实现感知-思考-行动 (Perceive-Think-Act) 循环。
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from agent_company.agent.memory import AgentMemory, Episode
from agent_company.agent.state import AgentState, AgentWorkload

if TYPE_CHECKING:
    from agent_company.comm.message import Message
    from agent_company.llm import LLMProvider
    from agent_company.pool.profile import AgentProfile


class BaseAgent:
    """Agent 执行引擎基类。

    实现完整的 感知→思考→行动 认知循环。
    每个 Agent 拥有独立的记忆系统、工作负载追踪和消息收件箱。
    """

    def __init__(
        self,
        profile: AgentProfile,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        """初始化 Agent。

        Args:
            profile: Agent 的个人档案（技能、性格、价值观等）
            llm_provider: LLM 调用提供者，为 None 时使用占位逻辑
        """
        self._id: str = str(uuid.uuid4())
        self._profile = profile
        self._role: str = ""
        self._state: AgentState = AgentState.IDLE
        self._llm_provider = llm_provider

        # 记忆系统
        self.memory = AgentMemory()

        # 工作负载追踪
        self.workload = AgentWorkload()

        # 消息收件箱
        self.inbox: list[Any] = []  # list[Message]，避免循环导入问题

    # ─── 属性 ─────────────────────────────────────────────

    @property
    def id(self) -> str:
        """Agent 唯一标识。"""
        return self._id

    @property
    def profile(self) -> AgentProfile:
        """Agent 档案（只读）。"""
        return self._profile

    @property
    def name(self) -> str:
        """Agent 名称，从 profile 中获取。"""
        return self._profile.name if self._profile else "unnamed"

    @property
    def role(self) -> str:
        """Agent 在组织中的角色。"""
        return self._role

    @role.setter
    def role(self, value: str) -> None:
        self._role = value

    @property
    def state(self) -> AgentState:
        """Agent 当前运行状态。"""
        return self._state

    @state.setter
    def state(self, value: AgentState) -> None:
        self._state = value

    # ─── 核心认知循环 ─────────────────────────────────────

    async def perceive(self, stimuli: list[dict]) -> dict:
        """感知阶段 — 处理外部输入，通过 Agent 视角进行过滤和解读。

        Args:
            stimuli: 外部刺激列表，每项包含 type、content 等字段

        Returns:
            感知结果字典，包含 observations、relevance 等
        """
        self._state = AgentState.THINKING

        # 将刺激加入工作记忆
        for stimulus in stimuli:
            self.memory.add_to_working_memory(stimulus)

        # 构建感知提示
        context = {
            "phase": "perceive",
            "stimuli": stimuli,
            "memory_summary": self.memory.get_context_summary(),
        }

        messages = self._build_messages(context)

        # 调用 LLM 进行感知解读
        if self._llm_provider is not None:
            response = await self._llm_provider.chat(messages)
            perception = {
                "observations": response.get("content", ""),
                "relevance": response.get("relevance", 0.5),
                "raw_stimuli_count": len(stimuli),
            }
        else:
            # 占位逻辑：无 LLM 时直接汇总刺激
            perception = {
                "observations": [s.get("content", "") for s in stimuli],
                "relevance": 0.5,
                "raw_stimuli_count": len(stimuli),
            }

        # 记录感知事件
        self.memory.remember(
            Episode(
                event_type="perception",
                content=f"感知到 {len(stimuli)} 个刺激",
                importance=0.3,
            )
        )

        return perception

    async def think(self, perception: dict) -> dict:
        """思考阶段 — 基于感知结果进行推理，形成意图。

        Args:
            perception: 感知阶段的输出

        Returns:
            思考结果字典，包含 intent、reasoning、confidence 等
        """
        self._state = AgentState.THINKING

        context = {
            "phase": "think",
            "perception": perception,
            "memory_summary": self.memory.get_context_summary(),
            "current_workload": {
                "load_factor": self.workload.load_factor,
                "is_overloaded": self.workload.is_overloaded,
            },
        }

        messages = self._build_messages(context)

        # 调用 LLM 进行推理
        if self._llm_provider is not None:
            response = await self._llm_provider.chat(messages)
            thought = {
                "intent": response.get("intent", "observe"),
                "reasoning": response.get("reasoning", ""),
                "confidence": response.get("confidence", 0.5),
                "planned_actions": response.get("planned_actions", []),
            }
        else:
            # 占位逻辑：无 LLM 时返回默认思考结果
            thought = {
                "intent": "observe",
                "reasoning": "无 LLM 提供者，使用默认推理",
                "confidence": 0.5,
                "planned_actions": [],
            }

        # 记录思考事件
        self.memory.remember(
            Episode(
                event_type="thinking",
                content=f"意图: {thought['intent']}, 置信度: {thought['confidence']}",
                importance=0.4,
            )
        )

        return thought

    async def act(self, thought: dict) -> list[dict]:
        """行动阶段 — 基于思考结果决定并执行动作。

        Args:
            thought: 思考阶段的输出

        Returns:
            动作列表，每项包含 action_type、params、result 等
        """
        self._state = AgentState.EXECUTING

        planned_actions: list[dict] = thought.get("planned_actions", [])

        # 如果没有计划的动作，默认为"无操作"
        if not planned_actions:
            self._state = AgentState.IDLE
            return [{"action_type": "noop", "params": {}, "result": "无需行动"}]

        executed_actions: list[dict] = []
        for action in planned_actions:
            # 实际执行逻辑由子类或工具系统实现
            result = {
                "action_type": action.get("type", "unknown"),
                "params": action.get("params", {}),
                "result": "pending_implementation",
            }
            executed_actions.append(result)

        # 记录行动事件
        self.memory.remember(
            Episode(
                event_type="action",
                content=f"执行了 {len(executed_actions)} 个动作",
                importance=0.5,
            )
        )

        self._state = AgentState.IDLE
        return executed_actions

    async def step(self, stimuli: list[dict]) -> list[dict]:
        """完整认知循环: 感知 → 思考 → 行动。

        Args:
            stimuli: 外部刺激列表

        Returns:
            执行的动作列表
        """
        perception = await self.perceive(stimuli)
        thought = await self.think(perception)
        actions = await self.act(thought)
        return actions

    # ─── 通信接口 ─────────────────────────────────────────

    def receive_message(self, message: Message) -> None:
        """接收消息，放入收件箱。

        Args:
            message: 来自其他 Agent 或系统的消息
        """
        self.inbox.append(message)
        # 同时记入工作记忆
        self.memory.add_to_working_memory(
            {"type": "message", "from": getattr(message, "sender_id", "unknown")}
        )

    # ─── 提示词构建 ─────────────────────────────────────────

    def get_system_prompt(self) -> str:
        """构建系统提示词。

        综合 profile、role、价值观、记忆等信息生成完整的 system prompt。
        """
        parts: list[str] = []

        # 基本身份
        parts.append(f"你是 {self.name}，一个 AI Agent。")
        if self._role:
            parts.append(f"你的角色是: {self._role}")

        # Profile 信息
        if self._profile:
            if hasattr(self._profile, "description") and self._profile.description:
                parts.append(f"背景描述: {self._profile.description}")
            if hasattr(self._profile, "skills") and self._profile.skills:
                parts.append(f"技能: {', '.join(self._profile.skills)}")
            if hasattr(self._profile, "values") and self._profile.values:
                parts.append(f"价值观: {', '.join(self._profile.values)}")
            if hasattr(self._profile, "personality") and self._profile.personality:
                parts.append(f"性格特征: {self._profile.personality}")

        # 记忆摘要
        memory_summary = self.memory.get_context_summary()
        if memory_summary:
            parts.append(f"\n{memory_summary}")

        return "\n".join(parts)

    def _build_messages(self, context: dict) -> list[dict]:
        """将上下文格式化为 LLM API 调用所需的消息列表。

        Args:
            context: 包含当前阶段信息的上下文字典

        Returns:
            符合 OpenAI/Anthropic 消息格式的列表
        """
        system_prompt = self.get_system_prompt()

        # 构建用户消息内容
        phase = context.get("phase", "unknown")
        if phase == "perceive":
            user_content = (
                f"请分析以下外部输入，从你的角色视角进行解读:\n\n"
                f"输入内容: {context.get('stimuli', [])}\n\n"
                f"请返回你的观察和判断。"
            )
        elif phase == "think":
            user_content = (
                f"基于以下感知结果，进行推理和规划:\n\n"
                f"感知: {context.get('perception', {})}\n"
                f"工作负载: {context.get('current_workload', {})}\n\n"
                f"请决定下一步行动意图。"
            )
        else:
            user_content = f"上下文: {context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        return messages
