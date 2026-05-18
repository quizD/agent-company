"""任务编排引擎 — 管理任务的分配、调度和执行"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from agent_company.task.process import Process, Step
from agent_company.task.task import Deliverable, SubTask, Task, TaskResult, TaskStatus

if TYPE_CHECKING:
    from agent_company.org.company import Company

logger = logging.getLogger(__name__)


class TaskPipeline:
    """任务编排引擎 — 将 Process 转化为可执行的 SubTask 序列并调度执行"""

    def __init__(self, company: Company):
        self.company = company
        self.current_tick: int = 0
        self.subtasks: list[SubTask] = []
        self.log: list[dict[str, Any]] = []

    async def execute(self, task: Task, process: Process) -> TaskResult:
        """
        执行任务的主循环

        流程:
        1. 将 Process 的 Steps 转化为 SubTasks
        2. 按顺序/并行调度 SubTasks
        3. 每个 tick 推进一步
        4. 收集结果
        """
        task.start()
        self._log_event("task_started", {"task_id": task.id, "title": task.title})

        # Step 1: 将 Process Steps 转化为 SubTasks
        self._create_subtasks(task, process)

        # Step 2: 逐步执行
        total_ticks = 0
        for step_group in process.get_parallel_groups():
            group_subtasks = self._get_subtasks_for_steps(task.id, step_group)

            if len(group_subtasks) > 1:
                # 并行执行
                results = await asyncio.gather(
                    *[self._execute_subtask(st) for st in group_subtasks],
                    return_exceptions=True,
                )
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"SubTask {group_subtasks[i].id} 失败: {result}")
                        group_subtasks[i].status = TaskStatus.FAILED
            else:
                # 串行执行
                for st in group_subtasks:
                    await self._execute_subtask(st)

            total_ticks += max(st.max_ticks for st in group_subtasks)

            # 检查是否有决策点需要处理
            for st in group_subtasks:
                step = self._find_step(process, st.assigned_role, st.title)
                if step and step.decision and st.output:
                    self._log_event(
                        "decision_made",
                        {
                            "role": st.assigned_role,
                            "decision": st.output[:200],
                        },
                    )

        # Step 3: 收集交付物
        all_artifacts: list[Deliverable] = []
        for st in self.subtasks:
            if st.parent_task_id == task.id:
                all_artifacts.extend(st.artifacts)

        task.complete(deliverables=all_artifacts)

        return TaskResult(
            task_id=task.id,
            status=task.status,
            deliverables=all_artifacts,
            process_log=self.log,
            total_ticks=total_ticks,
        )

    def _create_subtasks(self, task: Task, process: Process) -> None:
        """将 Process Steps 转化为 SubTasks"""
        prev_ids: list[str] = []

        for step in process.steps:
            subtask = SubTask(
                parent_task_id=task.id,
                title=step.action,
                description=f"[{step.role}] {step.action}",
                assigned_role=step.role,
                max_ticks=step.max_ticks,
                depends_on=[] if step.parallel else prev_ids.copy(),
            )
            self.subtasks.append(subtask)

            if not step.parallel:
                prev_ids = [subtask.id]
            else:
                prev_ids.append(subtask.id)

    def _get_subtasks_for_steps(
        self, task_id: str, steps: list[Step]
    ) -> list[SubTask]:
        """获取对应步骤的 SubTasks"""
        result = []
        for step in steps:
            for st in self.subtasks:
                if st.parent_task_id == task_id and st.title == step.action:
                    result.append(st)
                    break
        return result

    async def _execute_subtask(self, subtask: SubTask) -> None:
        """执行单个子任务"""
        subtask.start()
        self._log_event(
            "subtask_started",
            {
                "subtask_id": subtask.id,
                "role": subtask.assigned_role,
                "action": subtask.title,
            },
        )

        # 找到对应角色的 Agent
        agent = self._find_agent_for_role(subtask.assigned_role)
        if not agent:
            logger.warning(f"找不到角色 {subtask.assigned_role} 对应的 Agent")
            subtask.status = TaskStatus.FAILED
            return

        subtask.assigned_agent_id = agent.id

        # 构建上下文
        context = self._build_context(subtask)

        # Agent 执行（perceive → think → act）
        try:
            actions = await agent.step(context)

            # 提取产出
            output_parts = []
            for action in actions:
                if isinstance(action, dict):
                    if "content" in action:
                        output_parts.append(action["content"])
                    if "artifact" in action:
                        subtask.artifacts.append(
                            Deliverable(
                                name=action.get("name", subtask.title),
                                content=action["artifact"],
                            )
                        )

            subtask.complete(output="\n".join(output_parts))
            self._log_event(
                "subtask_completed",
                {
                    "subtask_id": subtask.id,
                    "agent_id": agent.id,
                    "output_length": len(subtask.output or ""),
                },
            )
        except Exception as e:
            logger.error(f"SubTask {subtask.id} 执行异常: {e}")
            subtask.status = TaskStatus.FAILED
            self._log_event(
                "subtask_failed",
                {"subtask_id": subtask.id, "error": str(e)},
            )

    def _find_agent_for_role(self, role_name: str) -> Any:
        """在公司中找到对应角色的 Agent"""
        for agent in self.company.agents.values():
            if hasattr(agent, "role_name") and agent.role_name == role_name:
                return agent
        # 回退：找第一个可用的 agent
        agents = list(self.company.agents.values())
        return agents[0] if agents else None

    def _build_context(self, subtask: SubTask) -> list[dict]:
        """为 Agent 构建执行上下文"""
        context = [
            {
                "type": "task",
                "task_id": subtask.parent_task_id,
                "role": subtask.assigned_role,
                "action": subtask.title,
                "description": subtask.description,
            }
        ]

        # 添加前序任务的产出
        for st in self.subtasks:
            if st.id in subtask.depends_on and st.status == TaskStatus.COMPLETED:
                context.append(
                    {
                        "type": "dependency_output",
                        "from_role": st.assigned_role,
                        "from_action": st.title,
                        "output": st.output or "",
                    }
                )

        return context

    def _find_step(self, process: Process, role: str, action: str) -> Step | None:
        """在 Process 中找到对应的 Step"""
        for step in process.steps:
            if step.role == role and step.action == action:
                return step
        return None

    def _log_event(self, event_type: str, data: dict) -> None:
        """记录事件日志"""
        self.current_tick += 1
        self.log.append(
            {
                "tick": self.current_tick,
                "event": event_type,
                **data,
            }
        )
        logger.info(f"[Tick {self.current_tick}] {event_type}: {data}")
