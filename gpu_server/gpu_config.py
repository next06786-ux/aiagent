"""
GPU服务器配置
单机部署模式：FastAPI + SGLang + Qwen3.5-9B + 用户 LoRA
"""
import os

DATA_DIR = os.environ.get("GPU_DATA_DIR", "/root/autodl-tmp")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    "models_base": f"{DATA_DIR}/models/base",
    "models_lora": os.environ.get("LORA_MODELS_DIR", f"{PROJECT_DIR}/models/lora"),
    "huggingface": f"{DATA_DIR}/huggingface",
    "database": f"{DATA_DIR}/data/database",
    "rag_data": f"{DATA_DIR}/data/rag",
    "logs": f"{DATA_DIR}/logs",
}

MODEL_CONFIGS = {
    "qwen3.5-9b": {
        "hf_name": "Qwen/Qwen3.5-9B",
        "display_name": "Qwen3.5 9B",
        "vram_gb": 20,
        "lora_r": 64,
        "lora_alpha": 128,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "max_length": 2048,
        "batch_size": 4,
        "context_length": 32768,
    },
}

CURRENT_MODEL = "qwen3.5-9b"

SGLANG_CONFIG = {
    "host": "0.0.0.0",
    "port": 8001,
    "tensor_parallel_size": 1,
    "mem_fraction_static": 0.8,
    "context_length": 32768,
    "reasoning_parser": "qwen3",
}

LORA_TRAINING_CONFIG = {
    "min_conversations": 10,
    "num_epochs": 3,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "gradient_accumulation_steps": 4,
    "save_steps": 100,
    "logging_steps": 10,
}

ENV_CONFIG = {
    "HF_HOME": PATHS["huggingface"],
    "HF_ENDPOINT": "https://hf-mirror.com",
    "HF_HUB_ENABLE_HF_TRANSFER": "0",
}


def get_model_config(model_key: str = None):
    key = model_key or CURRENT_MODEL
    if key not in MODEL_CONFIGS:
        raise ValueError(f"未知模型: {key}, 当前仅支持: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[key]


def get_sglang_launch_cmd(model_key: str = None):
    config = get_model_config(model_key)
    sglang = SGLANG_CONFIG
    return f"""python -m sglang.launch_server \\
  --model-path {config['hf_name']} \\
  --port {sglang['port']} \\
  --tensor-parallel-size {sglang['tensor_parallel_size']} \\
  --mem-fraction-static {sglang['mem_fraction_static']} \\
  --context-length {sglang['context_length']} \\
  --reasoning-parser {sglang['reasoning_parser']} \\
  --download-dir {PATHS['huggingface']}"""


def ensure_dirs():
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)


def setup_env():
    for key, value in ENV_CONFIG.items():
        os.environ[key] = value


if __name__ == "__main__":
    print("GPU服务器配置 (SGLang 单机部署):")
    print(f"  数据目录: {DATA_DIR}")
    print(f"  当前模型: {CURRENT_MODEL}")
    print(f"  LoRA目录: {PATHS['models_lora']}")
    config = get_model_config()
    print(f"  模型名称: {config['hf_name']}")
    print(f"  显存需求: {config['vram_gb']} GB")
    print()
    print("SGLang 启动命令:")
    print(get_sglang_launch_cmd())
