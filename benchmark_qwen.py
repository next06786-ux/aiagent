"""
Qwen 模型性能测试
测试推理速度和响应时间
"""
import requests
import time
import json

def benchmark_qwen():
    """性能测试"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Qwen3.5-0.8B 性能测试")
    print("=" * 60)
    print()
    
    # 测试用例
    test_cases = [
        {
            "name": "短文本生成 (50 tokens)",
            "prompt": "你好",
            "max_tokens": 50
        },
        {
            "name": "中等文本生成 (100 tokens)",
            "prompt": "请介绍一下人工智能的发展历史",
            "max_tokens": 100
        },
        {
            "name": "长文本生成 (200 tokens)",
            "prompt": "请详细解释什么是深度学习，包括其原理和应用",
            "max_tokens": 200
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['name']}")
        print(f"输入: {test['prompt']}")
        print(f"最大生成: {test['max_tokens']} tokens")
        print("-" * 60)
        
        # 发送请求
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "qwen3.5-0.8b",
                "messages": [
                    {"role": "user", "content": test['prompt']}
                ],
                "max_tokens": test['max_tokens'],
                "temperature": 0.7
            }
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            output = result['choices'][0]['message']['content']
            
            # 计算实际生成的 token 数（粗略估计：中文 1 字 ≈ 1.5 tokens）
            output_length = len(output)
            estimated_tokens = int(output_length * 1.5)
            tokens_per_second = estimated_tokens / elapsed if elapsed > 0 else 0
            
            print(f"✅ 成功")
            print(f"⏱️  耗时: {elapsed:.2f} 秒")
            print(f"📝 输出长度: {output_length} 字")
            print(f"🚀 估计速度: {tokens_per_second:.1f} tokens/s")
            print(f"💬 输出: {output[:100]}{'...' if len(output) > 100 else ''}")
            
            results.append({
                "test": test['name'],
                "elapsed": elapsed,
                "tokens_per_second": tokens_per_second
            })
        else:
            print(f"❌ 失败: {response.status_code}")
    
    # 总结
    print("\n" + "=" * 60)
    print("性能总结")
    print("=" * 60)
    
    if results:
        avg_speed = sum(r['tokens_per_second'] for r in results) / len(results)
        print(f"\n平均推理速度: {avg_speed:.1f} tokens/s")
        print()
        
        # 性能评级
        if avg_speed >= 40:
            rating = "🌟 优秀"
            comment = "性能很好，接近理论上限"
        elif avg_speed >= 30:
            rating = "✅ 良好"
            comment = "性能正常，符合预期"
        elif avg_speed >= 20:
            rating = "⚠️ 一般"
            comment = "性能偏慢，可能需要优化"
        else:
            rating = "❌ 较慢"
            comment = "性能较差，建议检查配置"
        
        print(f"性能评级: {rating}")
        print(f"评价: {comment}")
        print()
        
        # 对比参考
        print("参考对比:")
        print("  - RTX 3050 预期: 30-40 tokens/s")
        print("  - RTX 3060: 40-60 tokens/s")
        print("  - RTX 4090: 80-120 tokens/s")
        print("  - 云端 API: 100-200 tokens/s")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        benchmark_qwen()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("请确保已启动: start_qwen_server.bat")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
