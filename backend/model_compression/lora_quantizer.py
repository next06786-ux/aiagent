"""
LoRA 权重量化器
基于 llmquant 的 4-bit per-channel 量化方案

特点:
- 独立函数，无污染原始权重
- 支持量化/反量化一致性保证
- 保存量化元数据（scale, offset）供推理使用
"""

import os
import sys
import json
import torch
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class LoRAQuantizer:
    """LoRA 权重量化器"""
    
    def __init__(
        self,
        user_id: str,
        lora_dir: str,
        bits: int = 4,
        per_channel: bool = True
    ):
        """
        初始化量化器
        
        Args:
            user_id: 用户 ID
            lora_dir: LoRA 目录路径
            bits: 量化位数（2, 3, 4, 8）
            per_channel: 是否使用 per-channel 量化
        """
        self.user_id = user_id
        self.lora_dir = lora_dir
        self.bits = bits
        self.per_channel = per_channel
        
        # 尝试导入 llmquant
        self.llmquant_available = self._init_llmquant()
    
    def _init_llmquant(self) -> bool:
        """初始化 llmquant 库"""
        try:
            llmquant_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../external_repos/llmquant')
            )
            if llmquant_path not in sys.path:
                sys.path.insert(0, llmquant_path)
            
            from binary import (
                iterative_affine_quantize_perchannel,
                quantize_to_2bit_perchannel,
                quantize_to_3bit_perchannel,
                quantize_to_4bit_perchannel,
                quantize_to_8bit_perchannel
            )
            
            self.iterative_affine_quantize_perchannel = iterative_affine_quantize_perchannel
            self.quantize_funcs = {
                2: quantize_to_2bit_perchannel,
                3: quantize_to_3bit_perchannel,
                4: quantize_to_4bit_perchannel,
                8: quantize_to_8bit_perchannel
            }
            
            logger.info("✓ llmquant 库已加载")
            return True
        
        except Exception as e:
            logger.warning(f"⚠️ llmquant 库加载失败: {e}")
            logger.warning("将使用简单的静态量化（而非迭代优化）")
            return False
    
    def quantize_lora_weights(
        self,
        bits: int = 4,
        per_channel: bool = True,
        n_iter: int = 5,
        save_metadata: bool = True,
        output_suffix: str = "_q4"
    ) -> Dict[str, Any]:
        """
        量化 LoRA 权重
        
        Args:
            bits: 量化位数
            per_channel: 是否 per-channel 量化
            n_iter: 迭代次数（llmquant）
            save_metadata: 是否保存量化元数据
            output_suffix: 输出目录后缀
        
        Returns:
            {
                "status": "success" | "failed",
                "output_path": str,
                "size_before_mb": float,
                "size_after_mb": float,
                "compression_ratio": float,
                "metadata": {...},
                "error": str (if failed)
            }
        """
        logger.info(f"开始量化 LoRA 权重 (bits={bits})")
        
        try:
            # 查找最新版本的 LoRA 模型
            adapter_path = self._find_latest_lora_adapter()
            if not adapter_path:
                raise FileNotFoundError(f"未找到用户 {self.user_id} 的 LoRA 模型")
            
            logger.info(f"找到 LoRA 模型: {adapter_path}")
            
            # 加载 adapter 权重
            adapter_weights = self._load_adapter_weights(adapter_path)
            if not adapter_weights:
                raise RuntimeError("无法加载 adapter 权重")
            
            # 计算原始大小
            size_before_mb = sum(
                p.data.element_size() * p.data.numel() / (1024 ** 2)
                for p in adapter_weights.values()
            )
            
            logger.info(f"原始大小: {size_before_mb:.2f} MB")
            
            # 执行量化
            quantized_weights, metadata = self._quantize_weights(
                adapter_weights,
                bits=bits,
                per_channel=per_channel,
                n_iter=n_iter
            )
            
            # 计算量化后大小
            size_after_mb = sum(
                q.element_size() * q.numel() / (1024 ** 2)
                if isinstance(q, torch.Tensor) else 0
                for q in quantized_weights.values()
            )
            
            # 保存量化模型
            output_dir = self._create_output_dir(output_suffix)
            self._save_quantized_weights(quantized_weights, output_dir)
            
            # 保存元数据
            if save_metadata:
                self._save_metadata(metadata, output_dir)
            
            compression_ratio = size_before_mb / size_after_mb if size_after_mb > 0 else 1.0
            
            logger.info(f"✓ 量化完成")
            logger.info(f"  大小: {size_before_mb:.2f} MB → {size_after_mb:.2f} MB")
            logger.info(f"  压缩率: {compression_ratio:.2f}x")
            logger.info(f"  输出: {output_dir}")
            
            return {
                "status": "success",
                "output_path": output_dir,
                "size_before_mb": round(size_before_mb, 2),
                "size_after_mb": round(size_after_mb, 2),
                "compression_ratio": round(compression_ratio, 2),
                "metadata": metadata,
                "bits": bits,
                "per_channel": per_channel
            }
        
        except Exception as e:
            logger.error(f"✗ 量化失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _find_latest_lora_adapter(self) -> Optional[str]:
        """查找最新的 LoRA adapter 目录"""
        versions = []
        for item in os.listdir(self.lora_dir):
            if item.startswith('v') and os.path.isdir(os.path.join(self.lora_dir, item)):
                try:
                    version_num = int(item[1:])
                    versions.append((version_num, item))
                except ValueError:
                    continue
        
        if not versions:
            return None
        
        latest_version = sorted(versions)[-1][1]
        adapter_path = os.path.join(self.lora_dir, latest_version, "final")
        
        if os.path.exists(adapter_path):
            return adapter_path
        return None
    
    def _load_adapter_weights(self, adapter_path: str) -> Dict[str, torch.Tensor]:
        """加载 adapter 权重"""
        try:
            import safetensors.torch
            
            # 尝试加载 safetensors
            safetensors_path = os.path.join(adapter_path, "adapter_model.safetensors")
            if os.path.exists(safetensors_path):
                logger.info(f"从 safetensors 加载: {safetensors_path}")
                return safetensors.torch.load_file(safetensors_path)
        
        except ImportError:
            pass
        
        # 回退到 .bin
        bin_path = os.path.join(adapter_path, "adapter_model.bin")
        if os.path.exists(bin_path):
            logger.info(f"从 bin 加载: {bin_path}")
            return torch.load(bin_path, map_location="cpu")
        
        raise FileNotFoundError(f"未找到 adapter 权重文件: {adapter_path}")
    
    def _quantize_weights(
        self,
        weights: Dict[str, torch.Tensor],
        bits: int = 4,
        per_channel: bool = True,
        n_iter: int = 5
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
        """量化权重"""
        quantized_weights = {}
        metadata = {
            "bits": bits,
            "per_channel": per_channel,
            "quantization_method": "llmquant_iterative" if self.llmquant_available else "static",
            "layers": {}
        }
        
        for name, weight in weights.items():
            if weight.ndim < 2 or 'lora' not in name.lower():
                # 非 LoRA 权重或维度不足，保持原样
                quantized_weights[name] = weight
                continue
            
            logger.info(f"量化 {name}: {weight.shape}")
            
            if self.llmquant_available and per_channel:
                # 使用迭代优化量化
                try:
                    quantized, info = self.iterative_affine_quantize_perchannel(
                        weight,
                        bits=bits,
                        n_iter=n_iter,
                        return_info=True
                    )
                    
                    quantized_weights[name] = quantized.to(weight.dtype)
                    metadata["layers"][name] = {
                        "scale": info["scale"].tolist() if hasattr(info["scale"], "tolist") else str(info["scale"]),
                        "offset": info["offset"].tolist() if hasattr(info["offset"], "tolist") else str(info["offset"]),
                        "zero_point": info["zero_point"].tolist() if hasattr(info["zero_point"], "tolist") else str(info["zero_point"]),
                        "mse": float(info["best_mse"]),
                        "iterations": info["iters"]
                    }
                
                except Exception as e:
                    logger.warning(f"迭代量化失败 ({name}): {e}，使用静态量化")
                    quantized = self._static_quantize(weight, bits)
                    quantized_weights[name] = quantized
            else:
                # 使用静态量化
                quantized = self._static_quantize(weight, bits)
                quantized_weights[name] = quantized
        
        return quantized_weights, metadata
    
    def _static_quantize(self, tensor: torch.Tensor, bits: int) -> torch.Tensor:
        """静态量化（fallback）"""
        if tensor.ndim < 2:
            return tensor
        
        # Per-channel min/max
        shape = tensor.shape
        tensor_2d = tensor.flatten(1)
        
        maxq = 2 ** bits - 1
        x_min = tensor_2d.amin(dim=1)
        x_max = tensor_2d.amax(dim=1)
        
        # 避免全零
        x_min = torch.minimum(x_min, torch.zeros_like(x_min))
        x_max = torch.maximum(x_max, torch.zeros_like(x_max))
        
        scale = (x_max - x_min) / maxq
        scale = torch.clamp(scale, min=1e-8)
        
        # 量化
        x_q = torch.round((tensor_2d - x_min.unsqueeze(1)) / scale.unsqueeze(1)).clamp(0, maxq)
        
        # 反量化（伪量化）
        x_hat = x_q * scale.unsqueeze(1) + x_min.unsqueeze(1)
        
        return x_hat.reshape(shape)
    
    def _create_output_dir(self, suffix: str) -> str:
        """创建输出目录"""
        output_dir = os.path.join(
            os.path.dirname(self.lora_dir),
            f"{os.path.basename(self.lora_dir)}{suffix}"
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # 复制 adapter_config.json
        config_src = os.path.join(
            self._find_latest_lora_adapter() or self.lora_dir,
            "adapter_config.json"
        )
        if os.path.exists(config_src):
            import shutil
            shutil.copy(config_src, os.path.join(output_dir, "adapter_config.json"))
        
        return output_dir
    
    def _save_quantized_weights(
        self,
        weights: Dict[str, torch.Tensor],
        output_dir: str
    ):
        """保存量化权重"""
        try:
            import safetensors.torch
            safetensors_path = os.path.join(output_dir, "adapter_model.safetensors")
            safetensors.torch.save_file(weights, safetensors_path)
            logger.info(f"✓ 量化权重已保存 (safetensors): {safetensors_path}")
        
        except ImportError:
            bin_path = os.path.join(output_dir, "adapter_model.bin")
            torch.save(weights, bin_path)
            logger.info(f"✓ 量化权重已保存 (torch): {bin_path}")
    
    def _save_metadata(self, metadata: Dict[str, Any], output_dir: str):
        """保存量化元数据"""
        metadata_path = os.path.join(output_dir, "quantization_metadata.json")
        
        # 清理不可序列化的对象
        def serialize_value(v):
            if isinstance(v, (int, float, str, bool, type(None))):
                return v
            elif isinstance(v, dict):
                return {k: serialize_value(val) for k, val in v.items()}
            elif isinstance(v, (list, tuple)):
                return [serialize_value(item) for item in v]
            else:
                return str(v)
        
        metadata_clean = serialize_value(metadata)
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata_clean, f, indent=2)
        
        logger.info(f"✓ 量化元数据已保存: {metadata_path}")
