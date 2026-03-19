#!/usr/bin/env python3
"""
模型下载脚本
下载并缓存所需的模型到数据盘
"""
import os
import sys
import argparse
from pathlib import Path

# 设置环境
DATA_DIR = os.environ.get("DATA_DIR", "/root/autodl-tmp")
MODELS_DIR = os.path.join(DATA_DIR, "models", "base")
HF_CACHE = os.path.join(DATA_DIR, "huggingface")

os.environ["HF_HOME"] = HF_CACHE
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE
os.makedirs(MODELS_DIR, exist_ok=True)


# 可下载的模型列表
AVAILABLE_MODELS = {
    "qwen2.5-3b": {
        "name": "Qwen/Qwen2.5-3B-Instruct",
        "size": "~6GB",
        "description": "轻量级模型，适合8GB显存"
    },
    "qwen2.5-7b": {
        "name": "Qwen/Qwen2.5-7B-Instruct",
        "size": "~14GB",
        "description": "推荐模型，适合16GB+显存"
    },
    "qwen2.5-14b": {
        "name": "Qwen/Qwen2.5-14B-Instruct",
        "size": "~28GB",
        "description": "高性能模型，适合32GB显存"
    },
    "embedding": {
        "name": "BAAI/bge-small-zh-v1.5",
        "size": "~100MB",
        "description": "中文嵌入模型，用于RAG"
    }
}


def download_model(model_key: str, force: bool = False):
    """下载指定模型"""
    if model_key not in AVAILABLE_MODELS:
        print(f"❌ 未知模型: {model_key}")
        print(f"可用模型: {list(AVAILABLE_MODELS.keys())}")
        return False
    
    model_info = AVAILABLE_MODELS[model_key]
    model_name = model_info["name"]
    
    print(f"\n📥 下载模型: {model_name}")
    print(f"   大小: {model_info['size']}")
    print(f"   说明: {model_info['description']}")
    
    # 检查是否已下载
    local_path = os.path.join(MODELS_DIR, model_key)
    if os.path.exists(local_path) and not force:
        print(f"✅ 模型已存在: {local_path}")
        return True
    
    try:
        if model_key == "embedding":
            # 下载嵌入模型
            from sentence_transformers import SentenceTransformer
            print("   下载中...")
            model = SentenceTransformer(model_name, cache_folder=HF_CACHE)
            model.save(local_path)
        else:
            # 下载LLM模型
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            print("   下载Tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir=HF_CACHE
            )
            tokenizer.save_pretrained(local_path)
            
            print("   下载模型权重（这可能需要一些时间）...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir=HF_CACHE,
                torch_dtype="auto",
                device_map="cpu"  # 先下载到CPU
            )
            model.save_pretrained(local_path)
        
        print(f"✅ 模型已保存到: {local_path}")
        return True
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_models():
    """列出可用模型"""
    print("\n📋 可下载的模型:")
    print("-" * 60)
    
    for key, info in AVAILABLE_MODELS.items():
        local_path = os.path.join(MODELS_DIR, key)
        status = "✅ 已下载" if os.path.exists(local_path) else "⬜ 未下载"
        print(f"  {key:15} {status}")
        print(f"    名称: {info['name']}")
        print(f"    大小: {info['size']}")
        print(f"    说明: {info['description']}")
        print()


def download_recommended():
    """下载推荐的模型组合"""
    print("📦 下载推荐模型组合...")
    
    # 检测GPU显存
    try:
        import torch
        if torch.cuda.is_available():
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"🎮 检测到GPU显存: {gpu_mem:.1f} GB")
            
            if gpu_mem >= 24:
                models = ["qwen2.5-14b", "embedding"]
            elif gpu_mem >= 16:
                models = ["qwen2.5-7b", "embedding"]
            else:
                models = ["qwen2.5-3b", "embedding"]
        else:
            models = ["qwen2.5-3b", "embedding"]
    except:
        models = ["qwen2.5-7b", "embedding"]
    
    print(f"📥 将下载: {models}")
    
    for model in models:
        download_model(model)


def main():
    parser = argparse.ArgumentParser(description="模型下载工具")
    parser.add_argument("action", nargs="?", default="list",
                       choices=["list", "download", "recommended"],
                       help="操作: list(列出模型), download(下载指定模型), recommended(下载推荐模型)")
    parser.add_argument("--model", "-m", help="要下载的模型名称")
    parser.add_argument("--force", "-f", action="store_true", help="强制重新下载")
    parser.add_argument("--all", "-a", action="store_true", help="下载所有模型")
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║              LifeSwarm 模型下载工具                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"📁 模型目录: {MODELS_DIR}")
    
    if args.action == "list":
        list_models()
    
    elif args.action == "download":
        if args.all:
            for model in AVAILABLE_MODELS:
                download_model(model, args.force)
        elif args.model:
            download_model(args.model, args.force)
        else:
            print("❌ 请指定模型名称 (--model) 或使用 --all 下载所有模型")
            list_models()
    
    elif args.action == "recommended":
        download_recommended()


if __name__ == "__main__":
    main()
