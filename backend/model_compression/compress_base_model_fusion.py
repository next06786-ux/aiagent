"""
OBR + llmquant 融合压缩入口脚本

使用方式:
HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python backend/model_compression/compress_base_model_fusion.py \
  --model /root/autodl-tmp/models/base/Qwen3.5-9B \
  --output models/qwen-fusion \
  --nsamples 128 \
  --svd-rank 256 \
  --adaptive-rank \
  --quant-method 4bit
"""

import os
import sys
import json
import logging
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.model_compression.fusion_compressor import FusionCompressor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


def main():
    parser = argparse.ArgumentParser(description="OBR + llmquant 融合压缩")
    # 模型参数
    parser.add_argument("--model", type=str, required=True, help="模型路径")
    parser.add_argument("--output", type=str, default="models/qwen-fusion", help="输出目录")
    # FlatQuant 参数
    parser.add_argument("--w-bits", type=int, default=4, help="权重量化位数")
    parser.add_argument("--a-bits", type=int, default=16, help="激活量化位数")
    parser.add_argument("--k-bits", type=int, default=4, help="Key 量化位数")
    parser.add_argument("--v-bits", type=int, default=4, help="Value 量化位数")
    parser.add_argument("--nsamples", type=int, default=128, help="校准样本数")
    parser.add_argument("--dataset", type=str, default="wikitext2", help="校准数据集")
    parser.add_argument("--flatquant-epochs", type=int, default=15, help="FlatQuant 校准 epochs")
    # llmquant 参数
    parser.add_argument("--svd-rank", type=int, default=256, help="SVD rank")
    parser.add_argument("--adaptive-rank", action="store_true", help="启用自适应 rank")
    parser.add_argument("--avg-rank", type=int, default=256, help="平均 rank 预算")
    parser.add_argument("--min-rank", type=int, default=128, help="最小 rank")
    parser.add_argument("--max-rank", type=int, default=512, help="最大 rank")
    parser.add_argument("--quant-method", type=str, default="4bit", help="残差量化方法")
    parser.add_argument("--blocksize", type=int, default=128, help="GPTQ block 大小")
    parser.add_argument("--no-row-prune", action="store_true", help="禁用行剪枝")
    parser.add_argument("--no-obr-twogroup", action="store_true", help="禁用 OBR 两组残差")
    
    args = parser.parse_args()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"OBR + llmquant 融合压缩")
    logger.info(f"{'='*60}\n")
    
    compressor = FusionCompressor(
        model_name=args.model,
        output_dir=args.output,
        w_bits=args.w_bits,
        a_bits=args.a_bits,
        k_bits=args.k_bits,
        v_bits=args.v_bits,
        nsamples=args.nsamples,
        cali_dataset=args.dataset,
        flatquant_epochs=args.flatquant_epochs,
        svd_rank=args.svd_rank,
        adaptive_rank=args.adaptive_rank,
        avg_rank=args.avg_rank,
        min_rank=args.min_rank,
        max_rank=args.max_rank,
        quant_method=args.quant_method,
        blocksize=args.blocksize,
        row_prune_enable=not args.no_row_prune,
        obr_twogroup_enable=not args.no_obr_twogroup,
    )
    
    result = compressor.compress()
    logger.info(f"\n结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
