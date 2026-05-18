"""pool 命令 — 管理人才池。"""

from __future__ import annotations

import click

from agent_company_cli.display import console, print_pool_table


@click.group("pool")
def pool_cmd():
    """管理人才池"""
    pass


@pool_cmd.command("list")
@click.option("--category", "-c", help="按分类筛选: writer/engineer/analyst/designer/manager")
@click.option("--limit", "-l", default=20, help="显示数量")
def pool_list(category: str | None, limit: int):
    """列出人才池中的 Agent"""
    try:
        from agent_company.pool.talent_pool import TalentPool
    except ImportError as e:
        console.print(f"[red]错误: 无法导入核心包 — {e}[/red]")
        raise SystemExit(1)

    pool = TalentPool()

    # 查询人才池
    agents = pool.query(
        role_match=category,
        limit=limit,
    )

    if not agents:
        console.print("[yellow]人才池为空。请先注册 Agent 或加载人才数据。[/yellow]")
        return

    print_pool_table(agents, category=category)


@pool_cmd.command("info")
@click.argument("name")
def pool_info(name: str):
    """查看 Agent 详细信息"""
    try:
        from agent_company.pool.talent_pool import TalentPool
    except ImportError as e:
        console.print(f"[red]错误: 无法导入核心包 — {e}[/red]")
        raise SystemExit(1)

    from rich.panel import Panel
    from rich.text import Text

    pool = TalentPool()

    # 尝试按名称查询
    agents = pool.query(limit=100)
    matched = [a for a in agents if a.name == name]

    if not matched:
        console.print(f"[red]未找到名为 '{name}' 的 Agent[/red]")
        raise SystemExit(1)

    agent = matched[0]

    # 构建详情面板
    info_text = Text()
    info_text.append(f"名称: {agent.name}\n", style="bold")
    info_text.append(f"ID: {agent.id}\n", style="dim")
    info_text.append(f"分类: {agent.category}\n")
    info_text.append(f"工作风格: {agent.work_style}\n")
    info_text.append(f"沟通风格: {agent.communication_style}\n")

    if agent.specializations:
        info_text.append(f"专业领域: {', '.join(agent.specializations)}\n")

    if agent.values:
        info_text.append(f"价值观: {', '.join(agent.values)}\n")

    if agent.skills:
        info_text.append("\n技能:\n", style="bold")
        for skill, level in sorted(agent.skills.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(level * 10) + "░" * (10 - int(level * 10))
            info_text.append(f"  {skill:<20} {bar} {level:.2f}\n")

    if hasattr(agent, "performance_avg"):
        info_text.append(f"\n综合绩效: {agent.performance_avg:.2f}\n", style="bold green")

    console.print(Panel(info_text, title=f"[bold cyan]{agent.name}[/bold cyan]", border_style="cyan"))


@pool_cmd.command("stats")
def pool_stats():
    """人才池统计"""
    try:
        from agent_company.pool.talent_pool import TalentPool
    except ImportError as e:
        console.print(f"[red]错误: 无法导入核心包 — {e}[/red]")
        raise SystemExit(1)

    from rich.table import Table
    from rich import box

    pool = TalentPool()
    all_agents = pool.query(limit=1000)

    if not all_agents:
        console.print("[yellow]人才池为空。[/yellow]")
        return

    # 按分类统计
    category_counts: dict[str, int] = {}
    for agent in all_agents:
        cat = agent.category if hasattr(agent, "category") and agent.category else "未分类"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    table = Table(title="[bold cyan]人才池统计[/bold cyan]", box=box.ROUNDED)
    table.add_column("分类", style="bold", min_width=15)
    table.add_column("数量", justify="center", min_width=8)
    table.add_column("占比", justify="center", min_width=10)

    total = len(all_agents)
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        table.add_row(cat, str(count), f"{pct:.1f}%")

    table.add_row("[bold]合计[/bold]", f"[bold]{total}[/bold]", "[bold]100%[/bold]")

    console.print(table)
