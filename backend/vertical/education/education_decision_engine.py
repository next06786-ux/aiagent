"""
教育升学决策引擎
基于学业竞争力、录取概率、申请策略的决策系统
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


class EducationLevel(Enum):
    """教育水平"""
    HIGH_SCHOOL = "high_school"          # 高中
    BACHELOR = "bachelor"                # 本科
    MASTER = "master"                   # 硕士
    DOCTOR = "doctor"                  # 博士
    PROFESSIONAL = "professional"       # 职业资格


class SchoolType(Enum):
    """学校类型"""
    TOP = "top"                         # 顶尖（清北/华五/常青藤）
    ELITE = "elite"                     # 精英（985/211/知名海外）
    STANDARD = "standard"              # 普通（一本/普通院校）
    LOCAL = "local"                     # 地方/专科


@dataclass
class AcademicProfile:
    """学业档案"""
    current_gpa: float                   # 当前GPA
    ranking_percent: float               # 排名百分比
    test_scores: Dict[str, float]       # 标准化考试成绩
    research_experience: float          # 科研经历 0-1
    publications: int                   # 发表论文数
    awards: List[str]                   # 获奖经历
    extracurricular: List[str]           # 课外活动


@dataclass
class TargetSchool:
    """目标学校"""
    name: str
    school_type: SchoolType
    location: str
    tuition_annual: float               # 年学费
    acceptance_rate: float              # 录取率
    avg_gpa_accepted: float             # 录取平均GPA
    employment_rate: float              # 就业率
    avg_salary: float                   # 毕业后平均薪资


@dataclass
class EducationDecisionContext:
    """教育决策上下文"""
    decision_topic: str                 # 决策主题
    current_level: EducationLevel       # 当前学历
    target_level: EducationLevel        # 目标学历
    academic_profile: AcademicProfile    # 学业档案
    target_schools: List[TargetSchool]  # 目标学校列表
    budget: float                       # 预算
    preferences: Dict[str, Any]         # 偏好设置


class EducationDecisionEngine:
    """
    教育升学决策引擎
    
    核心功能：
    1. 学业竞争力评估
    2. 录取概率计算
    3. 学校对比分析
    4. 申请策略建议
    """
    
    def __init__(self):
        self.core_engine = CoreDecisionEngine()
    
    def evaluate_academic_competitiveness(
        self,
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        评估学业竞争力
        
        Returns:
            竞争力评估结果
        """
        profile = context.academic_profile
        
        # GPA得分
        gpa_score = profile.current_gpa / 4.0
        
        # 排名得分
        ranking_score = 1.0 - profile.ranking_percent
        
        # 标化成绩得分
        test_scores = list(profile.test_scores.values())
        test_score = sum(test_scores) / len(test_scores) / 1600 if test_scores else 0.5  # 假设满分1600
        
        # 软实力得分
        soft_power = (
            profile.research_experience * 0.4 +
            min(1.0, profile.publications / 5) * 0.3 +
            min(1.0, len(profile.awards) / 10) * 0.15 +
            min(1.0, len(profile.extracurricular) / 5) * 0.15
        )
        
        # 综合竞争力
        total_score = (
            gpa_score * 0.35 +
            ranking_score * 0.25 +
            test_score * 0.20 +
            soft_power * 0.20
        ) * 100
        
        return {
            "total_score": round(total_score, 1),
            "breakdown": {
                "gpa": round(gpa_score * 100, 1),
                "ranking": round(ranking_score * 100, 1),
                "test": round(test_score * 100, 1),
                "soft_power": round(soft_power * 100, 1)
            },
            "percentile": self._calculate_percentile(total_score),
            "recommendations": self._generate_competitiveness_recommendations(
                gpa_score, test_score, soft_power
            )
        }
    
    def _calculate_percentile(self, score: float) -> int:
        """计算百分位"""
        if score >= 90:
            return 95
        elif score >= 80:
            return 85
        elif score >= 70:
            return 70
        elif score >= 60:
            return 50
        else:
            return 30
    
    def _generate_competitiveness_recommendations(
        self,
        gpa: float,
        test: float,
        soft: float
    ) -> List[str]:
        """生成竞争力提升建议"""
        recommendations = []
        
        if gpa < 0.85:
            recommendations.append("提高GPA至3.7以上以提升竞争力")
        if test < 0.8:
            recommendations.append("加强标准化考试准备")
        if soft < 0.7:
            recommendations.append("增加科研或竞赛经历")
        
        if not recommendations:
            recommendations.append("学业背景良好，可专注申请策略")
        
        return recommendations
    
    def calculate_admission_probability(
        self,
        school: TargetSchool,
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        计算录取概率
        
        Returns:
            录取概率分析
        """
        profile = context.academic_profile
        
        # GPA匹配度
        gpa_match = profile.current_gpa / school.avg_gpa_accepted if school.avg_gpa_accepted > 0 else 0.8
        
        # 排名优势
        ranking_advantage = 1.0 - (profile.ranking_percent * 0.5)
        
        # 综合得分
        competitiveness = self.evaluate_academic_competitiveness(context)
        
        # 计算概率
        base_prob = school.acceptance_rate
        
        # 调整因子
        if gpa_match >= 1.0:
            adjustment = 1.3
        elif gpa_match >= 0.9:
            adjustment = 1.1
        elif gpa_match >= 0.8:
            adjustment = 0.9
        else:
            adjustment = 0.7
        
        # 考虑竞争激烈程度
        if school.acceptance_rate < 0.1:
            adjustment *= 0.8
        
        probability = min(0.95, base_prob * adjustment * (competitiveness['total_score'] / 100))
        
        # 风险评估
        if probability >= 0.7:
            risk_level = "low"
            assessment = "高概率录取"
        elif probability >= 0.4:
            risk_level = "medium"
            assessment = "有挑战但有机会"
        else:
            risk_level = "high"
            assessment = "需要谨慎考虑"
        
        return {
            "probability": round(probability, 3),
            "risk_level": risk_level,
            "assessment": assessment,
            "gpa_match": round(gpa_match, 2),
            "recommendation": self._get_admission_recommendation(probability, school)
        }
    
    def _get_admission_recommendation(self, prob: float, school: TargetSchool) -> str:
        """获取录取建议"""
        if prob >= 0.7:
            return f"建议申请{school.name}，录取概率较高"
        elif prob >= 0.4:
            return f"建议申请{school.name}，需要提升申请材料"
        else:
            return f"{school.name}为冲刺项目，建议同时申请保底学校"
    
    def compare_schools(
        self,
        schools: List[TargetSchool],
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        学校对比分析
        
        Returns:
            学校对比结果
        """
        if not schools:
            return {"comparisons": [], "ranking": []}
        
        comparisons = []
        rankings = []
        
        for school in schools:
            # 录取概率
            admission = self.calculate_admission_probability(school, context)
            
            # 计算综合评分
            cost_score = max(0, 1 - (school.tuition_annual / 100000))
            employment_score = school.employment_rate
            salary_score = min(1, school.avg_salary / 300000)
            
            # 综合得分（加权）
            total_score = (
                admission['probability'] * 0.4 +
                cost_score * 0.2 +
                employment_score * 0.2 +
                salary_score * 0.2
            ) * 100
            
            comparisons.append({
                "school_name": school.name,
                "school_type": school.school_type.value,
                "location": school.location,
                "tuition": school.tuition_annual,
                "admission_prob": admission['probability'],
                "employment_rate": school.employment_rate,
                "avg_salary": school.avg_salary,
                "total_score": round(total_score, 1),
                "risk_level": admission['risk_level']
            })
            
            rankings.append({
                "rank": len(rankings) + 1,
                "school_name": school.name,
                "total_score": round(total_score, 1),
                "key_advantages": self._identify_school_advantages(school, admission)
            })
        
        # 按综合得分排序
        rankings.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 更新排名
        for i, r in enumerate(rankings):
            r['rank'] = i + 1
        
        return {
            "comparisons": comparisons,
            "ranking": rankings,
            "best_choice": rankings[0] if rankings else None,
            "safety_option": next(
                (r for r in rankings if comparisons[len(rankings) - rankings.index(r) - 1]['risk_level'] == 'low'),
                rankings[-1] if rankings else None
            )
        }
    
    def _identify_school_advantages(self, school: TargetSchool, admission: Dict) -> List[str]:
        """识别学校优势"""
        advantages = []
        
        if school.school_type == SchoolType.TOP:
            advantages.append("顶尖院校，声誉高")
        if school.acceptance_rate > 0.3:
            advantages.append("录取相对友好")
        if school.employment_rate > 0.9:
            advantages.append("就业率高")
        if school.avg_salary > 200000:
            advantages.append("薪资待遇优厚")
        if school.tuition_annual < 30000:
            advantages.append("学费相对较低")
        
        if not advantages:
            advantages.append("综合表现中等")
        
        return advantages
    
    def suggest_application_strategy(
        self,
        schools: List[TargetSchool],
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        生成申请策略建议
        
        Returns:
            申请策略
        """
        # 分析每所学校
        school_analysis = []
        for school in schools:
            admission = self.calculate_admission_probability(school, context)
            school_analysis.append({
                'school': school,
                'admission': admission
            })
        
        # 按概率分组
        safety = [s for s in school_analysis if s['admission']['risk_level'] == 'low']
        match = [s for s in school_analysis if s['admission']['risk_level'] == 'medium']
        reach = [s for s in school_analysis if s['admission']['risk_level'] == 'high']
        
        # 推荐组合
        recommended = []
        
        # 保底2-3所
        for s in safety[:3]:
            recommended.append({
                'school_name': s['school'].name,
                'type': '保底',
                'probability': s['admission']['probability'],
                'strategy': '确保有学上'
            })
        
        # 匹配3-4所
        for s in match[:4]:
            recommended.append({
                'school_name': s['school'].name,
                'type': '匹配',
                'probability': s['admission']['probability'],
                'strategy': '重点准备申请材料'
            })
        
        # 冲刺1-2所
        for s in reach[:2]:
            recommended.append({
                'school_name': s['school'].name,
                'type': '冲刺',
                'probability': s['admission']['probability'],
                'strategy': '冲刺申请，万一成功呢'
            })
        
        return {
            'total_schools': len(schools),
            'strategy_breakdown': {
                'safety': len(safety),
                'match': len(match),
                'reach': len(reach)
            },
            'recommended_applications': recommended,
            'application_tips': self._generate_application_tips(school_analysis)
        }
    
    def _generate_application_tips(self, analysis: List[Dict]) -> List[str]:
        """生成申请技巧"""
        tips = []
        
        # 识别共性问题
        low_gpa_count = sum(1 for s in analysis if s['admission']['gpa_match'] < 0.9)
        if low_gpa_count > len(analysis) / 2:
            tips.append("多所学校GPA要求较高，需要突出其他方面的优势")
        
        # 资源建议
        tips.append("提前准备个人陈述，突出独特经历和目标")
        tips.append("获取有分量的推荐信")
        tips.append("注意申请截止日期，建议提前2周提交")
        
        return tips
    
    def create_education_decision_option(
        self,
        option_id: str,
        school: TargetSchool,
        context: EducationDecisionContext,
        expected_outcomes: Dict[str, float]
    ) -> DecisionOption:
        """
        创建教育决策选项
        
        Returns:
            决策选项对象
        """
        # 计算录取概率
        admission = self.calculate_admission_probability(school, context)
        
        # 计算可行性
        feasibility_score = admission['probability']
        
        # 计算收益
        benefit_score = (
            expected_outcomes.get('employment_rate', 0.9) * 0.4 +
            expected_outcomes.get('salary_increase', 0.5) * 0.4 +
            expected_outcomes.get('career_growth', 0.5) * 0.2
        )
        
        # 计算风险
        risk_score = 1.0 - admission['probability']
        
        # 计算可逆性
        reversibility_score = 0.7  # 教育决策通常可逆性较高
        
        return DecisionOption(
            id=option_id,
            title=f"申请{school.name}",
            description=f"申请{school.name}{school.school_type.value}院校",
            feasibility_score=feasibility_score,
            benefit_score=benefit_score,
            risk_score=risk_score,
            reversibility_score=reversibility_score,
            alignment_score=0.8,  # 需要用户目标信息
            resource_score=1.0 - (school.tuition_annual / 100000),  # 成本考量
            evidence={
                "school": school.name,
                "school_type": school.school_type.value,
                "admission_probability": admission['probability'],
                "expected_employment": expected_outcomes.get('employment_rate', 0.9),
                "expected_salary": expected_outcomes.get('avg_salary', school.avg_salary)
            },
            assumptions=[
                "假设申请材料准备充分",
                "假设推荐信有足够分量",
                "假设没有重大外部变化（如政策、疫情）"
            ]
        )


# 示例使用
if __name__ == "__main__":
    engine = EducationDecisionEngine()
    
    # 创建教育决策上下文
    context = EducationDecisionContext(
        decision_topic="申请哪所大学的研究生项目",
        current_level=EducationLevel.BACHELOR,
        target_level=EducationLevel.MASTER,
        academic_profile=AcademicProfile(
            current_gpa=3.6,
            ranking_percent=0.15,
            test_scores={"GRE": 325, "TOEFL": 105},
            research_experience=0.7,
            publications=2,
            awards=["校长奖", "竞赛一等奖"],
            extracurricular=["社团", "志愿者"]
        ),
        target_schools=[
            TargetSchool(
                name="清华大学",
                school_type=SchoolType.TOP,
                location="北京",
                tuition_annual=50000,
                acceptance_rate=0.05,
                avg_gpa_accepted=3.8,
                employment_rate=0.98,
                avg_salary=250000
            ),
            TargetSchool(
                name="复旦大学",
                school_type=SchoolType.ELITE,
                location="上海",
                tuition_annual=45000,
                acceptance_rate=0.15,
                avg_gpa_accepted=3.6,
                employment_rate=0.95,
                avg_salary=220000
            ),
            TargetSchool(
                name="上海交通大学",
                school_type=SchoolType.ELITE,
                location="上海",
                tuition_annual=45000,
                acceptance_rate=0.18,
                avg_gpa_accepted=3.5,
                employment_rate=0.95,
                avg_salary=230000
            )
        ],
        budget=200000,
        preferences={"location": ["北京", "上海"], "cost_sensitive": True}
    )
    
    # 评估竞争力
    competitiveness = engine.evaluate_academic_competitiveness(context)
    print("=" * 60)
    print("学业竞争力评估")
    print("=" * 60)
    print(f"综合得分: {competitiveness['total_score']}")
    print(f"百分位: 前{competitiveness['percentile']}%")
    print(f"各项得分: {competitiveness['breakdown']}")
    
    # 学校对比
    comparison = engine.compare_schools(context.target_schools, context)
    print("\n" + "=" * 60)
    print("学校对比排名")
    print("=" * 60)
    for r in comparison['ranking']:
        print(f"{r['rank']}. {r['school_name']} - 综合得分: {r['total_score']}")
        print(f"   优势: {', '.join(r['key_advantages'])}")
    
    # 申请策略
    strategy = engine.suggest_application_strategy(context.target_schools, context)
    print("\n" + "=" * 60)
    print("申请策略建议")
    print("=" * 60)
    print(f"总学校数: {strategy['total_schools']}")
    for app in strategy['recommended_applications']:
        print(f"  [{app['type']}] {app['school_name']} - 概率: {app['probability']:.1%}")