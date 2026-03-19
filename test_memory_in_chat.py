"""
测试在实际对话中的历史记忆检索
"""

import sys
sys.path.append('backend')

from llm.deep_ai_processor import get_deep_ai_processor


def test_memory_in_chat():
    """测试对话中的记忆检索"""
    print("=" * 80)
    print("测试：第2层历史记忆检索在实际对话中的表现")
    print("=" * 80)
    
    # 创建处理器（会自动初始化测试记忆）
    processor = get_deep_ai_processor("test_user")
    
    # 测试查询
    test_queries = [
        "我最近学习效率很低，怎么办？",
        "我睡眠不好，经常失眠",
        "如何管理时间？",
        "我想改善人际关系"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}: {query}")
        print(f"{'=' * 80}")
        
        # 处理查询
        result = processor.process(
            user_message=query,
            user_context={},
            progress_callback=lambda layer, msg: print(f"  [{layer}层] {msg}"),
            thinking_callback=lambda text: print(text, end='')
        )
        
        # 显示第2层的检索结果
        memory_layer = result['layers'].get('memory', {})
        similar_memories = memory_layer.get('similar_memories', [])
        
        print(f"\n📊 第2层检索结果:")
        print(f"   找到 {len(similar_memories)} 条相关记忆")
        
        if similar_memories:
            for j, mem in enumerate(similar_memories[:3], 1):
                print(f"   {j}. [{mem['type']}] {mem['content'][:60]}...")
                print(f"      相似度: {mem['similarity']:.1%}, 时间: {mem['timestamp'][:10]}")
        else:
            print(f"   ⚠️  未检索到相关记忆")
        
        print(f"\n💬 AI回复:")
        print(f"   {result['final_response'][:200]}...")
        
        input(f"\n按回车继续下一个测试...")


if __name__ == "__main__":
    test_memory_in_chat()
