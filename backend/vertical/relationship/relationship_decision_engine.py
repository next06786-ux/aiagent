"""
人际关系决策引擎
基于关系网络和沟通策略
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.decision_algorithm.core_decision_engine import (
    CoreDecisionEngine,
    DecisionOption,
    DecisionDimension
)


class RelationshipType(Enum):
    """关系类型"""
    FAMILY = "family"  # 家人
    PARTNER = "partner"  # 伴侣
    FRIEND = "friend"  # 朋友
    COLLEAGUE = "colleague"  # 同事
    MENTOR = "mentor"  # 导师


class ConflictType(Enum):
    """冲突类型"""
    INTEREST = "interest"  # 利益冲突
    VALUE = "value"  # 价值观冲突
    EXPECTATION = "expectation"  # 期待差异
    COMMUNICATION = "communication"  # 沟通障碍


@dataclass
class Person:
    """人物信息"""
    name: str
    relationship_type: RelationshipType
    influence_weight: float  # 0-1，影响权重
    emotional_closeness: float  # 0-1，情感亲密度
    support_level: float  # 0-1，支持程度（-1到1，负数表示反对）
    key_concerns: List[str] = None  # 关键顾虑
    
    def __post_init__(self):
        if self.key_concerns is None:
            self.key_concerns = []


@dataclass
class RelationshipDecisionContext:
    """关系决策上下文"""
    decision_topic: str  # 决策主题
    key_people: List[Person] = None  # 关键人物
    current_conflicts: List[str] = None  # 当前冲突
    relationship_goals: List[str] = None  # 关系目标
    communication_history: Dict[str, Any] = None  # 沟通历史
    
    def __post_init__(self):
        if self.key_people is None:
            self.key_people = []
        if self.current_conflicts is None:
            self.current_conflicts = []
        if self.relationship_goals is None:
            self.relationship_goals = []
        if self.communication_history is None:
            self.communication_history = {}


class RelationshipDecisionEngine:
    """
    人际关系决策引擎
    
    核心功能：
    1. 关系网络建模
    2. 冲突分析
    3. 沟通策略建议
    4. 关系影响评估
    """
    
    def __init__(self):
        self.core_engine = CoreDecisionEngine()
    
    def analyze_relationship_network(
        self,
        context: RelationshipDecisionContext
    ) -> Dict[str, Any]:
        """
        分析关系网络
        
        Returns:
            关系网络分析结果
        """
        if not context.key_people:
            return {
                "total_influence": 0.0,
                "support_ratio": 0.0,
                "opposition_ratio": 0.0,
                "key_supporters": [],
                "key_opponents": [],
                "neutral_parties": []
            }
        
        # 计算总影响力
        total_influence = sum(p.influence_weight for p in context.key_people)
        
        # 分类人物
        supporters = [p for p in context.key_people if p.support_level > 0.3]
        opponents = [p for p in context.key_people if p.support_level < -0.3]
        neutral = [p for p in context.key_people if -0.3 <= p.support_level <= 0.3]
        
        # 计算支持/反对比例
        support_influence = sum(p.influence_weight * p.support_level for p in supporters)
        oppose_influence = sum(p.influence_weight * abs(p.support_level) for p in opponents)
        
        support_ratio = support_influence / total_influence if total_influence > 0 else 0.0
        opposition_ratio = oppose_influence / total_influence if total_influence > 0 else 0.0
        
        return {
            "total_influence": round(total_influence, 2),
            "support_ratio": round(support_ratio, 2),
            "opposition_ratio": round(opposition_ratio, 2),
            "key_supporters": [
                {
                    "name": p.name,
                    "type": p.relationship_type.value,
                    "influence": p.influence_weight,
                    "support": p.support_level
                }
                for p in sorted(supporters, key=lambda x: x.influence_weight, reverse=True)[:3]
            ],
            "key_opponents": [
                {
                    "name": p.name,
                    "type": p.relationship_type.value,
                    "influence": p.influence_weight,
                    "opposition": abs(p.support_level),
                    "concerns": p.key_concerns
                }
                for p in sorted(opponents, key=lambda x: x.influence_weight, reverse=True)[:3]
            ],
            "neutral_parties": [p.name for p in neutral]
        }
    
    def analyze_conflicts(
        self,
        context: RelationshipDecisionContext
    ) -> Dict[str, Any]:
        """
        分析冲突
        
        Returns:
            冲突分析结果
        """
        conflicts = []
        
        for person in context.key_people:
            if person.support_level < -0.3:
                # 识别冲突类型
                conflict_types = self._identify_conflict_types(person.key_concerns)
                
                conflicts.append({
                    "person": person.name,
                    "relationship": person.relationship_type.value,
                    "severity": abs(person.support_level),
                    "influence": person.influence_weight,
                    "conflict_types": conflict_types,
                    "concerns": person.key_concerns,
                    "priority": "high" if person.influence_weight > 0.7 else "medium"
                })
        
        # 按严重程度排序
        conflicts.sort(key=lambda x: x["severity"] * x["influence"], reverse=True)
        
        return {
            "conflict_count": len(conflicts),
            "high_priority_conflicts": [c for c in conflicts if c["priority"] == "high"],
            "all_conflicts": conflicts,
            "most_common_type": self._get_most_common_conflict_type(conflicts)
        }
    
    def _identify_conflict_types(self, concerns: List[str]) -> List[str]:
        """识别冲突类型"""
        types = []
        concern_text = " ".join(concerns).lower()
        
        if any(word in concern_text for word in ["钱", "收入", "财务", "经济"]):
            types.append("interest")
        if any(word in concern_text for word in ["价值观", "理念", "信念"]):
            types.append("value")
        if any(word in concern_text for word in ["期待", "希望", "要求"]):
            types.append("expectation")
        if any(word in concern_text for word in ["沟通", "理解", "误会"]):
            types.append("communication")
        
        return types if types else ["general"]
    
    def _get_most_common_conflict_type(self, conflicts: List[Dict]) -> str:
        """获取最常见的冲突类型"""
        if not conflicts:
            return "none"
        
        type_counts = {}
        for conflict in conflicts:
            for ctype in conflict["conflict_types"]:
                type_counts[ctype] = type_counts.get(ctype, 0) + 1
        
        return max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "general"
    
    def generate_communication_strategy(
        self,
        person: Person,
        decision_topic: str,
        conflict_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成沟通策略
        
        Returns:
            沟通策略建议
        """
        # 找到该人物的冲突信息
        person_conflict = None
        for conflict in conflict_analysis.get("all_conflicts", []):
            if conflict["person"] == person.name:
                person_conflict = conflict
                break
        
        if not person_conflict:
            return {
                "approach": "维持沟通",
                "key_points": ["保持现有关系", "定期联系"],
                "timing": "随时",
                "tone": "轻松友好"
            }
        
        # 根据关系类型和冲突类型生成策略
        approach = self._determine_approach(person.relationship_type, person_conflict["conflict_types"])
        key_points = self._generate_key_points(person, person_conflict)
        timing = self._suggest_timing(person.relationship_type, person_conflict["severity"])
        tone = self._suggest_tone(person.relationship_type, person.emotional_closeness)
        
        return {
            "person": person.name,
            "relationship": person.relationship_type.value,
            "approach": approach,
            "key_points": key_points,
            "timing": timing,
            "tone": tone,
            "concerns_to_address": person.key_concerns,
            "expected_outcome": self._predict_outcome(person, approach)
        }
    
    def _determine_approach(self, rel_type: RelationshipType, conflict_types: List[str]) -> str:
        """确定沟通方式"""
        if rel_type == RelationshipType.FAMILY:
            return "情感优先，强调家庭纽带"
        elif rel_type == RelationshipType.PARTNER:
            return "平等对话，寻求共识"
        elif rel_type == RelationshipType.MENTOR:
            return "虚心请教，展示思考"
        elif "interest" in conflict_types:
            return "理性分析，展示双赢"
        else:
            return "坦诚沟通，理解立场"
    
    def _generate_key_points(self, person: Person, conflict: Dict) -> List[str]:
        """生成沟通要点"""
        points = []
        
        # 基于关系类型
        if person.relationship_type == RelationshipType.FAMILY:
            points.append("强调这个决定对家庭长期发展的好处")
        elif person.relationship_type == RelationshipType.PARTNER:
            points.append("说明这个决定如何考虑了双方的需求")
        
        # 基于顾虑
        for concern in person.key_concerns[:2]:
            points.append(f"针对'{concern}'的顾虑，说明应对方案")
        
        # 基于冲突类型
        if "interest" in conflict["conflict_types"]:
            points.append("展示利益分配的公平性")
        if "value" in conflict["conflict_types"]:
            points.append("寻找价值观的共同点")
        
        return points
    
    def _suggest_timing(self, rel_type: RelationshipType, severity: float) -> str:
        """建议沟通时机"""
        if severity > 0.7:
            return "尽快沟通，不宜拖延"
        elif rel_type in [RelationshipType.FAMILY, RelationshipType.PARTNER]:
            return "选择双方都放松的时间，如周末晚餐后"
        else:
            return "选择对方方便的时间，提前预约"
    
    def _suggest_tone(self, rel_type: RelationshipType, closeness: float) -> str:
        """建议沟通语气"""
        if closeness > 0.7:
            return "亲密温和"
        elif rel_type == RelationshipType.MENTOR:
            return "尊重谦逊"
        else:
            return "真诚友好"
    
    def _predict_outcome(self, person: Person, approach: str) -> str:
        """预测沟通结果"""
        if person.emotional_closeness > 0.7:
            return "预期能够达成理解，即使不完全同意"
        elif person.support_level < -0.6:
            return "预期仍会有分歧，但能减少对立"
        else:
            return "预期能够改善关系，增加支持"
    
    def create_relationship_decision_option(
        self,
        option_id: str,
        title: str,
        description: str,
        context: RelationshipDecisionContext,
        expected_relationship_changes: Dict[str, float]  # 预期关系变化
    ) -> DecisionOption:
        """
        创建关系决策选项
        
        Returns:
            决策选项对象
        """
        # 分析关系网络
        network_analysis = self.analyze_relationship_network(context)
        
        # 分析冲突
        conflict_analysis = self.analyze_conflicts(context)
        
        # 计算可行性（基于支持度）
        feasibility_score = (network_analysis["support_ratio"] + 1 - network_analysis["opposition_ratio"]) / 2
        
        # 计算收益（关系改善程度）
        relationship_benefit = sum(expected_relationship_changes.values()) / len(expected_relationship_changes) if expected_relationship_changes else 0.5
        benefit_score = (relationship_benefit + 1) / 2  # 归一化到0-1
        
        # 计算风险（冲突严重程度）
        conflict_risk = conflict_analysis["conflict_count"] * 0.1
        risk_score = min(1.0, conflict_risk + network_analysis["opposition_ratio"])
        
        # 计算可逆性（关系修复难度）
        high_priority_conflicts = len(conflict_analysis["high_priority_conflicts"])
        reversibility_score = 1.0 - (high_priority_conflicts * 0.2)
        
        # 创建决策选项
        option = DecisionOption(
            id=option_id,
            title=title,
            description=description,
            feasibility_score=feasibility_score,
            benefit_score=benefit_score,
            risk_score=risk_score,
            reversibility_score=max(0.0, reversibility_score),
            alignment_score=0.7,  # 需要用户目标信息
            resource_score=0.8,  # 关系决策通常资源需求较低
            evidence={
                "network_analysis": network_analysis,
                "conflict_analysis": conflict_analysis,
                "expected_changes": expected_relationship_changes
            },
            assumptions=[
                "假设沟通策略得到有效执行",
                "假设关键人物愿意倾听",
                "假设没有突发的外部事件影响关系"
            ]
        )
        
        return option


# 示例使用
if __name__ == "__main__":
    engine = RelationshipDecisionEngine()
    
    # 创建关系决策上下文
    context = RelationshipDecisionContext(
        decision_topic="是否接受外地工作机会",
        key_people=[
            Person(
                name="父母",
                relationship_type=RelationshipType.FAMILY,
                influence_weight=0.8,
                emotional_closeness=0.9,
                support_level=-0.6,
                key_concerns=["离家太远", "担心安全", "希望常回家"]
            ),
            Person(
                name="女友",
                relationship_type=RelationshipType.PARTNER,
                influence_weight=0.9,
                emotional_closeness=0.85,
                support_level=0.4,
                key_concerns=["异地恋", "未来规划"]
            ),
            Person(
                name="导师",
                relationship_type=RelationshipType.MENTOR,
                influence_weight=0.6,
                emotional_closeness=0.7,
                support_level=0.8,
                key_concerns=[]
            )
        ]
    )
    
    # 分析关系网络
    network = engine.analyze_relationship_network(context)
    print("=" * 60)
    print("关系网络分析")
    print("=" * 60)
    print(f"支持比例: {network['support_ratio']}")
    print(f"反对比例: {network['opposition_ratio']}")
    print(f"关键支持者: {[s['name'] for s in network['key_supporters']]}")
    print(f"关键反对者: {[o['name'] for o in network['key_opponents']]}")
    
    # 分析冲突
    conflicts = engine.analyze_conflicts(context)
    print(f"\n冲突数量: {conflicts['conflict_count']}")
    print(f"高优先级冲突: {len(conflicts['high_priority_conflicts'])}")
    
    # 生成沟通策略
    for person in context.key_people:
        if person.support_level < -0.3:
            strategy = engine.generate_communication_strategy(person, context.decision_topic, conflicts)
            print(f"\n{person.name}的沟通策略:")
            print(f"  方式: {strategy['approach']}")
            print(f"  时机: {strategy['timing']}")
            print(f"  语气: {strategy['tone']}")
