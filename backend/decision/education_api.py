"""
教育升学决策API路由

提供教育升学决策的完整API：
1. 学校数据查询
2. 录取概率计算
3. 教育ROI分析
4. 申请策略优化
5. 升学推演模拟
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.decision.multi_agent_education_evaluator import (
    MultiAgentEducationEvaluator
)
from backend.decision_algorithm.education_decision_algorithm import (
    EducationDecisionAlgorithm,
    EducationStage,
    SchoolTier,
    MajorCategory,
    KnowledgeGraphEducationIntegration
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v5/education", tags=["education"])


# ==================== 请求模型 ====================

class AcademicRecordInput(BaseModel):
    """学业记录输入"""
    gpa: float = Field(default=3.5, ge=0, le=4.0, description="GPA 0-4.0")
    gpa_max: float = Field(default=4.0, description="GPA满分")
    ranking: float = Field(default=0.2, ge=0, le=1, description="年级排名百分比")
    sat_act: float = Field(default=1450, ge=0, description="SAT/ACT成绩")
    gre_gmat: float = Field(default=0, ge=0, description="GRE/GMAT成绩")
    toefl_ielts: float = Field(default=7.5, ge=0, description="语言成绩")
    publications: int = Field(default=0, ge=0, description="发表论文数")
    research_experience: float = Field(default=0.5, ge=0, le=1, description="科研经历 0-1")
    awards: List[str] = Field(default_factory=list, description="获奖经历")


class SchoolInput(BaseModel):
    """目标学校输入"""
    school_id: str = Field(..., description="学校ID")
    school_name: str = Field(..., description="学校名称")
    tier: str = Field(default="elite", description="学校层级: top_tier, elite, good, standard, specialized")
    location: str = Field(default="", description="地理位置")
    tuition_annual: float = Field(default=50000, ge=0, description="年学费")
    living_cost_annual: float = Field(default=20000, ge=0, description="年生活费")
    major_ranking: int = Field(default=0, ge=0, description="专业排名")
    overall_ranking: int = Field(default=0, ge=0, description="综合排名")
    acceptance_rate: float = Field(default=0.2, ge=0, le=1, description="录取率")
    avg_salary_post_grad: float = Field(default=150000, ge=0, description="毕业后平均薪资")
    employment_rate: float = Field(default=0.9, ge=0, le=1, description="就业率")
    avg_gpa_accepted: float = Field(default=3.5, ge=0, le=4.0, description="录取平均GPA")


class MajorInput(BaseModel):
    """专业输入"""
    major_id: str = Field(..., description="专业ID")
    major_name: str = Field(..., description="专业名称")
    category: str = Field(default="cs_it", description="专业大类")
    difficulty: float = Field(default=0.5, ge=0, le=1, description="学习难度")
    market_demand: float = Field(default=0.7, ge=0, le=1, description="市场需求")
    salary_potential: float = Field(default=0.7, ge=0, le=1, description="薪资潜力")
    growth_potential: float = Field(default=0.7, ge=0, le=1, description="增长潜力")
    competition_intensity: float = Field(default=0.5, ge=0, le=1, description="竞争强度")


class StudentProfileInput(BaseModel):
    """学生画像输入"""
    student_id: str
    current_stage: str = Field(default="undergraduate", description="当前阶段")
    academic_record: AcademicRecordInput = Field(default_factory=AcademicRecordInput)
    family_income: float = Field(default=300000, ge=0, description="家庭年收入")
    scholarship_need: float = Field(default=0.5, ge=0, le=1, description="奖学金需求")
    preferred_locations: List[str] = Field(default_factory=list, description="偏好地区")
    risk_tolerance: float = Field(default=0.5, ge=0, le=1, description="风险承受度")


class EducationOptionInput(BaseModel):
    """升学选项输入"""
    id: str = Field(..., description="选项ID")
    school: SchoolInput
    major: MajorInput
    degree_level: str = Field(default="master", description="学位级别")
    application_deadline: str = Field(default="", description="申请截止日期")


class EducationDecisionRequest(BaseModel):
    """教育升学决策请求"""
    user_id: str
    question: str = Field(..., description="决策问题")
    options: List[EducationOptionInput] = Field(..., description="升学选项列表")
    student_profile: Optional[StudentProfileInput] = Field(default=None, description="学生画像")


class AdmissionProbabilityRequest(BaseModel):
    """录取概率计算请求"""
    user_id: str
    school: SchoolInput
    student_profile: StudentProfileInput


class ROICalculationRequest(BaseModel):
    """ROI计算请求"""
    user_id: str
    option: EducationOptionInput
    student_profile: StudentProfileInput


class EducationSimulationRequest(BaseModel):
    """升学推演请求"""
    user_id: str
    question: str = Field(..., description="决策问题")
    options: List[EducationOptionInput]
    student_profile: Optional[StudentProfileInput] = Field(default=None)
    months: int = Field(default=6, ge=1, le=24, description="推演月数")


# ==================== API路由 ====================

@router.get("/schools")
async def get_available_schools():
    """
    获取可选学校列表
    
    返回系统支持的所有学校数据
    """
    try:
        # 模拟学校数据库
        schools = [
            {
                "school_id": "tsinghua",
                "school_name": "清华大学",
                "tier": "top_tier",
                "location": "北京",
                "tuition_annual": 50000,
                "living_cost_annual": 20000,
                "major_ranking": 5,
                "overall_ranking": 1,
                "acceptance_rate": 0.01,
                "avg_salary_post_grad": 250000,
                "employment_rate": 0.98,
                "avg_gpa_accepted": 3.9
            },
            {
                "school_id": "pku",
                "school_name": "北京大学",
                "tier": "top_tier",
                "location": "北京",
                "tuition_annual": 50000,
                "living_cost_annual": 20000,
                "major_ranking": 3,
                "overall_ranking": 2,
                "acceptance_rate": 0.01,
                "avg_salary_post_grad": 240000,
                "employment_rate": 0.98,
                "avg_gpa_accepted": 3.9
            },
            {
                "school_id": "fudan",
                "school_name": "复旦大学",
                "tier": "elite",
                "location": "上海",
                "tuition_annual": 45000,
                "living_cost_annual": 18000,
                "major_ranking": 20,
                "overall_ranking": 5,
                "acceptance_rate": 0.05,
                "avg_salary_post_grad": 220000,
                "employment_rate": 0.95,
                "avg_gpa_accepted": 3.7
            },
            {
                "school_id": "mit",
                "school_name": "MIT",
                "tier": "top_tier",
                "location": "Massachusetts",
                "tuition_annual": 55000,
                "living_cost_annual": 25000,
                "major_ranking": 1,
                "overall_ranking": 1,
                "acceptance_rate": 0.04,
                "avg_salary_post_grad": 350000,
                "employment_rate": 0.95,
                "avg_gpa_accepted": 3.9
            },
            {
                "school_id": "sjtu",
                "school_name": "上海交通大学",
                "tier": "elite",
                "location": "上海",
                "tuition_annual": 45000,
                "living_cost_annual": 18000,
                "major_ranking": 15,
                "overall_ranking": 6,
                "acceptance_rate": 0.06,
                "avg_salary_post_grad": 230000,
                "employment_rate": 0.95,
                "avg_gpa_accepted": 3.65
            }
        ]
        
        return {
            "success": True,
            "data": {
                "schools": schools,
                "total": len(schools)
            }
        }
    except Exception as e:
        logger.error(f"[EducationAPI] 获取学校列表失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": {"schools": [], "total": 0}
        }


@router.get("/majors")
async def get_available_majors():
    """
    获取可选专业列表
    
    返回系统支持的所有专业数据
    """
    try:
        majors = [
            {
                "major_id": "cs",
                "major_name": "计算机科学",
                "category": "cs_it",
                "difficulty": 0.7,
                "market_demand": 0.95,
                "salary_potential": 0.95,
                "growth_potential": 0.9,
                "competition_intensity": 0.9
            },
            {
                "major_id": "ai",
                "major_name": "人工智能",
                "category": "cs_it",
                "difficulty": 0.85,
                "market_demand": 0.98,
                "salary_potential": 0.98,
                "growth_potential": 0.95,
                "competition_intensity": 0.95
            },
            {
                "major_id": "finance",
                "major_name": "金融",
                "category": "business",
                "difficulty": 0.6,
                "market_demand": 0.8,
                "salary_potential": 0.85,
                "growth_potential": 0.6,
                "competition_intensity": 0.8
            },
            {
                "major_id": "economics",
                "major_name": "经济学",
                "category": "social",
                "difficulty": 0.65,
                "market_demand": 0.75,
                "salary_potential": 0.8,
                "growth_potential": 0.65,
                "competition_intensity": 0.75
            },
            {
                "major_id": "ee",
                "major_name": "电子工程",
                "category": "engineering",
                "difficulty": 0.75,
                "market_demand": 0.85,
                "salary_potential": 0.9,
                "growth_potential": 0.8,
                "competition_intensity": 0.85
            }
        ]
        
        return {
            "success": True,
            "data": {
                "majors": majors,
                "total": len(majors)
            }
        }
    except Exception as e:
        logger.error(f"[EducationAPI] 获取专业列表失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": {"majors": [], "total": 0}
        }


@router.post("/analyze")
async def analyze_education_decision(request: EducationDecisionRequest):
    """
    分析教育升学决策
    
    综合分析录取概率、ROI、申请策略
    """
    try:
        # 构建选项数据
        options_data = [
            {
                "id": opt.id,
                "school_name": opt.school.school_name,
                "major_name": opt.major.major_name,
                "degree_level": opt.degree_level,
                "deadline": opt.application_deadline,
                "safety_level": "match"
            }
            for opt in request.options
        ]
        
        # 分析决策
        integration = KnowledgeGraphEducationIntegration(request.user_id)
        result = integration.analyze_education_decision(
            request.question,
            options_data
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"[EducationAPI] 分析决策失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/admission-probability")
async def calculate_admission_probability(request: AdmissionProbabilityRequest):
    """
    计算录取概率
    
    基于学生画像和目标学校计算录取概率
    """
    try:
        from backend.decision_algorithm.education_decision_algorithm import (
            StudentProfile, AcademicRecord, School, Major, EducationOption, EducationStage, SchoolTier, MajorCategory
        )
        
        # 构建学生画像
        student = StudentProfile(
            student_id=request.user_id,
            current_stage=EducationStage[request.student_profile.current_stage.upper()],
            academic_record=AcademicRecord(
                gpa=request.student_profile.academic_record.gpa,
                gpa_max=request.student_profile.academic_record.gpa_max,
                ranking=request.student_profile.academic_record.ranking,
                sat_act=request.student_profile.academic_record.sat_act,
                gre_gmat=request.student_profile.academic_record.gre_gmat,
                toefl_ielts=request.student_profile.academic_record.toefl_ielts,
                publications=request.student_profile.academic_record.publications,
                research_experience=request.student_profile.academic_record.research_experience,
                awards=request.student_profile.academic_record.awards
            ),
            family_income=request.student_profile.family_income,
            scholarship_need=request.student_profile.scholarship_need,
            preferred_locations=request.student_profile.preferred_locations,
            risk_tolerance=request.student_profile.risk_tolerance
        )
        
        # 构建学校
        school = School(
            school_id=request.school.school_id,
            school_name=request.school.school_name,
            tier=SchoolTier[request.school.tier.upper().replace("_", "")],
            location=request.school.location,
            tuition_annual=request.school.tuition_annual,
            living_cost_annual=request.school.living_cost_annual,
            major_ranking=request.school.major_ranking,
            overall_ranking=request.school.overall_ranking,
            acceptance_rate=request.school.acceptance_rate,
            avg_salary_post_grad=request.school.avg_salary_post_grad,
            employment_rate=request.school.employment_rate,
            avg_gpa_accepted=request.school.avg_gpa_accepted
        )
        
        # 计算概率
        algorithm = EducationDecisionAlgorithm()
        result = algorithm.calculate_admission_probability(student, EducationOption(
            option_id=request.school.school_id,
            school=school,
            major=Major(major_id="temp", major_name="通用", category=MajorCategory.CS_IT),
            degree_level=EducationStage[request.student_profile.current_stage.upper()]
        ))
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"[EducationAPI] 计算录取概率失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/roi")
async def calculate_education_roi(request: ROICalculationRequest):
    """
    计算教育投资回报率
    
    分析升学项目的经济回报
    """
    try:
        from backend.decision_algorithm.education_decision_algorithm import (
            StudentProfile, AcademicRecord, School, Major, EducationOption, EducationStage, SchoolTier, MajorCategory
        )
        
        # 构建学生画像
        student = StudentProfile(
            student_id=request.user_id,
            current_stage=EducationStage[request.student_profile.current_stage.upper()],
            academic_record=AcademicRecord(
                gpa=request.student_profile.academic_record.gpa,
                gpa_max=request.student_profile.academic_record.gpa_max,
                ranking=request.student_profile.academic_record.ranking,
                sat_act=request.student_profile.academic_record.sat_act,
                gre_gmat=request.student_profile.academic_record.gre_gmat,
                toefl_ielts=request.student_profile.academic_record.toefl_ielts,
                publications=request.student_profile.academic_record.publications,
                research_experience=request.student_profile.academic_record.research_experience,
                awards=request.student_profile.academic_record.awards
            ),
            family_income=request.student_profile.family_income,
            scholarship_need=request.student_profile.scholarship_need,
            preferred_locations=request.student_profile.preferred_locations,
            risk_tolerance=request.student_profile.risk_tolerance
        )
        
        # 构建选项
        school = School(
            school_id=request.option.school.school_id,
            school_name=request.option.school.school_name,
            tier=SchoolTier[request.option.school.tier.upper().replace("_", "")],
            location=request.option.school.location,
            tuition_annual=request.option.school.tuition_annual,
            living_cost_annual=request.option.school.living_cost_annual,
            major_ranking=request.option.school.major_ranking,
            overall_ranking=request.option.school.overall_ranking,
            acceptance_rate=request.option.school.acceptance_rate,
            avg_salary_post_grad=request.option.school.avg_salary_post_grad,
            employment_rate=request.option.school.employment_rate,
            avg_gpa_accepted=request.option.school.avg_gpa_accepted
        )
        
        major = Major(
            major_id=request.option.major.major_id,
            major_name=request.option.major.major_name,
            category=MajorCategory[request.option.major.category.upper()],
            difficulty=request.option.major.difficulty,
            market_demand=request.option.major.market_demand,
            salary_potential=request.option.major.salary_potential,
            growth_potential=request.option.major.growth_potential,
            competition_intensity=request.option.major.competition_intensity
        )
        
        option = EducationOption(
            option_id=request.option.id,
            school=school,
            major=major,
            degree_level=EducationStage[request.option.degree_level.upper()]
        )
        
        # 计算ROI
        algorithm = EducationDecisionAlgorithm()
        result = algorithm.calculate_education_roi(option, student)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"[EducationAPI] 计算ROI失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/simulate")
async def simulate_education_outcomes(request: EducationSimulationRequest):
    """
    模拟升学推演
    
    使用多Agent系统模拟升学决策在时间线上的变化
    """
    try:
        # 构建上下文
        academic_profile = {
            "gpa": 80 + request.student_profile.academic_record.gpa * 5 if request.student_profile else 82.5,
            "test_score": request.student_profile.academic_record.sat_act if request.student_profile else 1450,
            "research_score": request.student_profile.academic_record.research_experience * 100 if request.student_profile else 65
        }
        
        context = {
            "academic_profile": academic_profile,
            "financial_profile": {
                "total_budget": 300000,
                "scholarship_need": request.student_profile.scholarship_need * 100000 if request.student_profile else 50000
            },
            "application_strategy": {
                "total_tasks": len(request.options) * 3
            },
            "options": [
                {
                    "school_name": opt.school.school_name,
                    "base_probability": opt.school.acceptance_rate
                }
                for opt in request.options
            ]
        }
        
        # 创建评估器
        evaluator = MultiAgentEducationEvaluator(request.user_id)
        
        # 执行模拟
        result = await evaluator.simulate_full_timeline(context, request.months)
        
        # 序列化结果
        return {
            "success": True,
            "data": {
                "timeline": [
                    {
                        "month": month_data["month"],
                        "agents_state": month_data["agents_state"],
                        "milestones": month_data.get("milestones", [])
                    }
                    for month_data in result["timeline"]
                ],
                "summary": result["summary"]
            }
        }
        
    except Exception as e:
        logger.error(f"[EducationAPI] 模拟推演失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.get("/profile/{user_id}")
async def get_student_profile(user_id: str):
    """
    获取学生画像
    
    从知识图谱获取学生的学业档案
    """
    try:
        integration = KnowledgeGraphEducationIntegration(user_id)
        profile = integration.extract_student_profile_from_kg()
        
        return {
            "success": True,
            "data": {
                "student_id": profile.student_id,
                "current_stage": profile.current_stage.value,
                "academic_record": {
                    "gpa": profile.academic_record.gpa,
                    "gpa_max": profile.academic_record.gpa_max,
                    "ranking": profile.academic_record.ranking,
                    "sat_act": profile.academic_record.sat_act,
                    "publications": profile.academic_record.publications,
                    "research_experience": profile.academic_record.research_experience,
                    "awards": profile.academic_record.awards
                },
                "family_income": profile.family_income,
                "scholarship_need": profile.scholarship_need,
                "preferred_locations": profile.preferred_locations,
                "risk_tolerance": profile.risk_tolerance
            }
        }
        
    except Exception as e:
        logger.error(f"[EducationAPI] 获取学生画像失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/compare")
async def compare_education_options(request: EducationDecisionRequest):
    """
    对比升学选项
    
    多维度对比各选项的优劣
    """
    try:
        from backend.vertical.education.education_decision_engine import (
            EducationDecisionEngine,
            EducationLevel,
            AcademicProfile,
            TargetSchool,
            EducationDecisionContext
        )
        
        # 构建学业档案
        if request.student_profile:
            academic = request.student_profile.academic_record
            academic_profile = AcademicProfile(
                current_gpa=academic.gpa,
                ranking_percent=academic.ranking,
                test_scores={"SAT": academic.sat_act, "TOEFL": academic.toefl_ielts},
                research_experience=academic.research_experience,
                publications=academic.publications,
                awards=academic.awards,
                extracurricular=[]
            )
            stage = EducationLevel[request.student_profile.current_stage.upper()]
            budget = request.student_profile.family_income * 0.5
            prefs = {"location": request.student_profile.preferred_locations}
        else:
            academic_profile = AcademicProfile(
                current_gpa=3.5,
                ranking_percent=0.2,
                test_scores={},
                research_experience=0.5,
                publications=0,
                awards=[],
                extracurricular=[]
            )
            stage = EducationLevel.UNDERGRADUATE
            budget = 200000
            prefs = {}
        
        # 构建目标学校
        target_schools = []
        for opt in request.options:
            from backend.vertical.education.education_decision_engine import SchoolType
            tier_map = {
                "top_tier": SchoolType.TOP,
                "elite": SchoolType.ELITE,
                "good": SchoolType.STANDARD,
                "standard": SchoolType.STANDARD,
                "specialized": SchoolType.LOCAL
            }
            target_schools.append(TargetSchool(
                name=opt.school.school_name,
                school_type=tier_map.get(opt.school.tier, SchoolType.STANDARD),
                location=opt.school.location,
                tuition_annual=opt.school.tuition_annual,
                acceptance_rate=opt.school.acceptance_rate,
                avg_gpa_accepted=opt.school.avg_gpa_accepted,
                employment_rate=opt.school.employment_rate,
                avg_salary=opt.school.avg_salary_post_grad
            ))
        
        # 构建上下文
        context = EducationDecisionContext(
            decision_topic=request.question,
            current_level=EducationLevel.BACHELOR,
            target_level=stage,
            academic_profile=academic_profile,
            target_schools=target_schools,
            budget=budget,
            preferences=prefs
        )
        
        # 对比分析
        engine = EducationDecisionEngine()
        competitiveness = engine.evaluate_academic_competitiveness(context)
        comparison = engine.compare_schools(target_schools, context)
        strategy = engine.suggest_application_strategy(target_schools, context)
        
        return {
            "success": True,
            "data": {
                "competitiveness": competitiveness,
                "comparison": comparison,
                "strategy": strategy
            }
        }
        
    except Exception as e:
        logger.error(f"[EducationAPI] 对比选项失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
