"""
升学规划决策引擎
基于学校数据和录取信息
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from backend.decision_algorithm.core_decision_engine import (
    CoreDecisionEngine,
    DecisionOption,
    DecisionDimension
)


@dataclass
class School:
    """学校信息"""
    name: str
    ranking: int  # 排名
    location: str
    major: str
    tuition: float  # 学费（万/年）
    admission_score: int  # 录取分数线
    admission_rate: float  # 录取率
    employment_rate: float  # 就业率
    average_salary: float  # 毕业生平均薪资（万/年）
    program_duration: int  # 学制（年）
    
    def __post_init__(self):
        self.total_cost = self.tuition * self.program_duration


@dataclass
class EducationDecisionContext:
    """升学决策上下文"""
    current_score: int  # 当前成绩/分数
    target_major: Optional[str] = None
    location_preference: Optional[str] = None
    budget_limit: float = 0.0  # 预算上限（万）
    career_goal: Optional[str] = None
    study_time_available: int = 0  # 可用备考时间（月）
    family_support: float = 0.5  # 0-1，家庭支持程度
    
    def __post_init__(self):
        if self.budget_limit == 0.0:
            self.budget_limit = float('inf')


class EducationDecisionEngine:
    """
    升学决策引擎
    
    核心功能：
    1. 学校匹配分析
    2. 录取概率评估
    3. 成本收益分析
    4. 备考规划
    """
    
    def __init__(self):
        self.core_engine = CoreDecisionEngine()
    
    def calculate_admission_probability(
        self,
        school: School,
        context: EducationDecisionContext
    ) -> float:
        """
        计算录取概率
        
        Returns:
            录取概率 0-1
        """
        # 基于分数差距
        score_gap = context.current_score - school.admission_score
        
        if score_gap >= 20:
            base_prob = 0.9
        elif score_gap >= 10:
            base_prob = 0.75
        elif score_gap >= 0:
            base_prob = 0.6
        elif score_gap >= -10:
            base_prob = 0.4
        elif score_gap >= -20:
            base_prob = 0.2
        else:
            base_prob = 0.05
        
        # 考虑录取率
        rate_factor = school.admission_rate
        
        # 考虑备考时间
        time_factor = min(1.0, context.study_time_available / 6)  # 6个月为基准
        
        # 综合概率
        final_prob = base_prob * (0.6 + rate_factor * 0.2 + time_factor * 0.2)
        
        return round(min(0.95, max(0.05, final_prob)), 2)
    
    def analyze_school_match(
        self,
        school: School,
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        分析学校匹配度
        
        Returns:
            匹配度分析结果
        """
        # 1. 录取概率
        admission_prob = self.calculate_admission_probability(school, context)
        
        # 2. 专业匹配
        major_match = 1.0 if not context.target_major or school.major == context.target_major else 0.6
        
        # 3. 地域匹配
        location_match = 1.0 if not context.location_preference or school.location == context.location_preference else 0.7
        
        # 4. 预算匹配
        budget_match = 1.0 if school.total_cost <= context.budget_limit else context.budget_limit / school.total_cost
        
        # 5. 就业前景
        employment_score = school.employment_rate
        
        # 综合匹配度
        overall_match = (
            admission_prob * 0.30 +
            major_match * 0.25 +
            employment_score * 0.20 +
            budget_match * 0.15 +
            location_match * 0.10
        )
        
        return {
            "overall_match": round(overall_match, 2),
            "admission_probability": admission_prob,
            "major_match": round(major_match, 2),
            "location_match": round(location_match, 2),
            "budget_match": round(budget_match, 2),
            "employment_score": round(employment_score, 2),
            "score_gap": context.current_score - school.admission_score,
            "recommendation": self._generate_recommendation(admission_prob, overall_match)
        }
    
    def _generate_recommendation(self, admission_prob: float, match_score: float) -> str:
        """生成推荐建议"""
        if admission_prob >= 0.8 and match_score >= 0.75:
            return "强烈推荐：录取概率高且高度匹配"
        elif admission_prob >= 0.6 and match_score >= 0.6:
            return "推荐：有较大把握且基本符合期望"
        elif admission_prob >= 0.4:
            return f"可以尝试：需要努力提升{abs(admission_prob - 0.6) * 100:.0f}分左右"
        elif admission_prob >= 0.2:
            return "冲刺选项：录取概率较低，建议作为冲刺目标"
        else:
            return "不推荐：当前分数差距较大，建议选择更匹配的学校"
    
    def calculate_roi(
        self,
        school: School,
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        计算投资回报率
        
        Returns:
            ROI分析结果
        """
        # 总成本
        total_cost = school.total_cost
        
        # 机会成本（假设不读书直接工作）
        opportunity_cost = 8.0 * school.program_duration  # 假设年薪8万
        
        # 总投入
        total_investment = total_cost + opportunity_cost
        
        # 预期收益（毕业后薪资提升）
        salary_increase = school.average_salary - 8.0
        
        # 回本时间（年）
        payback_period = total_investment / salary_increase if salary_increase > 0 else float('inf')
        
        # 10年总收益
        ten_year_benefit = salary_increase * 10 - total_investment
        
        # ROI
        roi = (ten_year_benefit / total_investment * 100) if total_investment > 0 else 0
        
        return {
            "total_cost": round(total_cost, 1),
            "opportunity_cost": round(opportunity_cost, 1),
            "total_investment": round(total_investment, 1),
            "expected_salary": school.average_salary,
            "salary_increase": round(salary_increase, 1),
            "payback_period_years": round(payback_period, 1) if payback_period != float('inf') else "无法回本",
            "ten_year_benefit": round(ten_year_benefit, 1),
            "roi_percentage": round(roi, 1),
            "roi_level": "高" if roi > 100 else ("中" if roi > 50 else "低")
        }
    
    def create_study_plan(
        self,
        school: School,
        context: EducationDecisionContext
    ) -> Dict[str, Any]:
        """
        创建备考计划
        
        Returns:
            备考计划
        """
        score_gap = school.admission_score - context.current_score
        
        if score_gap <= 0:
            return {
                "needed": False,
                "message": "当前分数已达标，保持状态即可"
            }
        
        # 计算每月需要提升的分数
        monthly_target = score_gap / context.study_time_available if context.study_time_available > 0 else score_gap
        
        # 判断难度
        if monthly_target <= 5:
            difficulty = "容易"
            daily_hours = 2
        elif monthly_target <= 10:
            difficulty = "中等"
            daily_hours = 4
        elif monthly_target <= 15:
            difficulty = "困难"
            daily_hours = 6
        else:
            difficulty = "极难"
            daily_hours = 8
        
        return {
            "needed": True,
            "score_gap": score_gap,
            "study_months": context.study_time_available,
            "monthly_target": round(monthly_target, 1),
            "difficulty": difficulty,
            "daily_study_hours": daily_hours,
            "weekly_plan": self._generate_weekly_plan(daily_hours),
            "milestones": self._generate_milestones(score_gap, context.study_time_available)
        }
    
    def _generate_weekly_plan(self, daily_hours: int) -> Dict[str, str]:
        """生成每周计划"""
        return {
            "周一至周五": f"每天{daily_hours}小时，重点突破薄弱科目",
            "周六": f"{daily_hours + 2}小时，综合练习和模拟考试",
            "周日": "复习总结，调整计划"
        }
    
    def _generate_milestones(self, score_gap: int, months: int) -> List[Dict[str, Any]]:
        """生成里程碑"""
        if months == 0:
            return []
        
        milestones = []
        step = score_gap / min(months, 4)  # 最多4个里程碑
        
        for i in range(1, min(months, 4) + 1):
            milestones.append({
                "month": i,
                "target_score_increase": round(step * i, 0),
                "checkpoint": f"第{i}个月检查点"
            })
        
        return milestones
    
    def create_education_decision_option(
        self,
        option_id: str,
        title: str,
        school: School,
        context: EducationDecisionContext
    ) -> DecisionOption:
        """
        创建升学决策选项
        
        Returns:
            决策选项对象
        """
        # 分析学校匹配
        match_analysis = self.analyze_school_match(school, context)
        
        # 计算ROI
        roi_analysis = self.calculate_roi(school, context)
        
        # 创建备考计划
        study_plan = self.create_study_plan(school, context)
        
        # 计算可行性
        feasibility_score = match_analysis["admission_probability"]
        
        # 计算收益
        benefit_score = min(1.0, roi_analysis["roi_percentage"] / 200)  # 归一化
        
        # 计算风险
        failure_prob = 1 - match_analysis["admission_probability"]
        failure_cost = school.total_cost / 10  # 归一化
        
        risk_score, risk_details = self.core_engine.calculate_risk(
            failure_probability=failure_prob,
            failure_cost=failure_cost,
            uncertainty_factors=["考试发挥", "录取竞争", "政策变化"],
            mitigation_plans=["充分备考", "多个志愿", "保底选择"]
        )
        
        # 计算可逆性（退学成本）
        reversibility_score, reversibility_details = self.core_engine.calculate_reversibility(
            can_undo=True,
            undo_cost=school.tuition,  # 已交学费
            time_to_undo=365,
            reputation_impact=0.4
        )
        
        # 创建决策选项
        option = DecisionOption(
            id=option_id,
            title=title,
            description=f"{school.name} - {school.major}",
            feasibility_score=feasibility_score,
            benefit_score=benefit_score,
            risk_score=risk_score,
            reversibility_score=reversibility_score,
            alignment_score=match_analysis["major_match"],
            resource_score=match_analysis["budget_match"],
            evidence={
                "match_analysis": match_analysis,
                "roi_analysis": roi_analysis,
                "study_plan": study_plan,
                "risk_details": risk_details,
                "reversibility_details": reversibility_details,
                "school_info": {
                    "name": school.name,
                    "ranking": school.ranking,
                    "location": school.location,
                    "major": school.major,
                    "tuition": f"{school.tuition}万/年",
                    "employment_rate": f"{school.employment_rate * 100}%"
                }
            },
            assumptions=[
                "假设学校录取标准保持稳定",
                "假设就业市场情况不发生重大变化",
                f"假设能够按计划完成{school.program_duration}年学业"
            ]
        )
        
        return option
    
    def compare_education_options(
        self,
        schools: List[School],
        context: EducationDecisionContext,
        user_weights: Optional[Dict[DecisionDimension, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        对比多个升学选项
        
        Returns:
            排序后的选项列表
        """
        options = []
        for i, school in enumerate(schools):
            option = self.create_education_decision_option(
                option_id=f"edu_opt_{i+1}",
                title=f"{school.name} - {school.major}",
                school=school,
                context=context
            )
            options.append(option)
        
        return self.core_engine.compare_options(options, user_weights)


# 示例使用
if __name__ == "__main__":
    engine = EducationDecisionEngine()
    
    # 创建升学决策上下文
    context = EducationDecisionContext(
        current_score=580,
        target_major="计算机科学",
        location_preference="北京",
        budget_limit=20.0,
        career_goal="互联网大厂",
        study_time_available=6,
        family_support=0.8
    )
    
    # 创建学校信息
    schools = [
        School(
            name="清华大学",
            ranking=1,
            location="北京",
            major="计算机科学",
            tuition=0.5,
            admission_score=680,
            admission_rate=0.02,
            employment_rate=0.98,
            average_salary=35.0,
            program_duration=4
        ),
        School(
            name="北京邮电大学",
            ranking=30,
            location="北京",
            major="计算机科学",
            tuition=0.5,
            admission_score=600,
            admission_rate=0.15,
            employment_rate=0.92,
            average_salary=25.0,
            program_duration=4
        ),
        School(
            name="北京工业大学",
            ranking=80,
            location="北京",
            major="计算机科学",
            tuition=0.5,
            admission_score=560,
            admission_rate=0.30,
            employment_rate=0.85,
            average_salary=18.0,
            program_duration=4
        )
    ]
    
    # 对比选项
    results = engine.compare_education_options(schools, context)
    
    print("=" * 60)
    print("升学决策对比结果")
    print("=" * 60)
    
    for result in results:
        option = result['option']
        print(f"\n排名 {result['rank']}: {option.title}")
        print(f"总分: {result['total_score']:.2f}")
        print(f"录取概率: {option.evidence['match_analysis']['admission_probability']}")
        print(f"ROI: {option.evidence['roi_analysis']['roi_percentage']}%")
        print(f"推荐: {option.evidence['match_analysis']['recommendation']}")
