#!/usr/bin/env python3
"""
vLLM 兼容的 LoRA 训练器
训练完成后自动注册到 vLLM 服务
"""
import os
import sys
import json
import torch
import gc
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset
import httpx


# ============== 配置 ==============

@dataclass
class TrainingConfig:
    """训练配置"""
    # 路径
    data_dir: str = "/root/autodl-tmp"
    lora_output_dir: str = "/root/autodl-tmp/models/lora"
    
    # 模型
    base_model: str = "Qwen/Qwen2.5-7B-Instruct"
    
    # LoRA 参数
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = None
    
    # 训练参数
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    max_length: int = 1024
    gradient_accumulation_steps: int = 4
    
    # vLLM 服务地址（训练完成后通知）
    vllm_server_url: str = "http://localhost:8000"
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]


# ============== 数据集 ==============

class ConversationDataset(Dataset):
    """对话数据集"""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 1024):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        item = self.conversations[idx]
        
        # Qwen 格式
        text = f"<|im_start|>user\n{item['user']}<|im_end|>\n<|im_start|>assistant\n{item['assistant']}<|im_end|>"
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze()
        }


# ============== 训练器 ==============

class VLLMLoRATrainer:
    """vLLM 兼容的 LoRA 训练器"""
    
    def __init__(self, user_id: str, config: TrainingConfig = None):
        self.user_id = user_id
        self.config = config or TrainingConfig()
        
        self.user_lora_dir = Path(self.config.lora_output_dir) / user_id
        self.status_file = self.user_lora_dir / "status.json"
        
        self.model = None
        self.tokenizer = None
        
        # 加载状态
        self.status = self._load_status()
    
    def _load_status(self) -> Dict:
        """加载训练状态"""
        if self.status_file.exists():
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "user_id": self.user_id,
            "model_version": 0,
            "total_trainings": 0,
            "last_training": None,
            "total_samples": 0,
            "is_training": False
        }
    
    def _save_status(self):
        """保存训练状态"""
        self.user_lora_dir.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def _load_model(self):
        """加载基座模型"""
        if self.model is not None:
            return
        
        print(f"📥 加载基座模型: {self.config.base_model}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        
        if torch.cuda.is_available():
            mem_gb = torch.cuda.memory_allocated() / 1024**3
            print(f"✅ 模型加载完成，显存占用: {mem_gb:.2f} GB")
    
    def train(self, conversations: List[Dict]) -> Dict:
        """
        训练 LoRA 模型
        
        Args:
            conversations: [{"user": "...", "assistant": "..."}]
        
        Returns:
            训练结果
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始 LoRA 训练")
        print(f"👤 用户: {self.user_id}")
        print(f"📊 数据量: {len(conversations)} 条对话")
        print(f"{'='*60}\n")
        
        if len(conversations) < 5:
            return {"success": False, "error": "数据量不足，至少需要 5 条对话"}
        
        self.status["is_training"] = True
        self._save_status()
        
        try:
            # 1. 加载模型
            self._load_model()
            
            # 2. 准备数据集
            print("📚 准备数据集...")
            dataset = ConversationDataset(
                conversations,
                self.tokenizer,
                self.config.max_length
            )
            
            # 3. 配置 LoRA
            print("🔧 配置 LoRA...")
            lora_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                target_modules=self.config.target_modules,
                lora_dropout=self.config.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
            
            model = get_peft_model(self.model, lora_config)
            
            # 打印参数统计
            trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in model.parameters())
            print(f"📊 可训练参数: {trainable:,} / {total:,} ({100*trainable/total:.4f}%)")
            
            # 4. 训练配置
            new_version = self.status["model_version"] + 1
            output_dir = self.user_lora_dir / f"v{new_version}"
            
            training_args = TrainingArguments(
                output_dir=str(output_dir),
                num_train_epochs=self.config.num_epochs,
                per_device_train_batch_size=self.config.batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                learning_rate=self.config.learning_rate,
                warmup_ratio=0.1,
                bf16=True,
                logging_steps=10,
                save_strategy="epoch",
                save_total_limit=2,
                report_to="none",
                remove_unused_columns=False,
                gradient_checkpointing=True,
            )
            
            # 5. 训练
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset
            )
            
            print("\n🎯 开始训练...\n")
            start_time = datetime.now()
            
            result = trainer.train()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # 6. 保存模型
            final_path = output_dir / "final"
            model.save_pretrained(str(final_path))
            self.tokenizer.save_pretrained(str(final_path))
            
            # 7. 更新状态
            self.status["model_version"] = new_version
            self.status["total_trainings"] += 1
            self.status["last_training"] = datetime.now().isoformat()
            self.status["total_samples"] = len(conversations)
            self.status["is_training"] = False
            self._save_status()
            
            # 8. 通知 vLLM 服务重新加载
            self._notify_vllm_reload()
            
            # 9. 清理
            del model, trainer
            gc.collect()
            torch.cuda.empty_cache()
            
            print(f"\n{'='*60}")
            print(f"✅ 训练完成!")
            print(f"⏱️  耗时: {duration:.1f} 秒")
            print(f"📉 Loss: {result.training_loss:.4f}")
            print(f"💾 保存: {final_path}")
            print(f"{'='*60}\n")
            
            return {
                "success": True,
                "model_path": str(final_path),
                "version": new_version,
                "training_loss": result.training_loss,
                "duration_seconds": duration
            }
            
        except Exception as e:
            self.status["is_training"] = False
            self._save_status()
            
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            import traceback
            error = f"{e}\n{traceback.format_exc()}"
            print(f"❌ 训练失败: {error}")
            
            return {"success": False, "error": str(e)}
    
    def _notify_vllm_reload(self):
        """通知 vLLM 服务重新加载 LoRA"""
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(f"{self.config.vllm_server_url}/v1/loras/reload")
                if resp.status_code == 200:
                    print(f"✅ 已通知 vLLM 服务重新加载 LoRA")
                else:
                    print(f"⚠️ vLLM 通知失败: {resp.status_code}")
        except Exception as e:
            print(f"⚠️ 无法连接 vLLM 服务: {e}")
    
    def get_status(self) -> Dict:
        """获取训练状态"""
        return {
            **self.status,
            "lora_path": str(self.user_lora_dir / f"v{self.status['model_version']}" / "final")
            if self.status["model_version"] > 0 else None
        }


# ============== 测试 ==============

if __name__ == "__main__":
    # 测试训练
    trainer = VLLMLoRATrainer("test_user")
    
    # 模拟数据
    test_data = [
        {"user": "你好", "assistant": "你好！有什么我可以帮助你的吗？"},
        {"user": "今天天气怎么样", "assistant": "我无法获取实时天气信息，建议你查看天气预报应用。"},
        {"user": "推荐一本书", "assistant": "推荐《思考，快与慢》，这本书深入探讨了人类决策的心理学原理。"},
        {"user": "如何学习编程", "assistant": "建议从 Python 开始，它语法简洁，适合初学者。可以通过在线课程和实践项目来学习。"},
        {"user": "谢谢", "assistant": "不客气！如果还有其他问题，随时问我。"},
    ] * 10  # 复制得到 50 条
    
    result = trainer.train(test_data)
    print(f"\n训练结果: {result}")
