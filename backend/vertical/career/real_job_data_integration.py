"""
真实岗位数据集成
支持多个招聘平台的数据获取和统一处理

支持的平台：
1. BOSS直聘 - 通过API或爬虫
2. 拉勾网 - 通过API
3. 智联招聘 - 通过爬虫
4. 前程无忧 - 通过爬虫

注意：
- 使用官方API优先
- 遵守robots.txt和使用条款
- 控制请求频率，避免被封
- 数据缓存，减少重复请求
"""

from typing import Dict, List, Any, Optional
import re
import json
import time
import requests
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class JobData:
    """统一的岗位数据格式"""
    job_id: str
    title: str
    company: str
    company_id: str
    salary_min: float  # 万/年
    salary_max: float  # 万/年
    salary_avg: float  # 万/年
    required_skills: List[str]
    experience_required: int  # 年限
    education_required: str
    location: str
    district: str  # 区域（如"朝阳区"）
    industry: str
    company_size: str
    company_stage: str  # 融资阶段
    job_description: str
    welfare_tags: List[str]  # 福利标签
    source: str  # 数据来源
    source_url: str  # 原始链接
    crawled_at: str  # 爬取时间
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class JobDataCache:
    """岗位数据缓存"""
    
    def __init__(self, cache_hours: int = 24):
        self.cache: Dict[str, Dict] = {}
        self.cache_hours = cache_hours
    
    def _make_key(self, keyword: str, location: str, source: str) -> str:
        """生成缓存key"""
        text = f"{keyword}_{location}_{source}"
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, keyword: str, location: str, source: str) -> Optional[List[JobData]]:
        """获取缓存"""
        key = self._make_key(keyword, location, source)
        cached = self.cache.get(key)
        
        if not cached:
            return None
        
        # 检查是否过期
        cached_time = datetime.fromisoformat(cached['time'])
        if datetime.now() - cached_time > timedelta(hours=self.cache_hours):
            del self.cache[key]
            return None
        
        # 反序列化
        jobs = [JobData(**job) for job in cached['jobs']]
        logger.info(f"从缓存获取 {len(jobs)} 个岗位 - {keyword} @ {location}")
        return jobs
    
    def set(self, keyword: str, location: str, source: str, jobs: List[JobData]):
        """设置缓存"""
        key = self._make_key(keyword, location, source)
        self.cache[key] = {
            'time': datetime.now().isoformat(),
            'jobs': [job.to_dict() for job in jobs]
        }
        logger.info(f"缓存 {len(jobs)} 个岗位 - {keyword} @ {location}")


class BOSSZhipinCrawler:
    """
    BOSS直聘数据获取
    
    方案1：使用官方API（需要申请）
    方案2：使用爬虫（需要处理反爬）
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://www.zhipin.com"
        self.api_url = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
    
    def search_jobs(
        self,
        keyword: str,
        location: str = "北京",
        limit: int = 20
    ) -> List[JobData]:
        """
        搜索岗位
        
        Args:
            keyword: 搜索关键词
            location: 城市
            limit: 返回数量
        """
        jobs = []
        
        # 城市代码映射
        city_codes = {
            "北京": "101010100",
            "上海": "101020100",
            "广州": "101280100",
            "深圳": "101280600",
            "杭州": "101210100",
            "成都": "101270100",
            "南京": "101190100",
            "武汉": "101200100",
            "西安": "101110100"
        }
        
        city_code = city_codes.get(location, "101010100")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.zhipin.com/",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        
        params = {
            "scene": "1",
            "query": keyword,
            "city": city_code,
            "page": "1",
            "pageSize": str(limit)
        }
        
        try:
            response = requests.get(
                self.api_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("code") == 0 and data.get("zpData"):
                    job_list = data["zpData"].get("jobList", [])
                    
                    for job_item in job_list:
                        job = self._parse_boss_job(job_item, location)
                        if job:
                            jobs.append(job)
                    
                    logger.info(f"从BOSS直聘获取到 {len(jobs)} 个岗位")
                else:
                    logger.warning(f"BOSS直聘API返回错误: {data.get('message')}")
            else:
                logger.warning(f"BOSS直聘API请求失败: {response.status_code}")
        
        except Exception as e:
            logger.error(f"BOSS直聘数据获取失败: {e}")
        
        return jobs
    
    def _parse_boss_job(self, job_item: Dict, location: str) -> Optional[JobData]:
        """解析BOSS直聘岗位数据"""
        try:
            # 解析薪资
            salary_desc = job_item.get("salaryDesc", "")
            salary_min, salary_max = self._parse_salary(salary_desc)
            
            # 解析技能标签
            skills = job_item.get("skills", [])
            if isinstance(skills, list):
                skill_list = skills
            else:
                skill_list = []
            
            # 解析经验要求
            job_experience = job_item.get("jobExperience", "")
            experience = self._parse_experience(job_experience)
            
            # 福利标签
            welfare_list = job_item.get("welfareList", [])
            
            return JobData(
                job_id=str(job_item.get("encryptJobId", "")),
                title=job_item.get("jobName", ""),
                company=job_item.get("brandName", ""),
                company_id=str(job_item.get("encryptBrandId", "")),
                salary_min=salary_min,
                salary_max=salary_max,
                salary_avg=(salary_min + salary_max) / 2,
                required_skills=skill_list,
                experience_required=experience,
                education_required=job_item.get("jobDegree", "本科"),
                location=location,
                district=job_item.get("cityName", ""),
                industry=job_item.get("industryName", ""),
                company_size=job_item.get("brandScaleName", ""),
                company_stage=job_item.get("brandStageName", ""),
                job_description=job_item.get("jobLabels", ""),
                welfare_tags=welfare_list,
                source="boss_zhipin",
                source_url=f"https://www.zhipin.com/job_detail/{job_item.get('encryptJobId', '')}.html",
                crawled_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"解析BOSS直聘岗位失败: {e}")
            return None
    
    def _parse_salary(self, salary_desc: str) -> tuple:
        """解析薪资"""
        if not salary_desc:
            return (0, 0)
        
        # 匹配 "20-35K" 或 "20K-35K" 或 "2-3.5万"
        match = re.search(r'(\d+\.?\d*)[kK万]?-(\d+\.?\d*)[kK万]', salary_desc)
        
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            
            # 判断单位
            if 'K' in salary_desc or 'k' in salary_desc:
                # K表示千/月，转换为万/年
                return (min_val * 1.2, max_val * 1.2)
            elif '万' in salary_desc:
                # 判断是月薪还是年薪
                if '月' in salary_desc:
                    return (min_val * 12, max_val * 12)
                else:
                    return (min_val, max_val)
        
        return (0, 0)
    
    def _parse_experience(self, exp_text: str) -> int:
        """解析经验要求"""
        if not exp_text or "不限" in exp_text or "应届" in exp_text:
            return 0
        
        match = re.search(r'(\d+)', exp_text)
        if match:
            return int(match.group(1))
        
        return 0


class RealJobDataIntegration:
    """
    真实岗位数据集成器
    
    统一管理多个数据源，提供缓存和降级策略
    """
    
    def __init__(self):
        self.cache = JobDataCache(cache_hours=24)
        self.boss_crawler = BOSSZhipinCrawler()
        
        # 集成GitHub开源爬虫
        try:
            from backend.vertical.career.github_crawler_adapter import github_crawler
            self.github_crawler = github_crawler
            if github_crawler.available:
                logger.info("✓ GitHub开源爬虫已集成")
            else:
                logger.warning("⚠ GitHub开源爬虫不可用")
                self.github_crawler = None
        except Exception as e:
            logger.warning(f"GitHub开源爬虫加载失败: {e}")
            self.github_crawler = None
        
        # 从现有的爬虫导入
        try:
            from backend.vertical.career.job_data_crawler import job_crawler
            self.lagou_crawler = job_crawler
        except:
            self.lagou_crawler = None
    
    def search_jobs(
        self,
        keyword: str,
        location: str = "北京",
        limit: int = 20,
        use_cache: bool = True
    ) -> List[JobData]:
        """
        搜索岗位（多数据源聚合）
        
        策略：
        1. 优先从缓存获取
        2. 尝试BOSS直聘
        3. 降级到拉勾网
        4. 最后使用模拟数据
        """
        # 1. 尝试缓存
        if use_cache:
            cached_jobs = self.cache.get(keyword, location, "aggregated")
            if cached_jobs:
                return cached_jobs[:limit]
        
        all_jobs = []
        
        # 1. 优先使用GitHub开源爬虫（支持多平台）
        if self.github_crawler and self.github_crawler.available:
            try:
                github_jobs = self.github_crawler.search_jobs(
                    keyword, location, limit,
                    platforms=['boss', 'zhilian']  # BOSS直聘 + 智联招聘
                )
                all_jobs.extend(github_jobs)
                logger.info(f"GitHub爬虫: {len(github_jobs)} 个岗位")
                
                if len(all_jobs) >= limit:
                    self.cache.set(keyword, location, "github_crawler", all_jobs)
                    return all_jobs[:limit]
            except Exception as e:
                logger.warning(f"GitHub爬虫获取失败: {e}")
        
        # 2. BOSS直聘（备用）
        if len(all_jobs) < limit:
            try:
                boss_jobs = self.boss_crawler.search_jobs(keyword, location, limit - len(all_jobs))
                all_jobs.extend(boss_jobs)
                logger.info(f"BOSS直聘: {len(boss_jobs)} 个岗位")
            except Exception as e:
                logger.warning(f"BOSS直聘获取失败: {e}")
        
        # 3. 拉勾网（如果BOSS数据不足）
        if len(all_jobs) < limit and self.lagou_crawler:
            try:
                lagou_jobs = self.lagou_crawler.search_jobs(keyword, location, limit - len(all_jobs))
                # 转换为统一格式
                for lj in lagou_jobs:
                    all_jobs.append(JobData(
                        job_id=lj.job_id,
                        title=lj.title,
                        company=lj.company,
                        company_id="",
                        salary_min=lj.salary_min,
                        salary_max=lj.salary_max,
                        salary_avg=lj.salary_avg,
                        required_skills=lj.required_skills,
                        experience_required=lj.experience_required,
                        education_required=lj.education_required,
                        location=lj.location,
                        district="",
                        industry=lj.industry,
                        company_size=lj.company_size,
                        company_stage="",
                        job_description=lj.job_description,
                        welfare_tags=[],
                        source=lj.source,
                        source_url="",
                        crawled_at=datetime.now().isoformat()
                    ))
                logger.info(f"拉勾网: {len(lagou_jobs)} 个岗位")
            except Exception as e:
                logger.warning(f"拉勾网获取失败: {e}")
        
        # 4. 去重（基于job_id和company）
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        # 5. 缓存结果
        if unique_jobs:
            self.cache.set(keyword, location, "aggregated", unique_jobs)
        
        return unique_jobs[:limit]
    
    def _deduplicate_jobs(self, jobs: List[JobData]) -> List[JobData]:
        """去重"""
        seen = set()
        unique = []
        
        for job in jobs:
            key = f"{job.title}_{job.company}"
            if key not in seen:
                seen.add(key)
                unique.append(job)
        
        return unique
    
    def get_market_statistics(
        self,
        keyword: str,
        location: str = "北京"
    ) -> Dict[str, Any]:
        """
        获取市场统计数据
        
        Returns:
            {
                'total_jobs': 总岗位数,
                'avg_salary': 平均薪资,
                'salary_distribution': 薪资分布,
                'top_skills': 热门技能,
                'top_companies': 热门公司,
                'experience_distribution': 经验分布
            }
        """
        jobs = self.search_jobs(keyword, location, limit=100)
        
        if not jobs:
            return {
                'total_jobs': 0,
                'avg_salary': 0,
                'salary_distribution': {},
                'top_skills': [],
                'top_companies': [],
                'experience_distribution': {}
            }
        
        # 统计薪资
        salaries = [job.salary_avg for job in jobs if job.salary_avg > 0]
        avg_salary = sum(salaries) / len(salaries) if salaries else 0
        
        # 薪资分布
        salary_ranges = {
            '0-15万': 0,
            '15-25万': 0,
            '25-35万': 0,
            '35-50万': 0,
            '50万+': 0
        }
        
        for salary in salaries:
            if salary < 15:
                salary_ranges['0-15万'] += 1
            elif salary < 25:
                salary_ranges['15-25万'] += 1
            elif salary < 35:
                salary_ranges['25-35万'] += 1
            elif salary < 50:
                salary_ranges['35-50万'] += 1
            else:
                salary_ranges['50万+'] += 1
        
        # 技能统计
        skill_count = {}
        for job in jobs:
            for skill in job.required_skills:
                skill_count[skill] = skill_count.get(skill, 0) + 1
        
        top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 公司统计
        company_count = {}
        for job in jobs:
            company_count[job.company] = company_count.get(job.company, 0) + 1
        
        top_companies = sorted(company_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 经验分布
        exp_distribution = {
            '应届生': 0,
            '1-3年': 0,
            '3-5年': 0,
            '5-10年': 0,
            '10年+': 0
        }
        
        for job in jobs:
            exp = job.experience_required
            if exp == 0:
                exp_distribution['应届生'] += 1
            elif exp <= 3:
                exp_distribution['1-3年'] += 1
            elif exp <= 5:
                exp_distribution['3-5年'] += 1
            elif exp <= 10:
                exp_distribution['5-10年'] += 1
            else:
                exp_distribution['10年+'] += 1
        
        return {
            'total_jobs': len(jobs),
            'avg_salary': round(avg_salary, 1),
            'salary_distribution': salary_ranges,
            'top_skills': [{'skill': s, 'count': c} for s, c in top_skills],
            'top_companies': [{'company': c, 'count': cnt} for c, cnt in top_companies],
            'experience_distribution': exp_distribution,
            'data_sources': list(set(job.source for job in jobs)),
            'updated_at': datetime.now().isoformat()
        }


# 全局实例
real_job_integration = RealJobDataIntegration()


if __name__ == "__main__":
    # 测试
    integration = RealJobDataIntegration()
    
    print("=" * 60)
    print("测试岗位搜索")
    print("=" * 60)
    
    jobs = integration.search_jobs("Python工程师", "北京", 10)
    print(f"\n找到 {len(jobs)} 个岗位：\n")
    
    for job in jobs[:5]:
        print(f"{job.title} - {job.company}")
        print(f"  薪资: {job.salary_min:.1f}-{job.salary_max:.1f}万/年")
        print(f"  技能: {', '.join(job.required_skills[:5])}")
        print(f"  来源: {job.source}")
        print()
    
    print("\n" + "=" * 60)
    print("测试市场统计")
    print("=" * 60)
    
    stats = integration.get_market_statistics("Python工程师", "北京")
    print(f"\n总岗位数: {stats['total_jobs']}")
    print(f"平均薪资: {stats['avg_salary']:.1f}万/年")
    print(f"\n热门技能:")
    for skill_data in stats['top_skills'][:5]:
        print(f"  {skill_data['skill']}: {skill_data['count']}个岗位")


# 创建全局实例供其他模块使用
unified_job_service = RealJobDataIntegration()
