"""测试职业决策系统集成"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json

BASE_URL = "http://localhost:8000"

def test_career_graph():
    """测试职业星图"""
    print("\n" + "=" * 60)
    print("1. 测试职业星图视图")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v5/future-os/career-graph"
    data = {
        "user_id": "test_user",
        "mastered_skills": ["Python", "JavaScript", "Git", "MySQL"],
        "partial_skills": ["React", "Docker"],
        "missing_skills": ["Kubernetes", "AWS"],
        "target_direction": "Python工程师"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get("success"):
            graph_data = result["data"]
            print(f"✓ 职业星图生成成功")
            print(f"  节点数: {graph_data['metadata']['total_nodes']}")
            print(f"  边数: {graph_data['metadata']['total_edges']}")
            print(f"  技能层: {graph_data['metadata']['layer_info']['layer1']['count']} 个")
            print(f"  岗位层: {graph_data['metadata']['layer_info']['layer2']['count']} 个")
            print(f"  公司层: {graph_data['metadata']['layer_info']['layer3']['count']} 个")
            
            if 'data_sources' in graph_data['metadata']:
                print(f"  数据来源: {graph_data['metadata']['data_sources']}")
            
            return True
        else:
            print(f"✗ 失败: {result.get('message')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ 后端服务未启动")
        print("  请先启动后端: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_career_decision():
    """测试职业决策算法"""
    print("\n" + "=" * 60)
    print("2. 测试职业决策算法")
    print("=" * 60)
    
    # 检查决策算法模块
    try:
        from backend.decision_algorithm.career_decision_algorithm import (
            CareerDecisionAlgorithm,
            KnowledgeGraphCareerIntegration
        )
        
        algo = CareerDecisionAlgorithm()
        print("✓ 职业决策算法模块加载成功")
        
        # 测试技能ROI计算
        print("\n测试技能ROI计算:")
        skill_roi = algo.calculate_skill_roi(
            skill_name="Python",
            current_level=0.6,
            target_level=0.9,
            learning_time_months=6
        )
        print(f"  Python技能ROI: {skill_roi:.2f}")
        
        # 测试职业路径模拟
        print("\n测试职业路径模拟:")
        from backend.decision_algorithm.career_decision_algorithm import Skill, PersonalCapital
        
        current_capital = PersonalCapital(
            skills=[
                Skill("Python", 0.7, 3),
                Skill("Django", 0.6, 2)
            ],
            network_size=50,
            network_quality=0.6,
            resilience=0.7,
            optimism=0.8,
            self_efficacy=0.7,
            savings=10,
            debt=0
        )
        
        target_skills = [
            Skill("Python", 0.9, 5),
            Skill("Django", 0.8, 4),
            Skill("Docker", 0.7, 2)
        ]
        
        path = algo.simulate_career_path(
            current_capital=current_capital,
            target_skills=target_skills,
            time_horizon_years=3
        )
        
        print(f"  路径长度: {len(path)} 个阶段")
        print(f"  最终人力资本: {path[-1]['human_capital']:.2f}")
        
        return True
        
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_career_simulation():
    """测试职业决策模拟推演"""
    print("\n" + "=" * 60)
    print("3. 测试职业决策模拟推演")
    print("=" * 60)
    
    try:
        from backend.decision.career_simulation_integration import CareerSimulationIntegration
        import asyncio
        
        sim = CareerSimulationIntegration()
        print("✓ 职业模拟推演模块加载成功")
        
        # 测试推演
        user_id = "test_user"
        question = "我应该选择去字节跳动还是阿里巴巴？"
        options = [
            {
                "id": "option_1",
                "title": "字节跳动 - Python后端工程师",
                "description": "薪资30万，996工作制，技术栈先进"
            },
            {
                "id": "option_2", 
                "title": "阿里巴巴 - 全栈工程师",
                "description": "薪资28万，大小周，平台大"
            }
        ]
        
        print("\n开始推演...")
        
        # 使用asyncio运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                sim.simulate_career_decision_with_agents(user_id, question, options)
            )
        finally:
            loop.close()
        
        if result:
            print(f"✓ 推演完成")
            print(f"  分支数: {len(result)}")
            
            for branch in result[:2]:
                print(f"\n  分支: {branch['option_title']}")
                print(f"    综合评分: {branch.get('overall_score', 'N/A')}")
                if 'timeline' in branch:
                    print(f"    时间线节点: {len(branch['timeline'])} 个")
                if 'recommendation' in branch:
                    print(f"    推荐度: {branch['recommendation']}")
            
            return True
        else:
            print(f"✗ 推演返回空结果")
            return False
            
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("职业决策系统集成测试")
    print("=" * 60)
    
    results = {
        "职业星图": test_career_graph(),
        "决策算法": test_career_decision(),
        "模拟推演": test_career_simulation()
    }
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！职业决策系统已完整集成")
    else:
        print("⚠ 部分测试失败，请检查上述错误信息")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
