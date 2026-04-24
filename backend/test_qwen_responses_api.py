"""
测试阿里云DashScope Responses API
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_responses_api():
    """测试新的responses API"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 未配置")
        return
    
    print("🔧 初始化客户端...")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    print("📤 发送请求...")
    response = client.responses.create(
        model="qwen3.6-flash",
        input="你能做些什么？"
    )
    
    print("\n" + "="*60)
    print("📊 响应结果:")
    print("="*60)
    
    # 使用官方API的output_text
    print(response.output_text)
    
    print("\n" + "="*60)

def test_responses_api_stream():
    """测试流式responses API"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY 未配置")
        return
    
    print("🔧 初始化客户端（流式）...")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1",
    )
    
    print("📤 发送流式请求...")
    completion = client.responses.create(
        model="qwen3.6-flash",
        input="解释一下量子纠缠的原理",
        stream=True,
        extra_body={"enable_thinking": True}
    )
    
    print("\n" + "="*60)
    print("📊 流式响应:")
    print("="*60)
    
    reasoning_started = False
    answer_started = False
    
    for chunk in completion:
        if hasattr(chunk, 'output') and chunk.output:
            for item in chunk.output:
                if item.type == "reasoning":
                    if not reasoning_started:
                        print("\n【推理过程】")
                        reasoning_started = True
                    for summary in item.summary:
                        print(summary.text, end='', flush=True)
                elif item.type == "message":
                    if not answer_started:
                        print("\n\n【最终答案】")
                        answer_started = True
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                print(content_item.text, end='', flush=True)
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🚀 测试阿里云DashScope Responses API\n")
    
    print("1️⃣ 测试非流式API")
    test_responses_api()
    
    print("\n\n2️⃣ 测试流式API")
    test_responses_api_stream()
    
    print("\n✅ 测试完成")
