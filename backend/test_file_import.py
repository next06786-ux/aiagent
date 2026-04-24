"""
测试Agent文件导入功能
"""
import requests
import os

# 配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://47.115.230.195:8000")

def get_test_token():
    """获取测试token"""
    url = f"{API_BASE_URL}/api/auth/login"
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                token = data['data']['token']
                print(f"✅ 登录成功")
                return token
        print(f"❌ 登录失败")
        return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None


def test_file_import(token, agent_type, file_path):
    """测试文件导入"""
    
    url = f"{API_BASE_URL}/api/agent-import-file"
    
    print(f"\n{'='*60}")
    print(f"测试文件导入: {agent_type} Agent")
    print(f"文件: {file_path}")
    print(f"{'='*60}")
    
    try:
        # 读取文件
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/plain')}
            data = {
                'agent_type': agent_type,
                'token': token
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"\n✅ 导入成功!")
                print(f"导入数量: {result.get('count')} 条")
                print(f"文件名: {result.get('filename')}")
                return True
            else:
                print(f"\n❌ 导入失败: {result.get('message')}")
                return False
        else:
            print(f"\n❌ 请求失败")
            print(f"响应: {response.text[:200]}")
            return False
            
    except FileNotFoundError:
        print(f"\n❌ 文件不存在: {file_path}")
        return False
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Agent文件导入功能测试")
    print("=" * 60)
    
    # 1. 获取token
    print("\n步骤1: 登录获取token...")
    token = get_test_token()
    
    if not token:
        print("\n❌ 无法获取token，测试终止")
        return
    
    # 2. 测试文件导入
    print("\n步骤2: 测试文件导入...")
    
    test_files = [
        ("education", "backend/test_data/education_sample.txt"),
        ("career", "backend/test_data/career_sample.txt"),
        ("relationship", "backend/test_data/relationship_sample.txt")
    ]
    
    results = []
    for agent_type, file_path in test_files:
        success = test_file_import(token, agent_type, file_path)
        results.append((agent_type, success))
        print("\n" + "-" * 60)
    
    # 3. 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for agent_type, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{agent_type.ljust(15)} {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")


if __name__ == "__main__":
    main()
