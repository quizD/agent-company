"""FastAPI 应用入口。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agent Company API", version="0.2.0")

# CORS 支持（用于前端 Dashboard 对接）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用状态（单例）
app.state.pool = None
app.state.current_company = None
app.state.performance_engine = None
app.state.health_monitor = None
app.state.value_vault = None


@app.on_event("startup")
async def startup():
    """应用启动时初始化核心模块。"""
    from agent_company.pool.presets import create_default_pool
    from agent_company.health.monitor import HealthMonitor
    from agent_company.values.vault import ValueVault
    from agent_company.performance.engine import PerformanceEngine

    app.state.pool = create_default_pool()
    app.state.health_monitor = HealthMonitor()
    app.state.value_vault = ValueVault()
    app.state.performance_engine = PerformanceEngine()


# 注册路由
from agent_company_server.routes import pool, tender, performance, health, values  # noqa: E402

app.include_router(pool.router)
app.include_router(tender.router)
app.include_router(performance.router)
app.include_router(health.router)
app.include_router(values.router)
