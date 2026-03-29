"""
OBR FlatQuant 包装器
提供简化的 API 用于基座模型深度压缩
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


def _unwrap_flatquant(model):
    """
    拆除 FlatQuant 包装，还原原始模型结构。
    变换矩阵已在 reparameterize 时融合进权重，
    拆包后权重值保留融合效果，但模型结构恢复为原始的 nn.Linear。
    
    这样 obr_fwrd 面对的是干净的原始模型结构，
    不会有 FlatQuantizedLinear 的 forward 路径干扰。
    """
    import torch.nn as nn
    
    for idx in range(model.config.num_hidden_layers):
        layer = model.model.layers[idx]
        
        # 处理注意力层
        if hasattr(layer, 'linear_attn'):
            attn = layer.linear_attn
            # GatedDeltaNet: 拆分的 q/k/v_proj 需要合并回 in_proj_qkv
            if hasattr(attn, 'q_proj') and hasattr(attn.q_proj, 'linear'):
                import torch
                q_w = attn.q_proj.linear.weight.data
                k_w = attn.k_proj.linear.weight.data
                v_w = attn.v_proj.linear.weight.data
                merged_w = torch.cat([q_w, k_w, v_w], dim=0)
                
                # 创建新的 in_proj_qkv
                new_qkv = nn.Linear(merged_w.shape[1], merged_w.shape[0], bias=False)
                new_qkv.weight = nn.Parameter(merged_w)
                
                # 还原到原始结构
                # 删除拆分的 proj，恢复 in_proj_qkv
                if hasattr(attn, '_module'):
                    # 包装类模式
                    attn._module.in_proj_qkv = new_qkv
                else:
                    attn.in_proj_qkv = new_qkv
                
                # 还原其他 Linear 层
                for name in ['in_proj_z', 'in_proj_b', 'in_proj_a', 'out_proj']:
                    fql = getattr(attn, name, None)
                    if fql is not None and hasattr(fql, 'linear'):
                        if hasattr(attn, '_module'):
                            setattr(attn._module, name, fql.linear)
                        else:
                            setattr(attn, name, fql.linear)
                
                # 用原始模块替换包装类
                if hasattr(attn, '_module'):
                    # 保留非 Linear 组件已经在 _module 上
                    layer.linear_attn = attn._module
                    # 确保 in_proj_qkv 是合并后的
                    layer.linear_attn.in_proj_qkv = new_qkv
        
        elif hasattr(layer, 'self_attn'):
            attn = layer.self_attn
            if hasattr(attn, '_module'):
                # FlatQuantQwen3_5StdAttention: 委托模式
                # 把 FlatQuantizedLinear 的 linear 还原到 _module
                for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
                    fql = getattr(attn, name, None)
                    if fql is not None and hasattr(fql, 'linear'):
                        setattr(attn._module, name, fql.linear)
                layer.self_attn = attn._module
        
        # 处理 MLP 层
        mlp = layer.mlp
        if hasattr(mlp, 'up_proj') and hasattr(mlp.up_proj, 'linear'):
            for name in ['up_proj', 'gate_proj', 'down_proj']:
                fql = getattr(mlp, name, None)
                if fql is not None and hasattr(fql, 'linear'):
                    setattr(layer.mlp, name, fql.linear)
            # FlatQuantQwen3MLP 需要还原 act_fn 和 hidden_size
            if hasattr(mlp, 'act_fn') and not hasattr(layer.mlp, 'act_fn'):
                layer.mlp.act_fn = mlp.act_fn
            if hasattr(mlp, 'hidden_size') and not hasattr(layer.mlp, 'hidden_size'):
                layer.mlp.hidden_size = mlp.hidden_size
            if hasattr(mlp, 'intermediate_size') and not hasattr(layer.mlp, 'intermediate_size'):
                layer.mlp.intermediate_size = mlp.intermediate_size
    
    logger.info(f"  拆包完成: {model.config.num_hidden_layers} 层")
    return model


class OBRCompressor:
    """OBR FlatQuant 压缩器包装"""
    
    def __init__(
        self,
        model_name: str,
        output_dir: str,
        w_bits: int = 4,
        a_bits: int = 16,
        k_bits: int = 4,
        v_bits: int = 4,
        sparsity_ratio: float = 0.5,
        nsamples: int = 128,
        cali_dataset: str = "wikitext2",
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        self.w_bits = w_bits
        self.a_bits = a_bits
        self.k_bits = k_bits
        self.v_bits = v_bits
        self.sparsity_ratio = sparsity_ratio
        self.nsamples = nsamples
        self.cali_dataset = cali_dataset
        
        os.makedirs(output_dir, exist_ok=True)
    
    def _build_obr_args(self) -> argparse.Namespace:
        """构建 OBR 所需的参数对象"""
        args = argparse.Namespace()
        
        # 基本参数
        args.model = self.model_name
        args.seed = 0
        args.hf_token = None
        
        # 量化参数
        args.w_bits = self.w_bits
        args.a_bits = self.a_bits
        args.q_bits = 16
        args.k_bits = self.k_bits
        args.v_bits = self.v_bits
        
        args.w_asym = True
        args.a_asym = False
        args.k_asym = True
        args.v_asym = True
        
        args.w_groupsize = -1
        args.a_groupsize = -1
        args.q_groupsize = -1
        args.k_groupsize = 128
        args.v_groupsize = 128
        
        # 稀疏化参数
        args.sparsity_ratio = self.sparsity_ratio
        args.prune_n = 0
        args.prune_m = 0
        
        # OBR 特定参数
        args.obr_alpha = 0.5
        args.obr_rtn = False
        args.percdamp = 0.01
        args.act_order = False
        args.gptq_mse = False
        
        # 校准参数
        args.cali_dataset = self.cali_dataset
        args.nsamples = self.nsamples
        args.cali_bsz = 4
        args.epochs = 15
        
        # FlatQuant 参数
        args.flat_lr = 1e-5
        args.cali_trans = True      # ✅ 启用校准变换学习
        args.add_diag = True         # ✅ 启用 per-channel 缩放
        args.lwc = False             # 可选：learnable weight clipping
        args.lac = False             # 可选：learnable activation clipping
        args.resume = False
        args.save_matrix = False
        args.reload_matrix = False
        args.matrix_path = None
        args.diag_init = "sq_style"
        args.diag_alpha = 0.3
        args.warmup = False
        args.deactive_amp = False
        args.direct_inv = False
        args.separate_vtrans = False
        
        # ✅ 激活量化参数
        if args.a_bits < 16:
            args.a_asym = False     # 激活量化为对称量化
            args.a_groupsize = -1   # 全局量化
        
        # ✅ KV cache 量化参数  
        args.q_asym = False         # Query 对称量化
        args.q_groupsize = -1
        args.k_asym = True          # Key 非对称量化
        args.k_groupsize = 128      # Key per-group 量化
        args.v_asym = True          # Value 非对称量化
        args.v_groupsize = 128      # Value per-group 量化
        
        # 输出参数
        args.output_dir = self.output_dir
        args.exp_name = "compression"
        args.load_qmodel_path = ""
        args.save_qmodel_path = os.path.join(self.output_dir, "quantized_model.pt")
        
        # 评估参数
        args.ppl_eval = True
        args.lm_eval = False
        args.tasks = ["piqa", "hellaswag", "arc_easy", "arc_challenge"]
        args.lm_eval_batch_size = 128
        args.distribute_model = False
        
        # 自动设置 quantize 标志
        args.quantize = (args.w_bits < 16) or (args.a_bits < 16) or (args.q_bits < 16) or (args.k_bits < 16) or (args.v_bits < 16)
        
        # 缓存和输出路径
        args.cache_dir = os.path.join(args.output_dir, ".cache")
        os.makedirs(args.cache_dir, exist_ok=True)
        
        args.model_name = args.model.split("/")[-1]
        args.exp_dir = os.path.join(args.output_dir, args.model_name, f"w{args.w_bits}a{args.a_bits}", args.exp_name)
        os.makedirs(args.exp_dir, exist_ok=True)
        
        return args
    
    def compress(self) -> Dict[str, Any]:
        """执行 OBR 压缩"""
        import time as _time
        _start_time = _time.time()
        
        def _elapsed():
            return f"[{_time.time() - _start_time:.0f}s]"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始 OBR FlatQuant 压缩")
        logger.info(f"{'='*60}")
        logger.info(f"  模型: {self.model_name}")
        logger.info(f"  量化: W{self.w_bits}A{self.a_bits}K{self.k_bits}V{self.v_bits}")
        logger.info(f"  稀疏度: {self.sparsity_ratio*100:.0f}%")
        logger.info(f"  校准数据: {self.nsamples} samples from {self.cali_dataset}")
        
        try:
            # 检查 OBR 是否存在
            obr_path = os.path.join(os.getcwd(), "external_repos", "OBR", "FlatQuant")
            if not os.path.exists(obr_path):
                raise FileNotFoundError(f"OBR FlatQuant 不存在: {obr_path}")
            
            # 添加到 sys.path
            if obr_path not in sys.path:
                sys.path.insert(0, obr_path)
                sys.path.insert(0, os.path.join(os.path.dirname(obr_path), "FlatQuant"))
            
            # 导入 OBR 模块
            from flatquant import utils, model_utils, data_utils, train_utils, flat_utils
            from flatquant import obr_utils
            import torch
            import transformers
            
            # 构建参数
            args = self._build_obr_args()
            logger.info(f"\nOBR 参数配置:")
            logger.info(f"  weight_bits: {args.w_bits}")
            logger.info(f"  activation_bits: {args.a_bits}")
            logger.info(f"  kv_cache_bits: K{args.k_bits}V{args.v_bits}")
            logger.info(f"  sparsity: {args.sparsity_ratio}")
            
            # ========== 阶段 1: 加载模型 ==========
            utils.seed_everything(seed=args.seed)
            logger.info(f"\n{_elapsed()} [1/6] 加载模型: {self.model_name}")
            
            model, apply_flatquant_to_model = model_utils.get_model(args.model, None)
            model.eval()
            
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                args.model, use_fast=False, trust_remote_code=True
            )
            logger.info(f"{_elapsed()} [1/6] 模型加载完成 ✓")
            
            # ========== 阶段 2: 加载校准数据 ==========
            logger.info(f"\n{_elapsed()} [2/6] 加载校准数据: {args.cali_dataset} ({args.nsamples} samples)")
            trainloader = data_utils.get_loaders(
                args, args.cali_dataset, nsamples=args.nsamples,
                seed=args.seed, model=args.model,
                seqlen=model.seqlen, eval_mode=False
            )
            logger.info(f"{_elapsed()} [2/6] 校准数据加载完成 ✓")
            
            # ========== 阶段 3: 应用 FlatQuant 包装 ==========
            if args.quantize:
                logger.info(f"\n{_elapsed()} [3/6] 应用 FlatQuant 量化包装...")
                model = apply_flatquant_to_model(args, model)
                logger.info(f"{_elapsed()} [3/6] FlatQuant 包装完成 ✓")
            
            # ========== 阶段 4: 校准训练 ==========
            if args.cali_trans or args.add_diag or args.lwc or args.lac:
                # 检查是否有已保存的校准参数可以恢复
                flat_params_path = os.path.join(args.exp_dir, "flat_parameters.pth")
                if os.path.exists(flat_params_path):
                    logger.info(f"\n{_elapsed()} [4/6] 发现已保存的校准参数: {flat_params_path}")
                    logger.info(f"  跳过校准训练，直接加载参数...")
                    flat_utils.load_flat_parameters(args, model, path=args.exp_dir)
                    logger.info(f"{_elapsed()} [4/6] 校准参数加载完成 ✓")
                else:
                    num_layers = model.config.num_hidden_layers
                    logger.info(f"\n{_elapsed()} [4/6] 执行 FlatQuant 校准训练 ({num_layers} 层 × {args.epochs} epochs)...")
                    logger.info(f"  cali_trans={args.cali_trans}, add_diag={args.add_diag}, lwc={args.lwc}, lac={args.lac}")
                    logger.info(f"  预计耗时: ~{num_layers * args.epochs * 7 / 60:.0f} 分钟")
                    train_utils.cali_flat_quant(args, model, trainloader, utils.DEV, logger=logger)
                    logger.info(f"{_elapsed()} [4/6] 校准训练完成 ✓")
            
            # ========== 阶段 5: 重参数化 + OBR 量化 ==========
            if args.quantize:
                logger.info(f"\n{_elapsed()} [5/6] 执行模型重参数化...")
                flat_utils.reparameterize_model(model)
                logger.info(f"{_elapsed()} [5/6] 重参数化完成 ✓")
            
            if args.w_bits < 16 and not args.load_qmodel_path:
                logger.info(f"\n{_elapsed()} [5/6] 执行 OBR 联合量化+稀疏化...")
                logger.info(f"  W{args.w_bits}-bit + {args.sparsity_ratio*100:.0f}% 稀疏 (GPTQ + WANDA + Hessian)")
                
                quantizers = obr_utils.obr_fwrd(model, trainloader, utils.DEV, args)
                logger.info(f"{_elapsed()} [5/6] OBR 量化+稀疏化完成 ✓")
            
            # ========== 阶段 6: 保存模型 ==========
            if args.save_qmodel_path:
                logger.info(f"\n{_elapsed()} [6/6] 保存量化模型到 {args.save_qmodel_path}")
                os.makedirs(os.path.dirname(args.save_qmodel_path), exist_ok=True)
                save_dict = model.state_dict()
                torch.save(save_dict, args.save_qmodel_path)
                
                # 计算文件大小
                file_size_gb = os.path.getsize(args.save_qmodel_path) / (1024**3)
                logger.info(f"{_elapsed()} [6/6] 模型已保存 ({file_size_gb:.2f} GB) ✓")
            
            total_time = _time.time() - _start_time
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ OBR 压缩成功 (总耗时: {total_time/60:.1f} 分钟)")
            logger.info(f"{'='*60}")
            
            return {
                "status": "success",
                "method": "OBR_FlatQuant",
                "model_name": self.model_name,
                "w_bits": self.w_bits,
                "a_bits": self.a_bits,
                "kv_bits": f"K{self.k_bits}V{self.v_bits}",
                "sparsity": self.sparsity_ratio,
                "output_path": self.output_dir,
                "config_path": args.exp_dir,
                "total_time_minutes": round(total_time / 60, 1),
                "completion_time": datetime.now().isoformat(),
            }
        
        except Exception as e:
            elapsed = _time.time() - _start_time
            logger.error(f"\n❌ OBR 压缩失败 (在 {elapsed:.0f}s 时): {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e),
                "output_dir": self.output_dir
            }


def main():
    parser = argparse.ArgumentParser(description="OBR FlatQuant 压缩工具")
    parser.add_argument("--model", type=str, required=True, help="模型路径或名称")
    parser.add_argument("--output", type=str, default="models/qwen-obr", help="输出目录")
    parser.add_argument("--w-bits", type=int, default=4, help="权重量化位数")
    parser.add_argument("--sparsity", type=float, default=0.5, help="稀疏度")
    parser.add_argument("--nsamples", type=int, default=128, help="校准样本数")
    parser.add_argument("--dataset", type=str, default="wikitext2", help="校准数据集")
    
    args = parser.parse_args()
    
    compressor = OBRCompressor(
        model_name=args.model,
        output_dir=args.output,
        w_bits=args.w_bits,
        sparsity_ratio=args.sparsity,
        nsamples=args.nsamples,
        cali_dataset=args.dataset,
    )
    
    result = compressor.compress()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
