"""
快速演示脚本 - 展示完整系统的功能
"""

import json
from datetime import datetime


def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_knowledge_graph():
    """演示知识图谱"""
    print_section("[1] Knowledge Graph Automation")
    
    from backend.knowledge.automated_kg_builder import get_automated_kg_builder
    
    kg_builder = get_automated_kg_builder("demo_user")
    
    user_data = {
        "sleep_hours": 5,
        "exercise_minutes": 20,
        "stress_level": 8,
        "mood": 4,
        "health_score": 60
    }
    
    user_message = "I have been sleeping poorly and feeling stressed lately"
    
    result = kg_builder.build_from_user_data(user_data, user_message)
    
    print(f"[OK] Extracted entities: {result['extracted_entities']}")
    print(f"[OK] Inferred relations: {result['new_relations']}")
    
    stats = kg_builder.get_graph_statistics()
    print(f"[OK] Knowledge Graph Statistics:")
    print(f"   - Total entities: {stats['total_entities']}")
    print(f"   - Total relations: {stats['total_relations']}")
    print(f"   - Top entity: {stats['top_entities'][0]['name'] if stats['top_entities'] else 'N/A'}")


def demo_reinforcement_learning():
    """演示强化学习"""
    print_section("[2] Reinforcement Learning Training")
    
    from backend.learning.rl_trainer import get_rl_trainer, FeedbackType
    
    rl_trainer = get_rl_trainer("demo_user")
    
    user_data = {
        "sleep_hours": 5,
        "exercise_minutes": 20,
        "stress_level": 8,
        "mood": 4,
        "health_score": 60
    }
    
    # Simulate interactions
    for i in range(3):
        result = rl_trainer.record_interaction(
            user_data,
            "exercise",
            FeedbackType.HELPFUL,
            "hybrid"
        )
        print(f"[OK] Interaction {i+1}: Q-value change = {result['q_value_change']:.4f}")
    
    stats = rl_trainer.get_training_statistics()
    print(f"\n[OK] Training Statistics:")
    print(f"   - Total episodes: {stats['total_episodes']}")
    print(f"   - Average reward: {stats['average_reward']:.4f}")
    print(f"   - Best strategy: {stats['best_strategy']}")


def demo_decision_engine():
    """演示决策引擎"""
    print_section("[3] Decision Engine")
    
    from backend.decision.decision_engine import get_decision_engine
    
    decision_engine = get_decision_engine("demo_user")
    
    user_data = {
        "sleep_hours": 5,
        "exercise_minutes": 20,
        "stress_level": 8,
        "mood": 4,
        "health_score": 60
    }
    
    decision = decision_engine.make_decision(user_data)
    
    print(f"[OK] Decision: {decision.recommendation}")
    print(f"[OK] Reasoning: {decision.reasoning}")
    print(f"[OK] Confidence: {decision.confidence:.2f}")
    print(f"[OK] Expected impact: {decision.expected_impact}")


def demo_emergence_detection():
    """演示涌现检测"""
    print_section("[4] Emergence Detection")
    
    from backend.emergence.emergence_detector import get_emergence_detector
    
    detector = get_emergence_detector("demo_user")
    
    # Add multiple data points
    data_points = [
        {"sleep_hours": 7, "stress_level": 5, "mood": 7, "health_score": 75},
        {"sleep_hours": 6, "stress_level": 6, "mood": 6, "health_score": 70},
        {"sleep_hours": 5, "stress_level": 8, "mood": 4, "health_score": 60},
        {"sleep_hours": 4, "stress_level": 9, "mood": 3, "health_score": 55},
    ]
    
    for data in data_points:
        detector.add_data_point(data)
    
    events = detector.detect_all_emergences()
    
    print(f"[OK] Detected {len(events)} emergence phenomena")
    for event in events[:3]:
        print(f"   - {event.emergence_type.value}: {event.description}")


def demo_digital_twin():
    """演示数字孪生"""
    print_section("[5] Digital Twin Prediction")
    
    from backend.digital_twin.digital_twin import get_digital_twin
    
    initial_state = {
        "sleep_hours": 5,
        "stress_level": 8,
        "mood": 4,
        "health_score": 60,
        "exercise_minutes": 20
    }
    
    twin = get_digital_twin("demo_user", initial_state)
    
    prediction = twin.predict_future_state(7)
    
    print(f"[OK] Predicted next 7 days")
    print(f"[OK] Recommended scenario: {prediction['recommended_scenario']}")
    
    for scenario in prediction['scenarios']:
        final_state = prediction['scenarios'][scenario]['final_state']
        print(f"\n   {scenario.upper()} scenario:")
        print(f"   - Sleep hours: {final_state.get('sleep_hours', 0):.1f}")
        print(f"   - Stress level: {final_state.get('stress_level', 0):.1f}")
        print(f"   - Mood: {final_state.get('mood', 0):.1f}")


def demo_counterfactual_analysis():
    """演示反事实分析"""
    print_section("[6] Counterfactual Analysis")
    
    from backend.decision.counterfactual_analyzer import get_counterfactual_analyzer
    
    analyzer = get_counterfactual_analyzer("demo_user")
    
    user_data = {
        "sleep_hours": 5,
        "stress_level": 8,
        "mood": 4,
        "health_score": 60
    }
    
    analysis = analyzer.analyze_what_if("work", "exercise", user_data, {})
    
    print(f"[OK] Original decision: {analysis.original_decision}")
    print(f"[OK] Alternative decision: {analysis.alternative_decision}")
    print(f"\n[OK] Insights:")
    for insight in analysis.insights:
        print(f"   - {insight}")


def demo_hybrid_intelligence():
    """演示混合智能系统"""
    print_section("[7] Hybrid Intelligence Integration")
    
    from backend.hybrid.hybrid_intelligence import get_hybrid_intelligence_system
    
    hybrid_system = get_hybrid_intelligence_system("demo_user")
    
    user_message = "I have been sleeping poorly and feeling stressed"
    user_data = {
        "sleep_hours": 5,
        "exercise_minutes": 20,
        "stress_level": 8,
        "mood": 4,
        "health_score": 60
    }
    
    result = hybrid_system.process_user_input(user_message, user_data)
    
    print(f"[OK] Processing completed")
    print(f"[OK] Selected mode: {result['components']['mode_selection']['selected_mode']}")
    print(f"[OK] Final recommendation: {result['final_recommendation']['primary_action']}")
    
    overview = hybrid_system.get_system_overview()
    print(f"\n[OK] System Overview:")
    print(f"   - System health: {overview['system_health']:.2f}")
    print(f"   - Total interactions: {overview['statistics']['total_interactions']}")
    print(f"   - Knowledge graph entities: {overview['component_status']['knowledge_graph']['entity_count']}")


def main():
    """Main function"""
    print("\n")
    print("=" * 70)
    print("  Life Quality AI Assistant System - Complete Demo")
    print("=" * 70)
    
    try:
        demo_knowledge_graph()
        demo_reinforcement_learning()
        demo_decision_engine()
        demo_emergence_detection()
        demo_digital_twin()
        demo_counterfactual_analysis()
        demo_hybrid_intelligence()
        
        print_section("[SUCCESS] Demo Completed!")
        print("All system components demonstrated successfully")
        print("\nTip: After starting the server, test the API with:")
        print("   curl -X POST http://localhost:8000/api/v3/system/full-test \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{...}'")
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

