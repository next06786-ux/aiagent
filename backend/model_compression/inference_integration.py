"""
推理集成模块
为 llm_service 提供量化模型自动加载和管理能力

支持:
- 自动检测并加载量化模型
- 量化/非量化模型动态切换
- 混合推理（量化基座 + LoRA）
- 推理性能统计
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, AutoTokenizer
from peft import PeftModel

logger = logging.getLogger(__name__)


class QuantizedModelLoader:
    """量化模型加载器"""
    
    def __init__(self):
        self.last_loaded_model = None
        self.last_loaded_path = None
        self.inference_stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "avg_latency_ms": 0.0
        }
    
    def find_quantized_model(self, base_model_name: str) -> Optional[str]:
        """查找已量化的模型（支持 OBR 压缩格式和标准格式）"""
        quantized_candidates = [
            f"models/{base_model_name}-w4a4kv4-s50",
            f"models/{base_model_name}-q4",
            f"models/{base_model_name}-quantized",
            f"models/qwen-obr",  # OBR 默认输出路径
        ]
        
        for path in quantized_candidates:
            if os.path.exists(path):
                # 检查是否有 OBR 压缩的 state_dict
                obr_model_pt = os.path.join(path, "quantized_model.pt")
                if os.path.exists(obr_model_pt):
                    logger.info(f"找到 OBR 压缩模型: {path}")
                    return path
                # 检查标准 HuggingFace 格式
                config_file = os.path.join(path, "config.json")
                compression_config = os.path.join(path, "compression_config.json")
                if os.path.exists(config_file) or os.path.exists(compression_config):
                    logger.info(f"找到量化模型: {path}")
                    return path
        
        return None
    
    def load_with_quantization(
        self,
        model_name_or_path: str,
        quantization_type: str = "int4",
        device_map: str = "auto"
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        使用量化加载模型
        
        Args:
            model_name_or_path: 模型名称或路径
            quantization_type: 量化类型 (int4, int8)
            device_map: 设备映射
        
        Returns:
            (model, tokenizer)
        """
        logger.info(f"使用 {quantization_type} 量化加载模型: {model_name_or_path}")
        
        if quantization_type == "int4":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
        elif quantization_type == "int8":
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
        else:
            raise ValueError(f"不支持的量化类型: {quantization_type}")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=True
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )
        
        vram_gb = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
        logger.info(f"✓ 模型加载完成 (VRAM: {vram_gb:.2f} GB)")
        
        self.last_loaded_model = model
        self.last_loaded_path = model_name_or_path
        
        return model, tokenizer
    
    def load_obr_compressed_model(
        self,
        model_dir: str,
        original_model_name: str,
        device_map: str = "auto"
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        加载 OBR FlatQuant 压缩后的模型
        
        OBR 压缩输出的是 state_dict（quantized_model.pt），
        需要先加载原始模型结构，再替换权重。
        
        Args:
            model_dir: OBR 压缩输出目录（包含 quantized_model.pt）
            original_model_name: 原始模型名称（用于加载模型结构和 tokenizer）
            device_map: 设备映射
        
        Returns:
            (model, tokenizer)
        """
        import torch as _torch
        
        obr_weights_path = os.path.join(model_dir, "quantized_model.pt")
        if not os.path.exists(obr_weights_path):
            raise FileNotFoundError(f"OBR 压缩模型不存在: {obr_weights_path}")
        
        logger.info(f"加载 OBR 压缩模型: {model_dir}")
        logger.info(f"  原始模型结构: {original_model_name}")
        
        # 1. 加载原始模型结构（低精度以节省内存）
        model = AutoModelForCausalLM.from_pretrained(
            original_model_name,
            torch_dtype=_torch.float16,
            device_map=device_map,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        
        # 2. 加载 OBR 压缩后的 state_dict
        logger.info(f"加载 OBR 权重: {obr_weights_path}")
        compressed_state_dict = _torch.load(obr_weights_path, map_location="cpu")
        
        # 3. 替换权重
        missing, unexpected = model.load_state_dict(compressed_state_dict, strict=False)
        if missing:
            logger.warning(f"缺失的权重 ({len(missing)}): {missing[:5]}...")
        if unexpected:
            logger.warning(f"多余的权重 ({len(unexpected)}): {unexpected[:5]}...")
        
        # 4. 加载 tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            original_model_name,
            trust_remote_code=True
        )
        
        vram_gb = _torch.cuda.memory_allocated() / 1024**3 if _torch.cuda.is_available() else 0
        logger.info(f"✓ OBR 压缩模型加载完成 (VRAM: {vram_gb:.2f} GB)")
        
        self.last_loaded_model = model
        self.last_loaded_path = model_dir
        
        return model, tokenizer
    
    def load_without_quantization(
        self,
        model_name_or_path: str,
        device_map: str = "auto"
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        不使用量化加载模型（FP16 或 FP32）
        
        Args:
            model_name_or_path: 模型名称或路径
            device_map: 设备映射
        
        Returns:
            (model, tokenizer)
        """
        logger.info(f"使用 FP16/BF16 加载模型: {model_name_or_path}")
        
        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch_dtype,
            device_map=device_map,
            trust_remote_code=True
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )
        
        vram_gb = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
        logger.info(f"✓ 模型加载完成 (VRAM: {vram_gb:.2f} GB)")
        
        self.last_loaded_model = model
        self.last_loaded_path = model_name_or_path
        
        return model, tokenizer
    
    def load_with_auto_select(
        self,
        model_name: str,
        enable_quantization: bool = True,
        device_map: str = "auto"
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer, Dict[str, Any]]:
        """
        自动选择最优的加载方式
        
        优先级:
        1. 如果启用量化且找到量化模型 → 使用量化模型
        2. 否则 → 使用原始模型 (FP16/BF16)
        
        Args:
            model_name: 模型名称
            enable_quantization: 是否启用量化
            device_map: 设备映射
        
        Returns:
            (model, tokenizer, metadata)
        """
        metadata = {
            "model_name": model_name,
            "loaded_at": datetime.now().isoformat(),
            "quantized": False,
            "quantization_type": None,
            "vram_gb": 0.0
        }
        
        if enable_quantization:
            # 尝试查找量化模型
            quantized_path = self.find_quantized_model(
                model_name.split('/')[-1]
            )
            
            if quantized_path:
                # 检查是否是 OBR 压缩格式
                obr_model_pt = os.path.join(quantized_path, "quantized_model.pt")
                if os.path.exists(obr_model_pt):
                    model, tokenizer = self.load_obr_compressed_model(
                        model_dir=quantized_path,
                        original_model_name=model_name,
                        device_map=device_map
                    )
                    metadata["quantized"] = True
                    metadata["quantization_type"] = "obr_flatquant"
                    metadata["quantized_path"] = quantized_path
                else:
                    model, tokenizer = self.load_with_quantization(
                        quantized_path,
                        quantization_type="int4",
                        device_map=device_map
                    )
                    metadata["quantized"] = True
                    metadata["quantization_type"] = "int4"
            else:
                logger.info("未找到量化模型，使用 bitsandbytes 动态量化加载")
                model, tokenizer = self.load_with_quantization(
                    model_name,
                    quantization_type="int4",
                    device_map=device_map
                )
                metadata["quantized"] = True
                metadata["quantization_type"] = "int4_dynamic"
        else:
            model, tokenizer = self.load_without_quantization(
                model_name,
                device_map=device_map
            )
        
        if torch.cuda.is_available():
            metadata["vram_gb"] = round(torch.cuda.memory_allocated() / 1024**3, 2)
        
        return model, tokenizer, metadata
    
    def load_quantized_lora(
        self,
        base_model,
        lora_path: str,
        is_quantized: bool = True
    ) -> PeftModel:
        """
        加载量化的 LoRA 适配器
        
        支持在量化基座模型上加载 LoRA
        
        Args:
            base_model: 基座模型（可能是量化的）
            lora_path: LoRA 路径
            is_quantized: LoRA 是否量化
        
        Returns:
            wrapped model with LoRA
        """
        logger.info(f"加载 {'量化' if is_quantized else ''} LoRA: {lora_path}")
        
        model = PeftModel.from_pretrained(
            base_model,
            lora_path,
            is_trainable=False
        )
        
        logger.info("✓ LoRA 加载完成")
        
        return model
    
    def record_inference_stats(self, num_tokens: int, latency_ms: float):
        """记录推理统计"""
        self.inference_stats["total_calls"] += 1
        self.inference_stats["total_tokens"] += num_tokens
        
        # 计算移动平均延迟
        total_calls = self.inference_stats["total_calls"]
        old_avg = self.inference_stats["avg_latency_ms"]
        new_avg = (old_avg * (total_calls - 1) + latency_ms) / total_calls
        self.inference_stats["avg_latency_ms"] = new_avg
    
    def get_inference_stats(self) -> Dict[str, Any]:
        """获取推理统计"""
        return {
            **self.inference_stats,
            "last_loaded_path": self.last_loaded_path,
            "avg_tokens_per_call": (
                self.inference_stats["total_tokens"] / self.inference_stats["total_calls"]
                if self.inference_stats["total_calls"] > 0 else 0
            )
        }


def create_inference_pipeline(
    model_name: str,
    enable_quantization: bool = True,
    use_auto_select: bool = True
) -> Dict[str, Any]:
    """
    创建推理管道
    
    Returns:
        {
            "model": model,
            "tokenizer": tokenizer,
            "loader": loader,
            "config": {...}
        }
    """
    loader = QuantizedModelLoader()
    
    if use_auto_select:
        model, tokenizer, metadata = loader.load_with_auto_select(
            model_name,
            enable_quantization=enable_quantization
        )
    else:
        if enable_quantization:
            model, tokenizer = loader.load_with_quantization(
                model_name,
                quantization_type="int4"
            )
            metadata = {"quantized": True}
        else:
            model, tokenizer = loader.load_without_quantization(model_name)
            metadata = {"quantized": False}
    
    return {
        "model": model,
        "tokenizer": tokenizer,
        "loader": loader,
        "config": metadata
    }


# 全局推理管道实例
_inference_pipeline = None


def get_or_create_inference_pipeline(
    model_name: str,
    enable_quantization: bool = True
) -> Dict[str, Any]:
    """获取或创建推理管道"""
    global _inference_pipeline
    
    if _inference_pipeline is None:
        _inference_pipeline = create_inference_pipeline(
            model_name,
            enable_quantization=enable_quantization
        )
    
    return _inference_pipeline


def get_inference_stats() -> Dict[str, Any]:
    """获取推理统计"""
    global _inference_pipeline
    
    if _inference_pipeline is None:
        return {}
    
    return _inference_pipeline["loader"].get_inference_stats()


# ============== 与 llm_service 的集成 ==============

def integrate_with_llm_service():
    """
    为 llm_service 添加量化支持的集成代码
    
    在 backend/llm/llm_service.py 的 LLMService._initialize() 中调用:
    
    if self.provider == LLMProvider.TRANSFORMERS:
        from backend.model_compression.inference_integration import \\
            get_or_create_inference_pipeline
        pipeline = get_or_create_inference_pipeline(
            model_name=get_model_hf_name(),
            enable_quantization=get_quantization_config()["enable_quantization"]
        )
        self.model = pipeline["model"]
        self.tokenizer = pipeline["tokenizer"]
    """
    pass
