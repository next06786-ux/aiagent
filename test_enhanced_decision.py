"""
测试增强决策系统
信息收集（Qwen3.5-plus）+ 决策模拟（本地模型+LoRA）
新流程：用户先说 -> AI问"还有吗" -> 用户说"没了" -> AI开始针对性提问
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_info_collection_flow():
    """测试完整的信息收集流程"""
    print("="*60)
    print("测试：信息收集 + 决策模拟流程")
    print("="*60)
    
    # 1. 开始信息收集
    print("\n【步骤1】开始信息收集...")
    start_response = requests.post(
        f"{BASE_URL}/api/decision/enhanced/collect/start",
        json={
            "user_id": "test_user",
            "initial_question": "我是大三学生，毕业后不知道该考研还是工作"
        }
    )
    
    if start_response.status_code != 200:
        print(f"❌ 开始信息收集失败: {start_response.text}")
        return
    
    start_data = start_response.json()
    print(f"✅ 信息收集已开始")
    print(f"   会话ID: {start_data['data']['session_id']}")
    print(f"   阶段: {start_data['data']['phase']}")
    print(f"   提示: {start_data['data']['message']}")
    
    session_id = start_data['data']['session_id']
    
    # 2. 用户自由表达阶段
    print(f"\n{'='*60}")
    print("【阶段1：用户自由表达】")
    print("="*60)
    
    user_free_talks = [
        "我学的是计算机专业，成绩中等，家里经济条件一般。我比较想提升学历，但也担心考不上浪费时间。",
        "我最看重的是未来的发展空间和收入，希望能有稳定的工作。时间上希望能尽快独立，不想再让家里负担。",
        "没有了"  # 用户表示没有更多要说的
    ]
    
    for i, user_response in enumerate(user_free_talks, 1):
        print(f"\n第 {i} 轮 - 用户说:")
        print(f"   {user_response}")
        
        continue_response = requests.post(
            f"{BASE_URL}/api/decision/enhanced/collect/continue",
            json={
                "session_id": session_id,
                "user_response": user_response
            }
        )
        
        if continue_response.status_code != 200:
            print(f"❌ 继续收集失败: {continue_response.text}")
            return
        
        continue_data = continue_response.json()
        
        print(f"   阶段: {continue_data['data'].get('phase', 'unknown')}")
        
        if continue_data['data'].get('is_complete'):
            print(f"\n✅ 信息收集完成！")
            print(f"   总结: {continue_data['data'].get('summary', '无')}")
            break
        else:
            print(f"   AI问: {continue_data['data']['ai_question']}")
            
            # 如果进入AI提问阶段，跳出循环
            if continue_data['data'].get('phase') == 'ai_questioning':
                print(f"\n{'='*60}")
                print("【阶段2：AI针对性提问】")
                print("="*60)
                break
        
        time.sleep(1)
    
    # 3. AI提问阶段
    if continue_data['data'].get('phase') == 'ai_questioning':
        ai_questioning_responses = [
            "我主要担心考研失败后既浪费时间又错过校招，但直接工作又觉得学历不够竞争力不强。",
            "我的专业能力还可以，做过几个项目，但不算特别突出。家里希望我能稳定一些。"
        ]
        
        for i, user_response in enumerate(ai_questioning_responses, 1):
            print(f"\n第 {i} 轮 - 用户回答:")
            print(f"   {user_response}")
            
            continue_response = requests.post(
                f"{BASE_URL}/api/decision/enhanced/collect/continue",
                json={
                    "session_id": session_id,
                    "user_response": user_response
                }
            )
            
            if continue_response.status_code != 200:
                print(f"❌ 继续收集失败: {continue_response.text}")
                return
            
            continue_data = continue_response.json()
            
            if continue_data['data'].get('is_complete'):
                print(f"\n✅ 信息收集完成！")
                print(f"   总结: {continue_data['data'].get('summary', '无')}")
                print(f"\n收集到的信息:")
                collected_info = continue_data['data']['collected_info']
                print(f"   - 决策背景: {collected_info.get('decision_context', {})}")
                print(f"   - 约束条件: {collected_info.get('user_constraints', {})}")
                print(f"   - 优先级: {collected_info.get('priorities', {})}")
                print(f"   - 顾虑: {collected_info.get('concerns', [])}")
                print(f"   - 提到的选项: {collected_info.get('options_mentioned', [])}")
                break
            else:
                print(f"   AI问: {continue_data['data']['ai_question']}")
            
            time.sleep(1)
    
    # 4. 使用收集的信息进行决策模拟
    print(f"\n{'='*60}")
    print("【步骤2：开始决策模拟（使用本地模型+LoRA）】")
    print("="*60)
    
    simulate_response = requests.post(
        f"{BASE_URL}/api/decision/enhanced/simulate/with-collection",
        json={
            "session_id": session_id,
            "options": [
                {"title": "考研", "description": "继续深造，提升学历"},
                {"title": "直接工作", "description": "进入职场，积累经验"}
            ],
            "use_lora": False  # 先不使用LoRA测试
        }
    )
    
    if simulate_response.status_code != 200:
        print(f"❌ 决策模拟失败: {simulate_response.text}")
        return
    
    simulate_data = simulate_response.json()
    print(f"✅ 决策模拟完成！")
    print(f"   模拟ID: {simulate_data['data']['simulation_id']}")
    print(f"   使用LoRA: {simulate_data['data']['used_lora']}")
    
    # 显示模拟结果
    print(f"\n模拟结果:")
    for option in simulate_data['data']['options']:
        print(f"\n选项: {option['title']}")
        print(f"   综合得分: {option['final_score']:.1f}/100")
        print(f"   风险等级: {option['risk_level']:.2f}")
        print(f"   时间线事件数: {len(option['timeline'])}")
    
    print(f"\nAI推荐:")
    recommendation = simulate_data['data']['recommendation']
    print(f"   {recommendation[:200]}..." if len(recommendation) > 200 else f"   {recommendation}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("增强决策系统测试")
    print("="*60)
    
    try:
        test_info_collection_flow()
        
        print("\n" + "="*60)
        print("✅ 测试完成")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("   请确保后端服务已启动")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
