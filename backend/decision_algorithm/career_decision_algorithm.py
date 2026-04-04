"""
职业决策算法引擎
基于职业发展理论、人力资本理论、网络理论的量化决策系统

核心价值：
1. 长期路径模拟（5-10年）- 大模型做不到的时间跨度推演
2. 量化技能投资回报率 - 基于真实市场数据
3. 职业网络分析 - 基于图论的转换可行性
4. 个人资本综合评估 - 多维度资本模型
5. 时间价值折现 - 考虑年龄、机会窗口
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from datetime import datetime, timedelta


class CareerStage(Enum):
    """职业阶段"""
    ENTRY = "entry"              # 入门期 (0-2年)
    GROWTH = "growth"            # 成长期 (3-5年)
    MATURE = "mature"            # 成熟期 (6-10年)
    EXPERT = "expert"            # 专家期 (10+年)
    TRANSITION = "transition"    # 转型期


class CapitalType(Enum):
    """资本类型"""
    HUMAN = "human"              # 人力资本（技能、知识、经验）
    SOCIAL = "social"            # 社会资本（人脉、声誉、影响力）
    PSYCHOLOGICAL = "psychological"  # 心理资本（自信、韧性、乐观）
    ECONOMIC = "economic"        # 经济资本（储蓄、资产）


@dataclass
class Skill:
    """技能"""
    name: str
    level: float  # 0-10
    market_demand: float  # 市场需求度 0-1
    decay_rate: float = 0.1  # 年衰减率
    learning_curve: float = 0.5  # 学习曲线陡峭度
    transferability: float = 0.5  # 可迁移性
    
    def calculate_market_value(self, years_experience: float) -> float:
        """计算市场价值"""
        # 考虑经验、市场需求、衰减
        experience_factor = min(1.0, years_experience / 5.0)
        decay_factor = math.exp(-self.decay_rate * years_experience)
        return self.level * self.market_demand * experience_factor * decay_factor


@dataclass
class CareerPath:
    """职业路径"""
    path_id: str
    current_role: str
    target_role: str
    intermediate_roles: List[str] = field(default_factory=list)
    
    # 路径特征
    total_duration_months: int = 36  # 总时长（月）
    success_probability: float = 0.5  # 成功概率
    required_skills: List[Skill] = field(default_factory=list)
    skill_gap: Dict[str, float] = field(default_factory=dict)
    
    # 成本收益
    learning_cost_hours: int = 0  # 学习成本（小时）
    opportunity_cost: float = 0.0  # 机会成本
    expected_salary_increase: float = 0.0  # 预期薪资增长
    
    # 风险因素
    market_volatility: float = 0.3  # 市场波动性
    role_stability: float = 0.7  # 角色稳定性
    industry_growth: float = 0.5  # 行业增长率


@dataclass
class PersonalCapital:
    """个人资本"""
    # 人力资本
    skills: List[Skill] = field(default_factory=list)
    years_experience: float = 0.0
    education_level: int = 3  # 1-5 (高中-博士)
    certifications: List[str] = field(default_factory=list)
    
    # 社会资本
    network_size: int = 0
    network_quality: float = 0.5  # 0-1
    industry_reputation: float = 0.5  # 0-1
    mentor_quality: float = 0.0  # 0-1
    
    # 心理资本
    self_efficacy: float = 0.7  # 自我效能感
    resilience: float = 0.7  # 韧性
    optimism: float = 0.7  # 乐观度
    adaptability: float = 0.7  # 适应性
    
    # 经济资本
    savings: float = 0.0
    monthly_expenses: float = 0.0
    financial_runway_months: float = 6.0  # 财务跑道
    
    def calculate_human_capital_score(self) -> float:
        """计算人力资本得分"""
        skill_score = sum(s.calculate_market_value(self.years_experience) for s in self.skills) / max(len(self.skills), 1)
        experience_score = min(1.0, self.years_experience / 10.0)
        education_score = self.education_level / 5.0
        cert_score = min(1.0, len(self.certifications) / 5.0)
        
        return (skill_score * 0.4 + experience_score * 0.3 + 
                education_score * 0.2 + cert_score * 0.1)
    
    def calculate_social_capital_score(self) -> float:
        """计算社会资本得分"""
        network_score = min(1.0, self.network_size / 500.0) * self.network_quality
        reputation_score = self.industry_reputation
        mentor_score = self.mentor_quality
        
        return (network_score * 0.4 + reputation_score * 0.4 + mentor_score * 0.2)
    
    def calculate_psychological_capital_score(self) -> float:
        """计算心理资本得分"""
        return (self.self_efficacy * 0.3 + self.resilience * 0.3 + 
                self.optimism * 0.2 + self.adaptability * 0.2)
    
    def calculate_economic_capital_score(self) -> float:
        """计算经济资本得分"""
        runway_score = min(1.0, self.financial_runway_months / 12.0)
        savings_score = min(1.0, self.savings / (self.monthly_expenses * 24))
        return (runway_score * 0.6 + savings_score * 0.4)


class CareerDecisionAlgorithm:
    """
    职业决策算法引擎
    
    核心算法：
    1. 马尔可夫决策过程 (MDP) - 路径规划
    2. 技能投资回报率 (ROI) - 学习价值
    3. 图论算法 - 职业网络分析
    4. 蒙特卡洛模拟 - 风险评估
    5. 动态规划 - 最优路径
    """
    
    def __init__(self):
        # 职业转换图（邻接矩阵）
        self.career_graph: Dict[str, List[Tuple[str, float]]] = {}
        
        # 技能市场数据
        self.skill_market_data: Dict[str, Dict[str, float]] = {}
        
        # 行业数据
        self.industry_data: Dict[str, Dict[str, float]] = {}
        
        # 时间折现率
        self.discount_rate = 0.05  # 年化5%
        
        # 风险厌恶系数
        self.risk_aversion = 0.5  # 0-1，越高越厌恶风险
    
    def calculate_skill_roi(
        self,
        skill: Skill,
        learning_hours: int,
        current_salary: float,
        target_salary: float,
        time_horizon_years: int = 5
    ) -> Dict[str, float]:
        """
        计算技能学习的投资回报率
        
        这是大模型做不到的：基于真实数据的量化计算
        """
        # 学习成本
        hourly_cost = current_salary / (40 * 52)  # 假设周工作40小时
        learning_cost = learning_hours * hourly_cost
        
        # 预期收益（考虑时间折现）
        salary_increase = target_salary - current_salary
        discounted_benefits = []
        
        for year in range(1, time_horizon_years + 1):
            # 考虑技能衰减
            skill_value_factor = math.exp(-skill.decay_rate * year)
            # 考虑市场需求变化
            market_factor = 1 + (skill.market_demand - 0.5) * 0.1 * year
            # 时间折现
            discount_factor = 1 / ((1 + self.discount_rate) ** year)
            
            annual_benefit = salary_increase * skill_value_factor * market_factor * discount_factor
            discounted_benefits.append(annual_benefit)
        
        total_benefit = sum(discounted_benefits)
        net_benefit = total_benefit - learning_cost
        roi = (net_benefit / learning_cost) if learning_cost > 0 else 0
        
        # 计算回本时间
        cumulative = 0
        payback_years = time_horizon_years
        for year, benefit in enumerate(discounted_benefits, 1):
            cumulative += benefit
            if cumulative >= learning_cost:
                payback_years = year
                break
        
        return {
            'learning_cost': learning_cost,
            'total_benefit': total_benefit,
            'net_benefit': net_benefit,
            'roi': roi,
            'payback_years': payback_years,
            'annual_benefits': discounted_benefits
        }
    
    def simulate_career_path(
        self,
        path: CareerPath,
        personal_capital: PersonalCapital,
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        蒙特卡洛模拟职业路径
        
        这是大模型做不到的：概率模拟和风险量化
        """
        success_count = 0
        salary_outcomes = []
        time_outcomes = []
        
        for _ in range(num_simulations):
            # 模拟成功概率（考虑个人资本）
            base_success_prob = path.success_probability
            
            # 人力资本加成
            human_capital_bonus = personal_capital.calculate_human_capital_score() * 0.2
            # 社会资本加成
            social_capital_bonus = personal_capital.calculate_social_capital_score() * 0.15
            # 心理资本加成
            psychological_bonus = personal_capital.calculate_psychological_capital_score() * 0.15
            
            adjusted_success_prob = min(0.95, base_success_prob + human_capital_bonus + 
                                       social_capital_bonus + psychological_bonus)
            
            # 模拟是否成功
            import random
            if random.random() < adjusted_success_prob:
                success_count += 1
                
                # 模拟薪资结果（正态分布）
                salary_mean = path.expected_salary_increase
                salary_std = salary_mean * path.market_volatility
                salary_outcome = random.gauss(salary_mean, salary_std)
                salary_outcomes.append(max(0, salary_outcome))
                
                # 模拟时间结果
                time_mean = path.total_duration_months
                time_std = time_mean * 0.2
                time_outcome = random.gauss(time_mean, time_std)
                time_outcomes.append(max(time_mean * 0.5, time_outcome))
        
        # 统计结果
        success_rate = success_count / num_simulations
        
        if salary_outcomes:
            avg_salary = sum(salary_outcomes) / len(salary_outcomes)
            salary_p10 = sorted(salary_outcomes)[int(len(salary_outcomes) * 0.1)]
            salary_p50 = sorted(salary_outcomes)[int(len(salary_outcomes) * 0.5)]
            salary_p90 = sorted(salary_outcomes)[int(len(salary_outcomes) * 0.9)]
        else:
            avg_salary = salary_p10 = salary_p50 = salary_p90 = 0
        
        if time_outcomes:
            avg_time = sum(time_outcomes) / len(time_outcomes)
            time_p10 = sorted(time_outcomes)[int(len(time_outcomes) * 0.1)]
            time_p90 = sorted(time_outcomes)[int(len(time_outcomes) * 0.9)]
        else:
            avg_time = time_p10 = time_p90 = path.total_duration_months
        
        return {
            'success_rate': success_rate,
            'salary_outcomes': {
                'mean': avg_salary,
                'p10': salary_p10,
                'median': salary_p50,
                'p90': salary_p90
            },
            'time_outcomes': {
                'mean_months': avg_time,
                'best_case_months': time_p10,
                'worst_case_months': time_p90
            },
            'risk_adjusted_value': avg_salary * success_rate
        }
    
    def find_optimal_path_dynamic_programming(
        self,
        current_role: str,
        target_role: str,
        personal_capital: PersonalCapital,
        max_steps: int = 5
    ) -> Tuple[List[str], float]:
        """
        动态规划找最优职业路径
        
        这是大模型做不到的：全局最优解搜索
        
        Returns:
            (最优路径, 总价值)
        """
        # 状态: (当前角色, 已用步数) -> (最大价值, 路径)
        dp: Dict[Tuple[str, int], Tuple[float, List[str]]] = {}
        
        # 初始状态
        dp[(current_role, 0)] = (0.0, [current_role])
        
        # 动态规划
        for step in range(max_steps):
            for (role, s), (value, path) in list(dp.items()):
                if s != step:
                    continue
                
                # 尝试所有可能的下一步
                next_roles = self.career_graph.get(role, [])
                for next_role, transition_prob in next_roles:
                    # 计算转换价值
                    transition_value = self._calculate_transition_value(
                        role, next_role, personal_capital
                    )
                    
                    new_value = value + transition_value * transition_prob
                    new_path = path + [next_role]
                    
                    # 更新最优解
                    key = (next_role, step + 1)
                    if key not in dp or new_value > dp[key][0]:
                        dp[key] = (new_value, new_path)
        
        # 找到目标角色的最优路径
        best_value = -float('inf')
        best_path = []
        
        for (role, steps), (value, path) in dp.items():
            if role == target_role and value > best_value:
                best_value = value
                best_path = path
        
        return best_path, best_value
    
    def _calculate_transition_value(
        self,
        from_role: str,
        to_role: str,
        personal_capital: PersonalCapital
    ) -> float:
        """计算职业转换的价值"""
        # 基础价值（假设有薪资数据）
        base_value = 1.0
        
        # 技能匹配度加成
        skill_match = personal_capital.calculate_human_capital_score()
        
        # 社会资本加成
        social_bonus = personal_capital.calculate_social_capital_score() * 0.5
        
        return base_value * (1 + skill_match + social_bonus)
    
    def calculate_career_network_centrality(
        self,
        role: str,
        graph: Dict[str, List[Tuple[str, float]]]
    ) -> Dict[str, float]:
        """
        计算职业在网络中的中心性
        
        这是大模型做不到的：图论算法
        """
        # 度中心性
        degree = len(graph.get(role, []))
        
        # PageRank 中心性（简化版）
        pagerank = self._calculate_pagerank(role, graph)
        
        # 介数中心性（计算量大，简化）
        betweenness = self._estimate_betweenness(role, graph)
        
        return {
            'degree_centrality': degree,
            'pagerank': pagerank,
            'betweenness': betweenness,
            'composite_score': (degree * 0.3 + pagerank * 0.4 + betweenness * 0.3)
        }
    
    def _calculate_pagerank(
        self,
        role: str,
        graph: Dict[str, List[Tuple[str, float]]],
        damping: float = 0.85,
        iterations: int = 20
    ) -> float:
        """计算 PageRank"""
        nodes = list(graph.keys())
        n = len(nodes)
        if n == 0:
            return 0.0
        
        # 初始化
        ranks = {node: 1.0 / n for node in nodes}
        
        # 迭代
        for _ in range(iterations):
            new_ranks = {}
            for node in nodes:
                rank_sum = 0.0
                # 找所有指向该节点的边
                for source, targets in graph.items():
                    for target, weight in targets:
                        if target == node:
                            out_degree = len(graph.get(source, []))
                            if out_degree > 0:
                                rank_sum += ranks[source] / out_degree
                
                new_ranks[node] = (1 - damping) / n + damping * rank_sum
            
            ranks = new_ranks
        
        return ranks.get(role, 0.0)
    
    def _estimate_betweenness(
        self,
        role: str,
        graph: Dict[str, List[Tuple[str, float]]]
    ) -> float:
        """估算介数中心性（简化版）"""
        # 简化：计算有多少路径经过该节点
        count = 0
        nodes = list(graph.keys())
        
        for source in nodes[:10]:  # 限制计算量
            for target in nodes[:10]:
                if source == target or source == role or target == role:
                    continue
                
                # 简单BFS检查是否经过role
                if self._path_goes_through(source, target, role, graph):
                    count += 1
        
        return count / max(len(nodes), 1)
    
    def _path_goes_through(
        self,
        source: str,
        target: str,
        intermediate: str,
        graph: Dict[str, List[Tuple[str, float]]]
    ) -> bool:
        """检查从source到target的路径是否经过intermediate"""
        # 简化：只检查2步路径
        neighbors = [n for n, _ in graph.get(source, [])]
        if intermediate in neighbors:
            intermediate_neighbors = [n for n, _ in graph.get(intermediate, [])]
            if target in intermediate_neighbors:
                return True
        return False


class KnowledgeGraphCareerIntegration:
    """
    与知识图谱集成：从真实数据构建职业决策模型
    
    这是核心价值所在：将真实的技能、岗位、公司数据转化为可计算的决策模型
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.algorithm = CareerDecisionAlgorithm()
    
    def extract_personal_capital_from_kg(self) -> PersonalCapital:
        """
        从知识图谱提取个人资本
        
        这是大模型做不到的：结构化数据提取和量化
        """
        try:
            from backend.decision.personal_knowledge_fusion import PersonalFactExtractor
            
            # 提取个人事实
            extractor = PersonalFactExtractor(self.user_id)
            facts = extractor.extract_all()
            
            # 解析技能
            skills = []
            for fact in facts:
                if '技能' in fact.relation or 'skill' in fact.relation.lower():
                    # 从知识图谱获取技能详情
                    skill = Skill(
                        name=fact.obj,
                        level=7.0,  # 默认，可从图谱获取
                        market_demand=0.7,  # 可从市场数据获取
                        decay_rate=0.1,
                        learning_curve=0.5,
                        transferability=0.6
                    )
                    skills.append(skill)
            
            # 解析经验年限
            years_exp = 0.0
            for fact in facts:
                if '工作' in fact.relation or '经验' in fact.relation:
                    # 尝试提取年限
                    import re
                    match = re.search(r'(\d+)年', fact.obj)
                    if match:
                        years_exp = float(match.group(1))
            
            # 解析人脉
            network_size = 0
            for fact in facts:
                if '认识' in fact.relation:
                    network_size += 1
            
            # 解析财务状况
            savings = 0.0
            monthly_expenses = 5000.0  # 默认
            for fact in facts:
                if '薪资' in fact.relation or '月薪' in fact.relation:
                    import re
                    match = re.search(r'(\d+)[kK]', fact.obj)
                    if match:
                        monthly_salary = float(match.group(1)) * 1000
                        savings = monthly_salary * 6  # 假设有6个月储蓄
                        monthly_expenses = monthly_salary * 0.6
            
            return PersonalCapital(
                skills=skills,
                years_experience=years_exp,
                education_level=3,
                certifications=[],
                network_size=network_size,
                network_quality=0.6,
                industry_reputation=0.5,
                mentor_quality=0.3,
                self_efficacy=0.7,
                resilience=0.7,
                optimism=0.7,
                adaptability=0.7,
                savings=savings,
                monthly_expenses=monthly_expenses,
                financial_runway_months=savings / monthly_expenses if monthly_expenses > 0 else 6.0
            )
        
        except Exception as e:
            print(f"[职业决策] 从知识图谱提取个人资本失败: {e}")
            return PersonalCapital()
    
    def build_career_graph_from_real_data(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        从真实岗位数据构建职业转换图
        
        这是大模型做不到的：基于真实数据的网络构建
        """
        # TODO: 集成真实岗位API
        # 这里先用示例数据
        career_graph = {
            "初级后端工程师": [
                ("中级后端工程师", 0.8),
                ("全栈工程师", 0.5),
                ("技术支持", 0.3)
            ],
            "中级后端工程师": [
                ("高级后端工程师", 0.7),
                ("架构师", 0.4),
                ("技术经理", 0.5),
                ("产品经理", 0.3)
            ],
            "高级后端工程师": [
                ("架构师", 0.8),
                ("技术专家", 0.7),
                ("技术总监", 0.5)
            ],
            "产品经理": [
                ("高级产品经理", 0.7),
                ("产品总监", 0.4),
                ("创业", 0.2)
            ]
        }
        
        self.algorithm.career_graph = career_graph
        return career_graph
    
    def fetch_market_skill_data(self, skill_name: str) -> Dict[str, float]:
        """
        获取技能的市场数据
        
        这是大模型做不到的：实时市场数据查询
        """
        # TODO: 集成真实招聘API（如拉勾、Boss直聘）
        # 返回：需求度、平均薪资、增长趋势
        
        # 示例数据
        market_data = {
            "Python": {"demand": 0.9, "avg_salary": 25000, "growth_rate": 0.15},
            "Java": {"demand": 0.85, "avg_salary": 23000, "growth_rate": 0.08},
            "Go": {"demand": 0.75, "avg_salary": 28000, "growth_rate": 0.25},
            "Kubernetes": {"demand": 0.8, "avg_salary": 30000, "growth_rate": 0.3},
            "React": {"demand": 0.85, "avg_salary": 22000, "growth_rate": 0.12}
        }
        
        return market_data.get(skill_name, {"demand": 0.5, "avg_salary": 15000, "growth_rate": 0.05})

    def calculate_career_decision_score(
        self,
        option_title: str = "",
        current_month: int = 1
    ) -> Dict[str, Any]:
        """
        计算职业决策评分（用于推演中的月度评分）

        这是职业决策算法在实时推演中的应用：
        1. 提取个人资本
        2. 计算各维度得分
        3. 综合评分

        Args:
            option_title: 选项标题
            current_month: 当前月份

        Returns:
            {
                'total_score': 综合评分,
                'human_capital': 人力资本得分,
                'social_capital': 社会资本得分,
                'psychological_capital': 心理资本得分,
                'economic_capital': 经济资本得分,
                'market_environment': 市场环境得分
            }
        """
        # 提取个人资本
        personal_capital = self.extract_personal_capital_from_kg()

        # 计算各维度得分
        human_score = personal_capital.calculate_human_capital_score() * 100
        social_score = personal_capital.calculate_social_capital_score() * 100
        psychological_score = personal_capital.calculate_psychological_capital_score() * 100
        economic_score = personal_capital.calculate_economic_capital_score() * 100

        # 市场环境（简化估算，随月份变化）
        market_base = 60.0
        market_score = market_base + (current_month - 1) * 0.5  # 随时间缓慢变化

        # 综合评分（加权平均）
        weights = {
            'human_capital': 0.30,
            'social_capital': 0.20,
            'psychological_capital': 0.15,
            'economic_capital': 0.20,
            'market_environment': 0.15
        }

        total_score = (
            human_score * weights['human_capital'] +
            social_score * weights['social_capital'] +
            psychological_score * weights['psychological_capital'] +
            economic_score * weights['economic_capital'] +
            market_score * weights['market_environment']
        )

        return {
            'total_score': round(total_score, 1),
            'human_capital': round(human_score, 1),
            'social_capital': round(social_score, 1),
            'psychological_capital': round(psychological_score, 1),
            'economic_capital': round(economic_score, 1),
            'market_environment': round(market_score, 1),
            'option_title': option_title,
            'current_month': current_month
        }

    def analyze_career_decision(
        self,
        question: str,
        options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        综合分析职业决策
        
        这是完整的决策流程：
        1. 提取个人资本
        2. 构建职业网络
        3. 模拟各选项
        4. 量化对比
        """
        # 1. 提取个人资本
        personal_capital = self.extract_personal_capital_from_kg()
        
        # 2. 构建职业网络
        career_graph = self.build_career_graph_from_real_data()
        
        # 3. 分析每个选项
        results = []
        for option in options:
            option_analysis = self._analyze_single_option(
                option, personal_capital, career_graph
            )
            results.append(option_analysis)
        
        # 4. 排序和推荐
        results.sort(key=lambda x: x['综合得分'], reverse=True)
        
        return {
            'question': question,
            'personal_capital_summary': {
                'human_capital': personal_capital.calculate_human_capital_score(),
                'social_capital': personal_capital.calculate_social_capital_score(),
                'psychological_capital': personal_capital.calculate_psychological_capital_score(),
                'economic_capital': personal_capital.calculate_economic_capital_score()
            },
            'options_analysis': results,
            'recommendation': results[0] if results else None
        }
    
    def _analyze_single_option(
        self,
        option: Dict[str, Any],
        personal_capital: PersonalCapital,
        career_graph: Dict[str, List[Tuple[str, float]]]
    ) -> Dict[str, Any]:
        """分析单个选项"""
        # 构建路径
        path = CareerPath(
            path_id=option.get('id', 'opt1'),
            current_role=option.get('current_role', '当前岗位'),
            target_role=option.get('target_role', '目标岗位'),
            total_duration_months=option.get('duration_months', 36),
            success_probability=option.get('success_prob', 0.6),
            expected_salary_increase=option.get('salary_increase', 5000),
            market_volatility=option.get('volatility', 0.3)
        )
        
        # 蒙特卡洛模拟
        simulation_result = self.algorithm.simulate_career_path(
            path, personal_capital, num_simulations=1000
        )
        
        # 计算网络中心性
        centrality = self.algorithm.calculate_career_network_centrality(
            path.target_role, career_graph
        )
        
        # 综合评分
        success_score = simulation_result['success_rate'] * 100
        salary_score = min(100, simulation_result['salary_outcomes']['mean'] / 100)
        network_score = centrality['composite_score'] * 100
        
        综合得分 = (success_score * 0.4 + salary_score * 0.3 + network_score * 0.3)
        
        return {
            'option_id': option.get('id'),
            'option_title': option.get('title', ''),
            '成功率': f"{simulation_result['success_rate']:.1%}",
            '预期薪资增长': simulation_result['salary_outcomes'],
            '预期时间': simulation_result['time_outcomes'],
            '风险调整价值': simulation_result['risk_adjusted_value'],
            '职业网络价值': centrality,
            '综合得分': 综合得分,
            '详细分析': {
                'human_capital_match': personal_capital.calculate_human_capital_score(),
                'social_capital_advantage': personal_capital.calculate_social_capital_score(),
                'economic_feasibility': personal_capital.calculate_economic_capital_score(),
                'psychological_readiness': personal_capital.calculate_psychological_capital_score()
            }
        }


# 使用示例
if __name__ == "__main__":
    # 创建集成实例
    integration = KnowledgeGraphCareerIntegration(user_id="test_user")
    
    # 分析职业决策
    result = integration.analyze_career_decision(
        question="我应该转行做产品经理还是继续深耕技术？",
        options=[
            {
                'id': 'opt1',
                'title': '转行产品经理',
                'current_role': '中级后端工程师',
                'target_role': '产品经理',
                'duration_months': 24,
                'success_prob': 0.6,
                'salary_increase': 3000,
                'volatility': 0.4
            },
            {
                'id': 'opt2',
                'title': '深耕技术成为架构师',
                'current_role': '中级后端工程师',
                'target_role': '架构师',
                'duration_months': 36,
                'success_prob': 0.7,
                'salary_increase': 8000,
                'volatility': 0.25
            }
        ]
    )
    
    print("\n" + "="*80)
    print("职业决策分析结果")
    print("="*80)
    print(f"\n问题: {result['question']}")
    print(f"\n个人资本评估:")
    for key, value in result['personal_capital_summary'].items():
        print(f"  {key}: {value:.2f}")
    
    print(f"\n选项分析:")
    for i, option in enumerate(result['options_analysis'], 1):
        print(f"\n  {i}. {option['option_title']}")
        print(f"     综合得分: {option['综合得分']:.1f}")
        print(f"     成功率: {option['成功率']}")
        print(f"     风险调整价值: {option['风险调整价值']:.0f}")
    
    print(f"\n推荐方案: {result['recommendation']['option_title']}")
    print("="*80)
