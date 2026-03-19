"""
GPU服务器配置
针对 AutoDL 32GB vGPU 优化
"""
import os

# 路径配置
DATA_DIR = "/root/autodl-tmp"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 目录结构
PATHS = {
    "models_base": f"{DATA_DIR}/models/base",      # 基座模型
    "models_lora": f"{DATA_DIR}/models/lora",      # 用户LoRA
    "database": f"{DATA_DIR}/data/database",        # 数据库
    "rag_data": f"{DATA_DIR}/data/rag",            # RAG数据
    "logs": f"{DATA_DIR}/logs",                     # 日志
}

# 模型配置 - 针对32GB显存优化
MODEL_CONFIGS = {
    # 推荐：Qwen3-8B，32GB显存完美运行
    "qwen3-8b": {
        "hf_name": "Qwen/Qwen3-8B",
        "display_name": "Qwen3 8B",
        "vram_gb": 18,
        "lora_r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "max_length": 2048,
        "batch_size": 4,
        "use_4bit": False,
    },
    # 轻量版：Qwen3-4B
    "qwen3-4b": {
        "hf_name": "Qwen/Qwen3-4B", 
        "display_name": "Qwen3 4B",
        "vram_gb": 10,
        "lora_r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "max_length": 2048,
        "batch_size": 8,
        "use_4bit": False,
    },
    # 超轻量：你原来用的0.8B（现在叫Qwen3-0.6B或类似）
    "qwen3-0.6b": {
        "hf_name": "Qwen/Qwen3-0.6B",
        "display_name": "Qwen3 0.6B", 
        "vram_gb": 2,
        "lora_r": 8,
        "lora_alpha": 16,
        "target_modules": ["q_proj", "v_proj"],
        "max_length": 2048,
        "batch_size": 16,
        "use_4bit": False,
    },
    # 备选：Qwen2.5-7B（稳定版）
    "qwen2.5-7b": {
        "hf_name": "Qwen/Qwen2.5-7B-Instruct",
        "display_name": "Qwen2.5 7B Instruct",
        "vram_gb": 16,
        "lora_r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "max_length": 2048,
        "batch_size": 4,
        "use_4bit": False,
    },
}

# 当前使用的模型（可以改成你想用的）
CURRENT_MODEL = "qwen2.5-7b"  # 推荐用这个，稳定且效果好

# 服务器配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1,  # GPU推理用单worker
    "reload": False,
}

# LoRA训练配置
LORA_TRAINING_CONFIG = {
    "min_conversations": 10,      # 最少对话数才能训练
    "num_epochs": 3,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "gradient_accumulation_steps": 4,
    "save_steps": 100,
    "logging_steps": 10,
}


def get_model_config(model_key: str = None):
    """获取模型配置"""
    key = model_key or CURRENT_MODEL
    if key not in MODEL_CONFIGS:
        raise ValueError(f"未知模型: {key}, 可选: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[key]


def ensure_dirs():
    """确保所有目录存在"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)


if __name__ == "__main__":
    print("GPU服务器配置:")
    print(f"  数据目录: {DATA_DIR}")
    print(f"  当前模型: {CURRENT_MODEL}")
    
    config = get_model_config()
    print(f"  模型名称: {config['hf_name']}")
    print(f"  显存需求: {config['vram_gb']} GB")
