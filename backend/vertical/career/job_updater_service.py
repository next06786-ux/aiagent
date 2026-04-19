"""
岗位数据更新服务

在应用启动时自动启动，后台定时更新热门岗位数据
"""

import asyncio
import logging
from typing import Optional
import threading

logger = logging.getLogger(__name__)


class JobUpdaterService:
    """岗位数据更新服务"""
    
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self):
        """启动服务"""
        if self.running:
            logger.warning("岗位更新服务已在运行")
            return
        
        logger.info("🚀 启动岗位数据更新服务")
        
        # 在新线程中运行事件循环
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self.running = True
        logger.info("✅ 岗位数据更新服务已启动")
    
    def _run_loop(self):
        """在独立线程中运行事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._background_update())
        except Exception as e:
            logger.error(f"后台更新任务异常: {e}")
        finally:
            self.loop.close()
    
    async def _background_update(self):
        """后台更新任务"""
        from backend.vertical.career.smart_job_crawler import smart_crawler
        
        logger.info("后台更新任务开始运行")
        
        # 启动智能爬虫的后台更新
        await smart_crawler.background_update_hot_jobs()
    
    def stop(self):
        """停止服务"""
        if not self.running:
            return
        
        logger.info("停止岗位数据更新服务")
        
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self.thread:
            self.thread.join(timeout=5)
        
        self.running = False
        logger.info("岗位数据更新服务已停止")


# 全局实例
job_updater_service = JobUpdaterService()


def start_job_updater():
    """启动岗位更新服务（在应用启动时调用）"""
    job_updater_service.start()


def stop_job_updater():
    """停止岗位更新服务（在应用关闭时调用）"""
    job_updater_service.stop()


if __name__ == "__main__":
    # 测试
    import time
    
    print("启动服务...")
    start_job_updater()
    
    print("服务运行中，按Ctrl+C停止")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止服务...")
        stop_job_updater()
