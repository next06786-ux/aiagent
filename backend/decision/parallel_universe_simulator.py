"""
平行宇宙模拟器
通过本地 Qwen3.5-9B 基座 + 用户专属 LoRA 模拟不同决策选项的未来时间线

架构：
  simulate_decision (async)
    → 对每个选项调用 LoRADecisionAnalyzer.generate_timeline_with_lora (async → transformers+peft)
    → 本地计算得分 & 风险评估
    → 调用 LoRADecisionAnalyzer.generate_personalized_recommendation (async → transformers+peft)
"""
import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.digital_twin.digital_twin import DigitalTwin
from backend.personality.personality_test import PersonalityTest
from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
from backend.decision.risk_assessment_engine import RiskAssessmentEngine


@dataclass
class TimelineEvent:
    """时间线事件 / 副本节点"""
    event_id: str
    parent_event_id: Optional[str]
    month: int
    event: str
    impact: Dict[str, float]
    probability: float
    event_type: str = "general"
    branch_group: str = "main"
    node_level: int = 1
    risk_tag: str = "medium"
    opportunity_tag: str = "medium"
    visual_weight: float = 0.5


@dataclass
class DecisionOption:
    """决策选项"""
    option_id: str
    title: str
    description: str
    timeline: List[TimelineEvent]
    final_score: float
    risk_level: float
    risk_assessment: Optional[Dict] = None


@dataclass
class SimulationResult:
    """模拟结果"""
    simulation_id: str
    user_id: str
    question: str
    options: List[DecisionOption]
    recommendation: str
    created_at: str


class ParallelUniverseSimulator:
    """平行宇宙模拟器 — 通过本地 transformers + LoRA 推理"""

    def __init__(self):
        self.personality_test = PersonalityTest()
        self.lora_analyzer = LoRADecisionAnalyzer()
        self.risk_engine = RiskAssessmentEngine()

    async def simulate_decision(
        self,
        user_id: str,
        question: str,
        options: List[Dict[str, str]],
    ) -> SimulationResult:
        """
        模拟决策（异步，通过本地 Qwen3.5-9B + 用户 LoRA 推理）

        Args:
            user_id: 用户ID
            question: 决策问题
            options: [{"title": "选项A", "description": "..."}]

        Returns:
            SimulationResult
        """
        # 检查用户是否有 LoRA 模型
        if not self.lora_analyzer.has_lora_model(user_id):
            raise ValueError(
                f"用户 {user_id} 还没有训练 LoRA 模型，无法进行个性化决策模拟。"
                f"请先通过 /api/lora/train/{user_id} 触发训练。"
            )

        # 1. 加载用户性格画像
        profile = self.personality_test.load_profile(user_id)

        # 2. 串行为每个选项生成时间线，避免一次请求并发加载多个 LoRA 导致显存冲突
        timelines = []
        for opt in options:
            timeline_data = await self.lora_analyzer.generate_timeline_with_lora(
                user_id=user_id,
                question=question,
                option=opt,
                profile=profile,
                num_events=5
            )
            timelines.append(timeline_data)

        # 3. 本地计算得分和风险
        simulated_options = []
        for i, (option, timeline_data) in enumerate(zip(options, timelines)):
            timeline = []
            option_branch = option['title'].lower().replace(' ', '_')
            previous_event_id = None
            for idx, e in enumerate(timeline_data):
                risk_tag = "medium"
                opportunity_tag = "medium"
                negative_impact = sum(abs(v) for v in e['impact'].values() if v < 0)
                positive_impact = sum(v for v in e['impact'].values() if v > 0)
                if negative_impact >= 0.5:
                    risk_tag = "high"
                elif negative_impact <= 0.1:
                    risk_tag = "low"
                if positive_impact >= 0.5:
                    opportunity_tag = "high"
                elif positive_impact <= 0.1:
                    opportunity_tag = "low"

                timeline.append(TimelineEvent(
                    event_id=f"{option_branch}_node_{idx+1}",
                    parent_event_id=previous_event_id,
                    month=e['month'],
                    event=e['event'],
                    impact=e['impact'],
                    probability=e['probability'],
                    event_type=self._infer_event_type(e['event']),
                    branch_group=option_branch,
                    node_level=idx + 1,
                    risk_tag=risk_tag,
                    opportunity_tag=opportunity_tag,
                    visual_weight=max(0.2, min(1.0, positive_impact + negative_impact))
                ))
                previous_event_id = timeline[-1].event_id

            # 为高影响节点生成分支事件，形成思维导图拓扑
            branch_nodes = self._generate_branch_events(timeline, option_branch)
            timeline.extend(branch_nodes)

            if len(timeline) < 2:
                print(f"⚠️ 选项 '{option['title']}' 时间线事件不足，跳过风险评估")
                final_score = 50.0
                risk_level = 0.5
                risk_assessment_dict = None
            else:
                final_score = self._calculate_final_score(timeline, profile)
                risk_level = self._calculate_risk_level(timeline)
                risk_obj = self.risk_engine.assess_option_risk(
                    option_title=option['title'],
                    timeline=[asdict(e) for e in timeline],
                    profile=profile
                )
                risk_assessment_dict = {
                    "overall_risk": risk_obj.overall_risk,
                    "overall_level": risk_obj.overall_level.value,
                    "high_risk_count": risk_obj.high_risk_count,
                    "dimensions": {
                        key: {
                            "name": dim.name,
                            "score": dim.score,
                            "level": dim.level.value,
                            "factors": dim.factors,
                            "mitigation": dim.mitigation
                        }
                        for key, dim in risk_obj.dimensions.items()
                    },
                    "recommendations": risk_obj.recommendations
                }

            simulated_options.append(DecisionOption(
                option_id=f"option_{i+1}",
                title=option['title'],
                description=option.get('description', ''),
                timeline=timeline,
                final_score=final_score,
                risk_level=risk_level,
                risk_assessment=risk_assessment_dict
            ))

        # 4. 生成个性化推荐（SGLang + LoRA）
        options_for_rec = [
            {
                "title": opt.title,
                "description": opt.description,
                "final_score": opt.final_score,
                "risk_level": opt.risk_level,
                "timeline_summary": self._summarize_timeline(opt.timeline)
            }
            for opt in simulated_options
        ]
        recommendation = await self.lora_analyzer.generate_personalized_recommendation(
            user_id=user_id,
            question=question,
            options=options_for_rec,
            profile=profile
        )

        # 5. 构造并保存结果
        simulation_id = f"sim_{user_id}_{int(datetime.now().timestamp())}"
        result = SimulationResult(
            simulation_id=simulation_id,
            user_id=user_id,
            question=question,
            options=simulated_options,
            recommendation=recommendation,
            created_at=datetime.now().isoformat()
        )
        self._save_simulation(result)
        return result

    # ==================== 分支生成 ====================

    def _generate_branch_events(
        self, main_timeline: List[TimelineEvent], branch_prefix: str
    ) -> List[TimelineEvent]:
        """
        从主时间线中选出高影响力节点，为其生成 1-2 个分支事件，
        形成思维导图式的拓扑结构。
        """
        branch_nodes: List[TimelineEvent] = []
        # 筛选影响力较大的节点作为分支点
        candidates = [
            e for e in main_timeline
            if sum(abs(v) for v in e.impact.values()) >= 0.3
        ]
        # 最多取 2 个分支点
        for parent in candidates[:2]:
            # 正面分支
            pos_impact = {k: round(v * 0.6, 2) for k, v in parent.impact.items()}
            branch_id = f"{branch_prefix}_fork_{parent.node_level}_pos"
            branch_nodes.append(TimelineEvent(
                event_id=branch_id,
                parent_event_id=parent.event_id,
                month=parent.month + 1,
                event=f"（乐观分支）{parent.event}进展顺利，带来额外机遇",
                impact=pos_impact,
                probability=round(parent.probability * 0.6, 2),
                event_type=parent.event_type,
                branch_group=f"{branch_prefix}_fork",
                node_level=parent.node_level + 1,
                risk_tag="low",
                opportunity_tag="high",
                visual_weight=0.4,
            ))
            # 负面分支
            neg_impact = {k: round(-abs(v) * 0.4, 2) for k, v in parent.impact.items()}
            neg_branch_id = f"{branch_prefix}_fork_{parent.node_level}_neg"
            branch_nodes.append(TimelineEvent(
                event_id=neg_branch_id,
                parent_event_id=parent.event_id,
                month=parent.month + 2,
                event=f"（风险分支）{parent.event}遇到阻碍，需要调整策略",
                impact=neg_impact,
                probability=round(parent.probability * 0.3, 2),
                event_type=parent.event_type,
                branch_group=f"{branch_prefix}_fork",
                node_level=parent.node_level + 1,
                risk_tag="high",
                opportunity_tag="low",
                visual_weight=0.35,
            ))
        return branch_nodes

    # ==================== 辅助计算 ====================

    def _summarize_timeline(self, timeline: List[TimelineEvent]) -> str:
        if not timeline:
            return "无关键事件"
        parts = [f"第{e.month}月：{e.event}" for e in timeline[:3]]
        return "；".join(parts)

    def _infer_event_type(self, event_text: str) -> str:
        text = event_text.lower()
        if any(k in text for k in ["工作", "职业", "入职", "实习", "公司", "面试"]):
            return "career"
        if any(k in text for k in ["学习", "考试", "课程", "培训", "技术"]):
            return "learning"
        if any(k in text for k in ["情绪", "焦虑", "压力", "自信", "心态"]):
            return "emotion"
        if any(k in text for k in ["社交", "朋友", "家人", "关系", "沟通"]):
            return "social"
        if any(k in text for k in ["收入", "财务", "花费", "存款", "薪资"]):
            return "finance"
        if any(k in text for k in ["健康", "睡眠", "身体", "运动"]):
            return "health"
        return "general"

    def _calculate_final_score(self, timeline: List[TimelineEvent], profile: Any) -> float:
        weights = {"健康": 1.0, "财务": 1.0, "社交": 1.0, "情绪": 1.0, "学习": 1.0, "时间": 1.0}
        if profile:
            prio = getattr(profile, 'life_priority', '')
            mapping = {
                "health_first": "健康", "wealth_first": "财务",
                "relationship_first": "社交", "career_first": "学习"
            }
            if prio in mapping:
                weights[mapping[prio]] = 1.5

        total = 0.0
        for event in timeline:
            for dim, impact in event.impact.items():
                w = weights.get(dim, 1.0)
                total += impact * w * event.probability
        return max(0, min(100, (total + 10) / 20 * 100))

    def _calculate_risk_level(self, timeline: List[TimelineEvent]) -> float:
        risk = 0.0
        for event in timeline:
            neg = sum(abs(v) for v in event.impact.values() if v < 0)
            risk += neg * (1 + (1 - event.probability))
        return max(0, min(1, risk / (len(timeline) * 5)))

    # ==================== 持久化 ====================

    def _save_simulation(self, result: SimulationResult):
        save_dir = "./data/simulations"
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"{result.simulation_id}.json")
        data = {
            "simulation_id": result.simulation_id,
            "user_id": result.user_id,
            "question": result.question,
            "options": [
                {
                    "option_id": opt.option_id,
                    "title": opt.title,
                    "description": opt.description,
                    "timeline": [asdict(e) for e in opt.timeline],
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "risk_assessment": opt.risk_assessment
                }
                for opt in result.options
            ],
            "recommendation": result.recommendation,
            "created_at": result.created_at
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_simulation(self, simulation_id: str) -> Optional[SimulationResult]:
        filepath = f"./data/simulations/{simulation_id}.json"
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        options = []
        for od in data['options']:
            timeline = [TimelineEvent(**ed) for ed in od['timeline']]
            options.append(DecisionOption(
                option_id=od['option_id'],
                title=od['title'],
                description=od['description'],
                timeline=timeline,
                final_score=od['final_score'],
                risk_level=od['risk_level'],
                risk_assessment=od.get('risk_assessment')
            ))
        return SimulationResult(
            simulation_id=data['simulation_id'],
            user_id=data['user_id'],
            question=data['question'],
            options=options,
            recommendation=data['recommendation'],
            created_at=data['created_at']
        )
