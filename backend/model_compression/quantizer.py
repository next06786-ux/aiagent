"""
通用模型量化器
统一接口支持多种量化方案：bitsandbytes、llmquant、OBR

使用策略:
1. 基座模型: 优先 bitsandbytes，可选 OBR 预压缩
2. LoRA: llmquant per-channel 量化
"""

import os
import sys
import torch
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QuantizationMethod(Enum):
    """量化方法"""
    BITSANDBYTES = "bitsandbytes"  # 推理时动态量化
    LLMQUANT = "llmquant"  # 训练时静态量化（迭代优化）
    OBR = "obr"  # 离线量化 + 稀疏化


class QuantizationConfig:
    """量化配置"""
    
    def __init__(
        self,
        method: QuantizationMethod = QuantizationMethod.BITSANDBYTES,
        bits: int = 4,
        per_channel: bool = True,
        use_double_quant: bool = True,
        quant_type: str = "nf4",
        compute_dtype: torch.dtype = torch.bfloat16
    ):
        self.method = method
        self.bits = bits
        self.per_channel = per_channel
        self.use_double_quant = use_double_quant
        self.quant_type = quant_type
        self.compute_dtype = compute_dtype


class ModelQuantizer:
    """通用模型量化器"""
    
    def __init__(self, method: QuantizationMethod = QuantizationMethod.BITSANDBYTES):
        """
        初始化量化器
        
        Args:
            method: 量化方法
        """
        self.method = method
        self._init_backends()
    
    def _init_backends(self):
        """初始化各个后端"""
        self.bitsandbytes_available = self._check_bitsandbytes()
        self.llmquant_available = self._check_llmquant()
        self.obr_available = self._check_obr()
        
        logger.info("量化后端可用性:")
        logger.info(f"  bitsandbytes: {self.bitsandbytes_available}")
        logger.info(f"  llmquant: {self.llmquant_available}")
        logger.info(f"  OBR: {self.obr_available}")
    
    def _check_bitsandbytes(self) -> bool:
        """检查 bitsandbytes 是否可用"""
        try:
            import bitsandbytes
            return True
        except ImportError:
            return False
    
    def _check_llmquant(self) -> bool:
        """检查 llmquant 是否可用"""
        try:
            llmquant_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../external_repos/llmquant')
            )
            if not os.path.exists(llmquant_path):
                return False
            
            sys.path.insert(0, llmquant_path)
            from binary import quantize_to_4bit_perchannel
            return True
        except Exception:
            return False
    
    def _check_obr(self) -> bool:
        """检查 OBR 是否可用"""
        try:
            obr_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../external_repos/OBR')
            )
            return os.path.exists(obr_path)
        except Exception:
            return False
    
    def quantize_model_bitsandbytes(
        self,
        model_name_or_path: str,
        bits: int = 4,
        double_quant: bool = True
    ) -> Tuple[Any, Any, Dict[str, Any]]:
        """
        使用 bitsandbytes 量化模型（推理时）
        
        Args:
            model_name_or_path: 模型名称或路径
            bits: 量化位数（4 或 8）
            double_quant: 是否启用双量化
        
        Returns:
            (model, tokenizer, config)
        """
        if not self.bitsandbytes_available:
            raise RuntimeError("bitsandbytes 不可用，请先安装: pip install bitsandbytes")
        
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        
        logger.info(f"使用 bitsandbytes {bits}-bit 量化加载: {model_name_or_path}")
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=(bits == 4),
            load_in_8bit=(bits == 8),
            bnb_4bit_use_double_quant=double_quant,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )
        
        config = {
            "method": "bitsandbytes",
            "bits": bits,
            "double_quant": double_quant,
            "vram_gb": torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
        }
        
        return model, tokenizer, config
    
    def quantize_model_obr(
        self,
        model_name: str,
        output_dir: str,
        w_bits: int = 4,
        a_bits: int = 16,
        k_bits: int = 4,
        v_bits: int = 4,
        sparsity_ratio: float = 0.5,
        nsamples: int = 128,
        cali_dataset: str = "wikitext2"
    ) -> Dict[str, Any]:
        """
        使用 OBR 离线压缩模型（真正执行压缩）
        
        Args:
            model_name: 模型名称或路径
            output_dir: 输出目录
            w_bits: 权重量化位数
            a_bits: 激活量化位数
            k_bits: Key 量化位数
            v_bits: Value 量化位数
            sparsity_ratio: 稀疏度
            nsamples: 校准样本数
            cali_dataset: 校准数据集
        
        Returns:
            压缩结果
        """
        if not self.obr_available:
            raise RuntimeError("OBR 库不可用，请确认 external_repos/OBR 存在")
        
        from backend.model_compression.obr_wrapper import OBRCompressor
        
        logger.info(f"使用 OBR FlatQuant 离线压缩: {model_name}")
        logger.info(f"  W{w_bits}A{a_bits}K{k_bits}V{v_bits}+{sparsity_ratio*100:.0f}% sparsity")
        
        compressor = OBRCompressor(
            model_name=model_name,
            output_dir=output_dir,
            w_bits=w_bits,
            a_bits=a_bits,
            k_bits=k_bits,
            v_bits=v_bits,
            sparsity_ratio=sparsity_ratio,
            nsamples=nsamples,
            cali_dataset=cali_dataset,
        )
        
        result = compressor.compress()
        
        if result["status"] == "success":
            logger.info(f"✓ OBR 压缩成功: {output_dir}")
        else:
            logger.error(f"✗ OBR 压缩失败: {result.get('error', 'unknown')}")
        
        return result
    
    def quantize_tensor_llmquant(
        self,
        tensor: torch.Tensor,
        bits: int = 4,
        per_channel: bool = True,
        n_iter: int = 5,
        return_metadata: bool = False
    ) -> Tuple[torch.Tensor, Optional[Dict[str, Any]]]:
        """
        使用 llmquant 量化单个张量（LoRA 权重）
        
        Args:
            tensor: 输入张量
            bits: 量化位数
            per_channel: 是否 per-channel 量化
            n_iter: 迭代次数
            return_metadata: 是否返回量化元数据
        
        Returns:
            (quantized_tensor, metadata)
        """
        if not self.llmquant_available:
            logger.warning("llmquant 不可用，将使用静态量化")
            return self._static_quantize(tensor, bits), None
        
        from external_repos.llmquant.binary import iterative_affine_quantize_perchannel
        
        logger.info(f"使用 llmquant {bits}-bit 量化张量: {tensor.shape}")
        
        try:
            if return_metadata:
                quantized, info = iterative_affine_quantize_perchannel(
                    tensor,
                    bits=bits,
                    n_iter=n_iter,
                    return_info=True
                )
                return quantized, info
            else:
                quantized = iterative_affine_quantize_perchannel(
                    tensor,
                    bits=bits,
                    n_iter=n_iter
                )
                return quantized, None
        
        except Exception as e:
            logger.warning(f"llmquant 量化失败: {e}，回退到静态量化")
            return self._static_quantize(tensor, bits), None
    
    def _static_quantize(self, tensor: torch.Tensor, bits: int) -> torch.Tensor:
        """静态量化（fallback）"""
        if tensor.ndim < 2:
            return tensor
        
        shape = tensor.shape
        tensor_2d = tensor.flatten(1)
        
        maxq = 2 ** bits - 1
        x_min = tensor_2d.amin(dim=1)
        x_max = tensor_2d.amax(dim=1)
        
        x_min = torch.minimum(x_min, torch.zeros_like(x_min))
        x_max = torch.maximum(x_max, torch.zeros_like(x_max))
        
        scale = (x_max - x_min) / maxq
        scale = torch.clamp(scale, min=1e-8)
        
        x_q = torch.round((tensor_2d - x_min.unsqueeze(1)) / scale.unsqueeze(1)).clamp(0, maxq)
        x_hat = x_q * scale.unsqueeze(1) + x_min.unsqueeze(1)
        
        return x_hat.reshape(shape)
    
    def benchmark_quantization(
        self,
        model: Any,
        tokenizer: Any,
        test_input: str = "Hello, how are you?",
        num_runs: int = 5
    ) -> Dict[str, float]:
        """
        基准测试量化模型
        
        Args:
            model: 量化模型
            tokenizer: 分词器
            test_input: 测试输入
            num_runs: 运行次数
        
        Returns:
            基准测试结果
        """
        import time
        
        logger.info(f"开始基准测试（{num_runs} 次运行）")
        
        # 预热
        inputs = tokenizer(test_input, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        
        with torch.no_grad():
            model.generate(**inputs, max_new_tokens=10)
        
        # 计时
        times = []
        for _ in range(num_runs):
            start = time.time()
            
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=10)
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        # 显存
        vram_mb = torch.cuda.max_memory_allocated() / (1024 ** 2) if torch.cuda.is_available() else 0
        
        results = {
            "avg_latency_sec": sum(times) / len(times),
            "min_latency_sec": min(times),
            "max_latency_sec": max(times),
            "vram_mb": vram_mb,
            "throughput_tokens_per_sec": len(outputs[0]) / (sum(times) / len(times)) if sum(times) > 0 else 0
        }
        
        logger.info("基准测试结果:")
        logger.info(f"  平均延迟: {results['avg_latency_sec']:.4f}s")
        logger.info(f"  显存占用: {results['vram_mb']:.1f}MB")
        logger.info(f"  吞吐量: {results['throughput_tokens_per_sec']:.1f} tokens/s")
        
        return results


# 全局实例
_global_quantizer: Optional[ModelQuantizer] = None


def get_quantizer(method: QuantizationMethod = QuantizationMethod.BITSANDBYTES) -> ModelQuantizer:
    """获取全局量化器实例"""
    global _global_quantizer
    
    if _global_quantizer is None:
        _global_quantizer = ModelQuantizer(method)
    
    return _global_quantizer
