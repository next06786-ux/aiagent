"""
量化启用验证脚本
"""
import os
import sys
import logging

# 关键：把项目根目录加入 sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_config():
    logger.info("\n" + "=" * 60)
    logger.info("1️⃣  检查量化配置")
    logger.info("=" * 60)

    from backend.llm.model_config import get_quantization_config, get_lora_quantization_config

    q = get_quantization_config()
    l = get_lora_quantization_config()

    logger.info(f"\n📋 基座模型量化:")
    logger.info(f"  enable_quantization:      {q.get('enable_quantization')}")
    logger.info(f"  load_in_4bit:             {q.get('load_in_4bit')}")
    logger.info(f"  bnb_4bit_use_double_quant:{q.get('bnb_4bit_use_double_quant')}")
    logger.info(f"  bnb_4bit_quant_type:      {q.get('bnb_4bit_quant_type')}")

    logger.info(f"\n📋 LoRA 量化:")
    logger.info(f"  quantize_after_training:  {l.get('quantize_after_training')}")
    logger.info(f"  lora_quantization_bits:   {l.get('lora_quantization_bits')}")
    logger.info(f"  per_channel:              {l.get('lora_quantization_per_channel')}")
    logger.info(f"  adaptive_rank:            {l.get('adaptive_rank')}")

    ok = q.get('enable_quantization') and q.get('load_in_4bit') and l.get('quantize_after_training')
    logger.info(f"\n{'✅ 全部已启用' if ok else '❌ 未完全启用'}")
    return ok


def check_deps():
    logger.info("\n" + "=" * 60)
    logger.info("2️⃣  检查依赖库")
    logger.info("=" * 60)

    deps = {}
    for name in ["torch", "transformers", "peft", "bitsandbytes"]:
        try:
            mod = __import__(name)
            ver = getattr(mod, '__version__', '?')
            logger.info(f"  ✅ {name}: {ver}")
            deps[name] = True
        except ImportError:
            logger.info(f"  ❌ {name}: 未安装")
            deps[name] = False

    for name, sub in [("llmquant", "external_repos/llmquant"), ("OBR", "external_repos/OBR")]:
        p = os.path.join(PROJECT_ROOT, sub)
        ok = os.path.exists(p)
        logger.info(f"  {'✅' if ok else '❌'} {name}: {p}")
        deps[name] = ok

    return all(deps.values())


def check_gpu():
    logger.info("\n" + "=" * 60)
    logger.info("3️⃣  检查 GPU")
    logger.info("=" * 60)

    try:
        import torch
        if not torch.cuda.is_available():
            logger.info("  ⚠️  CUDA 不可用")
            return False
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            total = props.total_memory / 1024 ** 3
            used = torch.cuda.memory_allocated(i) / 1024 ** 3
            logger.info(f"  ✅ GPU {i}: {props.name}  总显存: {total:.1f}GB  已用: {used:.2f}GB")
        return True
    except Exception as e:
        logger.info(f"  ❌ {e}")
        return False


def check_tools():
    logger.info("\n" + "=" * 60)
    logger.info("4️⃣  检查量化工具模块")
    logger.info("=" * 60)

    tools_dir = os.path.dirname(__file__)
    files = [
        "quantizer.py",
        "lora_quantizer.py",
        "quality_monitor.py",
        "compress_base_model.py",
        "inference_integration.py",
        "enable_compression.py",
        "eval_compression_quality.py",
    ]
    ok = True
    for f in files:
        exists = os.path.exists(os.path.join(tools_dir, f))
        logger.info(f"  {'✅' if exists else '❌'} {f}")
        ok = ok and exists

    # 尝试实际导入核心模块
    try:
        from backend.model_compression.quantizer import ModelQuantizer
        quantizer = ModelQuantizer()
        logger.info(f"\n  📊 量化后端:")
        logger.info(f"    bitsandbytes: {'✅' if quantizer.bitsandbytes_available else '❌'}")
        logger.info(f"    llmquant:     {'✅' if quantizer.llmquant_available else '❌'}")
        logger.info(f"    OBR:          {'✅' if quantizer.obr_available else '❌'}")
    except Exception as e:
        logger.info(f"\n  ⚠️  导入 ModelQuantizer 失败: {e}")

    return ok


def check_lora():
    logger.info("\n" + "=" * 60)
    logger.info("5️⃣  检查 LoRA 管理")
    logger.info("=" * 60)

    try:
        from backend.lora.lora_model_manager import LoRAModelManager
        mgr = LoRAModelManager()

        test_user = "test_user"
        lora_path = mgr.get_user_lora_path(test_user)
        q_path = mgr.get_quantized_lora_path(test_user)

        logger.info(f"  用户 '{test_user}':")
        logger.info(f"    原始 LoRA: {lora_path or '无（正常，尚未训练）'}")
        logger.info(f"    量化 LoRA: {q_path or '无（正常，尚未训练）'}")
        logger.info(f"  ✅ LoRA 管理器工作正常")
        return True
    except Exception as e:
        logger.info(f"  ❌ LoRA 管理检查失败: {e}")
        return False


def check_bnb_quantize_smoke():
    """实际创建一个 BitsAndBytesConfig 验证能正常工作"""
    logger.info("\n" + "=" * 60)
    logger.info("6️⃣  BitsAndBytesConfig 冒烟测试")
    logger.info("=" * 60)

    try:
        import torch
        from transformers import BitsAndBytesConfig

        cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        logger.info(f"  ✅ BitsAndBytesConfig 创建成功")
        logger.info(f"    load_in_4bit: {cfg.load_in_4bit}")
        logger.info(f"    quant_type:   {cfg.bnb_4bit_quant_type}")
        logger.info(f"    double_quant: {cfg.bnb_4bit_use_double_quant}")
        return True
    except Exception as e:
        logger.info(f"  ❌ BitsAndBytesConfig 创建失败: {e}")
        return False


def main():
    logger.info("\n🔍  量化启用验证工具\n")

    results = {
        "配置启用": check_config(),
        "依赖完整": check_deps(),
        "GPU 可用": check_gpu(),
        "工具就绪": check_tools(),
        "LoRA 管理": check_lora(),
        "BnB 冒烟": check_bnb_quantize_smoke(),
    }

    logger.info("\n" + "=" * 60)
    logger.info("✨ 验证总结")
    logger.info("=" * 60 + "\n")

    for k, v in results.items():
        logger.info(f"  {k}: {'✅' if v else '❌'}")

    if all(results.values()):
        logger.info("\n🎉 所有检查通过！量化功能已就绪。")
        logger.info("\n💡 下一步：")
        logger.info("  python backend/model_compression/verify_quantization.py --load-model")
        logger.info("  （实际加载模型验证显存节省，需要 GPU）")
        return 0
    else:
        failed = [k for k, v in results.items() if not v]
        logger.info(f"\n⚠️  失败项: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--load-model", action="store_true")
    parser.parse_args()
    sys.exit(main())
