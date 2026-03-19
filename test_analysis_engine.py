"""
分析引擎测试脚本
验证6大领域分析模型的功能
"""
from backend.analysis.unified_analyzer import get_analysis_engine
from datetime import datetime, timedelta
import json


def generate_test_history(days=30):
    """生成测试历史数据"""
    history = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        
        record = {
            "timestamp": date.isoformat(),
            "sleep_hours": 7 + (i % 3 - 1),  # 6-8小时
            "sleep_quality": 7 + (i % 3 - 1),  # 6-8分
            "exercise_minutes": 30 + (i % 4) * 10,  # 30-60分钟
            "stress_level": 5 + (i % 4 - 2),  # 3-7分
            "health_score": 75 + (i % 5 - 2),  # 73-77分
            "heart_rate": 70 + (i % 10 - 5),  # 65-75 bpm
            "steps": 5000 + (i % 3) * 1000,  # 5000-7000步
            "mood": 7 + (i % 3 - 1),  # 6-8分
            "work_hours": 8 + (i % 3 - 1),  # 7-9小时
            "focus_time": 6 + (i % 3 - 1),  # 5-7小时
            "task_completion_rate": 0.7 + (i % 3) * 0.1,  # 70-90%
            "interruptions": 3 + (i % 4),  # 3-6次
            "time_pressure": 0.3 + (i % 4) * 0.1,  # 0.3-0.6
            "social_hours": 2 + (i % 3 - 1),  # 1-3小时
            "social_interactions": 5 + (i % 4),  # 5-9次
            "loneliness": 3 + (i % 4 - 2),  # 1-5分
            "social_satisfaction": 7 + (i % 3 - 1),  # 6-8分
            "income": 5000,
            "spending": 3000 + (i % 5) * 200,  # 3000-3800
            "savings": 2000 - (i % 5) * 100,  # 1600-2000
            "debt": 0,
            "learning_hours": 1 + (i % 3) * 0.5,  # 1-2.5小时
            "learning_quality": 7 + (i % 3 - 1),  # 6-8分
            "test_score": 75 + (i % 5 - 2),  # 73-77分
            "goal_progress": 0.5 + (i % 3) * 0.1  # 50-70%
        }
        
        history.append(record)
    
    return history


def test_analysis_engine():
    """测试分析引擎"""
    
    print("\n" + "="*60)
    print("  Analysis Engine Test")
    print("="*60 + "\n")
    
    # 获取分析引擎
    engine = get_analysis_engine()
    
    # 生成测试数据
    print("[TEST] Generating 30 days of test data...")
    history = generate_test_history(30)
    print(f"[OK] Generated {len(history)} test data points\n")
    
    # 进行分析
    user_id = "test_user_001"
    user_data = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }
    
    print("[TEST] Starting comprehensive life analysis...")
    analysis = engine.analyze(user_id, user_data, history)
    
    # 打印结果
    print("\n" + "="*60)
    print("  Analysis Results")
    print("="*60 + "\n")
    
    print(f"User ID: {analysis.user_id}")
    print(f"Analysis Time: {analysis.timestamp}")
    print(f"Overall Life Quality Score: {analysis.overall_score}/100\n")
    
    # 打印各领域分数
    print("Domain Scores:")
    print(f"  Health: {analysis.health.get('health_score', 0)}/100")
    print(f"  Time: {analysis.time.get('efficiency_score', 0)}/100")
    print(f"  Emotion: {analysis.emotion.get('emotional_stability', 0)}/100")
    print(f"  Social: {analysis.social.get('satisfaction_score', 0)}/100")
    print(f"  Finance: {analysis.finance.get('financial_health', 0)}/100")
    print(f"  Learning: {analysis.learning.get('learning_efficiency', 0)}/100\n")
    
    # 打印关键洞察
    print("Key Insights:")
    for i, insight in enumerate(analysis.key_insights, 1):
        print(f"  {i}. {insight}")
    
    print("\nPriority Actions:")
    for i, action in enumerate(analysis.priority_actions, 1):
        print(f"  {i}. {action}")
    
    # 打印详细分析
    print("\n" + "="*60)
    print("  Detailed Analysis")
    print("="*60 + "\n")
    
    print("Health Domain:")
    print(f"  Sleep Debt: {analysis.health.get('sleep_debt', 0)} hours")
    print(f"  Immunity Score: {analysis.health.get('immunity_score', 0)}/100")
    print(f"  Recovery Status: {analysis.health.get('recovery_status', 'unknown')}")
    print(f"  Risk Factors: {', '.join(analysis.health.get('risk_factors', []))}\n")
    
    print("Time Domain:")
    print(f"  Efficiency Score: {analysis.time.get('efficiency_score', 0)}/100")
    print(f"  Cognitive Load: {analysis.time.get('cognitive_load', 0)}/10")
    print(f"  Time Pressure: {analysis.time.get('time_pressure', 0)}")
    print(f"  Procrastination Level: {analysis.time.get('procrastination_level', 0)}/10\n")
    
    print("Emotion Domain:")
    print(f"  Mood Score: {analysis.emotion.get('mood_score', 0)}/10")
    print(f"  Emotional Stability: {analysis.emotion.get('emotional_stability', 0)}/100")
    print(f"  Regulation Ability: {analysis.emotion.get('regulation_ability', 0)}/100")
    print(f"  Risk Level: {analysis.emotion.get('risk_level', 'unknown')}\n")
    
    print("Social Domain:")
    print(f"  Loneliness: {analysis.social.get('loneliness_score', 0)}/10")
    print(f"  Satisfaction: {analysis.social.get('satisfaction_score', 0)}/100")
    print(f"  Relationship Quality: {analysis.social.get('relationship_quality', 0)}/100\n")
    
    print("Finance Domain:")
    print(f"  Savings Rate: {analysis.finance.get('savings_rate', 0):.1%}")
    print(f"  Financial Health: {analysis.finance.get('financial_health', 0)}/100")
    print(f"  Risk Level: {analysis.finance.get('risk_level', 'unknown')}\n")
    
    print("Learning Domain:")
    print(f"  Learning Efficiency: {analysis.learning.get('learning_efficiency', 0)}/100")
    print(f"  Knowledge Retention: {analysis.learning.get('knowledge_retention', 0)}/100")
    print(f"  Learning Consistency: {analysis.learning.get('learning_consistency', 0)}/100\n")
    
    print("="*60)
    print("[OK] Analysis engine test completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_analysis_engine()

