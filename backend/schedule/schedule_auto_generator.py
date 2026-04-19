"""
智能日程自动生成器
AI后台异步定时自动生成用户日程
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio

from backend.schedule.schedule_task_manager import ScheduleTaskManager
from backend.schedule.schedule_config import ScheduleAutoConfig
from backend.database.db_manager import db_manager


class ScheduleAutoGenerator:
    """智能日程自动生成器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.task_manager = ScheduleTaskManager()
        self._is_running = False
        
    def start(self):
        """启动定时任务调度器"""
        if self._is_running:
            print("[日程自动生成] 调度器已在运行")
            return
        
        print("\n" + "="*60)
        print("🤖 智能日程自动生成器启动")
        print("="*60)
        
        config = ScheduleAutoConfig.to_dict()
        
        # 1. 每天凌晨自动生成次日日程
        if config['daily_generation']['enabled']:
            self.scheduler.add_job(
                self._generate_daily_schedules,
                CronTrigger(
                    hour=config['daily_generation']['hour'],
                    minute=config['daily_generation']['minute']
                ),
                id='daily_schedule_generation',
                name='每日日程自动生成',
                replace_existing=True
            )
            print(f"✓ 定时任务已添加: 每天 {config['daily_generation']['hour']:02d}:{config['daily_generation']['minute']:02d} 自动生成次日日程")
        
        # 2. 每周日晚上生成下周计划
        if config['weekly_generation']['enabled']:
            self.scheduler.add_job(
                self._generate_weekly_schedules,
                CronTrigger(
                    day_of_week=config['weekly_generation']['day'],
                    hour=config['weekly_generation']['hour'],
                    minute=config['weekly_generation']['minute']
                ),
                id='weekly_schedule_generation',
                name='每周日程自动生成',
                replace_existing=True
            )
            print(f"✓ 定时任务已添加: 每周{config['weekly_generation']['day']} {config['weekly_generation']['hour']:02d}:{config['weekly_generation']['minute']:02d} 生成下周计划")
        
        # 3. 定期检查是否需要重新生成（数据变化触发）
        if config['update_trigger']['enabled']:
            # 每小时检查一次（在每小时的第0分钟）
            interval = config['update_trigger']['check_interval_minutes']
            if interval >= 60:
                # 如果间隔大于等于60分钟，使用小时触发器
                self.scheduler.add_job(
                    self._check_and_regenerate,
                    CronTrigger(hour='*', minute=0),  # 每小时的第0分钟
                    id='schedule_regeneration_check',
                    name='日程重新生成检查',
                    replace_existing=True
                )
                print(f"✓ 定时任务已添加: 每小时检查数据变化")
            else:
                # 如果间隔小于60分钟，使用分钟触发器
                self.scheduler.add_job(
                    self._check_and_regenerate,
                    CronTrigger(minute=f'*/{interval}'),
                    id='schedule_regeneration_check',
                    name='日程重新生成检查',
                    replace_existing=True
                )
                print(f"✓ 定时任务已添加: 每{interval}分钟检查数据变化")
        
        # 启动调度器
        self.scheduler.start()
        self._is_running = True
        
        print("="*60)
        print("✅ 智能日程自动生成器已启动")
        print("="*60 + "\n")
    
    def stop(self):
        """停止定时任务调度器"""
        if not self._is_running:
            return
        
        self.scheduler.shutdown()
        self._is_running = False
        print("[日程自动生成] 调度器已停止")
    
    async def _generate_daily_schedules(self):
        """为所有活跃用户生成次日日程"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始自动生成次日日程...")
        
        try:
            # 获取所有活跃用户
            active_users = await self._get_active_users()
            print(f"[日程生成] 发现 {len(active_users)} 个活跃用户")
            
            # 为每个用户异步生成日程
            tasks = []
            for user_id in active_users:
                task = self._generate_schedule_for_user(
                    user_id,
                    target_date=datetime.now().date() + timedelta(days=1)
                )
                tasks.append(task)
            
            # 并发执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            success_count = sum(1 for r in results if r is True)
            print(f"[日程生成] 完成: {success_count}/{len(active_users)} 个用户")
            
        except Exception as e:
            print(f"[日程生成] 错误: {e}")
            import traceback
            traceback.print_exc()
    
    async def _generate_weekly_schedules(self):
        """为所有活跃用户生成下周计划"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始自动生成下周计划...")
        
        try:
            active_users = await self._get_active_users()
            print(f"[周计划生成] 发现 {len(active_users)} 个活跃用户")
            
            tasks = []
            for user_id in active_users:
                # 生成下周7天的日程
                for days_ahead in range(1, 8):
                    target_date = datetime.now().date() + timedelta(days=days_ahead)
                    task = self._generate_schedule_for_user(user_id, target_date)
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            print(f"[周计划生成] 完成: {success_count}/{len(tasks)} 个日程")
            
        except Exception as e:
            print(f"[周计划生成] 错误: {e}")
    
    async def _check_and_regenerate(self):
        """检查数据变化，必要时重新生成日程"""
        try:
            # 获取最近有数据更新的用户
            users_with_updates = await self._get_users_with_recent_updates()
            
            if not users_with_updates:
                return
            
            print(f"[日程更新] 检测到 {len(users_with_updates)} 个用户有数据变化")
            
            tasks = []
            for user_id in users_with_updates:
                # 重新生成今天和明天的日程
                for days_ahead in [0, 1]:
                    target_date = datetime.now().date() + timedelta(days=days_ahead)
                    task = self._generate_schedule_for_user(user_id, target_date)
                    tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            print(f"[日程更新] 错误: {e}")
    
    async def _generate_schedule_for_user(
        self,
        user_id: str,
        target_date: datetime.date
    ) -> bool:
        """为单个用户生成日程"""
        try:
            # 使用异步任务管理器生成日程
            task_id = await self.task_manager.create_schedule_generation_task(
                user_id=user_id,
                target_date=target_date.isoformat(),
                auto_generated=True  # 标记为自动生成
            )
            
            print(f"[日程生成] 用户 {user_id[:8]}... 日期 {target_date} - 任务ID: {task_id}")
            return True
            
        except Exception as e:
            print(f"[日程生成] 用户 {user_id[:8]}... 失败: {e}")
            return False
    
    async def _get_active_users(self) -> List[str]:
        """获取活跃用户列表"""
        try:
            # 从数据库获取最近7天有活动的用户
            users = db_manager.get_active_users(days=7)
            return [user.user_id for user in users]
        except Exception as e:
            print(f"[用户查询] 获取活跃用户失败: {e}")
            # 返回默认测试用户
            return ["2c2139f7-bab4-483d-9882-ae83ce8734cd"]
    
    async def _get_users_with_recent_updates(self) -> List[str]:
        """获取最近有数据更新的用户"""
        try:
            # 检查最近1小时内有健康记录、任务更新等的用户
            users = db_manager.get_users_with_recent_updates(hours=1)
            return [user.user_id for user in users]
        except Exception as e:
            print(f"[用户查询] 获取更新用户失败: {e}")
            return []
    
    def get_scheduler_status(self) -> dict:
        """获取调度器状态"""
        if not self._is_running:
            return {
                "running": False,
                "jobs": []
            }
        
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "running": True,
            "jobs": jobs
        }


# 全局单例
_auto_generator: Optional[ScheduleAutoGenerator] = None


def get_auto_generator() -> ScheduleAutoGenerator:
    """获取全局自动生成器实例"""
    global _auto_generator
    if _auto_generator is None:
        _auto_generator = ScheduleAutoGenerator()
    return _auto_generator


def start_auto_generator():
    """启动自动生成器"""
    generator = get_auto_generator()
    generator.start()


def stop_auto_generator():
    """停止自动生成器"""
    generator = get_auto_generator()
    generator.stop()
