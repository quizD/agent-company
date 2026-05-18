"""Agent Company CLI 入口模块。"""

import sys
from pathlib import Path

# 开发模式下将 core/src 加入 sys.path
_core_src = Path(__file__).resolve().parents[4] / "core" / "src"
if _core_src.exists() and str(_core_src) not in sys.path:
    sys.path.insert(0, str(_core_src))

import click

from agent_company_cli.commands.run import run_cmd
from agent_company_cli.commands.pool import pool_cmd
from agent_company_cli.commands.health import health_cmd
from agent_company_cli.commands.tender import tender_cmd


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """Agent Company — 招标制 AI Agent 公司框架"""
    pass


# 注册子命令
cli.add_command(run_cmd, "run")
cli.add_command(pool_cmd, "pool")
cli.add_command(health_cmd, "health")
cli.add_command(tender_cmd, "tender")


if __name__ == "__main__":
    cli()
