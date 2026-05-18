"""价值观注入/审计/检测模块。

将价值观转化为行为指令，并提供消息和交付物的价值观符合度审计。
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from .vault import ValuePrinciple


class ValueAudit(BaseModel):
    """价值观审计结果。"""

    score: float = Field(ge=0.0, le=1.0, description="符合度评分（0-1）")
    violations: list[str] = Field(default_factory=list, description="检测到的违反项")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")


# 违反价值观的关键词/模式检测规则
_VIOLATION_PATTERNS: dict[str, list[tuple[str, str, str]]] = {
    # 模式: (正则表达式, 违反描述, 改进建议)
    "敷衍": [
        (r"差不多[就了]", "表现出敷衍态度，缺乏追求卓越的精神", "明确给出具体的完成标准和质量要求"),
        (r"随便[吧了]", "表现出不负责任的态度", "认真对待每个决策点，给出明确的建议"),
        (r"就这样吧", "缺乏精益求精的态度", "思考是否还有可以优化的空间"),
        (r"能用就行", "标准过低，缺乏卓越追求", "设定更高的质量标准并持续优化"),
    ],
    "推卸": [
        (r"不是我的[问题责任事]", "推卸责任，缺乏主人翁精神", "主动承担问题并寻找解决方案"),
        (r"不关我[的事]", "缺乏全局视角和责任感", "从全局角度思考如何贡献价值"),
        (r"这不归我管", "职责边界思维过重", "主动跨边界协作，推动问题解决"),
        (r"你们自己[看搞弄]", "推诿协作责任", "提供具体帮助或资源支持"),
    ],
    "隐瞒": [
        (r"先不[说提告]", "有隐瞒信息的倾向", "及时透明地分享所有相关信息"),
        (r"别让.{0,4}知道", "刻意隐瞒信息", "保持信息透明，让相关方了解实际情况"),
        (r"这个[先暂]不汇报", "延迟汇报关键信息", "无论好坏消息都应及时同步"),
    ],
    "含糊": [
        (r"大概[是可能]", "表述含糊，缺乏明确性", "给出具体的数据、时间节点或确定性结论"),
        (r"应该[没不]", "缺乏确定性的表述", "用数据或事实验证后给出确定性结论"),
        (r"可能[会是有]", "模糊表达，不够笃定", "进行验证后给出明确判断"),
        (r"不太确定", "缺乏深入调研", "先做调研和验证，再给出有依据的结论"),
    ],
    "消极抵抗": [
        (r"做不到", "消极抵抗，缺乏解决问题的意愿", "分析阻碍因素并提出替代方案"),
        (r"不可能[的了]", "过早放弃，缺乏挑战精神", "从第一性原理重新审视问题"),
        (r"没[什么有]意义", "消极态度", "寻找工作的意义和价值连接点"),
        (r"算了[吧不]", "放弃态度", "坚持寻找解决方案，不轻言放弃"),
    ],
}

# 价值观到行为指令的转化模板
_BEHAVIOR_TEMPLATES: dict[str, str] = {
    "excellence": (
        "在每次产出前，你必须自问：这是我能做到的最高质量吗？如果不是，继续优化。"
        "不接受'差不多'的标准，追求让人惊叹的品质。"
    ),
    "transparency": (
        "你必须坦诚地分享所有相关信息，包括不确定性和风险。"
        "永远不要隐瞒坏消息或美化事实。用数据和证据说话。"
    ),
    "ownership": (
        "把每个任务当作自己的事业来对待。遇到问题不推诿，"
        "主动寻找解决方案。确保每件事都有明确的闭环和结果。"
    ),
    "decision_making": (
        "做决策时优先考虑速度与质量的平衡。可逆决策快速执行，"
        "不可逆决策审慎分析。始终用数据支撑判断。"
    ),
    "learning": (
        "保持强烈的好奇心和学习欲望。从每次经历中提取教训，"
        "主动总结和分享知识。勇于尝试新方法。"
    ),
    "collaboration": (
        "在协作中优先考虑全局最优。主动补位，帮助他人成功。"
        "有不同意见时建设性地提出，决策后全力执行。"
    ),
    "long_termism": (
        "在短期利益和长期价值冲突时，坚定选择长期价值。"
        "每个决策都要考虑其长期影响，建设可持续的系统而非临时方案。"
    ),
}


class ValueSystem:
    """价值观系统，负责将价值观注入 Agent 行为并审计合规性。"""

    def __init__(self, values: list[ValuePrinciple]) -> None:
        """初始化价值观系统。

        Args:
            values: 当前生效的价值观列表。
        """
        self._values = values
        self._categories = list({v.category for v in values})

    def generate_behavior_prompt(self) -> str:
        """将价值观转化为 Agent system prompt 中的行为指令。

        不是简单罗列价值观名称，而是转化为具体的行为约束和自我检查机制。
        """
        lines: list[str] = []
        lines.append("## 行为价值观准则")
        lines.append("")
        lines.append("你的每一个行为都必须遵循以下准则：")
        lines.append("")

        # 按分类生成行为指令
        for category in self._categories:
            category_values = [v for v in self._values if v.category == category]
            template = _BEHAVIOR_TEMPLATES.get(category, "")
            if template:
                lines.append(f"### {category.upper()}")
                lines.append(f"**核心要求**：{template}")
                lines.append("")
                lines.append("**具体准则**：")
                for v in category_values:
                    lines.append(f"- [{v.origin}] {v.rule}")
                lines.append("")
                lines.append("**绝不允许**：")
                for v in category_values:
                    lines.append(f"- {v.violation}")
                lines.append("")

        # 添加自我检查指令
        lines.append("### 自我检查")
        lines.append("在每次回复前，检查以下几点：")
        lines.append("1. 我的产出是否达到了最高标准？")
        lines.append("2. 我是否完全透明，没有隐瞒任何信息？")
        lines.append("3. 我是否像主人翁一样对结果负责？")
        lines.append("4. 我的建议是否经过深思熟虑？")
        lines.append("")

        return "\n".join(lines)

    def audit_message(self, message_content: str) -> ValueAudit:
        """审计消息是否符合价值观（基于规则的启发式检测，不调用 LLM）。

        检测敷衍、推卸、隐瞒、含糊、消极抵抗等关键词模式。

        Args:
            message_content: 待审计的消息内容。
        """
        violations: list[str] = []
        suggestions: list[str] = []

        for _pattern_type, patterns in _VIOLATION_PATTERNS.items():
            for regex, violation_desc, suggestion in patterns:
                if re.search(regex, message_content):
                    violations.append(violation_desc)
                    suggestions.append(suggestion)

        # 去重
        violations = list(dict.fromkeys(violations))
        suggestions = list(dict.fromkeys(suggestions))

        # 计算符合度评分
        # 基础分 1.0，每个违反扣 0.15，最低 0.0
        score = max(0.0, 1.0 - len(violations) * 0.15)

        return ValueAudit(score=score, violations=violations, suggestions=suggestions)

    def audit_deliverable(
        self, deliverable_description: str, quality_score: float
    ) -> ValueAudit:
        """审计交付物质量是否体现价值观。

        Args:
            deliverable_description: 交付物描述。
            quality_score: 外部评定的质量分数（0-1）。
        """
        violations: list[str] = []
        suggestions: list[str] = []

        # 基于质量分数评估卓越标准
        if quality_score < 0.6:
            violations.append("交付物质量未达到卓越标准（低于0.6）")
            suggestions.append("重新审视交付物，对照最高标准进行优化")
        elif quality_score < 0.8:
            suggestions.append("质量尚可但仍有提升空间，建议追求更高标准")

        # 检查交付物描述的完整性（透明度）
        if len(deliverable_description.strip()) < 20:
            violations.append("交付物描述过于简略，缺乏透明度")
            suggestions.append("提供详细的交付物说明，包括范围、限制和已知问题")

        # 检查是否有明确的结果闭环（主人翁精神）
        closure_keywords = ["完成", "结果", "交付", "产出", "成果", "已"]
        has_closure = any(kw in deliverable_description for kw in closure_keywords)
        if not has_closure:
            suggestions.append("建议明确标注交付状态和完成度，体现闭环思维")

        # 综合评分
        base_score = quality_score
        penalty = len(violations) * 0.1
        score = max(0.0, min(1.0, base_score - penalty))

        return ValueAudit(score=score, violations=violations, suggestions=suggestions)
