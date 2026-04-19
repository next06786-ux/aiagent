"""
机器学习模型 - 简化版
提供可行性预测、风险评估、趋势预测、推荐生成
"""
from typing import Dict, List, Any, Optional
from datetime import datetime


class FeasibilityPredictor:
    """可行性预测器"""
    
    def predict_feasibility(
        self,
        decision_context: Dict[str, Any],
        current_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测决策可行性"""
        
        # 简化的加权评分算法
        factors = {
            'gpa': current_status.get('gpa', 0) / 4.0 * 100,
            'academic_score': current_status.get('academic_score', 0),
            'study_hours': min(current_status.get('study_hours_per_week', 0) / 40 * 100, 100),
            'stress_level': max(0, 100 - current_status.get('stress_level', 5) * 10)
        }
        
        # 计算加权平均
        weights = {'gpa': 0.4, 'academic_score': 0.3, 'study_hours': 0.2, 'stress_level': 0.1}
        feasibility_score = sum(factors.get(k, 0) * w for k, w in weights.items())
        
        # 找出最强和最弱因素
        strongest_factor = max(factors.items(), key=lambda x: x[1])[0] if factors else 'unknown'
        weakest_factor = min(factors.items(), key=lambda x: x[1])[0] if factors else 'unknown'
        
        return {
            'feasibility_score': round(feasibility_score, 2),
            'confidence': 0.85,
            'strongest_factor': strongest_factor,
            'weakest_factor': weakest_factor,
            'feature_importance': factors
        }


class RiskAssessor:
    """风险评估器"""
    
    def assess_risks(
        self,
        decision_context: Dict[str, Any],
        current_status: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """评估风险"""
        
        risks = []
        
        # 学业风险
        gpa = current_status.get('gpa', 0)
        if gpa < 3.0:
            risks.append({
                'type': '学业风险',
                'severity': 'high' if gpa < 2.5 else 'medium',
                'score': max(0, (3.0 - gpa) / 3.0 * 100),
                'description': f'当前GPA {gpa:.2f}低于目标要求',
                'mitigation': '制定GPA提升计划，重点关注薄弱科目'
            })
        
        # 压力风险
        stress = current_status.get('stress_level', 0)
        if stress > 7:
            risks.append({
                'type': '压力风险',
                'severity': 'high' if stress > 8 else 'medium',
                'score': stress * 10,
                'description': f'压力水平{stress}/10，可能影响学习效率',
                'mitigation': '调整学习节奏，增加休息时间'
            })
        
        # 时间管理风险
        study_hours = current_status.get('study_hours_per_week', 0)
        if study_hours < 20:
            risks.append({
                'type': '时间管理风险',
                'severity': 'medium',
                'score': (20 - study_hours) / 20 * 100,
                'description': f'每周学习时间{study_hours}小时，低于建议值',
                'mitigation': '优化时间分配，提高学习效率'
            })
        
        # 计算总体风险分数
        overall_risk_score = sum(r['score'] for r in risks) / len(risks) if risks else 0
        overall_risk_level = 'high' if overall_risk_score > 70 else 'medium' if overall_risk_score > 40 else 'low'
        
        return {
            'overall_risk_score': round(overall_risk_score, 2),
            'overall_risk_level': overall_risk_level,
            'risks': risks,
            'risk_count': len(risks)
        }


class TrendPredictor:
    """趋势预测器"""
    
    def predict_multiple_metrics(
        self,
        history: List[Dict[str, Any]],
        metrics: List[str],
        periods_ahead: int = 3
    ) -> Dict[str, Any]:
        """预测多个指标的趋势"""
        
        predictions = {}
        concerning_metrics = []
        
        for metric in metrics:
            # 提取历史值
            values = [h.get(metric, 0) for h in history if metric in h]
            
            if len(values) < 2:
                continue
            
            # 简单线性趋势
            current_value = values[-1]
            avg_change = (values[-1] - values[0]) / len(values)
            trend_slope = avg_change
            
            # 判断趋势方向
            if abs(trend_slope) < 0.1:
                trend_direction = '稳定'
                trend_strength = 'weak'
            elif trend_slope > 0:
                trend_direction = '上升'
                trend_strength = 'strong' if abs(trend_slope) > 0.5 else 'moderate'
            else:
                trend_direction = '下降'
                trend_strength = 'strong' if abs(trend_slope) > 0.5 else 'moderate'
            
            predictions[metric] = {
                'status': 'success',
                'current_value': current_value,
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'trend_slope': trend_slope,
                'confidence_interval': 0.15
            }
            
            # 识别需要关注的指标
            if (metric in ['stress_level', 'risk_score'] and trend_direction == '上升') or \
               (metric in ['gpa', 'health_score', 'mood'] and trend_direction == '下降'):
                concerning_metrics.append(metric)
        
        return {
            'predictions': predictions,
            'concerning_metrics': concerning_metrics,
            'total_metrics': len(metrics)
        }


class PersonalizedRecommender:
    """个性化推荐器"""
    
    def generate_recommendations(
        self,
        decision_context: Dict[str, Any],
        current_status: Dict[str, Any],
        feasibility_result: Dict[str, Any],
        risk_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成个性化推荐"""
        
        recommendations = []
        
        # 基于可行性评分的推荐
        feasibility_score = feasibility_result.get('feasibility_score', 0)
        if feasibility_score < 70:
            recommendations.append({
                'priority': 'high',
                'category': '能力提升',
                'title': f'提升{feasibility_result.get("weakest_factor", "核心能力")}',
                'actions': [
                    f'重点关注{feasibility_result.get("weakest_factor")}的提升',
                    '制定详细的提升计划',
                    '设定阶段性目标'
                ],
                'expected_impact': '预计可提升可行性评分10-15分',
                'timeline': '1-3个月'
            })
        
        # 基于风险的推荐
        for risk in risk_result.get('risks', [])[:2]:
            recommendations.append({
                'priority': 'high' if risk['severity'] == 'high' else 'medium',
                'category': '风险控制',
                'title': f'应对{risk["type"]}',
                'actions': [risk['mitigation']],
                'expected_impact': f'降低{risk["type"]}风险',
                'timeline': '立即开始'
            })
        
        # 通用建议
        recommendations.append({
            'priority': 'medium',
            'category': '综合提升',
            'title': '保持优势，补齐短板',
            'actions': [
                f'继续保持{feasibility_result.get("strongest_factor")}优势',
                '定期回顾和调整计划',
                '寻求导师或同伴支持'
            ],
            'expected_impact': '全面提升决策成功率',
            'timeline': '持续进行'
        })
        
        return recommendations


# 全局实例
_feasibility_predictor = None
_risk_assessor = None
_trend_predictor = None
_recommender = None


def get_feasibility_predictor() -> FeasibilityPredictor:
    """获取可行性预测器"""
    global _feasibility_predictor
    if _feasibility_predictor is None:
        _feasibility_predictor = FeasibilityPredictor()
    return _feasibility_predictor


def get_risk_assessor() -> RiskAssessor:
    """获取风险评估器"""
    global _risk_assessor
    if _risk_assessor is None:
        _risk_assessor = RiskAssessor()
    return _risk_assessor


def get_trend_predictor() -> TrendPredictor:
    """获取趋势预测器"""
    global _trend_predictor
    if _trend_predictor is None:
        _trend_predictor = TrendPredictor()
    return _trend_predictor


def get_recommender() -> PersonalizedRecommender:
    """获取推荐器"""
    global _recommender
    if _recommender is None:
        _recommender = PersonalizedRecommender()
    return _recommender
