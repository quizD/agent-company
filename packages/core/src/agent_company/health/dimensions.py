"""十二维健康度维度定义与评分逻辑。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthDimension(BaseModel):
    """单个健康维度模型。"""

    name: str = Field(description="维度英文标识")
    display_name: str = Field(description="维度中文名称")
    description: str = Field(description="该维度评估的内容")
    weight: float = Field(default=1.0, description="权重（越高越重要）")
    score: float = Field(default=0.0, ge=0.0, le=100.0, description="当前得分 (0-100)")
    indicators: list[str] = Field(default_factory=list, description="构成指标列表")


class DimensionScorer:
    """各维度评分逻辑，每个方法返回 0-100 分。"""

    # ------------------------------------------------------------------
    # 1. 组织学
    # ------------------------------------------------------------------
    @staticmethod
    def score_organizational(company_data: dict) -> float:
        """评估组织结构健康度：
        - 所有 Agent 都有明确角色 (+25)
        - 部门数量合理 (+25)
        - 存在汇报关系 (+25)
        - 治理规则完整 (+25)
        """
        score = 0.0
        agents = company_data.get("agents", [])
        departments = company_data.get("departments", [])
        governance_rules = company_data.get("governance_rules", [])

        # 所有 Agent 都有明确角色
        if agents and all(a.get("role") for a in agents):
            score += 25.0
        elif agents:
            defined = sum(1 for a in agents if a.get("role"))
            score += 25.0 * (defined / len(agents))

        # 部门数量合理：至少 1 个，且不超过 Agent 总数
        if departments:
            agent_count = max(len(agents), 1)
            dept_count = len(departments)
            if 1 <= dept_count <= agent_count:
                score += 25.0
            else:
                score += 12.5

        # 存在汇报关系
        has_reporting = any(a.get("reports_to") for a in agents)
        if has_reporting:
            score += 25.0

        # 治理规则完整
        if len(governance_rules) >= 3:
            score += 25.0
        elif governance_rules:
            score += 25.0 * (len(governance_rules) / 3)

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 2. 社会学
    # ------------------------------------------------------------------
    @staticmethod
    def score_sociological(company_data: dict) -> float:
        """评估团队社会健康度：
        - 沟通频率适中 (+30)
        - 存在跨部门沟通 (+35)
        - 冲突解决记录 (+35)
        """
        score = 0.0
        messages = company_data.get("messages", [])
        agents = company_data.get("agents", [])
        departments = company_data.get("departments", [])

        # 沟通频率：每个 Agent 平均至少发送 1 条消息
        agent_count = max(len(agents), 1)
        msg_per_agent = len(messages) / agent_count
        if msg_per_agent >= 1.0:
            score += 30.0
        else:
            score += 30.0 * msg_per_agent

        # 跨部门沟通：消息中存在不同部门的 Agent 之间的交流
        if len(departments) > 1 and messages:
            # 简化判定：消息发送者和接收者属于不同部门
            senders = {m.get("from") for m in messages}
            receivers = {m.get("to") for m in messages}
            participants = senders | receivers
            dept_map: dict[str, str] = {}
            for dept in departments:
                for member in dept.get("members", []):
                    dept_map[member] = dept.get("name", "")
            involved_depts = {dept_map.get(p, "") for p in participants if dept_map.get(p)}
            if len(involved_depts) > 1:
                score += 35.0
            else:
                score += 10.0
        elif len(departments) <= 1 and messages:
            # 只有一个部门时，只要有沟通就给分
            score += 35.0

        # 冲突解决记录
        conflicts_resolved = company_data.get("conflicts_resolved", 0)
        conflicts_total = company_data.get("conflicts_total", 0)
        if conflicts_total > 0:
            score += 35.0 * (conflicts_resolved / conflicts_total)
        else:
            # 没有冲突也算健康
            score += 35.0

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 3. 商业
    # ------------------------------------------------------------------
    @staticmethod
    def score_business(company_data: dict) -> float:
        """评估商业交付健康度：
        - 任务完成率 (+40)
        - 质量达标率 (+30)
        - 效率（按时完成比例）(+30)
        """
        score = 0.0
        tasks = company_data.get("tasks", [])

        if not tasks:
            return 50.0  # 无任务时给中等分

        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        quality_pass = sum(1 for t in tasks if t.get("quality_pass", False))
        on_time = sum(1 for t in tasks if t.get("on_time", False))

        score += 40.0 * (completed / total)
        score += 30.0 * (quality_pass / total)
        score += 30.0 * (on_time / total)

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 4. 心理学
    # ------------------------------------------------------------------
    @staticmethod
    def score_psychological(company_data: dict) -> float:
        """评估 Agent 心理健康度：
        - 负载均衡度 (+35)
        - 压力分布合理 (+35)
        - 工作满意度 (+30)
        """
        score = 0.0
        agents = company_data.get("agents", [])

        if not agents:
            return 50.0

        # 负载均衡：各 Agent 任务数的标准差越小越好
        workloads = [a.get("workload", 0) for a in agents]
        if workloads:
            avg_load = sum(workloads) / len(workloads)
            if avg_load > 0:
                variance = sum((w - avg_load) ** 2 for w in workloads) / len(workloads)
                std_dev = variance ** 0.5
                # 标准差占平均值的比例越小越好
                cv = std_dev / avg_load  # 变异系数
                balance_score = max(0.0, 1.0 - cv)
                score += 35.0 * balance_score
            else:
                score += 35.0  # 都没有负载也算均衡

        # 压力分布：没有 Agent 过载
        max_capacity = company_data.get("max_capacity_per_agent", 10)
        overloaded = sum(1 for w in workloads if w > max_capacity)
        if overloaded == 0:
            score += 35.0
        else:
            score += 35.0 * (1 - overloaded / len(agents))

        # 工作满意度
        satisfaction_scores = [a.get("satisfaction", 0.8) for a in agents]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
        score += 30.0 * avg_satisfaction

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 5. 伦理学
    # ------------------------------------------------------------------
    @staticmethod
    def score_ethical(company_data: dict) -> float:
        """评估伦理健康度：
        - 价值观一致性 (+35)
        - 公平性（任务分配均匀）(+35)
        - 透明度（决策有记录）(+30)
        """
        score = 0.0
        agents = company_data.get("agents", [])
        values = company_data.get("values", [])
        decisions = company_data.get("decisions", [])

        # 价值观一致性：Agent 的行为记录中未违反公司价值观
        violations = company_data.get("value_violations", 0)
        if values:
            if violations == 0:
                score += 35.0
            else:
                penalty = min(violations * 5, 35)
                score += max(0.0, 35.0 - penalty)
        else:
            score += 17.5  # 未定义价值观给一半分

        # 公平性：任务分配的均匀度
        if agents:
            task_counts = [a.get("task_count", 0) for a in agents]
            if any(task_counts):
                avg_tasks = sum(task_counts) / len(task_counts)
                if avg_tasks > 0:
                    max_diff = max(abs(tc - avg_tasks) for tc in task_counts)
                    fairness = max(0.0, 1.0 - (max_diff / avg_tasks / 2))
                    score += 35.0 * fairness
                else:
                    score += 35.0
            else:
                score += 35.0

        # 透明度：决策有记录
        if decisions:
            documented = sum(1 for d in decisions if d.get("documented", False))
            score += 30.0 * (documented / len(decisions))
        else:
            score += 15.0  # 无决策记录给一半

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 6. 生态/系统论
    # ------------------------------------------------------------------
    @staticmethod
    def score_ecological(company_data: dict) -> float:
        """评估系统生态健康度：
        - 资源利用效率 (+35)
        - 可持续性（无资源耗尽风险）(+35)
        - 冗余度（关键角色有备份）(+30)
        """
        score = 0.0
        agents = company_data.get("agents", [])
        budget_info = company_data.get("budget_info", {})

        # 资源利用效率：已用资源 / 总资源
        total_resource = budget_info.get("total_resource", 0)
        used_resource = budget_info.get("used_resource", 0)
        if total_resource > 0:
            utilization = used_resource / total_resource
            # 最优利用率在 60%-85% 之间
            if 0.6 <= utilization <= 0.85:
                score += 35.0
            elif utilization < 0.6:
                score += 35.0 * (utilization / 0.6)
            else:
                # 过度使用，扣分
                score += 35.0 * max(0.0, 1.0 - (utilization - 0.85) / 0.15)
        else:
            score += 17.5

        # 可持续性：剩余预算占比
        budget_total = budget_info.get("budget_total", 0)
        budget_remaining = budget_info.get("budget_remaining", 0)
        if budget_total > 0:
            remaining_ratio = budget_remaining / budget_total
            score += 35.0 * min(remaining_ratio * 2, 1.0)  # 剩余50%以上满分
        else:
            score += 17.5

        # 冗余度：关键角色是否有多个 Agent 能胜任
        roles = [a.get("role", "") for a in agents if a.get("role")]
        if roles:
            from collections import Counter
            role_counts = Counter(roles)
            critical_roles = company_data.get("critical_roles", [])
            if critical_roles:
                redundant = sum(1 for r in critical_roles if role_counts.get(r, 0) > 1)
                score += 30.0 * (redundant / len(critical_roles))
            else:
                # 没有定义关键角色，看是否存在重复角色
                has_redundancy = any(c > 1 for c in role_counts.values())
                score += 15.0 if has_redundancy else 10.0
        else:
            score += 10.0

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 7. 信息论/控制论
    # ------------------------------------------------------------------
    @staticmethod
    def score_information(company_data: dict) -> float:
        """评估信息流健康度：
        - 信息流畅度（消息响应时间）(+35)
        - 反馈及时性 (+35)
        - 决策效率 (+30)
        """
        score = 0.0
        messages = company_data.get("messages", [])
        decisions = company_data.get("decisions", [])

        # 信息流畅度：消息有回复的比例
        if messages:
            replied = sum(1 for m in messages if m.get("replied", False))
            score += 35.0 * (replied / len(messages))
        else:
            score += 17.5

        # 反馈及时性：平均响应时间
        avg_response_time = company_data.get("avg_response_time", None)
        max_acceptable_time = company_data.get("max_acceptable_response_time", 60)
        if avg_response_time is not None:
            if avg_response_time <= max_acceptable_time:
                score += 35.0
            else:
                ratio = max_acceptable_time / avg_response_time
                score += 35.0 * ratio
        else:
            score += 17.5

        # 决策效率：决策从提出到执行的时间
        if decisions:
            efficient = sum(1 for d in decisions if d.get("efficient", False))
            score += 30.0 * (efficient / len(decisions))
        else:
            score += 15.0

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 8. 人类学/文化
    # ------------------------------------------------------------------
    @staticmethod
    def score_cultural(company_data: dict) -> float:
        """评估文化健康度：
        - 价值观践行度 (+35)
        - 仪式文化（定期回顾/会议）(+30)
        - 知识传承（文档完善度）(+35)
        """
        score = 0.0
        values = company_data.get("values", [])
        rituals = company_data.get("rituals", [])
        knowledge_base = company_data.get("knowledge_base", {})

        # 价值观践行度
        if values:
            practiced = company_data.get("values_practiced", 0)
            score += 35.0 * min(practiced / len(values), 1.0)
        else:
            score += 17.5

        # 仪式文化：是否有定期活动
        if rituals:
            active_rituals = sum(1 for r in rituals if r.get("active", False))
            score += 30.0 * (active_rituals / len(rituals))
        else:
            score += 0.0  # 无仪式文化不给分

        # 知识传承：文档覆盖率
        doc_coverage = knowledge_base.get("coverage", 0.0)
        score += 35.0 * doc_coverage

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 9. 政治学
    # ------------------------------------------------------------------
    @staticmethod
    def score_political(company_data: dict) -> float:
        """评估治理健康度：
        - 权力分配合理性 (+35)
        - 治理有效性 (+35)
        - 参与度 (+30)
        """
        score = 0.0
        agents = company_data.get("agents", [])
        governance_rules = company_data.get("governance_rules", [])

        # 权力分配：不应过度集中
        if agents:
            power_levels = [a.get("authority_level", 1) for a in agents]
            max_power = max(power_levels)
            min_power = min(power_levels)
            if max_power > 0:
                # 权力差距不应超过3倍
                ratio = max_power / max(min_power, 1)
                if ratio <= 3:
                    score += 35.0
                else:
                    score += 35.0 * (3 / ratio)

        # 治理有效性：规则被执行的比例
        if governance_rules:
            if isinstance(governance_rules[0], dict):
                enforced = sum(1 for r in governance_rules if r.get("enforced", False))
            else:
                enforced = len(governance_rules)
            total_rules = len(governance_rules)
            score += 35.0 * (enforced / total_rules)
        else:
            score += 0.0

        # 参与度：Agent 参与决策的比例
        decisions = company_data.get("decisions", [])
        if decisions and agents:
            participants = set()
            for d in decisions:
                participants.update(d.get("participants", []))
            participation_rate = len(participants) / len(agents)
            score += 30.0 * min(participation_rate, 1.0)
        else:
            score += 15.0

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 10. 时间维度
    # ------------------------------------------------------------------
    @staticmethod
    def score_temporal(company_data: dict) -> float:
        """评估时间管理健康度：
        - 进度掌控（按计划完成率）(+35)
        - 节奏稳定性 (+35)
        - 适应变化能力 (+30)
        """
        score = 0.0
        tasks = company_data.get("tasks", [])

        if not tasks:
            return 50.0

        # 进度掌控：按时完成的比例
        total = len(tasks)
        on_schedule = sum(1 for t in tasks if t.get("on_time", False))
        score += 35.0 * (on_schedule / total)

        # 节奏稳定性：任务完成时间的波动性
        durations = [t.get("duration", 0) for t in tasks if t.get("duration")]
        if durations:
            avg_dur = sum(durations) / len(durations)
            if avg_dur > 0:
                variance = sum((d - avg_dur) ** 2 for d in durations) / len(durations)
                std_dev = variance ** 0.5
                cv = std_dev / avg_dur
                stability = max(0.0, 1.0 - cv)
                score += 35.0 * stability
            else:
                score += 35.0
        else:
            score += 17.5

        # 适应变化能力：需求变更后仍能完成的比例
        changed_tasks = [t for t in tasks if t.get("requirements_changed", False)]
        if changed_tasks:
            adapted = sum(1 for t in changed_tasks if t.get("status") == "completed")
            score += 30.0 * (adapted / len(changed_tasks))
        else:
            score += 30.0  # 没有变更也算适应良好

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 11. 经济维度
    # ------------------------------------------------------------------
    @staticmethod
    def score_economic(company_data: dict) -> float:
        """评估经济健康度：
        - 成本效率 (+35)
        - 预算利用率 (+35)
        - 投入产出比 (+30)
        """
        score = 0.0
        budget_info = company_data.get("budget_info", {})
        tasks = company_data.get("tasks", [])

        # 成本效率：实际成本 vs 预算
        actual_cost = budget_info.get("actual_cost", 0)
        planned_cost = budget_info.get("planned_cost", 0)
        if planned_cost > 0:
            cost_ratio = actual_cost / planned_cost
            if cost_ratio <= 1.0:
                score += 35.0
            else:
                # 超支扣分
                score += 35.0 * max(0.0, 2.0 - cost_ratio)
        else:
            score += 17.5

        # 预算利用率：已使用预算 / 总预算，最优 70%-90%
        budget_total = budget_info.get("budget_total", 0)
        budget_used = budget_info.get("budget_used", 0)
        if budget_total > 0:
            usage = budget_used / budget_total
            if 0.7 <= usage <= 0.9:
                score += 35.0
            elif usage < 0.7:
                score += 35.0 * (usage / 0.7)
            else:
                score += 35.0 * max(0.0, 1.0 - (usage - 0.9) / 0.1)
        else:
            score += 17.5

        # 投入产出比：完成任务数 / 成本
        if tasks and actual_cost > 0:
            completed = sum(1 for t in tasks if t.get("status") == "completed")
            expected_output = budget_info.get("expected_output", len(tasks))
            if expected_output > 0:
                roi = completed / expected_output
                score += 30.0 * min(roi, 1.0)
            else:
                score += 15.0
        else:
            score += 15.0

        return min(score, 100.0)

    # ------------------------------------------------------------------
    # 12. 学习维度
    # ------------------------------------------------------------------
    @staticmethod
    def score_learning(company_data: dict) -> float:
        """评估学习能力健康度：
        - 错误修正率 (+35)
        - 知识增长 (+35)
        - 持续改进 (+30)
        """
        score = 0.0
        performance_scores = company_data.get("performance_scores", {})

        # 错误修正率：错误被修复的比例
        errors_total = performance_scores.get("errors_total", 0)
        errors_fixed = performance_scores.get("errors_fixed", 0)
        if errors_total > 0:
            score += 35.0 * (errors_fixed / errors_total)
        else:
            score += 35.0  # 无错误满分

        # 知识增长：技能数或知识条目增长
        knowledge_growth = performance_scores.get("knowledge_growth_rate", 0.0)
        score += 35.0 * min(knowledge_growth, 1.0)

        # 持续改进：后续任务评分是否高于前期
        improvement_rate = performance_scores.get("improvement_rate", 0.0)
        if improvement_rate > 0:
            score += 30.0 * min(improvement_rate, 1.0)
        elif improvement_rate == 0:
            score += 15.0  # 没有退步也给一半
        else:
            score += 0.0  # 退步不给分

        return min(score, 100.0)


# --------------------------------------------------------------------------
# 预定义 12 个维度
# --------------------------------------------------------------------------
ALL_DIMENSIONS: list[HealthDimension] = [
    HealthDimension(
        name="organizational",
        display_name="组织学",
        description="结构清晰度、角色定义完整性、汇报关系合理性",
        weight=1.2,
        indicators=["角色定义率", "部门合理度", "汇报关系覆盖率", "治理规则数"],
    ),
    HealthDimension(
        name="sociological",
        display_name="社会学",
        description="团队凝聚力、沟通质量、冲突处理",
        weight=1.0,
        indicators=["沟通频率", "跨部门沟通率", "冲突解决率"],
    ),
    HealthDimension(
        name="business",
        display_name="商业",
        description="交付完成度、质量达标率、效率",
        weight=1.5,
        indicators=["任务完成率", "质量达标率", "按时完成率"],
    ),
    HealthDimension(
        name="psychological",
        display_name="心理学",
        description="Agent 负载均衡、压力分布、工作满意度",
        weight=1.0,
        indicators=["负载均衡度", "过载率", "满意度均值"],
    ),
    HealthDimension(
        name="ethical",
        display_name="伦理学",
        description="价值观一致性、公平性、透明度",
        weight=1.0,
        indicators=["价值观违规数", "任务分配均匀度", "决策文档化率"],
    ),
    HealthDimension(
        name="ecological",
        display_name="生态/系统论",
        description="资源利用效率、可持续性、冗余度",
        weight=1.0,
        indicators=["资源利用率", "预算剩余率", "关键角色冗余度"],
    ),
    HealthDimension(
        name="information",
        display_name="信息论/控制论",
        description="信息流畅度、反馈及时性、决策效率",
        weight=1.1,
        indicators=["消息回复率", "平均响应时间", "决策执行效率"],
    ),
    HealthDimension(
        name="cultural",
        display_name="人类学/文化",
        description="价值观践行度、仪式文化、知识传承",
        weight=0.8,
        indicators=["价值观践行率", "活跃仪式数", "文档覆盖率"],
    ),
    HealthDimension(
        name="political",
        display_name="政治学",
        description="权力分配合理性、治理有效性、参与度",
        weight=0.9,
        indicators=["权力集中度", "规则执行率", "决策参与率"],
    ),
    HealthDimension(
        name="temporal",
        display_name="时间维度",
        description="进度掌控、节奏稳定性、适应变化能力",
        weight=1.1,
        indicators=["按计划完成率", "节奏稳定性", "变更适应率"],
    ),
    HealthDimension(
        name="economic",
        display_name="经济维度",
        description="成本效率、预算利用率、投入产出比",
        weight=1.2,
        indicators=["成本效率比", "预算利用率", "投入产出比"],
    ),
    HealthDimension(
        name="learning",
        display_name="学习维度",
        description="错误修正率、知识增长、持续改进",
        weight=1.1,
        indicators=["错误修正率", "知识增长率", "改进率"],
    ),
]
