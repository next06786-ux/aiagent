"""
涌现检测系统测试脚本
验证涌现模式检测、报告生成等功能
"""
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加后端路径
import os
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

from backend.prediction.emergence_detector import get_emergence_detector, PatternType
from backend.prediction.emergence_report_generator import get_report_generator


def generate_test_history(days: int = 30) -> List[Dict[str, Any]]:
    """生成测试历史数据"""
    history = []
    
    for i in range(days):
        # 模拟压力和睡眠的反向关系
        stress = 3 + (i % 10) * 0.5  # 3-8
        sleep = 8 - (i % 10) * 0.3   # 5-8
        
        # 模拟健康分数的下降趋势
        health = 100 - (i * 0.5)
        
        # 模拟情绪的波动
        mood = 5 + (i % 7 - 3) * 0.5
        
        # 模拟运动和心情的正相关
        exercise = 20 + (i % 5) * 10
        
        record = {
            "timestamp": (datetime.now() - timedelta(days=days-i)).timestamp(),
            "health_score": max(50, health),
            "sleep_hours": sleep,
            "exercise_minutes": exercise,
            "stress_level": stress,
            "mood": max(1, min(10, mood)),
            "time_pressure": 0.3 + (i % 5) * 0.1,
            "social_satisfaction": 5 + (i % 3) - 1,
            "efficiency_score": 70 - (i % 10) * 2,
            "loneliness": 3 + (i % 5) - 2,
            "social_hours": 1 + (i % 4),
            "sleep_quality": 6 + (i % 3),
            "heart_rate": 70 + (i % 20),
            "steps": 5000 + (i % 3000)
        }
        history.append(record)
    
    return history


def test_cascade_detection():
    """测试级联效应检测"""
    print("\n" + "="*60)
    print("Test 1: Cascade Detection")
    print("="*60)
    
    detector = get_emergence_detector()
    history = generate_test_history(30)
    
    cascades = detector.cascade_detector.detect_cascades({}, history)
    
    print(f"\nDetected {len(cascades)} cascade patterns:")
    for cascade in cascades:
        print(f"\n  [CASCADE] {cascade.description}")
        print(f"     Type: {cascade.pattern_type.value}")
        print(f"     Domains: {', '.join(cascade.domains)}")
        print(f"     Confidence: {cascade.confidence:.2%}")
        print(f"     Impact: {cascade.impact_score:.2%}")
        print(f"     Recommendations:")
        for rec in cascade.recommendations[:2]:
            print(f"       - {rec}")


def test_feedback_loop_detection():
    """测试反馈环检测"""
    print("\n" + "="*60)
    print("Test 2: Feedback Loop Detection")
    print("="*60)
    
    detector = get_emergence_detector()
    history = generate_test_history(30)
    
    loops = detector.feedback_detector.detect_feedback_loops({}, history)
    
    print(f"\nDetected {len(loops)} feedback loops:")
    for loop in loops:
        print(f"\n  [LOOP] {loop.description}")
        print(f"     Type: {loop.pattern_type.value}")
        print(f"     Domains: {', '.join(loop.domains)}")
        print(f"     Confidence: {loop.confidence:.2%}")
        print(f"     Impact: {loop.impact_score:.2%}")


def test_tipping_point_detection():
    """测试临界点检测"""
    print("\n" + "="*60)
    print("Test 3: Tipping Point Detection")
    print("="*60)
    
    detector = get_emergence_detector()
    history = generate_test_history(30)
    
    tipping_points = detector.tipping_detector.detect_tipping_points({}, history)
    
    print(f"\nDetected {len(tipping_points)} tipping points:")
    for tp in tipping_points:
        print(f"\n  [TIPPING] {tp.description}")
        print(f"     Type: {tp.pattern_type.value}")
        print(f"     Domains: {', '.join(tp.domains)}")
        print(f"     Confidence: {tp.confidence:.2%}")
        print(f"     Impact: {tp.impact_score:.2%}")


def test_synergy_detection():
    """测试协同效应检测"""
    print("\n" + "="*60)
    print("Test 4: Synergy Detection")
    print("="*60)
    
    detector = get_emergence_detector()
    history = generate_test_history(30)
    
    synergies = detector.synergy_detector.detect_synergies({}, history)
    
    print(f"\nDetected {len(synergies)} synergies:")
    for synergy in synergies:
        print(f"\n  [SYNERGY] {synergy.description}")
        print(f"     Type: {synergy.pattern_type.value}")
        print(f"     Domains: {', '.join(synergy.domains)}")
        print(f"     Confidence: {synergy.confidence:.2%}")
        print(f"     Impact: {synergy.impact_score:.2%}")


def test_all_patterns_detection():
    """测试所有模式检测"""
    print("\n" + "="*60)
    print("Test 5: Comprehensive Pattern Detection")
    print("="*60)
    
    detector = get_emergence_detector()
    history = generate_test_history(30)
    
    patterns = detector.detect_all_patterns({}, history)
    
    print(f"\nTotal patterns detected: {len(patterns)}")
    
    # 按类型统计
    by_type = {}
    for pattern in patterns:
        ptype = pattern.pattern_type.value
        by_type[ptype] = by_type.get(ptype, 0) + 1
    
    print("\nDistribution by type:")
    for ptype, count in by_type.items():
        print(f"  - {ptype}: {count}")
    
    # 按影响程度排序
    print("\nTop 5 patterns by impact:")
    sorted_patterns = sorted(patterns, key=lambda p: p.impact_score, reverse=True)
    for i, pattern in enumerate(sorted_patterns[:5], 1):
        print(f"\n  {i}. {pattern.description}")
        print(f"     Impact: {pattern.impact_score:.2%}")
        print(f"     Confidence: {pattern.confidence:.2%}")


def test_report_generation():
    """测试报告生成"""
    print("\n" + "="*60)
    print("Test 6: Report Generation")
    print("="*60)
    
    detector = get_emergence_detector()
    generator = get_report_generator()
    
    history = generate_test_history(30)
    patterns = detector.detect_all_patterns({}, history)
    
    # 转换为字典格式
    patterns_dict = [
        {
            "pattern_id": p.pattern_id,
            "type": p.pattern_type.value,
            "domains": p.domains,
            "description": p.description,
            "confidence": p.confidence,
            "impact_score": p.impact_score,
            "recommendations": p.recommendations,
            "evidence": p.evidence,
            "affected_metrics": p.affected_metrics
        }
        for p in patterns
    ]
    
    # 生成报告
    report = generator.generate_comprehensive_report(
        user_id="test_user",
        patterns=patterns_dict,
        user_data={},
        history=history
    )
    
    print("\n[EXECUTIVE SUMMARY]")
    summary = report.get("executive_summary", {})
    print(f"  Status: {summary.get('status', 'unknown')}")
    print(f"  Message: {summary.get('message', '')}")
    print(f"  Total patterns: {summary.get('total_patterns', 0)}")
    print(f"  High impact: {summary.get('high_impact_patterns', 0)}")
    
    print("\n[RISK ASSESSMENT]")
    risk = report.get("risk_assessment", {})
    print(f"  Overall risk level: {risk.get('overall_risk_level', 'unknown')}")
    print(f"  Urgent actions needed: {risk.get('urgent_actions_needed', False)}")
    
    print("\n[ACTION PLAN]")
    action_plan = report.get("action_plan", {})
    
    immediate = action_plan.get("immediate_actions", {})
    print(f"  Immediate actions ({immediate.get('timeframe', '')}): {len(immediate.get('actions', []))} items")
    for action in immediate.get('actions', [])[:2]:
        print(f"    - {action}")
    
    short_term = action_plan.get("short_term_actions", {})
    print(f"  Short-term actions ({short_term.get('timeframe', '')}): {len(short_term.get('actions', []))} items")
    for action in short_term.get('actions', [])[:2]:
        print(f"    - {action}")
    
    print("\n[PROGRESS TRACKING]")
    progress = report.get("progress_tracking", {})
    print(f"  Trend: {progress.get('trend', 'unknown')}")
    changes = progress.get("changes", {})
    print(f"  Health score change: {changes.get('health_change', 0):+.1f}")
    print(f"  Mood change: {changes.get('mood_change', 0):+.1f}")
    print(f"  Stress change: {changes.get('stress_change', 0):+.1f}")


def test_cross_domain_insights():
    """测试跨领域洞察"""
    print("\n" + "="*60)
    print("Test 7: Cross-Domain Insights")
    print("="*60)
    
    detector = get_emergence_detector()
    generator = get_report_generator()
    
    history = generate_test_history(30)
    patterns = detector.detect_all_patterns({}, history)
    
    patterns_dict = [
        {
            "pattern_id": p.pattern_id,
            "type": p.pattern_type.value,
            "domains": p.domains,
            "description": p.description,
            "confidence": p.confidence,
            "impact_score": p.impact_score,
            "recommendations": p.recommendations
        }
        for p in patterns
    ]
    
    insights = generator._generate_cross_domain_insights(patterns_dict)
    
    print("\nMost affected domains:")
    for domain in insights.get("most_affected_domains", []):
        print(f"  - {domain}")
    
    print(f"\nInterconnection strength: {insights.get('interconnection_strength', 0):.2%}")
    
    print("\nSystemic insights:")
    for insight in insights.get("systemic_insights", []):
        print(f"  - {insight}")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  LifeSwarm Emergence Detection System Tests")
    print("="*60)
    
    try:
        # 运行所有测试
        test_cascade_detection()
        test_feedback_loop_detection()
        test_tipping_point_detection()
        test_synergy_detection()
        test_all_patterns_detection()
        test_report_generation()
        test_cross_domain_insights()
        
        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


