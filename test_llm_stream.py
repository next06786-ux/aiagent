"""
测试LLM流式服务
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.llm.llm_service import get_llm_service
import time

def test_llm_stream():
    print("=" * 60)
    print("测试LLM流式服务")
    print("=" * 60)
    
    # 获取LLM服务
    llm_service = get_llm_service()
    print(f"\n1. LLM服务实例: {llm_service}")
    print(f"   类型: {type(llm_service)}")
    print(f"   enabled: {getattr(llm_service, 'enabled', 'N/A')}")
    print(f"   provider: {getattr(llm_service, 'provider', 'N/A')}")
    
    if not llm_service or not getattr(llm_service, "enabled", False):
        print("\n❌ LLM服务未就绪！")
        return
    
    print("\n✓ LLM服务就绪")
    
    # 测试流式调用
    print("\n2. 测试流式调用...")
    messages = [{
        "role": "system",
        "content": "你是一个助手。"
    }, {
        "role": "user",
        "content": "请用一句话介绍Python编程语言。"
    }]
    
    print(f"   发送消息: {messages[1]['content']}")
    
    start_time = time.time()
    chunk_count = 0
    total_content = ""
    
    try:
        print("\n3. 开始接收流式响应:")
        for chunk_data in llm_service.chat_stream(messages, temperature=0.7):
            chunk_count += 1
            chunk_type = chunk_data.get("type", "unknown")
            content = chunk_data.get("content", "")
            
            if chunk_count <= 5:
                print(f"   Chunk #{chunk_count}: type={chunk_type}, content='{content[:50]}...'")
            
            if chunk_type == "answer":
                total_content += content
            elif chunk_type == "error":
                print(f"\n❌ 错误: {content}")
                break
        
        elapsed = time.time() - start_time
        print(f"\n4. 完成!")
        print(f"   总chunk数: {chunk_count}")
        print(f"   总内容长度: {len(total_content)} 字符")
        print(f"   耗时: {elapsed:.2f} 秒")
        print(f"   完整内容: {total_content}")
        
        if chunk_count == 0:
            print("\n⚠️  警告: 没有收到任何chunk！")
        else:
            print("\n✓ 流式服务工作正常")
            
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_stream()
