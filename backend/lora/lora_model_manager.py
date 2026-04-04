"""
LoRA 模型管理器
负责加载和使用用户的 LoRA 模型
"""
import os
from typing import Optional
import sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.model_config import get_model_hf_name


class LoRAModelManager:
    """LoRA 模型管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.base_model = None
        self.tokenizer = None
        self.loaded_loras = {}  # {user_id: model}
        local_base_model_path = os.environ.get("LOCAL_BASE_MODEL_PATH")
        self.base_model_name = local_base_model_path if local_base_model_path else "/root/autodl-tmp/models/base/Qwen3.5-9B"
        self._initialized = True
    
    def load_base_model(self):
        """加载基础模型（只加载一次）"""
        if self.base_model is None:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            model_path = self.base_model_name
            print(f"📥 加载基础模型: {model_path}")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"本地基础模型目录不存在: {model_path}")
            
            # 检查是否启用量化
            from backend.llm.model_config import get_quantization_config
            quant_config = get_quantization_config()
            
            load_kwargs = {
                "trust_remote_code": True,
                "device_map": "auto",
                "local_files_only": True
            }
            
            # 根据配置选择加载方式
            if quant_config.get("enable_quantization") and quant_config.get("load_in_4bit"):
                # 使用 4-bit 量化加载（bitsandbytes）
                print("🔧 启用 4-bit 量化加载...")
                from transformers import BitsAndBytesConfig
                
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=quant_config.get("bnb_4bit_use_double_quant", True),
                    bnb_4bit_quant_type=quant_config.get("bnb_4bit_quant_type", "nf4"),
                    bnb_4bit_compute_dtype=torch.bfloat16
                )
                load_kwargs["quantization_config"] = bnb_config
            else:
                # 使用 FP16 或 BF16 加载
                load_kwargs["torch_dtype"] = torch.bfloat16 if torch.cuda.is_available() else torch.float32
            
            self.base_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **load_kwargs
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            vram_gb = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
            print(f"✅ 基础模型加载完成 (VRAM: {vram_gb:.2f} GB)\n")
    
    def get_user_lora_path(self, user_id: str) -> Optional[str]:
        """获取用户最新的 LoRA 模型路径"""
        lora_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "lora", user_id))
        
        if not os.path.exists(lora_dir):
            return None
        
        # 找到最新版本
        versions = [d for d in os.listdir(lora_dir) if d.startswith('v') and os.path.isdir(os.path.join(lora_dir, d))]
        if not versions:
            return None
        
        # 按版本号排序
        latest_version = sorted(versions, key=lambda x: int(x[1:]))[-1]
        lora_path = os.path.join(lora_dir, latest_version, "final")
        
        if os.path.exists(lora_path):
            return lora_path
        
        return None
    
    def has_lora_model(self, user_id: str) -> bool:
        """检查用户是否有 LoRA 模型"""
        return self.get_user_lora_path(user_id) is not None
    
    def get_lora_path(self, user_id: str) -> Optional[str]:
        """获取用户 LoRA 模型路径（别名方法）"""
        return self.get_user_lora_path(user_id)
    
    def get_quantized_lora_path(self, user_id: str) -> Optional[str]:
        """获取用户量化 LoRA 模型路径（如果存在）"""
        lora_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "models", "lora")
        )
        q4_path = os.path.join(lora_dir, f"{user_id}_q4")
        
        if os.path.exists(q4_path):
            config_file = os.path.join(q4_path, "adapter_config.json")
            if os.path.exists(config_file):
                return q4_path
        
        return None

    def load_user_lora(self, user_id: str, prefer_quantized: bool = True):
        """
        加载用户的 LoRA 模型
        
        优先加载量化版本（如果存在且启用了量化）
        """
        from peft import PeftModel

        # 如果已经加载，直接返回
        if user_id in self.loaded_loras:
            return self.loaded_loras[user_id]
        
        # 加载基础模型
        self.load_base_model()
        
        # 检查是否优先使用量化 LoRA
        lora_path = None
        is_quantized = False
        
        if prefer_quantized:
            from backend.llm.model_config import MODEL_CONFIG
            lora_quant_cfg = MODEL_CONFIG.get("lora_config_quantization", {})
            
            if lora_quant_cfg.get("quantize_after_training"):
                q4_path = self.get_quantized_lora_path(user_id)
                if q4_path:
                    lora_path = q4_path
                    is_quantized = True
                    print(f"🔧 找到量化 LoRA: {q4_path}")
        
        # 如果没有量化版本，使用原始版本
        if not lora_path:
            lora_path = self.get_user_lora_path(user_id)
        
        if not lora_path:
            print(f"⚠️  用户 {user_id} 还没有训练 LoRA 模型，使用基础模型")
            return None

        adapter_safetensors = os.path.join(lora_path, "adapter_model.safetensors")
        adapter_bin = os.path.join(lora_path, "adapter_model.bin")
        if not os.path.exists(adapter_safetensors) and not os.path.exists(adapter_bin):
            # 量化版本没有完整 adapter，回退到原始版本
            if is_quantized:
                print(f"⚠️  量化 LoRA 不完整，回退到原始版本")
                lora_path = self.get_user_lora_path(user_id)
                is_quantized = False
                if not lora_path:
                    return None
                adapter_safetensors = os.path.join(lora_path, "adapter_model.safetensors")
                adapter_bin = os.path.join(lora_path, "adapter_model.bin")
                if not os.path.exists(adapter_safetensors) and not os.path.exists(adapter_bin):
                    print(f"❌ 用户 {user_id} 的 LoRA 模型不完整: {lora_path}")
                    return None
            else:
                print(f"❌ 用户 {user_id} 的 LoRA 模型不完整: {lora_path}")
                return None
        
        try:
            q_label = " (量化4-bit)" if is_quantized else ""
            print(f"📥 加载用户 {user_id} 的 LoRA 模型{q_label}...")
            model = PeftModel.from_pretrained(
                self.base_model,
                model_id=lora_path,
                is_trainable=False
            )
            
            self.loaded_loras[user_id] = model
            print(f"✅ LoRA 模型加载完成{q_label}\n")
            
            return model
            
        except Exception as e:
            print(f"❌ 加载 LoRA 失败: {e}")
            # 如果量化版本加载失败，回退到原始版本
            if is_quantized:
                print("⚠️  尝试回退到原始 LoRA...")
                original_path = self.get_user_lora_path(user_id)
                if original_path:
                    try:
                        model = PeftModel.from_pretrained(
                            self.base_model,
                            model_id=original_path,
                            is_trainable=False
                        )
                        self.loaded_loras[user_id] = model
                        print(f"✅ 原始 LoRA 加载完成\n")
                        return model
                    except Exception as e2:
                        print(f"❌ 原始 LoRA 也加载失败: {e2}")
            return None
    
    def unload_user_lora(self, user_id: str):
        """卸载用户的 LoRA 模型（释放内存）"""
        if user_id in self.loaded_loras:
            del self.loaded_loras[user_id]
            print(f"🗑️  已卸载用户 {user_id} 的 LoRA 模型")
    
    def generate(self, user_id: str, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        """使用用户的 LoRA 模型生成回复"""
        import torch

        model = self.load_user_lora(user_id)
        
        if model is None:
            self.load_base_model()
            model = self.base_model
            print(f"ℹ️  使用基础模型（用户 {user_id} 的 LoRA 未找到）")
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda:0") for k, v in inputs.items()}
        
        # 生成参数（优化内存使用）
        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": temperature > 0,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.15,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "use_cache": True,
            "num_beams": 1  # 使用贪婪搜索，减少内存
        }
        
        # 如果温度为 0，使用贪婪解码
        if temperature == 0:
            gen_kwargs["do_sample"] = False
            gen_kwargs.pop("temperature", None)
            gen_kwargs.pop("top_p", None)
            gen_kwargs.pop("top_k", None)
        
        # 生成
        try:
            with torch.no_grad():
                with torch.amp.autocast("cuda"):
                    outputs = model.generate(
                        **inputs,
                        **gen_kwargs
                    )
            
            # 解码
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除输入部分
            response = response[len(prompt):].strip()
            
            # 清理
            del inputs, outputs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return response
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            # 清理内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise

    def generate_stream(self, user_id: str, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7):
        """使用用户的 LoRA 模型流式生成回复"""
        import torch
        from transformers import TextIteratorStreamer

        model = self.load_user_lora(user_id)
        if model is None:
            self.load_base_model()
            model = self.base_model
            print(f"ℹ️  使用基础模型流式生成（用户 {user_id} 的 LoRA 未找到）")

        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=3072)
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda:0") for k, v in inputs.items()}

        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        gen_kwargs = {
            **inputs,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": temperature > 0,
            "top_p": 0.92,
            "top_k": 40,
            "repetition_penalty": 1.15,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "use_cache": True,
            "num_beams": 1,
            "streamer": streamer
        }
        if temperature == 0:
            gen_kwargs["do_sample"] = False
            gen_kwargs.pop("temperature", None)
            gen_kwargs.pop("top_p", None)
            gen_kwargs.pop("top_k", None)

        def _run_generate():
            try:
                with torch.no_grad():
                    with torch.amp.autocast("cuda"):
                        model.generate(**gen_kwargs)
            except Exception as e:
                print(f"❌ 流式生成失败: {e}")
            finally:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        thread = threading.Thread(target=_run_generate)
        thread.start()

        for text in streamer:
            if text:
                yield text

        thread.join()
    
    def get_model_info(self, user_id: str) -> dict:
        """获取用户模型信息（包含量化状态）"""
        lora_path = self.get_user_lora_path(user_id)
        quantized_lora_path = self.get_quantized_lora_path(user_id)
        
        info = {
            "user_id": user_id,
            "has_lora": lora_path is not None,
            "lora_path": lora_path,
            "has_quantized_lora": quantized_lora_path is not None,
            "quantized_lora_path": quantized_lora_path,
            "is_loaded": user_id in self.loaded_loras,
            "base_model": self.base_model_name,
            "base_model_quantized": False
        }
        
        # 检查基座模型是否使用了量化
        try:
            from backend.llm.model_config import get_quantization_config
            quant_cfg = get_quantization_config()
            info["base_model_quantized"] = quant_cfg.get("enable_quantization", False)
            info["quantization_type"] = quant_cfg.get("quantization_type", "none")
        except Exception:
            pass
        
        # 当前 VRAM 使用
        try:
            import torch
            if torch.cuda.is_available():
                info["vram_used_gb"] = round(torch.cuda.memory_allocated() / 1024**3, 2)
                info["vram_total_gb"] = round(torch.cuda.get_device_properties(0).total_mem / 1024**3, 2)
        except Exception:
            pass
        
        # 读取训练状态
        status_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "lora", user_id, "status.json"))
        if os.path.exists(status_file):
            import json
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
                info.update(status)
        
        return info


# 全局单例
lora_manager = LoRAModelManager()


# 测试代码
if __name__ == "__main__":
    manager = LoRAModelManager()
    
    # 测试生成
    user_id = "test_user"
    prompt = "<|im_start|>user\n你好<|im_end|>\n<|im_start|>assistant\n"
    
    response = manager.generate(user_id, prompt, max_new_tokens=50)
    print(f"回复: {response}")
    
    # 获取模型信息
    info = manager.get_model_info(user_id)
    print(f"\n模型信息: {info}")
