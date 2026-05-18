"""
Agent Company — 完整招标流程示例

演示：需求分析 → 招标组建 → 价值观对齐 → 绩效模拟 → 末位淘汰

运行方式: python3 examples/full_tender_demo.py
"""

import sys
import os
import random

# 添加 core 包路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from agent_company.pool.presets import create_default_pool
from agent_company.tender.analyzer import RequirementAnalyzer
from agent_company.tender.engine import TenderEngine
from agent_company.values.vault import ValueVault
from agent_company.values.matcher import ValueMatcher
from agent_company.values.system import ValueSystem
from agent_company.performance.engine import PerformanceEngine
from agent_company.performance.elimination import EliminationEngine


def print_header(title: str) -> None:
    """打印格式化标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_separator() -> None:
    print(f"\n{'-'*60}\n")


def main():
    random.seed(42)  # 固定随机种子以便复现

    print_header("Agent Company — 完整招标流程演示")
    print("本示例将完整演示：")
    print("  1. 需求分析 → 结构化招标书")
    print("  2. 价值观匹配 → 任务适配的价值观组合")
    print("  3. 招标组建 → 从人才池筛选最佳团队")
    print("  4. 价值观注入 → 生成行为约束 prompt")
    print("  5. 绩效模拟 → 3轮绩效评审")
    print("  6. 末位淘汰 → 低绩效替换")
    print()

    # ══════════════════════════════════════════
    # Step 1: 需求分析
    # ══════════════════════════════════════════
    print_header("Step 1: 需求分析")

    user_request = "出一本关于AI创业的书，涵盖技术选型、产品设计、融资策略和团队管理，面向技术背景的创业者"

    print(f"用户需求: {user_request}")
    print()

    analyzer = RequirementAnalyzer()
    tender_spec = analyzer.analyze(user_request, budget=15.0)

    print(f"项目类型: {tender_spec.project_type}")
    print(f"复杂度: {tender_spec.estimated_complexity}")
    print(f"预算: ${tender_spec.budget_usd}")
    print(f"交付物:")
    for d in tender_spec.deliverables:
        print(f"  - {d}")
    print(f"质量标准:")
    for k, v in tender_spec.quality_standards.items():
        print(f"  - {k}: {v}")
    print(f"需要角色:")
    for role in tender_spec.required_roles:
        print(f"  - {role.name} x{role.count} [{role.priority}] (最低模型等级: {role.min_model_tier})")
        print(f"    必备技能: {role.must_have_skills}")
    print(f"价值观优先: {tender_spec.value_priorities}")

    # ══════════════════════════════════════════
    # Step 2: 价值观匹配
    # ══════════════════════════════════════════
    print_header("Step 2: 价值观匹配")

    vault = ValueVault()
    matcher = ValueMatcher(vault)

    # 出版类任务使用 creative_writing 任务类型
    task_type = "creative_writing"
    weights = matcher.get_weighted_values(task_type)
    print(f"任务类型: {task_type}")
    print(f"价值观权重分布:")
    for category, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        bar = "#" * int(weight * 40)
        print(f"  {category:18s} {weight:.2f} {bar}")

    matched_values = matcher.match_for_task(task_type)
    print(f"\n匹配的价值观 ({len(matched_values)} 条):")
    for v in matched_values:
        print(f"  [{v.category}] {v.name} — 来源: {v.origin}")

    # ══════════════════════════════════════════
    # Step 3: 招标组建
    # ══════════════════════════════════════════
    print_header("Step 3: 招标组建团队")

    pool = create_default_pool()
    print(f"人才池已加载，共 {pool.size} 个 Agent\n")

    engine = TenderEngine(pool)
    result = engine.run_tender(tender_spec)

    # 打印招标日志
    print("招标过程日志:")
    for log_entry in result.tender_log:
        print(f"  {log_entry}")

    print(f"\n中标团队 ({len(result.selected_team)} 人):")
    for member in result.selected_team:
        profile = member["profile"]
        role_spec = member["role"]
        score = member["score"]
        print(f"  {profile.name}")
        print(f"    角色: {role_spec.name} | 模型等级: {profile.model_tier} | 得分: {score.total_score:.1f}")
        print(f"    技能: {list(profile.skills.keys())[:5]}")

    print(f"\n公司: {result.company.name}")
    print(f"团队规模: {len(result.company.agents)} 人")

    # ══════════════════════════════════════════
    # Step 4: 价值观注入
    # ══════════════════════════════════════════
    print_header("Step 4: 价值观注入")

    value_system = ValueSystem(matched_values)
    behavior_prompt = value_system.generate_behavior_prompt()

    # 只打印前500字符作为预览
    print("生成的行为约束 Prompt（预览）:")
    print("-" * 40)
    preview = behavior_prompt[:500]
    print(preview)
    if len(behavior_prompt) > 500:
        print(f"... (共 {len(behavior_prompt)} 字符)")
    print("-" * 40)

    # 演示价值观审计
    print("\n价值观审计示例:")
    test_messages = [
        "这篇文章差不多就行了，赶紧发吧",
        "我已经完成了第三章的初稿，质量评分达到92分，所有事实核查都已通过",
        "这个不是我的问题，让其他人处理吧",
    ]
    for msg in test_messages:
        audit = value_system.audit_message(msg)
        status = "PASS" if audit.score >= 0.8 else "WARN" if audit.score >= 0.5 else "FAIL"
        print(f"  [{status}] (分数:{audit.score:.2f}) \"{msg[:40]}...\"")
        if audit.violations:
            print(f"        违反: {audit.violations[0]}")

    # ══════════════════════════════════════════
    # Step 5: 绩效模拟（3轮评审）
    # ══════════════════════════════════════════
    print_header("Step 5: 绩效模拟（3轮评审）")

    perf_engine = PerformanceEngine(
        review_interval=5,
        elimination_threshold=50.0,  # 低于50分触发淘汰
        warning_threshold=65.0,
    )

    # 注册所有团队成员到绩效引擎
    team_agent_ids = []
    for member in result.selected_team:
        profile = member["profile"]
        role_spec = member["role"]
        perf_engine.register_agent(profile.id, role_spec.name, profile.name)
        team_agent_ids.append(profile.id)

    print(f"已注册 {len(team_agent_ids)} 名成员到绩效引擎\n")

    # 模拟 3 轮绩效评审
    # 为了触发淘汰，让最后一个 agent 的绩效故意很差
    for round_num in range(1, 4):
        print(f"--- 第 {round_num} 轮绩效评审 ---\n")

        # 模拟每个 Agent 的工作表现数据
        for i, agent_id in enumerate(team_agent_ids):
            # 最后一个 agent 表现很差，其他正常
            if i == len(team_agent_ids) - 1:
                # 故意差的绩效
                quality = random.uniform(0.2, 0.4)
                response_time = random.uniform(8.0, 15.0)
                on_time = random.random() < 0.2
            elif i == 0:
                # 第一个表现最好
                quality = random.uniform(0.85, 0.98)
                response_time = random.uniform(1.0, 3.0)
                on_time = random.random() < 0.95
            else:
                # 其他人正常表现
                quality = random.uniform(0.6, 0.85)
                response_time = random.uniform(2.0, 6.0)
                on_time = random.random() < 0.75

            # 记录多次信号，模拟工作周期
            for tick in range(5):
                perf_engine.on_message(agent_id, response_time + random.uniform(-1, 1), int(quality * 3000), tick=tick)
                if tick % 2 == 0:
                    perf_engine.on_task_complete(agent_id, quality, on_time, tick=tick)

        # 执行绩效评审
        review = perf_engine.periodic_review(team_agent_ids)

        print(f"  公司整体得分: {review.company_score:.1f}")
        print(f"  排名:")
        for ps in review.rankings:
            grade_icon = {"S": "★", "A": "◆", "B": "●", "C": "○", "D": "△", "F": "✗"}
            icon = grade_icon.get(ps.grade.value, "?")
            print(f"    {icon} #{ps.rank} {ps.agent_name:12s} | "
                  f"得分: {ps.total_score:5.1f} | "
                  f"等级: {ps.grade.value} | "
                  f"趋势: {ps.trend}")

        if review.warnings:
            print(f"  警告名单: {[ps.agent_name for ps in review.warnings]}")
        if review.eliminations:
            print(f"  淘汰名单: {[ps.agent_name for ps in review.eliminations]}")
        print()

    # ══════════════════════════════════════════
    # Step 6: 末位淘汰
    # ══════════════════════════════════════════
    print_header("Step 6: 末位淘汰")

    elimination_engine = EliminationEngine(pool, bottom_ratio=0.2)

    # 获取最后一轮评审结果
    last_review = perf_engine.review_history[-1]

    # 执行淘汰
    replacements = elimination_engine.process_eliminations(
        review=last_review,
        company_values=tender_spec.value_priorities,
        current_agent_ids=team_agent_ids,
    )

    if replacements:
        print(f"本轮淘汰 {len(replacements)} 人:\n")
        for r in replacements:
            print(f"  淘汰: {r.removed_name}")
            print(f"    原因: {r.reason}")
            print(f"    绩效: {r.score:.1f} (等级 {r.grade})")
            print(f"    替补: {r.replaced_by_name}")
            print()
    else:
        print("本轮无需淘汰（所有成员绩效达标）")
        # 如果没有自动触发淘汰，手动处理末位
        print("\n执行额外评审以确保触发淘汰演示...")
        # 再跑一轮，确保有F级
        for i, agent_id in enumerate(team_agent_ids):
            if i == len(team_agent_ids) - 1:
                for tick in range(5):
                    perf_engine.on_message(agent_id, 20.0, 100, tick=tick)
                    perf_engine.on_task_complete(agent_id, 0.1, False, tick=tick)
            else:
                for tick in range(5):
                    perf_engine.on_message(agent_id, 2.0, 2000, tick=tick)
                    perf_engine.on_task_complete(agent_id, 0.85, True, tick=tick)

        extra_review = perf_engine.periodic_review(team_agent_ids)
        replacements = elimination_engine.process_eliminations(
            review=extra_review,
            company_values=tender_spec.value_priorities,
            current_agent_ids=team_agent_ids,
        )
        if replacements:
            print(f"\n本轮淘汰 {len(replacements)} 人:\n")
            for r in replacements:
                print(f"  淘汰: {r.removed_name}")
                print(f"    原因: {r.reason}")
                print(f"    绩效: {r.score:.1f} (等级 {r.grade})")
                print(f"    替补: {r.replaced_by_name}")
                print()

    # ══════════════════════════════════════════
    # Step 7: 总结
    # ══════════════════════════════════════════
    print_header("流程总结")

    print("Agent Company 完整招标流程演示完成:")
    print()
    print("  [x] 需求分析: 用户需求 → 结构化招标书 (TenderSpec)")
    print("  [x] 价值观匹配: 任务类型 → 最适配的价值观组合")
    print("  [x] 招标组建: 人才池筛选 → 竞标评审 → 最佳团队")
    print("  [x] 价值观注入: 价值观 → Agent 行为约束 prompt")
    print("  [x] 绩效模拟: KPI追踪 → 定期评审 → S/A/B/C/D/F 评级")
    print("  [x] 末位淘汰: 低绩效识别 → 自动替换 → 团队升级")
    print()
    print("关键数据:")
    print(f"  - 人才池规模: {pool.size} 个 Agent")
    print(f"  - 团队规模: {len(result.selected_team)} 人")
    print(f"  - 评审轮次: {len(perf_engine.review_history)} 轮")
    print(f"  - 淘汰人数: {len(replacements)} 人")
    print(f"  - 价值观条数: {len(matched_values)} 条")
    print()


if __name__ == "__main__":
    main()
