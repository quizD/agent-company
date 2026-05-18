"""Agent Company — 招标制 AI Agent 公司框架

Usage:
    from agent_company import Company, Agent, Role, Task

    company = Company.from_template("software-company")
    result = await company.execute(Task("开发一个 CLI 计算器工具"))
"""

from agent_company.agent.base import BaseAgent
from agent_company.comm.bus import MessageBus
from agent_company.comm.message import Message
from agent_company.economy.budget import ModelBudgetManager
from agent_company.economy.capability import AgentCapability
from agent_company.economy.model_tiers import ModelTierRegistry
from agent_company.org.company import Company
from agent_company.org.role import Role
from agent_company.performance.elimination import EliminationEngine
from agent_company.performance.engine import PerformanceEngine
from agent_company.pool.profile import AgentProfile
from agent_company.pool.talent_pool import TalentPool
from agent_company.task.task import Task
from agent_company.tender.analyzer import RequirementAnalyzer
from agent_company.tender.engine import TenderEngine
from agent_company.values.matcher import ValueMatcher
from agent_company.values.system import ValueSystem

# Phase 2: 招标 + 绩效 + 价值观 + 经济
from agent_company.values.vault import ValueVault

__version__ = "0.2.0"

__all__ = [
    # Phase 1: 核心引擎
    "BaseAgent",
    "Company",
    "Role",
    "Task",
    "AgentProfile",
    "TalentPool",
    "Message",
    "MessageBus",
    # Phase 2: 招标 + 绩效 + 价值观 + 经济
    "ValueVault",
    "ValueSystem",
    "ValueMatcher",
    "ModelTierRegistry",
    "ModelBudgetManager",
    "AgentCapability",
    "TenderEngine",
    "RequirementAnalyzer",
    "PerformanceEngine",
    "EliminationEngine",
]
