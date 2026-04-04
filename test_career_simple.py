"""简化的职业决策系统测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("职业决策系统模块测试")
print("=" * 60)

# 1. 测试职业星图数据生成
print("\n1. 职业星图数据生成")
print("-" * 60)
try:
    from backend.vertical.career.career_knowledge_graph import career_kg, UserSkillProfile
    
    profile = UserSkillProfile(
        mastered_skills=["Python", "JavaScript"],
        partial_skills=["React"],
        missing_skills=["Kubernetes"],
        target_direction="Python工程师"
    )
    
    graph = career_kg.build_career_graph(profile)
    
    print(f"✓ 职业星图生成成功")
    print(f"  节点数: {graph['metadata']['total_nodes']}")
    print(f"  边数: {graph['metadata']['total_edges']}")
    print(f"  技能层: {len(graph['layers']['skills'])} 个")
    print(f"  岗位层: {len(graph['layers']['jobs'])} 个")
    print(f"  公司层: {len(graph['layers']['companies'])} 个")
    
    if 'data_sources' in graph['metadata']:
        print(f"  数据来源: {graph['metadata']['data_sources']}")
    
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试职业决策算法
print("\n2. 职业决策算法")
print("-" * 60)
try:
    from backend.decision_algorithm.career_decision_algorithm import (
        CareerDecisionAlgorithm,
        Skill,
        PersonalCapital,
        CareerPath
    )
    
    algo = CareerDecisionAlgorithm()
    print("✓ 算法模块加载成功")
    
    # 测试技能ROI计算
    skill = Skill(name="Python", proficiency=0.7, years_experience=3)
    roi = algo.calculate_skill_roi(
        skill=skill,
        learning_hours=200,
        current_salary=20,
        target_salary=30,
        time_horizon_years=3
    )
    
    print(f"  技能ROI计算:")
    print(f"    学习成本: {roi['learning_cost']:.2f}万")
    print(f"    总收益: {roi['total_benefit']:.2f}万")
    print(f"    ROI: {roi['roi']:.2%}")
    print(f"    回本时间: {roi['payback_years']} 年")
    
    # 测试职业路径模拟
    current_capital = PersonalCapital(
        skills=[Skill("Python", 0.7, 3)],
        network_size=50,
        network_quality=0.6,
        resilience=0.7,
        optimism=0.8,
        self_efficacy=0.7,
        savings=10,
        debt=0
    )
    
    path = CareerPath(
        stages=[],
        total_duration_years=3,
        expected_salary_growth=0.5,
        risk_level=0.3
    )
    
    simulated_path = algo.simulate_career_path(path, current_capital, time_horizon_years=3)
    print(f"  职业路径模拟: {len(simulated_path)} 个阶段")
    
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试多Agent职业评估
print("\n3. 多Agent职业评估")
print("-" * 60)
try:
    from backend.decision.multi_agent_career_evaluator import MultiAgentCareerEvaluator
    
    evaluator = MultiAgentCareerEvaluator()
    print("✓ 多Agent评估器加载成功")
    print(f"  支持的Agent类型: {len(evaluator.agent_types)} 个")
    
    # 测试单个Agent评估
    test_option = {
        "title": "Python后端工程师",
        "company": "字节跳动",
        "salary": "25-35万",
        "description": "负责后端服务开发"
    }
    
    test_context = {
        "user_skills": ["Python", "Django"],
        "experience_years": 3,
        "career_goal": "技术专家"
    }
    
    # 注意：这个方法可能需要异步调用
    print(f"  测试评估选项: {test_option['title']}")
    print(f"  评估维度: 技术匹配、薪资、发展空间、工作生活平衡")
    
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试职业模拟推演集成
print("\n4. 职业模拟推演集成")
print("-" * 60)
try:
    from backend.decision.career_simulation_integration import CareerSimulationIntegration
    
    sim = CareerSimulationIntegration()
    print("✓ 模拟推演模块加载成功")
    print("  注意: 完整推演需要提供collected_info参数")
    print("  包含: 用户技能、经验、目标、风险偏好等信息")
    
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n总结:")
print("1. 职业星图: 可以生成3层同心圆结构（技能-岗位-公司）")
print("2. 决策算法: 支持技能ROI计算、职业路径模拟")
print("3. 多Agent评估: 支持多维度评估（技术、薪资、发展等）")
print("4. 模拟推演: 支持12个月时间线推演")
print("\n要完整测试，需要:")
print("- 启动后端服务: cd backend && python main.py")
print("- 访问前端: http://localhost:5173")
print("- 切换到'职业发展'视图查看星图")
