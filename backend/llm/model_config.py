"""
模型配置
统一管理 SGLang 使用的 Qwen3.5-9B 参数
"""

MODEL_CONFIG = {
    "current_model": "qwen3.5-9b",
    "available_models": {
        "qwen3.5-9b": {
            "hf_model_name": "Qwen/Qwen3.5-9B",
            "display_name": "Qwen 3.5 (9B)",
            "vram_required": 20.0,
            "inference_speed": 50,
            "context_length": 32768,
            "description": "Qwen 3.5 主力模型，SGLang 生产推理模型"
        }
    },
    "sglang_config": {
        "default_port": 8001,
        "tensor_parallel_size": 1,
        "mem_fraction_static": 0.8,
        "context_length": 32768,
        "reasoning_parser": "qwen3"
    },
    "lora_config": {
        "r": 64,
        "lora_alpha": 128,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "lora_dropout": 0.05,
        "bias": "none"
    },
    "training_config": {
        "min_data_size": 100,
        "train_interval_days": 7,
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 2e-4,
        "max_length": 2048
    }
}


def get_current_model_config():
    return MODEL_CONFIG["available_models"][MODEL_CONFIG["current_model"]]


def get_model_hf_name():
    return get_current_model_config()["hf_model_name"]


def get_model_display_name():
    return get_current_model_config()["display_name"]


def get_sglang_config():
    return MODEL_CONFIG["sglang_config"]


def get_lora_config():
    return MODEL_CONFIG["lora_config"]


def list_available_models():
    return MODEL_CONFIG["available_models"]


def switch_model(model_key: str):
    if model_key != "qwen3.5-9b":
        raise ValueError("当前部署仅支持 qwen3.5-9b")
    MODEL_CONFIG["current_model"] = model_key
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
