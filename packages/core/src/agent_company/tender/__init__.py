"""招标系统模块 — 从需求分析到团队组建的完整流程。"""

from agent_company.tender.analyzer import RequirementAnalyzer, RoleSpec, TenderSpec
from agent_company.tender.bidding import BiddingProcess, BidProposal
from agent_company.tender.engine import TenderEngine, TenderResult
from agent_company.tender.scoring import BidScore, ScoringMatrix

__all__ = [
    "RequirementAnalyzer",
    "RoleSpec",
    "TenderSpec",
    "BiddingProcess",
    "BidProposal",
    "TenderEngine",
    "TenderResult",
    "BidScore",
    "ScoringMatrix",
]
