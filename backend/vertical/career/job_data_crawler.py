"""
岗位数据爬虫
从招聘网站爬取真实的岗位信息
"""
from typing import Dict, List, Any, Optional
import re
import json
import time
import requests
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class JobData:
    """岗位数据"""
    job_id: str
    title: str
    company: str
    salary_min: float  # 万/年
    salary_max: float  # 万/年
    salary_avg: float  # 万/年
    required_skills: List[str]
    experience_required: int  # 年限
    education_required: str
    location: str
    industry: str
    company_size: str
    job_description: str
    source: str  # 数据来源


class JobDataCrawler:
    """
    岗位数据爬虫
    
    注意：这是示例实现，实际使用需要：
    1. 遵守网站的robots.txt
    2. 控制爬取频率
    3. 使用合法的API（如果有）
    """
    
    def __init__(self):
        self.skill_keywords = [
            "Python", "Java", "JavaScript", "Go", "C++", "C#", "PHP", "Ruby",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask", "Spring",
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "机器学习", "深度学习", "NLP", "计算机视觉", "数据分析",
            "Git", "Linux", "Nginx", "Kafka", "RabbitMQ"
        ]
    
    def search_jobs(
        self,
        keyword: str,
        location: str = "北京",
        limit: int = 20
    ) -> List[JobData]:
        """
        搜索岗位
        
        Args:
            keyword: 搜索关键词（如"Python工程师"）
            location: 地点
            limit: 返回数量
        
        Returns:
            岗位数据列表
        """
        # 尝试从真实API获取数据
        try:
            jobs = self._fetch_from_lagou(keyword, location, limit)
            if jobs:
                logger.info(f"从拉勾网获取到 {len(jobs)} 个岗位")
                return jobs
        except Exception as e:
            logger.warning(f"拉勾API调用失败: {e}，使用模拟数据")
        
        # 如果API失败，使用模拟数据
        return self._generate_mock_jobs(keyword, location, limit)
    
    def _fetch_from_lagou(
        self,
        keyword: str,
        location: str,
        limit: int
    ) -> List[JobData]:
        """
        从拉勾网API获取岗位数据
        
        注意：拉勾网有反爬机制，需要：
        1. 设置合适的User-Agent
        2. 控制请求频率
        3. 可能需要登录token
        """
        jobs = []
        
        # 拉勾网API地址（可能需要更新）
        url = "https://www.lagou.com/jobs/positionAjax.json"
        
        # 城市代码映射
        city_map = {
            "北京": "2",
            "上海": "3",
            "广州": "213",
            "深圳": "215",
            "杭州": "179",
            "成都": "252"
        }
        
        city_code = city_map.get(location, "2")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.lagou.com/jobs/list_python",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        params = {
            "city": location,
            "needAddtionalResult": "false",
            "first": "true"
        }
        
        data = {
            "first": "true",
            "pn": 1,
            "kd": keyword
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and result.get("content"):
                    position_result = result["content"].get("positionResult", {})
                    positions = position_result.get("result", [])
                    
                    for pos in positions[:limit]:
                        job = self._parse_lagou_position(pos)
                        if job:
                            jobs.append(job)
            
        except Exception as e:
            logger.error(f"拉勾API请求失败: {e}")
            raise
        
        return jobs
    
    def _parse_lagou_position(self, pos: Dict) -> Optional[JobData]:
        """解析拉勾网岗位数据"""
        try:
            # 解析薪资
            salary_text = pos.get("salary", "")
            salary_min, salary_max = self.parse_salary(salary_text)
            
            # 解析经验要求
            work_year = pos.get("workYear", "")
            experience = self._parse_experience(work_year)
            
            # 提取技能
            job_desc = pos.get("positionAdvantage", "") + " " + pos.get("positionName", "")
            skills = self.extract_skills_from_jd(job_desc)
            
            return JobData(
                job_id=str(pos.get("positionId", "")),
                title=pos.get("positionName", ""),
                company=pos.get("companyFullName", ""),
                salary_min=salary_min,
                salary_max=salary_max,
                salary_avg=(salary_min + salary_max) / 2,
                required_skills=skills,
                experience_required=experience,
                education_required=pos.get("education", "本科"),
                location=pos.get("city", ""),
                industry=pos.get("industryField", ""),
                company_size=pos.get("companySize", ""),
                job_description=pos.get("positionAdvantage", ""),
                source="lagou"
            )
        except Exception as e:
            logger.error(f"解析拉勾岗位数据失败: {e}")
            return None
    
    def _parse_experience(self, work_year: str) -> int:
        """解析工作年限"""
        if "不限" in work_year or "应届" in work_year:
            return 0
        
        # 匹配数字
        match = re.search(r'(\d+)', work_year)
        if match:
            return int(match.group(1))
        
        return 0
    
    def _generate_mock_jobs(
        self,
        keyword: str,
        location: str,
        limit: int
    ) -> List[JobData]:
        """
        生成模拟岗位数据
        
        实际使用时替换为真实的爬虫或API调用
        """
        mock_jobs = []
        
        # 根据关键词生成不同的岗位
        if "Python" in keyword or "python" in keyword.lower():
            templates = [
                {
                    "title": "Python后端工程师",
                    "skills": ["Python", "Django", "MySQL", "Redis", "Docker"],
                    "salary": (20, 35),
                    "experience": 3
                },
                {
                    "title": "Python全栈工程师",
                    "skills": ["Python", "Vue", "MySQL", "Redis", "Linux"],
                    "salary": (25, 40),
                    "experience": 3
                },
                {
                    "title": "机器学习工程师",
                    "skills": ["Python", "机器学习", "深度学习", "TensorFlow", "PyTorch"],
                    "salary": (30, 50),
                    "experience": 3
                },
                {
                    "title": "数据分析师",
                    "skills": ["Python", "数据分析", "SQL", "Pandas", "可视化"],
                    "salary": (18, 30),
                    "experience": 2
                }
            ]
        elif "Java" in keyword or "java" in keyword.lower():
            templates = [
                {
                    "title": "Java后端工程师",
                    "skills": ["Java", "Spring", "MySQL", "Redis", "Kafka"],
                    "salary": (22, 38),
                    "experience": 3
                },
                {
                    "title": "Java架构师",
                    "skills": ["Java", "Spring", "微服务", "分布式", "高并发"],
                    "salary": (40, 70),
                    "experience": 5
                }
            ]
        else:
            templates = [
                {
                    "title": f"{keyword}工程师",
                    "skills": ["编程", "算法", "数据结构"],
                    "salary": (20, 35),
                    "experience": 3
                }
            ]
        
        companies = [
            {"name": "字节跳动", "size": "10000人以上", "industry": "互联网"},
            {"name": "阿里巴巴", "size": "10000人以上", "industry": "互联网"},
            {"name": "腾讯", "size": "10000人以上", "industry": "互联网"},
            {"name": "美团", "size": "10000人以上", "industry": "互联网"},
            {"name": "京东", "size": "10000人以上", "industry": "电商"},
            {"name": "百度", "size": "10000人以上", "industry": "互联网"},
            {"name": "小米", "size": "5000-10000人", "industry": "硬件"},
            {"name": "华为", "size": "10000人以上", "industry": "通信"},
        ]
        
        for i in range(min(limit, len(templates) * len(companies))):
            template = templates[i % len(templates)]
            company = companies[i % len(companies)]
            
            salary_min, salary_max = template["salary"]
            salary_avg = (salary_min + salary_max) / 2
            
            job = JobData(
                job_id=f"job_{i+1}",
                title=template["title"],
                company=company["name"],
                salary_min=salary_min,
                salary_max=salary_max,
                salary_avg=salary_avg,
                required_skills=template["skills"],
                experience_required=template["experience"],
                education_required="本科",
                location=location,
                industry=company["industry"],
                company_size=company["size"],
                job_description=f"{template['title']}岗位，负责{', '.join(template['skills'])}相关工作",
                source="mock_data"
            )
            
            mock_jobs.append(job)
        
        return mock_jobs
    
    def extract_skills_from_jd(self, job_description: str) -> List[str]:
        """
        从JD中提取技能关键词
        
        Args:
            job_description: 岗位描述
        
        Returns:
            技能列表
        """
        skills = []
        
        for skill in self.skill_keywords:
            if skill.lower() in job_description.lower():
                skills.append(skill)
        
        return list(set(skills))
    
    def parse_salary(self, salary_text: str) -> tuple:
        """
        解析薪资文本
        
        Args:
            salary_text: 薪资文本（如"20k-35k"、"20-35K"、"2万-3.5万/月"）
        
        Returns:
            (最低薪资, 最高薪资) 单位：万/年
        """
        if not salary_text:
            return (0, 0)
        
        # 匹配 "20k-35k" 或 "20-35k" 或 "20K-35K" 格式
        match = re.search(r'(\d+)k?-(\d+)k', salary_text.lower())
        
        if match:
            min_salary = float(match.group(1))
            max_salary = float(match.group(2))
            
            # 转换为万/年（假设月薪，乘以12个月，再除以10000）
            return (min_salary * 1.2, max_salary * 1.2)
        
        # 匹配 "2万-3.5万" 格式
        match = re.search(r'(\d+\.?\d*)万-(\d+\.?\d*)万', salary_text)
        if match:
            min_salary = float(match.group(1))
            max_salary = float(match.group(2))
            
            # 如果是月薪，乘以12
            if "月" in salary_text:
                return (min_salary * 12, max_salary * 12)
            else:
                return (min_salary, max_salary)
        
        return (0, 0)


# 全局实例
job_crawler = JobDataCrawler()


if __name__ == "__main__":
    # 测试
    crawler = JobDataCrawler()
    jobs = crawler.search_jobs("Python工程师", "北京", 10)
    
    print(f"找到 {len(jobs)} 个岗位：\n")
    for job in jobs:
        print(f"{job.title} - {job.company}")
        print(f"  薪资: {job.salary_min}-{job.salary_max}万/年")
        print(f"  技能: {', '.join(job.required_skills)}")
        print()
