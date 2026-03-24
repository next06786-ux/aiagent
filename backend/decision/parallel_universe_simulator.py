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
    """时间线事件"""
    month: int
    event: str
    impact: Dict[str, float]
    probability: float


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
                num_events=3
            )
            timelines.append(timeline_data)

        # 3. 本地计算得分和风险
        simulated_options = []
        for i, (option, timeline_data) in enumerate(zip(options, timelines)):
            timeline = [
                TimelineEvent(
                    month=e['month'],
                    event=e['event'],
                    impact=e['impact'],
                    probability=e['probability']
                )
                for e in timeline_data
            ]

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

    # ==================== 辅助计算 ====================

    def _summarize_timeline(self, timeline: List[TimelineEvent]) -> str:
        if not timeline:
            return "无关键事件"
        parts = [f"第{e.month}月：{e.event}" for e in timeline[:3]]
        return "；".join(parts)

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
