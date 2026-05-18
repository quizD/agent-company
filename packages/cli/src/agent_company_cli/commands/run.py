"""run 命令 — 执行任务的完整流程。"""

from __future__ import annotations

import click
from rich.panel import Panel
from rich.text import Text

from agent_company_cli.display import console, print_team_table, print_tender_result


@click.command("run")
@click.argument("task_description")
@click.option("--budget", "-b", default=10.0, help="项目预算(美元)")
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["quality_first", "cost_first", "balanced"]),
    default="balanced",
    help="招标策略",
)
@click.option("--values", "-v", multiple=True, help="期望的价值观")
@click.option("--verbose", is_flag=True, help="详细输出")
def run_cmd(task_description: str, budget: float, strategy: str, values: tuple, verbose: bool):
    """执行任务：自动分析需求 → 招标 → 组建团队 → 执行

    示例: agent-co run "开发一个待办事项应用" --budget 20 --strategy quality_first
    """
    try:
        from agent_company.tender.analyzer import RequirementAnalyzer
        from agent_company.tender.engine import TenderEngine
        from agent_company.pool.talent_pool import TalentPool
    except ImportError as e:
        console.print(f"[red]错误: 无法导入核心包 — {e}[/red]")
        console.print("[dim]请确保 agent-company-core 已安装或 core/src 在 PYTHONPATH 中[/dim]")
        raise SystemExit(1)

    # 步骤 1: 分析需求
    console.print(Panel(
        f"[bold]{task_description}[/bold]\n\n"
        f"预算: [green]${budget:.2f}[/green]  策略: [cyan]{strategy}[/cyan]  "
        f"价值观: {', '.join(values) if values else '默认'}",
        title="[bold blue]任务信息[/bold blue]",
        border_style="blue",
    ))

    with console.status("[bold green]分析需求中..."):
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze(
            description=task_description,
            budget_usd=budget,
            value_priorities=list(values) if values else None,
        )

    console.print("[green]✓[/green] 需求分析完成")

    if verbose:
        console.print(f"  项目类型: {spec.project_type}")
        console.print(f"  需要角色: {len(spec.required_roles)} 个")
        console.print(f"  交付物: {', '.join(spec.deliverables)}")
        console.print(f"  复杂度: {spec.estimated_complexity}")

    # 步骤 2: 招标组建团队
    with console.status("[bold green]招标组建团队中..."):
        pool = TalentPool()
        # 注: 当前为空池演示，实际使用需要加载已注册的 Agent
        engine = TenderEngine(pool=pool)
        result = engine.run_tender(spec)

    console.print("[green]✓[/green] 招标流程完成")

    # 步骤 3: 展示结果
    print_tender_result(result)

    # 步骤 4: 后续执行（当前阶段仅展示流程）
    console.print("\n[dim]─── 实际任务执行将在后续版本中实现 ───[/dim]")
