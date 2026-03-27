"""
压缩质量监控模块
监测量化过程中的精度损失、性能变化等指标

功能:
- PPL 变化监控
- KL divergence 计算
- 推理性能基准测试
- 逐层残差能量分析（集成 llmquant residual_analyzer）
- 自动告警
"""

import os
import sys
import json
import time
import torch
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)


def _init_residual_analyzer():
    """初始化 llmquant 残差分析器"""
    try:
        llmquant_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../external_repos/llmquant')
        )
        if llmquant_path not in sys.path:
            sys.path.insert(0, llmquant_path)
        
        from residual_analyzer import (
            analyze_distribution,
            save_residual,
            analyze_all,
            clear_data,
            residual_data,
        )
        return {
            "available": True,
            "analyze_distribution": analyze_distribution,
            "save_residual": save_residual,
            "analyze_all": analyze_all,
            "clear_data": clear_data,
            "residual_data": residual_data,
        }
    except Exception as e:
        logger.warning(f"llmquant residual_analyzer 不可用: {e}")
        return {"available": False}


_residual_analyzer = _init_residual_analyzer()


class CompressionQualityMonitor:
    """压缩质量监控器"""
    
    def __init__(self, model_name: str):
        """
        初始化监控器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.baseline_metrics = {}
        self.current_metrics = {}
        self.alerts = []
        self.residual_analyzer_available = _residual_analyzer["available"]
    
    def record_baseline(
        self,
        ppl: float,
        latency_ms: float,
        vram_gb: float,
        tokens_per_sec: float,
        **kwargs
    ):
        """记录基准指标"""
        self.baseline_metrics = {
            "ppl": ppl,
            "latency_ms": latency_ms,
            "vram_gb": vram_gb,
            "tokens_per_sec": tokens_per_sec,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        logger.info(f"✓ 基准指标已记录")
        logger.info(f"  PPL: {ppl:.4f}")
        logger.info(f"  延迟: {latency_ms:.2f}ms")
        logger.info(f"  显存: {vram_gb:.2f}GB")
        logger.info(f"  吞吐: {tokens_per_sec:.1f} tokens/s")
    
    def record_compressed(
        self,
        ppl: float,
        latency_ms: float,
        vram_gb: float,
        tokens_per_sec: float,
        quantization_method: str = "unknown",
        **kwargs
    ):
        """记录压缩后的指标"""
        self.current_metrics = {
            "ppl": ppl,
            "latency_ms": latency_ms,
            "vram_gb": vram_gb,
            "tokens_per_sec": tokens_per_sec,
            "quantization_method": quantization_method,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        logger.info(f"✓ 压缩后指标已记录")
        logger.info(f"  PPL: {ppl:.4f}")
        logger.info(f"  延迟: {latency_ms:.2f}ms")
        logger.info(f"  显存: {vram_gb:.2f}GB")
        logger.info(f"  吞吐: {tokens_per_sec:.1f} tokens/s")
    
    def analyze_quality_degradation(
        self,
        ppl_increase_threshold: float = 0.5,
        vram_reduction_min: float = 0.3,
        latency_increase_threshold: float = 0.15
    ) -> Dict[str, Any]:
        """
        分析质量衰减
        
        Args:
            ppl_increase_threshold: PPL 增长告警阈值（绝对值）
            vram_reduction_min: 显存节省最小值（比例）
            latency_increase_threshold: 延迟增长告警阈值（比例）
        
        Returns:
            {
                "quality_score": float,  # 0-100
                "recommendations": List[str],
                "alerts": List[Dict],
                "metrics_comparison": Dict
            }
        """
        if not self.baseline_metrics or not self.current_metrics:
            logger.warning("基准或压缩后指标未完整记录")
            return {"quality_score": 0, "recommendations": [], "alerts": []}
        
        analysis = {
            "quality_score": 100.0,
            "recommendations": [],
            "alerts": [],
            "metrics_comparison": {}
        }
        
        # PPL 分析
        baseline_ppl = self.baseline_metrics["ppl"]
        current_ppl = self.current_metrics["ppl"]
        ppl_increase = current_ppl - baseline_ppl
        ppl_increase_pct = (ppl_increase / baseline_ppl * 100) if baseline_ppl > 0 else 0
        
        analysis["metrics_comparison"]["ppl"] = {
            "baseline": baseline_ppl,
            "current": current_ppl,
            "increase": ppl_increase,
            "increase_pct": ppl_increase_pct
        }
        
        if ppl_increase > ppl_increase_threshold:
            analysis["quality_score"] -= 30
            analysis["alerts"].append({
                "level": "warning",
                "metric": "ppl",
                "message": f"PPL 增长 {ppl_increase:.4f} 超过阈值 {ppl_increase_threshold}",
                "value": ppl_increase,
                "threshold": ppl_increase_threshold
            })
            analysis["recommendations"].append(
                f"降低量化位数或增加 calibration 样本数"
            )
        elif ppl_increase_pct < 1.0:
            analysis["quality_score"] += 20
            analysis["recommendations"].append("✓ PPL 损失极小，质量优秀")
        elif ppl_increase_pct < 2.0:
            analysis["quality_score"] += 10
            analysis["recommendations"].append("✓ PPL 损失可接受")
        
        # 显存分析
        baseline_vram = self.baseline_metrics["vram_gb"]
        current_vram = self.current_metrics["vram_gb"]
        vram_reduction = (baseline_vram - current_vram) / baseline_vram
        
        analysis["metrics_comparison"]["vram"] = {
            "baseline_gb": baseline_vram,
            "current_gb": current_vram,
            "reduction_pct": vram_reduction * 100
        }
        
        if vram_reduction < vram_reduction_min:
            analysis["quality_score"] -= 15
            analysis["alerts"].append({
                "level": "warning",
                "metric": "vram",
                "message": f"显存节省 {vram_reduction*100:.1f}% 低于预期 {vram_reduction_min*100:.1f}%",
                "value": vram_reduction,
                "threshold": vram_reduction_min
            })
        elif vram_reduction > 0.7:
            analysis["quality_score"] += 15
            analysis["recommendations"].append("✓ 显存节省显著")
        
        # 延迟分析
        baseline_latency = self.baseline_metrics["latency_ms"]
        current_latency = self.current_metrics["latency_ms"]
        latency_increase_pct = (current_latency - baseline_latency) / baseline_latency if baseline_latency > 0 else 0
        
        analysis["metrics_comparison"]["latency"] = {
            "baseline_ms": baseline_latency,
            "current_ms": current_latency,
            "increase_pct": latency_increase_pct * 100
        }
        
        if latency_increase_pct > latency_increase_threshold:
            analysis["quality_score"] -= 10
            analysis["alerts"].append({
                "level": "warning",
                "metric": "latency",
                "message": f"推理延迟增长 {latency_increase_pct*100:.1f}%",
                "value": latency_increase_pct,
                "threshold": latency_increase_threshold
            })
            analysis["recommendations"].append("考虑优化推理框架或使用更激进的剪枝策略")
        elif latency_increase_pct < -0.1:  # 延迟减少
            analysis["quality_score"] += 10
            analysis["recommendations"].append("✓ 推理速度提升")
        
        # 综合评分
        analysis["quality_score"] = max(0, min(100, analysis["quality_score"]))
        
        # 生成摘要
        if analysis["quality_score"] >= 90:
            analysis["summary"] = "🟢 质量优秀，可投入生产"
        elif analysis["quality_score"] >= 75:
            analysis["summary"] = "🟡 质量可接受，建议监控"
        elif analysis["quality_score"] >= 60:
            analysis["summary"] = "🟠 质量有所下降，需要优化"
        else:
            analysis["summary"] = "🔴 质量不达标，不建议使用"
        
        return analysis
    
    def estimate_inference_cost(
        self,
        num_requests_per_day: int = 10000,
        avg_input_tokens: int = 256,
        avg_output_tokens: int = 128
    ) -> Dict[str, Any]:
        """
        估算推理成本
        
        Args:
            num_requests_per_day: 日请求数
            avg_input_tokens: 平均输入 token 数
            avg_output_tokens: 平均输出 token 数
        
        Returns:
            成本对比分析
        """
        if not self.baseline_metrics or not self.current_metrics:
            return {}
        
        baseline_latency = self.baseline_metrics["latency_ms"]
        current_latency = self.current_metrics["latency_ms"]
        
        # 粗估：延迟 ∝ 计算
        baseline_time_per_day_hours = (
            num_requests_per_day * baseline_latency / 1000 / 3600
        )
        current_time_per_day_hours = (
            num_requests_per_day * current_latency / 1000 / 3600
        )
        
        # 粗估成本（GPU-hour，假设 A100 $1/hour）
        baseline_cost_usd = baseline_time_per_day_hours * 1.0 * 30  # 月
        current_cost_usd = current_time_per_day_hours * 1.0 * 30
        
        # 显存成本（并发 GPU 数）
        baseline_gpu_count = (self.baseline_metrics["vram_gb"] + 79) // 80  # 80GB A100
        current_gpu_count = (self.current_metrics["vram_gb"] + 79) // 80
        baseline_gpu_cost = baseline_gpu_count * 24 * 30 * 0.8  # 月租赁成本 (rough)
        current_gpu_cost = current_gpu_count * 24 * 30 * 0.8
        
        return {
            "inference_cost_analysis": {
                "baseline_monthly_usd": round(baseline_cost_usd + baseline_gpu_cost, 2),
                "compressed_monthly_usd": round(current_cost_usd + current_gpu_cost, 2),
                "savings_pct": round(
                    (1 - (current_cost_usd + current_gpu_cost) / (baseline_cost_usd + baseline_gpu_cost)) * 100
                    if (baseline_cost_usd + baseline_gpu_cost) > 0 else 0,
                    1
                ),
                "breakdown": {
                    "baseline": {
                        "compute_hours_per_day": round(baseline_time_per_day_hours, 2),
                        "gpu_count": baseline_gpu_count,
                    },
                    "compressed": {
                        "compute_hours_per_day": round(current_time_per_day_hours, 2),
                        "gpu_count": current_gpu_count,
                    }
                }
            }
        }
    
    def analyze_residual_energy(
        self,
        model_fp16,
        model_quantized,
        eval_dataset,
        target_layers: Optional[List[int]] = None,
        save_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 llmquant 的 residual_analyzer 进行逐层残差能量分析
        
        对比 FP16 和量化模型在各层的权重残差分布，
        识别量化损失集中的层，为混合精度策略提供依据。
        
        Args:
            model_fp16: FP16 原始模型
            model_quantized: 量化后的模型
            eval_dataset: 评估数据（list of input_ids tensors）
            target_layers: 要分析的层索引，None 则自动选取首/中/尾层
            save_dir: 可视化图表保存目录，None 则不生成图表
        
        Returns:
            逐层残差统计和质量评估
        """
        if not self.residual_analyzer_available:
            logger.warning("llmquant residual_analyzer 不可用，跳过残差分析")
            return {"status": "skipped", "reason": "residual_analyzer not available"}
        
        analyze_distribution = _residual_analyzer["analyze_distribution"]
        
        logger.info("开始逐层残差能量分析...")
        
        # 自动选取目标层
        num_layers = model_fp16.config.num_hidden_layers
        if target_layers is None:
            target_layers = [0, num_layers // 4, num_layers // 2, 
                           3 * num_layers // 4, num_layers - 1]
            target_layers = sorted(set(target_layers))
        
        layer_results = {}
        
        fp16_params = dict(model_fp16.named_parameters())
        quant_params = dict(model_quantized.named_parameters())
        
        for layer_idx in target_layers:
            layer_prefix = f"model.layers.{layer_idx}"
            layer_stats = {}
            
            for param_name, fp16_weight in fp16_params.items():
                if not param_name.startswith(layer_prefix):
                    continue
                if fp16_weight.ndim < 2:
                    continue
                
                short_name = param_name.replace(layer_prefix + ".", "")
                
                # 获取量化模型对应权重
                if param_name not in quant_params:
                    continue
                quant_weight = quant_params[param_name]
                
                # 确保形状一致
                if fp16_weight.shape != quant_weight.shape:
                    continue
                
                # 计算残差 R = W_fp16 - W_quantized
                residual = (fp16_weight.float() - quant_weight.float()).detach()
                
                # 使用 llmquant 的分布分析
                stats = analyze_distribution(residual)
                
                # 计算残差能量（Frobenius 范数比）
                residual_energy = torch.norm(residual).item()
                original_energy = torch.norm(fp16_weight.float()).item()
                energy_ratio = residual_energy / (original_energy + 1e-8)
                
                stats["residual_energy"] = residual_energy
                stats["original_energy"] = original_energy
                stats["energy_ratio"] = energy_ratio
                
                # 使用 llmquant 的 save_residual 记录数据（用于后续可视化）
                if save_dir:
                    H = torch.eye(fp16_weight.shape[1], device='cpu')
                    _residual_analyzer["save_residual"](
                        layer_idx, short_name, fp16_weight.cpu().float(), H, False
                    )
                    _residual_analyzer["save_residual"](
                        layer_idx, short_name, residual.cpu(), H, True
                    )
                
                layer_stats[short_name] = stats
            
            layer_results[f"layer_{layer_idx}"] = layer_stats
        
        # 生成可视化
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            try:
                _residual_analyzer["analyze_all"](
                    save_dir, salient_metric=50, target_layers=target_layers
                )
                logger.info(f"✓ 残差可视化已保存: {save_dir}")
            except Exception as e:
                logger.warning(f"残差可视化生成失败: {e}")
            finally:
                _residual_analyzer["clear_data"]()
        
        # 汇总分析
        all_energy_ratios = []
        problematic_layers = []
        for layer_key, layer_stats in layer_results.items():
            for param_name, stats in layer_stats.items():
                ratio = stats.get("energy_ratio", 0)
                all_energy_ratios.append(ratio)
                if ratio > 0.1:  # 残差能量超过原始 10%
                    problematic_layers.append({
                        "layer": layer_key,
                        "param": param_name,
                        "energy_ratio": ratio
                    })
        
        avg_energy_ratio = sum(all_energy_ratios) / len(all_energy_ratios) if all_energy_ratios else 0
        
        summary = {
            "status": "success",
            "num_layers_analyzed": len(target_layers),
            "avg_energy_ratio": avg_energy_ratio,
            "max_energy_ratio": max(all_energy_ratios) if all_energy_ratios else 0,
            "problematic_layers": problematic_layers,
            "layer_details": layer_results,
        }
        
        if avg_energy_ratio < 0.05:
            summary["assessment"] = "✓ 残差能量极低，量化质量优秀"
        elif avg_energy_ratio < 0.1:
            summary["assessment"] = "⚠ 残差能量可接受，建议关注高损失层"
        else:
            summary["assessment"] = "✗ 残差能量偏高，建议对高损失层使用更高精度"
        
        if problematic_layers:
            summary["recommendation"] = (
                f"建议对以下层保持 FP16 或使用 8-bit 量化: "
                + ", ".join(p["layer"] for p in problematic_layers[:5])
            )
        
        logger.info(f"残差分析完成: avg_energy_ratio={avg_energy_ratio:.6f}, "
                    f"problematic_layers={len(problematic_layers)}")
        
        return summary
    
    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """生成完整质量报告"""
        report = {
            "model": self.model_name,
            "timestamp": datetime.now().isoformat(),
            "baseline_metrics": self.baseline_metrics,
            "compressed_metrics": self.current_metrics,
            "quality_analysis": self.analyze_quality_degradation(),
            "cost_analysis": self.estimate_inference_cost()
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"✓ 质量报告已保存: {output_path}")
        
        return report


def calculate_kl_divergence(
    logits_baseline: torch.Tensor,
    logits_compressed: torch.Tensor,
    temperature: float = 1.0
) -> float:
    """
    计算 KL divergence（衡量分布差异）
    
    Args:
        logits_baseline: 基础模型 logits
        logits_compressed: 压缩模型 logits
        temperature: 温度参数
    
    Returns:
        KL divergence 值
    """
    import torch.nn.functional as F
    
    # 转换为概率分布
    p = F.softmax(logits_baseline / temperature, dim=-1)
    q = F.softmax(logits_compressed / temperature, dim=-1)
    
    # 计算 KL(P||Q)
    kl = torch.sum(p * (torch.log(p + 1e-8) - torch.log(q + 1e-8)))
    
    return kl.item()


def calculate_cosine_similarity(
    output_baseline: torch.Tensor,
    output_compressed: torch.Tensor
) -> float:
    """
    计算余弦相似度
    
    Args:
        output_baseline: 基础模型输出
        output_compressed: 压缩模型输出
    
    Returns:
        余弦相似度 (-1 到 1)
    """
    import torch.nn.functional as F
    
    # 展平并正规化
    p = F.normalize(output_baseline.flatten(), p=2, dim=0)
    q = F.normalize(output_compressed.flatten(), p=2, dim=0)
    
    # 计算余弦相似度
    similarity = torch.dot(p, q)
    
    return similarity.item()
