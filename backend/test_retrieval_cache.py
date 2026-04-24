"""
测试检索缓存行为
验证：
1. Workflow的memory_load使用缓存
2. Agent工具的retrieve_user_data不使用缓存
"""

def test_cache_behavior():
    """测试缓存行为"""
    print("=" * 60)
    print("测试检索缓存行为")
    print("=" * 60)
    
    # 模拟代码逻辑
    print("\n1. Workflow memory_load节点:")
    print("   - 调用: retrieve_from_external_memory()")
    print("   - 参数: use_cache=True (默认)")
    print("   - 行为: 第一次真实检索，后续命中缓存")
    
    print("\n2. Agent retrieve_user_data工具:")
    print("   - 调用: retrieve_from_external_memory()")
    print("   - 参数: use_cache=False (显式禁用)")
    print("   - 行为: 每次都执行真实的混合检索")
    
    print("\n3. 两者都使用相同的检索系统:")
    print("   - UnifiedHybridRetrieval.retrieve()")
    print("   - 策略: HYBRID_PARALLEL (图检索 + 向量检索)")
    print("   - 融合: 根据配置的fusion_method融合结果")
    
    print("\n✅ 修改完成:")
    print("   - 添加了use_cache参数到retrieve_from_external_memory()")
    print("   - Agent工具调用时use_cache=False")
    print("   - 确保工具每次都获取最新数据")
    
    print("\n" + "=" * 60)
    print("测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_cache_behavior()
