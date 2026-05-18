"""
Agent Company — Quickstart 示例

演示框架的核心功能：
1. 创建人才池
2. 组建公司
3. 定义工作流程
4. 执行任务
"""

import asyncio
import sys
import os

# 添加 core 包路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from agent_company.pool.presets import create_default_pool
from agent_company.pool.talent_pool import TalentPool
from agent_company.agent.base import BaseAgent
from agent_company.agent.memory import AgentMemory
from agent_company.agent.state import AgentWorkload
from agent_company.org.role import Role
from agent_company.org.department import Department
from agent_company.org.company import Company
from agent_company.org.governance import GovernanceSystem, GovernanceRule, DecisionType, DecisionModel
from agent_company.comm.bus import MessageBus
from agent_company.comm.message import Message, MessageType, Visibility, Priority
from agent_company.task.task import Task
from agent_company.task.process import Process, Step, ProcessTemplate


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def main():
    # ══════════════════════════════════════════
    # Step 1: 创建人才池
    # ══════════════════════════════════════════
    print_header("Step 1: 创建人才池")

    pool = create_default_pool()
    print(f"人才池已创建，共 {pool.size} 个 Agent\n")

    # 按类别展示
    writers = pool.query(role_match="writer", limit=5)
    engineers = pool.query(role_match="engineer", limit=5)
    print("写作类 Agent:")
    for a in writers:
        print(f"  - {a.name} | 模型等级: {a.model_tier} | 技能: {list(a.skills.keys())[:3]}")

    print("\n工程类 Agent:")
    for a in engineers:
        print(f"  - {a.name} | 模型等级: {a.model_tier} | 技能: {list(a.skills.keys())[:3]}")

    # ══════════════════════════════════════════
    # Step 2: 定义角色和部门
    # ══════════════════════════════════════════
    print_header("Step 2: 定义角色和部门")

    pm_role = Role(
        name="product-manager",
        department="产品部",
        responsibilities=["需求分析", "PRD 撰写", "优先级排序"],
        authorities=["定义需求", "调整优先级"],
        kpis=[
            {"name": "需求清晰度", "measure": "prd_quality_score", "target": ">=85", "weight": 40},
            {"name": "沟通效率", "measure": "response_time", "target": "<=2轮", "weight": 30},
        ],
    )

    tech_lead_role = Role(
        name="tech-lead",
        department="工程部",
        responsibilities=["架构设计", "技术决策", "代码审查"],
        authorities=["技术方案审批", "代码合并"],
        reports_to="cto",
    )

    engineer_role = Role(
        name="software-engineer",
        department="工程部",
        responsibilities=["编码实现", "单元测试", "技术文档"],
        reports_to="tech-lead",
    )

    qa_role = Role(
        name="qa-engineer",
        department="工程部",
        responsibilities=["测试计划", "自动化测试", "Bug 追踪"],
    )

    print("已定义角色:")
    for role in [pm_role, tech_lead_role, engineer_role, qa_role]:
        print(f"  - {role.name} @ {role.department} | 职责: {role.responsibilities[:2]}")

    # ══════════════════════════════════════════
    # Step 3: 组建公司
    # ══════════════════════════════════════════
    print_header("Step 3: 组建公司")

    # 创建通信总线
    bus = MessageBus()
    bus.create_channel("general", Visibility.PUBLIC, "全员频道")
    bus.create_channel("engineering", Visibility.DEPARTMENT, "工程部频道")
    bus.create_channel("management", Visibility.EXECUTIVE, "管理层频道")

    # 创建治理系统
    governance = GovernanceSystem(
        rules=[
            GovernanceRule(
                decision_type=DecisionType.OPERATIONAL,
                decision_model=DecisionModel.HIERARCHICAL,
            ),
            GovernanceRule(
                decision_type=DecisionType.TACTICAL,
                decision_model=DecisionModel.VOTING,
            ),
            GovernanceRule(
                decision_type=DecisionType.STRATEGIC,
                decision_model=DecisionModel.CONSENSUS,
            ),
        ],
        escalation_path=["tech-lead", "cto", "ceo"],
    )

    # 创建公司
    company = Company(
        name="AI Startup Co.",
        mission="用 AI 构建改变世界的产品",
        values=["追求极致", "坦诚清晰", "崇尚行动"],
        message_bus=bus,
        governance=governance,
    )

    # 从人才池选人并加入公司
    selected = pool.query(limit=4)
    for i, profile in enumerate(selected):
        roles = [pm_role, tech_lead_role, engineer_role, qa_role]
        agent = BaseAgent(profile=profile)
        agent.role = roles[i].name
        company.hire(agent, roles[i], roles[i].department)

    print(f"公司: {company.name}")
    print(f"使命: {company.mission}")
    print(f"价值观: {company.values}")
    print(f"团队规模: {len(company.agents)} 人")
    print(f"通信频道: {list(bus.channels.keys())}")
    print(f"\n团队成员:")
    for agent_id, agent in company.agents.items():
        print(f"  - {agent.profile.name} → {agent.role} (模型: {agent.profile.model_tier}级)")

    # ══════════════════════════════════════════
    # Step 4: 定义工作流程
    # ══════════════════════════════════════════
    print_header("Step 4: 定义工作流程")

    template = ProcessTemplate.software_development()
    process = template.processes[0]  # feature-development

    print(f"流程: {process.name}")
    print(f"步骤:")
    for i, step in enumerate(process.steps):
        marker = "⟹" if step.decision else "→"
        parallel = " [并行]" if step.parallel else ""
        print(f"  {i+1}. [{step.role}] {marker} {step.action}{parallel}")

    # ══════════════════════════════════════════
    # Step 5: 创建任务
    # ══════════════════════════════════════════
    print_header("Step 5: 创建任务")

    task = Task(
        title="开发一个命令行待办事项工具",
        description="使用 Python 开发一个 CLI 待办事项管理工具，支持添加、删除、列表、标记完成",
        deliverables_spec=["todo.py 源代码", "README.md 使用说明", "test_todo.py 测试"],
        quality_standards={
            "代码规范": "遵循 PEP 8",
            "测试覆盖": ">= 80%",
            "文档完整": "README 包含使用示例",
        },
        max_ticks=30,
    )

    print(f"任务: {task.title}")
    print(f"描述: {task.description}")
    print(f"交付物: {task.deliverables_spec}")
    print(f"质量标准: {task.quality_standards}")

    # ══════════════════════════════════════════
    # Step 6: 模拟通信
    # ══════════════════════════════════════════
    print_header("Step 6: 模拟 Agent 通信")

    agents = list(company.agents.values())

    # PM 发布需求
    msg1 = Message(
        sender_id=agents[0].id,
        sender_role="product-manager",
        channel="general",
        content="新任务: 开发命令行待办事项工具。核心功能：增删改查 + 状态标记。优先级：高。",
        message_type=MessageType.DIRECTIVE,
        visibility=Visibility.PUBLIC,
        priority=Priority.HIGH,
    )
    await bus.publish(msg1)
    print(f"[{msg1.sender_role}] {msg1.content[:60]}...")

    # Tech Lead 回复
    msg2 = Message(
        sender_id=agents[1].id,
        sender_role="tech-lead",
        channel="general",
        content="收到。建议使用 Click 库 + SQLite 存储。预计 2 天完成。我来做架构设计。",
        message_type=MessageType.FEEDBACK,
        visibility=Visibility.PUBLIC,
        priority=Priority.NORMAL,
        references=[msg1.id],
    )
    await bus.publish(msg2)
    print(f"[{msg2.sender_role}] {msg2.content[:60]}...")

    # Engineer 确认
    msg3 = Message(
        sender_id=agents[2].id,
        sender_role="software-engineer",
        channel="engineering",
        content="我负责核心 CRUD 逻辑和 CLI 接口。准备开始编码。",
        message_type=MessageType.REPORT,
        visibility=Visibility.DEPARTMENT,
        priority=Priority.NORMAL,
    )
    await bus.publish(msg3)
    print(f"[{msg3.sender_role}] {msg3.content[:60]}...")

    print(f"\n消息总线记录: {len(bus.history)} 条消息")
    print(f"频道 'general' 历史: {len(bus.channels['general'].history)} 条")

    # ══════════════════════════════════════════
    # 总结
    # ══════════════════════════════════════════
    print_header("Quickstart 完成!")

    print("Agent Company 框架核心功能演示完成:")
    print("  [x] 人才池: 17 个预设 Agent，支持技能/绩效查询")
    print("  [x] 角色系统: 职责、权限、KPI 定义")
    print("  [x] 公司组建: 部门、治理、价值观")
    print("  [x] 工作流程: 串行/并行步骤、决策点")
    print("  [x] 任务系统: 任务定义、交付物、质量标准")
    print("  [x] 通信系统: 消息总线、频道、消息类型")
    print()
    print("下一步 (Phase 2):")
    print("  - 招标系统: 自动从人才池竞标组建团队")
    print("  - 绩效考核: 三层 KPI + S/A/B/C/D/F 评级")
    print("  - 末位淘汰: 低绩效替换 + 预算重分配")
    print("  - 价值观库: 来自顶级企业的 30+ 条行为准则")
    print("  - 模型经济: S/A/B/C 等级模型 = Agent 薪资等级")


if __name__ == "__main__":
    asyncio.run(main())
