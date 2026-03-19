"""
LoRA定时训练调度器
自动调度用户的LoRA模型训练任务
"""
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.lora.auto_lora_trainer import AutoLoRATrainer
from backend.personality.dynamic_profile_updater import DynamicProfileUpdater


class LoRAScheduler:
    """LoRA训练调度器"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.active_users = []  # 活跃用户列表
        self.training_queue = []  # 训练队列
        self.profile_updater = DynamicProfileUpdater()
        
        # 调度配置
        self.config = {
            "weekly_training_day": "sunday",  # 每周日训练
            "weekly_training_time": "03:00",  # 凌晨3点
            "profile_update_day": "sunday",   # 每周日更新画像
            "profile_update_time": "02:00",   # 凌晨2点（在训练前）
            "check_interval": 3600,           # 每小时检查一次
        }
        
        # 加载活跃用户列表
        self._load_active_users()
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            print("⚠️  调度器已在运行中")
            return
        
        print("\n" + "="*60)
        print("🚀 LoRA训练调度器启动")
        print("="*60)
        print(f"每周训练时间: {self.config['weekly_training_day']} {self.config['weekly_training_time']}")
        print(f"画像更新时间: {self.config['profile_update_day']} {self.config['profile_update_time']}")
        print(f"活跃用户数: {len(self.active_users)}")
        print("="*60 + "\n")
        
        self.is_running = True
        
        # 设置定时任务
        self._setup_schedules()
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("✅ 调度器已启动\n")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            print("⚠️  调度器未运行")
            return
        
        print("\n🛑 正在停止调度器...")
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("✅ 调度器已停止\n")
    
    def _setup_schedules(self):
        """设置定时任务"""
        print("📅 定时任务已设置:")
        print(f"  - 画像更新: 每周{self.config['profile_update_day']} {self.config['profile_update_time']}")
        print(f"  - LoRA训练: 每周{self.config['weekly_training_day']} {self.config['weekly_training_time']}")
        print(f"  - 队列检查: 每小时")
    
    def _run_scheduler(self):
        """运行调度器主循环"""
        last_profile_update = datetime.now()
        last_lora_training = datetime.now()
        last_queue_check = datetime.now()
        
        while self.is_running:
            try:
                now = datetime.now()
                
                # 检查是否到了画像更新时间（每周日凌晨2点）
                if self._should_run_weekly_task(now, last_profile_update, 
                                               self.config['profile_update_day'],
                                               self.config['profile_update_time']):
                    self._weekly_profile_update()
                    last_profile_update = now
                
                # 检查是否到了LoRA训练时间（每周日凌晨3点）
                if self._should_run_weekly_task(now, last_lora_training,
                                               self.config['weekly_training_day'],
                                               self.config['weekly_training_time']):
                    self._weekly_lora_training()
                    last_lora_training = now
                
                # 每小时检查训练队列
                if (now - last_queue_check).total_seconds() >= 3600:
                    self._check_training_queue()
                    last_queue_check = now
                
                time.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                print(f"❌ 调度器错误: {e}")
                import traceback
                traceback.print_exc()
    
    def _should_run_weekly_task(self, now: datetime, last_run: datetime, 
                                target_day: str, target_time: str) -> bool:
        """检查是否应该运行周任务"""
        days = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        target_weekday = days.get(target_day.lower(), 6)
        hour, minute = map(int, target_time.split(':'))
        
        # 检查是否是目标星期几
        if now.weekday() != target_weekday:
            return False
        
        # 检查是否是目标时间（允许1小时误差）
        if not (hour <= now.hour < hour + 1):
            return False
        
        # 检查距离上次运行是否超过6天（避免重复运行）
        if (now - last_run).days < 6:
            return False
        
        return True
    
    def _weekly_profile_update(self):
        """每周画像更新任务"""
        print("\n" + "="*60)
        print(f"📊 开始每周画像更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        updated_count = 0
        
        for user_id in self.active_users:
            try:
                # 检查是否需要更新
                if self.profile_updater.check_update_trigger(user_id):
                    print(f"\n更新用户画像: {user_id}")
                    result = self.profile_updater.update_profile(user_id)
                    
                    if result.has_changes:
                        updated_count += 1
                        print(f"✅ {user_id}: {result.summary}")
                    else:
                        print(f"⏭️  {user_id}: 无显著变化")
                else:
                    print(f"⏭️  {user_id}: 不满足更新条件")
                
            except Exception as e:
                print(f"❌ {user_id} 更新失败: {e}")
        
        print(f"\n{'='*60}")
        print(f"画像更新完成: {updated_count}/{len(self.active_users)} 个用户有变化")
        print(f"{'='*60}\n")
    
    def _weekly_lora_training(self):
        """每周LoRA训练任务"""
        print("\n" + "="*60)
        print(f"🤖 开始每周LoRA训练 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        trained_count = 0
        
        for user_id in self.active_users:
            try:
                print(f"\n训练用户模型: {user_id}")
                trainer = AutoLoRATrainer(user_id)
                
                # 检查是否需要训练
                if trainer.check_training_trigger():
                    print(f"✅ {user_id}: 开始训练...")
                    trainer.auto_train_workflow()
                    trained_count += 1
                else:
                    print(f"⏭️  {user_id}: 不满足训练条件")
                
            except Exception as e:
                print(f"❌ {user_id} 训练失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print(f"LoRA训练完成: {trained_count}/{len(self.active_users)} 个用户完成训练")
        print(f"{'='*60}\n")
    
    def _check_training_queue(self):
        """检查训练队列（处理高优先级训练）"""
        if not self.training_queue:
            return
        
        print(f"\n📋 检查训练队列: {len(self.training_queue)} 个任务")
        
        # 处理队列中的任务
        processed = []
        
        for task in self.training_queue:
            user_id = task['user_id']
            priority = task.get('priority', 'normal')
            
            try:
                print(f"\n处理队列任务: {user_id} (优先级: {priority})")
                trainer = AutoLoRATrainer(user_id)
                
                # 高优先级任务降低训练间隔要求
                if priority == 'high':
                    original_interval = trainer.training_config["train_interval_days"]
                    trainer.training_config["train_interval_days"] = 0
                
                trainer.auto_train_workflow()
                
                # 恢复配置
                if priority == 'high':
                    trainer.training_config["train_interval_days"] = original_interval
                
                processed.append(task)
                print(f"✅ {user_id}: 训练完成")
                
            except Exception as e:
                print(f"❌ {user_id}: 训练失败 - {e}")
        
        # 移除已处理的任务
        for task in processed:
            self.training_queue.remove(task)
        
        print(f"\n队列处理完成: {len(processed)} 个任务完成\n")
    
    def add_training_task(self, user_id: str, priority: str = "normal"):
        """
        添加训练任务到队列
        
        Args:
            user_id: 用户ID
            priority: 优先级 (normal/high)
        """
        task = {
            "user_id": user_id,
            "priority": priority,
            "added_time": datetime.now().isoformat()
        }
        
        # 检查是否已在队列中
        if any(t['user_id'] == user_id for t in self.training_queue):
            print(f"⚠️  {user_id} 已在训练队列中")
            return
        
        self.training_queue.append(task)
        print(f"✅ 已添加训练任务: {user_id} (优先级: {priority})")
    
    def add_active_user(self, user_id: str):
        """添加活跃用户"""
        if user_id not in self.active_users:
            self.active_users.append(user_id)
            self._save_active_users()
            print(f"✅ 已添加活跃用户: {user_id}")
    
    def remove_active_user(self, user_id: str):
        """移除活跃用户"""
        if user_id in self.active_users:
            self.active_users.remove(user_id)
            self._save_active_users()
            print(f"✅ 已移除活跃用户: {user_id}")
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "active_users": len(self.active_users),
            "training_queue": len(self.training_queue),
            "next_profile_update": self._get_next_run_time(
                self.config['profile_update_day'],
                self.config['profile_update_time']
            ),
            "next_lora_training": self._get_next_run_time(
                self.config['weekly_training_day'],
                self.config['weekly_training_time']
            )
        }
    
    def _get_next_run_time(self, day: str, time_str: str) -> str:
        """计算下次运行时间"""
        days = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        target_day = days.get(day.lower(), 6)
        now = datetime.now()
        current_day = now.weekday()
        
        # 计算距离目标日期的天数
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        
        # 计算下次运行时间
        next_run = now + timedelta(days=days_ahead)
        hour, minute = map(int, time_str.split(':'))
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_run.isoformat()
    
    def _load_active_users(self):
        """加载活跃用户列表"""
        config_file = "./data/scheduler_config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_users = data.get('active_users', [])
                    print(f"✅ 加载了 {len(self.active_users)} 个活跃用户")
            except Exception as e:
                print(f"⚠️  加载配置失败: {e}")
                self.active_users = []
        else:
            # 默认用户
            self.active_users = ["test_user_001"]
            self._save_active_users()
    
    def _save_active_users(self):
        """保存活跃用户列表"""
        config_file = "./data/scheduler_config.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        data = {
            "active_users": self.active_users,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局调度器实例
_scheduler_instance = None

def get_scheduler() -> LoRAScheduler:
    """获取全局调度器实例（单例）"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = LoRAScheduler()
    return _scheduler_instance


# 测试代码
if __name__ == "__main__":
    scheduler = LoRAScheduler()
    
    print("="*60)
    print("LoRA训练调度器测试")
    print("="*60)
    print()
    
    # 添加测试用户
    scheduler.add_active_user("test_user_001")
    
    # 获取状态
    status = scheduler.get_status()
    print("调度器状态:")
    print(f"  运行中: {status['is_running']}")
    print(f"  活跃用户: {status['active_users']}")
    print(f"  训练队列: {status['training_queue']}")
    print(f"  下次画像更新: {status['next_profile_update']}")
    print(f"  下次LoRA训练: {status['next_lora_training']}")
    print()
    
    # 启动调度器
    scheduler.start()
    
    # 添加高优先级训练任务
    scheduler.add_training_task("test_user_001", priority="high")
    
    try:
        # 运行一段时间
        print("调度器运行中... (按Ctrl+C停止)")
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n收到停止信号")
        scheduler.stop()
        print("\n测试完成")
