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
        args.cali_trans = True
        args.add_diag = True
        args.lwc = False
        args.lac = False
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
            
            # 初始化
            utils.seed_everything(seed=args.seed)
            logger.info(f"\n加载模型: {self.model_name}")
            
            model, apply_flatquant_to_model = model_utils.get_model(args.model, args.hf_token)
            model.eval()
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                args.model, use_fast=False, use_auth_token=args.hf_token
            )
            
            # 加载校准数据
            logger.info(f"加载校准数据: {args.cali_dataset} ({args.nsamples} samples)")
            trainloader = data_utils.get_loaders(
                args, args.cali_dataset, nsamples=args.nsamples,
                seed=args.seed, model=args.model,
                seqlen=model.seqlen, eval_mode=False
            )
            
            # 应用 FlatQuant
            if args.quantize:
                logger.info(f"\n应用 FlatQuant 量化...")
                model = apply_flatquant_to_model(args, model)
                
                if args.cali_trans or args.add_diag or args.lwc or args.lac:
                    logger.info(f"执行校准训练...")
                    train_utils.cali_flat_quant(args, model, trainloader, utils.DEV, logger=logger)
                
                flat_utils.reparameterize_model(model)
                logger.info(f"FlatQuant 应用完成")
            
            # OBR 量化
            if args.w_bits < 16 and not args.load_qmodel_path:
                logger.info(f"\n执行 OBR 联合量化+稀疏化...")
                quantizers = obr_utils.obr_fwrd(model, trainloader, utils.DEV, args)
                logger.info(f"OBR 压缩完成")
            
            # 保存模型
            if args.save_qmodel_path:
                logger.info(f"\n保存量化模型到 {args.save_qmodel_path}")
                os.makedirs(os.path.dirname(args.save_qmodel_path), exist_ok=True)
                save_dict = model.state_dict()
                torch.save(save_dict, args.save_qmodel_path)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ OBR 压缩成功")
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
                "completion_time": datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"\n❌ OBR 压缩失败: {e}")
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
