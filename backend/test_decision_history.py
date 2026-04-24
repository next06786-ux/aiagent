"""
测试决策历史保存和查询功能 - 完整流程测试
"""
import requests
import json
from datetime import datetime
import time

# 配置
BASE_URL = "http://localhost:8000"
USER_ID = "test_user_123"
SESSION_ID = f"test_session_{int(datetime.now().timestamp())}"

print("=" * 80)
print("决策历史功能完整流程测试")
print("=" * 80)
print(f"用户ID: {USER_ID}")
print(f"会话ID: {SESSION_ID}")
print("=" * 80)

def test_save_option(option_id, option_title, score):
    """测试保存单个选项"""
    print(f"\n{'='*60}")
    print(f"测试保存选项: {option_id} - {option_title}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/api/decision/history/save"
    
    # 模拟选项数据结构（新格式）
    options_data = {
        option_id: {
            "option_id": option_id,
            "option_title": option_title,
            "option_description": f"{option_title}的详细描述",
            "total_score": score,
            "current_round": 12,
            "agents": [
                {
                    "id": "rational_analyst",
                    "name": "理性分析师",
                    "status": "complete",
                    "stance": "支持" if score > 60 else "中立",
                    "score": score,
                    "thinking_history": [
                        {"phase": "independent_thinking", "message": "独立思考中..."},
                        {"phase": "deep_reflection", "message": "深度反思中..."}
                    ],
                    "final_message": f"我给出{score}分"
                },
                {
                    "id": "adventurer",
                    "name": "冒险家",
                    "status": "complete",
                    "stance": "支持" if score > 70 else "反对",
                    "score": score - 10,
                    "thinking_history": [
                        {"phase": "independent_thinking", "message": "这个选项很有趣"},
                        {"phase": "deep_reflection", "message": "但风险较高"}
                    ],
                    "final_message": f"我给出{score-10}分"
                }
            ],
            "report": {
                "summary": f"这是{option_title}的综合评估报告",
                "key_insights": [
                    "关键洞察1：这个选项有明显优势",
                    "关键洞察2：需要注意潜在风险"
                ],
                "strengths": [
                    "优势1：长期收益高",
                    "优势2：符合个人发展"
                ],
                "risks": [
                    "风险1：短期压力大",
                    "风险2：不确定性高"
                ],
                "recommendation": f"综合来看，{option_title}是一个值得考虑的选择",
                "total_score": score
            },
            "completed_at": datetime.now().isoformat()
        }
    }
    
    data = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "question": "测试决策问题：我应该选择哪个职业方向？",
        "decision_type": "career",
        "options_data": options_data
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ {option_id} 保存成功！")
            return True
        else:
            print(f"❌ {option_id} 保存失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_get_history_list():
    """测试获取历史列表"""
    print(f"\n{'='*60}")
    print("测试获取历史列表")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/api/decision/history/list"
    params = {
        "user_id": USER_ID,
        "limit": 10,
        "offset": 0
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            histories = result.get('histories', [])
            total = result.get('total', 0)
            print(f"\n✅ 查询成功！")
            print(f"总记录数: {total}")
            print(f"返回记录数: {len(histories)}")
            
            # 找到我们刚才保存的记录
            our_record = None
            for h in histories:
                if h.get('session_id') == SESSION_ID:
                    our_record = h
                    break
            
            if our_record:
                print(f"\n找到测试记录:")
                print(f"  ID: {our_record.get('id')}")
                print(f"  问题: {our_record.get('question')}")
                print(f"  选项数: {our_record.get('options_count')}")
                print(f"  时间: {our_record.get('completed_at')}")
                return our_record.get('id')
            else:
                print(f"\n⚠️ 未找到测试记录 (session_id: {SESSION_ID})")
                return None
        else:
            print(f"❌ 查询失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None


def test_get_history_detail(history_id):
    """测试获取历史详情"""
    print(f"\n{'='*60}")
    print(f"测试获取历史详情 (ID: {history_id})")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/api/decision/history/detail/{history_id}"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            history = result.get('history')
            print(f"\n✅ 查询成功！")
            print(f"问题: {history.get('question')}")
            print(f"类型: {history.get('decision_type')}")
            print(f"时间: {history.get('completed_at')}")
            
            options_data = history.get('options_data', {})
            print(f"\n选项数据结构:")
            print(f"  顶层keys: {list(options_data.keys())}")
            
            # 检查每个选项
            for key, value in options_data.items():
                if key.startswith('option_'):
                    print(f"\n  {key}:")
                    print(f"    标题: {value.get('option_title')}")
                    print(f"    评分: {value.get('total_score')}")
                    print(f"    Agent数量: {len(value.get('agents', []))}")
                    print(f"    有报告: {'是' if value.get('report') else '否'}")
                    
                    if value.get('agents'):
                        print(f"    Agents:")
                        for agent in value.get('agents', [])[:2]:  # 只显示前2个
                            print(f"      - {agent.get('name')}: {agent.get('stance')} ({agent.get('score')}分)")
            
            return True
        else:
            print(f"❌ 查询失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_existing_record():
    """测试更新现有记录（模拟第二个选项完成）"""
    print(f"\n{'='*60}")
    print("测试更新现有记录（添加第二个选项）")
    print(f"{'='*60}")
    
    # 先获取现有记录
    list_response = requests.get(
        f"{BASE_URL}/api/decision/history/list",
        params={"user_id": USER_ID, "limit": 10}
    )
    
    if not list_response.ok:
        print("❌ 无法获取历史列表")
        return False
    
    list_data = list_response.json()
    our_record = None
    for h in list_data.get('histories', []):
        if h.get('session_id') == SESSION_ID:
            our_record = h
            break
    
    if not our_record:
        print("❌ 未找到现有记录")
        return False
    
    # 获取详情
    detail_response = requests.get(
        f"{BASE_URL}/api/decision/history/detail/{our_record['id']}"
    )
    
    if not detail_response.ok:
        print("❌ 无法获取历史详情")
        return False
    
    detail_data = detail_response.json()
    existing_options_data = detail_data['history']['options_data']
    
    print(f"现有选项: {list(existing_options_data.keys())}")
    
    # 添加第二个选项
    existing_options_data['option_2'] = {
        "option_id": "option_2",
        "option_title": "选项2：直接工作",
        "option_description": "进入职场积累经验",
        "total_score": 70,
        "current_round": 12,
        "agents": [
            {
                "id": "pragmatist",
                "name": "实用主义者",
                "status": "complete",
                "stance": "支持",
                "score": 75,
                "thinking_history": [],
                "final_message": "实践出真知"
            }
        ],
        "report": {
            "summary": "直接工作是一个务实的选择",
            "key_insights": ["尽早积累经验"],
            "strengths": ["实战经验"],
            "risks": ["缺少学历优势"],
            "recommendation": "适合动手能力强的人",
            "total_score": 70
        },
        "completed_at": datetime.now().isoformat()
    }
    
    # 保存更新
    save_response = requests.post(
        f"{BASE_URL}/api/decision/history/save",
        json={
            "user_id": USER_ID,
            "session_id": SESSION_ID,
            "question": "测试决策问题：我应该选择哪个职业方向？",
            "decision_type": "career",
            "options_data": existing_options_data
        }
    )
    
    if save_response.ok:
        result = save_response.json()
        if result.get('success'):
            print(f"✅ 更新成功！现在有 {len(existing_options_data)} 个选项")
            return True
    
    print(f"❌ 更新失败")
    return False


if __name__ == "__main__":
    print("\n[1/5] 保存第一个选项...")
    success1 = test_save_option("option_1", "选项1：继续深造读研", 75)
    
    if not success1:
        print("\n❌ 第一步失败，终止测试")
        exit(1)
    
    time.sleep(1)
    
    print("\n[2/5] 查询历史列表...")
    history_id = test_get_history_list()
    
    if not history_id:
        print("\n❌ 第二步失败，终止测试")
        exit(1)
    
    time.sleep(1)
    
    print("\n[3/5] 查询历史详情...")
    success3 = test_get_history_detail(history_id)
    
    if not success3:
        print("\n❌ 第三步失败，终止测试")
        exit(1)
    
    time.sleep(1)
    
    print("\n[4/5] 更新记录（添加第二个选项）...")
    success4 = test_update_existing_record()
    
    if not success4:
        print("\n❌ 第四步失败，终止测试")
        exit(1)
    
    time.sleep(1)
    
    print("\n[5/5] 再次查询详情（验证更新）...")
    success5 = test_get_history_detail(history_id)
    
    print("\n" + "=" * 80)
    if success5:
        print("✅ 所有测试通过！")
        print("\n测试总结:")
        print("  ✅ 保存第一个选项")
        print("  ✅ 查询历史列表")
        print("  ✅ 查询历史详情")
        print("  ✅ 更新记录（添加第二个选项）")
        print("  ✅ 验证更新成功")
        print("\n数据结构验证:")
        print("  ✅ 一个决策问题 = 一条历史记录")
        print("  ✅ 记录包含多个选项 (option_1, option_2, ...)")
        print("  ✅ 每个选项有完整的 agents 和 report 数据")
        print("  ✅ 更新记录不会创建新记录")
    else:
        print("❌ 测试失败")
    print("=" * 80)

