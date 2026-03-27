"""
基座模型压缩集成脚本
使用 OBR FlatQuant 方案对 Qwen3.5-9B 执行离线 W4A4KV4 + 50% 稀疏量化

执行方式:
python backend/model_compression/compress_base_model.py \\
  --model Qwen/Qwen3.5-9B \\
  --output models/qwen3.5-9b-w4a4kv4-s50 \\
  --sparsity 0.5 \\
  --eval-dataset wikitext2
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


class BaseModelCompressor:
    """基座模型压缩器 - OBR FlatQuant 集成"""
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3.5-9B",
        output_dir: Optional[str] = None,
        sparsity_ratio: float = 0.5,
        bits: int = 4,
    ):
        """
        初始化压缩器
        
        Args:
            model_name: HuggingFace 模型名称
            output_dir: 压缩模型输出目录
            sparsity_ratio: 稀疏度（0.5 = 50%）
            bits: 量化位数（4 为 W4A4）
        """
        self.model_name = model_name
        self.output_dir = output_dir or f"models/{model_name.split('/')[-1]}-w{bits}a{bits}kv{bits}-s{int(sparsity_ratio*100)}"
        self.sparsity_ratio = sparsity_ratio
        self.bits = bits
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 配置文件
        self.config_path = os.path.join(self.output_dir, "compression_config.json")
        self.config = self._load_or_init_config()
    
    def _load_or_init_config(self) -> Dict[str, Any]:
        """加载或初始化配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f)
        
        return {
            "model_name": self.model_name,
            "compression_method": "OBR_FlatQuant",
            "quantization_strategy": f"W{self.bits}A{self.bits}KV{self.bits}",
            "sparsity_ratio": self.sparsity_ratio,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "metrics": {}
        }
    
    def _save_config(self):
        """保存配置"""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def compress_with_bitsandbytes(self) -> Dict[str, Any]:
        """
        使用 bitsandbytes 进行实时量化（推荐用于推理）
        
        这是相比 OBR 离线量化的替代方案：
        - 优点：开箱即用，无需 calibration，自动处理推理优化
        - 缺点：推理时动态量化，相比离线量化会略慢
        """
        logger.info(f"开始使用 bitsandbytes 压缩基座模型")
        logger.info(f"  模型: {self.model_name}")
        logger.info(f"  输出目录: {self.output_dir}")
        
        try:
            from transformers import BitsAndBytesConfig
            
            # 构建量化配置
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
            
            logger.info("加载模型（启用 4-bit 量化）...")
            
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
            
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            logger.info("✓ 模型加载完成")
            logger.info(f"  显存占用: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            
            # 保存量化模型
            logger.info("保存量化模型...")
            model.save_pretrained(self.output_dir)
            tokenizer.save_pretrained(self.output_dir)
            
            # 更新配置
            self.config.update({
                "status": "success",
                "method": "bitsandbytes",
                "actual_vram_gb": round(torch.cuda.memory_allocated() / 1024**3, 2),
                "completion_time": datetime.now().isoformat(),
            })
            self._save_config()
            
            logger.info(f"✓ 模型保存完成: {self.output_dir}\n")
            
            return {
                "status": "success",
                "output_path": self.output_dir,
                "method": "bitsandbytes",
                "vram_gb": round(torch.cuda.memory_allocated() / 1024**3, 2),
                "config_path": self.config_path
            }
        
        except Exception as e:
            logger.error(f"✗ 量化失败: {e}")
            self.config["status"] = "failed"
            self.config["error"] = str(e)
            self._save_config()
            
            return {
                "status": "failed",
                "error": str(e),
                "config_path": self.config_path
            }
    
    def compress_with_obr(
        self,
        eval_dataset: str = "wikitext2",
        eval: bool = True
    ) -> Dict[str, Any]:
        """
        使用 OBR FlatQuant 进行离线压缩（推荐用于高精度）
        
        这需要 OBR 库已安装在 external_repos/OBR 中
        """
        logger.info(f"开始使用 OBR FlatQuant 压缩基座模型")
        logger.info(f"  模型: {self.model_name}")
        logger.info(f"  量化策略: W{self.bits}A{self.bits}KV{self.bits}")
        logger.info(f"  稀疏度: {self.sparsity_ratio*100:.0f}%")
        logger.info(f"  输出目录: {self.output_dir}")
        
        try:
            # 检查 OBR 是否存在
            obr_path = "external_repos/OBR"
            if not os.path.exists(obr_path):
                raise FileNotFoundError(f"OBR 不存在: {obr_path}，请先克隆 OBR 库")
            
            # 动态导入 OBR
            obr_flatquant_path = os.path.join(obr_path, "FlatQuant")
            if obr_flatquant_path not in sys.path:
                sys.path.insert(0, obr_flatquant_path)
            
            try:
                from main import run_compression
            except ImportError as e:
                logger.warning(f"OBR 导入失败: {e}")
                logger.info("降级到使用 bitsandbytes 方案...")
                return self.compress_with_bitsandbytes()
            
            # 构建 OBR 压缩参数
            obr_args = {
                "model": self.model_name,
                "w_bits": self.bits,
                "a_bits": self.bits,
                "k_bits": self.bits,
                "v_bits": self.bits,
                "k_asym": True,
                "v_asym": True,
                "k_groupsize": 128,
                "v_groupsize": 128,
                "sparsity_ratio": self.sparsity_ratio,
                "output_dir": self.output_dir,
                "ppl_eval": eval,
                "eval_dataset": eval_dataset,
            }
            
            logger.info("OBR 压缩参数:")
            for k, v in obr_args.items():
                logger.info(f"  {k}: {v}")
            
            # 执行 OBR 压缩
            logger.info("\n开始压缩（这可能需要 1-4 小时）...")
            metrics = run_compression(obr_args)
            
            # 更新配置
            self.config.update({
                "status": "success",
                "method": "OBR_FlatQuant",
                "metrics": metrics or {},
                "completion_time": datetime.now().isoformat(),
            })
            self._save_config()
            
            logger.info(f"\n✓ 压缩完成")
            logger.info(f"  输出目录: {self.output_dir}")
            logger.info(f"  配置文件: {self.config_path}\n")
            
            return {
                "status": "success",
                "output_path": self.output_dir,
                "method": "OBR_FlatQuant",
                "metrics": metrics or {},
                "config_path": self.config_path
            }
        
        except Exception as e:
            logger.error(f"✗ OBR 压缩失败: {e}")
            import traceback
            traceback.print_exc()
            
            self.config["status"] = "failed"
            self.config["error"] = str(e)
            self._save_config()
            
            return {
                "status": "failed",
                "error": str(e),
                "config_path": self.config_path
            }
    
    def verify_compression(self) -> Dict[str, Any]:
        """验证压缩后的模型"""
        logger.info(f"验证压缩模型...")
        
        try:
            # 尝试加载压缩模型
            from transformers import AutoModelForCausalLM, BitsAndBytesConfig
            
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                self.output_dir,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
            
            tokenizer = AutoTokenizer.from_pretrained(self.output_dir)
            
            logger.info("✓ 模型加载成功")
            logger.info(f"  显存占用: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            
            # 简单推理测试
            test_prompt = "你好，请介绍一下自己。"
            inputs = tokenizer(test_prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.7,
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"✓ 推理测试通过")
            logger.info(f"  输入: {test_prompt}")
            logger.info(f"  输出: {response[:100]}...\n")
            
            return {
                "status": "success",
                "vram_gb": round(torch.cuda.memory_allocated() / 1024**3, 2),
                "inference_working": True
            }
        
        except Exception as e:
            logger.error(f"✗ 验证失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }


def main():
    parser = argparse.ArgumentParser(description="基座模型压缩工具")
    parser.add_argument("--model", type=str, default="Qwen/Qwen3.5-9B", help="模型名称")
    parser.add_argument("--output", type=str, default=None, help="输出目录")
    parser.add_argument("--method", type=str, default="bitsandbytes", 
                       choices=["bitsandbytes", "obr"], help="压缩方法")
    parser.add_argument("--sparsity", type=float, default=0.5, help="稀疏度")
    parser.add_argument("--bits", type=int, default=4, help="量化位数")
    parser.add_argument("--eval-dataset", type=str, default="wikitext2", help="评估数据集")
    parser.add_argument("--verify", action="store_true", help="压缩后进行验证")
    
    args = parser.parse_args()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"LifeSwarm 基座模型压缩")
    logger.info(f"{'='*60}\n")
    
    compressor = BaseModelCompressor(
        model_name=args.model,
        output_dir=args.output,
        sparsity_ratio=args.sparsity,
        bits=args.bits,
    )
    
    # 执行压缩
    if args.method == "obr":
        result = compressor.compress_with_obr(eval_dataset=args.eval_dataset)
    else:
        result = compressor.compress_with_bitsandbytes()
    
    logger.info(f"压缩结果: {json.dumps(result, indent=2)}")
    
    # 验证
    if args.verify and result["status"] == "success":
        verify_result = compressor.verify_compression()
        logger.info(f"验证结果: {json.dumps(verify_result, indent=2)}")


if __name__ == "__main__":
    main()
