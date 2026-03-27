"""
模型压缩模块
集成 llmquant 和 OBR 的模型优化能力

核心组件:
- ModelQuantizer: 基座模型量化器（OBR/bitsandbytes）
- LoRAQuantizer: LoRA 权重量化器（llmquant 4-bit）
- CompressionQualityMonitor: 量化质量监控器
- BaseModelCompressor: 基座模型离线压缩工具
- QuantizedModelLoader: 量化模型推理加载器
"""

from .quantizer import ModelQuantizer
from .quality_monitor import CompressionQualityMonitor
from .lora_quantizer import LoRAQuantizer
from .compress_base_model import BaseModelCompressor
from .inference_integration import QuantizedModelLoader, get_or_create_inference_pipeline

__all__ = [
    "ModelQuantizer",
    "CompressionQualityMonitor",
    "LoRAQuantizer",
    "BaseModelCompressor",
    "QuantizedModelLoader",
    "get_or_create_inference_pipeline",
]
