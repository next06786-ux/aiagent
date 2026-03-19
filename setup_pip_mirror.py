#!/usr/bin/env python3
"""
配置 pip 国内镜像源
支持 Windows、Linux、macOS
"""
import os
import sys
from pathlib import Path

def setup_pip_mirror():
    """设置 pip 镜像源"""
    
    print("\n" + "=" * 70)
    print("  Configure pip with Chinese Mirror")
    print("=" * 70 + "\n")
    
    # 确定 pip 配置目录
    if sys.platform == "win32":
        pip_config_dir = Path(os.getenv("APPDATA")) / "pip"
    else:
        pip_config_dir = Path.home() / ".pip"
    
    # 创建目录
    pip_config_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ pip config directory: {pip_config_dir}")
    
    # 创建 pip.ini (Windows) 或 pip.conf (Linux/macOS)
    if sys.platform == "win32":
        config_file = pip_config_dir / "pip.ini"
    else:
        config_file = pip_config_dir / "pip.conf"
    
    # 配置内容
    config_content = """[global]
# 清华大学镜像（推荐，速度最快）
index-url = https://pypi.tsinghua.edu.cn/simple

# 备用镜像源
extra-index-url = 
    https://mirrors.aliyun.com/pypi/simple/
    https://pypi.org/simple/

[install]
# 信任的主机
trusted-host = 
    pypi.tsinghua.edu.cn
    mirrors.aliyun.com
    pypi.org

# 超时时间（秒）
timeout = 120
"""
    
    # 写入配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Configuration file created: {config_file}")
    print("\n📋 Configuration:")
    print("   Primary Mirror: Tsinghua University (清华大学)")
    print("   Backup Mirror: Aliyun (阿里云)")
    print("   Timeout: 120 seconds")
    print("\n🚀 Now you can install packages faster:")
    print("   pip install -r requirements.txt")
    print("\n✨ Mirror sources:")
    print("   - https://pypi.tsinghua.edu.cn/simple (清华)")
    print("   - https://mirrors.aliyun.com/pypi/simple/ (阿里云)")
    print("   - https://pypi.douban.com/simple (豆瓣)")
    print("   - https://pypi.mirrors.ustc.edu.cn/simple (中科大)")
    print()

if __name__ == "__main__":
    try:
        setup_pip_mirror()
        print("✅ Setup completed successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)










