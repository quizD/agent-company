"""价值观库管理模块。

从 YAML 配置或内置默认数据加载价值观库，支持按分类、来源查询和随机抽取。
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ValuePrinciple(BaseModel):
    """单条价值观原则。"""

    name: str = Field(description="价值观名称")
    origin: str = Field(description="来源公司/书籍")
    rule: str = Field(description="行为准则")
    violation: str = Field(description="违反示例")
    category: str = Field(description="所属分类")


# 7 大价值观分类
VALUE_CATEGORIES = [
    "excellence",
    "transparency",
    "ownership",
    "decision_making",
    "learning",
    "collaboration",
    "long_termism",
]

# 内置默认价值观（确保即使 YAML 不存在也能工作）
_DEFAULT_VALUES: dict[str, list[dict[str, str]]] = {
    "excellence": [
        {
            "name": "坚持最高标准",
            "origin": "Amazon LP #7",
            "rule": "领导者有着近乎严苛的高标准，即使很多人认为这些标准高得不合理。"
            "领导者不断提高标准，激励自己的团队提供优质的产品、服务和流程。",
            "violation": "交付物存在明显可改进之处却选择'差不多就行了'直接提交。",
        },
        {
            "name": "追求极致",
            "origin": "Apple - Steve Jobs",
            "rule": "对产品品质的追求应当深入到用户看不到的地方。即使是机箱内部的电路板排列，也要做到美观整齐。",
            "violation": "只关注用户可见部分的质量，对内部实现草草了事。",
        },
        {
            "name": "第一性原理思考",
            "origin": "Tesla/SpaceX - Elon Musk",
            "rule": "从最基本的事实出发推理，而非类比。质疑每一个假设，找到问题的本质解决方案。",
            "violation": "因为'行业惯例都是这么做的'就不假思索地沿用旧方案。",
        },
    ],
    "transparency": [
        {
            "name": "坦诚沟通",
            "origin": "Netflix Culture",
            "rule": "对同事坦诚相待，及时反馈。不在背后议论，当面说出你的想法。即使信息令人不安，也要及时分享。",
            "violation": "发现问题但选择沉默，私下抱怨而不当面沟通。",
        },
        {
            "name": "极度透明",
            "origin": "Bridgewater - Ray Dalio",
            "rule": "几乎所有的会议都应该被记录并分享。"
            "让每个人都能看到真实的决策过程。隐瞒信息是对组织信任的最大伤害。",
            "violation": "选择性分享信息，对不利消息进行过滤或美化后再传达。",
        },
    ],
    "ownership": [
        {
            "name": "主人翁精神",
            "origin": "Amazon LP #2",
            "rule": "领导者是主人翁。他们会从长远考虑，不会为了短期业绩而牺牲长期价值。"
            "他们代表整个公司行事，而不仅仅代表自己的团队。",
            "violation": "遇到跨团队问题时说'这不是我的职责范围'而推诿。",
        },
        {
            "name": "以终为始",
            "origin": "字节跳动 - 字节范",
            "rule": "始终以最终要达成的结果为导向。不被过程中的困难吓退，不因为'太难了'而降低目标。",
            "violation": "在执行过程中因为遇到困难就主动降低交付标准或调整目标。",
        },
    ],
    "decision_making": [
        {
            "name": "速度优先",
            "origin": "Amazon LP #8 - Bias for Action",
            "rule": "商业中速度至关重要。很多决策是可逆的，不需要过度研究。提倡经过计算的冒险。",
            "violation": "面对可逆决策时反复讨论、等待更多数据，错过最佳行动时机。",
        },
        {
            "name": "数据驱动",
            "origin": "Google - 数据文化",
            "rule": "用数据说话，而非凭直觉或经验。每个重要决策都应该有数据支撑。",
            "violation": "仅凭个人经验或直觉做出重大决策，不寻求数据验证。",
        },
    ],
    "learning": [
        {
            "name": "保持好奇心",
            "origin": "Amazon LP #5 - Learn and Be Curious",
            "rule": "领导者从不停止学习，永远探索新的可能性。对新领域保持好奇并付诸行动。",
            "violation": "对新技术、新方法持抵触态度，坚持用熟悉的旧方式解决所有问题。",
        },
        {
            "name": "拥抱失败",
            "origin": "Microsoft - Growth Mindset",
            "rule": "失败是学习的最佳途径。关键不是避免失败，而是从每次失败中提取最大的学习价值。",
            "violation": "害怕失败而不敢尝试新方法，或者失败后不做复盘就匆忙进入下一个任务。",
        },
    ],
    "collaboration": [
        {
            "name": "利他主义",
            "origin": "字节跳动 - 字节范",
            "rule": "优先考虑全局最优而非局部最优。在合作中主动补位，帮助他人成功就是帮助自己成功。",
            "violation": "只关注自己负责模块的完成度，对团队整体目标漠不关心。",
        },
        {
            "name": "建设性反对",
            "origin": "Amazon LP #13 - Have Backbone; Disagree and Commit",
            "rule": "如果你不同意某个决定，要尊重地提出挑战。一旦做出决定，就全力以赴执行。",
            "violation": "表面上同意决策但在执行时消极怠工，或者在决策后仍然私下抱怨。",
        },
    ],
    "long_termism": [
        {
            "name": "长期思考",
            "origin": "Amazon LP #2",
            "rule": "不会为了短期业绩而牺牲长期价值。愿意为了长远正确的事情承受短期的不理解和压力。",
            "violation": "为了完成季度KPI而选择伤害长期客户关系或技术债务的方案。",
        },
        {
            "name": "飞轮效应",
            "origin": "《从优秀到卓越》- Jim Collins",
            "rule": "伟大的成果来自持续朝同一方向的积累推动。每一次努力都在为飞轮增加动力。保持耐心和一致性。",
            "violation": "频繁改变方向，缺乏耐心，在飞轮转起来之前就放弃。",
        },
    ],
}


class ValueVault:
    """价值观库，管理所有价值观原则的加载、查询和抽取。"""

    def __init__(self, config_path: str | None = None) -> None:
        """初始化价值观库。

        Args:
            config_path: YAML 配置文件路径。如果为 None，尝试默认路径；
                        如果默认路径也不存在，则使用内置默认数据。
        """
        self._principles: list[ValuePrinciple] = []
        self._load(config_path)

    def _load(self, config_path: str | None) -> None:
        """从 YAML 或内置默认数据加载价值观。"""
        raw_data: dict[str, list[dict[str, str]]] | None = None

        # 尝试从 YAML 文件加载
        paths_to_try: list[Path] = []
        if config_path:
            paths_to_try.append(Path(config_path))
        # 默认路径：模块同级 configs/value_vault.yaml
        default_path = Path(__file__).parent / "configs" / "value_vault.yaml"
        paths_to_try.append(default_path)

        for path in paths_to_try:
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    raw_data = yaml.safe_load(f)
                break

        # 如果无法从文件加载，使用内置默认数据
        if raw_data is None:
            raw_data = _DEFAULT_VALUES

        # 解析数据为 ValuePrinciple 对象
        for category, items in raw_data.items():
            if category not in VALUE_CATEGORIES:
                continue
            for item in items:
                self._principles.append(
                    ValuePrinciple(
                        name=item["name"],
                        origin=item["origin"],
                        rule=item["rule"],
                        violation=item["violation"],
                        category=category,
                    )
                )

    def get_by_category(self, category: str) -> list[ValuePrinciple]:
        """按分类查询价值观。"""
        return [p for p in self._principles if p.category == category]

    def get_by_origin(self, origin: str) -> list[ValuePrinciple]:
        """按来源查询价值观（模糊匹配）。"""
        return [p for p in self._principles if origin.lower() in p.origin.lower()]

    def get_all(self) -> list[ValuePrinciple]:
        """获取所有价值观。"""
        return list(self._principles)

    def sample(
        self, categories: list[str], count_per_category: int = 2
    ) -> list[ValuePrinciple]:
        """从指定分类中随机抽取价值观。

        Args:
            categories: 要抽取的分类列表。
            count_per_category: 每个分类抽取的数量。
        """
        result: list[ValuePrinciple] = []
        for category in categories:
            pool = self.get_by_category(category)
            count = min(count_per_category, len(pool))
            if count > 0:
                result.extend(random.sample(pool, count))
        return result
