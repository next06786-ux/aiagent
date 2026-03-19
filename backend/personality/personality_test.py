"""
心理测评系统
构建用户性格基座
"""
import json
import os
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class PersonalityProfile:
    """用户性格画像"""
    user_id: str
    
    # 大五人格得分 (1-4)
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    
    # 决策风格
    decision_style: str  # rational/intuitive/balanced
    decision_speed: float  # 1-4
    consultation_tendency: float  # 1-4
    regret_tendency: float  # 1-4
    information_seeking: float  # 1-4
    
    # 风险偏好
    risk_preference: str  # risk_averse/risk_neutral/risk_seeking
    financial_risk: float  # 1-4
    career_risk: float  # 1-4
    relationship_risk: float  # 1-4
    change_tolerance: float  # 1-4
    failure_tolerance: float  # 1-4
    
    # 生活优先级
    life_priority: str  # health_first/career_first/relationship_first/freedom_first/wealth_first/balanced
    health_priority: float  # 1-4
    career_priority: float  # 1-4
    relationship_priority: float  # 1-4
    freedom_priority: float  # 1-4
    wealth_priority: float  # 1-4
    
    # 元数据
    test_date: str
    test_version: str = "1.0"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def get_summary(self) -> Dict[str, str]:
        """获取画像摘要"""
        return {
            "personality_type": self._get_personality_type(),
            "decision_style": self.decision_style,
            "risk_preference": self.risk_preference,
            "life_priority": self.life_priority,
            "description": self._get_description()
        }
    
    def _get_personality_type(self) -> str:
        """获取性格类型描述"""
        traits = []
        
        if self.openness >= 3:
            traits.append("开放创新")
        if self.conscientiousness >= 3:
            traits.append("严谨自律")
        if self.extraversion >= 3:
            traits.append("外向活跃")
        if self.agreeableness >= 3:
            traits.append("温和友善")
        if self.neuroticism <= 2:
            traits.append("情绪稳定")
        
        return "、".join(traits) if traits else "平衡型"
    
    def _get_description(self) -> str:
        """生成个性化描述"""
        desc_parts = []
        
        # 性格描述
        if self.openness >= 3:
            desc_parts.append("你对新事物充满好奇，喜欢探索和创新")
        else:
            desc_parts.append("你更倾向于稳定和传统的方式")
        
        # 决策风格描述
        if self.decision_style == "rational":
            desc_parts.append("做决定时依赖理性分析和数据")
        elif self.decision_style == "intuitive":
            desc_parts.append("做决定时更相信直觉和感觉")
        else:
            desc_parts.append("做决定时会综合理性和直觉")
        
        # 风险偏好描述
        if self.risk_preference == "risk_seeking":
            desc_parts.append("愿意承担风险以追求更大回报")
        elif self.risk_preference == "risk_averse":
            desc_parts.append("倾向于规避风险，追求稳定")
        else:
            desc_parts.append("对风险持中性态度")
        
        return "。".join(desc_parts) + "。"


class PersonalityTest:
    """心理测评系统"""
    
    def __init__(self):
        self.questions_file = os.path.join(
            os.path.dirname(__file__),
            "questions.json"
        )
        self.questions_data = self._load_questions()
    
    def _load_questions(self) -> Dict:
        """加载题目"""
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_questions(self) -> Dict:
        """获取所有题目"""
        return {
            "test_info": self.questions_data["test_info"],
            "questions": self.questions_data["questions"]
        }
    
    def calculate_profile(self, user_id: str, answers: Dict[int, int]) -> PersonalityProfile:
        """
        计算性格画像
        
        Args:
            user_id: 用户ID
            answers: {question_id: selected_value}
        
        Returns:
            PersonalityProfile
        """
        # 按维度分组答案
        dimension_scores = {
            "openness": [],
            "conscientiousness": [],
            "extraversion": [],
            "agreeableness": [],
            "neuroticism": [],
            "rational_vs_intuitive": [],
            "speed": [],
            "consultation": [],
            "regret_tendency": [],
            "information_seeking": [],
            "financial": [],
            "career": [],
            "relationship": [],
            "change": [],
            "failure_tolerance": [],
            "health": [],
            "career_priority": [],
            "relationship_priority": [],
            "freedom": [],
            "wealth": []
        }
        
        # 收集各维度得分
        for question in self.questions_data["questions"]:
            q_id = question["id"]
            if q_id in answers:
                subdim = question["subdimension"]
                value = answers[q_id]
                dimension_scores[subdim].append(value)
        
        # 计算平均分
        def avg(scores): return sum(scores) / len(scores) if scores else 2.5
        
        # 大五人格
        openness = avg(dimension_scores["openness"])
        conscientiousness = avg(dimension_scores["conscientiousness"])
        extraversion = avg(dimension_scores["extraversion"])
        agreeableness = avg(dimension_scores["agreeableness"])
        neuroticism = avg(dimension_scores["neuroticism"])
        
        # 决策风格
        rational_score = avg(dimension_scores["rational_vs_intuitive"])
        decision_style = self._classify_decision_style(rational_score)
        decision_speed = avg(dimension_scores["speed"])
        consultation = avg(dimension_scores["consultation"])
        regret = avg(dimension_scores["regret_tendency"])
        info_seeking = avg(dimension_scores["information_seeking"])
        
        # 风险偏好
        financial_risk = avg(dimension_scores["financial"])
        career_risk = avg(dimension_scores["career"])
        relationship_risk = avg(dimension_scores["relationship"])
        change_tolerance = avg(dimension_scores["change"])
        failure_tolerance = avg(dimension_scores["failure_tolerance"])
        
        overall_risk = (financial_risk + career_risk + relationship_risk + 
                       change_tolerance + failure_tolerance) / 5
        risk_preference = self._classify_risk_preference(overall_risk)
        
        # 生活优先级
        health_priority = avg(dimension_scores["health"])
        career_priority = avg(dimension_scores["career_priority"])
        relationship_priority = avg(dimension_scores["relationship_priority"])
        freedom_priority = avg(dimension_scores["freedom"])
        wealth_priority = avg(dimension_scores["wealth"])
        
        life_priority = self._classify_life_priority({
            "health": health_priority,
            "career": career_priority,
            "relationship": relationship_priority,
            "freedom": freedom_priority,
            "wealth": wealth_priority
        })
        
        # 构建画像
        profile = PersonalityProfile(
            user_id=user_id,
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism,
            decision_style=decision_style,
            decision_speed=decision_speed,
            consultation_tendency=consultation,
            regret_tendency=regret,
            information_seeking=info_seeking,
            risk_preference=risk_preference,
            financial_risk=financial_risk,
            career_risk=career_risk,
            relationship_risk=relationship_risk,
            change_tolerance=change_tolerance,
            failure_tolerance=failure_tolerance,
            life_priority=life_priority,
            health_priority=health_priority,
            career_priority=career_priority,
            relationship_priority=relationship_priority,
            freedom_priority=freedom_priority,
            wealth_priority=wealth_priority,
            test_date=datetime.now().isoformat()
        )
        
        return profile
    
    def _classify_decision_style(self, score: float) -> str:
        """分类决策风格"""
        if score <= 2.0:
            return "intuitive"
        elif score >= 3.0:
            return "rational"
        else:
            return "balanced"
    
    def _classify_risk_preference(self, score: float) -> str:
        """分类风险偏好"""
        if score <= 2.0:
            return "risk_averse"
        elif score >= 3.0:
            return "risk_seeking"
        else:
            return "risk_neutral"
    
    def _classify_life_priority(self, priorities: Dict[str, float]) -> str:
        """分类生活优先级"""
        # 找到最高分
        max_priority = max(priorities.items(), key=lambda x: x[1])
        
        # 检查是否平衡（所有分数都接近）
        values = list(priorities.values())
        if max(values) - min(values) <= 1.0:
            return "balanced"
        
        # 返回最高优先级
        priority_map = {
            "health": "health_first",
            "career": "career_first",
            "relationship": "relationship_first",
            "freedom": "freedom_first",
            "wealth": "wealth_first"
        }
        
        return priority_map.get(max_priority[0], "balanced")
    
    def save_profile(self, profile: PersonalityProfile):
        """保存画像到文件"""
        profiles_dir = "./data/personality_profiles"
        os.makedirs(profiles_dir, exist_ok=True)
        
        filepath = os.path.join(profiles_dir, f"{profile.user_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_profile(self, user_id: str) -> PersonalityProfile:
        """加载用户画像"""
        filepath = f"./data/personality_profiles/{user_id}.json"
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PersonalityProfile(**data)


# 测试代码
if __name__ == "__main__":
    test = PersonalityTest()
    
    # 模拟答案
    answers = {i: 3 for i in range(1, 21)}  # 所有题都选3
    
    profile = test.calculate_profile("test_user", answers)
    print("性格画像:")
    print(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2))
    print("\n摘要:")
    print(json.dumps(profile.get_summary(), ensure_ascii=False, indent=2))
    
    # 保存
    test.save_profile(profile)
    print("\n✅ 画像已保存")
