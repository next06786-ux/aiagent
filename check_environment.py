"""
检查 LoRA 训练环境是否准备就绪
"""
import sys

def check_environment():
    """检查环境配置"""
    
    print("=" * 60)
    print("🔍 LoRA 训练环境检查")
    print("=" * 60)
    print()
    
    issues = []
    
    # 1. 检查 Python 版本
    print("1. Python 版本检查...")
    python_version = sys.version_info
    print(f"   当前版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major >= 3 and python_version.minor >= 8:
        print("   ✅ Python 版本符合要求 (>= 3.8)")
    else:
        print("   ❌ Python 版本过低，需要 >= 3.8")
        issues.append("Python 版本")
    print()
    
    # 2. 检查 PyTorch
    print("2. PyTorch 检查...")
    try:
        import torch
        print(f"   版本: {torch.__version__}")
        print(f"   CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA 版本: {torch.version.cuda}")
            print(f"   GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
                props = torch.cuda.get_device_properties(i)
                print(f"      显存: {props.total_memory / 1024**3:.1f} GB")
            print("   ✅ PyTorch + CUDA 正常")
        else:
            print("   ⚠️ CUDA 不可用，将使用 CPU（训练会很慢）")
            issues.append("CUDA 不可用")
    except ImportError:
        print("   ❌ PyTorch 未安装")
        issues.append("PyTorch 未安装")
    print()
    
    # 3. 检查 Transformers
    print("3. Transformers 检查...")
    try:
        import transformers
        print(f"   版本: {transformers.__version__}")
        print("   ✅ Transformers 已安装")
    except ImportError:
        print("   ❌ Transformers 未安装")
        print("   安装命令: pip install transformers")
        issues.append("Transformers 未安装")
    print()
    
    # 4. 检查 PEFT (LoRA)
    print("4. PEFT (LoRA) 检查...")
    try:
        import peft
        print(f"   版本: {peft.__version__}")
        print("   ✅ PEFT 已安装")
    except ImportError:
        print("   ❌ PEFT 未安装")
        print("   安装命令: pip install peft")
        issues.append("PEFT 未安装")
    print()
    
    # 5. 检查其他依赖
    print("5. 其他依赖检查...")
    dependencies = {
        "accelerate": "加速训练",
        "bitsandbytes": "量化支持",
        "datasets": "数据集处理",
        "sentencepiece": "分词器",
        "protobuf": "模型序列化"
    }
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"   ✅ {package} ({description})")
        except ImportError:
            print(f"   ⚠️ {package} 未安装 ({description})")
            print(f"      安装命令: pip install {package}")
    print()
    
    # 6. 检查磁盘空间
    print("6. 磁盘空间检查...")
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        print(f"   可用空间: {free_gb:.1f} GB")
        if free_gb >= 10:
            print("   ✅ 磁盘空间充足")
        else:
            print("   ⚠️ 磁盘空间不足，建议至少 10GB")
            issues.append("磁盘空间不足")
    except Exception as e:
        print(f"   ⚠️ 无法检查磁盘空间: {e}")
    print()
    
    # 7. 检查模型缓存目录
    print("7. Hugging Face 缓存检查...")
    import os
    cache_dir = os.path.expanduser("~/.cache/huggingface")
    if os.path.exists(cache_dir):
        print(f"   缓存目录: {cache_dir}")
        print("   ✅ 缓存目录存在")
    else:
        print(f"   缓存目录: {cache_dir}")
        print("   ℹ️ 缓存目录不存在（首次下载模型时会自动创建）")
    print()
    
    # 总结
    print("=" * 60)
    if not issues:
        print("✅ 环境检查通过！可以开始训练 LoRA 模型")
        print()
        print("下一步:")
        print("1. 启动 Qwen 服务器: start_qwen_server.bat")
        print("2. 测试服务器: python test_local_qwen.py")
        print("3. 开始 LoRA 训练")
    else:
        print(f"❌ 发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print()
        print("请先解决这些问题再继续")
    print("=" * 60)

if __name__ == "__main__":
    check_environment()
