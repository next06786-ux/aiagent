"""
智能岗位爬虫 - 支持准实时更新

策略：
1. 分层缓存：热门岗位短缓存，冷门岗位长缓存
2. 请求限流：避免被封
3. 代理轮换：提高稳定性
4. 降级策略：爬虫失败时使用缓存数据
5. 异步更新：后台定时更新热门数据
"""

from typing import Dict, List, Any, Optional
import asyncio
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SmartJobCrawler:
    """
    智能岗位爬虫
    
    特点：
    - 分层缓存
    - 请求限流
    - 异步更新
    - 降级策略
    """
    
    def __init__(self):
        # 缓存配置
        self.cache_dir = Path("backend/data/job_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存时长（小时）
        self.cache_duration = {
            'hot': 1,      # 热门岗位：1小时
            'normal': 6,   # 普通岗位：6小时
            'cold': 24,    # 冷门岗位：24小时
            'stats': 12    # 统计数据：12小时
        }
        
        # 查询频率统计（用于判断热度）
        self.query_count = defaultdict(int)
        self.query_history = []
        
        # 请求限流
        self.last_request_time = {}
        self.min_request_interval = 3  # 最小请求间隔（秒）
        
        # 导入爬虫
        from backend.vertical.career.real_job_data_integration import (
            real_job_integration
        )
        self.crawler = real_job_integration
        
        # Neo4j存储
        from backend.vertical.career.job_neo4j_storage import job_storage
        self.storage = job_storage
    
    def _get_cache_key(self, keyword: str, location: str) -> str:
        """生成缓存key"""
        return f"{keyword}_{location}".replace(" ", "_")
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_hotness(self, cache_key: str) -> str:
        """
        判断岗位热度
        
        Returns:
            'hot' | 'normal' | 'cold'
        """
        # 统计最近1小时的查询次数
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        recent_queries = [
            q for q in self.query_history
            if q['time'] > one_hour_ago and q['key'] == cache_key
        ]
        
        count = len(recent_queries)
        
        if count >= 5:
            return 'hot'
        elif count >= 2:
            return 'normal'
        else:
            return 'cold'
    
    def _is_cache_valid(self, cache_file: Path, hotness: str) -> bool:
        """检查缓存是否有效"""
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data['cached_at'])
            cache_duration = self.cache_duration[hotness]
            
            if datetime.now() - cached_time < timedelta(hours=cache_duration):
                return True
        
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
        
        return False
    
    def _load_cache(self, cache_file: Path) -> Optional[List[Dict]]:
        """加载缓存"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"从缓存加载 {len(data['jobs'])} 个岗位")
            return data['jobs']
        
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None
    
    def _save_cache(self, cache_file: Path, jobs: List[Dict]):
        """保存缓存"""
        try:
            data = {
                'cached_at': datetime.now().isoformat(),
                'jobs': jobs
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"缓存 {len(jobs)} 个岗位")
        
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    async def _rate_limit(self, source: str):
        """请求限流"""
        last_time = self.last_request_time.get(source, 0)
        elapsed = time.time() - last_time
        
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            # 添加随机抖动，避免规律性
            wait_time += random.uniform(0, 1)
            
            logger.info(f"限流等待 {wait_time:.1f}秒")
            await asyncio.sleep(wait_time)
        
        self.last_request_time[source] = time.time()
    
    async def search_jobs(
        self,
        keyword: str,
        location: str = "北京",
        limit: int = 20,
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        智能搜索岗位
        
        Args:
            keyword: 搜索关键词
            location: 城市
            limit: 返回数量
            force_refresh: 强制刷新（忽略缓存）
        
        Returns:
            岗位列表
        """
        cache_key = self._get_cache_key(keyword, location)
        cache_file = self._get_cache_file(cache_key)
        
        # 记录查询
        self.query_count[cache_key] += 1
        self.query_history.append({
            'key': cache_key,
            'time': datetime.now()
        })
        
        # 清理旧的查询记录（保留最近24小时）
        cutoff = datetime.now() - timedelta(hours=24)
        self.query_history = [
            q for q in self.query_history
            if q['time'] > cutoff
        ]
        
        # 判断热度
        hotness = self._get_hotness(cache_key)
        logger.info(f"岗位热度: {hotness} - {keyword} @ {location}")
        
        # 检查缓存
        if not force_refresh and self._is_cache_valid(cache_file, hotness):
            cached_jobs = self._load_cache(cache_file)
            if cached_jobs:
                return cached_jobs[:limit]
        
        # 缓存失效或强制刷新，爬取新数据
        try:
            # 请求限流
            await self._rate_limit('boss_zhipin')
            
            # 爬取数据
            logger.info(f"开始爬取: {keyword} @ {location}")
            jobs = self.crawler.search_jobs(keyword, location, limit)
            
            if jobs:
                # 转换为字典格式
                jobs_dict = [job.to_dict() for job in jobs]
                
                # 保存到Neo4j
                try:
                    save_result = self.storage.save_jobs_batch(jobs_dict)
                    logger.info(f"保存到Neo4j: 成功{save_result['success']}, 失败{save_result['failed']}")
                except Exception as e:
                    logger.warning(f"保存到Neo4j失败: {e}")
                
                # 保存缓存
                self._save_cache(cache_file, jobs_dict)
                
                return jobs_dict
            else:
                # 爬取失败，尝试使用旧缓存
                logger.warning("爬取失败，尝试使用旧缓存")
                cached_jobs = self._load_cache(cache_file)
                if cached_jobs:
                    return cached_jobs[:limit]
        
        except Exception as e:
            logger.error(f"爬取异常: {e}")
            
            # 降级：使用旧缓存
            cached_jobs = self._load_cache(cache_file)
            if cached_jobs:
                logger.info("使用旧缓存数据")
                return cached_jobs[:limit]
        
        # 所有方法都失败，返回空列表
        logger.error("无法获取岗位数据")
        return []
    
    async def get_market_stats(
        self,
        keyword: str,
        location: str = "北京",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取市场统计数据
        
        统计数据使用更长的缓存时间
        """
        cache_key = f"stats_{self._get_cache_key(keyword, location)}"
        cache_file = self._get_cache_file(cache_key)
        
        # 检查缓存
        if not force_refresh and self._is_cache_valid(cache_file, 'stats'):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("从缓存加载市场统计")
                return data['stats']
            except:
                pass
        
        # 获取岗位数据
        jobs_dict = await self.search_jobs(keyword, location, limit=100)
        
        if not jobs_dict:
            return {
                'total_jobs': 0,
                'avg_salary': 0,
                'error': '无法获取数据'
            }
        
        # 计算统计
        stats = self._calculate_stats(jobs_dict)
        
        # 保存缓存
        try:
            data = {
                'cached_at': datetime.now().isoformat(),
                'stats': stats
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存统计缓存失败: {e}")
        
        return stats
    
    def _calculate_stats(self, jobs: List[Dict]) -> Dict[str, Any]:
        """计算统计数据"""
        if not jobs:
            return {}
        
        # 薪资统计
        salaries = [j['salary_avg'] for j in jobs if j.get('salary_avg', 0) > 0]
        avg_salary = sum(salaries) / len(salaries) if salaries else 0
        
        # 技能统计
        skill_count = defaultdict(int)
        for job in jobs:
            for skill in job.get('required_skills', []):
                skill_count[skill] += 1
        
        top_skills = sorted(
            skill_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # 公司统计
        company_count = defaultdict(int)
        for job in jobs:
            company_count[job.get('company', '')] += 1
        
        top_companies = sorted(
            company_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_jobs': len(jobs),
            'avg_salary': round(avg_salary, 1),
            'top_skills': [
                {'skill': s, 'count': c}
                for s, c in top_skills
            ],
            'top_companies': [
                {'company': c, 'count': cnt}
                for c, cnt in top_companies
            ],
            'updated_at': datetime.now().isoformat()
        }
    
    async def background_update_hot_jobs(self):
        """
        后台任务：定时更新热门岗位
        
        每小时运行一次，更新查询频率高的岗位
        """
        while True:
            try:
                logger.info("开始后台更新热门岗位")
                
                # 找出热门查询
                hot_queries = [
                    key for key, count in self.query_count.items()
                    if count >= 5
                ]
                
                logger.info(f"发现 {len(hot_queries)} 个热门查询")
                
                # 更新热门岗位
                for cache_key in hot_queries[:10]:  # 限制更新数量
                    try:
                        # 解析cache_key
                        parts = cache_key.split('_')
                        if len(parts) >= 2:
                            keyword = '_'.join(parts[:-1])
                            location = parts[-1]
                            
                            # 强制刷新
                            await self.search_jobs(
                                keyword,
                                location,
                                limit=20,
                                force_refresh=True
                            )
                            
                            logger.info(f"更新热门岗位: {keyword} @ {location}")
                            
                            # 避免请求过快
                            await asyncio.sleep(5)
                    
                    except Exception as e:
                        logger.error(f"更新失败: {e}")
                
                # 重置计数器
                self.query_count.clear()
                
                logger.info("热门岗位更新完成")
            
            except Exception as e:
                logger.error(f"后台更新异常: {e}")
            
            # 每小时运行一次
            await asyncio.sleep(3600)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        # 统计各类缓存
        hot_count = 0
        normal_count = 0
        cold_count = 0
        
        for f in cache_files:
            cache_key = f.stem
            if cache_key.startswith('stats_'):
                continue
            
            hotness = self._get_hotness(cache_key)
            if hotness == 'hot':
                hot_count += 1
            elif hotness == 'normal':
                normal_count += 1
            else:
                cold_count += 1
        
        return {
            'total_files': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'hot_jobs': hot_count,
            'normal_jobs': normal_count,
            'cold_jobs': cold_count,
            'query_count': dict(self.query_count)
        }


# 全局实例
smart_crawler = SmartJobCrawler()


async def start_background_updater():
    """启动后台更新任务"""
    logger.info("启动后台更新任务")
    await smart_crawler.background_update_hot_jobs()


if __name__ == "__main__":
    # 测试
    async def test():
        crawler = SmartJobCrawler()
        
        print("=" * 60)
        print("测试智能爬虫")
        print("=" * 60)
        
        # 第一次查询（会爬取）
        print("\n第一次查询...")
        jobs1 = await crawler.search_jobs("Python工程师", "北京", 10)
        print(f"获取到 {len(jobs1)} 个岗位")
        
        # 第二次查询（使用缓存）
        print("\n第二次查询（应该使用缓存）...")
        jobs2 = await crawler.search_jobs("Python工程师", "北京", 10)
        print(f"获取到 {len(jobs2)} 个岗位")
        
        # 查看缓存统计
        print("\n缓存统计:")
        stats = crawler.get_cache_stats()
        print(f"  缓存文件数: {stats['total_files']}")
        print(f"  缓存大小: {stats['total_size_mb']} MB")
        print(f"  热门岗位: {stats['hot_jobs']}")
        print(f"  普通岗位: {stats['normal_jobs']}")
        print(f"  冷门岗位: {stats['cold_jobs']}")
        
        # 市场统计
        print("\n市场统计:")
        market_stats = await crawler.get_market_stats("Python工程师", "北京")
        print(f"  总岗位数: {market_stats['total_jobs']}")
        print(f"  平均薪资: {market_stats['avg_salary']}万/年")
        print(f"  热门技能: {[s['skill'] for s in market_stats['top_skills'][:5]]}")
    
    asyncio.run(test())
