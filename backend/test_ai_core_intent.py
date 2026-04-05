#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI核心智能路由功能（LLM驱动）
"""
import sys
import os

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_core.intent_router import intent_router


def test_intent_recognition():
    """测试LLM驱动的意图识别"""
    print("\n" + "="*60)
    print("AI核心智能路由测试（LLM驱动）")
    print("="*60)
    
    test_cases = [
        # 明确的导航意图
        "我的人际关系图谱咋样了",
        "我最近的有关人际关系的问题",
        "想看看我的社交网络",
        
        # 决策相关
        "我应该跳槽吗",
        "纠结要不要考研",
        
        # 职业相关
        "想看看我的职业发展情况",
        "我的技能树怎么样",
        
        # 教育相关
        "我要申请哪些学校",
        "我的GPA够不够",
        
        # 平行人生
        "如果我选择创业会怎样",
        "假如我当时选了另一条路",
        
        # 涌现洞察
        "帮我分析一下最近的状态",
        "我最近有什么模式吗",
        
        # 普通对话（无导航意图）
        "今天天气怎么样",
        "你好",
        "谢谢",
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {message}")
        print("-" * 60)
        
        result = intent_router.analyze_intent(message)
        
        if result["has_navigation_intent"]:
            print(f"[OK] 检测到导航意图")
            print(f"  分析: {result.get('analysis', 'N/A')}")
            print(f"\n  主要推荐: {result['primary_route']['name']}")
            print(f"  置信度: {result['primary_route']['confidence']}")
            print(f"  路径: {result['primary_route']['path']}")
            print(f"  理由: {result['primary_route'].get('reason', 'N/A')}")
            
            if result['primary_route'].get('view_mode'):
                print(f"  视图模式: {result['primary_route']['view_mode']}")
            
            if len(result["suggested_routes"]) > 1:
                print(f"\n  其他建议:")
                for route in result["suggested_routes"][1:]:
                    print(f"    - {route['name']} (置信度: {route['confidence']})")
        else:
            print(f"[SKIP] 未检测到导航意图（普通对话）")
            if result.get('analysis'):
                print(f"  分析: {result['analysis']}")


if __name__ == "__main__":
    test_intent_recognition()
