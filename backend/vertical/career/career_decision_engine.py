"""
职业选择决策引擎
基于真实岗位数据和市场信息
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from backend.decision_algorithm.core_decision_engine import (
    CoreDecisionEngine,
    DecisionOption,
    DecisionDimension
)


@dataclass
class JobPosition:
    """岗位信息"""
    title: str
    company: str
    salary_range: Tuple[float, float]  # 薪资范围（万/年）
    required_skills: List[str]
    experience_required: int  # 年限
    industry: str
    location: str
    description: str = ""


@dataclass
class CareerDecisionContext:
    """职业决策上下文"""
    current_position: Optional[str] = None
    current_salary: float = 0.0  # 万/年
    years_experience: int = 0
    current_skills: List[str] = None
    target_industry: Optional[str] = None
    location_preference: Optional[str] = None
    financial_pressure: float = 0.5  # 0-1，财务压力
    growth_priority: float = 0.5  # 0-1，成长优先级
    
    def __post_init__(self):
        if self.current_skills is None:
            self.current_skills = []


class CareerDecisionEngine:
    """
    职业决策引擎
    
    核心功能：
    1. 岗位匹配分析
    2. 薪资预期分析
    3. 学习路径规划
    4. 转型风险评估
    """
    
    def __init__(self):
        self.core_engine = CoreDecisionEngine()
        # 技能树（简化版）
        self.skill_tree = self._build_skill_tree()
    
    def _build_skill_tree(self) -> Dict[str, List[str]]:
        """构建技能依赖树"""
        return {
            "Python": [],
            "Django": ["Python"],
            "FastAPI": ["Python"],
            "React": ["JavaScript"],
            "Vue": ["JavaScript"],
            "Docker": [],
            "Kubernetes": ["Docker"],
            "AWS": [],
            "机器学习": ["Python"],
            "深度学习": ["Python", "机器学习"],
        }
    
    def analyze_job_match(
        self,
        job: JobPosition,
        context: CareerDecisionContext
    ) -> Dict[str, Any]:
        """
        分析岗位匹配度
        
        Returns:
            匹配度分析结果
        """
        # 1. 技能匹配
        skill_match = len(set(job.required_skills) & set(context.current_skills)) / len(job.required_skills) if job.required_skills else 1.0
        missing_skills = list(set(job.required_skills) - set(context.current_skills))
        
        # 2. 经验匹配
        experience_match = min(1.0, context.years_experience / job.experience_required) if job.experience_required > 0 else 1.0
        
        # 3. 薪资匹配
        salary_min, salary_max = job.salary_range
        salary_avg = (salary_min + salary_max) / 2
        salary_growth = (salary_avg - context.current_salary) / context.current_salary if context.current_salary > 0 else 0.5
        
        # 4. 地域匹配
        location_match = 1.0 if not context.location_preference or job.location == context.location_preference else 0.6
        
        # 5. 行业匹配
        industry_match = 1.0 if not context.target_industry or job.industry == context.target_industry else 0.7
        
        # 综合匹配度
        overall_match = (
            skill_match * 0.35 +
            experience_match * 0.25 +
            min(1.0, max(0.0, salary_growth + 0.5)) * 0.20 +
            location_match * 0.10 +
            industry_match * 0.10
        )
        
        return {
            "overall_match": round(overall_match, 2),
            "skill_match": round(skill_match, 2),
            "experience_match": round(experience_match, 2),
            "salary_growth": round(salary_growth, 2),
            "location_match": round(location_match, 2),
            "industry_match": round(industry_match, 2),
            "missing_skills": missing_skills,
            "salary_range": f"{salary_min}-{salary_max}万/年",
            "recommendation": self._generate_recommendation(overall_match, missing_skills)
        }
    
    def _generate_recommendation(self, match_score: float, missing_skills: List[str]) -> str:
        """生成推荐建议"""
        if match_score >= 0.8:
            return "强烈推荐：您的背景与该岗位高度匹配"
        elif match_score >= 0.6:
            if missing_skills:
                return f"推荐：建议补充技能 {', '.join(missing_skills[:3])} 后申请"
            return "推荐：您的背景基本符合该岗位要求"
        elif match_score >= 0.4:
            return f"谨慎考虑：需要补充较多技能，建议先积累经验"
        else:
            return "不推荐：当前背景与岗位要求差距较大"
    
    def plan_learning_path(
        self,
        target_skills: List[str],
        current_skills: List[str]
    ) -> Dict[str, Any]:
        """
        规划学习路径
        
        Returns:
            学习路径规划
        """
        missing_skills = list(set(target_skills) - set(current_skills))
        
        # 计算每个技能的前置依赖
        learning_plan = []
        learned = set(current_skills)
        
        while missing_skills:
            # 找出可以立即学习的技能（前置依赖都已满足）
            ready_to_learn = []
            for skill in missing_skills:
                prerequisites = self.skill_tree.get(skill, [])
                if all(prereq in learned for prereq in prerequisites):
                    ready_to_learn.append(skill)
            
            if not ready_to_learn:
                # 如果没有可学习的，说明有循环依赖或未知技能
                ready_to_learn = missing_skills[:1]
            
            # 添加到学习计划
            for skill in ready_to_learn:
                learning_plan.append({
                    "skill": skill,
                    "prerequisites": self.skill_tree.get(skill, []),
                    "estimated_time": self._estimate_learning_time(skill),
                    "priority": "high" if skill in target_skills[:3] else "medium"
                })
                learned.add(skill)
                missing_skills.remove(skill)
        
        total_time = sum(item["estimated_time"] for item in learning_plan)
        
        return {
            "learning_plan": learning_plan,
            "total_time_weeks": total_time,
            "total_time_months": round(total_time / 4, 1),
            "current_skills_count": len(current_skills),
            "target_skills_count": len(target_skills),
            "skills_to_learn": len(learning_plan)
        }
    
    def _estimate_learning_time(self, skill: str) -> int:
        """估算学习时间（周）"""
        # 简化版：根据技能类型估算
        if skill in ["Python", "JavaScript"]:
            return 8
        elif skill in ["React", "Vue", "Django", "FastAPI"]:
            return 6
        elif skill in ["Docker", "AWS"]:
            return 4
        elif skill in ["机器学习", "深度学习"]:
            return 12
        else:
            return 4
    
    def create_career_decision_option(
        self,
        option_id: str,
        title: str,
        job: JobPosition,
        context: CareerDecisionContext
    ) -> DecisionOption:
        """
        创建职业决策选项
        
        Returns:
            决策选项对象
        """
        # 分析岗位匹配
        match_analysis = self.analyze_job_match(job, context)
        
        # 计算可行性
        feasibility_score = match_analysis["overall_match"]
        
        # 计算收益
        salary_min, salary_max = job.salary_range
        salary_avg = (salary_min + salary_max) / 2
        short_term_gain = (salary_avg - context.current_salary) / 10  # 归一化
        long_term_gain = context.growth_priority * 0.8  # 基于成长优先级
        
        benefit_score, benefit_details = self.core_engine.calculate_benefit(
            short_term_gains={"salary": short_term_gain},
            long_term_gains={"career_growth": long_term_gain},
            opportunity_cost=0.3 if context.current_position else 0.0
        )
        
        # 计算风险
        failure_prob = 1 - match_analysis["skill_match"]
        failure_cost = context.financial_pressure * 5  # 财务压力越大，失败代价越高
        
        risk_score, risk_details = self.core_engine.calculate_risk(
            failure_probability=failure_prob,
            failure_cost=failure_cost,
            uncertainty_factors=match_analysis["missing_skills"],
            mitigation_plans=["技能培训", "试用期观察", "保持现有工作"]
        )
        
        # 计算可逆性
        can_undo = context.current_position is not None
        undo_cost = 3.0 if can_undo else 8.0
        
        reversibility_score, reversibility_details = self.core_engine.calculate_reversibility(
            can_undo=can_undo,
            undo_cost=undo_cost,
            time_to_undo=90 if can_undo else 365,
            reputation_impact=0.3 if can_undo else 0.6
        )
        
        # 创建决策选项
        option = DecisionOption(
            id=option_id,
            title=title,
            description=f"{job.company} - {job.title}",
            feasibility_score=feasibility_score,
            benefit_score=benefit_score,
            risk_score=risk_score,
            reversibility_score=reversibility_score,
            alignment_score=0.7,  # 默认值，需要用户目标信息
            resource_score=1 - context.financial_pressure,
            evidence={
                "match_analysis": match_analysis,
                "benefit_details": benefit_details,
                "risk_details": risk_details,
                "reversibility_details": reversibility_details,
                "job_info": {
                    "company": job.company,
                    "title": job.title,
                    "salary_range": f"{salary_min}-{salary_max}万",
                    "industry": job.industry,
                    "location": job.location
                }
            },
            assumptions=[
                f"假设您能在{self._estimate_learning_time(match_analysis['missing_skills'][0]) if match_analysis['missing_skills'] else 0}周内补充缺失技能",
                "假设市场薪资水平保持稳定",
                "假设公司发展前景良好"
            ]
        )
        
        return option
    
    def compare_career_options(
        self,
        jobs: List[JobPosition],
        context: CareerDecisionContext,
        user_weights: Optional[Dict[DecisionDimension, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        对比多个职业选项
        
        Returns:
            排序后的选项列表
        """
        options = []
        for i, job in enumerate(jobs):
            option = self.create_career_decision_option(
                option_id=f"career_opt_{i+1}",
                title=f"{job.company} - {job.title}",
                job=job,
                context=context
            )
            options.append(option)
        
        return self.core_engine.compare_options(options, user_weights)


# 示例使用
if __name__ == "__main__":
    engine = CareerDecisionEngine()
    
    # 创建职业决策上下文
    context = CareerDecisionContext(
        current_position="Python开发工程师",
        current_salary=20.0,
        years_experience=3,
        current_skills=["Python", "Django", "MySQL", "Redis"],
        target_industry="互联网",
        location_preference="北京",
        financial_pressure=0.6,
        growth_priority=0.7
    )
    
    # 创建岗位信息
    jobs = [
        JobPosition(
            title="高级Python工程师",
            company="字节跳动",
            salary_range=(30, 40),
            required_skills=["Python", "Django", "Redis", "Kafka"],
            experience_required=3,
            industry="互联网",
            location="北京"
        ),
        JobPosition(
            title="机器学习工程师",
            company="阿里巴巴",
            salary_range=(35, 50),
            required_skills=["Python", "机器学习", "深度学习", "TensorFlow"],
            experience_required=3,
            industry="互联网",
            location="北京"
        )
    ]
    
    # 对比选项
    results = engine.compare_career_options(jobs, context)
    
    print("=" * 60)
    print("职业决策对比结果")
    print("=" * 60)
    
    for result in results:
        option = result['option']
        print(f"\n排名 {result['rank']}: {option.title}")
        print(f"总分: {result['total_score']:.2f}")
        print(f"匹配度: {option.evidence['match_analysis']['overall_match']}")
        print(f"推荐: {option.evidence['match_analysis']['recommendation']}")
