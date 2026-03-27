"""
模型配置
统一管理 Qwen3.5-9B 使用 Transformers 原生推理的参数
"""

MODEL_CONFIG = {
    "current_model": "qwen3.5-9b-obr",  # 改成压缩模型
    "available_models": {
        "qwen3.5-9b": {
            "hf_model_name": "Qwen/Qwen3.5-9B",
            "display_name": "Qwen 3.5 (9B) - 原始模型",
            "vram_required": 20.0,
            "inference_speed": 50,
            "context_length": 32768,
            "description": "Qwen 3.5 原始模型 (FP16)",
            "dtype": "float16",
            "device_map": "auto"
        },
        "qwen3.5-9b-obr": {
            "local_path": "models/qwen-obr",  # 本地压缩模型路径
            "display_name": "Qwen 3.5 (9B) - OBR 压缩",
            "vram_required": 5.0,
            "inference_speed": 200,  # 4-8x 加速
            "context_length": 32768,
            "description": "OBR FlatQuant 压缩 (W4A16 + 50% 稀疏)",
            "compression_method": "OBR_FlatQuant",
            "quantization_bits": 4,
            "sparsity": 0.5,
            "dtype": "int4",
            "device_map": "auto"
        }
    },
    "inference_config": {
        "max_new_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": True,
        "num_beams": 1
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
    },
    "quantization_config": {
        "enable_quantization": True,            # 是否启用量化
        "quantization_type": "int4",            # 支持: int4, int8, fp8
        "load_in_8bit": False,
        "load_in_4bit": True,
        "bnb_4bit_use_double_quant": True,      # 双量化
        "bnb_4bit_quant_type": "nf4",           # NormalFloat4
        "bnb_4bit_compute_dtype": "bfloat16"
    },
    "lora_config_quantization": {
        "quantize_after_training": True,        # 训练后自动量化
        "lora_quantization_bits": 4,            # LoRA 4-bit 量化
        "lora_quantization_per_channel": True,  # per-channel 量化
        "adaptive_rank": True                   # 自适应 rank 分配
    }
}


def get_current_model_config():
    return MODEL_CONFIG["available_models"][MODEL_CONFIG["current_model"]]


def get_model_hf_name():
    """获取模型名称或本地路径"""
    config = get_current_model_config()
    if "local_path" in config:
        return config["local_path"]  # 返回本地路径
    return config["hf_model_name"]


def get_model_display_name():
    return get_current_model_config()["display_name"]


def get_inference_config():
    return MODEL_CONFIG["inference_config"]


def get_lora_config():
    return MODEL_CONFIG["lora_config"]


def get_quantization_config():
    return MODEL_CONFIG["quantization_config"]


def get_lora_quantization_config():
    """获取 LoRA 量化配置"""
    return MODEL_CONFIG["lora_config_quantization"]


def get_training_config():
    return MODEL_CONFIG["training_config"]


def list_available_models():
    return MODEL_CONFIG["available_models"]


def switch_model(model_key: str):
    if model_key != "qwen3.5-9b":
        raise ValueError("当前部署仅支持 qwen3.5-9b")
    MODEL_CONFIG["current_model"] = model_key
    return get_current_model_config()


def set_quantization(enable: bool, quantization_type: str = "int4"):
    """启用或禁用量化"""
    MODEL_CONFIG["quantization_config"]["enable_quantization"] = bool(enable)
    MODEL_CONFIG["quantization_config"]["quantization_type"] = str(quantization_type)
    
    if quantization_type == "int4":
        MODEL_CONFIG["quantization_config"]["load_in_4bit"] = enable
        MODEL_CONFIG["quantization_config"]["load_in_8bit"] = False
    elif quantization_type == "int8":
        MODEL_CONFIG["quantization_config"]["load_in_8bit"] = enable
        MODEL_CONFIG["quantization_config"]["load_in_4bit"] = False
    else:
        raise ValueError(f"不支持的量化类型: {quantization_type}")


if __name__ == "__main__":
    print("当前模型配置:")
    model_cfg = get_current_model_config()
    print(f"  模型: {model_cfg['display_name']}")
    print(f"  HF名称: {model_cfg['hf_model_name']}")
    print(f"  显存需求: {model_cfg['vram_required']} GB (FP16)")
    print(f"  推理精度: {model_cfg['dtype']}")
    print()
    
    print("推理配置:")
    inference = get_inference_config()
    for k, v in inference.items():
        print(f"  {k}: {v}")
    print()
    
    print("量化配置:")
    quant = get_quantization_config()
    for k, v in quant.items():
        print(f"  {k}: {v}")
    print()
    
    print("所有可用模型:")
    for key, config in list_available_models().items():
        print(f"  [{key}] {config['display_name']}")
        print(f"      {config['description']}")
