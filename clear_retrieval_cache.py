"""
清除混合检索缓存
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.learning.kg_rag_integration import get_kg_rag_system, clear_kg_rag_instances

# 清除所有实例（包括缓存）
clear_kg_rag_instances()

print("✅ 混合检索缓存已清除")
print("请重新运行测试")
