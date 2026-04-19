"""
多Agent协作系统 - 智慧洞察
Multi-Agent Collaboration System for Insight Generation

架构特点：
1. 共享记忆空间：所有Agent共用RAG+Neo4j混合检索数据
2. 任务链传递：一个Agent的输出自动成为下一个Agent的输入
3. 冲突仲裁：Gateway协调多个Agent对同一资源的访问
4. 状态广播：Agent完成工作后通知相关方

作者: AI System
版本: 1.0
日期: 2026-04-18
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
from threading import Lock


# ==================== 数据结构 ====================

class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"              # 空闲
    WORKING = "working"        # 工作中
    WAITING = "waiting"        # 等待输入
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    URGENT = 3


@dataclass
class SharedMemory:
    """
    共享记忆空间
    所有Agent共享的数据存储
    """
    user_id: str
    
    # RAG + Neo4j 混合检索数据
    hybrid_data: Dict[str, Any] = field(default_factory=dict)
    
    # Agent工作状态
    agent_states: Dict[str, AgentStatus] = field(default_factory=dict)
    
    # 任务链上下文（Agent之间传递的数据）
    task_chain_context: Dict[str, Any] = field(default_factory=dict)
    
    # Agent输出缓存
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # 资源锁（用于冲突仲裁）
    resource_locks: Dict[str, bool] = field(default_factory=dict)
    
    # 事件订阅（用于状态广播）
    event_subscribers: Dict[str, List[Callable]] = field(default_factory=dict)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update(self, key: str, value: Any):
        """更新共享数据"""
        if key == "hybrid_data":
            self.hybrid_data = value
        elif key == "task_chain_context":
            self.task_chain_context.update(value)
        elif key.startswith("agent_output_"):
            agent_name = key.replace("agent_output_", "")
            self.agent_outputs[agent_name] = value
        
        self.updated_at = datetime.now()
    
    def get(self, key: str, default=None) -> Any:
        """获取共享数据"""
        if key == "hybrid_data":
            return self.hybrid_data
        elif key == "task_chain_context":
            return self.task_chain_context
        elif key.startswith("agent_output_"):
            agent_name = key.replace("agent_output_", "")
            return self.agent_outputs.get(agent_name, default)
        return default
    
    def set_agent_status(self, agent_name: str, status: AgentStatus):
        """设置Agent状态"""
        self.agent_states[agent_name] = status
        self.updated_at = datetime.now()
    
    def get_agent_status(self, agent_name: str) -> AgentStatus:
        """获取Agent状态"""
        return self.agent_states.get(agent_name, AgentStatus.IDLE)
    
    def get_shared_context(self) -> Dict[str, Any]:
        """获取共享上下文数据（供Agent使用）"""
        return self.hybrid_data


@dataclass
class AgentTask:
    """Agent任务"""
    task_id: str
    agent_name: str
    task_type: str  # analyze/generate/evaluate
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他Agent
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: AgentStatus = AgentStatus.WAITING
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class AgentMessage:
    """Agent消息（用于状态广播）"""
    from_agent: str
    to_agents: List[str]  # 接收方Agent列表
    message_type: str  # status_update/task_complete/error/request
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== Agent Gateway ====================

class AgentGateway:
    """
    Agent网关 - 多Agent协调器
    
    职责：
    1. 任务分发：将用户请求分发给合适的Agent
    2. 冲突仲裁：协调多个Agent对共享资源的访问
    3. 状态广播：Agent状态变化时通知相关方
    4. 任务链管理：管理Agent之间的依赖关系
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.shared_memory = SharedMemory(user_id=user_id)
        self.agents: Dict[str, 'CollaborativeAgent'] = {}
        self.task_queue: List[AgentTask] = []
        self.message_queue: List[AgentMessage] = []
        self.lock = Lock()
        
        print(f"✅ [AgentGateway] 初始化完成: user={user_id}")
    
    def _get_view_config(self, agent_chain: Optional[List[str]]) -> Dict[str, Any]:
        """
        根据Agent链获取视图配置
        
        Returns:
            {
                "views": ["relationship"],  # 视图名称列表
                "entity_types": ["Person"],  # 要查询的Entity类型
                "concept_types": ["Skill", "Interest"],  # 要查询的Concept类型
                "event_types": ["Meeting", "Party"],  # 要查询的Event类型
                "relationship_types": ["KNOWS", "RELATED_TO"],  # 要查询的关系类型
                "include_concepts": True,  # 是否包含Concept节点
                "include_events": True  # 是否包含Event节点
            }
        """
        # 默认配置（查询所有）
        config = {
            "views": ["all"],
            "entity_types": ["Person", "School", "Job"],
            "concept_types": ["Skill", "Interest", "Value", "Goal"],
            "event_types": ["Meeting", "Interview", "Party", "Travel"],
            "relationship_types": ["KNOWS", "RELATED_TO", "INTERESTED_IN", "APPLIED_TO", "ADMITTED_TO", "REQUIRES", "HAS_PROFILE", "INVOLVES"],
            "include_concepts": True,
            "include_events": True
        }
        
        if not agent_chain:
            return config
        
        # 根据Agent链确定视图配置
        views = []
        entity_types = set()
        concept_types = set()
        event_types = set()
        relationship_types = set()
        
        for agent_name in agent_chain:
            if agent_name == "relationship":
                # 人际关系视图
                views.append("relationship")
                entity_types.add("Person")
                event_types.update(["Meeting", "Party", "Travel", "Gathering"])
                relationship_types.update(["KNOWS", "RELATED_TO", "INVOLVES", "PART_OF"])
                
            elif agent_name == "education":
                # 教育升学视图
                views.append("education")
                entity_types.add("School")
                concept_types.update(["Interest", "Goal"])
                event_types.update(["Application", "Admission", "Campus"])
                relationship_types.update(["INTERESTED_IN", "APPLIED_TO", "ADMITTED_TO", "HAS_PROFILE", "HAPPENED_AT"])
                
            elif agent_name == "career":
                # 职业规划视图
                views.append("career")
                entity_types.add("Job")
                concept_types.update(["Skill", "Interest", "Goal"])
                event_types.update(["Interview", "Meeting", "Training"])
                relationship_types.update(["INTERESTED_IN", "APPLIED_TO", "REQUIRES", "HAS_PROFILE", "INVOLVES"])
        
        # 如果有指定视图，使用指定的配置
        if views:
            config = {
                "views": views,
                "entity_types": list(entity_types),
                "concept_types": list(concept_types),
                "event_types": list(event_types),
                "relationship_types": list(relationship_types),
                "include_concepts": len(concept_types) > 0,
                "include_events": len(event_types) > 0
            }
        
        return config
    
    def register_agent(self, agent: 'CollaborativeAgent'):
        """注册Agent"""
        self.agents[agent.name] = agent
        agent.set_gateway(self)
        self.shared_memory.set_agent_status(agent.name, AgentStatus.IDLE)
        print(f"  ✓ 注册Agent: {agent.name}")
    
    def submit_task(self, task: AgentTask) -> str:
        """提交任务"""
        with self.lock:
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        print(f"  ✓ 任务已提交: {task.task_id} -> {task.agent_name}")
        return task.task_id
    
    def execute_task_chain(
        self,
        query: str,
        agent_chain: List[str],
        initial_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行任务链（串行模式）
        
        Args:
            query: 用户查询
            agent_chain: Agent执行顺序，如 ['relationship', 'education', 'career']
            initial_data: 初始数据
        
        Returns:
            所有Agent的输出汇总
        """
        print(f"\n{'='*60}")
        print(f"[AgentGateway] 开始执行任务链（串行模式）")
        print(f"  查询: {query}")
        print(f"  Agent链: {' → '.join(agent_chain)}")
        print(f"{'='*60}\n")
        
        # 1. 初始化共享记忆空间
        print("📦 步骤1: 初始化共享记忆空间...")
        self._initialize_shared_memory(query, initial_data, agent_chain)
        
        # 2. 按顺序执行Agent
        results = {}
        for i, agent_name in enumerate(agent_chain):
            print(f"\n🤖 步骤{i+2}: 执行 {agent_name} Agent...")
            
            # 检查Agent是否注册
            if agent_name not in self.agents:
                print(f"  ✗ Agent未注册: {agent_name}")
                continue
            
            agent = self.agents[agent_name]
            
            # 获取输入数据（来自共享记忆或上一个Agent的输出）
            if i == 0:
                # 第一个Agent使用共享记忆中的数据
                input_data = {
                    "query": query,
                    "hybrid_data": self.shared_memory.hybrid_data,
                    "context": initial_data or {}
                }
            else:
                # 后续Agent使用上一个Agent的输出
                prev_agent = agent_chain[i-1]
                prev_output = self.shared_memory.agent_outputs.get(prev_agent, {})
                input_data = {
                    "query": query,
                    "hybrid_data": self.shared_memory.hybrid_data,
                    "prev_agent_output": prev_output,
                    "context": self.shared_memory.task_chain_context
                }
            
            # 执行Agent
            try:
                output = agent.execute(input_data)
                results[agent_name] = output
                
                # 保存输出到共享记忆
                self.shared_memory.agent_outputs[agent_name] = output
                
                # 更新任务链上下文
                self.shared_memory.task_chain_context[f"{agent_name}_insights"] = output.get("key_findings", [])
                
                # 广播完成状态
                self._broadcast_message(AgentMessage(
                    from_agent=agent_name,
                    to_agents=[a for a in agent_chain if a != agent_name],
                    message_type="task_complete",
                    content={"status": "success", "output_summary": output.get("summary", "")}
                ))
                
                print(f"  ✓ {agent_name} Agent 完成")
                
            except Exception as e:
                print(f"  ✗ {agent_name} Agent 失败: {e}")
                results[agent_name] = {"error": str(e)}
                
                # 广播错误状态
                self._broadcast_message(AgentMessage(
                    from_agent=agent_name,
                    to_agents=[a for a in agent_chain if a != agent_name],
                    message_type="error",
                    content={"error": str(e)}
                ))
        
        # 3. 汇总结果
        print(f"\n{'='*60}")
        print(f"[AgentGateway] 任务链执行完成")
        print(f"  成功: {len([r for r in results.values() if 'error' not in r])}/{len(agent_chain)}")
        print(f"{'='*60}\n")
        
        return {
            "query": query,
            "agent_chain": agent_chain,
            "results": results,
            "shared_context": self.shared_memory.task_chain_context,
            "execution_time": (datetime.now() - self.shared_memory.created_at).total_seconds()
        }
    
    async def execute_parallel_agents(
        self,
        query: str,
        agent_names: List[str],
        initial_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        并行执行多个Agent（所有Agent同时思考）
        
        Args:
            query: 用户查询
            agent_names: 要并行执行的Agent列表，如 ['relationship', 'education', 'career']
            initial_data: 初始数据
        
        Returns:
            所有Agent的输出汇总
        """
        print(f"\n{'='*60}")
        print(f"[AgentGateway] 开始并行执行Agent")
        print(f"  查询: {query}")
        print(f"  并行Agent: {', '.join(agent_names)}")
        print(f"{'='*60}\n")
        
        # 1. 初始化共享记忆空间
        print("📦 步骤1: 初始化共享记忆空间...")
        self._initialize_shared_memory(query, initial_data, agent_names)
        
        # 2. 准备所有Agent的输入数据
        input_data = {
            "query": query,
            "hybrid_data": self.shared_memory.hybrid_data,
            "context": initial_data or {}
        }
        
        # 3. 创建并行任务
        print(f"\n🚀 步骤2: 启动 {len(agent_names)} 个Agent并行执行...\n")
        
        async def execute_agent_async(agent_name: str) -> tuple:
            """异步执行单个Agent"""
            if agent_name not in self.agents:
                print(f"  ✗ Agent未注册: {agent_name}")
                return agent_name, {"error": f"Agent未注册: {agent_name}"}
            
            agent = self.agents[agent_name]
            
            try:
                # 在线程池中执行同步的agent.execute
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(None, agent.execute, input_data)
                
                # 保存输出到共享记忆
                self.shared_memory.agent_outputs[agent_name] = output
                
                # 更新任务链上下文
                self.shared_memory.task_chain_context[f"{agent_name}_insights"] = output.get("key_findings", [])
                
                # 广播完成状态
                self._broadcast_message(AgentMessage(
                    from_agent=agent_name,
                    to_agents=[a for a in agent_names if a != agent_name],
                    message_type="task_complete",
                    content={"status": "success", "output_summary": output.get("summary", "")}
                ))
                
                return agent_name, output
                
            except Exception as e:
                print(f"  ✗ {agent_name} Agent 失败: {e}")
                error_result = {"error": str(e)}
                
                # 广播错误状态
                self._broadcast_message(AgentMessage(
                    from_agent=agent_name,
                    to_agents=[a for a in agent_names if a != agent_name],
                    message_type="error",
                    content={"error": str(e)}
                ))
                
                return agent_name, error_result
        
        # 4. 并行执行所有Agent
        tasks = [execute_agent_async(name) for name in agent_names]
        agent_results = await asyncio.gather(*tasks)
        
        # 5. 整理结果
        results = {name: result for name, result in agent_results}
        
        # 6. 汇总结果
        print(f"\n{'='*60}")
        print(f"[AgentGateway] 并行执行完成")
        print(f"  成功: {len([r for r in results.values() if 'error' not in r])}/{len(agent_names)}")
        print(f"{'='*60}\n")
        
        return {
            "query": query,
            "agent_names": agent_names,
            "execution_mode": "parallel",
            "results": results,
            "shared_context": self.shared_memory.task_chain_context,
            "execution_time": (datetime.now() - self.shared_memory.created_at).total_seconds()
        }
    
    def _initialize_shared_memory(self, query: str, initial_data: Optional[Dict], agent_chain: Optional[List[str]] = None):
        """初始化共享记忆空间 - 根据Agent类型查询对应视图的完整数据"""
        from neo4j import GraphDatabase
        from backend.learning.rag_manager import RAGManager
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # 根据 Agent 链确定要查询的视图
        view_config = self._get_view_config(agent_chain)
        
        try:
            # 创建 Neo4j 连接
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "your_password")
            
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            
            # 1. 查询节点
            print(f"  🔍 从 Neo4j 查询节点（视图: {', '.join(view_config['views'])}）...")
            neo4j_nodes = []
            
            with driver.session() as session:
                # 查询 Entity 节点
                if view_config['entity_types']:
                    entity_query = """
                    MATCH (n:Entity {user_id: $user_id})
                    WHERE n.type IN $entity_types
                    RETURN n
                    LIMIT 50
                    """
                    result = session.run(entity_query, user_id=self.user_id, entity_types=view_config['entity_types'])
                    
                    for record in result:
                        node = record['n']
                        node_props = dict(node)
                        
                        # 保留所有属性
                        node_data = {
                            "id": node_props.get('id', node_props.get('entity_id', '')),
                            "type": node_props.get('type', ''),
                            "name": node_props.get('name', ''),
                            "category": node_props.get('category', ''),
                            "content": node_props.get('content', ''),
                            "description": node_props.get('description', ''),
                            "source": "neo4j",
                            "score": 1.0,
                            "confidence": node_props.get('confidence', 1.0)
                        }
                        
                        # 添加 attributes 字段中的所有属性
                        if 'attributes' in node_props and node_props['attributes']:
                            attributes = node_props['attributes']
                            # 如果 attributes 是字符串，尝试解析为 JSON
                            if isinstance(attributes, str):
                                try:
                                    import json
                                    attributes = json.loads(attributes)
                                except:
                                    pass  # 解析失败，跳过
                            
                            # 如果是字典，添加所有属性
                            if isinstance(attributes, dict):
                                for key, value in attributes.items():
                                    if key not in node_data:
                                        node_data[key] = value
                        
                        # 添加其他所有属性
                        for key, value in node_props.items():
                            if key not in node_data and key != 'attributes':
                                node_data[key] = value
                        
                        neo4j_nodes.append(node_data)
                
                # 查询 Concept 节点（如果需要）
                if view_config['include_concepts']:
                    concept_query = """
                    MATCH (u:User {user_id: $user_id})-[:HAS_PROFILE|INTERESTED_IN]->(c:Concept)
                    WHERE c.type IN $concept_types
                    RETURN c
                    LIMIT 20
                    """
                    result = session.run(concept_query, user_id=self.user_id, concept_types=view_config['concept_types'])
                    
                    for record in result:
                        node = record['c']
                        node_props = dict(node)
                        
                        node_data = {
                            "id": node_props.get('id', node_props.get('concept_id', '')),
                            "type": "Concept",
                            "node_type": node_props.get('type', ''),  # Skill/Interest等
                            "name": node_props.get('name', ''),
                            "category": node_props.get('type', ''),
                            "content": node_props.get('description', ''),
                            "description": node_props.get('description', ''),
                            "level": node_props.get('level', ''),
                            "source": "neo4j",
                            "score": 0.8,
                            "confidence": node_props.get('confidence', 0.8)
                        }
                        
                        neo4j_nodes.append(node_data)
                
                # 查询 Event 节点（如果需要）
                if view_config['include_events']:
                    event_query = """
                    MATCH (u:User {user_id: $user_id})-[:PARTICIPATED_IN]->(e:Event)
                    WHERE e.type IN $event_types
                    RETURN e
                    LIMIT 20
                    """
                    result = session.run(event_query, user_id=self.user_id, event_types=view_config['event_types'])
                    
                    for record in result:
                        node = record['e']
                        node_props = dict(node)
                        
                        node_data = {
                            "id": node_props.get('id', node_props.get('event_id', '')),
                            "type": "Event",
                            "node_type": node_props.get('type', ''),
                            "name": node_props.get('name', ''),
                            "category": node_props.get('type', ''),
                            "content": node_props.get('description', ''),
                            "description": node_props.get('description', ''),
                            "start_time": str(node_props.get('start_time', '')),
                            "location": node_props.get('location', ''),
                            "source": "neo4j",
                            "score": 0.7,
                            "confidence": node_props.get('confidence', 0.7)
                        }
                        
                        neo4j_nodes.append(node_data)
            
            print(f"  ✓ Neo4j 查询完成: {len(neo4j_nodes)} 个节点")
            
            # 调试：打印前3个节点的详细信息
            if neo4j_nodes:
                print(f"  [调试] 前3个节点详情:")
                for i, node in enumerate(neo4j_nodes[:3], 1):
                    print(f"    节点{i}: id={node.get('id')}, type={node.get('type')}, name={node.get('name')}, category={node.get('category')}")
            
            # 2. 从 FAISS 查询向量
            print("  🔍 从 FAISS 查询向量...")
            rag_nodes = []
            try:
                rag_manager = RAGManager()
                rag_system = rag_manager.get_system(self.user_id, use_gpu=False)
                
                # 使用 search 方法查询
                rag_results = rag_system.search(query, top_k=10)
                
                for memory in rag_results:
                    rag_nodes.append({
                        "id": memory.id,
                        "type": memory.metadata.get('type', 'Memory'),
                        "name": memory.metadata.get('name', ''),
                        "category": memory.metadata.get('category', 'memory'),
                        "content": memory.content,
                        "source": "faiss",
                        "score": memory.importance
                    })
                
                print(f"  ✓ FAISS 查询完成: {len(rag_nodes)} 个节点")
            except Exception as e:
                print(f"  ⚠️  FAISS 查询失败（跳过）: {e}")
            
            # 3. 合并节点
            all_nodes = neo4j_nodes + rag_nodes
            
            # 4. 查询关系
            print("  🔍 从 Neo4j 查询关系...")
            relationships = []
            
            with driver.session() as session:
                # 构建关系查询
                if view_config['relationship_types']:
                    # 查询1: User到Entity的关系（如INTERESTED_IN, APPLIED_TO等）
                    user_to_entity_query = """
                    MATCH (u:User {user_id: $user_id})-[r]->(e:Entity {user_id: $user_id})
                    WHERE type(r) IN $rel_types
                    RETURN u.user_id as source_id, u.name as source_name,
                           type(r) as rel_type,
                           e.id as target_id, e.name as target_name,
                           properties(r) as rel_props
                    LIMIT 50
                    """
                    result = session.run(user_to_entity_query, user_id=self.user_id, rel_types=view_config['relationship_types'])
                    
                    for record in result:
                        rel_data = {
                            "source": record['source_id'],
                            "target": record['target_id'],
                            "type": record['rel_type'],
                            "source_name": record.get('source_name', 'User'),
                            "target_name": record['target_name']
                        }
                        
                        # 添加关系属性
                        rel_props = record.get('rel_props', {})
                        if rel_props:
                            rel_data.update(rel_props)
                        
                        relationships.append(rel_data)
                    
                    # 查询2: Entity之间的关系（如RELATED_TO, REQUIRES等）
                    entity_to_entity_query = """
                    MATCH (n:Entity {user_id: $user_id})-[r]->(m:Entity {user_id: $user_id})
                    WHERE type(r) IN $rel_types
                    RETURN n.id as source_id, n.name as source_name,
                           type(r) as rel_type,
                           m.id as target_id, m.name as target_name,
                           properties(r) as rel_props
                    LIMIT 50
                    """
                    result = session.run(entity_to_entity_query, user_id=self.user_id, rel_types=view_config['relationship_types'])
                    
                    for record in result:
                        rel_data = {
                            "source": record['source_id'],
                            "target": record['target_id'],
                            "type": record['rel_type'],
                            "source_name": record['source_name'],
                            "target_name": record['target_name']
                        }
                        
                        # 添加关系属性
                        rel_props = record.get('rel_props', {})
                        if rel_props:
                            rel_data.update(rel_props)
                            rel_data.update(rel_props)
                        
                        relationships.append(rel_data)
            
            driver.close()
            print(f"  ✓ 关系查询完成: {len(relationships)} 条关系")
            
            # 5. 计算影响力摘要
            influence_summary = {}
            for node in all_nodes:
                category = node.get('category', 'unknown')
                score = node.get('score', 0)
                influence_summary[category] = influence_summary.get(category, 0) + score
            
            # 归一化
            total_influence = sum(influence_summary.values())
            if total_influence > 0:
                influence_summary = {k: v / total_influence for k, v in influence_summary.items()}
            
            # 6. 构建混合数据
            hybrid_data = {
                "nodes": all_nodes,
                "relationships": relationships,
                "influence_summary": influence_summary,
                "stats": {
                    "neo4j": len(neo4j_nodes),
                    "faiss": len(rag_nodes),
                    "total": len(all_nodes)
                }
            }
            
            self.shared_memory.hybrid_data = hybrid_data
            
            print(f"  ✓ 数据整合完成: {len(all_nodes)} 个节点, {len(relationships)} 条关系")
            
        except Exception as e:
            print(f"  ✗ 数据查询失败: {e}")
            import traceback
            traceback.print_exc()
            self.shared_memory.hybrid_data = {"nodes": [], "relationships": [], "influence_summary": {}, "stats": {}}
        
        # 设置初始上下文
        if initial_data:
            self.shared_memory.task_chain_context.update(initial_data)
    
    def _broadcast_message(self, message: AgentMessage):
        """广播消息给相关Agent"""
        self.message_queue.append(message)
        
        # 通知订阅者
        for to_agent in message.to_agents:
            if to_agent in self.agents:
                agent = self.agents[to_agent]
                agent.on_message_received(message)
    
    def acquire_resource(self, agent_name: str, resource_name: str) -> bool:
        """
        获取资源锁（冲突仲裁）
        
        Returns:
            True if acquired, False if resource is locked
        """
        with self.lock:
            if self.shared_memory.resource_locks.get(resource_name, False):
                print(f"  ⚠️ 资源冲突: {agent_name} 等待资源 {resource_name}")
                return False
            
            self.shared_memory.resource_locks[resource_name] = True
            print(f"  ✓ 资源获取: {agent_name} 获得资源 {resource_name}")
            return True
    
    def release_resource(self, agent_name: str, resource_name: str):
        """释放资源锁"""
        with self.lock:
            self.shared_memory.resource_locks[resource_name] = False
            print(f"  ✓ 资源释放: {agent_name} 释放资源 {resource_name}")
    
    def get_shared_data(self, key: str, default=None) -> Any:
        """获取共享数据"""
        return self.shared_memory.get(key, default)
    
    def set_shared_data(self, key: str, value: Any):
        """设置共享数据"""
        self.shared_memory.update(key, value)


# ==================== Collaborative Agent Base ====================

class CollaborativeAgent:
    """
    协作Agent基类
    
    特点：
    1. 访问共享记忆空间
    2. 接收和发送消息
    3. 支持任务链传递
    """
    
    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.gateway: Optional[AgentGateway] = None
        self.status = AgentStatus.IDLE
    
    def set_gateway(self, gateway: AgentGateway):
        """设置网关"""
        self.gateway = gateway
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            input_data: 输入数据，包含：
                - query: 用户查询
                - hybrid_data: 共享的混合检索数据
                - prev_agent_output: 上一个Agent的输出（如果有）
                - context: 任务链上下文
        
        Returns:
            输出数据，将传递给下一个Agent
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def on_message_received(self, message: AgentMessage):
        """接收消息回调"""
        print(f"  📨 [{self.name}] 收到消息: {message.message_type} from {message.from_agent}")
    
    def send_message(self, to_agents: List[str], message_type: str, content: Dict):
        """发送消息"""
        if self.gateway:
            message = AgentMessage(
                from_agent=self.name,
                to_agents=to_agents,
                message_type=message_type,
                content=content
            )
            self.gateway._broadcast_message(message)
    
    def get_shared_data(self, key: str, default=None) -> Any:
        """从共享记忆获取数据"""
        if self.gateway:
            return self.gateway.get_shared_data(key, default)
        return default
    
    def set_shared_data(self, key: str, value: Any):
        """设置共享数据"""
        if self.gateway:
            self.gateway.set_shared_data(key, value)


# ==================== 便捷函数 ====================

def create_multi_agent_system(user_id: str) -> AgentGateway:
    """创建多Agent协作系统"""
    gateway = AgentGateway(user_id)
    return gateway


# ==================== 示例用法 ====================

if __name__ == "__main__":
    # 创建多Agent系统
    gateway = create_multi_agent_system("test_user")
    
    # 注册Agent（实际使用时会注册真实的Agent）
    # gateway.register_agent(RelationshipAgent())
    # gateway.register_agent(EducationAgent())
    # gateway.register_agent(CareerAgent())
    
    # 执行任务链
    results = gateway.execute_task_chain(
        query="分析我的整体发展情况",
        agent_chain=["relationship", "education", "career"]
    )
    
    print(json.dumps(results, indent=2, ensure_ascii=False))
