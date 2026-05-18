"""tender 命令 — 执行招标流程。"""

from __future__ import annotations

import click
from rich.panel import Panel

from agent_company_cli.display import console, print_tender_result


@click.command("tender")
@click.argument("task_description")
@click.option("--budget", "-b", default=10.0, help="项目预算(美元)")
@click.option("--dry-run", is_flag=True, help="仅展示招标结果，不创建公司")
def tender_cmd(task_description: str, budget: float, dry_run: bool):
    """执行招标流程

    示例: agent-co tender "撰写技术博客" --budget 5 --dry-run
    """
    try:
        from agent_company.tender.analyzer import RequirementAnalyzer
        from agent_company.tender.engine import TenderEngine
        from agent_company.pool.talent_pool import TalentPool
    except ImportError as e:
        console.print(f"[red]错误: 无法导入核心包 — {e}[/red]")
        console.print("[dim]请确保 agent-company-core 已安装或 core/src 在 PYTHONPATH 中[/dim]")
        raise SystemExit(1)

    # 步骤 1: 需求分析
    console.print(Panel(
        f"[bold]{task_description}[/bold]\n预算: [green]${budget:.2f}[/green]"
        + ("  [yellow](dry-run 模式)[/yellow]" if dry_run else ""),
        title="[bold blue]招标任务[/bold blue]",
        border_style="blue",
    ))

    with console.status("[bold green]分析需求中..."):
        analyzer = RequirementAnalyzer()
        spec = analyzer.analyze(
            description=task_description,
            budget_usd=budget,
        )

    console.print("[green]✓[/green] 需求分析完成")

    # 步骤 2: 执行招标
    with console.status("[bold green]执行招标流程..."):
        pool = TalentPool()
        engine = TenderEngine(pool=pool)
        result = engine.run_tender(spec)

    console.print("[green]✓[/green] 招标流程完成")

    # 步骤 3: 展示结果
    print_tender_result(result)

    if dry_run:
        console.print("\n[yellow]── dry-run 模式：未创建公司实例 ──[/yellow]")
    elif result.company:
        console.print(f"\n[green]✓ 公司已创建，准备执行任务[/green]")
