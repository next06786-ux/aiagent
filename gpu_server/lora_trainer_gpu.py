"""
GPU服务器专用 LoRA 训练器
针对32GB显存优化，支持更大模型和更高效训练
"""
import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    Trainer, 
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel, prepare_model_for_kbit_training
from torch.utils.data import Dataset
from datetime import datetime
from typing import List, Dict, Optional
import os
import json
import gc


class ConversationDataset(Dataset):
    """对话数据集 - 支持多种对话格式"""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 1024):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # 确保tokenizer有pad_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        item = self.conversations[idx]
        
        # 构造训练文本（Qwen格式）
        text = f"<|im_start|>user\n{item['user']}<|im_end|>\n<|im_start|>assistant\n{item['assistant']}<|im_end|>"
        
        # Tokenize
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


class GPULoRATrainer:
    """
    GPU服务器专用LoRA训练器
    针对32GB显存优化配置
    """
    
    # 支持的模型配置
    MODEL_CONFIGS = {
        "qwen2.5-7b": {
            "name": "Qwen/Qwen2.5-7B-Instruct",
            "lora_r": 16,
            "lora_alpha": 32,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            "max_length": 2048,
            "batch_size": 4,
            "gradient_accumulation": 4,
            "use_4bit": False  # 32GB显存可以不用量化
        },
        "qwen2.5-14b": {
            "name": "Qwen/Qwen2.5-14B-Instruct",
            "lora_r": 16,
            "lora_alpha": 32,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            "max_length": 1024,
            "batch_size": 2,
            "gradient_accumulation": 8,
            "use_4bit": True  # 14B需要4bit量化
        },
        "qwen2.5-3b": {
            "name": "Qwen/Qwen2.5-3B-Instruct",
            "lora_r": 32,
            "lora_alpha": 64,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            "max_length": 2048,
            "batch_size": 8,
            "gradient_accumulation": 2,
            "use_4bit": False
        }
    }
    
    def __init__(
        self, 
        user_id: str, 
        model_type: str = "qwen2.5-7b",
        output_base_dir: str = "./models/lora"
    ):
        self.user_id = user_id
        self.model_type = model_type
        self.output_base_dir = output_base_dir
        
        # 获取模型配置
        if model_type not in self.MODEL_CONFIGS:
            raise ValueError(f"不支持的模型类型: {model_type}，可选: {list(self.MODEL_CONFIGS.keys())}")
        
        self.config = self.MODEL_CONFIGS[model_type]
        self.model_name = self.config["name"]
        
        # 状态文件
        self.status_file = os.path.join(output_base_dir, user_id, "status.json")
        self.status = self._load_status()
        
        # 模型和tokenizer（延迟加载）
        self.model = None
        self.tokenizer = None
    
    def _load_status(self) -> Dict:
        """加载训练状态"""
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "last_training_time": None,
            "total_trainings": 0,
            "training_samples": 0,
            "model_version": 0,
            "model_type": self.model_type,
            "is_training": False
        }
    
    def _save_status(self):
        """保存训练状态"""
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def _load_model_and_tokenizer(self):
        """加载模型和tokenizer"""
        if self.model is not None:
            return
        
        print(f"📥 加载模型: {self.model_name}")
        
        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 模型加载配置
        load_kwargs = {
            "trust_remote_code": True,
            "device_map": "auto",
        }
        
        if self.config["use_4bit"]:
            # 4bit量化配置
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )
            load_kwargs["quantization_config"] = bnb_config
        else:
            load_kwargs["torch_dtype"] = torch.bfloat16
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **load_kwargs
        )
        
        if self.config["use_4bit"]:
            self.model = prepare_model_for_kbit_training(self.model)
        
        # 打印显存使用
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            print(f"✅ 模型加载完成，显存占用: {allocated:.2f} GB")
    
    def _get_lora_config(self) -> LoraConfig:
        """获取LoRA配置"""
        return LoraConfig(
            r=self.config["lora_r"],
            lora_alpha=self.config["lora_alpha"],
            target_modules=self.config["target_modules"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )

    def train(
        self, 
        conversations: List[Dict],
        num_epochs: int = 3,
        learning_rate: float = 2e-4,
        warmup_ratio: float = 0.1
    ) -> Dict:
        """
        训练LoRA模型
        
        Args:
            conversations: 对话数据列表 [{"user": "...", "assistant": "..."}]
            num_epochs: 训练轮数
            learning_rate: 学习率
            warmup_ratio: 预热比例
        
        Returns:
            训练结果信息
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始LoRA训练")
        print(f"👤 用户: {self.user_id}")
        print(f"🤖 模型: {self.model_type}")
        print(f"📊 数据量: {len(conversations)} 条对话")
        print(f"{'='*60}\n")
        
        # 检查数据量
        if len(conversations) < 5:
            return {
                "success": False,
                "error": f"数据量不足，需要至少5条对话，当前: {len(conversations)}"
            }
        
        self.status["is_training"] = True
        self._save_status()
        
        try:
            # 1. 加载模型
            self._load_model_and_tokenizer()
            
            # 2. 准备数据集
            print("📚 准备数据集...")
            dataset = ConversationDataset(
                conversations, 
                self.tokenizer, 
                self.config["max_length"]
            )
            
            # 3. 添加LoRA层
            print("🔧 添加LoRA适配器...")
            lora_config = self._get_lora_config()
            model = get_peft_model(self.model, lora_config)
            
            # 打印可训练参数
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total_params = sum(p.numel() for p in model.parameters())
            print(f"📊 可训练参数: {trainable_params:,} / {total_params:,} ({100*trainable_params/total_params:.4f}%)")
            
            # 4. 训练配置
            new_version = self.status["model_version"] + 1
            output_dir = os.path.join(self.output_base_dir, self.user_id, f"v{new_version}")
            
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=self.config["batch_size"],
                gradient_accumulation_steps=self.config["gradient_accumulation"],
                learning_rate=learning_rate,
                warmup_ratio=warmup_ratio,
                bf16=True,
                logging_steps=10,
                save_strategy="epoch",
                save_total_limit=2,
                report_to="none",
                remove_unused_columns=False,
                optim="adamw_torch",
                gradient_checkpointing=True,  # 节省显存
                dataloader_pin_memory=True
            )
            
            # 5. 创建Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset
            )
            
            # 6. 开始训练
            print("\n🎯 开始训练...\n")
            start_time = datetime.now()
            
            train_result = trainer.train()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 7. 保存模型
            final_path = os.path.join(output_dir, "final")
            model.save_pretrained(final_path)
            self.tokenizer.save_pretrained(final_path)
            
            # 8. 更新状态
            self.status["last_training_time"] = datetime.now().isoformat()
            self.status["total_trainings"] += 1
            self.status["training_samples"] = len(conversations)
            self.status["model_version"] = new_version
            self.status["is_training"] = False
            self._save_status()
            
            # 9. 清理显存
            del model, trainer
            gc.collect()
            torch.cuda.empty_cache()
            
            result = {
                "success": True,
                "model_path": final_path,
                "model_version": new_version,
                "training_samples": len(conversations),
                "training_time_seconds": duration,
                "train_loss": train_result.training_loss
            }
            
            print(f"\n{'='*60}")
            print(f"✅ 训练完成!")
            print(f"⏱️  耗时: {duration:.1f} 秒")
            print(f"📉 Loss: {train_result.training_loss:.4f}")
            print(f"💾 模型保存: {final_path}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            self.status["is_training"] = False
            self._save_status()
            
            # 清理显存
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"❌ 训练失败: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def generate(
        self, 
        prompt: str, 
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """使用训练好的LoRA模型生成回复"""
        
        # 加载基础模型
        self._load_model_and_tokenizer()
        
        # 查找最新的LoRA权重
        lora_path = self._get_latest_lora_path()
        
        if lora_path and os.path.exists(lora_path):
            print(f"📥 加载LoRA权重: {lora_path}")
            model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                torch_dtype=torch.bfloat16
            )
        else:
            print("⚠️ 未找到LoRA权重，使用基础模型")
            model = self.model
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # 解码
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(prompt):].strip()
        
        return response
    
    def _get_latest_lora_path(self) -> Optional[str]:
        """获取最新的LoRA模型路径"""
        user_dir = os.path.join(self.output_base_dir, self.user_id)
        
        if not os.path.exists(user_dir):
            return None
        
        versions = [d for d in os.listdir(user_dir) 
                   if d.startswith('v') and os.path.isdir(os.path.join(user_dir, d))]
        
        if not versions:
            return None
        
        latest = sorted(versions, key=lambda x: int(x[1:]))[-1]
        final_path = os.path.join(user_dir, latest, "final")
        
        return final_path if os.path.exists(final_path) else None
    
    def get_status(self) -> Dict:
        """获取训练状态"""
        return {
            **self.status,
            "model_type": self.model_type,
            "has_lora": self._get_latest_lora_path() is not None,
            "lora_path": self._get_latest_lora_path()
        }


# 测试代码
if __name__ == "__main__":
    # 测试训练
    trainer = GPULoRATrainer(
        user_id="test_user",
        model_type="qwen2.5-7b"
    )
    
    # 模拟对话数据
    test_conversations = [
        {"user": "你好，我在考虑要不要换工作", "assistant": "换工作是个重要决定。你目前工作有什么不满意的地方吗？"},
        {"user": "主要是薪资太低，而且没有成长空间", "assistant": "理解你的顾虑。薪资和成长空间确实是职业发展的关键因素。你有考虑过目标公司或行业吗？"},
        {"user": "想去互联网大厂", "assistant": "互联网大厂确实机会多，但竞争也激烈。建议你先评估自己的技术栈是否匹配，同时准备好面试。"},
        {"user": "我应该先学什么技术？", "assistant": "这取决于你想去的岗位。如果是后端，可以深入学习分布式系统；如果是前端，可以关注React/Vue生态。"},
        {"user": "谢谢你的建议", "assistant": "不客气！祝你求职顺利，有问题随时问我。"},
    ] * 10  # 复制10次得到50条数据
    
    # 开始训练
    result = trainer.train(test_conversations, num_epochs=1)
    print(f"\n训练结果: {result}")
