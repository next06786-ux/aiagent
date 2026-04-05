# -*- coding: utf-8 -*-
"""简单测试LLM意图识别"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试单个案例
test_message = "我的人际关系图谱咋样了"

print(f"测试消息: {test_message}")
print("-" * 60)

try:
    from backend.ai_core.intent_router import intent_router
    result = intent_router.analyze_intent(test_message)
    
    print(f"has_navigation_intent: {result['has_navigation_intent']}")
    print(f"analysis: {result.get('analysis', 'N/A')}")
    
    if result['primary_route']:
        print(f"\n主要推荐:")
        print(f"  name: {result['primary_route']['name']}")
        print(f"  path: {result['primary_route']['path']}")
        print(f"  confidence: {result['primary_route']['confidence']}")
        print(f"  view_mode: {result['primary_route'].get('view_mode', 'N/A')}")
    
    print("\n成功!")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
