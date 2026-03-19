"""
测试 LoRA 系统集成
验证 API 和调度器是否正常工作
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_lora_status():
    """测试获取 LoRA 状态"""
    print("\n" + "="*60)
    print("测试 1: 获取 LoRA 训练状态")
    print("="*60)
    
    user_id = "test_user_001"
    url = f"{BASE_URL}/api/lora/status/{user_id}"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data}")
            
            if data['code'] == 200:
                status = data['data']
                print(f"\n✅ 状态获取成功:")
                print(f"   用户: {status['user_id']}")
                print(f"   有模型: {status['has_model']}")
                print(f"   模型版本: {status['model_version']}")
                print(f"   训练次数: {status['total_trainings']}")
                print(f"   数据量: {status['current_data_size']}/{status['min_data_size']}")
                print(f"   可以训练: {status['can_train']}")
                print(f"   正在训练: {status['is_training']}")
                return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_lora_training():
    """测试触发 LoRA 训练"""
    print("\n" + "="*60)
    print("测试 2: 触发 LoRA 训练")
    print("="*60)
    
    user_id = "test_user_001"
    url = f"{BASE_URL}/api/lora/train/{user_id}"
    
    try:
        response = requests.post(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data}")
            
            if data['code'] == 200:
                print(f"\n✅ 训练已启动:")
                print(f"   用户: {data['data']['user_id']}")
                print(f"   数据量: {data['data']['data_size']}")
                print(f"   预计时间: {data['data']['estimated_time']}")
                return True
            else:
                print(f"⚠️  {data['message']}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_list_models():
    """测试列出所有模型"""
    print("\n" + "="*60)
    print("测试 3: 列出所有 LoRA 模型")
    print("="*60)
    
    url = f"{BASE_URL}/api/lora/models"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data['code'] == 200:
                models = data['data']['models']
                print(f"\n✅ 找到 {len(models)} 个模型:")
                for model in models:
                    print(f"   - 用户: {model['user_id']}, 版本: {model['version']}")
                return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_health():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试 0: 健康检查")
    print("="*60)
    
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务正常运行")
            print(f"   服务: {data['services']}")
            return True
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print(f"\n💡 请先启动后端服务:")
        print(f"   cd backend")
        print(f"   python start_server.py")
        return False

def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("  LoRA 系统集成测试")
    print("="*70)
    
    # 0. 健康检查
    if not test_health():
        return
    
    time.sleep(1)
    
    # 1. 获取状态
    test_lora_status()
    time.sleep(1)
    
    # 2. 列出模型
    test_list_models()
    time.sleep(1)
    
    # 3. 触发训练（可选）
    print("\n" + "="*60)
    print("是否要测试触发训练？(y/n)")
    print("⚠️  注意：训练需要 3-5 分钟")
    print("="*60)
    
    choice = input("请选择: ").strip().lower()
    if choice == 'y':
        test_lora_training()
    
    print("\n" + "="*70)
    print("  测试完成")
    print("="*70)
    print()

if __name__ == "__main__":
    main()
