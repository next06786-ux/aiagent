"""
测试LLM服务的Responses API集成
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.llm_service import LLMService
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_llm_service_chat():
    """测试LLM服务的对话功能"""
    print("🔧 初始化LLM服务...")
    service = LLMService(provider="qwen")
    
    if not service.enabled:
        print("❌ LLM服务未启用")
        return
    
    print(f"✅ LLM服务已启用，模型: {service.model}")
    
    messages = [
        {"role": "user", "content": "9.9和9.11哪个大？请详细解释你的推理过程。"}
    ]
    
    print("\n📤 发送请求...")
    response = service.chat(messages, temperature=0.7)
    
    print("\n" + "="*60)
    print("📊 响应结果:")
    print("="*60)
    print(response)
    print("="*60)

def test_llm_service_stream():
    """测试LLM服务的流式对话功能"""
    print("\n🔧 测试流式对话...")
    service = LLMService(provider="qwen")
    
    if not service.enabled:
        print("❌ LLM服务未启用")
        return
    
    messages = [
        {"role": "user", "content": "解释一下相对论的基本原理"}
    ]
    
    print("\n📤 发送流式请求...")
    print("\n" + "="*60)
    print("📊 流式响应:")
    print("="*60)
    
    reasoning_started = False
    answer_started = False
    
    for chunk in service.chat_stream(messages, temperature=0.7):
        if chunk["type"] == "thinking":
            if not reasoning_started:
                print("\n【推理过程】")
                reasoning_started = True
            print(chunk["content"], end='', flush=True)
        elif chunk["type"] == "answer":
            if not answer_started:
                print("\n\n【最终答案】")
                answer_started = True
            print(chunk["content"], end='', flush=True)
        elif chunk["type"] == "error":
            print(f"\n❌ 错误: {chunk['content']}")
    
    print("\n" + "="*60)

def test_model_comparison():
    """测试不同模型的对比"""
    print("\n🔧 测试模型对比...")
    
    test_question = "什么是机器学习？"
    
    # 测试qwen-turbo（旧API）
    print("\n1️⃣ 测试 qwen-turbo (旧API):")
    service_turbo = LLMService(provider="qwen")
    service_turbo.model = "qwen-turbo"
    
    messages = [{"role": "user", "content": test_question}]
    response_turbo = service_turbo.chat(messages)
    print(f"响应: {response_turbo[:200]}...")
    
    # 测试qwen3.6-flash（新API）
    print("\n2️⃣ 测试 qwen3.6-flash (新API):")
    service_plus = LLMService(provider="qwen")
    service_plus.model = "qwen3.6-flash"
    
    response_plus = service_plus.chat(messages)
    print(f"响应: {response_plus[:200]}...")

if __name__ == "__main__":
    print("🚀 测试LLM服务的Responses API集成\n")
    
    try:
        # 测试1: 基本对话
        test_llm_service_chat()
        
        # 测试2: 流式对话
        test_llm_service_stream()
        
        # 测试3: 模型对比
        test_model_comparison()
        
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
