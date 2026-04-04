#!/usr/bin/env python3
"""
测试 session 检查
"""
import json
import os

# 读取所有 session 文件
sessions_dir = "./backend/data/decision_sessions"
sessions = []

for filename in os.listdir(sessions_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(sessions_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            session = json.load(f)
            sessions.append({
                'session_id': session['session_id'],
                'user_id': session['user_id'],
                'question': session['initial_question'],
                'is_complete': session.get('is_complete', False),
                'round': session.get('current_round', 0),
                'created_at': session.get('created_at', ''),
            })

# 按创建时间排序
sessions.sort(key=lambda x: x['created_at'], reverse=True)

print("=" * 80)
print("所有 Decision Sessions")
print("=" * 80)

for i, session in enumerate(sessions, 1):
    print(f"\n{i}. Session ID: {session['session_id']}")
    print(f"   User ID: {session['user_id']}")
    print(f"   Question: {session['question']}")
    print(f"   Is Complete: {session['is_complete']}")
    print(f"   Round: {session['round']}")
    print(f"   Created: {session['created_at']}")

print("\n" + "=" * 80)
print(f"总共 {len(sessions)} 个 sessions")
print("=" * 80)

# 找出已完成的 sessions
completed = [s for s in sessions if s['is_complete']]
print(f"\n已完成的 sessions: {len(completed)}")
for session in completed:
    print(f"  - {session['session_id']}")
