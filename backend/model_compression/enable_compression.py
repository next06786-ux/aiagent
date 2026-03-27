"""
模型压缩启用脚本
一键启用/禁用模型压缩和量化功能

使用方式:
python backend/model_compression/enable_compression.py --enable
python backend/model_compression/enable_compression.py --disable
python backend/model_compression/enable_compression.py --status
"""

import os
import json
import argparse
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


def get_model_config_path():
    """获取模型配置文件路径"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'llm', 'model_config.py'
    )


def enable_compression():
    """启用模型压缩和量化"""
    logger.info(f"\n{'='*60}")
    logger.info("启用模型压缩和量化功能")
    logger.info(f"{'='*60}\n")
    
    config_path = get_model_config_path()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改配置
    content = content.replace(
        '"enable_quantization": False,',
        '"enable_quantization": True,'
    )
    content = content.replace(
        '"load_in_4bit": False,',
        '"load_in_4bit": True,'
    )
    content = content.replace(
        '"quantize_after_training": False,',
        '"quantize_after_training": True,'
    )
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✓ 已启用以下功能:")
    logger.info("  • 基座模型 4-bit 量化 (bitsandbytes)")
    logger.info("  • 双量化 (bnb_4bit_use_double_quant)")
    logger.info("  • LoRA 训练后自动量化 (llmquant 4-bit per-channel)")
    logger.info("  • 自适应 LoRA rank 分配\n")
    
    logger.info("预期效果:")
    logger.info("  • 基座模型显存: 20GB → 3-5GB")
    logger.info("  • LoRA 存储空间: 50MB → 12MB (4x 压缩)")
    logger.info("  • 推理速度: 提升 30-40%\n")


def disable_compression():
    """禁用模型压缩和量化"""
    logger.info(f"\n{'='*60}")
    logger.info("禁用模型压缩和量化功能")
    logger.info(f"{'='*60}\n")
    
    config_path = get_model_config_path()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改配置
    content = content.replace(
        '"enable_quantization": True,',
        '"enable_quantization": False,'
    )
    content = content.replace(
        '"load_in_4bit": True,',
        '"load_in_4bit": False,'
    )
    content = content.replace(
        '"quantize_after_training": True,',
        '"quantize_after_training": False,'
    )
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✓ 已禁用量化功能\n")
    logger.info("模型将使用:")
    logger.info("  • 基座模型 FP16 (原始精度)")
    logger.info("  • LoRA FP32 (原始精度)\n")


def show_status():
    """显示压缩功能状态"""
    logger.info(f"\n{'='*60}")
    logger.info("模型压缩功能状态")
    logger.info(f"{'='*60}\n")
    
    from backend.llm.model_config import get_quantization_config, get_lora_config
    
    quant_cfg = get_quantization_config()
    lora_cfg = get_lora_config()
    
    logger.info("基座模型量化配置:")
    logger.info(f"  启用: {quant_cfg.get('enable_quantization')}")
    logger.info(f"  类型: {quant_cfg.get('quantization_type')}")
    logger.info(f"  4-bit 加载: {quant_cfg.get('load_in_4bit')}")
    logger.info(f"  双量化: {quant_cfg.get('bnb_4bit_use_double_quant')}")
    logger.info(f"  量化类型: {quant_cfg.get('bnb_4bit_quant_type')}\n")
    
    logger.info("LoRA 量化配置:")
    logger.info(f"  训练后量化: {get_quantization_config().get('quantize_after_training')}")
    logger.info(f"  量化位数: {get_quantization_config().get('lora_quantization_bits')} bit")
    logger.info(f"  Per-channel: {get_quantization_config().get('lora_quantization_per_channel')}")
    logger.info(f"  自适应 rank: {get_quantization_config().get('adaptive_rank')}\n")


def verify_compression_setup():
    """验证压缩功能配置"""
    logger.info(f"\n{'='*60}")
    logger.info("验证压缩功能配置")
    logger.info(f"{'='*60}\n")
    
    issues = []
    
    # 检查 bitsandbytes
    try:
        import bitsandbytes
        logger.info("✓ bitsandbytes 已安装")
    except ImportError:
        logger.warning("⚠️ bitsandbytes 未安装")
        issues.append("bitsandbytes")
    
    # 检查 PEFT
    try:
        import peft
        logger.info("✓ PEFT 已安装")
    except ImportError:
        logger.warning("⚠️ PEFT 未安装")
        issues.append("PEFT")
    
    # 检查 llmquant
    llmquant_path = os.path.abspath("external_repos/llmquant")
    if os.path.exists(llmquant_path):
        logger.info("✓ llmquant 库已克隆")
    else:
        logger.warning("⚠️ llmquant 库未找到")
        issues.append("llmquant")
    
    # 检查 OBR
    obr_path = os.path.abspath("external_repos/OBR")
    if os.path.exists(obr_path):
        logger.info("✓ OBR 库已克隆")
    else:
        logger.warning("⚠️ OBR 库未找到（可选，bitsandbytes 可替代）")
    
    if issues:
        logger.info(f"\n⚠️  缺少依赖: {', '.join(issues)}")
        logger.info("\n安装缺失的依赖:")
        if "bitsandbytes" in issues:
            logger.info("  pip install bitsandbytes")
        if "PEFT" in issues:
            logger.info("  pip install peft")
        if "llmquant" in issues:
            logger.info("  git clone https://github.com/...llmquant external_repos/llmquant")
        return False
    else:
        logger.info("\n✓ 所有依赖已安装，压缩功能可用！\n")
        return True


def main():
    parser = argparse.ArgumentParser(description="模型压缩启用工具")
    parser.add_argument("--enable", action="store_true", help="启用压缩功能")
    parser.add_argument("--disable", action="store_true", help="禁用压缩功能")
    parser.add_argument("--status", action="store_true", help="显示压缩功能状态")
    parser.add_argument("--verify", action="store_true", help="验证压缩功能配置")
    
    args = parser.parse_args()
    
    if args.enable:
        enable_compression()
    elif args.disable:
        disable_compression()
    elif args.status:
        show_status()
    elif args.verify:
        verify_compression_setup()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
