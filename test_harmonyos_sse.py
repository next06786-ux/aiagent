"""
测试 HarmonyOS 前端能否正确接收 SSE 流式数据
模拟前端的请求方式
"""
import requests
import json

def test_sse_stream():
    url = "http://192.168.1.192:8000/api/chat/stream"
    
    payload = {
        "user_id": "harmonyos_user",
        "message": "你好"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    print(f"📨 发送请求到: {url}")
    print(f"📦 请求体: {json.dumps(payload, ensure_ascii=False)}")
    print(f"📋 请求头: {headers}")
    print("\n" + "="*60 + "\n")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=60
        )
        
        print(f"✅ 响应状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        print("\n" + "="*60 + "\n")
        
        if response.status_code == 200:
            print("📩 开始接收流式数据...\n")
            
            count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    count += 1
                    print(f"[{count}] {line[:200]}")
                    
                    if count >= 20:  # 只显示前20条
                        print("\n... (后续数据省略)")
                        break
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_sse_stream()
