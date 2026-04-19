"""职业知识图谱构建器 - 用于生成3D可视化的职业发展知识图谱"""
from typing import Dict, List, Any
from dataclasses import dataclass
import math

@dataclass
class UserSkillProfile:
    """用户技能档案"""
    mastered_skills: List[str]
    partial_skills: List[str]
    missing_skills: List[str]
    target_direction: str

class CareerKnowledgeGraph:
    """职业知识图谱构建器"""
    def __init__(self):
        # 使用统一的岗位数据服务（支持BOSS直聘+拉勾网）
        try:
            from backend.vertical.career.real_job_data_integration import unified_job_service
            self.job_service = unified_job_service
            print("[CareerKG] 使用真实岗位数据服务（BOSS直聘+拉勾网）")
        except Exception as e:
            print(f"[CareerKG] 真实数据服务加载失败: {e}，使用备用方案")
            from backend.vertical.career.job_data_crawler import JobDataCrawler
            self.job_service = JobDataCrawler()
        
        # 添加缓存，避免重复爬取
        self._job_cache = {}
        self._cache_ttl = 3600  # 缓存1小时
        self._last_cache_time = {}
        
        self.skill_dependencies = {
            "Python": [], "Django": ["Python"], "Flask": ["Python"], "FastAPI": ["Python"],
            "JavaScript": [], "React": ["JavaScript"], "Vue": ["JavaScript"],
            "Node.js": ["JavaScript"], "TypeScript": ["JavaScript"],
            "Java": [], "Spring": ["Java"], "MySQL": [], "PostgreSQL": [],
            "MongoDB": [], "Redis": [], "Docker": [], "Kubernetes": ["Docker"],
            "Git": [], "Linux": [], "AWS": ["Linux"],
            "机器学习": ["Python"], "深度学习": ["机器学习", "Python"],
            "数据分析": ["Python"], "算法": [], "数据结构": []
        }
    
    def _get_jobs_cached(self, keyword: str, location: str = "全国", limit: int = 20):
        """带缓存的岗位查询 - 使用真实数据源（BOSS直聘+拉勾网）"""
        import time
        cache_key = f"{keyword}_{location}_{limit}"
        current_time = time.time()
        
        # 检查缓存
        if cache_key in self._job_cache:
            last_time = self._last_cache_time.get(cache_key, 0)
            if current_time - last_time < self._cache_ttl:
                print(f"[CareerKG] 使用缓存岗位数据: {cache_key}")
                return self._job_cache[cache_key]
        
        # 缓存过期或不存在，重新获取
        print(f"[CareerKG] 从真实数据源获取岗位: {cache_key}")
        jobs = self.job_service.search_jobs(keyword=keyword, location=location, limit=limit)
        
        # 打印数据来源统计
        if jobs:
            sources = {}
            for job in jobs:
                source = getattr(job, 'source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            print(f"[CareerKG] 岗位数据来源: {sources}")
        
        self._job_cache[cache_key] = jobs
        self._last_cache_time[cache_key] = current_time
        return jobs
    
    def build_career_graph(self, user_profile: UserSkillProfile) -> Dict[str, Any]:
        """构建职业知识图谱 - 清晰的三层同心圆结构"""
        nodes = [{"id": "user_center", "label": "我", "type": "center", "layer": 0,
                  "position": {"x": 0, "y": 0, "z": 0}, "size": 20, "color": "#4A90E2"}]
        edges = []
        
        # 第一圈：技能层（半径 15-20）
        skill_nodes, skill_edges = self._build_skill_layer(user_profile)
        nodes.extend(skill_nodes)
        edges.extend(skill_edges)
        
        # 第二圈：岗位层（半径 35-40）
        job_nodes, job_edges = self._build_job_layer(user_profile, skill_nodes)
        nodes.extend(job_nodes)
        edges.extend(job_edges)
        
        # 第三圈：公司层（半径 55-60）
        company_nodes, company_edges = self._build_company_layer(job_nodes)
        nodes.extend(company_nodes)
        edges.extend(company_edges)
        
        return {
            "nodes": nodes, "edges": edges,
            "layers": {"skills": [n["id"] for n in skill_nodes],
                      "jobs": [n["id"] for n in job_nodes],
                      "companies": [n["id"] for n in company_nodes]},
            "metadata": {
                "total_nodes": len(nodes), 
                "total_edges": len(edges),
                "user_direction": user_profile.target_direction,
                "data_sources": self._get_data_sources_info(job_nodes),  # 添加数据来源信息
                "layer_info": {
                    "layer1": {"name": "技能层", "radius": 18, "count": len(skill_nodes)},
                    "layer2": {"name": "岗位层", "radius": 38, "count": len(job_nodes)},
                    "layer3": {"name": "公司层", "radius": 58, "count": len(company_nodes)}
                }
            }
        }
    
    def _get_data_sources_info(self, job_nodes: List[Dict]) -> Dict[str, int]:
        """统计岗位数据来源"""
        sources = {}
        for job_node in job_nodes:
            source = job_node.get("metadata", {}).get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def _build_skill_layer(self, user_profile: UserSkillProfile) -> tuple:
        """构建技能层 - 按掌握度分组布局，让缺失技能聚集在一起"""
        nodes, edges = [], []
        all_skills = set(user_profile.mastered_skills + user_profile.partial_skills + user_profile.missing_skills)
        
        if not all_skills:
            return nodes, edges
        
        # 按掌握度分组
        mastered = [s for s in all_skills if s in user_profile.mastered_skills]
        partial = [s for s in all_skills if s in user_profile.partial_skills]
        missing = [s for s in all_skills if s in user_profile.missing_skills]
        
        # 为每组分配不同的角度范围，让它们聚集
        def add_skill_group(skill_list, color, size, mastery, angle_start, angle_range, base_radius):
            n = len(skill_list)
            if n == 0:
                return
            
            for i, skill in enumerate(skill_list):
                # 在指定角度范围内均匀分布
                angle = angle_start + (i / max(n-1, 1)) * angle_range
                
                # 使用球面坐标
                theta = angle  # 水平角度
                phi = math.pi / 2 + (i % 3 - 1) * 0.3  # 垂直角度，稍微错开
                
                x = base_radius * math.sin(phi) * math.cos(theta)
                y = base_radius * math.cos(phi)
                z = base_radius * math.sin(phi) * math.sin(theta)
                
                node = {
                    "id": f"skill_{skill}", "label": skill, "type": "skill", "layer": 1,
                    "position": {"x": x, "y": y, "z": z},
                    "size": size, "color": color,
                    "metadata": {"mastery": mastery, "status": "mastered" if mastery == 1.0 else ("partial" if mastery == 0.5 else "missing")}
                }
                nodes.append(node)
                
                # 连接到中心节点 - 线条粗细表示掌握程度
                edges.append({"source": "user_center", "target": f"skill_{skill}", "type": "mastery",
                             "weight": mastery, "width": 1 + mastery * 3, "color": color})
                
                # 技能依赖关系（学习路径）
                if skill in self.skill_dependencies:
                    for dep_skill in self.skill_dependencies[skill]:
                        if dep_skill in all_skills:
                            edges.append({"source": f"skill_{dep_skill}", "target": f"skill_{skill}",
                                        "type": "dependency", "label": "学习路径", "width": 2,
                                        "color": "#FFC107", "dashed": True})
        
        # 已掌握技能：0-120度（前方）
        add_skill_group(mastered, "#4CAF50", 12, 1.0, 0, math.pi * 2/3, 18)
        
        # 部分掌握技能：120-240度（左侧）
        add_skill_group(partial, "#FFC107", 10, 0.5, math.pi * 2/3, math.pi * 2/3, 17)
        
        # 缺失技能：240-360度（右侧），聚集在一起
        add_skill_group(missing, "#F44336", 8, 0.0, math.pi * 4/3, math.pi * 2/3, 16)
        
        return nodes, edges

    
    def _build_job_layer(self, user_profile: UserSkillProfile, skill_nodes: List[Dict]) -> tuple:
        """构建岗位层 - 根据匹配度调整距离，高匹配的岗位离中心更近"""
        nodes, edges = [], []
        jobs = self._get_jobs_cached(keyword=user_profile.target_direction, location="全国", limit=20)
        if not jobs:
            return nodes, edges
        
        n = len(jobs)
        phi = math.pi * (3. - math.sqrt(5.))  # 黄金角
        user_skills = set(user_profile.mastered_skills + user_profile.partial_skills)
        
        for i, job in enumerate(jobs):
            job_skills = set(job.required_skills)
            if not job_skills:
                continue
            
            matched_skills = user_skills & job_skills
            match_rate = len(matched_skills) / len(job_skills) if job_skills else 0
            
            # 关键改变：根据匹配度调整半径 - 匹配度越高，离中心越近
            if match_rate >= 0.7:
                color, size = "#4CAF50", 10
                base_radius = 32  # 高匹配：最近（原来是38）
            elif match_rate >= 0.4:
                color, size = "#FFC107", 9
                base_radius = 38  # 中匹配：中等距离
            else:
                color, size = "#FF9800", 8
                base_radius = 44  # 低匹配：最远（原来是36）
            
            # 斐波那契球面分布
            y = 1 - (i / float(n - 1)) * 2 if n > 1 else 0
            radius_at_y = math.sqrt(1 - y * y)
            theta = phi * i
            
            x = base_radius * radius_at_y * math.cos(theta)
            z = base_radius * radius_at_y * math.sin(theta)
            y_pos = base_radius * y
            
            node = {
                "id": f"job_{i}", "label": job.title, "type": "job", "layer": 2,
                "position": {"x": x, "y": y_pos, "z": z},
                "size": size, "color": color,
                "metadata": {
                    "company": job.company,
                    "salary": f"{job.salary_min}-{job.salary_max}万",
                    "match_rate": match_rate,
                    "skills": list(job_skills),
                    "matched_skills": list(matched_skills),
                    "missing_skills": list(job_skills - user_skills),
                    "location": job.location,
                    "experience": job.experience_required,
                    "source": getattr(job, 'source', 'unknown'),  # 添加数据来源
                    "source_url": getattr(job, 'source_url', '')  # 添加原始链接
                }
            }
            nodes.append(node)
            
            # 连接"我"到岗位 - 线条粗细表示匹配度
            edges.append({
                "source": "user_center",
                "target": f"job_{i}",
                "type": "job_match",
                "label": f"匹配{int(match_rate*100)}%",
                "width": 1 + match_rate * 4,  # 匹配度越高，线越粗
                "color": color,
                "dashed": match_rate < 0.4
            })
            
            # 只连接已匹配的技能（减少视觉混乱）
            for skill in matched_skills:
                skill_node_id = f"skill_{skill}"
                if any(n["id"] == skill_node_id for n in skill_nodes):
                    edges.append({"source": skill_node_id, "target": f"job_{i}",
                                "type": "requirement", "label": "要求",
                                "width": 1.5, "color": "#4CAF50", "dashed": False})
        
        return nodes, edges
    
    def _build_company_layer(self, job_nodes: List[Dict]) -> tuple:
        """构建公司层 - 第三圈，半径55-60，均匀分布"""
        nodes, edges, companies = [], [], {}
        
        # 从岗位中提取公司信息
        for job_node in job_nodes:
            company_name = job_node["metadata"].get("company", "")
            if not company_name or company_name == "未知":
                continue
            if company_name not in companies:
                companies[company_name] = {"jobs": [], "avg_match": 0, "salary_range": []}
            companies[company_name]["jobs"].append(job_node["id"])
            companies[company_name]["avg_match"] += job_node["metadata"]["match_rate"]
            salary = job_node["metadata"].get("salary", "")
            if salary and salary != "面议" and "-" in salary:
                companies[company_name]["salary_range"].append(salary)
        
        # 计算平均匹配度
        for company in companies.values():
            if company["jobs"]:
                company["avg_match"] /= len(company["jobs"])
        
        # 创建公司节点 - 均匀分布在球面上
        company_list = list(companies.keys())
        n = len(company_list)
        if n == 0:
            return nodes, edges
        
        phi = math.pi * (3. - math.sqrt(5.))  # 黄金角
        base_radius = 58  # 第三圈半径
        
        for i, company_name in enumerate(company_list):
            company_data = companies[company_name]
            
            # 斐波那契球面分布
            y = 1 - (i / float(n - 1)) * 2 if n > 1 else 0
            radius_at_y = math.sqrt(1 - y * y)
            theta = phi * i
            
            x = base_radius * radius_at_y * math.cos(theta)
            z = base_radius * radius_at_y * math.sin(theta)
            y_pos = base_radius * y
            
            # 根据薪资和匹配度着色
            if company_data["salary_range"]:
                if company_data["avg_match"] >= 0.6:
                    color, size = "#2196F3", 9  # 高薪高匹配-蓝色
                else:
                    color, size = "#03A9F4", 8  # 高薪低匹配-浅蓝
            else:
                color, size = "#9E9E9E", 7  # 无薪资信息-灰色
            
            node = {
                "id": f"company_{i}", "label": company_name, "type": "company", "layer": 3,
                "position": {"x": x, "y": y_pos, "z": z},
                "size": size, "color": color,
                "metadata": {
                    "job_count": len(company_data["jobs"]),
                    "avg_match": company_data["avg_match"],
                    "salary_info": company_data["salary_range"]
                }
            }
            nodes.append(node)
            
            # 连接公司到岗位（只连接到该公司的岗位）
            for job_id in company_data["jobs"]:
                edges.append({"source": f"company_{i}", "target": job_id,
                            "type": "employment", "width": 1, "color": "#BDBDBD", "dashed": True})
        
        return nodes, edges
    
    def calculate_learning_path(self, user_profile: UserSkillProfile, target_skill: str) -> List[str]:
        """计算学习路径"""
        if target_skill not in self.skill_dependencies:
            return [target_skill]
        path, visited = [], set()
        def dfs(skill):
            if skill in visited:
                return
            visited.add(skill)
            for dep in self.skill_dependencies.get(skill, []):
                if dep not in user_profile.mastered_skills:
                    dfs(dep)
            if skill not in user_profile.mastered_skills:
                path.append(skill)
        dfs(target_skill)
        return path
    
    def find_reachable_jobs(self, user_profile: UserSkillProfile, max_missing_skills: int = 3) -> List[Dict]:
        """找到可达岗位"""
        jobs = self._get_jobs_cached(keyword=user_profile.target_direction, location="全国", limit=50)
        user_skills = set(user_profile.mastered_skills + user_profile.partial_skills)
        reachable = []
        for job in jobs:
            job_skills = set(job.required_skills)
            missing = job_skills - user_skills
            if len(missing) <= max_missing_skills:
                reachable.append({
                    "job": {
                        "title": job.title,
                        "company": job.company,
                        "salary": f"{job.salary_min}-{job.salary_max}万",
                        "location": job.location,
                        "experience": job.experience_required
                    },
                    "missing_skills": list(missing),
                    "match_rate": len(user_skills & job_skills) / len(job_skills) if job_skills else 0
                })
        reachable.sort(key=lambda x: x["match_rate"], reverse=True)
        return reachable


career_kg = CareerKnowledgeGraph()
