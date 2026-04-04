#!/usr/bin/env python3
"""
验证 session 是否可以用于推演
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from backend.decision.decision_info_collector import DecisionInfoCollector

# 创建收集器实例
collector = DecisionInfoCollector()

# 测试的 session_id（从前端获取）
test_session_id = input("请输入要测试的 session_id: ").strip()

print(f"\n正在检查 session: {test_session_id}")
print("=" * 80)

# 获取 session
session = collector.get_session(test_session_id)

if not session:
    print(f"❌ 会话不存在: {test_session_id}")
    print("\n可用的 sessions:")
    
    sessions_dir = "./backend/data/decision_sessions"
    import os
    for filename in os.listdir(sessions_dir):
        if filename.endswith('.json'):
            print(f"  - {filename.replace('.json', '')}")
    sys.exit(1)

print(f"✅ 会话存在")
print(f"\nSession 详情:")
print(f"  - User ID: {session.get('user_id')}")
print(f"  - Question: {session.get('initial_question')}")
print(f"  - Is Complete: {session.get('is_complete')}")
print(f"  - Current Round: {session.get('current_round')}")
print(f"  - Phase: {session.get('phase')}")
print(f"  - Created At: {session.get('created_at')}")

print(f"\nCollected Info:")
info = session.get('collected_info', {})
print(f"  - Decision Context: {len(info.get('decision_context', {}))} items")
print(f"  - User Constraints: {len(info.get('user_constraints', {}))} items")
print(f"  - Priorities: {len(info.get('priorities', {}))} items")
print(f"  - Concerns: {len(info.get('concerns', []))} items")
print(f"  - Options Mentioned: {len(info.get('options_mentioned', []))} items")

print("\n" + "=" * 80)

if session.get('is_complete'):
    print("✅ 此 session 可以用于推演")
else:
    print("❌ 此 session 不能用于推演（信息收集未完成）")
    print(f"   当前轮次: {session.get('current_round')}")
    print(f"   当前阶段: {session.get('phase')}")
