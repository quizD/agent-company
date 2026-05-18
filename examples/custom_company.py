"""
Agent Company — 自定义公司示例

演示如何手动创建 Agent、角色、部门，自定义价值观并组建公司。

运行方式: python3 examples/custom_company.py
"""

import sys
import os

# 添加 core 包路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from agent_company.pool.profile import AgentProfile
from agent_company.agent.base import BaseAgent
from agent_company.org.role import Role
from agent_company.org.company import Company
from agent_company.org.governance import GovernanceSystem, GovernanceRule, DecisionType, DecisionModel
from agent_company.comm.bus import MessageBus
from agent_company.comm.message import Visibility
from agent_company.values.vault import ValueVault, ValuePrinciple
from agent_company.values.system import ValueSystem


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    print_header("自定义公司组建示例")

    # ══════════════════════════════════════════
    # Step 1: 手动创建 Agent 档案
    # ══════════════════════════════════════════
    print_header("Step 1: 创建 Agent 档案")

    profiles = [
        AgentProfile(
            name="张三",
            category="engineer",
            model_tier="A",
            specializations=["架构设计", "系统开发"],
            skills={"python": 0.95, "architecture": 0.90, "code_review": 0.85},
            values=["quality", "innovation"],
            reliability_score=0.92,
            collaboration_score=0.85,
        ),
        AgentProfile(
            name="李四",
            category="writer",
            model_tier="B",
            specializations=["技术写作", "产品文档"],
            skills={"writing": 0.88, "research": 0.82, "editing": 0.75},
            values=["creativity", "accuracy"],
            reliability_score=0.85,
            collaboration_score=0.90,
        ),
        AgentProfile(
            name="王五",
            category="designer",
            model_tier="B",
            specializations=["UI设计", "品牌设计"],
            skills={"ui_design": 0.90, "prototyping": 0.85, "animation": 0.70},
            values=["creativity", "user_focus"],
            reliability_score=0.88,
            collaboration_score=0.87,
        ),
    ]

    print("已创建 Agent 档案:")
    for p in profiles:
        print(f"  - {p.name} | 类别: {p.category} | 模型等级: {p.model_tier}")
        print(f"    技能: {list(p.skills.keys())} | 可靠性: {p.reliability_score}")

    # ══════════════════════════════════════════
    # Step 2: 定义角色
    # ══════════════════════════════════════════
    print_header("Step 2: 定义角色")

    roles = [
        Role(
            name="技术负责人",
            department="技术部",
            responsibilities=["架构设计", "技术决策", "代码审查", "团队指导"],
            authorities=["技术方案审批", "代码合并权"],
            reports_to="ceo",
            kpis=[
                {"name": "架构合理性", "measure": "architecture_score", "target": ">=85", "weight": 40},
                {"name": "代码质量", "measure": "code_quality", "target": ">=90", "weight": 35},
            ],
        ),
        Role(
            name="技术文档工程师",
            department="内容部",
            responsibilities=["技术文档撰写", "API文档维护", "教程编写"],
            authorities=["文档发布"],
            reports_to="技术负责人",
        ),
        Role(
            name="UI设计师",
            department="设计部",
            responsibilities=["界面设计", "设计系统", "原型制作"],
            authorities=["设计规范制定"],
            reports_to="技术负责人",
        ),
    ]

    print("已定义角色:")
    for role in roles:
        print(f"  - {role.name} @ {role.department}")
        print(f"    职责: {role.responsibilities[:3]}")
        if role.authorities:
            print(f"    权限: {role.authorities}")

    # ══════════════════════════════════════════
    # Step 3: 自定义价值观
    # ══════════════════════════════════════════
    print_header("Step 3: 自定义价值观")

    custom_values = [
        ValuePrinciple(
            name="技术精益",
            origin="自定义",
            rule="每一行代码都要有明确的目的，拒绝过度设计，追求简洁优雅的解决方案",
            violation="为了展示技术能力而引入不必要的复杂性",
            category="excellence",
        ),
        ValuePrinciple(
            name="文档即产品",
            origin="自定义",
            rule="文档和代码一样重要，好的文档能让新人在一天内上手项目",
            violation="写完代码不写文档，或者文档与实际代码不同步",
            category="transparency",
        ),
        ValuePrinciple(
            name="用户视角",
            origin="自定义",
            rule="每个设计决策都要从最终用户的角度出发，而非开发者的便利",
            violation="因为技术实现困难就牺牲用户体验",
            category="ownership",
        ),
    ]

    print("自定义价值观:")
    for v in custom_values:
        print(f"  [{v.category}] {v.name}")
        print(f"    准则: {v.rule[:50]}...")
        print(f"    违反: {v.violation[:50]}...")
        print()

    # 生成行为约束
    value_system = ValueSystem(custom_values)
    prompt = value_system.generate_behavior_prompt()
    print(f"生成的行为约束 prompt 长度: {len(prompt)} 字符")

    # ══════════════════════════════════════════
    # Step 4: 组建公司
    # ══════════════════════════════════════════
    print_header("Step 4: 组建公司")

    # 创建通信总线
    bus = MessageBus()
    bus.create_channel("general", Visibility.PUBLIC, "全员频道")
    bus.create_channel("tech", Visibility.DEPARTMENT, "技术频道")

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
        escalation_path=["技术负责人", "ceo"],
    )

    # 创建公司
    company = Company(
        name="TechDoc Studio",
        mission="用技术和内容赋能开发者社区",
        values=["技术精益", "文档即产品", "用户视角"],
        message_bus=bus,
        governance=governance,
    )

    # 分配 Agent 到角色并加入公司
    for profile, role in zip(profiles, roles):
        agent = BaseAgent(profile=profile)
        agent.role = role.name
        company.hire(agent, role, role.department)

    print(f"公司名称: {company.name}")
    print(f"使命: {company.mission}")
    print(f"价值观: {company.values}")
    print(f"团队规模: {len(company.agents)} 人")
    print(f"通信频道: {list(bus.channels.keys())}")
    print(f"\n团队成员:")
    for agent_id, agent in company.agents.items():
        print(f"  - {agent.profile.name} → {agent.role} (模型: {agent.profile.model_tier}级)")

    # ══════════════════════════════════════════
    # 总结
    # ══════════════════════════════════════════
    print_header("自定义公司组建完成!")

    print("本示例展示了:")
    print("  [x] 手动创建 AgentProfile 档案")
    print("  [x] 定义角色（含职责、权限、KPI）")
    print("  [x] 自定义价值观原则")
    print("  [x] 配置治理系统和通信频道")
    print("  [x] 组建完整公司实例")
    print()
    print("你可以基于此模式:")
    print("  - 从 YAML 模板加载公司配置")
    print("  - 接入真实 LLM 让 Agent 执行任务")
    print("  - 启动绩效追踪和自动化管理")


if __name__ == "__main__":
    main()
