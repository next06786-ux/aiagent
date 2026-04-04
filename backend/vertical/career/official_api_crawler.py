"""
使用官方API获取岗位数据

支持的平台：
1. 猎聘网 - 有开放API
2. 智联招聘 - 企业版API
3. 前程无忧 - 企业版API
4. LinkedIn - 官方API（需要申请）
"""
import requests
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LinkedInJobAPI:
    """
    LinkedIn Jobs API
    
    优点：
    - 官方API，稳定可靠
    - 全球岗位数据
    - 无反爬限制
    
    缺点：
    - 需要申请API key
    - 有请求频率限制
    
    申请地址: https://developer.linkedin.com/
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.linkedin.com/v2"
        
    def search_jobs(self, keyword: str, location: str = "China", limit: int = 20):
        """搜索岗位"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        params = {
            "keywords": keyword,
            "location": location,
            "count": limit
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/jobSearch",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_jobs(data)
            else:
                logger.error(f"LinkedIn API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"LinkedIn API request failed: {e}")
            return []
    
    def _parse_jobs(self, data):
        """解析LinkedIn岗位数据"""
        jobs = []
        for item in data.get("elements", []):
            # 解析逻辑
            pass
        return jobs


class RapidAPIJobSearch:
    """
    使用RapidAPI的招聘数据API
    
    RapidAPI聚合了多个招聘平台的API：
    - JSearch API (Indeed, LinkedIn, Glassdoor等)
    - Jobs API
    - Reed Jobs API (英国)
    
    优点：
    - 一个API访问多个平台
    - 有免费额度
    - 稳定可靠
    
    注册地址: https://rapidapi.com/
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://jsearch.p.rapidapi.com"
        
    def search_jobs(self, keyword: str, location: str = "China", limit: int = 20):
        """搜索岗位"""
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        params = {
            "query": f"{keyword} in {location}",
            "page": "1",
            "num_pages": "1",
            "date_posted": "all"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for job in data.get("data", [])[:limit]:
                    jobs.append({
                        "title": job.get("job_title"),
                        "company": job.get("employer_name"),
                        "location": job.get("job_city"),
                        "description": job.get("job_description"),
                        "salary_min": self._parse_salary(job.get("job_min_salary")),
                        "salary_max": self._parse_salary(job.get("job_max_salary")),
                        "source": "jsearch_api",
                        "source_url": job.get("job_apply_link"),
                        "posted_at": job.get("job_posted_at_datetime_utc")
                    })
                
                logger.info(f"从JSearch API获取到 {len(jobs)} 个岗位")
                return jobs
            else:
                logger.error(f"RapidAPI error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"RapidAPI request failed: {e}")
            return []
    
    def _parse_salary(self, salary):
        """解析薪资"""
        if salary:
            return float(salary) / 10000  # 转换为万元
        return 0


class AdzunaJobAPI:
    """
    Adzuna Jobs API
    
    优点：
    - 完全免费
    - 覆盖多个国家
    - 有中国区数据
    - 官方API，稳定
    
    注册地址: https://developer.adzuna.com/
    """
    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs"
        
    def search_jobs(self, keyword: str, location: str = "China", limit: int = 20):
        """搜索岗位"""
        # Adzuna使用国家代码
        country_code = "cn"  # 中国
        
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": keyword,
            "where": location,
            "content-type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{country_code}/search/1",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for job in data.get("results", []):
                    jobs.append({
                        "title": job.get("title"),
                        "company": job.get("company", {}).get("display_name"),
                        "location": job.get("location", {}).get("display_name"),
                        "description": job.get("description"),
                        "salary_min": job.get("salary_min", 0) / 10000,
                        "salary_max": job.get("salary_max", 0) / 10000,
                        "source": "adzuna_api",
                        "source_url": job.get("redirect_url"),
                        "posted_at": job.get("created")
                    })
                
                logger.info(f"从Adzuna API获取到 {len(jobs)} 个岗位")
                return jobs
            else:
                logger.error(f"Adzuna API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Adzuna API request failed: {e}")
            return []


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("官方API岗位数据获取示例")
    print("=" * 60)
    
    # 1. RapidAPI (推荐 - 有免费额度)
    print("\n1. RapidAPI JSearch:")
    print("   - 注册: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
    print("   - 免费额度: 每月2500次请求")
    print("   - 覆盖: Indeed, LinkedIn, Glassdoor等")
    
    # 2. Adzuna (完全免费)
    print("\n2. Adzuna API:")
    print("   - 注册: https://developer.adzuna.com/")
    print("   - 完全免费")
    print("   - 覆盖: 全球多个国家包括中国")
    
    # 3. LinkedIn (需要企业账号)
    print("\n3. LinkedIn API:")
    print("   - 注册: https://developer.linkedin.com/")
    print("   - 需要企业账号")
    print("   - 最权威的职业数据")
    
    print("\n" + "=" * 60)
    print("推荐使用 Adzuna API (免费) 或 RapidAPI (有免费额度)")
    print("=" * 60)
