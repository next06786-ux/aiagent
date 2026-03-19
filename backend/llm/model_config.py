"""
本地模型配置
统一管理 Qwen3.5 模型和 SGLang 参数
"""

# 模型配置
MODEL_CONFIG = {
    # 当前使用的模型
    "current_model": "qwen3.5-9b",
    
    # 可用模型列表（仅 Qwen3.5 系列）
    "available_models": {
        "qwen3.5-9b": {
            "hf_model_name": "Qwen/Qwen3.5-9B",
            "display_name": "Qwen 3.5 (9B)",
            "vram_required": 20.0,  # GB
            "inference_speed": 50,  # tokens/s on A100
            "context_length": 32768,
            "description": "Qwen 3.5 主力模型，推荐用于生产环境"
        },
        "qwen3.5-0.8b": {
            "hf_model_name": "Qwen/Qwen3.5-0.8B",
            "display_name": "Qwen 3.5 (0.8B)",
            "vram_required": 2.0,  # GB
            "inference_speed": 80,  # tokens/s
            "context_length": 32768,
            "description": "Qwen 3.5 轻量模型，适合资源受限环境"
        }
    },
    
    # SGLang 服务配置
    "sglang_config": {
        "default_port": 8000,
        "tensor_parallel_size": 1,
        "mem_fraction_static": 0.8,
        "context_length": 32768,
        "reasoning_parser": "qwen3"
    },
    
    # LoRA 训练配置
    "lora_config": {
        "r": 64,  # LoRA 秩
        "lora_alpha": 128,  # LoRA 缩放因子
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],  # 训练的模块
        "lora_dropout": 0.05,
        "bias": "none"
    },
    
    # 训练配置
    "training_config": {
        "min_data_size": 100,  # 最少对话数
        "train_interval_days": 7,  # 训练间隔（天）
        "num_epochs": 3,  # 训练轮数
        "batch_size": 4,  # 批次大小
        "learning_rate": 2e-4,  # 学习率
        "max_length": 2048  # 最大序列长度
    }
}


def get_current_model_config():
    """获取当前模型配置"""
    current = MODEL_CONFIG["current_model"]
    return MODEL_CONFIG["available_models"][current]


def get_model_hf_name():
    """获取当前模型的 Hugging Face 名称"""
    return get_current_model_config()["hf_model_name"]


def get_model_display_name():
    """获取当前模型的显示名称"""
    return get_current_model_config()["display_name"]


def get_sglang_config():
    """获取 SGLang 配置"""
    return MODEL_CONFIG["sglang_config"]


def get_lora_config():
    """获取 LoRA 配置"""
    return MODEL_CONFIG["lora_config"]


def list_available_models():
    """列出所有可用模型"""
    return MODEL_CONFIG["available_models"]


def switch_model(model_key: str):
    """切换模型"""
    if model_key not in MODEL_CONFIG["available_models"]:
        raise ValueError(f"模型 {model_key} 不存在")
    
    MODEL_CONFIG["current_model"] = model_key
    print(f"✅ 已切换到模型: {get_model_display_name()}")
    return get_current_model_config()


if __name__ == "__main__":
    print("当前模型配置:")
    print(f"  模型: {get_model_display_name()}")
    print(f"  HF名称: {get_model_hf_name()}")
    print(f"  显存需求: {get_current_model_config()['vram_required']} GB")
    print()
    
    print("SGLang 配置:")
    sglang = get_sglang_config()
    for k, v in sglang.items():
        print(f"  {k}: {v}")
    print()
    
    print("所有可用模型:")
    for key, config in list_available_models().items():
        print(f"  [{key}] {config['display_name']}")
        print(f"      {config['description']}")
