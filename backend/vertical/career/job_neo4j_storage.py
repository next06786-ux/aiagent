"""
岗位数据Neo4j存储

将爬取的岗位数据持久化到Neo4j知识图谱
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class JobNeo4jStorage:
    """岗位数据Neo4j存储"""
    
    def __init__(self):
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """初始化Neo4j连接"""
        try:
            from backend.knowledge_graph.neo4j_client import Neo4jClient
            self.client = Neo4jClient()
            logger.info("Neo4j连接初始化成功")
        except Exception as e:
            logger.error(f"Neo4j连接初始化失败: {e}")
            self.client = None
    
    def save_job(self, job_data: Dict[str, Any]) -> bool:
        """
        保存单个岗位到Neo4j
        
        创建节点和关系：
        - Job节点
        - Company节点
        - Skill节点
        - Job-[:REQUIRES_SKILL]->Skill
        - Company-[:OFFERS]->Job
        """
        if not self.client:
            logger.warning("Neo4j未连接，跳过保存")
            return False
        
        try:
            # 1. 创建/更新Job节点
            job_query = """
            MERGE (j:Job {job_id: $job_id})
            SET j.title = $title,
                j.salary_min = $salary_min,
                j.salary_max = $salary_max,
                j.salary_avg = $salary_avg,
                j.experience_required = $experience_required,
                j.education_required = $education_required,
                j.location = $location,
                j.district = $district,
                j.job_description = $job_description,
                j.source = $source,
                j.source_url = $source_url,
                j.updated_at = $updated_at
            RETURN j
            """
            
            self.client.query(job_query, {
                'job_id': job_data['job_id'],
                'title': job_data['title'],
                'salary_min': job_data['salary_min'],
                'salary_max': job_data['salary_max'],
                'salary_avg': job_data['salary_avg'],
                'experience_required': job_data['experience_required'],
                'education_required': job_data['education_required'],
                'location': job_data['location'],
                'district': job_data.get('district', ''),
                'job_description': job_data.get('job_description', ''),
                'source': job_data['source'],
                'source_url': job_data.get('source_url', ''),
                'updated_at': datetime.now().isoformat()
            })
            
            # 2. 创建/更新Company节点
            company_query = """
            MERGE (c:Company {name: $company_name})
            SET c.company_id = $company_id,
                c.size = $company_size,
                c.stage = $company_stage,
                c.industry = $industry,
                c.updated_at = $updated_at
            RETURN c
            """
            
            self.client.query(company_query, {
                'company_name': job_data['company'],
                'company_id': job_data.get('company_id', ''),
                'company_size': job_data.get('company_size', ''),
                'company_stage': job_data.get('company_stage', ''),
                'industry': job_data.get('industry', ''),
                'updated_at': datetime.now().isoformat()
            })
            
            # 3. 创建Company-[:OFFERS]->Job关系
            offer_query = """
            MATCH (c:Company {name: $company_name})
            MATCH (j:Job {job_id: $job_id})
            MERGE (c)-[r:OFFERS]->(j)
            SET r.updated_at = $updated_at
            """
            
            self.client.query(offer_query, {
                'company_name': job_data['company'],
                'job_id': job_data['job_id'],
                'updated_at': datetime.now().isoformat()
            })
            
            # 4. 创建技能节点和关系
            for skill in job_data.get('required_skills', []):
                # 创建Skill节点
                skill_query = """
                MERGE (s:Skill {name: $skill_name})
                SET s.updated_at = $updated_at
                RETURN s
                """
                
                self.client.query(skill_query, {
                    'skill_name': skill,
                    'updated_at': datetime.now().isoformat()
                })
                
                # 创建Job-[:REQUIRES_SKILL]->Skill关系
                require_query = """
                MATCH (j:Job {job_id: $job_id})
                MATCH (s:Skill {name: $skill_name})
                MERGE (j)-[r:REQUIRES_SKILL]->(s)
                SET r.importance = 0.8,
                    r.updated_at = $updated_at
                """
                
                self.client.query(require_query, {
                    'job_id': job_data['job_id'],
                    'skill_name': skill,
                    'updated_at': datetime.now().isoformat()
                })
            
            logger.info(f"保存岗位成功: {job_data['title']} - {job_data['company']}")
            return True
        
        except Exception as e:
            logger.error(f"保存岗位失败: {e}")
            return False
    
    def save_jobs_batch(self, jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量保存岗位
        
        Returns:
            {'success': 成功数, 'failed': 失败数}
        """
        success_count = 0
        failed_count = 0
        
        for job in jobs:
            if self.save_job(job):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"批量保存完成: 成功{success_count}, 失败{failed_count}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(jobs)
        }
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """根据job_id查询岗位"""
        if not self.client:
            return None
        
        try:
            query = """
            MATCH (j:Job {job_id: $job_id})
            OPTIONAL MATCH (c:Company)-[:OFFERS]->(j)
            OPTIONAL MATCH (j)-[:REQUIRES_SKILL]->(s:Skill)
            RETURN j, c, collect(s.name) as skills
            """
            
            result = self.client.query(query, {'job_id': job_id})
            
            if result:
                job_node = result[0]['j']
                company_node = result[0].get('c')
                skills = result[0].get('skills', [])
                
                return {
                    'job_id': job_node.get('job_id'),
                    'title': job_node.get('title'),
                    'company': company_node.get('name') if company_node else '',
                    'salary_min': job_node.get('salary_min'),
                    'salary_max': job_node.get('salary_max'),
                    'required_skills': skills,
                    'location': job_node.get('location'),
                    'source': job_node.get('source')
                }
        
        except Exception as e:
            logger.error(f"查询岗位失败: {e}")
        
        return None
    
    def search_jobs_by_title(
        self,
        keyword: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        从Neo4j搜索岗位
        
        Args:
            keyword: 岗位关键词
            location: 城市（可选）
            limit: 返回数量
        """
        if not self.client:
            return []
        
        try:
            if location:
                query = """
                MATCH (j:Job)
                WHERE j.title CONTAINS $keyword AND j.location = $location
                OPTIONAL MATCH (c:Company)-[:OFFERS]->(j)
                OPTIONAL MATCH (j)-[:REQUIRES_SKILL]->(s:Skill)
                RETURN j, c.name as company, collect(s.name) as skills
                ORDER BY j.updated_at DESC
                LIMIT $limit
                """
                params = {'keyword': keyword, 'location': location, 'limit': limit}
            else:
                query = """
                MATCH (j:Job)
                WHERE j.title CONTAINS $keyword
                OPTIONAL MATCH (c:Company)-[:OFFERS]->(j)
                OPTIONAL MATCH (j)-[:REQUIRES_SKILL]->(s:Skill)
                RETURN j, c.name as company, collect(s.name) as skills
                ORDER BY j.updated_at DESC
                LIMIT $limit
                """
                params = {'keyword': keyword, 'limit': limit}
            
            results = self.client.query(query, params)
            
            jobs = []
            for record in results:
                job_node = record['j']
                jobs.append({
                    'job_id': job_node.get('job_id'),
                    'title': job_node.get('title'),
                    'company': record.get('company', ''),
                    'salary_min': job_node.get('salary_min'),
                    'salary_max': job_node.get('salary_max'),
                    'salary_avg': job_node.get('salary_avg'),
                    'required_skills': record.get('skills', []),
                    'location': job_node.get('location'),
                    'source': job_node.get('source')
                })
            
            return jobs
        
        except Exception as e:
            logger.error(f"搜索岗位失败: {e}")
            return []
    
    def get_skill_demand_stats(self, skill_name: str) -> Dict[str, Any]:
        """
        获取技能需求统计
        
        Returns:
            {
                'skill': 技能名称,
                'job_count': 需要该技能的岗位数,
                'avg_salary': 平均薪资,
                'top_companies': 招聘该技能的热门公司
            }
        """
        if not self.client:
            return {}
        
        try:
            query = """
            MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill {name: $skill_name})
            OPTIONAL MATCH (c:Company)-[:OFFERS]->(j)
            RETURN 
                count(j) as job_count,
                avg(j.salary_avg) as avg_salary,
                collect(DISTINCT c.name)[0..10] as top_companies
            """
            
            result = self.client.query(query, {'skill_name': skill_name})
            
            if result:
                return {
                    'skill': skill_name,
                    'job_count': result[0].get('job_count', 0),
                    'avg_salary': round(result[0].get('avg_salary', 0), 1),
                    'top_companies': result[0].get('top_companies', [])
                }
        
        except Exception as e:
            logger.error(f"统计技能需求失败: {e}")
        
        return {}
    
    def clean_old_jobs(self, days: int = 30):
        """
        清理旧岗位数据
        
        Args:
            days: 保留最近N天的数据
        """
        if not self.client:
            return
        
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = """
            MATCH (j:Job)
            WHERE j.updated_at < $cutoff_date
            DETACH DELETE j
            """
            
            self.client.query(query, {'cutoff_date': cutoff_date})
            logger.info(f"清理{days}天前的岗位数据完成")
        
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")


# 全局实例
job_storage = JobNeo4jStorage()


if __name__ == "__main__":
    # 测试
    storage = JobNeo4jStorage()
    
    # 测试保存
    test_job = {
        'job_id': 'test_001',
        'title': 'Python工程师',
        'company': '测试公司',
        'company_id': 'test_company',
        'salary_min': 20,
        'salary_max': 35,
        'salary_avg': 27.5,
        'required_skills': ['Python', 'Django', 'MySQL'],
        'experience_required': 3,
        'education_required': '本科',
        'location': '北京',
        'district': '朝阳区',
        'industry': '互联网',
        'company_size': '500-1000人',
        'company_stage': 'C轮',
        'job_description': '负责后端开发',
        'source': 'test',
        'source_url': 'http://test.com'
    }
    
    print("测试保存岗位...")
    success = storage.save_job(test_job)
    print(f"保存结果: {'成功' if success else '失败'}")
    
    # 测试查询
    print("\n测试查询岗位...")
    job = storage.get_job_by_id('test_001')
    if job:
        print(f"查询到: {job['title']} - {job['company']}")
    
    # 测试搜索
    print("\n测试搜索岗位...")
    jobs = storage.search_jobs_by_title('Python', '北京', 5)
    print(f"搜索到 {len(jobs)} 个岗位")
    
    # 测试技能统计
    print("\n测试技能统计...")
    stats = storage.get_skill_demand_stats('Python')
    print(f"Python岗位数: {stats.get('job_count', 0)}")
    print(f"平均薪资: {stats.get('avg_salary', 0)}万/年")
