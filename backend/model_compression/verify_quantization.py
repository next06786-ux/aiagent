"""
量化启用验证脚本
检查量化配置是否生效、依赖是否完整、推理是否正常
"""

import os
import sys
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def check_quantization_config():
    """检查量化配置是否启用"""
    logger.info("\n" + "="*60)
    logger.info("1️⃣  检查量化配置")
    logger.info("="*60)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from llm.model_config import get_quantization_config, get_lora_quantization_config
        
        quant_cfg = get_quantization_config()
        lora_cfg = get_lora_quantization_config()
        
        logger.info("\n📋 基座模型量化配置：")
        logger.info(f"  enable_quantization: {quant_cfg.get('enable_quantization')}")
        logger.info(f"  quantization_type: {quant_cfg.get('quantization_type')}")
        logger.info(f"  load_in_4bit: {quant_cfg.get('load_in_4bit')}")
        logger.info(f"  load_in_8bit: {quant_cfg.get('load_in_8bit')}")
        logger.info(f"  bnb_4bit_use_double_quant: {quant_cfg.get('bnb_4bit_use_double_quant')}")
        logger.info(f"  bnb_4bit_quant_type: {quant_cfg.get('bnb_4bit_quant_type')}")
        
        logger.info("\n📋 LoRA 量化配置：")
        logger.info(f"  quantize_after_training: {lora_cfg.get('quantize_after_training')}")
        logger.info(f"  lora_quantization_bits: {lora_cfg.get('lora_quantization_bits')}")
        logger.info(f"  lora_quantization_per_channel: {lora_cfg.get('lora_quantization_per_channel')}")
        logger.info(f"  adaptive_rank: {lora_cfg.get('adaptive_rank')}")
        
        # 检查启用状态
        is_enabled = quant_cfg.get('enable_quantization') and quant_cfg.get('load_in_4bit')
        lora_enabled = lora_cfg.get('quantize_after_training')
        
        if is_enabled:
            logger.info("\n✅ 基座模型量化已启用")
        else:
            logger.info("\n❌ 基座模型量化未启用")
        
        if lora_enabled:
            logger.info("✅ LoRA 量化已启用")
        else:
            logger.info("❌ LoRA 量化未启用")
        
        return is_enabled and lora_enabled
    
    except Exception as e:
        logger.error(f"❌ 检查配置失败: {e}")
        return False


def check_dependencies():
    """检查必要的依赖"""
    logger.info("\n" + "="*60)
    logger.info("2️⃣  检查依赖库")
    logger.info("="*60)
    
    dependencies = {
        "torch": None,
        "transformers": None,
        "peft": None,
        "bitsandbytes": None,
        "llmquant": "external",
        "OBR": "external"
    }
    
    results = {}
    
    for name, dep_type in dependencies.items():
        try:
            if dep_type == "external":
                # 检查外部库路径
                if name == "llmquant":
                    path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), '../../external_repos/llmquant')
                    )
                    exists = os.path.exists(path)
                    logger.info(f"  ✅ {name}: {path}" if exists else f"  ❌ {name}: 未找到")
                    results[name] = exists
                elif name == "OBR":
                    path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), '../../external_repos/OBR')
                    )
                    exists = os.path.exists(path)
                    logger.info(f"  ✅ {name}: {path}" if exists else f"  ❌ {name}: 未找到")
                    results[name] = exists
            else:
                # 检查 pip 安装的库
                __import__(name)
                import importlib
                mod = importlib.import_module(name)
                version = getattr(mod, '__version__', 'unknown')
                logger.info(f"  ✅ {name}: {version}")
                results[name] = True
        
        except ImportError:
            logger.warning(f"  ⚠️  {name}: 未安装")
            results[name] = False
        except Exception as e:
            logger.error(f"  ❌ {name}: {e}")
            results[name] = False
    
    all_ok = all(results.values())
    
    if all_ok:
        logger.info("\n✅ 所有依赖都可用")
    else:
        missing = [k for k, v in results.items() if not v]
        logger.info(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        logger.info("\n📦 安装缺失的依赖：")
        if "bitsandbytes" in missing:
            logger.info("  pip install bitsandbytes")
        if "llmquant" in missing:
            logger.info("  git clone https://github.com/...llmquant external_repos/llmquant")
        if "OBR" in missing:
            logger.info("  git clone https://github.com/csguoh/OBR external_repos/OBR")
    
    return results


def check_gpu_and_memory():
    """检查 GPU 和显存"""
    logger.info("\n" + "="*60)
    logger.info("3️⃣  检查 GPU 和显存")
    logger.info("="*60)
    
    try:
        import torch
        
        cuda_available = torch.cuda.is_available()
        if not cuda_available:
            logger.warning("⚠️  CUDA 不可用，量化推理将在 CPU 上运行（速度会很慢）")
            return False
        
        device_count = torch.cuda.device_count()
        logger.info(f"\n✅ CUDA 可用")
        logger.info(f"  GPU 数量: {device_count}")
        
        for i in range(device_count):
            props = torch.cuda.get_device_properties(i)
            total_mem = props.total_memory / (1024 ** 3)
            
            # 获取当前显存使用
            torch.cuda.reset_peak_memory_stats(i)
            allocated = torch.cuda.memory_allocated(i) / (1024 ** 3)
            reserved = torch.cuda.memory_reserved(i) / (1024 ** 3)
            
            logger.info(f"\n  GPU {i}: {props.name}")
            logger.info(f"    总显存: {total_mem:.1f} GB")
            logger.info(f"    已用: {allocated:.2f} GB")
            logger.info(f"    保留: {reserved:.2f} GB")
            logger.info(f"    可用: {total_mem - reserved:.2f} GB")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 检查 GPU 失败: {e}")
        return False


def test_model_loading():
    """测试模型加载（会占用显存）"""
    logger.info("\n" + "="*60)
    logger.info("4️⃣  测试模型加载")
    logger.info("="*60)
    
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from backend.llm.model_config import get_model_hf_name, get_quantization_config
        
        model_name = get_model_hf_name()
        quant_config = get_quantization_config()
        
        logger.info(f"\n📥 尝试加载模型: {model_name}")
        
        if not torch.cuda.is_available():
            logger.warning("⚠️  GPU 不可用，跳过加载测试")
            return False
        
        # 检查显存
        available_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        required_gb = 5 if quant_config.get('load_in_4bit') else 20
        
        if available_gb < required_gb:
            logger.warning(f"⚠️  显存不足: {available_gb:.1f} GB < {required_gb} GB")
            logger.info("  跳过实际加载测试（避免 OOM）")
            return False
        
        logger.info("  加载配置...")
        
        from transformers import BitsAndBytesConfig
        
        if quant_config.get('load_in_4bit'):
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            logger.info("  ✓ BitsAndBytesConfig 已创建")
            logger.info("  ✓ 4-bit 量化已配置")
        else:
            bnb_config = None
            logger.info("  ℹ️  将使用 FP16 加载")
        
        logger.info("  加载模型...")
        logger.info("  ⏳ 这可能需要 30-60 秒...")
        
        # 实际加载（可能会很慢）
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config if quant_config.get('load_in_4bit') else None,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=None if quant_config.get('load_in_4bit') else torch.float16,
            timeout=120
        )
        
        logger.info("  ✅ 模型加载成功！")
        
        # 检查显存使用
        vram_used = torch.cuda.memory_allocated() / (1024 ** 3)
        logger.info(f"\n  显存使用: {vram_used:.2f} GB")
        
        if quant_config.get('load_in_4bit'):
            if vram_used < 10:
                logger.info("  ✅ 4-bit 量化生效（显存 < 10 GB）")
                return True
            else:
                logger.warning("  ⚠️  量化可能未生效（显存过高）")
                return False
        else:
            logger.info(f"  ℹ️  FP16 加载，显存约 {vram_used:.1f} GB")
            return True
    
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quantized_lora_loading():
    """测试量化 LoRA 加载"""
    logger.info("\n" + "="*60)
    logger.info("5️⃣  测试量化 LoRA 加载")
    logger.info("="*60)
    
    try:
        from backend.lora.lora_model_manager import lora_manager
        
        test_user = "test_user_verification"
        
        logger.info(f"\n📥 检查用户 '{test_user}' 的 LoRA 模型...")
        
        lora_path = lora_manager.get_user_lora_path(test_user)
        quantized_path = lora_manager.get_quantized_lora_path(test_user)
        
        if not lora_path and not quantized_path:
            logger.info("ℹ️  该用户还没有训练 LoRA（这是正常的）")
            logger.info("  之后训练 LoRA 时会自动量化")
            return True
        
        if quantized_path:
            logger.info(f"✅ 找到量化 LoRA: {quantized_path}")
            return True
        elif lora_path:
            logger.info(f"ℹ️  找到原始 LoRA: {lora_path}")
            logger.info("  下次训练时会量化")
            return True
        else:
            logger.info("❌ LoRA 模型不完整")
            return False
    
    except Exception as e:
        logger.error(f"⚠️  检查 LoRA 失败: {e}")
        return False


def test_quantization_tools():
    """测试量化工具"""
    logger.info("\n" + "="*60)
    logger.info("6️⃣  测试量化工具")
    logger.info("="*60)
    
    try:
        from backend.model_compression.quantizer import ModelQuantizer, QuantizationMethod
        from backend.model_compression.lora_quantizer import LoRAQuantizer
        from backend.model_compression.quality_monitor import CompressionQualityMonitor
        
        logger.info("\n✅ LoRAQuantizer: 可用")
        logger.info("✅ ModelQuantizer: 可用")
        logger.info("✅ CompressionQualityMonitor: 可用")
        
        # 检查后端
        quantizer = ModelQuantizer()
        logger.info("\n📊 量化后端状态：")
        logger.info(f"  bitsandbytes: {'✅' if quantizer.bitsandbytes_available else '❌'}")
        logger.info(f"  llmquant: {'✅' if quantizer.llmquant_available else '❌'}")
        logger.info(f"  OBR: {'✅' if quantizer.obr_available else '❌'}")
        
        return quantizer.bitsandbytes_available
    
    except Exception as e:
        logger.error(f"❌ 量化工具检查失败: {e}")
        return False


def generate_verification_report():
    """生成完整验证报告"""
    logger.info("\n" + "="*60)
    logger.info("📊 验证报告")
    logger.info("="*60)
    
    results = {
        "config": check_quantization_config(),
        "dependencies": check_dependencies(),
        "gpu": check_gpu_and_memory(),
        "tools": test_quantization_tools(),
        "lora": test_quantized_lora_loading(),
    }
    
    logger.info("\n" + "="*60)
    logger.info("✨ 验证总结")
    logger.info("="*60)
    
    config_ok = results["config"]
    deps_ok = all(results["dependencies"].values())
    gpu_ok = results["gpu"]
    tools_ok = results["tools"]
    lora_ok = results["lora"]
    
    logger.info(f"\n配置启用: {'✅' if config_ok else '❌'}")
    logger.info(f"依赖完整: {'✅' if deps_ok else '⚠️'}")
    logger.info(f"GPU 可用: {'✅' if gpu_ok else '⚠️'}")
    logger.info(f"工具就绪: {'✅' if tools_ok else '❌'}")
    logger.info(f"LoRA 管理: {'✅' if lora_ok else '❌'}")
    
    all_ok = config_ok and deps_ok and gpu_ok and tools_ok
    
    if all_ok:
        logger.info("\n" + "🎉 "*20)
        logger.info("所有检查通过！量化已成功启用，可以开始使用了！")
        logger.info("🎉 "*20)
        return 0
    else:
        logger.info("\n⚠️  部分检查失败，请查看上方的错误信息")
        return 1


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="量化启用验证工具")
    parser.add_argument("--load-model", action="store_true", help="实际加载模型（会占用显存）")
    parser.add_argument("--quick", action="store_true", help="快速检查（跳过模型加载）")
    
    args = parser.parse_args()
    
    logger.info("\n" + "🔍 "*20)
    logger.info("量化启用验证工具")
    logger.info("🔍 "*20)
    
    # 基础检查
    check_quantization_config()
    check_dependencies()
    check_gpu_and_memory()
    test_quantization_tools()
    test_quantized_lora_loading()
    
    # 模型加载测试
    if args.load_model and not args.quick:
        test_model_loading()
    elif not args.quick:
        logger.info("\n" + "="*60)
        logger.info("💡 建议")
        logger.info("="*60)
        logger.info("\n要测试实际的模型加载，运行：")
        logger.info("  python verify_quantization.py --load-model")
        logger.info("\n⚠️  注意：模型加载会占用大量显存，需要 GPU 可用")
    
    # 生成报告
    return generate_verification_report()


if __name__ == "__main__":
    sys.exit(main())
