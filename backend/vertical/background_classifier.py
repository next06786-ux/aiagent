"""
后台LLM分类任务
系统启动时自动开始异步分类三个垂直领域的节点
"""

import threading
import time
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class BackgroundClassificationTask:
    """后台分类任务管理器"""
    
    def __init__(self):
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        print("[BackgroundClassifier] 后台分类任务管理器已初始化")
    
    def start(self):
        """启动后台分类任务"""
        if self.is_running:
            print("[BackgroundClassifier] 后台任务已在运行")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_classification_tasks, daemon=True)
        self.thread.start()
        print("[BackgroundClassifier] 后台分类任务已启动")
    
    def stop(self):
        """停止后台分类任务"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[BackgroundClassifier] 后台分类任务已停止")
    
    def _run_classification_tasks(self):
        """运行分类任务（在后台线程中）"""
        # 等待5秒，确保系统完全启动
        time.sleep(5)
        
        print("\n" + "="*60)
        print("[BackgroundClassifier] 开始后台LLM分类任务")
        print("="*60)
        
        try:
            # 任务1: 分类教育节点
            self._classify_education_nodes()
            
            # 任务2: 分类职业节点
            self._classify_career_nodes()
            
            # 任务3: 分类人际关系节点
            self._classify_relationship_nodes()
            
            print("\n" + "="*60)
            print("[BackgroundClassifier] 所有后台分类任务完成")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"[BackgroundClassifier] 后台分类任务失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _classify_education_nodes(self):
        """分类教育节点（跳过已分类节点）"""
        if not self.is_running:
            return
        
        print("\n[BackgroundClassifier] 任务1: 开始分类教育节点...")
        
        try:
            from backend.vertical.education.neo4j_education_kg import get_neo4j_education_kg
            from backend.vertical.llm_batch_classifier import get_llm_batch_classifier
            
            edu_kg = get_neo4j_education_kg()
            classifier = get_llm_batch_classifier()
            
            # 获取所有学校节点
            schools = edu_kg._get_schools_from_neo4j(limit=200)
            
            if not schools:
                print("[BackgroundClassifier] 未找到教育节点")
                return
            
            # 检查哪些节点已经分类（从Neo4j读取分类属性）
            classified_count = 0
            unclassified_nodes = []
            
            for school in schools:
                # 检查是否已有LLM分类属性（不是学校类别category）
                has_classification = (
                    school.get('vertical_domain') is not None or 
                    school.get('classification_score') is not None
                )
                
                if has_classification:
                    classified_count += 1
                else:
                    # 未分类，需要LLM处理
                    unclassified_nodes.append({
                        'id': school.get('id', ''),
                        'name': school['name'],
                        'type': 'school',
                        'properties': {
                            'location': school.get('location', ''),
                            'is_985': school.get('is_985', False),
                            'is_211': school.get('is_211', False),
                            'gpa_requirement': school.get('gpa_requirement', 3.0)
                        }
                    })
            
            print(f"[BackgroundClassifier] 已分类: {classified_count}/{len(schools)}，待分类: {len(unclassified_nodes)}")
            
            if not unclassified_nodes:
                print("[BackgroundClassifier] 所有教育节点已分类，跳过LLM调用")
                return
            
            # 只对未分类节点进行LLM分类
            print(f"[BackgroundClassifier] 开始增量分类 {len(unclassified_nodes)} 所未分类学校...")
            results = classifier.classify_nodes_batch_incremental(unclassified_nodes, None)
            
            # 将分类结果写回Neo4j（持久化）
            self._save_classification_to_neo4j(edu_kg, unclassified_nodes, results, 'School')
            
            print(f"[BackgroundClassifier] 教育节点分类完成，已持久化到Neo4j")
            
        except Exception as e:
            print(f"[BackgroundClassifier] 教育节点分类失败: {e}")
    
    def _classify_career_nodes(self):
        """分类职业节点（跳过已分类节点）"""
        if not self.is_running:
            return
        
        print("\n[BackgroundClassifier] 任务2: 开始分类职业节点...")
        
        try:
            from backend.vertical.career.neo4j_career_kg import get_neo4j_career_kg
            from backend.vertical.llm_batch_classifier import get_llm_batch_classifier
            
            career_kg = get_neo4j_career_kg()
            classifier = get_llm_batch_classifier()
            
            # 获取职位节点（多个关键词）
            keywords = ["Python", "Java", "前端", "后端", "算法"]
            all_jobs = []
            
            for keyword in keywords:
                if not self.is_running:
                    break
                jobs = career_kg._get_jobs_from_neo4j(keyword=keyword, limit=20)
                all_jobs.extend(jobs)
            
            if not all_jobs:
                print("[BackgroundClassifier] 未找到职业节点")
                return
            
            # 去重
            seen_ids = set()
            unique_jobs = []
            for job in all_jobs:
                job_id = job.get('id', '')
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    unique_jobs.append(job)
            
            # 检查哪些节点已经分类
            classified_count = 0
            unclassified_nodes = []
            
            for job in unique_jobs[:100]:  # 最多100个
                # 检查是否已有LLM分类属性
                has_classification = (
                    job.get('vertical_domain') is not None or 
                    job.get('classification_score') is not None
                )
                
                if has_classification:
                    classified_count += 1
                else:
                    unclassified_nodes.append({
                        'id': job.get('id', ''),
                        'name': job['position_name'],
                        'type': 'position',
                        'properties': {
                            'company': job['company_name'],
                            'salary': job.get('salary', 0),
                            'city': job.get('city', '')
                        }
                    })
            
            print(f"[BackgroundClassifier] 已分类: {classified_count}/{len(unique_jobs[:100])}，待分类: {len(unclassified_nodes)}")
            
            if not unclassified_nodes:
                print("[BackgroundClassifier] 所有职业节点已分类，跳过LLM调用")
                return
            
            # 只对未分类节点进行LLM分类
            print(f"[BackgroundClassifier] 开始增量分类 {len(unclassified_nodes)} 个未分类职位...")
            results = classifier.classify_nodes_batch_incremental(unclassified_nodes, None)
            
            # 将分类结果写回Neo4j（持久化）
            self._save_classification_to_neo4j(career_kg, unclassified_nodes, results, 'Job')
            
            print(f"[BackgroundClassifier] 职业节点分类完成，已持久化到Neo4j")
            
        except Exception as e:
            print(f"[BackgroundClassifier] 职业节点分类失败: {e}")
    
    def _classify_relationship_nodes(self):
        """分类人际关系节点"""
        if not self.is_running:
            return
        
        print("\n[BackgroundClassifier] 任务3: 开始分类人际关系节点...")
        
        try:
            # 人际关系节点通常是用户特定的，这里跳过通用分类
            print("[BackgroundClassifier] 人际关系节点为用户特定数据，跳过通用分类")
            
        except Exception as e:
            print(f"[BackgroundClassifier] 人际关系节点分类失败: {e}")
    
    def _save_classification_to_neo4j(self, kg_instance, nodes, results, node_label):
        """
        将分类结果持久化到Neo4j（L3缓存）
        
        Args:
            kg_instance: 知识图谱实例（edu_kg 或 career_kg）
            nodes: 节点列表
            results: 分类结果列表
            node_label: Neo4j节点标签（'School' 或 'Job'）
        """
        try:
            if not hasattr(kg_instance, 'driver'):
                print("[BackgroundClassifier] 知识图谱实例没有driver，跳过持久化")
                return
            
            with kg_instance.driver.session() as session:
                for node, result in zip(nodes, results):
                    node_name = node.get('name', '')
                    if not node_name:
                        continue
                    
                    # 更新Neo4j节点属性
                    query = f"""
                        MATCH (n:{node_label})
                        WHERE n.name = $name
                        SET n.vertical_domain = $vertical_domain,
                            n.category = $category,
                            n.classification_score = $score,
                            n.classification_reasons = $reasons,
                            n.classified_at = timestamp()
                        RETURN n.name as name
                    """
                    
                    session.run(
                        query,
                        name=node_name,
                        vertical_domain=result.vertical_domain,
                        category=result.category,
                        score=result.score,
                        reasons=result.reasons
                    )
            
            print(f"[BackgroundClassifier] 已将 {len(results)} 个节点的分类结果持久化到Neo4j")
            
        except Exception as e:
            print(f"[BackgroundClassifier] 持久化分类结果失败: {e}")
            import traceback
            traceback.print_exc()


# 全局单例
_background_task = None

def get_background_classifier() -> BackgroundClassificationTask:
    """获取后台分类任务单例"""
    global _background_task
    if _background_task is None:
        _background_task = BackgroundClassificationTask()
    return _background_task


def start_background_classification():
    """启动后台分类任务（在系统启动时调用）"""
    task = get_background_classifier()
    task.start()


def stop_background_classification():
    """停止后台分类任务（在系统关闭时调用）"""
    task = get_background_classifier()
    task.stop()
