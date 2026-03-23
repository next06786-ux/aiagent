"""
GPU服务器配置
针对 AutoDL GPU + SGLang 优化
"""
import os

# 路径配置
DATA_DIR = "/root/autodl-tmp"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 目录结构
PATHS = {
    "models_base": f"{DATA_DIR}/models/base",      # 基座模型
    "models_lora": f"{DATA_DIR}/models/lora",      # 用户LoRA
    "huggingface": f"{DATA_DIR}/huggingface",      # HuggingFace 缓存
    "database": f"{DATA_DIR}/data/database",        # 数据库
    "rag_data": f"{DATA_DIR}/data/rag",            # RAG数据
    "logs": f"{DATA_DIR}/logs",                     # 日志
}

# 模型配置 - 仅 Qwen3.5 系列
MODEL_CONFIGS = {
    # 主力模型：Qwen3.5-9B
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
    # 轻量版：Qwen3.5-0.8B
    "qwen3.5-0.8b": {
        "hf_name": "Qwen/Qwen3.5-0.8B",
        "display_name": "Qwen3.5 0.8B", 
        "vram_gb": 2,
        "lora_r": 32,
        "lora_alpha": 64,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "max_length": 2048,
        "batch_size": 8,
        "context_length": 32768,
    },
}

# 当前使用的模型
CURRENT_MODEL = "qwen3.5-9b"

# SGLang 服务器配置
SGLANG_CONFIG = {
    "host": "0.0.0.0",
    "port": 8001,
    "tensor_parallel_size": 1,
    "mem_fraction_static": 0.8,
    "context_length": 32768,
    "reasoning_parser": "qwen3",
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

# 环境变量配置（AutoDL 专用）
ENV_CONFIG = {
    "HF_HOME": f"{DATA_DIR}/huggingface",
    "HF_ENDPOINT": "https://hf-mirror.com",
    "HF_HUB_ENABLE_HF_TRANSFER": "0",
}


def get_model_config(model_key: str = None):
    """获取模型配置"""
    key = model_key or CURRENT_MODEL
    if key not in MODEL_CONFIGS:
        raise ValueError(f"未知模型: {key}, 可选: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[key]


def get_sglang_launch_cmd(model_key: str = None):
    """生成 SGLang 启动命令"""
    config = get_model_config(model_key)
    sglang = SGLANG_CONFIG
    
    cmd = f"""python -m sglang.launch_server \\
  --model-path {config['hf_name']} \\
  --port {sglang['port']} \\
  --tensor-parallel-size {sglang['tensor_parallel_size']} \\
  --mem-fraction-static {sglang['mem_fraction_static']} \\
  --context-length {sglang['context_length']} \\
  --reasoning-parser {sglang['reasoning_parser']} \\
  --download-dir {PATHS['huggingface']}"""
    
    return cmd


def ensure_dirs():
    """确保所有目录存在"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)


def setup_env():
    """设置环境变量"""
    for key, value in ENV_CONFIG.items():
        os.environ[key] = value


if __name__ == "__main__":
    print("GPU服务器配置 (SGLang):")
    print(f"  数据目录: {DATA_DIR}")
    print(f"  当前模型: {CURRENT_MODEL}")
    
    config = get_model_config()
    print(f"  模型名称: {config['hf_name']}")
    print(f"  显存需求: {config['vram_gb']} GB")
    print()
    print("SGLang 启动命令:")
    print(get_sglang_launch_cmd())
