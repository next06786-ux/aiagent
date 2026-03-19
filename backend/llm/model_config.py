"""
本地模型配置
可以在这里统一管理模型名称和参数
"""

# 模型配置
MODEL_CONFIG = {
    # 当前使用的模型
    "current_model": "qwen3.5-0.8b",
    
    # 可用模型列表
    "available_models": {
        "qwen3.5-0.8b": {
            "hf_model_name": "Qwen/Qwen3.5-0.8B",
            "display_name": "Qwen 3.5 (0.8B)",
            "vram_required": 2.0,  # GB
            "inference_speed": 40,  # tokens/s on RTX 3050
            "context_length": 32768,
            "description": "最新的 Qwen 3.5 小模型，性能优秀"
        },
        "qwen2.5-0.5b": {
            "hf_model_name": "Qwen/Qwen2.5-0.5B-Instruct",
            "display_name": "Qwen 2.5 (0.5B)",
            "vram_required": 1.5,  # GB
            "inference_speed": 35,  # tokens/s on RTX 3050
            "context_length": 32768,
            "description": "Qwen 2.5 小模型，显存占用更低"
        },
        "qwen2.5-1.5b": {
            "hf_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
            "display_name": "Qwen 2.5 (1.5B)",
            "vram_required": 3.5,  # GB
            "inference_speed": 25,  # tokens/s on RTX 3050
            "context_length": 32768,
            "description": "Qwen 2.5 中等模型，效果更好但速度稍慢"
        }
    },
    
    # LoRA 训练配置
    "lora_config": {
        "r": 8,  # LoRA 秩
        "lora_alpha": 32,  # LoRA 缩放因子
        "target_modules": ["q_proj", "v_proj"],  # 训练的模块
        "lora_dropout": 0.1,
        "bias": "none"
    },
    
    # 训练配置
    "training_config": {
        "min_data_size": 100,  # 最少对话数
        "train_interval_days": 7,  # 训练间隔（天）
        "num_epochs": 3,  # 训练轮数
        "batch_size": 4,  # 批次大小
        "learning_rate": 2e-4,  # 学习率
        "max_length": 512  # 最大序列长度
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
    # 测试
    print("当前模型配置:")
    print(f"  模型: {get_model_display_name()}")
    print(f"  HF名称: {get_model_hf_name()}")
    print(f"  显存需求: {get_current_model_config()['vram_required']} GB")
    print(f"  推理速度: {get_current_model_config()['inference_speed']} tokens/s")
    print()
    
    print("所有可用模型:")
    for key, config in list_available_models().items():
        print(f"  [{key}] {config['display_name']}")
        print(f"      {config['description']}")
        print(f"      显存: {config['vram_required']}GB, 速度: {config['inference_speed']} tokens/s")
        print()
