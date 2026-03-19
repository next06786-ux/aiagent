#!/usr/bin/env python3
"""
测试 SGLang 连接
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv("backend/.env")

def test_direct_http():
    """直接 HTTP 测试"""
    import httpx
    
    server_url = os.getenv("SGLANG_SERVER_URL", "http://localhost:8000")
    print(f"🔗 SGLang 服务器: {server_url}")
    
    # 健康检查
    print("\n1️⃣ 健康检查...")
    try:
        resp = httpx.get(f"{server_url}/health", timeout=10)
        print(f"   状态: {resp.status_code}")
        if resp.status_code == 200:
            print("   ✅ 服务器健康")
        else:
            print(f"   ⚠️ 响应: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    
    # 模型信息
    print("\n2️⃣ 获取模型信息...")
    try:
        resp = httpx.get(f"{server_url}/v1/models", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ 模型: {data}")
        else:
            print(f"   响应: {resp.text[:200]}")
    except Exception as e:
        print(f"   ⚠️ {e}")
    
    # 测试聊天
    print("\n3️⃣ 测试聊天...")
    model_name = os.getenv("SGLANG_MODEL_NAME", "Qwen/Qwen3.5-9B")
    try:
        resp = httpx.post(
            f"{server_url}/v1/chat/completions",
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "你好，请用一句话介绍自己"}],
                "max_tokens": 100,
                "temperature": 0.7
            },
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            print(f"   ✅ AI 回复: {content}")
        else:
            print(f"   ❌ 错误: {resp.status_code}")
            print(f"   {resp.text[:300]}")
    except Exception as e:
        print(f"   ❌ 聊天失败: {e}")
        return False
    
    return True


def test_llm_service():
    """测试 LLM Service"""
    print("\n4️⃣ 测试 LLM Service...")
    try:
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        if llm is None:
            print("   ❌ LLM 服务未初始化")
            return False
        
        if not llm.enabled:
            print("   ❌ LLM 服务未启用")
            return False
        
        print(f"   Provider: {llm.provider.value}")
        print(f"   Model: {llm.model}")
        
        # 测试聊天
        response = llm.chat([
            {"role": "user", "content": "1+1等于几？只回答数字"}
        ])
        print(f"   ✅ 回复: {response}")
        
        return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("  SGLang 连接测试")
    print("=" * 50)
    
    # 显示配置
    print(f"\n📋 当前配置:")
    print(f"   LLM_PROVIDER: {os.getenv('LLM_PROVIDER', '未设置')}")
    print(f"   SGLANG_SERVER_URL: {os.getenv('SGLANG_SERVER_URL', '未设置')}")
    print(f"   SGLANG_MODEL_NAME: {os.getenv('SGLANG_MODEL_NAME', '未设置')}")
    
    # 测试
    http_ok = test_direct_http()
    
    if http_ok:
        service_ok = test_llm_service()
    
    print("\n" + "=" * 50)
    if http_ok:
        print("✅ SGLang 连接正常！")
        print("\n下一步：")
        print("  1. 启动后端: python -m uvicorn backend.main:app --reload")
        print("  2. 测试 API: curl http://localhost:8000/health")
    else:
        print("❌ 连接失败，请检查：")
        print("  1. SGLang 服务器是否启动")
        print("  2. SGLANG_SERVER_URL 是否正确")
        print("  3. 防火墙/端口是否开放")
