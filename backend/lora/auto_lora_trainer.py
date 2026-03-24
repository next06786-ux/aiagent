"""
LoRA 自动化训练系统
为每个用户训练专属的个性化模型
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from torch.utils.data import Dataset
import schedule
import threading
from datetime import datetime
from typing import List, Dict
import os
import json
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConversationDataset(Dataset):
    """对话数据集"""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 512):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        item = self.conversations[idx]
        
        # 构造训练文本（Qwen 格式）
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


class AutoLoRATrainer:
    """LoRA 自动化训练器"""
    
    def __init__(self, user_id: str, base_model_name: str = "/root/autodl-tmp/models/base/Qwen3.5-9B"):
        self.user_id = user_id
        self.base_model_name = base_model_name
        
        # LoRA 配置（Qwen3.5-9B 用户专属适配）
        self.lora_config = LoraConfig(
            r=64,
            lora_alpha=128,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        
        # 训练配置（轻量版，快速且稳定）
        self.training_config = {
            "min_data_size": 20,         # 最少 20 条对话
            "train_interval_days": 7,    # 每 7 天训练一次
            "num_epochs": 1,             # 训练 1 轮（小数据集够用）
            "batch_size": 1,             # 批次大小 1（显存安全）
            "learning_rate": 2e-4,       # 学习率
            "max_length": 256            # 最大序列长度（对话够用）
        }
        
        # 训练状态
        self.status_file = f"./models/lora/{user_id}/status.json"
        self.status = self.load_status()
        
        # 缓存 RAG 系统（避免重复初始化）
        self._rag_system = None
    
    def load_status(self) -> Dict:
        """加载训练状态"""
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
                # 转换时间字符串
                if status.get("last_train_time"):
                    status["last_train_time"] = datetime.fromisoformat(status["last_train_time"])
                return status
        
        return {
            "last_train_time": None,
            "total_trainings": 0,
            "current_data_size": 0,
            "is_training": False,
            "model_version": 0
        }
    
    def save_status(self):
        """保存训练状态"""
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        
        status_to_save = {
            **self.status,
            "last_train_time": self.status["last_train_time"].isoformat() if self.status["last_train_time"] else None
        }
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_to_save, f, indent=2, ensure_ascii=False)
    
    def check_training_trigger(self) -> bool:
        """检查是否需要触发训练"""
        
        # 1. 获取用户对话数据
        conversations = self.get_user_conversations()
        self.status["current_data_size"] = len(conversations)
        
        # 2. 检查数据量
        if len(conversations) < self.training_config["min_data_size"]:
            print(f"❌ 数据不足: {len(conversations)}/{self.training_config['min_data_size']}")
            return False
        
        # 3. 检查时间间隔
        if self.status["last_train_time"]:
            days_since_last = (datetime.now() - self.status["last_train_time"]).days
            if days_since_last < self.training_config["train_interval_days"]:
                print(f"⏰ 距离上次训练仅 {days_since_last} 天")
                return False
        
        # 4. 检查是否正在训练
        if self.status["is_training"]:
            print("⚠️ 已有训练任务在进行中")
            return False
        
        return True
    
    def get_user_conversations(self) -> List[Dict]:
        """从 RAG 系统获取用户对话"""
        try:
            from learning.production_rag_system import ProductionRAGSystem
            
            # 使用缓存的 RAG 系统
            if self._rag_system is None:
                self._rag_system = ProductionRAGSystem(self.user_id)
            
            memories = self._rag_system.get_all_memories()
            
            # 只取对话类型的记忆
            conversations = []
            for mem in memories:
                if mem.memory_type.value == "conversation":
                    # 解析用户消息和 AI 回复
                    content = mem.content
                    if "用户:" in content and "AI:" in content:
                        parts = content.split("AI:")
                        user_msg = parts[0].replace("用户:", "").strip()
                        ai_msg = parts[1].strip() if len(parts) > 1 else ""
                        
                        if user_msg and ai_msg:
                            conversations.append({
                                "user": user_msg,
                                "assistant": ai_msg,
                                "timestamp": mem.timestamp
                            })
            
            return conversations
        except Exception as e:
            print(f"⚠️ 获取对话数据失败: {e}")
            return []
    
    def prepare_dataset(self, conversations: List[Dict]) -> Dataset:
        """准备训练数据集"""
        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True
        )
        
        return ConversationDataset(
            conversations,
            tokenizer,
            self.training_config["max_length"]
        )
    
    def train_lora(self, dataset: Dataset) -> str:
        """训练 LoRA 模型"""
        
        print(f"\n{'='*60}")
        print(f"🚀 开始为用户 {self.user_id} 训练 LoRA 模型")
        print(f"📊 训练数据量: {len(dataset)}")
        print(f"{'='*60}\n")
        
        try:
            # 1. 加载基础模型
            print("📥 加载基础模型...")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            # 2. 添加 LoRA 层
            print("🔧 添加 LoRA 适配器...")
            model = get_peft_model(base_model, self.lora_config)
            
            # 打印可训练参数
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total_params = sum(p.numel() for p in model.parameters())
            print(f"📊 可训练参数: {trainable_params:,} / {total_params:,} ({100 * trainable_params / total_params:.2f}%)")
            
            # 3. 训练参数
            output_dir = f"./models/lora/{self.user_id}/v{self.status['model_version'] + 1}"
            
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.training_config["num_epochs"],
                per_device_train_batch_size=self.training_config["batch_size"],
                gradient_accumulation_steps=4,
                learning_rate=self.training_config["learning_rate"],
                fp16=True,
                logging_steps=5,
                save_strategy="epoch",
                save_total_limit=3,
                report_to="none",
                remove_unused_columns=False
            )
            
            # 4. 创建 Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset
            )
            
            # 5. 开始训练
            print("🎯 开始训练...\n")
            start_time = datetime.now()
            
            trainer.train()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 6. 保存模型
            final_path = f"{output_dir}/final"
            os.makedirs(final_path, exist_ok=True)

            # 优先保存 PEFT adapter 权重
            model.save_pretrained(final_path, safe_serialization=True)

            # 同时保存 tokenizer，便于后续排查与复用
            tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
                local_files_only=True if os.path.exists(self.base_model_name) else False
            )
            tokenizer.save_pretrained(final_path)

            # 7. 校验关键文件
            expected_files = [
                os.path.join(final_path, "adapter_config.json"),
                os.path.join(final_path, "adapter_model.safetensors")
            ]
            missing_files = [f for f in expected_files if not os.path.exists(f)]
            if missing_files:
                raise RuntimeError(f"LoRA 保存不完整，缺少文件: {missing_files}")

            print(f"\n✅ 训练完成!")
            print(f"⏱️  耗时: {duration:.1f} 秒")
            print(f"💾 模型已保存到: {final_path}\n")
            
            return final_path
            
        except Exception as e:
            print(f"\n❌ 训练失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def auto_train_workflow(self):
        """自动训练工作流"""
        
        print(f"\n{'='*60}")
        print(f"🤖 LoRA 自动训练检查")
        print(f"👤 用户: {self.user_id}")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 1. 检查是否需要训练
        if not self.check_training_trigger():
            print("⏭️  跳过本次训练\n")
            return
        
        # 2. 获取训练数据
        print("📚 收集训练数据...")
        conversations = self.get_user_conversations()
        print(f"✅ 收集到 {len(conversations)} 条对话\n")
        
        # 3. 准备数据集
        print("🔄 准备数据集...")
        dataset = self.prepare_dataset(conversations)
        print(f"✅ 数据集准备完成\n")
        
        # 4. 开始训练
        self.status["is_training"] = True
        self.save_status()
        
        try:
            model_path = self.train_lora(dataset)
            
            if model_path:
                # 更新状态
                self.status["last_train_time"] = datetime.now()
                self.status["total_trainings"] += 1
                self.status["model_version"] += 1
                self.status["is_training"] = False
                
                # 保存状态
                self.save_status()
                
                print(f"📊 训练统计:")
                print(f"   - 总训练次数: {self.status['total_trainings']}")
                print(f"   - 当前版本: v{self.status['model_version']}")
                print(f"   - 数据量: {len(conversations)}")
                print(f"   - 下次训练: {self.training_config['train_interval_days']} 天后\n")
            else:
                self.status["is_training"] = False
                self.save_status()
                print("❌ 训练失败\n")
                
        except Exception as e:
            self.status["is_training"] = False
            self.save_status()
            print(f"❌ 训练异常: {e}\n")
            import traceback
            traceback.print_exc()


# 测试代码
if __name__ == "__main__":
    # 测试训练器
    trainer = AutoLoRATrainer("test_user")
    trainer.auto_train_workflow()
