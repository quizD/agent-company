"""Rich 格式化输出工具集。"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


def print_team_table(team: list[dict]) -> None:
    """格式化输出团队信息表格。"""
    table = Table(
        title="[bold cyan]组建团队[/bold cyan]",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("角色", style="bold yellow", min_width=12)
    table.add_column("Agent", style="green", min_width=15)
    table.add_column("核心技能", min_width=20)
    table.add_column("评分", justify="center", min_width=8)

    for member in team:
        profile = member.get("profile")
        role = member.get("role")
        score = member.get("score")

        role_name = role.name if hasattr(role, "name") else str(role)
        agent_name = profile.name if hasattr(profile, "name") else str(profile)

        skills_str = ""
        if hasattr(profile, "skills"):
            top_skills = sorted(profile.skills.items(), key=lambda x: x[1], reverse=True)[:3]
            skills_str = ", ".join(f"{k}({v:.1f})" for k, v in top_skills)

        score_val = ""
        if hasattr(score, "total"):
            score_val = f"[bold]{score.total:.2f}[/bold]"
        elif isinstance(score, (int, float)):
            score_val = f"[bold]{score:.2f}[/bold]"

        table.add_row(role_name, agent_name, skills_str, score_val)

    console.print(table)


def print_tender_result(result: Any) -> None:
    """格式化输出招标结果。"""
    spec = result.spec

    # 招标概要面板
    summary_text = Text()
    summary_text.append(f"项目类型: {spec.project_type}\n", style="bold")
    summary_text.append(f"项目描述: {spec.description}\n")
    summary_text.append(f"预算: ${spec.budget_usd:.2f}\n", style="green")
    summary_text.append(f"复杂度: {spec.estimated_complexity}\n")
    summary_text.append(f"所需角色: {len(spec.required_roles)} 个\n")

    if spec.deliverables:
        summary_text.append("交付物: " + ", ".join(spec.deliverables) + "\n")

    console.print(Panel(summary_text, title="[bold blue]招标概要[/bold blue]", border_style="blue"))

    # 招标日志
    if result.tender_log:
        log_text = "\n".join(result.tender_log[-10:])  # 最多显示最后10条
        console.print(Panel(log_text, title="[bold magenta]招标过程[/bold magenta]", border_style="magenta"))

    # 团队表格
    if result.selected_team:
        print_team_table(result.selected_team)

    # 统计
    console.print(
        f"\n[green]✓ 中标: {len(result.selected_team)} 人[/green]  "
        f"[red]✗ 未中标: {len(result.rejected)} 人[/red]"
    )


def print_health_report(report: dict) -> None:
    """格式化输出十二维健康度报告。"""
    table = Table(
        title="[bold cyan]十二维健康度报告[/bold cyan]",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("维度", style="bold", min_width=15)
    table.add_column("得分", justify="center", min_width=8)
    table.add_column("状态", justify="center", min_width=8)
    table.add_column("说明", min_width=30)

    for dimension, info in report.items():
        if isinstance(info, dict):
            score = info.get("score", 0.0)
            desc = info.get("description", "")
        else:
            score = float(info) if isinstance(info, (int, float)) else 0.0
            desc = ""

        # 根据得分着色
        if score >= 0.8:
            status = "[green]优秀[/green]"
            score_style = "green"
        elif score >= 0.6:
            status = "[yellow]良好[/yellow]"
            score_style = "yellow"
        elif score >= 0.4:
            status = "[orange3]一般[/orange3]"
            score_style = "orange3"
        else:
            status = "[red]预警[/red]"
            score_style = "red"

        table.add_row(
            dimension,
            f"[{score_style}]{score:.2f}[/{score_style}]",
            status,
            desc,
        )

    console.print(table)


def print_pool_table(agents: list, category: str | None = None) -> None:
    """格式化输出人才池表格。"""
    title = "[bold cyan]人才池[/bold cyan]"
    if category:
        title += f" [dim]({category})[/dim]"

    table = Table(title=title, box=box.ROUNDED, show_lines=True)
    table.add_column("名称", style="bold green", min_width=15)
    table.add_column("分类", min_width=10)
    table.add_column("专业领域", min_width=20)
    table.add_column("核心技能", min_width=25)
    table.add_column("工作风格", min_width=10)
    table.add_column("绩效", justify="center", min_width=8)

    for agent in agents:
        name = agent.name if hasattr(agent, "name") else str(agent)
        cat = agent.category if hasattr(agent, "category") else ""
        specs = ", ".join(agent.specializations[:3]) if hasattr(agent, "specializations") else ""

        skills_str = ""
        if hasattr(agent, "skills"):
            top_skills = sorted(agent.skills.items(), key=lambda x: x[1], reverse=True)[:3]
            skills_str = ", ".join(f"{k}" for k, _ in top_skills)

        work_style = agent.work_style if hasattr(agent, "work_style") else ""

        perf = ""
        if hasattr(agent, "performance_avg"):
            perf = f"{agent.performance_avg:.2f}"

        table.add_row(name, cat, specs, skills_str, work_style, perf)

    console.print(table)
    console.print(f"\n[dim]共 {len(agents)} 条记录[/dim]")
