"""
财务领域分析器
分析储蓄率、财务健康、风险评估等指标
"""
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class FinanceMetrics:
    """财务指标"""
    savings_rate: float  # 储蓄率（0-1）
    financial_health: float  # 财务健康分数（0-100）
    risk_level: str  # 风险等级（low/medium/high）
    spending_pattern: Dict[str, float]  # 支出模式
    financial_stability: float  # 财务稳定性（0-100）
    debt_ratio: float  # 债务比率（0-1）
    risk_factors: List[str]  # 风险因素
    recommendations: List[str]  # 建议


class FinanceAnalyzer:
    """财务领域分析器"""
    
    def __init__(self):
        self.savings_target = 0.2  # 目标储蓄率（20%）
        self.emergency_fund_months = 6  # 应急基金月数
    
    def analyze(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> FinanceMetrics:
        """分析财务指标"""
        
        # 计算储蓄率
        savings_rate = self._calculate_savings_rate(history)
        
        # 计算财务健康分数
        financial_health = self._calculate_financial_health(history, savings_rate)
        
        # 评估风险等级
        risk_level = self._assess_risk_level(history, savings_rate)
        
        # 分析支出模式
        spending_pattern = self._analyze_spending_pattern(history)
        
        # 计算财务稳定性
        financial_stability = self._calculate_financial_stability(history)
        
        # 计算债务比率
        debt_ratio = self._calculate_debt_ratio(history)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(savings_rate, financial_health, debt_ratio, spending_pattern)
        
        # 生成建议
        recommendations = self._generate_recommendations(risk_factors, savings_rate, spending_pattern)
        
        return FinanceMetrics(
            savings_rate=savings_rate,
            financial_health=financial_health,
            risk_level=risk_level,
            spending_pattern=spending_pattern,
            financial_stability=financial_stability,
            debt_ratio=debt_ratio,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _calculate_savings_rate(self, history: List[Dict[str, Any]]) -> float:
        """计算储蓄率（0-1）"""
        if not history:
            return 0.0
        
        recent = history[-30:]  # 查看最近30天
        
        total_income = sum(h.get('income', 0) for h in recent)
        total_savings = sum(h.get('savings', 0) for h in recent)
        
        if total_income == 0:
            return 0.0
        
        savings_rate = total_savings / total_income
        return round(min(1.0, max(0.0, savings_rate)), 2)
    
    def _calculate_financial_health(self, history: List[Dict[str, Any]], savings_rate: float) -> float:
        """计算财务健康分数（0-100）"""
        score = 100.0
        
        if not history:
            return 50.0
        
        recent = history[-30:]
        
        # 储蓄率贡献（40%）
        if savings_rate >= self.savings_target:
            savings_score = 40
        else:
            savings_score = (savings_rate / self.savings_target) * 40
        score -= (40 - savings_score)
        
        # 支出稳定性（30%）
        spendings = [h.get('spending', 0) for h in recent]
        if len(spendings) > 1:
            spending_std = np.std(spendings)
            spending_mean = np.mean(spendings)
            if spending_mean > 0:
                cv = spending_std / spending_mean  # 变异系数
                stability_score = max(0, 30 - (cv * 30))
            else:
                stability_score = 30
        else:
            stability_score = 30
        score -= (30 - stability_score)
        
        # 债务管理（30%）
        debts = [h.get('debt', 0) for h in recent]
        total_debt = sum(debts)
        total_income = sum(h.get('income', 0) for h in recent)
        
        if total_income > 0:
            debt_ratio = total_debt / total_income
            if debt_ratio <= 0.3:
                debt_score = 30
            elif debt_ratio <= 0.6:
                debt_score = 20
            elif debt_ratio <= 1.0:
                debt_score = 10
            else:
                debt_score = 0
        else:
            debt_score = 15
        
        score -= (30 - debt_score)
        
        return max(0, min(100, round(score, 1)))
    
    def _assess_risk_level(self, history: List[Dict[str, Any]], savings_rate: float) -> str:
        """评估风险等级"""
        
        if not history:
            return "medium"
        
        recent = history[-30:]
        
        # 计算应急基金
        monthly_spending = np.mean([h.get('spending', 0) for h in recent])
        total_savings = sum(h.get('savings', 0) for h in recent)
        
        if monthly_spending > 0:
            emergency_fund_months = total_savings / monthly_spending
        else:
            emergency_fund_months = 0
        
        # 计算债务比率
        total_debt = sum(h.get('debt', 0) for h in recent)
        total_income = sum(h.get('income', 0) for h in recent)
        
        if total_income > 0:
            debt_ratio = total_debt / total_income
        else:
            debt_ratio = 0
        
        # 评估风险
        if savings_rate < 0.05 or emergency_fund_months < 1 or debt_ratio > 1.0:
            return "high"
        elif savings_rate < 0.1 or emergency_fund_months < 3 or debt_ratio > 0.6:
            return "medium"
        else:
            return "low"
    
    def _analyze_spending_pattern(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析支出模式"""
        pattern = {
            "essential": 0.0,  # 必需支出（食物、住房、交通）
            "discretionary": 0.0,  # 可选支出（娱乐、购物）
            "savings": 0.0,  # 储蓄
            "debt_payment": 0.0,  # 债务偿还
            "other": 0.0  # 其他
        }
        
        if not history:
            return pattern
        
        recent = history[-30:]
        
        total_spending = sum(h.get('spending', 0) for h in recent)
        
        if total_spending == 0:
            return pattern
        
        # 简化实现：基于历史数据的比例
        essential = sum(h.get('essential_spending', 0) for h in recent)
        discretionary = sum(h.get('discretionary_spending', 0) for h in recent)
        savings = sum(h.get('savings', 0) for h in recent)
        debt_payment = sum(h.get('debt_payment', 0) for h in recent)
        
        total = essential + discretionary + savings + debt_payment
        
        if total > 0:
            pattern["essential"] = round(essential / total, 2)
            pattern["discretionary"] = round(discretionary / total, 2)
            pattern["savings"] = round(savings / total, 2)
            pattern["debt_payment"] = round(debt_payment / total, 2)
            pattern["other"] = round(1 - sum(pattern.values()), 2)
        
        return pattern
    
    def _calculate_financial_stability(self, history: List[Dict[str, Any]]) -> float:
        """计算财务稳定性（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-30:]
        
        stability = 100.0
        
        # 收入稳定性（40%）
        incomes = [h.get('income', 0) for h in recent]
        if len(incomes) > 1 and np.mean(incomes) > 0:
            income_cv = np.std(incomes) / np.mean(incomes)
            income_stability = max(0, 40 - (income_cv * 40))
        else:
            income_stability = 40
        stability -= (40 - income_stability)
        
        # 支出稳定性（30%）
        spendings = [h.get('spending', 0) for h in recent]
        if len(spendings) > 1 and np.mean(spendings) > 0:
            spending_cv = np.std(spendings) / np.mean(spendings)
            spending_stability = max(0, 30 - (spending_cv * 30))
        else:
            spending_stability = 30
        stability -= (30 - spending_stability)
        
        # 储蓄稳定性（30%）
        savings_list = [h.get('savings', 0) for h in recent]
        if len(savings_list) > 1 and np.mean(savings_list) > 0:
            savings_cv = np.std(savings_list) / np.mean(savings_list)
            savings_stability = max(0, 30 - (savings_cv * 30))
        else:
            savings_stability = 30
        stability -= (30 - savings_stability)
        
        return max(0, min(100, round(stability, 1)))
    
    def _calculate_debt_ratio(self, history: List[Dict[str, Any]]) -> float:
        """计算债务比率（0-1）"""
        if not history:
            return 0.0
        
        recent = history[-30:]
        
        total_debt = sum(h.get('debt', 0) for h in recent)
        total_income = sum(h.get('income', 0) for h in recent)
        
        if total_income == 0:
            return 0.0
        
        debt_ratio = total_debt / total_income
        return round(min(1.0, max(0.0, debt_ratio)), 2)
    
    def _identify_risk_factors(
        self,
        savings_rate: float,
        financial_health: float,
        debt_ratio: float,
        spending_pattern: Dict[str, float]
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        if savings_rate < 0.05:
            risks.append("储蓄率极低")
        elif savings_rate < 0.1:
            risks.append("储蓄率不足")
        
        if financial_health < 40:
            risks.append("财务健康状况严重不佳")
        elif financial_health < 60:
            risks.append("财务健康状况较差")
        
        if debt_ratio > 1.0:
            risks.append("债务严重超支")
        elif debt_ratio > 0.6:
            risks.append("债务负担较重")
        
        if spending_pattern.get("discretionary", 0) > 0.4:
            risks.append("可选支出过高")
        
        if spending_pattern.get("essential", 0) > 0.7:
            risks.append("必需支出占比过高")
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        savings_rate: float,
        spending_pattern: Dict[str, float]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if "储蓄率极低" in risk_factors:
            recommendations.append("立即制定储蓄计划，目标20%")
            recommendations.append("减少不必要的支出")
            recommendations.append("建立自动转账储蓄机制")
        elif "储蓄率不足" in risk_factors:
            recommendations.append("逐步增加储蓄率至20%")
            recommendations.append("审视支出结构，优化分配")
        
        if "财务健康状况严重不佳" in risk_factors:
            recommendations.append("进行全面的财务审计")
            recommendations.append("制定详细的财务改善计划")
            recommendations.append("考虑寻求财务顾问帮助")
        elif "财务健康状况较差" in risk_factors:
            recommendations.append("改善支出管理")
            recommendations.append("增加收入或减少支出")
        
        if "债务严重超支" in risk_factors:
            recommendations.append("制定债务偿还计划")
            recommendations.append("优先偿还高利息债务")
            recommendations.append("避免新增债务")
        elif "债务负担较重" in risk_factors:
            recommendations.append("加快债务偿还速度")
            recommendations.append("考虑债务重组")
        
        if "可选支出过高" in risk_factors:
            recommendations.append("减少娱乐和购物支出")
            recommendations.append("制定每月可选支出预算")
        
        if "必需支出占比过高" in risk_factors:
            recommendations.append("考虑降低住房或交通成本")
            recommendations.append("寻找更经济的生活方式")
        
        if savings_rate >= 0.2:
            recommendations.append("保持当前储蓄习惯")
            recommendations.append("考虑投资理财，增加财富")
        
        return recommendations

