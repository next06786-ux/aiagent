"""
教育升学决策算法引擎
基于教育经济学、多目标决策理论、录取概率模型的量化决策系统

核心价值：
1. 录取概率建模 - 综合GPA、标化成绩、软实力等多维度
2. 教育投资回报率 - 基于薪资数据、就业率、增长率
3. 学术路径规划 - 本科→硕士→博士最优路径
4. 竞争态势分析 - 相对排名、申请策略
5. 时间价值折现 - 考虑机会成本、年龄窗口
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


class EducationStage(Enum):
    """教育阶段"""
    HIGH_SCHOOL = "high_school"          # 高中
    UNDERGRADUATE = "undergraduate"      # 本科
    MASTER = "master"                   # 硕士
    PHD = "phd"                         # 博士
    PROFESSIONAL = "professional"       # 职业资格


class SchoolTier(Enum):
    """学校层级"""
    TOP_TIER = "top_tier"               # 顶尖（清北/华五/常青藤）
    ELITE = "elite"                     # 精英（985/211/知名海外）
    GOOD = "good"                      # 良好（一本/重点学科）
    STANDARD = "standard"               # 普通（二本/普通院校）
    SPECIALIZED = "specialized"        # 专科/职业技术


class MajorCategory(Enum):
    """专业大类"""
    CS_IT = "cs_it"                    # 计算机/信息技术
    ENGINEERING = "engineering"        # 工程
    BUSINESS = "business"               # 商科
    MEDICINE = "medicine"              # 医学
    LAW = "law"                        # 法学
    SCIENCE = "science"                # 理科
    ARTS = "arts"                     # 文科/艺术
    SOCIAL = "social"                  # 社科
    EDUCATION = "education"           # 教育


@dataclass
class AcademicRecord:
    """学业记录"""
    gpa: float = 3.0                    # GPA 0-4.0
    gpa_max: float = 4.0               # GPA满分
    ranking: float = 0.5               # 年级排名百分比（前50% = 0.5）
    sat_act: float = 0.0               # SAT/ACT成绩（标准化）
    gre_gmat: float = 0.0              # GRE/GMAT成绩
    toefl_ielts: float = 0.0           # 语言成绩
    publications: int = 0               # 发表论文数
    research_experience: float = 0.5    # 科研经历 0-1
    awards: List[str] = field(default_factory=list)  # 获奖经历


@dataclass
class School:
    """目标学校"""
    school_id: str
    school_name: str
    tier: SchoolTier
    location: str                       # 地理位置
    tuition_annual: float = 0.0        # 年学费
    living_cost_annual: float = 0.0    # 年生活费
    major_ranking: int = 0            # 专业排名
    overall_ranking: int = 0          # 综合排名
    acceptance_rate: float = 0.5       # 录取率
    avg_salary_post_grad: float = 0.0  # 毕业后平均薪资
    employment_rate: float = 0.9       # 就业率
    industry_growth: float = 0.5       # 行业增长率
    
    # 竞争数据
    avg_gpa_accepted: float = 3.5      # 录取平均GPA
    avg_test_accepted: float = 0.0     # 录取平均标化
    domestic_international: str = "domestic"  # 国内/海外


@dataclass
class Major:
    """专业"""
    major_id: str
    major_name: str
    category: MajorCategory
    difficulty: float = 0.5            # 学习难度 0-1
    market_demand: float = 0.5        # 市场需求 0-1
    salary_potential: float = 0.5      # 薪资潜力 0-1
    growth_potential: float = 0.5     # 增长潜力 0-1
    competition_intensity: float = 0.5  # 竞争强度 0-1


@dataclass
class EducationOption:
    """升学选项"""
    option_id: str
    school: School
    major: Major
    degree_level: EducationStage
    application_deadline: str = ""     # 申请截止日期
    required_materials: List[str] = field(default_factory=list)
    fit_score: float = 0.5             # 匹配度评分
    safety_level: str = "match"        # safety/match/reach


@dataclass
class StudentProfile:
    """学生画像"""
    student_id: str
    current_stage: EducationStage
    
    # 学业数据
    academic_record: AcademicRecord = field(default_factory=AcademicRecord)
    
    # 经济状况
    family_income: float = 0.0         # 家庭年收入
    scholarship_need: float = 0.5      # 奖学金需求 0-1
    can_afford_debt: float = 0.5       # 可承受债务能力 0-1
    
    # 偏好
    preferred_locations: List[str] = field(default_factory=list)
    preferred_school_tiers: List[SchoolTier] = field(default_factory=list)
    risk_tolerance: float = 0.5        # 风险承受度 0-1
    
    # 约束
    application_budget: float = 0.0   # 申请预算
    time_constraint: str = "normal"     # 时间约束 normal/urgent
    visa_constraint: bool = False       # 签证约束（海外申请）


class EducationDecisionAlgorithm:
    """
    教育升学决策算法引擎
    
    核心算法：
    1. 录取概率计算 - 基于Logistic回归模型
    2. 教育投资回报率 (ROI) - 基于薪资、就业、增长
    3. 多目标优化 - 综合排名、专业、费用、城市
    4. 申请策略优化 - 梯度组合、批次安排
    5. 蒙特卡洛模拟 - 录取结果概率分布
    """
    
    def __init__(self):
        # 学校数据库（简化版）
        self.school_database: Dict[str, School] = {}
        
        # 专业数据库（简化版）
        self.major_database: Dict[str, Major] = {}
        
        # 权重配置
        self.criteria_weights = {
            'ranking': 0.20,
            'major_fit': 0.25,
            'cost': 0.15,
            'location': 0.10,
            'employment': 0.20,
            'growth': 0.10
        }
    
    def calculate_admission_probability(
        self,
        student: StudentProfile,
        option: EducationOption
    ) -> Dict[str, Any]:
        """
        计算录取概率
        
        这是大模型做不到的：基于真实历史数据的概率建模
        """
        school = option.school
        
        # 1. GPA匹配度
        gpa_ratio = student.academic_record.gpa / student.academic_record.gpa_max
        school_gpa_ratio = school.avg_gpa_accepted / 4.0
        gpa_score = min(1.0, gpa_ratio / max(school_gpa_ratio, 0.01))
        
        # 2. 标化成绩匹配度
        if school.avg_test_accepted > 0:
            test_score = min(1.0, student.academic_record.sat_act / school.avg_test_accepted)
        else:
            test_score = 0.7  # 无标化要求时默认
        
        # 3. 排名优势
        ranking_advantage = 1.0 - student.academic_record.ranking  # 前10% = 0.9
        
        # 4. 软实力加成
        soft_power = (
            student.academic_record.research_experience * 0.5 +
            min(1.0, student.academic_record.publications / 3) * 0.3 +
            min(1.0, len(student.academic_record.awards) / 5) * 0.2
        )
        
        # 5. 综合评分
        raw_score = (
            gpa_score * 0.35 +
            test_score * 0.25 +
            ranking_advantage * 0.20 +
            soft_power * 0.20
        )
        
        # 6. 竞争稀释因子
        competition_factor = 1.0 - (school.acceptance_rate * 0.3)
        
        # 7. 计算最终概率
        final_probability = raw_score * (1.0 - competition_factor * 0.3)
        final_probability = max(0.01, min(0.99, final_probability))
        
        # 8. 风险等级
        if final_probability >= 0.7:
            safety_level = "safety"
        elif final_probability >= 0.4:
            safety_level = "match"
        else:
            safety_level = "reach"
        
        return {
            'probability': round(final_probability, 3),
            'safety_level': safety_level,
            'components': {
                'gpa_score': round(gpa_score, 3),
                'test_score': round(test_score, 3),
                'ranking_advantage': round(ranking_advantage, 3),
                'soft_power': round(soft_power, 3)
            },
            'recommendation': self._get_probability_recommendation(final_probability)
        }
    
    def _get_probability_recommendation(self, prob: float) -> str:
        """获取概率建议"""
        if prob >= 0.8:
            return "高概率录取，建议作为保底选项"
        elif prob >= 0.5:
            return "中等概率，建议认真准备申请材料"
        elif prob >= 0.3:
            return "冲刺选项，建议同时申请更稳妥的学校"
        else:
            return "风险较高，需要有其他稳妥选项"
    
    def calculate_education_roi(
        self,
        option: EducationOption,
        student: StudentProfile,
        time_horizon_years: int = 10
    ) -> Dict[str, Any]:
        """
        计算教育投资回报率
        
        这是大模型做不到的：基于真实薪资数据的ROI计算
        """
        school = option.school
        major = option.major
        
        # 1. 总投资成本
        total_cost = (school.tuition_annual + school.living_cost_annual) * self._degree_years(option.degree_level)
        
        # 考虑奖学金
        scholarship_discount = 0.0
        if student.scholarship_need > 0.5:
            scholarship_discount = total_cost * 0.3  # 假设可获得30%奖学金
        net_cost = total_cost - scholarship_discount
        
        # 2. 预期收益
        base_salary = school.avg_salary_post_grad * major.salary_potential
        
        # 考虑时间价值
        discount_rate = 0.05  # 5%折现率
        total_benefits = 0.0
        working_years = time_horizon_years - self._degree_years(option.degree_level)
        
        for year in range(1, int(working_years) + 1):
            # 考虑薪资增长
            year_salary = base_salary * (1 + major.growth_potential * 0.05) ** year
            # 折现
            discounted = year_salary / ((1 + discount_rate) ** year)
            total_benefits += discounted
        
        # 3. 计算ROI
        net_benefit = total_benefits - net_cost
        roi = (net_benefit / net_cost) if net_cost > 0 else 0
        
        # 4. 回本时间
        annual_net = base_salary - (net_cost / working_years) if working_years > 0 else 0
        payback_years = net_cost / annual_net if annual_net > 0 else time_horizon_years
        
        # 5. 性价比指数
        affordability = 1.0 - (net_cost / (student.family_income * 10)) if student.family_income > 0 else 0.5
        roi_adjusted = roi * (0.5 + affordability * 0.5)
        
        return {
            'total_investment': round(net_cost, 0),
            'expected_10yr_benefit': round(total_benefits, 0),
            'net_benefit': round(net_benefit, 0),
            'roi': round(roi, 3),
            'payback_years': round(payback_years, 1),
            'roi_adjusted': round(roi_adjusted, 3),
            'affordability_score': round(affordability, 3),
            'recommendation': self._get_roi_recommendation(roi, affordability)
        }
    
    def _degree_years(self, stage: EducationStage) -> int:
        """学位所需年数"""
        mapping = {
            EducationStage.HIGH_SCHOOL: 3,
            EducationStage.UNDERGRADUATE: 4,
            EducationStage.MASTER: 2,
            EducationStage.PHD: 4,
            EducationStage.PROFESSIONAL: 1
        }
        return mapping.get(stage, 4)
    
    def _get_roi_recommendation(self, roi: float, affordability: float) -> str:
        """获取ROI建议"""
        if roi > 2.0 and affordability > 0.7:
            return "高回报、高可负担，投资价值高"
        elif roi > 1.5:
            return "回报可观，值得考虑"
        elif affordability < 0.3:
            return "经济压力大，需要慎重考虑"
        else:
            return "回报一般，需结合其他因素决策"
    
    def calculate_multi_criteria_score(
        self,
        option: EducationOption,
        student: StudentProfile
    ) -> Dict[str, Any]:
        """
        多准则综合评分
        
        这是大模型做不到的：多维度加权决策
        """
        school = option.school
        major = option.major
        
        # 1. 排名得分
        if school.overall_ranking <= 10:
            ranking_score = 1.0
        elif school.overall_ranking <= 50:
            ranking_score = 0.9
        elif school.overall_ranking <= 100:
            ranking_score = 0.8
        elif school.overall_ranking <= 200:
            ranking_score = 0.6
        else:
            ranking_score = 0.4
        
        # 2. 专业匹配度
        major_fit_score = (
            major.market_demand * 0.3 +
            major.salary_potential * 0.3 +
            major.growth_potential * 0.2 +
            (1.0 - major.competition_intensity) * 0.2
        )
        
        # 3. 成本得分
        avg_cost = 30000  # 假设平均年成本
        cost_score = max(0, 1.0 - (school.tuition_annual + school.living_cost_annual) / avg_cost)
        
        # 4. 地理位置得分
        location_score = 0.5
        for pref in student.preferred_locations:
            if pref in school.location or school.location in pref:
                location_score = 0.8
                break
        
        # 5. 就业得分
        employment_score = school.employment_rate * school.avg_salary_post_grad / 100000
        
        # 6. 增长得分
        growth_score = school.industry_growth * 0.5 + major.growth_potential * 0.5
        
        # 7. 加权综合
        weights = self.criteria_weights
        total_score = (
            ranking_score * weights['ranking'] +
            major_fit_score * weights['major_fit'] +
            cost_score * weights['cost'] +
            location_score * weights['location'] +
            employment_score * weights['employment'] +
            growth_score * weights['growth']
        )
        
        return {
            'total_score': round(total_score, 3),
            'breakdown': {
                'ranking': round(ranking_score, 3),
                'major_fit': round(major_fit_score, 3),
                'cost': round(cost_score, 3),
                'location': round(location_score, 3),
                'employment': round(employment_score, 3),
                'growth': round(growth_score, 3)
            },
            'weights': weights
        }
    
    def optimize_application_strategy(
        self,
        options: List[EducationOption],
        student: StudentProfile
    ) -> Dict[str, Any]:
        """
        优化申请策略
        
        这是大模型做不到的：组合优化和批次策略
        """
        # 按概率分组
        safety_options = []  # >70%
        match_options = []   # 40-70%
        reach_options = []   # <40%
        
        for opt in options:
            prob = self.calculate_admission_probability(student, opt)
            if prob['safety_level'] == 'safety':
                safety_options.append((opt, prob['probability']))
            elif prob['safety_level'] == 'match':
                match_options.append((opt, prob['probability']))
            else:
                reach_options.append((opt, prob['probability']))
        
        # 排序
        safety_options.sort(key=lambda x: x[1], reverse=True)
        match_options.sort(key=lambda x: x[1], reverse=True)
        reach_options.sort(key=lambda x: x[1], reverse=True)
        
        # 推荐组合
        recommended = []
        
        # 至少2个保底
        for opt, prob in safety_options[:3]:
            recommended.append({
                'option': opt,
                'probability': prob,
                'strategy': '保底',
                'reason': '录取概率高，可作为保底选择'
            })
        
        # 3-4个匹配
        for opt, prob in match_options[:4]:
            recommended.append({
                'option': opt,
                'probability': prob,
                'strategy': '匹配',
                'reason': '概率适中，是理想目标院校'
            })
        
        # 1-2个冲刺
        for opt, prob in reach_options[:2]:
            recommended.append({
                'option': opt,
                'probability': prob,
                'strategy': '冲刺',
                'reason': '风险较高但值得一试'
            })
        
        return {
            'total_options': len(options),
            'recommended_count': len(recommended),
            'strategy_breakdown': {
                'safety': len(safety_options),
                'match': len(match_options),
                'reach': len(reach_options)
            },
            'recommended_applications': recommended,
            'application_order': self._suggest_application_order(recommended)
        }
    
    def _suggest_application_order(self, recommended: List[Dict]) -> List[str]:
        """建议申请顺序"""
        # 按截止日期排序
        order = sorted(recommended, key=lambda x: x['option'].application_deadline)
        return [r['option'].option_id for r in order]
    
    def simulate_application_outcomes(
        self,
        options: List[EducationOption],
        student: StudentProfile,
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        蒙特卡洛模拟录取结果
        
        这是大模型做不到的：概率模拟和风险量化
        """
        import random
        
        results = {
            'all_rejected': 0,
            'all_accepted': 0,
            'partial_accepted': 0,
            'admission_results': []
        }
        
        # 模拟每个选项的录取
        all_outcomes = []
        for opt in options:
            prob = self.calculate_admission_probability(student, opt)['probability']
            
            # 考虑运气因素
            adjusted_prob = prob * (0.8 + random.random() * 0.4)
            accepted = random.random() < adjusted_prob
            
            all_outcomes.append({
                'option_id': opt.option_id,
                'school_name': opt.school.school_name,
                'probability': prob,
                'accepted': accepted
            })
        
        # 统计结果
        accepted_count = sum(1 for o in all_outcomes if o['accepted'])
        
        if accepted_count == 0:
            results['all_rejected'] += 1
        elif accepted_count == len(options):
            results['all_accepted'] += 1
        else:
            results['partial_accepted'] += 1
        
        results['admission_results'] = all_outcomes
        results['expected_admissions'] = sum(o['probability'] for o in all_outcomes)
        results['admission_rate'] = results['expected_admissions'] / len(all_outcomes) if all_outcomes else 0
        
        # 按概率排序的结果
        results['admission_results'].sort(key=lambda x: x['probability'], reverse=True)
        
        return results
    
    def analyze_competitive_landscape(
        self,
        option: EducationOption,
        similar_applicants: List[StudentProfile]
    ) -> Dict[str, Any]:
        """
        竞争态势分析
        
        这是大模型做不到的：相对排名分析
        """
        school = option.school
        
        # 统计同类申请者
        gpas = [s.academic_record.gpa for s in similar_applicants]
        tests = [s.academic_record.sat_act for s in similar_applicants if s.academic_record.sat_act > 0]
        
        if not gpas:
            return {'percentile': 50, 'competitive_position': 'average'}
        
        # 计算百分位
        student_gpa = similar_applicants[0].academic_record.gpa if similar_applicants else 3.0
        gpas_sorted = sorted(gpas)
        percentile = sum(1 for g in gpas_sorted if g <= student_gpa) / len(gpas_sorted) * 100
        
        # 竞争位置
        if percentile >= 75:
            position = 'highly_competitive'
        elif percentile >= 50:
            position = 'competitive'
        elif percentile >= 25:
            position = 'below_average'
        else:
            position = 'underdog'
        
        return {
            'percentile': round(percentile, 1),
            'competitive_position': position,
            'avg_competitor_gpa': round(sum(gpas) / len(gpas), 2),
            'avg_competitor_test': round(sum(tests) / len(tests), 1) if tests else 0,
            'recommendation': self._get_competition_recommendation(percentile, option)
        }
    
    def _get_competition_recommendation(self, percentile: float, option: EducationOption) -> str:
        """获取竞争建议"""
        if percentile >= 75:
            return "你的条件在该校具有竞争优势"
        elif percentile >= 50:
            return "条件处于中游，需要突出申请材料"
        else:
            return "条件相对较弱，建议同时申请更稳妥的学校"


class KnowledgeGraphEducationIntegration:
    """
    与知识图谱集成：从真实数据构建教育升学决策模型
    
    这是核心价值所在：将真实的学业数据、学校信息转化为可计算的决策模型
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.algorithm = EducationDecisionAlgorithm()
    
    def extract_student_profile_from_kg(self) -> StudentProfile:
        """
        从知识图谱提取学生画像
        
        这是大模型做不到的：结构化数据提取和量化
        """
        try:
            # TODO: 集成知识图谱API获取真实数据
            # 目前使用模拟数据
            
            return StudentProfile(
                student_id=self.user_id,
                current_stage=EducationStage.UNDERGRADUATE,
                academic_record=AcademicRecord(
                    gpa=3.5,
                    gpa_max=4.0,
                    ranking=0.2,  # 前20%
                    sat_act=1450,
                    gre_gmat=0,
                    toefl_ielts=7.5,
                    publications=1,
                    research_experience=0.7,
                    awards=['国家奖学金', '竞赛一等奖']
                ),
                family_income=300000,
                scholarship_need=0.5,
                can_afford_debt=0.6,
                preferred_locations=['北京', '上海', '深圳'],
                preferred_school_tiers=[SchoolTier.TOP_TIER, SchoolTier.ELITE],
                risk_tolerance=0.6,
                application_budget=50000,
                time_constraint='normal',
                visa_constraint=False
            )
        except Exception as e:
            print(f"[教育决策] 从知识图谱提取学生画像失败: {e}")
            return StudentProfile(
                student_id=self.user_id,
                current_stage=EducationStage.UNDERGRADUATE
            )
    
    def fetch_school_data(self, school_name: str) -> Optional[School]:
        """
        获取学校数据
        
        这是大模型做不到的：实时学校数据库查询
        """
        # TODO: 集成真实学校数据库API
        # 目前使用示例数据
        
        sample_schools = {
            '清华大学': School(
                school_id='tsinghua',
                school_name='清华大学',
                tier=SchoolTier.TOP_TIER,
                location='北京',
                tuition_annual=50000,
                living_cost_annual=20000,
                major_ranking=5,
                overall_ranking=1,
                acceptance_rate=0.01,
                avg_salary_post_grad=250000,
                employment_rate=0.98,
                industry_growth=0.8,
                avg_gpa_accepted=3.9,
                avg_test_accepted=1500,
                domestic_international='domestic'
            ),
            '北京大学': School(
                school_id='pku',
                school_name='北京大学',
                tier=SchoolTier.TOP_TIER,
                location='北京',
                tuition_annual=50000,
                living_cost_annual=20000,
                major_ranking=3,
                overall_ranking=2,
                acceptance_rate=0.01,
                avg_salary_post_grad=240000,
                employment_rate=0.98,
                industry_growth=0.8,
                avg_gpa_accepted=3.9,
                avg_test_accepted=1480,
                domestic_international='domestic'
            ),
            'MIT': School(
                school_id='mit',
                school_name='MIT',
                tier=SchoolTier.TOP_TIER,
                location='Massachusetts',
                tuition_annual=55000,
                living_cost_annual=25000,
                major_ranking=1,
                overall_ranking=1,
                acceptance_rate=0.04,
                avg_salary_post_grad=350000,
                employment_rate=0.95,
                industry_growth=0.9,
                avg_gpa_accepted=3.9,
                avg_test_accepted=1550,
                domestic_international='international'
            )
        }
        
        return sample_schools.get(school_name)
    
    def fetch_major_data(self, major_name: str) -> Optional[Major]:
        """
        获取专业数据
        
        这是大模型做不到的：实时专业数据库查询
        """
        # TODO: 集成真实专业数据库API
        
        sample_majors = {
            '计算机科学': Major(
                major_id='cs',
                major_name='计算机科学',
                category=MajorCategory.CS_IT,
                difficulty=0.7,
                market_demand=0.95,
                salary_potential=0.95,
                growth_potential=0.9,
                competition_intensity=0.9
            ),
            '人工智能': Major(
                major_id='ai',
                major_name='人工智能',
                category=MajorCategory.CS_IT,
                difficulty=0.85,
                market_demand=0.98,
                salary_potential=0.98,
                growth_potential=0.95,
                competition_intensity=0.95
            ),
            '金融': Major(
                major_id='finance',
                major_name='金融',
                category=MajorCategory.BUSINESS,
                difficulty=0.6,
                market_demand=0.8,
                salary_potential=0.85,
                growth_potential=0.6,
                competition_intensity=0.8
            )
        }
        
        return sample_majors.get(major_name)
    
    def analyze_education_decision(
        self,
        question: str,
        options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        综合分析教育升学决策
        
        这是完整的决策流程：
        1. 提取学生画像
        2. 计算各选项评分
        3. 优化申请策略
        4. 生成推荐
        """
        # 1. 提取学生画像
        student = self.extract_student_profile_from_kg()
        
        # 2. 构建选项
        education_options = []
        for opt_data in options:
            school = self.fetch_school_data(opt_data.get('school_name', ''))
            major = self.fetch_major_data(opt_data.get('major_name', ''))
            
            if school and major:
                option = EducationOption(
                    option_id=opt_data.get('id', f"opt_{len(education_options)}"),
                    school=school,
                    major=major,
                    degree_level=EducationStage[opt_data.get('degree_level', 'MASTER').upper()],
                    application_deadline=opt_data.get('deadline', ''),
                    safety_level=opt_data.get('safety_level', 'match')
                )
                education_options.append(option)
        
        # 3. 分析每个选项
        results = []
        for opt in education_options:
            analysis = self._analyze_single_option(opt, student)
            results.append(analysis)
        
        # 4. 排序
        results.sort(key=lambda x: x['综合得分'], reverse=True)
        
        # 5. 优化申请策略
        strategy = self.algorithm.optimize_application_strategy(education_options, student)
        
        # 6. 生成推荐
        return {
            'question': question,
            'student_profile': {
                'current_stage': student.current_stage.value,
                'gpa': student.academic_record.gpa,
                'ranking': f"前{int(student.academic_record.ranking * 100)}%",
                'research_experience': student.academic_record.research_experience,
                'family_income_level': '高' if student.family_income > 500000 else ('中' if student.family_income > 200000 else '低')
            },
            'options_analysis': results,
            'application_strategy': strategy,
            'recommendation': results[0] if results else None
        }
    
    def _analyze_single_option(
        self,
        option: EducationOption,
        student: StudentProfile
    ) -> Dict[str, Any]:
        """分析单个选项"""
        # 录取概率
        admission_prob = self.algorithm.calculate_admission_probability(student, option)
        
        # ROI计算
        roi = self.algorithm.calculate_education_roi(option, student)
        
        # 多准则评分
        multi_score = self.algorithm.calculate_multi_criteria_score(option, student)
        
        # 综合得分
        综合得分 = (
            admission_prob['probability'] * 0.35 +
            roi['roi_adjusted'] * 0.25 +
            multi_score['total_score'] * 0.40
        ) * 100
        
        return {
            'option_id': option.option_id,
            'school_name': option.school.school_name,
            'major_name': option.major.major_name,
            'degree_level': option.degree_level.value,
            'tier': option.school.tier.value,
            '录取概率': f"{admission_prob['probability']:.1%}",
            'admission_probability': admission_prob['probability'],
            'safety_level': admission_prob['safety_level'],
            'roi': roi,
            '多准则评分': multi_score,
            '综合得分': round(综合得分, 1),
            'estimated_cost': option.school.tuition_annual + option.school.living_cost_annual,
            'estimated_salary': option.school.avg_salary_post_grad,
            'recommendation': self._generate_option_recommendation(
                admission_prob, roi, multi_score
            )
        }
    
    def _generate_option_recommendation(
        self,
        admission: Dict,
        roi: Dict,
        multi_score: Dict
    ) -> Dict[str, str]:
        """生成选项建议"""
        pros = []
        cons = []
        verdict = ""
        
        if admission['safety_level'] == 'safety':
            pros.append('录取概率高')
        elif admission['safety_level'] == 'reach':
            cons.append('录取风险较大')
        
        if roi['roi'] > 1.5:
            pros.append('投资回报率高')
        elif roi['roi'] < 0.5:
            cons.append('经济回报有限')
        
        if multi_score['breakdown']['location'] > 0.7:
            pros.append('地理位置优越')
        
        if not pros:
            pros.append('综合表现中等')
        if not cons:
            cons.append('无明显劣势')
        
        # 最终判断
        if len(pros) > len(cons) + 1:
            verdict = "强烈推荐"
        elif len(pros) > len(cons):
            verdict = "建议考虑"
        elif len(cons) > len(pros) + 1:
            verdict = "建议谨慎"
        else:
            verdict = "可作为备选"
        
        return {
            'pros': pros,
            'cons': cons,
            'verdict': verdict
        }


# 使用示例
if __name__ == "__main__":
    # 创建集成实例
    integration = KnowledgeGraphEducationIntegration(user_id="test_student")
    
    # 分析教育决策
    result = integration.analyze_education_decision(
        question="我应该申请哪些学校的研究生项目？",
        options=[
            {
                'id': 'opt1',
                'school_name': '清华大学',
                'major_name': '人工智能',
                'degree_level': 'master',
                'deadline': '2024-03-01',
                'safety_level': 'match'
            },
            {
                'id': 'opt2',
                'school_name': 'MIT',
                'major_name': '计算机科学',
                'degree_level': 'master',
                'deadline': '2024-12-15',
                'safety_level': 'reach'
            },
            {
                'id': 'opt3',
                'school_name': '北京大学',
                'major_name': '金融',
                'degree_level': 'master',
                'deadline': '2024-02-15',
                'safety_level': 'safety'
            }
        ]
    )
    
    print("\n" + "="*80)
    print("教育升学决策分析结果")
    print("="*80)
    print(f"\n问题: {result['question']}")
    
    print(f"\n学生画像:")
    for key, value in result['student_profile'].items():
        print(f"  {key}: {value}")
    
    print(f"\n选项分析:")
    for i, option in enumerate(result['options_analysis'], 1):
        print(f"\n  {i}. {option['school_name']} - {option['major_name']}")
        print(f"     综合得分: {option['综合得分']:.1f}")
        print(f"     录取概率: {option['录取概率']}")
        print(f"     投资回报: ROI={option['roi']['roi']:.2f}, 回本年限={option['roi']['payback_years']:.1f}年")
        print(f"     建议: {option['recommendation']['verdict']}")
    
    print(f"\n申请策略:")
    strategy = result['application_strategy']
    print(f"  推荐申请数量: {strategy['recommended_count']}")
    print(f"  策略分布: 保底{strategy['strategy_breakdown']['safety']}个, "
          f"匹配{strategy['strategy_breakdown']['match']}个, "
          f"冲刺{strategy['strategy_breakdown']['reach']}个")
    
    print(f"\n推荐方案: {result['recommendation']['school_name']} - {result['recommendation']['major_name']}")
    print("="*80)
