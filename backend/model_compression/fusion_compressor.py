"""
OBR + llmquant 融合压缩器（务实方案）

核心改进：在 FlatQuant 包装状态下收集激活统计，
确保 Hessian 和激活熵基于变换后的分布计算。

流程：
1. 加载模型 + FlatQuant 包装
2. FlatQuant 校准训练
3. 收集变换后的激活统计（Hessian、激活熵、稳定秩）
4. FlatQuant 重参数化
5. llmquant SVD + 残差量化（使用步骤 3 的统计）
6. 保存压缩模型

使用方式:
python backend/model_compression/compress_base_model_fusion.py \
  --model /root/autodl-tmp/models/base/Qwen3.5-9B \
  --output models/qwen-fusion \
  --nsamples 128
"""

import os
import sys
import time
import json
import logging
import argparse
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import torch
import torch.nn as nn

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


def _elapsed(start):
    return f"[{time.time() - start:.0f}s]"


def find_linear_layers(module, prefix=''):
    """递归查找所有 nn.Linear 层"""
    layers = {}
    for name, child in module.named_children():
        full_name = f"{prefix}.{name}" if prefix else name
        if isinstance(child, nn.Linear):
            layers[full_name] = child
        else:
            # 检查 FlatQuantizedLinear 包装
            if hasattr(child, 'linear') and isinstance(child.linear, nn.Linear):
                layers[full_name] = child.linear
            else:
                layers.update(find_linear_layers(child, full_name))
    return layers


class FusionCompressor:
    """
    OBR + llmquant 融合压缩器
    
    在 FlatQuant 包装状态下收集激活统计，
    确保 Hessian 基于变换后的分布计算。
    """
    
    def __init__(
        self,
        model_name: str,
        output_dir: str,
        # FlatQuant 参数
        w_bits: int = 4,
        a_bits: int = 16,
        k_bits: int = 4,
        v_bits: int = 4,
        nsamples: int = 128,
        cali_dataset: str = 'wikitext2',
        flatquant_epochs: int = 15,
        # llmquant 参数
        svd_rank: int = 256,
        adaptive_rank: bool = True,
        avg_rank: int = 256,
        min_rank: int = 128,
        max_rank: int = 512,
        quant_method: str = '4bit',
        blocksize: int = 128,
        salient_metric: str = 'hessian',
        # 行剪枝
        row_prune_enable: bool = True,
        row_prune_m_candidates: Optional[List[int]] = None,
        # OBR 两组残差
        obr_twogroup_enable: bool = True,
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        # FlatQuant
        self.w_bits = w_bits
        self.a_bits = a_bits
        self.k_bits = k_bits
        self.v_bits = v_bits
        self.nsamples = nsamples
        self.cali_dataset = cali_dataset
        self.flatquant_epochs = flatquant_epochs
        # llmquant
        self.svd_rank = svd_rank
        self.adaptive_rank = adaptive_rank
        self.avg_rank = avg_rank
        self.min_rank = min_rank
        self.max_rank = max_rank
        self.quant_method = quant_method
        self.blocksize = blocksize
        self.salient_metric = salient_metric
        self.row_prune_enable = row_prune_enable
        self.row_prune_m_candidates = row_prune_m_candidates or [0, 4, 8, 16, 32, 64]
        self.obr_twogroup_enable = obr_twogroup_enable

    def _build_flatquant_args(self) -> argparse.Namespace:
        """构建 FlatQuant 所需的参数（复用 OBRCompressor 的逻辑）"""
        from backend.model_compression.obr_wrapper import OBRCompressor
        compressor = OBRCompressor(
            model_name=self.model_name,
            output_dir=self.output_dir,
            w_bits=self.w_bits,
            a_bits=self.a_bits,
            k_bits=self.k_bits,
            v_bits=self.v_bits,
            nsamples=self.nsamples,
            cali_dataset=self.cali_dataset,
        )
        args = compressor._build_obr_args()
        args.epochs = self.flatquant_epochs
        return args

    def compress(self) -> Dict[str, Any]:
        """执行融合压缩"""
        start_time = time.time()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"OBR + llmquant 融合压缩")
        logger.info(f"{'='*60}")
        logger.info(f"  模型: {self.model_name}")
        logger.info(f"  FlatQuant: W{self.w_bits}A{self.a_bits}K{self.k_bits}V{self.v_bits}")
        logger.info(f"  llmquant: SVD rank={self.svd_rank}, method={self.quant_method}")
        logger.info(f"  自适应 rank: {self.adaptive_rank}")
        
        try:
            # 设置路径
            obr_path = os.path.join(PROJECT_ROOT, "external_repos", "OBR", "FlatQuant")
            llmquant_path = os.path.join(PROJECT_ROOT, "external_repos", "llmquant")
            if obr_path not in sys.path:
                sys.path.insert(0, obr_path)
            if llmquant_path not in sys.path:
                sys.path.insert(0, llmquant_path)
            
            from flatquant import utils, model_utils, data_utils, train_utils, flat_utils
            import transformers
            
            args = self._build_flatquant_args()
            utils.seed_everything(seed=args.seed)
            
            # ========== 阶段 1: 加载模型 + FlatQuant 包装 ==========
            logger.info(f"\n{_elapsed(start_time)} [1/6] 加载模型...")
            model, apply_flatquant_to_model = model_utils.get_model(args.model, None)
            model.eval()
            
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                args.model, use_fast=False, trust_remote_code=True
            )
            
            logger.info(f"{_elapsed(start_time)} [1/6] 加载校准数据...")
            trainloader = data_utils.get_loaders(
                args, args.cali_dataset, nsamples=args.nsamples,
                seed=args.seed, model=args.model,
                seqlen=model.seqlen, eval_mode=False
            )
            
            if args.quantize:
                logger.info(f"\n{_elapsed(start_time)} [1/6] 应用 FlatQuant 包装...")
                model = apply_flatquant_to_model(args, model)
            logger.info(f"{_elapsed(start_time)} [1/6] 完成 ✓")
            
            # ========== 阶段 2: FlatQuant 校准训练 ==========
            if args.cali_trans or args.add_diag or args.lwc or args.lac:
                num_layers = model.config.num_hidden_layers
                logger.info(f"\n{_elapsed(start_time)} [2/6] FlatQuant 校准训练 ({num_layers} 层 × {args.epochs} epochs)...")
                train_utils.cali_flat_quant(args, model, trainloader, utils.DEV, logger=logger)
                logger.info(f"{_elapsed(start_time)} [2/6] 校准训练完成 ✓")
            
            # ========== 阶段 3: 收集变换后的激活统计 ==========
            logger.info(f"\n{_elapsed(start_time)} [3/6] 收集变换后的激活统计...")
            logger.info(f"  （关键：在 FlatQuant 包装状态下收集，确保统计基于变换后的分布）")
            
            layer_hessians, layer_stats = self._collect_transformed_activations(
                model, trainloader, args
            )
            logger.info(f"{_elapsed(start_time)} [3/6] 激活统计收集完成 ✓")
            logger.info(f"  收集了 {len(layer_hessians)} 个层的 Hessian")
            
            # ========== 阶段 4: FlatQuant 重参数化 ==========
            if args.quantize:
                logger.info(f"\n{_elapsed(start_time)} [4/6] FlatQuant 重参数化...")
                flat_utils.reparameterize_model(model)
                logger.info(f"{_elapsed(start_time)} [4/6] 重参数化完成 ✓")
            
            # ========== 阶段 5: llmquant SVD + 残差量化 ==========
            logger.info(f"\n{_elapsed(start_time)} [5/6] llmquant SVD + 残差量化...")
            self._llmquant_quantize(model, trainloader, layer_hessians, layer_stats, args)
            logger.info(f"{_elapsed(start_time)} [5/6] llmquant 量化完成 ✓")
            
            # ========== 阶段 6: 保存 ==========
            save_path = os.path.join(self.output_dir, "quantized_model.pt")
            logger.info(f"\n{_elapsed(start_time)} [6/6] 保存模型到 {save_path}")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save(model.state_dict(), save_path)
            
            file_size_gb = os.path.getsize(save_path) / (1024**3)
            total_time = time.time() - start_time
            
            # 保存压缩配置
            config = {
                "method": "OBR_llmquant_fusion",
                "model_name": self.model_name,
                "flatquant": {"w_bits": self.w_bits, "a_bits": self.a_bits,
                              "k_bits": self.k_bits, "v_bits": self.v_bits},
                "llmquant": {"svd_rank": self.svd_rank, "adaptive_rank": self.adaptive_rank,
                             "quant_method": self.quant_method, "blocksize": self.blocksize},
                "file_size_gb": round(file_size_gb, 2),
                "total_time_minutes": round(total_time / 60, 1),
                "completion_time": datetime.now().isoformat(),
            }
            config_path = os.path.join(self.output_dir, "compression_config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{_elapsed(start_time)} [6/6] 模型已保存 ({file_size_gb:.2f} GB) ✓")
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ 融合压缩成功 (总耗时: {total_time/60:.1f} 分钟)")
            logger.info(f"{'='*60}")
            
            return {"status": "success", **config}
        
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"\n❌ 融合压缩失败 (在 {elapsed:.0f}s 时): {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}

    def _collect_transformed_activations(
        self, model, trainloader, args
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, Dict[str, float]]]:
        """
        在 FlatQuant 包装状态下收集激活统计
        
        关键：此时模型的 forward 经过 ln_trans 变换，
        收集到的 Hessian 和激活熵是基于变换后分布的。
        
        Returns:
            layer_hessians: {layer_key: H} Hessian 矩阵
            layer_stats: {layer_key: {activation_entropy, stable_rank, activation_norm}}
        """
        from flatquant import utils
        
        layers = model.model.layers
        device = utils.DEV
        
        # 收集第一层的输入
        use_cache = model.config.use_cache
        model.config.use_cache = False
        
        dtype = next(iter(model.parameters())).dtype
        seqlen = min(model.seqlen, 2048)
        inps = torch.zeros(
            (self.nsamples, seqlen, model.config.hidden_size),
            dtype=dtype, device=device
        )
        cache = {"i": 0, "attention_mask": None, "position_ids": None}
        
        layers[0] = layers[0].to(device)
        
        class Catcher(nn.Module):
            def __init__(self, module):
                super().__init__()
                self.module = module
                if hasattr(module, "attention_type"):
                    self.attention_type = module.attention_type
            
            def forward(self, inp, **kwargs):
                inps[cache["i"]] = inp
                cache["i"] += 1
                cache["attention_mask"] = kwargs.get("attention_mask", None)
                cache["position_ids"] = kwargs.get("position_ids", None)
                raise ValueError
        
        layers[0] = Catcher(layers[0])
        for batch in trainloader:
            try:
                inp = batch[0].to(device)
                if inp.dim() == 1:
                    inp = inp.unsqueeze(0)
                seq_len = inp.shape[1]
                attention_mask = torch.ones((inp.shape[0], seq_len), dtype=torch.long, device=device)
                position_ids = torch.arange(0, seq_len, dtype=torch.long, device=device).unsqueeze(0)
                model(input_ids=inp, attention_mask=attention_mask, position_ids=position_ids)
            except ValueError:
                pass
        
        layers[0] = layers[0].module
        layers[0] = layers[0].cpu()
        model.model.embed_tokens = model.model.embed_tokens.cpu()
        model.model.norm = model.model.norm.cpu()
        torch.cuda.empty_cache()
        
        outs = torch.zeros_like(inps)
        attention_mask = cache["attention_mask"]
        position_ids = cache.get("position_ids", None)
        
        # 逐层收集 Hessian 和激活统计
        layer_hessians = {}
        layer_stats = {}
        
        for i in range(len(layers)):
            layer = layers[i].to(device)
            subset = find_linear_layers(layer)
            
            logger.info(f"  收集 layer {i}/{len(layers)} 的激活统计 ({len(subset)} 个 Linear)...")
            
            # 为每个 Linear 层创建 Hessian 收集器
            hessian_collectors = {}
            activation_collectors = {}
            
            for name, linear in subset.items():
                n_cols = linear.weight.shape[1]
                hessian_collectors[name] = {
                    "H": torch.zeros((n_cols, n_cols), device=device, dtype=torch.float32),
                    "nsamples": 0,
                }
                activation_collectors[name] = []
            
            def make_hook(name, linear):
                def hook_fn(module, inp, out):
                    x = inp[0].data
                    if x.dim() == 3:
                        x = x.reshape(-1, x.shape[-1])
                    x = x.float()
                    
                    # 累积 Hessian: H += X^T X
                    collector = hessian_collectors[name]
                    collector["H"] += x.T @ x
                    collector["nsamples"] += x.shape[0]
                    
                    # 收集激活值用于计算熵
                    activation_collectors[name].append(x.cpu())
                return hook_fn
            
            handles = []
            for name, linear in subset.items():
                handles.append(linear.register_forward_hook(make_hook(name, linear)))
            
            # 跑 forward
            for j in range(self.nsamples):
                try:
                    if position_ids is not None:
                        pos = position_ids.to(device)
                    else:
                        pos = torch.arange(seqlen, device=device).unsqueeze(0)
                    
                    # 尝试不同的 forward 签名
                    try:
                        if hasattr(model.model, 'rotary_emb'):
                            position_embeddings = model.model.rotary_emb(
                                inps[j].unsqueeze(0), pos
                            )
                            outs[j] = layer(
                                inps[j].unsqueeze(0),
                                attention_mask=attention_mask,
                                position_ids=pos,
                                position_embeddings=position_embeddings,
                            )[0]
                        else:
                            outs[j] = layer(
                                inps[j].unsqueeze(0),
                                attention_mask=attention_mask,
                                position_ids=pos,
                            )[0]
                    except TypeError:
                        outs[j] = layer(
                            inps[j].unsqueeze(0),
                            attention_mask=attention_mask,
                        )[0]
                except Exception as e:
                    logger.warning(f"  layer {i} sample {j} forward 失败: {e}")
                    outs[j] = inps[j]
            
            for h in handles:
                h.remove()
            
            # 处理收集到的统计
            for name in subset:
                collector = hessian_collectors[name]
                layer_key = f"{i}.{name}"
                
                # 归一化 Hessian
                H = collector["H"]
                if collector["nsamples"] > 0:
                    H /= collector["nsamples"]
                layer_hessians[layer_key] = H.cpu()
                
                # 计算激活熵和稳定秩
                stats = {"activation_entropy": 1.0, "stable_rank": 1.0, "activation_norm": 1.0}
                
                if activation_collectors[name]:
                    try:
                        all_acts = torch.cat(activation_collectors[name], dim=0)
                        
                        # 激活范数
                        stats["activation_norm"] = float(all_acts.norm(dim=1).mean().item())
                        
                        # 激活熵（基于特征标准差的几何平均）
                        feature_stds = torch.std(all_acts, dim=0)
                        eps = 1e-8
                        log_stds = torch.log(feature_stds + eps)
                        stats["activation_entropy"] = float(torch.exp(log_stds.mean()).item())
                        
                        # 稳定秩（从 Hessian 的特征值计算）
                        try:
                            eigvals = torch.linalg.eigvalsh(H.cpu().float())
                            eigvals = torch.clamp(eigvals, min=0)
                            total_energy = eigvals.sum().item()
                            max_eigval = eigvals.max().item()
                            if max_eigval > 1e-9:
                                stats["stable_rank"] = float(total_energy / max_eigval)
                        except Exception:
                            W = subset[name].weight.data.float()
                            S = torch.linalg.svdvals(W)
                            S2 = S ** 2
                            stats["stable_rank"] = float(S2.sum().item() / (S[0].item() ** 2 + 1e-9))
                    except Exception as e:
                        logger.warning(f"  {layer_key} 统计计算失败: {e}")
                
                layer_stats[layer_key] = stats
            
            # 清理
            layers[i] = layer.cpu()
            del hessian_collectors, activation_collectors
            torch.cuda.empty_cache()
            
            inps, outs = outs, inps
        
        model.config.use_cache = use_cache
        return layer_hessians, layer_stats

    def _llmquant_quantize(
        self, model, trainloader, layer_hessians, layer_stats, flatquant_args
    ):
        """
        使用 llmquant 的 BRAGPTQ 逐层量化
        使用阶段 3 收集的变换后 Hessian 和激活统计
        """
        from binary import Binarization
        from bigptq import BRAGPTQ
        from flatquant import utils
        
        device = utils.DEV
        layers = model.model.layers
        
        use_cache = model.config.use_cache
        model.config.use_cache = False
        
        # 重新收集输入（重参数化后的模型）
        dtype = next(iter(model.parameters())).dtype
        seqlen = min(model.seqlen, 2048)
        inps = torch.zeros(
            (self.nsamples, seqlen, model.config.hidden_size),
            dtype=dtype, device=device
        )
        cache = {"i": 0, "attention_mask": None, "position_ids": None}
        
        model.model.embed_tokens = model.model.embed_tokens.to(device)
        model.model.norm = model.model.norm.to(device)
        layers[0] = layers[0].to(device)
        
        class Catcher(nn.Module):
            def __init__(self, module):
                super().__init__()
                self.module = module
                if hasattr(module, "attention_type"):
                    self.attention_type = module.attention_type
            
            def forward(self, inp, **kwargs):
                inps[cache["i"]] = inp
                cache["i"] += 1
                cache["attention_mask"] = kwargs.get("attention_mask", None)
                cache["position_ids"] = kwargs.get("position_ids", None)
                raise ValueError
        
        layers[0] = Catcher(layers[0])
        for batch in trainloader:
            try:
                inp = batch[0].to(device)
                if inp.dim() == 1:
                    inp = inp.unsqueeze(0)
                seq_len = inp.shape[1]
                attention_mask = torch.ones((inp.shape[0], seq_len), dtype=torch.long, device=device)
                position_ids = torch.arange(0, seq_len, dtype=torch.long, device=device).unsqueeze(0)
                model(input_ids=inp, attention_mask=attention_mask, position_ids=position_ids)
            except ValueError:
                pass
        
        layers[0] = layers[0].module
        layers[0] = layers[0].cpu()
        model.model.embed_tokens = model.model.embed_tokens.cpu()
        model.model.norm = model.model.norm.cpu()
        torch.cuda.empty_cache()
        
        outs = torch.zeros_like(inps)
        attention_mask = cache["attention_mask"]
        position_ids = cache.get("position_ids", None)
        
        # 自适应 rank 分配
        rank_allocations = {}
        if self.adaptive_rank:
            rank_allocations = self._compute_rank_allocations(layer_stats)
            logger.info(f"  自适应 rank 分配完成: {len(rank_allocations)} 层")
        
        # 逐层量化
        total_layers = len(layers)
        layer_results = []
        
        for i in range(total_layers):
            layer = layers[i].to(device)
            subset = find_linear_layers(layer)
            
            if not subset:
                for j in range(self.nsamples):
                    outs[j] = self._forward_layer(model, layer, inps[j].unsqueeze(0),
                                                   attention_mask, position_ids)
                layers[i] = layer.cpu()
                inps, outs = outs, inps
                continue
            
            # 为每个 Linear 创建 BRAGPTQ 量化器
            gptq_handlers = {}
            for name, linear in subset.items():
                braq_quantizer = Binarization(
                    linear.weight,
                    method=self.quant_method,
                    groupsize=self.blocksize,
                    iterative_2bit_enable=(self.quant_method in {"2bit", "3bit", "4bit"}),
                    iterative_2bit_iters=5,
                    iterative_2bit_eps=1e-8,
                    iterative_2bit_update_offset=True,
                    iterative_2bit_fixed_iters=False,
                    iterative_2bit_print_mse=False,
                )
                handler = BRAGPTQ(
                    linear,
                    braq_quantizer,
                    salient_metric=self.salient_metric,
                    disable_gptq=False,
                )
                
                # 注入预收集的 Hessian（关键改进）
                layer_key = f"{i}.{name}"
                if layer_key in layer_hessians:
                    handler.H = layer_hessians[layer_key].to(device).float()
                    handler.nsamples = self.nsamples
                    logger.info(f"  layer {i} {name}: 使用预收集的变换后 Hessian")
                
                gptq_handlers[name] = handler
            
            # 如果没有预收集的 Hessian，正常收集
            needs_collection = any(
                f"{i}.{name}" not in layer_hessians for name in gptq_handlers
            )
            if needs_collection:
                def add_batch(name):
                    def tmp(_, inp, out):
                        gptq_handlers[name].add_batch(inp[0].data, out.data)
                    return tmp
                
                handles = []
                for name in gptq_handlers:
                    if f"{i}.{name}" not in layer_hessians:
                        handles.append(subset[name].register_forward_hook(add_batch(name)))
                
                for j in range(self.nsamples):
                    outs[j] = self._forward_layer(model, layer, inps[j].unsqueeze(0),
                                                   attention_mask, position_ids)
                for h in handles:
                    h.remove()
            else:
                # 只跑 forward 更新 outs
                for j in range(self.nsamples):
                    outs[j] = self._forward_layer(model, layer, inps[j].unsqueeze(0),
                                                   attention_mask, position_ids)
            
            # 逐层量化
            for name, handler in gptq_handlers.items():
                layer_key = f"{i}.{name}"
                layer_rank = rank_allocations.get(layer_key, self.svd_rank)
                
                logger.info(f"  量化 layer {i} {name} (rank={layer_rank})...")
                
                info = handler.fasterquant(
                    percdamp=0.01,
                    blocksize=self.blocksize,
                    svd_rank=layer_rank,
                    svd_enable=True,
                    quant_method=self.quant_method,
                    obr=True,
                    block_gptq_enable=True,
                    gptq_groupsize=self.blocksize,
                    gptq_act_order=True,
                    svd_row_prune_search_enable=self.row_prune_enable,
                    svd_row_prune_m_candidates=self.row_prune_m_candidates,
                    svd_row_prune_score_metric="wanda" if self.salient_metric == "hessian" else "magnitude",
                    svd_row_prune_quant_scheme=f"std{self.quant_method}",
                    svd_2bit_obr_twogroup_adaptive_enable=self.obr_twogroup_enable,
                    svd_2bit_obr_twogroup_adaptive_max_stages=3,
                    svd_2bit_obr_twogroup_adaptive_e128_threshold=0.2,
                    svd_2bit_obr_twogroup_adaptive_base_ratio=0.1,
                    post_gptq_refill_enable=True,
                    post_gptq_refill_row_ratio=0.2,
                    post_gptq_refill_pos_ratio=0.2,
                )
                
                if isinstance(info, dict):
                    avg_bits = info.get("layer_avg_weight_bits", 0)
                    error = info.get("error", 0)
                    logger.info(f"    avg_bits={avg_bits:.4f}, error={error:.4f}")
                    layer_results.append({
                        "layer": layer_key, "rank": layer_rank,
                        "avg_bits": avg_bits, "error": error,
                    })
                
                handler.free()
            
            # 更新 outs
            for j in range(self.nsamples):
                outs[j] = self._forward_layer(model, layer, inps[j].unsqueeze(0),
                                               attention_mask, position_ids)
            
            layers[i] = layer.cpu()
            torch.cuda.empty_cache()
            inps, outs = outs, inps
        
        model.config.use_cache = use_cache
        
        # 汇总
        if layer_results:
            total_params = sum(1 for _ in layer_results)
            avg_bits = sum(r["avg_bits"] for r in layer_results) / total_params
            logger.info(f"\n  全局平均 bit/权重: {avg_bits:.4f}")
    
    def _forward_layer(self, model, layer, inp, attention_mask, position_ids):
        """兼容不同层类型的 forward"""
        device = inp.device
        pos = position_ids.to(device) if position_ids is not None else \
              torch.arange(inp.shape[1], device=device).unsqueeze(0)
        try:
            if hasattr(model.model, 'rotary_emb'):
                position_embeddings = model.model.rotary_emb(inp, pos)
                return layer(inp, attention_mask=attention_mask,
                           position_ids=pos, position_embeddings=position_embeddings)[0]
        except TypeError:
            pass
        try:
            return layer(inp, attention_mask=attention_mask, position_ids=pos)[0]
        except TypeError:
            return layer(inp, attention_mask=attention_mask)[0]
    
    def _compute_rank_allocations(self, layer_stats) -> Dict[str, int]:
        """基于激活统计计算自适应 rank 分配"""
        if not layer_stats:
            return {}
        
        total_budget = len(layer_stats) * self.avg_rank
        
        # 基于激活熵加权分配
        entropies = {k: v["activation_entropy"] for k, v in layer_stats.items()}
        total_entropy = sum(entropies.values())
        
        if total_entropy <= 0:
            return {k: self.avg_rank for k in layer_stats}
        
        allocations = {}
        for layer_key, entropy in entropies.items():
            # 按熵比例分配，clamp 到 [min_rank, max_rank]
            raw_rank = int(total_budget * (entropy / total_entropy))
            rank = max(self.min_rank, min(self.max_rank, raw_rank))
            # 对齐到 32 的倍数
            rank = (rank // 32) * 32
            rank = max(self.min_rank, rank)
            allocations[layer_key] = rank
        
        return allocations
