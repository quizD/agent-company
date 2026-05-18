"""health 命令 — 查看十二维健康度报告。"""

from __future__ import annotations

import json

import click

from agent_company_cli.display import console, print_health_report


# 十二维健康度模板（当 core 中尚未实现时使用）
DEFAULT_DIMENSIONS = {
    "文化认同": {"score": 0.0, "description": "团队对核心价值观的认同程度"},
    "技能覆盖": {"score": 0.0, "description": "技能需求覆盖率"},
    "协作效率": {"score": 0.0, "description": "跨角色协作效率"},
    "交付质量": {"score": 0.0, "description": "产出物质量得分"},
    "创新能力": {"score": 0.0, "description": "解决方案创新性"},
    "响应速度": {"score": 0.0, "description": "任务响应与完成时效"},
    "成本效率": {"score": 0.0, "description": "预算利用率"},
    "知识沉淀": {"score": 0.0, "description": "组织知识积累和复用率"},
    "人才储备": {"score": 0.0, "description": "人才池深度与梯队建设"},
    "风险控制": {"score": 0.0, "description": "风险识别与应对能力"},
    "适应能力": {"score": 0.0, "description": "面对新需求的适应速度"},
    "满意度": {"score": 0.0, "description": "任务委托方满意度"},
}


@click.command("health")
@click.option("--format", "-f", "output_format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
def health_cmd(output_format: str):
    """查看十二维健康度报告"""
    # 尝试从核心包获取健康报告
    report = None
    try:
        from agent_company.health import get_health_report  # type: ignore
        report = get_health_report()
    except (ImportError, AttributeError):
        # 核心包中 health 模块尚未完整实现，使用默认模板
        report = DEFAULT_DIMENSIONS

    if output_format == "json":
        # JSON 格式输出
        console.print_json(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        # Rich 表格格式输出
        print_health_report(report)
        console.print("\n[dim]提示: 健康度数据将在项目执行后自动更新[/dim]")
