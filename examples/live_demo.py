"""
Agent Company — Live Demo（真实 LLM 调用演示）

完整走通 招标→LLM调用→产出→绩效 的端到端流程。

用法:
    # 模拟模式（不需要任何 API key）
    python examples/live_demo.py --mock

    # 真实模式（需要设置环境变量）
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/live_demo.py

    # 指定 OpenAI
    export OPENAI_API_KEY=sk-...
    python examples/live_demo.py --provider openai

参数:
    --mock          使用模拟 LLM 响应，无需 API key
    --provider      选择 LLM provider: anthropic / openai（默认自动检测）
    --budget        项目预算（美元），默认 5.0
    --request       自定义需求文本
"""

import argparse
import os
import random
import sys
import time
from pathlib import Path

# 添加 core 包路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from agent_company.pool.presets import create_default_pool
from agent_company.tender.analyzer import RequirementAnalyzer
from agent_company.tender.engine import TenderEngine
from agent_company.values.vault import ValueVault
from agent_company.values.matcher import ValueMatcher
from agent_company.values.system import ValueSystem
from agent_company.performance.engine import PerformanceEngine
from agent_company.economy.budget import ModelBudgetManager, BudgetStrategy, CostRecord
from agent_company.economy.model_tiers import ModelTierRegistry
from agent_company.health.monitor import HealthMonitor

# 尝试导入 rich，如果没有安装就用简单的 fallback
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich import box

    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


# ════════════════════════════════════════════════════════════
# 输出辅助函数
# ════════════════════════════════════════════════════════════

def print_header(title: str) -> None:
    if HAS_RICH:
        console.print(Panel(f"[bold cyan]{title}[/]", box=box.DOUBLE, expand=True))
    else:
        print(f"\n{'═' * 60}")
        print(f"  {title}")
        print(f"{'═' * 60}\n")


def print_step(step_num: int, title: str) -> None:
    if HAS_RICH:
        console.print(f"\n[bold green]Step {step_num}[/] │ [bold]{title}[/]")
        console.print("─" * 50)
    else:
        print(f"\n--- Step {step_num}: {title} ---")


def print_kv(key: str, value, indent: int = 2) -> None:
    prefix = " " * indent
    if HAS_RICH:
        console.print(f"{prefix}[dim]{key}:[/] {value}")
    else:
        print(f"{prefix}{key}: {value}")


def print_success(msg: str) -> None:
    if HAS_RICH:
        console.print(f"  [green]OK[/] {msg}")
    else:
        print(f"  [OK] {msg}")


def print_warn(msg: str) -> None:
    if HAS_RICH:
        console.print(f"  [yellow]WARN[/] {msg}")
    else:
        print(f"  [WARN] {msg}")


# ════════════════════════════════════════════════════════════
# LLM 调用封装
# ════════════════════════════════════════════════════════════

class MockLLM:
    """模拟 LLM，用于 --mock 模式下不需要 API key 的演示。"""

    TEMPLATES = {
        "主编": "作为主编，我将负责整体内容策略和质量把控。首先确定文章结构：引言、技术原理、应用场景、"
                "未来展望四个部分。每个部分需要有清晰的逻辑链和充足的案例支撑。",
        "作者": "收到任务。我将从以下角度展开写作：\n"
                "1. AI Agent 的核心架构模式\n"
                "2. 多智能体协作的技术挑战\n"
                "3. 实际落地案例分析\n"
                "预计产出 3000 字高质量内容。",
        "校对": "我将从以下维度进行校对：事实准确性、逻辑一致性、语言流畅度、格式规范性。"
                "发现问题会标注具体位置和修改建议。",
        "技术负责人": "技术方案评审完成。架构设计合理，建议增加异常处理和性能优化部分。"
                     "代码示例需要补充单元测试。",
        "开发工程师": "已完成核心模块开发。代码覆盖率 87%，通过所有单元测试。"
                     "提交了 PR 等待 review。",
        "default": "任务已收到，正在处理中。预计按时完成交付。",
    }

    def generate(self, role: str, task: str) -> tuple[str, int, int]:
        """返回 (响应文本, input_tokens, output_tokens)"""
        time.sleep(random.uniform(0.3, 0.8))  # 模拟延迟
        response = self.TEMPLATES.get(role, self.TEMPLATES["default"])
        # 模拟 token 数
        input_tokens = len(task) * 2
        output_tokens = len(response) * 2
        return response, input_tokens, output_tokens


class RealLLM:
    """真实 LLM 调用封装，支持 Anthropic Claude、OpenAI GPT 及兼容 API。"""

    def __init__(self, provider: str):
        self.provider = provider
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.Anthropic()
                self._model = "claude-sonnet-4-20250514"
            except ImportError:
                raise RuntimeError("请安装 anthropic: pip install anthropic")
        elif self.provider == "openai":
            try:
                import openai
                # 支持自定义 endpoint（OpenAI 兼容协议）
                base_url = os.environ.get("OPENAI_API_BASE")
                api_key = os.environ.get("OPENAI_API_KEY", "sk-placeholder")
                self._client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                ) if base_url else openai.OpenAI()
                self._model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            except ImportError:
                raise RuntimeError("请安装 openai: pip install openai")

    def generate(self, role: str, task: str) -> tuple[str, int, int]:
        """调用真实 LLM API，返回 (响应文本, input_tokens, output_tokens)"""
        system_prompt = (
            f"你是一个 AI Agent，担任「{role}」角色。"
            f"请根据任务要求生成高质量的工作产出。保持专业、简洁。"
        )

        if self.provider == "anthropic":
            response = self._client.messages.create(
                model=self._model,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": task}],
            )
            text = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
        elif self.provider == "openai":
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task},
                ],
            )
            text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
        else:
            raise ValueError(f"未知 provider: {self.provider}")

        return text, input_tokens, output_tokens


def detect_provider() -> str | None:
    """自动检测可用的 LLM provider"""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_BASE"):
        return "openai"
    return None


# ════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Agent Company Live Demo — 端到端 LLM Agent 公司演示"
    )
    parser.add_argument("--mock", action="store_true", help="使用模拟 LLM（无需 API key）")
    parser.add_argument("--provider", choices=["anthropic", "openai"], help="指定 LLM provider")
    parser.add_argument("--budget", type=float, default=5.0, help="项目预算（美元）")
    parser.add_argument(
        "--request",
        type=str,
        default="写一篇关于 AI Agent 的技术博客，涵盖多智能体协作、招标制架构和绩效管理",
        help="自定义需求文本",
    )
    parser.add_argument("--config", type=str, default=None, help="配置目录路径（包含 agents.yaml/models.yaml/values.yaml）")
    args = parser.parse_args()

    # 确定使用 mock 还是真实 LLM
    if args.mock:
        llm = MockLLM()
        mode_label = "模拟模式 (Mock)"
    else:
        provider = args.provider or detect_provider()
        if not provider:
            print("未检测到 API key。使用 --mock 标志运行模拟模式，或设置环境变量：")
            print("  export ANTHROPIC_API_KEY=sk-ant-...")
            print("  export OPENAI_API_KEY=sk-...")
            sys.exit(1)
        llm = RealLLM(provider)
        mode_label = f"真实模式 ({provider.capitalize()})"

    start_time = time.time()
    total_cost = 0.0

    # ── 标题 ──
    print_header("Agent Company — Live Demo")
    print_kv("模式", mode_label, indent=0)
    print_kv("预算", f"${args.budget}", indent=0)
    print_kv("需求", args.request[:60] + "...", indent=0)
    if HAS_RICH:
        console.print()

    # ══════════════════════════════════════════
    # Step 1: 展示人才池
    # ══════════════════════════════════════════
    print_step(1, "人才池总览")

    if args.config:
        config_dir = Path(args.config)
    else:
        config_dir = Path(__file__).parent.parent / "configs"

    # 加载人才池
    if config_dir.exists() and (config_dir / "agents.yaml").exists():
        from agent_company.pool.loader import create_pool_from_yaml
        pool = create_pool_from_yaml(config_dir / "agents.yaml")
    else:
        pool = create_default_pool()
    if HAS_RICH:
        table = Table(title=f"人才池 ({pool.size} 个 Agent)", box=box.SIMPLE)
        table.add_column("名称", style="cyan")
        table.add_column("模型等级", justify="center")
        table.add_column("分类", style="green")
        table.add_column("核心技能")
        for profile in pool.query(limit=10):
            skills = ", ".join(list(profile.skills.keys())[:3])
            table.add_row(profile.name, profile.model_tier, profile.category, skills)
        console.print(table)
    else:
        print(f"  人才池共 {pool.size} 个 Agent:")
        for profile in pool.query(limit=8):
            skills = ", ".join(list(profile.skills.keys())[:3])
            print(f"    - {profile.name} [{profile.model_tier}] {skills}")

    # ══════════════════════════════════════════
    # Step 2: 需求分析
    # ══════════════════════════════════════════
    print_step(2, "需求分析")

    analyzer = RequirementAnalyzer()
    tender_spec = analyzer.analyze(args.request, budget=args.budget)

    print_kv("项目类型", tender_spec.project_type)
    print_kv("复杂度", tender_spec.estimated_complexity)
    print_kv("交付物", ", ".join(tender_spec.deliverables))
    print_kv("所需角色", f"{len(tender_spec.required_roles)} 个")
    for role in tender_spec.required_roles:
        print_kv(
            f"  {role.name}",
            f"x{role.count} [{role.priority}] 技能={role.must_have_skills}",
            indent=4,
        )
    print_success("需求分析完成")

    # ══════════════════════════════════════════
    # Step 3: 招标过程
    # ══════════════════════════════════════════
    print_step(3, "招标过程（评分 & 排名）")

    engine = TenderEngine(pool)
    result = engine.run_tender(tender_spec)

    if HAS_RICH:
        table = Table(title="中标团队", box=box.ROUNDED)
        table.add_column("姓名", style="bold")
        table.add_column("角色")
        table.add_column("模型等级", justify="center")
        table.add_column("得分", justify="right", style="green")
        for member in result.selected_team:
            p = member["profile"]
            r = member["role"]
            s = member["score"]
            table.add_row(p.name, r.name, p.model_tier, f"{s.total_score:.1f}")
        console.print(table)
    else:
        print("  中标团队:")
        for member in result.selected_team:
            p = member["profile"]
            r = member["role"]
            s = member["score"]
            print(f"    {p.name} -> {r.name} [{p.model_tier}] 得分: {s.total_score:.1f}")

    print_kv("落选人数", len(result.rejected))
    print_success(f"团队组建完成: {result.company.name}")

    # ══════════════════════════════════════════
    # Step 4: 价值观对齐检查
    # ══════════════════════════════════════════
    print_step(4, "价值观对齐")

    vault = ValueVault()
    matcher = ValueMatcher(vault)
    matched_values = matcher.match_for_task("creative_writing")
    value_system = ValueSystem(matched_values)

    print_kv("匹配价值观", f"{len(matched_values)} 条")
    # 展示前 5 条
    for v in matched_values[:5]:
        if HAS_RICH:
            console.print(f"    [dim][{v.category}][/] {v.name} — {v.origin}")
        else:
            print(f"    [{v.category}] {v.name} — {v.origin}")

    # 生成行为 prompt 预览
    behavior_prompt = value_system.generate_behavior_prompt()
    print_kv("行为约束 Prompt 长度", f"{len(behavior_prompt)} 字符")
    print_success("价值观对齐完成")

    # ══════════════════════════════════════════
    # Step 5: 模拟任务执行（LLM 调用）
    # ══════════════════════════════════════════
    print_step(5, "任务执行（LLM 调用）")

    budget_mgr = ModelBudgetManager(total_budget=args.budget, strategy=BudgetStrategy.BALANCED)
    registry = ModelTierRegistry()

    # 为每个团队成员分配任务并调用 LLM
    task_prompt = f"基于以下需求完成你的工作：{args.request}"
    outputs: dict[str, str] = {}

    for member in result.selected_team:
        profile = member["profile"]
        role_spec = member["role"]

        if HAS_RICH:
            console.print(f"  [cyan]{profile.name}[/] ({role_spec.name}) 正在工作...", end=" ")
        else:
            print(f"  {profile.name} ({role_spec.name}) 正在工作...", end=" ")

        response, input_tokens, output_tokens = llm.generate(role_spec.name, task_prompt)
        outputs[profile.id] = response

        # 计算成本（估算）
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000.0
        total_cost += cost
        budget_mgr.record_cost(CostRecord(
            agent_id=profile.id,
            model_id=f"model-{profile.model_tier}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        ))

        if HAS_RICH:
            console.print(f"[green]完成[/] ({output_tokens} tokens, ${cost:.4f})")
        else:
            print(f"完成 ({output_tokens} tokens, ${cost:.4f})")

        # 打印产出预览
        preview = response[:80].replace("\n", " ")
        if HAS_RICH:
            console.print(f"    [dim]{preview}...[/]")
        else:
            print(f"    > {preview}...")

    print_success(f"所有任务执行完成，总计 {len(outputs)} 份产出")

    # ══════════════════════════════════════════
    # Step 6: 绩效评审
    # ══════════════════════════════════════════
    print_step(6, "绩效评审")

    perf_engine = PerformanceEngine(review_interval=5, elimination_threshold=50.0, warning_threshold=65.0)

    # 注册团队成员
    team_ids = []
    for member in result.selected_team:
        profile = member["profile"]
        role_spec = member["role"]
        perf_engine.register_agent(profile.id, role_spec.name, profile.name)
        team_ids.append(profile.id)

    # 基于 LLM 产出模拟绩效信号
    for i, member in enumerate(result.selected_team):
        profile = member["profile"]
        output = outputs.get(profile.id, "")
        # 用产出长度和多样性来模拟质量
        quality = min(1.0, len(output) / 200.0) * random.uniform(0.7, 1.0)
        response_time = random.uniform(1.0, 5.0)
        on_time = quality > 0.5

        for tick in range(5):
            perf_engine.on_message(profile.id, response_time, len(output), tick=tick)
            if tick % 2 == 0:
                perf_engine.on_task_complete(profile.id, quality, on_time, tick=tick)

    review = perf_engine.periodic_review(team_ids)

    if HAS_RICH:
        table = Table(title=f"绩效评审结果 (公司整体: {review.company_score:.1f})", box=box.SIMPLE)
        table.add_column("#", justify="center")
        table.add_column("姓名")
        table.add_column("角色")
        table.add_column("得分", justify="right")
        table.add_column("等级", justify="center")
        table.add_column("趋势")
        for ps in review.rankings:
            style = "green" if ps.grade.value in ("S", "A") else "yellow" if ps.grade.value == "B" else "red"
            table.add_row(
                str(ps.rank), ps.agent_name, ps.role,
                f"{ps.total_score:.1f}", f"[{style}]{ps.grade.value}[/]", ps.trend
            )
        console.print(table)
    else:
        print(f"  公司整体得分: {review.company_score:.1f}")
        for ps in review.rankings:
            print(f"    #{ps.rank} {ps.agent_name:12s} | {ps.total_score:5.1f} | {ps.grade.value} | {ps.trend}")

    if review.warnings:
        print_warn(f"警告名单: {[ps.agent_name for ps in review.warnings]}")
    print_success("绩效评审完成")

    # ══════════════════════════════════════════
    # Step 7: 健康度评估
    # ══════════════════════════════════════════
    print_step(7, "健康度评估")

    monitor = HealthMonitor()
    company_data = {
        "agents": [
            {"id": m["profile"].id, "name": m["profile"].name, "role": m["role"].name}
            for m in result.selected_team
        ],
        "departments": [{"name": "执行层", "size": len(result.selected_team)}],
        "messages": [{"sender": m["profile"].id, "length": len(outputs.get(m["profile"].id, ""))}
                     for m in result.selected_team],
        "tasks": [{"status": "completed", "quality": 0.8}],
        "performance_scores": {ps.agent_id: ps.total_score for ps in review.rankings},
        "budget_info": budget_mgr.get_budget_report(),
        "governance_rules": ["hierarchical"],
        "values": tender_spec.value_priorities,
    }

    health_report = monitor.evaluate(company_data)

    if HAS_RICH:
        console.print(f"  综合评分: [bold]{health_report.overall_score:.1f}[/] / 100  等级: [bold]{health_report.grade}[/]")
        if health_report.strengths:
            console.print(f"  [green]优势:[/] {', '.join(health_report.strengths)}")
        if health_report.weaknesses:
            console.print(f"  [yellow]弱项:[/] {', '.join(health_report.weaknesses)}")
        if health_report.recommendations:
            console.print("  建议:")
            for rec in health_report.recommendations[:3]:
                console.print(f"    - {rec}")
    else:
        print(f"  综合评分: {health_report.overall_score:.1f}/100  等级: {health_report.grade}")
        if health_report.strengths:
            print(f"  优势: {', '.join(health_report.strengths)}")
        if health_report.weaknesses:
            print(f"  弱项: {', '.join(health_report.weaknesses)}")

    print_success("健康度评估完成")

    # ══════════════════════════════════════════
    # 总结
    # ══════════════════════════════════════════
    elapsed = time.time() - start_time

    print_header("演示完成")

    budget_report = budget_mgr.get_budget_report()

    if HAS_RICH:
        summary = Table(title="执行摘要", box=box.ROUNDED, show_header=False)
        summary.add_column("指标", style="bold")
        summary.add_column("值", style="cyan")
        summary.add_row("运行模式", mode_label)
        summary.add_row("团队规模", f"{len(result.selected_team)} 人")
        summary.add_row("LLM 调用次数", f"{len(outputs)} 次")
        summary.add_row("总成本", f"${budget_report['spent']:.4f}")
        summary.add_row("剩余预算", f"${budget_report['remaining']:.4f}")
        summary.add_row("预算使用率", f"{budget_report['usage_ratio'] * 100:.1f}%")
        summary.add_row("公司绩效", f"{review.company_score:.1f}/100")
        summary.add_row("健康度", f"{health_report.overall_score:.1f}/100 ({health_report.grade})")
        summary.add_row("总耗时", f"{elapsed:.1f} 秒")
        console.print(summary)
    else:
        print(f"  运行模式:     {mode_label}")
        print(f"  团队规模:     {len(result.selected_team)} 人")
        print(f"  LLM 调用次数: {len(outputs)} 次")
        print(f"  总成本:       ${budget_report['spent']:.4f}")
        print(f"  剩余预算:     ${budget_report['remaining']:.4f}")
        print(f"  预算使用率:   {budget_report['usage_ratio'] * 100:.1f}%")
        print(f"  公司绩效:     {review.company_score:.1f}/100")
        print(f"  健康度:       {health_report.overall_score:.1f}/100 ({health_report.grade})")
        print(f"  总耗时:       {elapsed:.1f} 秒")


if __name__ == "__main__":
    main()
