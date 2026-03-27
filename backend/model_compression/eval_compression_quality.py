"""
压缩质量评估脚本
评估量化后的模型精度损失、性能提升等指标

使用方式:
python backend/model_compression/eval_compression_quality.py \\
  --model-fp16 models/qwen3.5-9b-fp16 \\
  --model-quantized models/qwen3.5-9b-w4a4kv4-s50 \\
  --dataset wikitext2 \\
  --output reports/compression_report.json
"""

import os
import json
import argparse
import logging
from typing import Dict, Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


class CompressionQualityEvaluator:
    """压缩质量评估器"""
    
    def __init__(self, model_fp16_path: str, model_quantized_path: str):
        self.model_fp16_path = model_fp16_path
        self.model_quantized_path = model_quantized_path
        self.tokenizer = None
        self.model_fp16 = None
        self.model_quantized = None
    
    def load_models(self):
        """加载两个模型"""
        logger.info("加载 FP16 模型...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_fp16_path,
            trust_remote_code=True
        )
        
        self.model_fp16 = AutoModelForCausalLM.from_pretrained(
            self.model_fp16_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        logger.info(f"✓ FP16 模型加载完成")
        
        logger.info("\n加载量化模型...")
        from transformers import BitsAndBytesConfig
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        self.model_quantized = AutoModelForCausalLM.from_pretrained(
            self.model_quantized_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        logger.info(f"✓ 量化模型加载完成")
    
    def evaluate_perplexity(
        self,
        model,
        dataset_name: str = "wikitext2",
        num_samples: int = 128
    ) -> float:
        """评估模型 perplexity"""
        logger.info(f"评估 {dataset_name} 上的 Perplexity...")
        
        try:
            from datasets import load_dataset
            import math
            
            if dataset_name == "wikitext2":
                dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
                texts = dataset["text"][:num_samples]
            elif dataset_name == "c4":
                dataset = load_dataset("allenai/c4", "en", split="validation", streaming=True)
                texts = []
                for i, item in enumerate(dataset):
                    if i >= num_samples:
                        break
                    texts.append(item["text"])
            else:
                raise ValueError(f"不支持的数据集: {dataset_name}")
            
            text = "\n\n".join(texts)
            encodings = self.tokenizer(text, return_tensors="pt")
            input_ids = encodings.input_ids
            
            model.eval()
            device = next(model.parameters()).device
            
            nlls = []
            stride = 2048 // 2
            max_length = 2048
            
            for begin_loc in range(0, min(input_ids.size(1) - max_length, 20000), stride):
                end_loc = begin_loc + max_length
                input_chunk = input_ids[:, begin_loc:end_loc].to(device)
                target_chunk = input_chunk.clone()
                target_chunk[:, :stride] = -100
                
                with torch.no_grad():
                    outputs = model(input_chunk, labels=target_chunk)
                    neg_log_likelihood = outputs.loss
                
                nlls.append(neg_log_likelihood.item())
            
            ppl = math.exp(sum(nlls) / len(nlls)) if nlls else 0
            logger.info(f"  Perplexity: {ppl:.4f}")
            
            return ppl
        
        except Exception as e:
            logger.error(f"Perplexity 评估失败: {e}")
            return 0.0
    
    def compare_perplexity(self, dataset_name: str = "wikitext2") -> Dict[str, Any]:
        """对比两个模型的 perplexity"""
        logger.info(f"\n{'='*60}")
        logger.info("评估模型精度 (Perplexity)")
        logger.info(f"{'='*60}\n")
        
        ppl_fp16 = self.evaluate_perplexity(self.model_fp16, dataset_name)
        ppl_q = self.evaluate_perplexity(self.model_quantized, dataset_name)
        
        increase = ppl_q - ppl_fp16
        increase_pct = (increase / ppl_fp16 * 100) if ppl_fp16 > 0 else 0
        
        if increase < 0.5:
            recommendation = "✓ 精度损失可忽略，可直接部署"
        elif increase < 1.0:
            recommendation = "⚠ 精度有小幅下降，建议监控"
        elif increase < 2.0:
            recommendation = "⚠ 精度有明显下降，考虑调整量化参数"
        else:
            recommendation = "✗ 精度损失过大，不建议部署"
        
        result = {
            "dataset": dataset_name,
            "ppl_fp16": round(ppl_fp16, 4),
            "ppl_quantized": round(ppl_q, 4),
            "ppl_increase": round(increase, 4),
            "ppl_increase_pct": round(increase_pct, 2),
            "recommendation": recommendation
        }
        
        logger.info(f"结果:")
        logger.info(f"  FP16 PPL: {ppl_fp16:.4f}")
        logger.info(f"  Quantized PPL: {ppl_q:.4f}")
        logger.info(f"  增长: {increase:.4f} ({increase_pct:.2f}%)")
        logger.info(f"  {recommendation}\n")
        
        return result
    
    def estimate_memory_savings(self) -> Dict[str, Any]:
        """估算显存节省"""
        logger.info(f"\n{'='*60}")
        logger.info("评估显存节省")
        logger.info(f"{'='*60}\n")
        
        # 统计参数数量
        total_params = sum(p.numel() for p in self.model_fp16.parameters())
        
        # FP16 大小 (2 bytes per param)
        fp16_size_gb = (total_params * 2) / (1024 ** 3)
        
        # 4-bit 量化后大小 (0.5 bytes per param)
        quant_size_gb = (total_params * 0.5) / (1024 ** 3)
        
        # KV cache 节省 (假设 batch=1, seq=2048, num_layers=36, hidden=4096)
        # 原始: 2 * 36 * 2048 * 4096 * 2 bytes
        kv_fp16_gb = 2 * 36 * 2048 * 4096 * 2 / (1024 ** 3)
        kv_quant_gb = kv_fp16_gb * 0.25  # 4-bit 节省 75%
        
        # 总显存
        total_fp16_gb = fp16_size_gb + kv_fp16_gb
        total_quant_gb = quant_size_gb + kv_quant_gb
        
        reduction_pct = (1 - total_quant_gb / total_fp16_gb) * 100
        
        result = {
            "total_parameters": total_params,
            "model_fp16_gb": round(fp16_size_gb, 2),
            "model_quantized_gb": round(quant_size_gb, 2),
            "kv_cache_fp16_gb": round(kv_fp16_gb, 2),
            "kv_cache_quantized_gb": round(kv_quant_gb, 2),
            "total_vram_fp16_gb": round(total_fp16_gb, 2),
            "total_vram_quantized_gb": round(total_quant_gb, 2),
            "memory_reduction_pct": round(reduction_pct, 1),
            "compression_ratio": round(total_fp16_gb / total_quant_gb, 2)
        }
        
        logger.info(f"结果:")
        logger.info(f"  总参数数: {total_params:,}")
        logger.info(f"  模型显存:")
        logger.info(f"    FP16: {fp16_size_gb:.2f} GB")
        logger.info(f"    4-bit: {quant_size_gb:.2f} GB")
        logger.info(f"  KV Cache:")
        logger.info(f"    FP16: {kv_fp16_gb:.2f} GB")
        logger.info(f"    4-bit: {kv_quant_gb:.2f} GB")
        logger.info(f"  总显存:")
        logger.info(f"    FP16: {total_fp16_gb:.2f} GB")
        logger.info(f"    4-bit: {total_quant_gb:.2f} GB")
        logger.info(f"  显存节省: {reduction_pct:.1f}% ({total_fp16_gb:.1f}GB → {total_quant_gb:.1f}GB)")
        logger.info(f"  压缩比: {round(total_fp16_gb / total_quant_gb, 2)}x\n")
        
        return result
    
    def generate_report(self, output_path: str = "reports/compression_report.json") -> Dict[str, Any]:
        """生成完整评估报告"""
        logger.info(f"\n{'='*60}")
        logger.info("生成完整评估报告")
        logger.info(f"{'='*60}\n")
        
        self.load_models()
        
        report = {
            "evaluation_type": "base_model_compression",
            "timestamp": str(torch.now()) if hasattr(torch, 'now') else "unknown",
            "models": {
                "fp16": self.model_fp16_path,
                "quantized": self.model_quantized_path
            },
            "sections": {}
        }
        
        # 精度评估
        report["sections"]["perplexity"] = self.compare_perplexity()
        
        # 显存评估
        report["sections"]["memory"] = self.estimate_memory_savings()
        
        # 保存报告
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ 报告已保存: {output_path}\n")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="压缩质量评估工具")
    parser.add_argument("--model-fp16", type=str, required=True, help="FP16 模型路径")
    parser.add_argument("--model-quantized", type=str, required=True, help="量化模型路径")
    parser.add_argument("--dataset", type=str, default="wikitext2", help="评估数据集")
    parser.add_argument("--output", type=str, default="reports/compression_report.json", help="报告输出路径")
    
    args = parser.parse_args()
    
    logger.info(f"\n{'='*60}")
    logger.info("压缩质量评估")
    logger.info(f"{'='*60}\n")
    
    evaluator = CompressionQualityEvaluator(args.model_fp16, args.model_quantized)
    report = evaluator.generate_report(args.output)
    
    logger.info(f"评估完成！")
    logger.info(f"完整报告: {args.output}")


if __name__ == "__main__":
    main()
