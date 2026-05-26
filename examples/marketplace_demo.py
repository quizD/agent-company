"""
Agent Marketplace — 端到端 Demo

演示 Agent 市场的核心流程：浏览 → 搜索 → 安装 → 发布 → 认证。

用法:
    python examples/marketplace_demo.py
    python examples/marketplace_demo.py --root ./marketplace
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from agent_company.marketplace import (  # noqa: E402
    CardMetadata,
    MarketplaceRegistry,
    PerformanceAttestation,
)
from agent_company.pool.profile import AgentProfile  # noqa: E402
from agent_company.pool.talent_pool import TalentPool  # noqa: E402

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def header(text: str) -> None:
    if HAS_RICH:
        console.print(Panel(f"[bold cyan]{text}[/]", box=box.DOUBLE))
    else:
        print(f"\n=== {text} ===\n")


def step(n: int, title: str) -> None:
    if HAS_RICH:
        console.print(f"\n[bold green]Step {n}[/] │ [bold]{title}[/]")
    else:
        print(f"\n--- Step {n}: {title} ---")


def show_cards(cards, title: str) -> None:
    if HAS_RICH:
        table = Table(title=title, box=box.SIMPLE)
        table.add_column("Card ID", style="cyan")
        table.add_column("名称")
        table.add_column("等级", justify="center")
        table.add_column("标签")
        table.add_column("均分", justify="right", style="green")
        table.add_column("项目数", justify="right")
        for c in cards:
            table.add_row(
                c.metadata.card_id,
                c.profile.name,
                c.profile.model_tier,
                ", ".join(c.metadata.tags),
                f"{c.avg_score:.1f}",
                str(c.project_count),
            )
        console.print(table)
    else:
        print(f"  {title}")
        for c in cards:
            print(
                f"    {c.metadata.card_id} | {c.profile.name} "
                f"[{c.profile.model_tier}] avg={c.avg_score:.1f} "
                f"projects={c.project_count}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Marketplace Demo")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).parent.parent / "marketplace"),
        help="市场根目录（默认 ./marketplace）",
    )
    args = parser.parse_args()

    header("Agent Marketplace — Live Demo")

    # ── 1. 加载市场 ──
    step(1, "加载市场")
    registry = MarketplaceRegistry(args.root)
    all_cards = registry.list_agents()
    show_cards(all_cards, f"市场中共 {len(all_cards)} 张卡片")

    # ── 2. 搜索 ──
    step(2, "搜索：关键词 'python'")
    results = registry.search("python")
    show_cards(results, f"命中 {len(results)} 张")

    step(3, "搜索：标签 = ['writer']")
    results = registry.search(tags=["writer"])
    show_cards(results, f"命中 {len(results)} 张")

    step(4, "搜索：均分 ≥ 85")
    results = registry.search(min_avg_score=85.0)
    show_cards(results, f"命中 {len(results)} 张")

    # ── 5. 安装到本地人才池 ──
    step(5, "安装到本地人才池")
    pool = TalentPool()
    if all_cards:
        target_id = all_cards[0].metadata.card_id
        installed = registry.install(target_id, pool)
        print(f"  已安装 {installed.metadata.card_id} → 本地池 size={pool.size}")

    # ── 6. 发布一张新卡片（临时市场）──
    step(6, "发布一张新卡片到临时市场")
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = MarketplaceRegistry(tmp)
        new_profile = AgentProfile(
            name="DemoAgent",
            category="engineer",
            skills={"python": 0.8, "demo": 1.0},
            specializations=["示例"],
            model_tier="B",
            system_prompt_base="我是一个演示用 Agent。",
        )
        meta = CardMetadata(
            card_id="demo-user/demo-agent",
            author="demo-user",
            description="一个临时发布的演示 Agent",
            tags=["demo", "example"],
        )
        published = sandbox.publish(new_profile, meta)
        print(f"  发布成功: {published.metadata.card_id}")
        print(f"  指纹: {published.fingerprint}")

        # ── 7. 追加认证记录 ──
        step(7, "追加认证绩效记录")
        att = PerformanceAttestation(
            project_id="demo-proj-1",
            project_type="software_dev",
            role="开发",
            score=87.5,
            grade="A",
            attested_by="self",
        )
        updated = sandbox.attest("demo-user/demo-agent", att)
        print(f"  认证后 avg={updated.avg_score:.1f} project_count={updated.project_count}")

    header("Demo 完成")


if __name__ == "__main__":
    main()
