"""
获取测试用的Token
"""
import requests
import json

# 后端地址
BASE_URL = "http://localhost:8000"

def register_and_login():
    """注册并登录，获取token"""
    
    # 测试用户信息
    username = "test_user_ws"
    email = "test_ws@example.com"
    password = "test123456"
    
    print("="*60)
    print("获取测试Token")
    print("="*60)
    print()
    
    # 1. 尝试注册
    print("1. 尝试注册用户...")
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "nickname": "WebSocket测试用户"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=register_data
        )
        result = response.json()
        
        if result['code'] == 200:
            print(f"   ✅ 注册成功")
            token = result['data']['token']
            user_id = result['data']['user_id']
            print(f"   用户ID: {user_id}")
            print(f"   Token: {token}")
            return token, user_id
        elif "已存在" in result['message']:
            print(f"   ℹ️  用户已存在，尝试登录...")
        else:
            print(f"   ⚠️  注册失败: {result['message']}")
    except Exception as e:
        print(f"   ⚠️  注册请求失败: {e}")
    
    # 2. 登录
    print("\n2. 登录...")
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data
        )
        result = response.json()
        
        if result['code'] == 200:
            print(f"   ✅ 登录成功")
            token = result['data']['token']
            user_id = result['data']['user_id']
            print(f"   用户ID: {user_id}")
            print(f"   Token: {token}")
            return token, user_id
        else:
            print(f"   ❌ 登录失败: {result['message']}")
            return None, None
    except Exception as e:
        print(f"   ❌ 登录请求失败: {e}")
        return None, None


def verify_token(token):
    """验证token是否有效"""
    print("\n3. 验证Token...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-token",
            json={"token": token}
        )
        result = response.json()
        
        if result['code'] == 200 and result['data']['valid']:
            print(f"   ✅ Token有效")
            print(f"   用户ID: {result['data']['user_id']}")
            return True
        else:
            print(f"   ❌ Token无效")
            return False
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False


if __name__ == "__main__":
    try:
        # 获取token
        token, user_id = register_and_login()
        
        if token:
            # 验证token
            if verify_token(token):
                print("\n" + "="*60)
                print("✅ Token获取成功！")
                print("="*60)
                print()
                print("请在HTML测试页面中使用以下Token：")
                print()
                print(f"Token: {token}")
                print()
                print("="*60)
                
                # 保存到文件
                with open("test_token.txt", "w") as f:
                    f.write(f"Token: {token}\n")
                    f.write(f"User ID: {user_id}\n")
                    f.write(f"Username: test_user_ws\n")
                
                print("\nToken已保存到 test_token.txt 文件")
            else:
                print("\n❌ Token验证失败")
        else:
            print("\n❌ 无法获取Token")
            
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
