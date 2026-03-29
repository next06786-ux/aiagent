"""
模型压缩模块
集成 llmquant 和 OBR 的模型优化能力

核心组件:
- ModelQuantizer: 通用量化器（bitsandbytes/llmquant/OBR）
- LoRAQuantizer: LoRA 权重量化器（llmquant 4-bit）
- CompressionQualityMonitor: 量化质量监控器（含残差能量分析）
- OBRCompressor: 基座模型 OBR FlatQuant 离线压缩
- QuantizedModelLoader: 量化模型推理加载器（支持 OBR 格式）
"""

from .quantizer import ModelQuantizer, QuantizationMethod, QuantizationConfig
from .quality_monitor import CompressionQualityMonitor
from .lora_quantizer import LoRAQuantizer
from .obr_wrapper import OBRCompressor
from .inference_integration import (
    QuantizedModelLoader,
    get_or_create_inference_pipeline,
    create_inference_pipeline,
    get_inference_stats,
)

from .fusion_compressor import FusionCompressor

__all__ = [
    "ModelQuantizer",
    "QuantizationMethod",
    "QuantizationConfig",
    "CompressionQualityMonitor",
    "LoRAQuantizer",
    "OBRCompressor",
    "FusionCompressor",
    "QuantizedModelLoader",
    "get_or_create_inference_pipeline",
    "create_inference_pipeline",
    "get_inference_stats",
]
