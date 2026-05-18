# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-05-15

### Added

- **Tender System**: Requirement analysis, competitive bidding, 5-dimension scoring matrix (skill 30% + performance 25% + values 20% + team compatibility 15% + model efficiency 10%)
- **Performance Engine**: 3-layer KPI system (company/role/agent), S/A/B/C/D/F grading, periodic reviews
- **Elimination Engine**: Single F → immediate elimination, 2x consecutive D → elimination, automatic replacement from talent pool
- **Value System**: 29 behavioral principles from 10 top companies (Amazon, Netflix, Apple, Google, ByteDance, etc.), 7 categories, message auditing, violation detection
- **Model Economy**: S/A/B/C model tiers as salary grades, 3 budget strategies (quality_first/cost_first/balanced), capability = base_skill × (model_capability/100)
- **12-Dimension Health Monitor**: Organizational, sociological, business, psychological, ethical, ecological, information, cultural, political, temporal, economic, learning dimensions
- **CLI Tool** (`agent-co`): `run`, `pool`, `health`, `tender` commands with Rich formatted output
- **FastAPI Server**: 16 REST API endpoints covering pool, tender, performance, health, values
- **React Dashboard**: 6 pages (Dashboard, Pool, Tender, Performance, Health, Values) with dark theme, Recharts visualizations
- **Ollama Provider**: Local model support via Ollama REST API, zero cost
- **Industry Templates**: 6 YAML templates (software, publishing, consulting, education, design, finance)
- **Category field** on AgentProfile for improved talent pool queries
- **Auto-create departments** in Company.hire() instead of raising KeyError

### Fixed

- `BaseAgent.profile` property now public (was `_profile`)
- `pool.query(role_match="writer")` now matches by category field
- `StrEnum` replaced with `(str, Enum)` for Python 3.10 compatibility
- `quickstart.py` references updated (`role_name` → `role`)

## [0.1.0] - 2025-05-01

### Added

- **Core Engine**: Agent pool, base agent, organization structure (company/department/role)
- **Communication Layer**: Message bus, channels, message types
- **Task System**: Workflow, scheduler, orchestrator
- **LLM Abstraction**: Unified provider interface for Anthropic Claude and OpenAI GPT
- **Talent Pool**: 17 preset agents with Big Five personality traits, skill sets, and performance history
- **Basic Examples**: quickstart.py, full_tender_demo.py, custom_company.py
