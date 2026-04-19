"""
基于决策系统的日程分析器
从决策记录、知识图谱、RAG中提取任务和优先级，而非健康数据
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json


class DecisionBasedAnalyzer:
    """基于决策系统的日程分析器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 获取决策相关系统
        from backend.startup_manager import StartupManager
        from backend.database.db_manager import db_manager
        
        self.rag_system = StartupManager.get_user_system(user_id, 'rag')
        if not self.rag_system:
            self.rag_system = StartupManager.get_user_system('default_user', 'rag')
        
        self.db_manager = db_manager
        
        print(f"[决策日程] 初始化用户 {user_id} 的决策导向日程分析器")
    
    def analyze_decision_context(self) -> Dict[str, Any]:
        """
        分析用户的决策上下文，提取任务和优先级
        
        Returns:
            {
                'active_decisions': 进行中的决策列表,
                'action_items': 待执行的行动项,
                'priorities': 优先级排序,
                'constraints': 时间和资源约束,
                'goals': 短期和长期目标
            }
        """
        print(f"[决策日程] 开始分析用户 {self.user_id} 的决策上下文...")
        
        # 1. 从RAG获取决策相关记忆
        decision_memories = self._get_decision_memories()
        
        # 2. 从知识图谱获取用户背景
        user_context = self._get_user_context_from_kg()
        
        # 3. 从数据库获取决策记录
        decision_records = self._get_decision_records()
        
        # 4. 提取行动项和任务
        action_items = self._extract_action_items(decision_memories, decision_records)
        
        # 5. 分析优先级
        priorities = self._analyze_priorities(decision_memories, user_context)
        
        # 6. 识别约束条件
        constraints = self._identify_constraints(decision_memories, user_context)
        
        # 7. 提取目标
        goals = self._extract_goals(decision_memories, decision_records)
        
        print(f"[决策日程] 分析完成: {len(action_items)} 个行动项, {len(goals)} 个目标")
        
        return {
            'active_decisions': decision_records,
            'action_items': action_items,
            'priorities': priorities,
            'constraints': constraints,
            'goals': goals,
            'user_context': user_context
        }
    
    def _get_decision_memories(self) -> List[Dict]:
        """从RAG获取决策相关记忆"""
        try:
            from backend.learning.production_rag_system import MemoryType
            
            if not self.rag_system:
                print("[决策日程] RAG系统未初始化")
                return []
            
            print(f"[日程分析] 成功获取用户 {self.user_id} 的RAG系统")
            print(f"[日程分析] 开始分析用户 {self.user_id} 的决策和时间模式...")
            
            # 搜索决策相关记忆
            results = self.rag_system.search(
                query="决策 目标 计划 任务 行动",
                memory_types=[MemoryType.DECISION, MemoryType.CONVERSATION],
                top_k=30
            )
            
            memories = []
            for result in results:
                try:
                    if hasattr(result, 'content'):
                        memories.append({
                            'content': str(result.content),
                            'metadata': dict(result.metadata) if hasattr(result, 'metadata') else {},
                            'timestamp': result.metadata.get('timestamp') if hasattr(result, 'metadata') else None
                        })
                    else:
                        memories.append({
                            'content': str(result.get('content', '')),
                            'metadata': dict(result.get('metadata', {})),
                            'timestamp': result.get('metadata', {}).get('timestamp')
                        })
                except Exception as e:
                    print(f"[决策日程] 处理单条记忆失败: {e}")
                    continue
            
            print(f"[决策日程] 从RAG获取了 {len(memories)} 条决策记忆")
            print(f"[日程分析] ✅ 基于决策数据: {len(memories)} 条记忆")
            return memories
            
        except Exception as e:
            import traceback
            print(f"[决策日程] 获取决策记忆失败: {e}")
            print(traceback.format_exc())
            return []
    
    def _get_user_context_from_kg(self) -> Dict[str, Any]:
        """从知识图谱获取用户背景"""
        try:
            from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
            
            kg = InformationKnowledgeGraph(self.user_id)
            
            context = {
                'relationships': [],
                'education': [],
                'career': []
            }
            
            # 获取人际关系（可能影响决策优先级）
            relationships = kg.get_relationships(self.user_id, limit=10)
            for rel in relationships:
                # 确保转换为可序列化的字典
                if isinstance(rel, dict):
                    context['relationships'].append({
                        'type': str(rel.get('relationship_type', '')),
                        'name': str(rel.get('person_name', ''))
                    })
                else:
                    # 如果是 Neo4j 对象，提取属性
                    try:
                        context['relationships'].append({
                            'type': str(rel.get('relationship_type', '') if hasattr(rel, 'get') else ''),
                            'name': str(rel.get('person_name', '') if hasattr(rel, 'get') else '')
                        })
                    except:
                        pass
            
            # 获取教育背景
            education_nodes = kg.get_nodes_by_type(self.user_id, "School", limit=5)
            for node in education_nodes:
                if isinstance(node, dict):
                    name = node.get('name', '')
                else:
                    name = node.get('name', '') if hasattr(node, 'get') else ''
                if name:
                    context['education'].append(str(name))
            
            # 获取职业信息
            career_nodes = kg.get_nodes_by_type(self.user_id, "Job", limit=5)
            for node in career_nodes:
                if isinstance(node, dict):
                    name = node.get('name', '')
                else:
                    name = node.get('name', '') if hasattr(node, 'get') else ''
                if name:
                    context['career'].append(str(name))
            
            kg.close()
            
            print(f"[决策日程] 从知识图谱获取用户背景: {len(context['relationships'])} 个关系, {len(context['education'])} 个教育, {len(context['career'])} 个职业")
            return context
            
        except Exception as e:
            import traceback
            print(f"[决策日程] 获取知识图谱背景失败: {e}")
            print(traceback.format_exc())
            return {'relationships': [], 'education': [], 'career': []}
    
    def _get_decision_records(self) -> List[Dict]:
        """从数据库获取决策记录"""
        try:
            # 这里应该查询决策记录表
            # 暂时返回空列表，等待决策记录表的实现
            return []
        except Exception as e:
            print(f"[决策日程] 获取决策记录失败: {e}")
            return []
    
    def _extract_action_items(
        self,
        memories: List[Dict],
        records: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        从决策记忆和记录中提取行动项
        
        Returns:
            行动项列表，每个包含：title, priority, deadline, category
        """
        action_items = []
        
        # 从记忆中提取行动项
        for memory in memories:
            try:
                content = str(memory.get('content', ''))
                
                # 简单的关键词匹配（实际应该用LLM提取）
                if any(keyword in content for keyword in ['需要', '应该', '计划', '准备', '安排']):
                    action_items.append({
                        'title': content[:50] + '...' if len(content) > 50 else content,
                        'priority': 'medium',
                        'deadline': None,
                        'category': 'decision_related',
                        'source': 'memory'
                    })
            except Exception as e:
                print(f"[决策日程] 处理记忆行动项失败: {e}")
                continue
        
        # 从决策记录中提取
        for record in records:
            try:
                if 'action_plan' in record:
                    for action in record.get('action_plan', []):
                        action_items.append({
                            'title': str(action.get('title', '')),
                            'priority': str(action.get('priority', 'medium')),
                            'deadline': str(action.get('deadline')) if action.get('deadline') else None,
                            'category': 'decision_action',
                            'source': 'decision_record'
                        })
            except Exception as e:
                print(f"[决策日程] 处理决策记录行动项失败: {e}")
                continue
        
        return action_items[:20]  # 限制数量
    
    def _analyze_priorities(
        self,
        memories: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        分析优先级
        
        Returns:
            优先级权重字典
        """
        priorities = {
            'career': 0.3,  # 职业发展
            'education': 0.25,  # 教育学习
            'relationship': 0.2,  # 人际关系
            'personal_growth': 0.15,  # 个人成长
            'other': 0.1  # 其他
        }
        
        # 根据用户背景调整优先级
        if len(context.get('career', [])) > 0:
            priorities['career'] += 0.1
        
        if len(context.get('education', [])) > 0:
            priorities['education'] += 0.1
        
        # 归一化
        total = sum(priorities.values())
        priorities = {k: v/total for k, v in priorities.items()}
        
        return priorities
    
    def _identify_constraints(
        self,
        memories: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        识别约束条件
        
        Returns:
            约束条件字典
        """
        constraints = {
            'time_constraints': [],
            'resource_constraints': [],
            'dependency_constraints': []
        }
        
        # 从记忆中提取约束
        for memory in memories:
            try:
                content = str(memory.get('content', ''))
                
                if any(keyword in content for keyword in ['截止', '期限', 'deadline']):
                    constraints['time_constraints'].append(content[:100])
                
                if any(keyword in content for keyword in ['预算', '资金', '成本']):
                    constraints['resource_constraints'].append(content[:100])
            except Exception as e:
                print(f"[决策日程] 处理约束失败: {e}")
                continue
        
        return constraints
    
    def _extract_goals(
        self,
        memories: List[Dict],
        records: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        提取目标
        
        Returns:
            目标字典，包含短期和长期目标
        """
        goals = {
            'short_term': [],  # 短期目标（1-3个月）
            'long_term': []    # 长期目标（6个月以上）
        }
        
        # 从记忆中提取目标
        for memory in memories:
            try:
                content = str(memory.get('content', ''))
                
                if any(keyword in content for keyword in ['目标', 'goal', '希望', '想要']):
                    # 简单分类（实际应该用LLM判断）
                    if any(keyword in content for keyword in ['近期', '这个月', '下个月']):
                        goals['short_term'].append(content[:100])
                    else:
                        goals['long_term'].append(content[:100])
            except Exception as e:
                print(f"[决策日程] 处理目标失败: {e}")
                continue
        
        return goals
    
    def generate_decision_based_schedule(
        self,
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        生成基于决策的日程安排
        
        Args:
            target_date: 目标日期
        
        Returns:
            日程安排
        """
        if not target_date:
            target_date = datetime.now()
        
        # 分析决策上下文
        context = self.analyze_decision_context()
        
        # 生成日程
        schedule = {
            'date': target_date.date().isoformat(),
            'timeline': [],
            'summary': {
                'total_tasks': len(context['action_items']),
                'priorities': context['priorities'],
                'goals': context['goals']
            }
        }
        
        # 根据优先级安排任务
        for i, action in enumerate(context['action_items'][:10]):  # 限制每天10个任务
            start_hour = 9 + i  # 简单的时间分配
            schedule['timeline'].append({
                'start': f"{start_hour:02d}:00",
                'end': f"{start_hour+1:02d}:00",
                'title': action['title'],
                'type': action['category'],
                'priority': action['priority']
            })
        
        return schedule
