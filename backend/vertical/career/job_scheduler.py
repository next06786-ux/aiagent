"""
岗位数据定时调度器

功能：
1. 每小时更新热门岗位
2. 每天凌晨2点更新全量数据
3. 每周清理过期数据
"""

import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import List, Dict
import schedule
import threading

logger = logging.getLogger(__name__)


class JobScheduler:
    """岗位数据定时调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
        # 热门关键词列表
        self.hot_keywords = [
            "Python工程师",
            "Java工程师",
            "前端工程师",
            "产品经理",
            "数据分析师",
            "算法工程师",
            "测试工程师",
            "运维工程师"
        ]
        
        # 热门城市
        self.hot_cities = ["北京", "上海", "深圳", "杭州", "广州"]
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return
        
        logger.info("🚀 启动岗位数据调度器")
        
        # 配置定时任务
        self._setup_schedules()
        
        # 在新线程中运行
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("✅ 岗位数据调度器已启动")
    
    def _setup_schedules(self):
        """配置定时任务"""
        
        # 每小时更新热门岗位
        schedule.every().hour.at(":00").do(self._update_hot_jobs)
        
        # 每天凌晨2点全量更新
        schedule.every().day.at("02:00").do(self._full_update)
        
        # 每周日凌晨3点清理过期数据
        schedule.every().sunday.at("03:00").do(self._cleanup_old_data)
        
        # 每天早上8点更新市场统计
        schedule.every().day.at("08:00").do(self._update_market_stats)
        
        logger.info("定时任务配置完成")
    
    def _run_scheduler(self):
        """运行调度器"""
        logger.info("调度器开始运行")
        
        while self.running:
            try:
                schedule.run_pending()
                asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器异常: {e}")
    
    def _update_hot_jobs(self):
        """更新热门岗位（每小时）"""
        logger.info("⏰ 开始更新热门岗位")
        
        try:
            # 在新的事件循环中运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_update_hot_jobs())
            loop.close()
            
            logger.info("✅ 热门岗位更新完成")
        except Exception as e:
            logger.error(f"更新热门岗位失败: {e}")
    
    async def _async_update_hot_jobs(self):
        """异步更新热门岗位"""
        from backend.vertical.career.smart_job_crawler import smart_crawler
        
        # 只更新前3个热门关键词和前2个城市
        for keyword in self.hot_keywords[:3]:
            for city in self.hot_cities[:2]:
                try:
                    jobs = await smart_crawler.search_jobs(
                        keyword,
                        city,
                        limit=20,
                        force_refresh=True
                    )
                    logger.info(f"更新: {keyword} @ {city} - {len(jobs)}个岗位")
                    
                    # 避免请求过快
                    await asyncio.sleep(5)
                
                except Exception as e:
                    logger.error(f"更新失败 {keyword} @ {city}: {e}")
    
    def _full_update(self):
        """全量更新（每天凌晨2点）"""
        logger.info("⏰ 开始全量更新岗位数据")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_full_update())
            loop.close()
            
            logger.info("✅ 全量更新完成")
        except Exception as e:
            logger.error(f"全量更新失败: {e}")
    
    async def _async_full_update(self):
        """异步全量更新"""
        from backend.vertical.career.smart_job_crawler import smart_crawler
        
        total_jobs = 0
        
        # 更新所有热门关键词和城市
        for keyword in self.hot_keywords:
            for city in self.hot_cities:
                try:
                    jobs = await smart_crawler.search_jobs(
                        keyword,
                        city,
                        limit=50,
                        force_refresh=True
                    )
                    total_jobs += len(jobs)
                    logger.info(f"更新: {keyword} @ {city} - {len(jobs)}个岗位")
                    
                    # 避免请求过快
                    await asyncio.sleep(10)
                
                except Exception as e:
                    logger.error(f"更新失败 {keyword} @ {city}: {e}")
        
        logger.info(f"全量更新完成，共更新 {total_jobs} 个岗位")
    
    def _cleanup_old_data(self):
        """清理过期数据（每周日凌晨3点）"""
        logger.info("⏰ 开始清理过期数据")
        
        try:
            from backend.vertical.career.job_neo4j_storage import job_storage
            
            # 清理30天前的数据
            job_storage.clean_old_jobs(days=30)
            
            logger.info("✅ 过期数据清理完成")
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    def _update_market_stats(self):
        """更新市场统计（每天早上8点）"""
        logger.info("⏰ 开始更新市场统计")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_update_market_stats())
            loop.close()
            
            logger.info("✅ 市场统计更新完成")
        except Exception as e:
            logger.error(f"更新市场统计失败: {e}")
    
    async def _async_update_market_stats(self):
        """异步更新市场统计"""
        from backend.vertical.career.smart_job_crawler import smart_crawler
        
        # 为每个热门关键词生成市场统计
        for keyword in self.hot_keywords:
            try:
                stats = await smart_crawler.get_market_stats(
                    keyword,
                    "北京",
                    force_refresh=True
                )
                logger.info(
                    f"市场统计: {keyword} - "
                    f"{stats.get('total_jobs', 0)}个岗位, "
                    f"平均薪资{stats.get('avg_salary', 0)}万/年"
                )
                
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"更新市场统计失败 {keyword}: {e}")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        logger.info("停止岗位数据调度器")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("岗位数据调度器已停止")
    
    def run_task_now(self, task_name: str):
        """立即运行指定任务（用于测试）"""
        tasks = {
            'hot': self._update_hot_jobs,
            'full': self._full_update,
            'cleanup': self._cleanup_old_data,
            'stats': self._update_market_stats
        }
        
        task = tasks.get(task_name)
        if task:
            logger.info(f"立即运行任务: {task_name}")
            task()
        else:
            logger.warning(f"未知任务: {task_name}")


# 全局实例
job_scheduler = JobScheduler()


def start_job_scheduler():
    """启动岗位数据调度器（在应用启动时调用）"""
    job_scheduler.start()


def stop_job_scheduler():
    """停止岗位数据调度器（在应用关闭时调用）"""
    job_scheduler.stop()


if __name__ == "__main__":
    # 测试
    import time
    
    print("启动调度器...")
    start_job_scheduler()
    
    print("\n调度器运行中...")
    print("定时任务:")
    print("  - 每小时更新热门岗位")
    print("  - 每天凌晨2点全量更新")
    print("  - 每周日凌晨3点清理过期数据")
    print("  - 每天早上8点更新市场统计")
    print("\n按Ctrl+C停止")
    
    try:
        # 测试：立即运行一次热门岗位更新
        print("\n测试：立即运行热门岗位更新...")
        job_scheduler.run_task_now('hot')
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止调度器...")
        stop_job_scheduler()
