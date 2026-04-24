"""
测试流式输出功能
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.llm_service import get_llm_service


async def test_streaming():
    """测试LLM流式输出"""
    print("🧪 测试流式输出功能\n")
    
    llm = get_llm_service()
    if not llm or not llm.enabled:
        print("❌ LLM服务未启用")
        return
    
    print(f"✅ LLM服务已启用: {llm.provider.value}\n")
    
    messages = [
        {"role": "user", "content": "请用3句话介绍人工智能的发展历史"}
    ]
    
    print("📝 开始流式生成...\n")
    print("-" * 60)
    
    accumulated = ""
    chunk_count = 0
    
    try:
        async for chunk in llm.chat_stream_async(messages, temperature=0.7):
            chunk_type = chunk.get("type")
            content = chunk.get("content", "")
            
            if chunk_type == "thinking":
                print(f"💭 [思考] {content}", end="", flush=True)
            elif chunk_type == "answer":
                print(content, end="", flush=True)
                accumulated += content
                chunk_count += 1
            elif chunk_type == "error":
                print(f"\n❌ 错误: {content}")
                return
        
        print("\n" + "-" * 60)
        print(f"\n✅ 流式生成完成!")
        print(f"📊 统计: 共{chunk_count}个片段, 总长度{len(accumulated)}字符")
        print(f"\n完整内容:\n{accumulated}")
        
    except Exception as e:
        print(f"\n❌ 流式生成失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_streaming())
