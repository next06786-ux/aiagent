"""
基座模型压缩集成脚本
使用 OBR FlatQuant 方案对 Qwen3.5-9B 执行离线 W4A4KV4 + 50% 稀疏量化

执行方式:
python backend/model_compression/compress_base_model.py \
  --model /root/autodl-tmp/models/base/Qwen3.5-9B \
  --output models/qwen-obr \
  --w-bits 4 \
  --sparsity 0.5 \
  --nsamples 128
"""

import os
import sys
import json
import logging
import argparse

# 添加项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.model_compression.obr_wrapper import OBRCompressor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


def main():
    parser = argparse.ArgumentParser(description="LifeSwarm 基座模型 OBR FlatQuant 压缩")
    parser.add_argument("--model", type=str, required=True, help="模型路径或 HuggingFace 模型名称")
    parser.add_argument("--output", type=str, default="models/qwen-obr", help="输出目录")
    parser.add_argument("--w-bits", type=int, default=4, help="权重量化位数")
    parser.add_argument("--a-bits", type=int, default=16, help="激活量化位数")
    parser.add_argument("--k-bits", type=int, default=4, help="KV cache Key 量化位数")
    parser.add_argument("--v-bits", type=int, default=4, help="KV cache Value 量化位数")
    parser.add_argument("--sparsity", type=float, default=0.5, help="权重稀疏度")
    parser.add_argument("--nsamples", type=int, default=128, help="校准数据样本数")
    parser.add_argument("--dataset", type=str, default="wikitext2", help="校准数据集")
    
    args = parser.parse_args()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"LifeSwarm 基座模型 OBR FlatQuant 压缩")
    logger.info(f"{'='*60}\n")
    
    compressor = OBRCompressor(
        model_name=args.model,
        output_dir=args.output,
        w_bits=args.w_bits,
        a_bits=args.a_bits,
        k_bits=args.k_bits,
        v_bits=args.v_bits,
        sparsity_ratio=args.sparsity,
        nsamples=args.nsamples,
        cali_dataset=args.dataset,
    )
    
    result = compressor.compress()
    logger.info(f"\n结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
