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


def _remap_obr_state_dict(obr_sd: dict, orig_model) -> dict:
    """
    将 OBR 压缩后的 state_dict key 映射回原始模型的 key。
    
    OBR 压缩后的 key 格式（FlatQuantizedLinear 包装）：
      linear_attn.q_proj.linear.weight  →  linear_attn.in_proj_qkv.weight (部分)
      linear_attn.k_proj.linear.weight  →  linear_attn.in_proj_qkv.weight (部分)
      linear_attn.v_proj.linear.weight  →  linear_attn.in_proj_qkv.weight (部分)
      self_attn.q_proj.linear.weight    →  self_attn.q_proj.weight
      mlp.up_proj.linear.weight         →  mlp.up_proj.weight
    """
    remapped = {}
    orig_sd = orig_model.state_dict()
    
    # 先把所有非 .linear.weight 的 key 直接映射（embed_tokens, norm 等）
    for k, v in obr_sd.items():
        # 跳过量化器参数（weight_quantizer.scale 等）
        if 'weight_quantizer' in k or 'act_quantizer' in k:
            continue
        # 跳过变换矩阵（已在 reparameterize 时融合进权重）
        if 'trans.' in k or 'ln_trans' in k or 'out_trans' in k or \
           'vcache_trans' in k or 'kcache_trans' in k:
            continue
        
        # FlatQuantizedLinear 的权重：xxx.linear.weight → xxx.weight
        # 也处理 _module. 前缀的情况
        mapped = False
        test_key = k
        
        # 先去掉 _module. 前缀
        if '._module.' in test_key:
            test_key = test_key.replace('._module.', '.')
        
        # 再去掉 .linear. 中间层
        if '.linear.weight' in test_key:
            test_key = test_key.replace('.linear.weight', '.weight')
        elif '.linear.bias' in test_key:
            test_key = test_key.replace('.linear.bias', '.bias')
        
        if test_key in orig_sd:
            remapped[test_key] = v.to(orig_sd[test_key].dtype)
            continue
        
        # 直接匹配的 key
        if k in orig_sd:
            remapped[k] = v.to(orig_sd[k].dtype)
            continue
    
    # 处理 GatedDeltaNet 的拆分 q/k/v_proj → in_proj_qkv 合并
    # 找所有需要合并的层
    layers_needing_merge = set()
    for k in obr_sd.keys():
        if '.linear_attn.q_proj.linear.weight' in k:
            prefix = k.split('.linear_attn.q_proj.linear.weight')[0]
            layers_needing_merge.add(prefix)
    
    for prefix in layers_needing_merge:
        q_key = f"{prefix}.linear_attn.q_proj.linear.weight"
        k_key = f"{prefix}.linear_attn.k_proj.linear.weight"
        v_key = f"{prefix}.linear_attn.v_proj.linear.weight"
        orig_qkv_key = f"{prefix}.linear_attn.in_proj_qkv.weight"
        
        if all(k in obr_sd for k in [q_key, k_key, v_key]) and orig_qkv_key in orig_sd:
            q = obr_sd[q_key]
            k_w = obr_sd[k_key]
            v = obr_sd[v_key]
            # 合并回 in_proj_qkv
            merged = torch.cat([q, k_w, v], dim=0)
            if merged.shape == orig_sd[orig_qkv_key].shape:
                remapped[orig_qkv_key] = merged.to(orig_sd[orig_qkv_key].dtype)
            else:
                logger.warning(f"形状不匹配: {orig_qkv_key} {merged.shape} vs {orig_sd[orig_qkv_key].shape}")
    
    loaded = len(remapped)
    total = len(orig_sd)
    logger.info(f"  key 映射: {loaded}/{total} 个权重成功映射")
    
    return remapped


class CompressionQualityEvaluator:
    """压缩质量评估器"""
    
    def __init__(self, model_fp16_path: str, model_quantized_path: str):
        self.model_fp16_path = model_fp16_path
        self.model_quantized_path = model_quantized_path
        self.tokenizer = None
        self.model_fp16 = None
        self.model_quantized = None
    
    def load_models(self):
        """加载两个模型（支持 OBR 压缩格式）"""
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
        
        # 评估 FP16 的 PPL 后释放显存，再加载压缩模型
        # 避免同时加载两个模型导致 OOM
        self._fp16_ppl = None
        
        logger.info("\n加载压缩模型...")
        # 检查是否是 OBR 格式（quantized_model.pt）
        obr_weights = os.path.join(self.model_quantized_path, "quantized_model.pt")
        if os.path.exists(obr_weights):
            logger.info(f"检测到 OBR 压缩格式: {obr_weights}")
            self.model_quantized = self._load_obr_model(obr_weights)
        else:
            self.model_quantized = AutoModelForCausalLM.from_pretrained(
                self.model_quantized_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
        logger.info(f"✓ 压缩模型加载完成")
    
    def _load_obr_model(self, obr_weights_path):
        """加载 OBR 压缩模型（与压缩时一致的结构）"""
        import sys as _sys
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if project_root not in _sys.path:
            _sys.path.insert(0, project_root)
        obr_path = os.path.join(project_root, "external_repos", "OBR", "FlatQuant")
        if obr_path not in _sys.path:
            _sys.path.insert(0, obr_path)
        
        from flatquant import model_utils, flat_utils
        from backend.model_compression.obr_wrapper import OBRCompressor
        
        compressor = OBRCompressor(
            model_name=self.model_fp16_path,
            output_dir=os.path.dirname(obr_weights_path),
            w_bits=4, a_bits=16, k_bits=4, v_bits=4,
        )
        args = compressor._build_obr_args()
        
        logger.info("  加载原始模型结构...")
        model, apply_flatquant = model_utils.get_model(args.model, None)
        model.eval()
        
        if args.quantize:
            logger.info("  应用 FlatQuant 包装...")
            model = apply_flatquant(args, model)
        
        # 先尝试不 reparameterize 直接加载
        logger.info(f"  加载压缩权重（不 reparameterize）: {obr_weights_path}")
        state_dict = torch.load(obr_weights_path, map_location="cpu")
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        logger.info(f"  不 reparameterize 加载结果: missing={len(missing)}, unexpected={len(unexpected)}")
        if missing and len(missing) > 0:
            logger.info(f"  缺失 key 示例: {missing[:3]}")
        if unexpected and len(unexpected) > 0:
            logger.info(f"  多余 key 示例: {unexpected[:3]}")
        
        # 如果有 missing，说明需要 reparameterize 来匹配结构
        if len(missing) > 0:
            logger.info("  有缺失 key，重新加载：先 reparameterize 再 load_state_dict")
            # 重新加载原始模型
            model, apply_flatquant = model_utils.get_model(args.model, None)
            model.eval()
            model = apply_flatquant(args, model)
            flat_utils.reparameterize_model(model)
            missing2, unexpected2 = model.load_state_dict(state_dict, strict=False)
            logger.info(f"  reparameterize 后加载结果: missing={len(missing2)}, unexpected={len(unexpected2)}")
        state_dict = torch.load(obr_weights_path, map_location="cpu")
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        logger.info(f"  加载结果: missing={len(missing)}, unexpected={len(unexpected)}")
        
        for m in model.modules():
            if hasattr(m, '_eval_mode'):
                m._eval_mode = True
            if hasattr(m, '_ori_mode'):
                m._ori_mode = False
        
        model = model.to("cuda").eval()
        return model
    
    def _load_obr_model(self, obr_weights_path):
        """
        加载 OBR 压缩模型：
        1. 加载原始模型
        2. 应用 FlatQuant 包装（与压缩时一致）
        3. 加载压缩后的 state_dict
        4. 设为 eval 模式
        """
        import sys
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        obr_path = os.path.join(project_root, "external_repos", "OBR", "FlatQuant")
        if obr_path not in sys.path:
            sys.path.insert(0, obr_path)
        
        from flatquant import model_utils
        from backend.model_compression.obr_wrapper import OBRCompressor
        
        # 构建与压缩时一致的参数
        compressor = OBRCompressor(
            model_name=self.model_fp16_path,
            output_dir=os.path.dirname(obr_weights_path),
            w_bits=4, a_bits=16, k_bits=4, v_bits=4,
        )
        args = compressor._build_obr_args()
        
        # 加载模型并应用 FlatQuant 包装
        logger.info("  加载原始模型结构...")
        model, apply_flatquant = model_utils.get_model(args.model, None)
        model.eval()
        
        if args.quantize:
            logger.info("  应用 FlatQuant 包装...")
            model = apply_flatquant(args, model)
        
        # 方案 D：不做 reparameterize（避免重复融合变换矩阵）
        # 只切换变换矩阵到 eval 结构，让 state_dict key 匹配
        logger.info("  切换所有变换矩阵到 eval 结构...")
        for m in model.modules():
            if hasattr(m, 'to_eval_mode') and hasattr(m, '_eval_mode') and not m._eval_mode:
                m.to_eval_mode()
        
        # 加载压缩后的 state_dict
        logger.info(f"  加载压缩权重: {obr_weights_path}")
        state_dict = torch.load(obr_weights_path, map_location="cpu")
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        logger.info(f"  加载结果: missing={len(missing)}, unexpected={len(unexpected)}")
        if missing:
            logger.info(f"  缺失 key 示例: {missing[:5]}")
        
        # 设为 eval 模式，所有 FlatQuantizedLinear 切换到 eval forward
        for module in model.modules():
            if hasattr(module, '_eval_mode'):
                module._eval_mode = True
            if hasattr(module, '_ori_mode'):
                module._ori_mode = False
        
        model = model.to("cuda")
        model.eval()
        return model
    
    def load_models_sequential(self):
        """
        顺序加载模型（节省显存）
        先评估 FP16 PPL，释放后再评估压缩模型 PPL
        """
        logger.info("加载 tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_fp16_path, trust_remote_code=True
        )
        
        # 加载并评估 FP16
        logger.info("\n加载 FP16 模型...")
        self.model_fp16 = AutoModelForCausalLM.from_pretrained(
            self.model_fp16_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        logger.info(f"✓ FP16 模型加载完成")
        self._fp16_ppl = self.evaluate_perplexity(self.model_fp16)
        
        # 释放 FP16
        del self.model_fp16
        self.model_fp16 = None
        torch.cuda.empty_cache()
        import gc; gc.collect()
        logger.info("FP16 模型已释放")
        
        # 加载压缩模型
        logger.info("\n加载压缩模型...")
        obr_weights = os.path.join(self.model_quantized_path, "quantized_model.pt")
        if os.path.exists(obr_weights):
            logger.info(f"检测到 OBR 压缩格式: {obr_weights}")
            self.model_quantized = self._load_obr_model(obr_weights)
        else:
            self.model_quantized = AutoModelForCausalLM.from_pretrained(
                self.model_quantized_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
        logger.info(f"✓ 压缩模型加载完成")
    
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
        
        # 使用顺序加载模式节省显存
        self.load_models_sequential()
        
        report = {
            "evaluation_type": "base_model_compression",
            "models": {
                "fp16": self.model_fp16_path,
                "quantized": self.model_quantized_path
            },
            "sections": {}
        }
        
        # FP16 PPL 已在 load_models_sequential 中评估
        ppl_fp16 = self._fp16_ppl
        ppl_q = self.evaluate_perplexity(self.model_quantized)
        
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
        
        report["sections"]["perplexity"] = {
            "dataset": "wikitext2",
            "ppl_fp16": round(ppl_fp16, 4),
            "ppl_quantized": round(ppl_q, 4),
            "ppl_increase": round(increase, 4),
            "ppl_increase_pct": round(increase_pct, 2),
            "recommendation": recommendation
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"评估结果:")
        logger.info(f"  FP16 PPL: {ppl_fp16:.4f}")
        logger.info(f"  压缩后 PPL: {ppl_q:.4f}")
        logger.info(f"  PPL 增长: {increase:.4f} ({increase_pct:.2f}%)")
        logger.info(f"  {recommendation}")
        logger.info(f"{'='*60}\n")
        
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
