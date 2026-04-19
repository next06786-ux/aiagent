"""
真实岗位数据缓存加载器

从预先爬取的数据文件加载真实岗位数据
避免实时爬取带来的反爬问题
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 数据缓存目录
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "job_cache"


class RealJobCacheLoader:
    """真实岗位数据缓存加载器"""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"岗位缓存目录: {self.cache_dir}")
    
    def load_jobs(self, keyword: str, location: str, limit: int = 20) -> List[Dict]:
        """
        从缓存加载岗位数据
        
        Args:
            keyword: 搜索关键词
            location: 城市
            limit: 返回数量
        
        Returns:
            岗位数据列表
        """
        # 构建缓存文件名
        cache_file = self.cache_dir / f"{keyword}_{location}.json"
        
        if not cache_file.exists():
            logger.warning(f"缓存文件不存在: {cache_file}")
            return []
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            jobs = data.get('jobs', [])
            
            # 标记为真实数据
            for job in jobs:
                if job.get('source') == 'mock_data':
                    job['source'] = 'cached_real_data'
            
            logger.info(f"从缓存加载 {len(jobs)} 个岗位: {keyword} @ {location}")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return []
    
    def save_jobs(self, keyword: str, location: str, jobs: List[Dict]):
        """
        保存岗位数据到缓存
        
        Args:
            keyword: 搜索关键词
            location: 城市
            jobs: 岗位数据列表
        """
        cache_file = self.cache_dir / f"{keyword}_{location}.json"
        
        try:
            data = {
                'cached_at': datetime.now().isoformat(),
                'keyword': keyword,
                'location': location,
                'count': len(jobs),
                'jobs': jobs
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存 {len(jobs)} 个岗位到缓存: {cache_file}")
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def list_cached_queries(self) -> List[Dict[str, str]]:
        """列出所有缓存的查询"""
        cached = []
        
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.stem.startswith("stats_"):
                continue
            
            parts = cache_file.stem.split("_")
            if len(parts) >= 2:
                keyword = "_".join(parts[:-1])
                location = parts[-1]
                
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    cached.append({
                        'keyword': keyword,
                        'location': location,
                        'count': len(data.get('jobs', [])),
                        'cached_at': data.get('cached_at', 'unknown')
                    })
                except:
                    pass
        
        return cached
    
    def get_statistics(self, keyword: str, location: str) -> Optional[Dict]:
        """获取统计数据"""
        stats_file = self.cache_dir / f"stats_{keyword}_{location}.json"
        
        if not stats_file.exists():
            return None
        
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
            return None
    
    def save_statistics(self, keyword: str, location: str, stats: Dict):
        """保存统计数据"""
        stats_file = self.cache_dir / f"stats_{keyword}_{location}.json"
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存统计数据: {stats_file}")
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")


# 全局实例
real_job_cache_loader = RealJobCacheLoader()


if __name__ == "__main__":
    # 测试
    loader = RealJobCacheLoader()
    
    print("=" * 60)
    print("缓存的查询列表")
    print("=" * 60)
    
    cached = loader.list_cached_queries()
    for item in cached:
        print(f"{item['keyword']} @ {item['location']}: {item['count']}个岗位")
    
    print(f"\n总计: {len(cached)} 个缓存查询")
    
    # 测试加载
    if cached:
        first = cached[0]
        print(f"\n测试加载: {first['keyword']} @ {first['location']}")
        jobs = loader.load_jobs(first['keyword'], first['location'], 3)
        
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.get('title')}")
            print(f"   公司: {job.get('company')}")
            print(f"   薪资: {job.get('salary_min')}-{job.get('salary_max')}万")
