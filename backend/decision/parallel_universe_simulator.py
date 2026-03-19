"""
平行宇宙模拟器
模拟不同决策选项的未来时间线
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.digital_twin.digital_twin import DigitalTwin
from backend.personality.personality_test import PersonalityTest
from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
from backend.decision.risk_assessment_engine import RiskAssessmentEngine


@dataclass
class TimelineEvent:
    """时间线事件"""
    month: int  # 第几个月
    event: str  # 事件描述
    impact: Dict[str, float]  # 影响（健康/财务/社交/情绪/学习/时间）
    probability: float  # 发生概率


@dataclass
class DecisionOption:
    """决策选项"""
    option_id: str
    title: str
    description: str
    timeline: List[TimelineEvent]
    final_score: float  # 综合得分
    risk_level: float  # 风险等级 0-1
    risk_assessment: Optional[Dict] = None  # 详细风险评估


@dataclass
class SimulationResult:
    """模拟结果"""
    simulation_id: str
    user_id: str
    question: str
    options: List[DecisionOption]
    recommendation: str  # AI推荐
    created_at: str


class ParallelUniverseSimulator:
    """平行宇宙模拟器"""
    
    def __init__(self):
        self.personality_test = PersonalityTest()
        self.simulation_months = 12  # 模拟12个月
        self.lora_analyzer = LoRADecisionAnalyzer()  # LoRA分析器
        self.risk_engine = RiskAssessmentEngine()  # 风险评估引擎
    
    def simulate_decision(
        self,
        user_id: str,
        question: str,
        options: List[Dict[str, str]],
        use_lora: bool = False
    ) -> SimulationResult:
        """
        模拟决策
        
        Args:
            user_id: 用户ID
            question: 决策问题
            options: 选项列表 [{"title": "选项A", "description": "..."}]
            use_lora: 是否使用LoRA模型
        
        Returns:
            SimulationResult
        """
        # 1. 加载用户性格画像
        profile = self.personality_test.load_profile(user_id)
        
        # 2. 为每个选项创建数字孪生并模拟
        simulated_options = []
        
        for i, option in enumerate(options):
            option_id = f"option_{i+1}"
            
            print(f"\n{'='*60}")
            print(f"🔄 处理选项 {i+1}/{len(options)}: {option['title']}")
            print(f"{'='*60}")
            
            # 清理GPU缓存（在处理每个选项前）
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print(f"💾 GPU内存: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
            
            # 创建初始状态（基于用户当前状态）
            initial_state = {
                "health": 75.0,
                "finance": 70.0,
                "social": 65.0,
                "emotion": 70.0,
                "learning": 60.0,
                "time_management": 65.0
            }
            
            # 创建数字孪生
            twin = DigitalTwin(user_id, initial_state)
            
            # 模拟时间线
            timeline = self._simulate_timeline(
                twin=twin,
                profile=profile,
                option=option,
                question=question,
                use_lora=use_lora
            )
            
            # 清理GPU缓存（生成后立即清理）
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 计算综合得分和风险
            final_score = self._calculate_final_score(timeline, profile)
            risk_level = self._calculate_risk_level(timeline)
            
            # 详细风险评估
            risk_assessment_obj = self.risk_engine.assess_option_risk(
                option_title=option['title'],
                timeline=[asdict(event) for event in timeline],
                profile=profile
            )
            
            # 转换为可序列化格式
            risk_assessment_dict = {
                "overall_risk": risk_assessment_obj.overall_risk,
                "overall_level": risk_assessment_obj.overall_level.value,
                "high_risk_count": risk_assessment_obj.high_risk_count,
                "dimensions": {
                    key: {
                        "name": dim.name,
                        "score": dim.score,
                        "level": dim.level.value,
                        "factors": dim.factors,
                        "mitigation": dim.mitigation
                    }
                    for key, dim in risk_assessment_obj.dimensions.items()
                },
                "recommendations": risk_assessment_obj.recommendations
            }
            
            simulated_options.append(DecisionOption(
                option_id=option_id,
                title=option['title'],
                description=option.get('description', ''),
                timeline=timeline,
                final_score=final_score,
                risk_level=risk_level,
                risk_assessment=risk_assessment_dict
            ))
        
        # 3. 生成推荐（必须使用LoRA）
        if not use_lora:
            raise ValueError("决策推荐必须启用LoRA模型 (use_lora=True)")
        
        if not self.lora_analyzer.lora_manager.has_lora_model(user_id):
            raise ValueError(f"用户 {user_id} 还没有训练LoRA模型，无法进行个性化决策模拟")
        
        # 准备选项数据供LoRA分析
        options_for_lora = [
            {
                "title": opt.title,
                "description": opt.description,
                "final_score": opt.final_score,
                "risk_level": opt.risk_level,
                "timeline_summary": self._summarize_timeline(opt.timeline)
            }
            for opt in simulated_options
        ]
        
        recommendation = self.lora_analyzer.generate_personalized_recommendation(
            user_id=user_id,
            question=question,
            options=options_for_lora,
            profile=profile,
            use_lora=True
        )
        
        # 4. 创建结果
        simulation_id = f"sim_{user_id}_{int(datetime.now().timestamp())}"
        
        result = SimulationResult(
            simulation_id=simulation_id,
            user_id=user_id,
            question=question,
            options=simulated_options,
            recommendation=recommendation,
            created_at=datetime.now().isoformat()
        )
        
        # 5. 保存结果
        self._save_simulation(result)
        
        return result
    
    def _simulate_timeline(
        self,
        twin: DigitalTwin,
        profile: Any,
        option: Dict[str, str],
        question: str,
        use_lora: bool
    ) -> List[TimelineEvent]:
        """
        使用本地模型+LoRA模拟12个月的时间线
        
        必须使用LoRA模型，如果用户没有LoRA模型会抛出异常
        """
        if not use_lora:
            raise ValueError("决策模拟必须启用LoRA模型 (use_lora=True)")
        
        if not self.lora_analyzer.lora_manager.has_lora_model(twin.user_id):
            raise ValueError(f"用户 {twin.user_id} 还没有训练LoRA模型，无法进行个性化决策模拟")
        
        # 使用LoRA模型生成个性化时间线
        timeline = self._simulate_timeline_with_lora(
            user_id=twin.user_id,
            option=option,
            question=question,
            profile=profile
        )
        
        return timeline
    
    def _simulate_timeline_with_lora(
        self,
        user_id: str,
        option: Dict[str, str],
        question: str,
        profile: Any
    ) -> List[TimelineEvent]:
        """
        使用本地模型Qwen3.5-0.8B + LoRA生成个性化时间线
        """
        # 使用LoRADecisionAnalyzer生成时间线
        timeline_data = self.lora_analyzer.generate_timeline_with_lora(
            user_id=user_id,
            question=question,
            option=option,
            profile=profile,
            num_events=3  # 减少到3个事件，节省内存
        )
        
        # 转换为TimelineEvent对象
        timeline = []
        for event_data in timeline_data:
            timeline.append(TimelineEvent(
                month=event_data['month'],
                event=event_data['event'],
                impact=event_data['impact'],
                probability=event_data['probability']
            ))
        
        # 验证生成的事件数量
        if len(timeline) < 2:
            raise ValueError(f"LoRA生成的事件太少（{len(timeline)}个），无法进行有效的决策模拟")
        
        print(f"✅ 使用LoRA成功生成 {len(timeline)} 个个性化事件")
        return timeline
    
    def _summarize_timeline(self, timeline: List[TimelineEvent]) -> str:
        """总结时间线的关键信息"""
        if not timeline:
            return "无关键事件"
        
        summary_parts = []
        for event in timeline[:3]:  # 只取前3个关键事件
            summary_parts.append(f"第{event.month}月：{event.event}")
        
        return "；".join(summary_parts)
    
    def _calculate_final_score(self, timeline: List[TimelineEvent], profile: Any) -> float:
        """计算综合得分"""
        total_score = 0.0
        
        # 根据用户的生活优先级加权
        weights = {
            "健康": 1.0,
            "财务": 1.0,
            "社交": 1.0,
            "情绪": 1.0,
            "学习": 1.0,
            "时间": 1.0
        }
        
        if profile:
            # 根据用户优先级调整权重
            if profile.life_priority == "health_first":
                weights["健康"] = 1.5
            elif profile.life_priority == "wealth_first":
                weights["财务"] = 1.5
            elif profile.life_priority == "relationship_first":
                weights["社交"] = 1.5
            elif profile.life_priority == "career_first":
                weights["学习"] = 1.5
        
        # 计算加权平均
        for event in timeline:
            for dimension, impact in event.impact.items():
                weight = weights.get(dimension, 1.0)
                total_score += impact * weight * event.probability
        
        # 归一化到0-100
        normalized_score = (total_score + 10) / 20 * 100
        return max(0, min(100, normalized_score))
    
    def _calculate_risk_level(self, timeline: List[TimelineEvent]) -> float:
        """计算风险等级"""
        risk_score = 0.0
        
        for event in timeline:
            # 负面影响越大，风险越高
            negative_impact = sum(
                abs(impact) for impact in event.impact.values() if impact < 0
            )
            # 概率越低，风险越高
            uncertainty = 1 - event.probability
            
            risk_score += negative_impact * (1 + uncertainty)
        
        # 归一化到0-1
        normalized_risk = risk_score / (len(timeline) * 5)
        return max(0, min(1, normalized_risk))
    
    def _save_simulation(self, result: SimulationResult):
        """保存模拟结果"""
        save_dir = "./data/simulations"
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = os.path.join(save_dir, f"{result.simulation_id}.json")
        
        # 转换为可序列化的格式
        data = {
            "simulation_id": result.simulation_id,
            "user_id": result.user_id,
            "question": result.question,
            "options": [
                {
                    "option_id": opt.option_id,
                    "title": opt.title,
                    "description": opt.description,
                    "timeline": [
                        {
                            "month": event.month,
                            "event": event.event,
                            "impact": event.impact,
                            "probability": event.probability
                        }
                        for event in opt.timeline
                    ],
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level
                }
                for opt in result.options
            ],
            "recommendation": result.recommendation,
            "created_at": result.created_at
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_simulation(self, simulation_id: str) -> Optional[SimulationResult]:
        """加载模拟结果"""
        filepath = f"./data/simulations/{simulation_id}.json"
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重建对象
        options = []
        for opt_data in data['options']:
            timeline = [
                TimelineEvent(**event_data)
                for event_data in opt_data['timeline']
            ]
            options.append(DecisionOption(
                option_id=opt_data['option_id'],
                title=opt_data['title'],
                description=opt_data['description'],
                timeline=timeline,
                final_score=opt_data['final_score'],
                risk_level=opt_data['risk_level']
            ))
        
        return SimulationResult(
            simulation_id=data['simulation_id'],
            user_id=data['user_id'],
            question=data['question'],
            options=options,
            recommendation=data['recommendation'],
            created_at=data['created_at']
        )


# 测试代码
if __name__ == "__main__":
    simulator = ParallelUniverseSimulator()
    
    # 模拟决策
    result = simulator.simulate_decision(
        user_id="test_user_001",
        question="大三学生，毕业后应该选择什么？",
        options=[
            {"title": "考研", "description": "继续深造，提升学历"},
            {"title": "工作", "description": "直接就业，积累经验"},
            {"title": "创业", "description": "自主创业，追求梦想"}
        ]
    )
    
    print("="*60)
    print("平行宇宙模拟结果")
    print("="*60)
    print(f"\n问题: {result.question}\n")
    
    for option in result.options:
        print(f"\n选项: {option.title}")
        print(f"综合得分: {option.final_score:.1f}")
        print(f"风险等级: {option.risk_level:.2f}")
        print(f"\n时间线:")
        for event in option.timeline:
            print(f"  第{event.month}月: {event.event}")
            print(f"    影响: {event.impact}")
            print(f"    概率: {event.probability:.0%}")
    
    print(f"\n推荐:\n{result.recommendation}")
