"""
集成GitHub开源爬虫 (job-crawler)
项目地址: https://github.com/tengx7/job-crawler

支持平台:
- BOSS直聘
- 智联招聘
- 前程无忧
- 拉勾网
"""
import sys
import os
import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 添加job-crawler到Python路径
JOB_CRAWLER_PATH = os.path.join(os.path.dirname(__file__), "../../../job-crawler/backend")
if os.path.exists(JOB_CRAWLER_PATH) and JOB_CRAWLER_PATH not in sys.path:
    sys.path.insert(0, JOB_CRAWLER_PATH)
    logger.info(f"已添加job-crawler路径: {JOB_CRAWLER_PATH}")


@dataclass
class JobData:
    """统一的岗位数据格式"""
    job_id: str
    title: str
    company: str
    salary_min: float
    salary_max: float
    salary_avg: float
    required_skills: List[str]
    experience_required: int
    education_required: str
    location: str
    industry: str
    company_size: str
    job_description: str
    source: str
    source_url: str


class GitHubCrawlerAdapter:
    """GitHub开源爬虫适配器"""
    
    def __init__(self):
        self.available = False
        self._init_crawler()
    
    def _init_crawler(self):
        """初始化爬虫模块"""
        try:
            # 尝试导入job-crawler模块
            from app.crawler.sites import get_site_adapter
            from app.crawler.anti_crawl import AntiCrawl
            
            self.get_site_adapter = get_site_adapter
            self.anti_crawl = AntiCrawl()
            self.available = True
            logger.info("✓ GitHub开源爬虫初始化成功")
            
        except ImportError as e:
            logger.warning(f"⚠ GitHub开源爬虫不可用: {e}")
            logger.warning(f"请确保job-crawler项目位于: {JOB_CRAWLER_PATH}")
            self.available = False
    
    def search_jobs(
        self,
        keyword: str,
        location: str = "北京",
        limit: int = 20,
        platforms: List[str] = None
    ) -> List[JobData]:
        """
        搜索岗位
        
        Args:
            keyword: 搜索关键词
            location: 城市
            limit: 返回数量
            platforms: 平台列表 ['boss', 'zhilian', 'qianchen', 'lagou']
        """
        if not self.available:
            logger.warning("GitHub爬虫不可用，返回空列表")
            return []
        
        if platforms is None:
            platforms = ['boss', 'zhilian']  # 默认使用BOSS和智联
        
        # 使用asyncio运行异步爬虫
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            jobs = loop.run_until_complete(
                self._async_search(keyword, location, limit, platforms)
            )
            return jobs
        finally:
            loop.close()
    
    async def _async_search(
        self,
        keyword: str,
        location: str,
        limit: int,
        platforms: List[str]
    ) -> List[JobData]:
        """异步搜索岗位"""
        all_jobs = []
        
        for platform in platforms:
            try:
                adapter = self.get_site_adapter(platform)
                if not adapter:
                    logger.warning(f"平台 {platform} 适配器不可用")
                    continue
                
                # 构建规则配置
                rule_config = {
                    "list_page": {
                        "max_pages": max(1, limit // 10),  # 每页约10条
                        "item_selector": ".job-card-wrapper",
                        "fields": {}
                    },
                    "anti_crawl": {
                        "min_delay": 2,
                        "max_delay": 4
                    }
                }
                
                logger.info(f"开始从 {platform} 爬取: {keyword} @ {location}")
                
                # 调用适配器爬取
                items = await adapter.fetch(keyword, location, rule_config, self.anti_crawl)
                
                logger.info(f"原始数据: {len(items)} 条")
                
                # 转换为统一格式
                for item in items[:limit]:
                    logger.debug(f"处理岗位: {item.get('title', 'unknown')}")
                    job = self._convert_to_job_data(item, platform)
                    if job:
                        all_jobs.append(job)
                
                logger.info(f"✓ 从 {platform} 获取到 {len(items)} 个岗位，成功转换 {len(all_jobs)} 个")
                
                if len(all_jobs) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"从 {platform} 爬取失败: {e}")
                continue
        
        return all_jobs[:limit]
    
    def _convert_to_job_data(self, item: dict, platform: str) -> Optional[JobData]:
        """转换为统一的岗位数据格式"""
        try:
            # 解析薪资
            salary_raw = item.get("salary_raw", "")
            salary_min, salary_max = self._parse_salary(salary_raw)
            
            # 提取技能
            skills = item.get("skills", [])
            if not skills and item.get("title"):
                skills = self._extract_skills_from_title(item["title"])
            
            # 解析经验要求
            experience = self._parse_experience(item.get("experience", ""))
            
            return JobData(
                job_id=item.get("source_id", ""),
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                salary_min=salary_min,
                salary_max=salary_max,
                salary_avg=(salary_min + salary_max) / 2,
                required_skills=skills,
                experience_required=experience,
                education_required=item.get("education", ""),
                location=item.get("city", ""),
                industry="",
                company_size="",
                job_description="",
                source=f"github_crawler_{platform}",
                source_url=item.get("url", "")
            )
        except Exception as e:
            logger.error(f"转换岗位数据失败: {e}")
            return None
    
    def _parse_salary(self, salary_raw: str) -> tuple:
        """解析薪资字符串"""
        import re
        
        # 匹配 "15-25K" "15K-25K" "1.5万-2.5万" 等格式
        patterns = [
            r'(\d+\.?\d*)[kK万]-(\d+\.?\d*)[kK万]',
            r'(\d+\.?\d*)-(\d+\.?\d*)[kK万]',
            r'(\d+)-(\d+)[kK]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, salary_raw)
            if match:
                min_sal = float(match.group(1))
                max_sal = float(match.group(2))
                
                # 统一转换为万元
                if 'K' in salary_raw or 'k' in salary_raw:
                    min_sal = min_sal / 10
                    max_sal = max_sal / 10
                
                return min_sal, max_sal
        
        return 0, 0
    
    def _extract_skills_from_title(self, title: str) -> List[str]:
        """从职位标题提取技能"""
        common_skills = [
            'Python', 'Java', 'JavaScript', 'Go', 'C++', 'PHP', 'Ruby',
            'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'AWS', 'Linux', 'Git',
            '机器学习', '深度学习', '数据分析', '算法'
        ]
        
        skills = []
        title_upper = title.upper()
        for skill in common_skills:
            if skill.upper() in title_upper:
                skills.append(skill)
        
        return skills
    
    def _parse_experience(self, exp_str: str) -> int:
        """解析经验要求"""
        import re
        match = re.search(r'(\d+)', exp_str)
        if match:
            return int(match.group(1))
        
        if '不限' in exp_str or '应届' in exp_str:
            return 0
        return 1


# 创建全局实例
github_crawler = GitHubCrawlerAdapter()


# 测试函数
def test_crawler():
    """测试爬虫"""
    import logging
    import sys
    
    # 设置UTF-8编码
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("=" * 60)
    print("测试GitHub开源爬虫")
    print("=" * 60)
    
    if not github_crawler.available:
        print("\n✗ 爬虫不可用")
        print(f"请确保job-crawler项目位于: {JOB_CRAWLER_PATH}")
        return
    
    print("\n✓ 爬虫初始化成功")
    print("\n开始爬取: Python工程师 @ 北京")
    
    jobs = github_crawler.search_jobs(
        keyword="Python工程师",
        location="北京",
        limit=5,
        platforms=['boss']  # 只测试BOSS直聘
    )
    
    print(f"\n获取到 {len(jobs)} 个岗位:\n")
    
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.title}")
        print(f"   公司: {job.company}")
        print(f"   薪资: {job.salary_min}-{job.salary_max}万")
        print(f"   地点: {job.location}")
        print(f"   技能: {', '.join(job.required_skills)}")
        print(f"   来源: {job.source}")
        print(f"   链接: {job.source_url}")
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    test_crawler()
