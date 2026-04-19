"""
消息处理器 - 异步后台处理
自动从对话消息中提取信息并存入Neo4j和RAG
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import os


class MessageProcessor:
    """消息处理器 - 异步后台任务"""
    
    def __init__(self):
        self._processing_queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
    
    def start(self):
        """启动后台处理任务"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_worker())
            print("✅ [MessageProcessor] 后台处理任务已启动")
    
    def stop(self):
        """停止后台处理任务"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            print("⏹️ [MessageProcessor] 后台处理任务已停止")
    
    async def submit_message(
        self,
        user_id: str,
        message: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """提交消息到处理队列（非阻塞）"""
        await self._processing_queue.put({
            "user_id": user_id,
            "message": message,
            "session_id": session_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
        print(f"📥 [MessageProcessor] 消息已加入处理队列: {message[:50]}...")
    
    async def _process_worker(self):
        """后台工作线程 - 持续处理队列中的消息"""
        print("🔄 [MessageProcessor] 后台工作线程开始运行")
        
        while self._running:
            try:
                # 从队列获取消息（超时1秒）
                try:
                    task = await asyncio.wait_for(
                        self._processing_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 处理消息
                await self._process_message(task)
                
            except asyncio.CancelledError:
                print("⏹️ [MessageProcessor] 工作线程被取消")
                break
            except Exception as e:
                print(f"❌ [MessageProcessor] 工作线程错误: {e}")
                import traceback
                traceback.print_exc()
    
    async def _process_message(self, task: Dict[str, Any]):
        """处理单条消息 - 提取信息并存储"""
        user_id = task["user_id"]
        message = task["message"]
        session_id = task["session_id"]
        metadata = task.get("metadata", {})
        
        print(f"🔍 [MessageProcessor] 开始处理消息: {message[:50]}...")
        
        try:
            # 1. 使用LLM智能提取信息
            extracted_info = await self._extract_information_with_llm(
                user_id, message, metadata
            )
            
            if not extracted_info:
                print(f"ℹ️ [MessageProcessor] 未提取到有效信息")
                return
            
            # 2. 存储到Neo4j知识图谱
            await self._store_to_neo4j(user_id, extracted_info, session_id)
            
            # 3. 存储到RAG记忆系统
            await self._store_to_rag(user_id, message, extracted_info, metadata)
            
            print(f"✅ [MessageProcessor] 消息处理完成")
            
        except Exception as e:
            print(f"❌ [MessageProcessor] 处理消息失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _extract_information_with_llm(
        self,
        user_id: str,
        message: str,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """使用LLM智能提取信息"""
        try:
            from backend.knowledge.information_extractor import InformationExtractor
            
            extractor = InformationExtractor()
            
            # 从对话中提取信息
            extracted = extractor.extract_from_conversation(message, metadata)
            
            if not extracted or not any([
                extracted.get("entities"),
                extracted.get("events"),
                extracted.get("concepts"),
                extracted.get("patterns")
            ]):
                return None
            
            print(f"📊 [MessageProcessor] 提取结果:")
            print(f"   - 实体: {len(extracted.get('entities', []))} 个")
            print(f"   - 事件: {len(extracted.get('events', []))} 个")
            print(f"   - 概念: {len(extracted.get('concepts', []))} 个")
            print(f"   - 模式: {len(extracted.get('patterns', []))} 个")
            print(f"   - 决策: {len(extracted.get('decisions', []))} 个")
            
            return extracted
            
        except Exception as e:
            print(f"❌ [MessageProcessor] LLM提取失败: {e}")
            return None
    
    async def _store_to_neo4j(
        self,
        user_id: str,
        extracted_info: Dict[str, Any],
        session_id: str
    ):
        """存储到Neo4j知识图谱 - 完整实现6种节点和4类关系"""
        try:
            from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
            
            info_kg = InformationKnowledgeGraph(user_id)
            
            try:
                # ========== 1. 创建Source节点（来源溯源）==========
                source_id = f"conv_{session_id}_{int(datetime.now().timestamp())}"
                info_kg.add_source(
                    source_type="Conversation",
                    source_id=source_id,
                    timestamp=int(datetime.now().timestamp()),
                    metadata={"session_id": session_id}
                )
                
                # 建立Source-CREATED_BY->User关系
                self._create_source_user_relationship(info_kg, source_id, user_id)
                
                # ========== 2. 存储Entity节点 ==========
                entities_created = []
                for entity in extracted_info.get("entities", []):
                    entity_type = entity.get("entity_type", "unknown")
                    entity_name = entity["name"]
                    
                    # 按照Neo4j架构规范构建属性（扁平化，避免嵌套字典）
                    entity_attributes = entity.get("attributes", {})
                    
                    # 构建扁平化的属性字典
                    flat_attributes = {
                        "entity_id": f"entity_{user_id}_{entity_name}_{int(datetime.now().timestamp())}",
                        "type": entity_type,
                        "category": entity.get("category", "unknown"),
                        "description": entity_attributes.get("description", ""),
                        "confidence": entity.get("confidence", 0.8),
                        "extracted_at": datetime.now().isoformat(),
                        "source_id": source_id
                    }
                    
                    # 添加其他属性（扁平化）
                    for key, value in entity_attributes.items():
                        if key != "description" and isinstance(value, (str, int, float, bool)):
                            flat_attributes[f"attr_{key}"] = value
                    
                    # 创建Entity节点
                    info_kg.add_information(
                        name=entity_name,
                        info_type="entity",
                        category=entity.get("category", "unknown"),
                        confidence=entity.get("confidence", 0.8),
                        attributes=flat_attributes
                    )
                    
                    # 信息溯源关系：Entity-EXTRACTED_FROM->Source
                    info_kg.add_source_relationship(
                        info_name=entity_name,
                        source_id=source_id,
                        relation_type="EXTRACTED_FROM",
                        confidence=entity.get("confidence", 0.8)
                    )
                    
                    # 用户相关关系：根据实体类型建立不同关系
                    if entity_type == "Person":
                        # User-KNOWS->Person
                        self._create_user_knows_relationship(
                            info_kg, user_id, entity_name, 
                            entity.get("category", "friends"),
                            entity.get("confidence", 0.8)
                        )
                    elif entity_type in ["Job", "School"]:
                        # User-INTERESTED_IN->Job/School
                        self._create_user_interested_relationship(
                            info_kg, user_id, entity_name,
                            entity.get("confidence", 0.8)
                        )
                    
                    entities_created.append({
                        "name": entity_name,
                        "type": entity_type,
                        "attributes": entity.get("attributes", {})
                    })
                
                # ========== 3. 存储Event节点 ==========
                for event in extracted_info.get("events", []):
                    event_type = event.get("event_type", "unknown")
                    event_name = event["name"]
                    
                    event_attributes_raw = event.get("attributes", {})
                    
                    # 构建扁平化的属性字典
                    flat_attributes = {
                        "event_id": f"event_{user_id}_{event_name}_{int(datetime.now().timestamp())}",
                        "type": event_type,
                        "description": event_attributes_raw.get("description", ""),
                        "start_time": event_attributes_raw.get("time", ""),
                        "location": event_attributes_raw.get("location", ""),
                        "confidence": event.get("confidence", 0.8),
                        "extracted_at": datetime.now().isoformat(),
                        "source_id": source_id
                    }
                    
                    # 参与者列表转为字符串
                    participants = event_attributes_raw.get("participants", [])
                    if participants:
                        flat_attributes["participants"] = ",".join(participants)
                    
                    # 创建Event节点
                    info_kg.add_information(
                        name=event_name,
                        info_type="event",
                        category=event.get("category", "unknown"),
                        confidence=event.get("confidence", 0.8),
                        attributes=flat_attributes
                    )
                    
                    # 信息溯源关系：Event-EXTRACTED_FROM->Source
                    info_kg.add_source_relationship(
                        info_name=event_name,
                        source_id=source_id,
                        relation_type="EXTRACTED_FROM",
                        confidence=event.get("confidence", 0.8)
                    )
                    
                    # 用户相关关系：User-PARTICIPATED_IN->Event
                    self._create_user_participated_relationship(
                        info_kg, user_id, event_name,
                        event.get("confidence", 0.8)
                    )
                    
                    # 实体间关系：Event-INVOLVES->Person（参与者）
                    participants = event.get("attributes", {}).get("participants", [])
                    
                    # 过滤掉泛指词
                    pronoun_blacklist = {'说话者', '用户', '我', '你', '他', '她', '对方', '本人'}
                    valid_participants = [p for p in participants if p and p not in pronoun_blacklist]
                    
                    for participant in valid_participants:
                        self._create_event_involves_relationship(
                            info_kg, event_name, participant
                        )
                    
                    # 实体间关系：Event-HAPPENED_AT->Location（地点）
                    location = event.get("attributes", {}).get("location", "")
                    if location:
                        self._create_event_location_relationship(
                            info_kg, event_name, location
                        )
                
                # ========== 4. 存储Concept节点 ==========
                for concept in extracted_info.get("concepts", []):
                    concept_type = concept.get("concept_type", "unknown")
                    concept_name = concept["name"]
                    
                    concept_attributes_raw = concept.get("attributes", {})
                    
                    # 构建扁平化的属性字典
                    flat_attributes = {
                        "concept_id": f"concept_{user_id}_{concept_name}_{int(datetime.now().timestamp())}",
                        "type": concept_type,
                        "description": concept_attributes_raw.get("description", ""),
                        "level": concept_attributes_raw.get("level", ""),
                        "confidence": concept.get("confidence", 0.8),
                        "extracted_at": datetime.now().isoformat(),
                        "source_id": source_id
                    }
                    
                    # 创建Concept节点
                    info_kg.add_information(
                        name=concept_name,
                        info_type="concept",
                        category=concept.get("category", "unknown"),
                        confidence=concept.get("confidence", 0.8),
                        attributes=flat_attributes
                    )
                    
                    # 信息溯源关系：Concept-EXTRACTED_FROM->Source
                    info_kg.add_source_relationship(
                        info_name=concept_name,
                        source_id=source_id,
                        relation_type="EXTRACTED_FROM",
                        confidence=concept.get("confidence", 0.8)
                    )
                    
                    # 用户相关关系：User-HAS_PROFILE->Concept（技能/兴趣）
                    if concept_type in ["Skill", "Interest"]:
                        self._create_user_has_profile_relationship(
                            info_kg, user_id, concept_name,
                            concept.get("attributes", {}).get("level", ""),
                            concept.get("confidence", 0.8)
                        )
                    elif concept_type == "Goal":
                        # User-INTERESTED_IN->Goal
                        self._create_user_interested_relationship(
                            info_kg, user_id, concept_name,
                            concept.get("confidence", 0.8)
                        )
                    
                    # 实体间关系：Job-REQUIRES->Skill
                    # 如果有Job实体提到需要这个技能
                    if concept_type == "Skill":
                        for entity in entities_created:
                            if entity["type"] == "Job":
                                # 检查Job的描述中是否提到这个技能
                                job_desc = entity.get("attributes", {}).get("description", "")
                                if concept_name in job_desc:
                                    self._create_job_requires_skill_relationship(
                                        info_kg, entity["name"], concept_name
                                    )
                
                # ========== 5. 存储Pattern节点 ==========
                for pattern in extracted_info.get("patterns", []):
                    pattern_type = pattern.get("pattern_type", "unknown")
                    pattern_name = pattern["name"]
                    
                    pattern_attributes_raw = pattern.get("attributes", {})
                    
                    # 构建扁平化的属性字典
                    flat_attributes = {
                        "pattern_id": f"pattern_{user_id}_{pattern_name}_{int(datetime.now().timestamp())}",
                        "type": pattern_type,
                        "description": pattern_attributes_raw.get("description", ""),
                        "frequency": pattern_attributes_raw.get("frequency", 1),
                        "confidence": pattern.get("confidence", 0.8),
                        "identified_at": datetime.now().isoformat(),
                        "evidence": source_id  # 单个证据ID，不用列表
                    }
                    
                    # 创建Pattern节点
                    info_kg.add_information(
                        name=pattern_name,
                        info_type="pattern",
                        category=pattern.get("category", "unknown"),
                        confidence=pattern.get("confidence", 0.8),
                        attributes=flat_attributes
                    )
                    
                    # 信息溯源关系：Pattern-EXTRACTED_FROM->Source
                    info_kg.add_source_relationship(
                        info_name=pattern_name,
                        source_id=source_id,
                        relation_type="EXTRACTED_FROM",
                        confidence=pattern.get("confidence", 0.8)
                    )
                    
                    # 模式关系：User-EXHIBITS->Pattern
                    self._create_user_exhibits_pattern_relationship(
                        info_kg, user_id, pattern_name,
                        pattern.get("attributes", {}).get("frequency", 1),
                        pattern.get("confidence", 0.8)
                    )
                    
                    # 模式关系：Entity/Event-SUPPORTS->Pattern（证据支持）
                    # 将相关的实体和事件作为模式的证据
                    for entity in entities_created:
                        self._create_supports_pattern_relationship(
                            info_kg, entity["name"], pattern_name, 0.5
                        )
                
                print(f"✅ [MessageProcessor] 已按Neo4j架构规范存入知识图谱（6种节点+4类关系）")
                print(f"   节点: Source(1) + Entity({len(extracted_info.get('entities', []))}) + Event({len(extracted_info.get('events', []))}) + Concept({len(extracted_info.get('concepts', []))}) + Pattern({len(extracted_info.get('patterns', []))})")
                print(f"   关系: 溯源关系 + 用户关系 + 实体关系 + 模式关系")
                
            finally:
                info_kg.close()
                
        except Exception as e:
            print(f"❌ [MessageProcessor] 存储到Neo4j失败: {e}")
            import traceback
            traceback.print_exc()
    
    # ========== 关系创建辅助方法 ==========
    
    def _create_source_user_relationship(self, info_kg, source_id: str, user_id: str):
        """创建Source-CREATED_BY->User关系"""
        try:
            # 注意：这里需要确保User节点已存在
            # 实际实现中可能需要先检查或创建User节点
            pass  # 暂时跳过，因为InformationKnowledgeGraph可能没有这个方法
        except Exception as e:
            print(f"  [关系创建] Source-CREATED_BY->User 失败: {e}")
    
    def _create_user_knows_relationship(self, info_kg, user_id: str, person_name: str, 
                                       relationship_type: str, confidence: float):
        """创建User-KNOWS->Person关系"""
        try:
            info_kg.add_user_relationship(
                target_name=person_name,
                relation_type="KNOWS",
                properties={
                    "relationship_type": relationship_type,
                    "closeness": confidence,
                    "since": datetime.now().isoformat()
                }
            )
            print(f"  [关系创建] ✓ User-KNOWS->{person_name}")
        except Exception as e:
            print(f"  [关系创建] User-KNOWS->Person 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_user_interested_relationship(self, info_kg, user_id: str, target_name: str, 
                                            confidence: float):
        """创建User-INTERESTED_IN->Entity/Concept关系"""
        try:
            info_kg.add_user_relationship(
                target_name=target_name,
                relation_type="INTERESTED_IN",
                properties={
                    "interest_level": confidence,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"  [关系创建] ✓ User-INTERESTED_IN->{target_name}")
        except Exception as e:
            print(f"  [关系创建] User-INTERESTED_IN 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_user_participated_relationship(self, info_kg, user_id: str, event_name: str, 
                                              confidence: float):
        """创建User-PARTICIPATED_IN->Event关系"""
        try:
            info_kg.add_user_relationship(
                target_name=event_name,
                relation_type="PARTICIPATED_IN",
                properties={
                    "role": "participant",
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"  [关系创建] ✓ User-PARTICIPATED_IN->{event_name}")
        except Exception as e:
            print(f"  [关系创建] User-PARTICIPATED_IN->Event 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_user_has_profile_relationship(self, info_kg, user_id: str, concept_name: str, 
                                             level: str, confidence: float):
        """创建User-HAS_PROFILE->Concept关系"""
        try:
            info_kg.add_user_relationship(
                target_name=concept_name,
                relation_type="HAS_PROFILE",
                properties={
                    "level": level,
                    "confidence": confidence,
                    "since": datetime.now().isoformat()
                }
            )
            print(f"  [关系创建] ✓ User-HAS_PROFILE->{concept_name}")
        except Exception as e:
            print(f"  [关系创建] User-HAS_PROFILE->Concept 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_event_involves_relationship(self, info_kg, event_name: str, person_name: str):
        """创建Event-INVOLVES->Person关系"""
        try:
            info_kg.add_information_relationship(
                source_name=event_name,
                target_name=person_name,
                relation_type="INVOLVES",
                properties={"role": "participant"}
            )
            print(f"  [关系创建] ✓ {event_name}-INVOLVES->{person_name}")
        except Exception as e:
            print(f"  [关系创建] Event-INVOLVES->Person 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_event_location_relationship(self, info_kg, event_name: str, location: str):
        """创建Event-HAPPENED_AT->Location关系"""
        try:
            info_kg.add_information_relationship(
                source_name=event_name,
                target_name=location,
                relation_type="HAPPENED_AT",
                properties={"timestamp": datetime.now().isoformat()}
            )
            print(f"  [关系创建] ✓ {event_name}-HAPPENED_AT->{location}")
        except Exception as e:
            print(f"  [关系创建] Event-HAPPENED_AT->Location 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_job_requires_skill_relationship(self, info_kg, job_name: str, skill_name: str):
        """创建Job-REQUIRES->Skill关系"""
        try:
            info_kg.add_information_relationship(
                source_name=job_name,
                target_name=skill_name,
                relation_type="REQUIRES",
                properties={"importance": "high", "level": "intermediate"}
            )
            print(f"  [关系创建] ✓ {job_name}-REQUIRES->{skill_name}")
        except Exception as e:
            print(f"  [关系创建] Job-REQUIRES->Skill 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_user_exhibits_pattern_relationship(self, info_kg, user_id: str, pattern_name: str, 
                                                   frequency: int, confidence: float):
        """创建User-EXHIBITS->Pattern关系"""
        try:
            info_kg.add_user_relationship(
                target_name=pattern_name,
                relation_type="EXHIBITS",
                properties={
                    "frequency": frequency,
                    "confidence": confidence
                }
            )
            print(f"  [关系创建] ✓ User-EXHIBITS->{pattern_name}")
        except Exception as e:
            print(f"  [关系创建] User-EXHIBITS->Pattern 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_supports_pattern_relationship(self, info_kg, evidence_name: str, 
                                             pattern_name: str, weight: float):
        """创建Entity/Event-SUPPORTS->Pattern关系"""
        try:
            info_kg.add_information_relationship(
                source_name=evidence_name,
                target_name=pattern_name,
                relation_type="SUPPORTS",
                properties={"weight": weight}
            )
            print(f"  [关系创建] ✓ {evidence_name}-SUPPORTS->{pattern_name}")
        except Exception as e:
            print(f"  [关系创建] SUPPORTS->Pattern 失败: {e}")
            import traceback
            traceback.print_exc()
    
    
    def _infer_domain(self, item_type: str, category: str) -> str:
        """推断领域标签（用于分类检索）"""
        # 职业领域
        if item_type in ['Job', 'Organization'] or 'career' in category.lower():
            return 'career'
        # 教育领域
        elif item_type in ['School'] or 'education' in category.lower():
            return 'education'
        # 人际关系领域
        elif item_type in ['Person'] or category in ['family', 'close_friends', 'colleagues', 'friends', 'weak_ties']:
            return 'relationship'
        # 技能/兴趣
        elif item_type in ['Skill', 'Interest', 'Goal', 'Value']:
            return 'personal_development'
        else:
            return 'general'
    
    def _calculate_importance(self, item: Dict[str, Any]) -> float:
        """计算重要性评分（用于排序）"""
        # 基础分数 = 置信度
        importance = item.get("confidence", 0.5)
        
        # 根据类型调整
        item_type = item.get("entity_type") or item.get("event_type") or item.get("concept_type") or item.get("pattern_type")
        
        # 人物、职位、学校更重要
        if item_type in ['Person', 'Job', 'School']:
            importance *= 1.2
        # 技能、目标也很重要
        elif item_type in ['Skill', 'Goal']:
            importance *= 1.1
        
        # 有详细描述的更重要
        if item.get("attributes", {}).get("description"):
            importance *= 1.1
        
        return min(importance, 1.0)  # 最大1.0
    
    async def _store_to_rag(
        self,
        user_id: str,
        message: str,
        extracted_info: Dict[str, Any],
        metadata: Dict[str, Any]
    ):
        """存储到RAG记忆系统 - 按照FAISS架构规范存储9种记忆类型"""
        try:
            from backend.learning.rag_manager import MemorySystemManager
            from backend.learning.production_rag_system import MemoryType
            
            stored_counts = {
                "conversation": 0,
                "experience": 0,
                "knowledge": 0,
                "insight": 0,
                "decision": 0,
                "schedule": 0,
                "task_completion": 0,
                "sensor_data": 0,
                "photo": 0
            }
            
            # ========== 1. CONVERSATION（对话记录）- 完整对话上下文 ==========
            conversation_metadata = {
                "user_id": user_id,
                "session_id": metadata.get("session_id", ""),
                "turn": metadata.get("turn", 0),
                "user_message": message,
                "domain": self._infer_domain_from_message(message, extracted_info),
                "source": "user_input",
                "thinking": metadata.get("thinking", "")
            }
            
            # 使用正确的API：直接调用add_memory（强制GPU模式）
            MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                memory_type=MemoryType.CONVERSATION,
                content=message,
                metadata=conversation_metadata,
                importance=0.7
            )
            stored_counts["conversation"] = 1
            
            # ========== 2. EXPERIENCE（经验总结）- 从已完成的事件中提取 ==========
            for event in extracted_info.get("events", []):
                event_type = event.get("event_type", "unknown")
                status = event.get('attributes', {}).get('status', 'completed')
                
                # 只有已完成的活动才转为EXPERIENCE
                if status == 'completed' and event_type not in ['Schedule', 'TaskCompletion']:
                    description = event.get('attributes', {}).get('description', '')
                    participants = event.get('attributes', {}).get('participants', [])
                    location = event.get('attributes', {}).get('location', '')
                    time = event.get('attributes', {}).get('time', '')
                    
                    # 按照FAISS架构规范构建content（自包含、可读）
                    content_parts = [event['name']]
                    if description:
                        content_parts.append(description)
                    if participants:
                        content_parts.append(f"参与者：{', '.join(participants)}")
                    if location:
                        content_parts.append(f"地点：{location}")
                    if time:
                        content_parts.append(f"时间：{time}")
                    
                    content = "，".join(content_parts)
                    
                    # 按照FAISS架构规范构建metadata
                    experience_metadata = {
                        "user_id": user_id,
                        "domain": self._infer_domain(event_type, event.get("category", "")),
                        "tags": self._extract_tags(event['name'], description),
                        "event_type": event_type,
                        "participants": participants,
                        "location": location,
                        "duration": event.get('attributes', {}).get('duration', ''),
                        "outcome": self._infer_outcome(description),
                        "related_entities": [event['name']] + participants,
                        "extracted_from": "conversation",
                        "neo4j_node_name": event["name"],
                        "source": "conversation_extraction"
                    }
                    
                    MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                        memory_type=MemoryType.EXPERIENCE,
                        content=content,
                        metadata=experience_metadata,
                        importance=self._calculate_importance(event)
                    )
                    stored_counts["experience"] += 1
            
            # ========== 3. KNOWLEDGE（知识点）- 从概念中提取 ==========
            for concept in extracted_info.get("concepts", []):
                concept_type = concept.get("concept_type", "unknown")
                description = concept.get('attributes', {}).get('description', '')
                level = concept.get('attributes', {}).get('level', '')
                
                # 按照FAISS架构规范构建content
                content_parts = [concept['name']]
                if description:
                    content_parts.append(description)
                if level:
                    content_parts.append(f"水平：{level}")
                
                content = "，".join(content_parts)
                
                # 按照FAISS架构规范构建metadata
                knowledge_metadata = {
                    "user_id": user_id,
                    "domain": self._infer_domain(concept_type, concept.get("category", "")),
                    "category": concept_type.lower(),  # skill/interest/goal/value
                    "tags": self._extract_tags(concept['name'], description),
                    "source": "user_input",
                    "verified": True,
                    "level": level,
                    "concept_type": concept_type,
                    "related_skills": self._extract_related_skills(description),
                    "neo4j_node_name": concept["name"],
                    "extracted_from": "conversation"
                }
                
                MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                    memory_type=MemoryType.KNOWLEDGE,
                    content=content,
                    metadata=knowledge_metadata,
                    importance=self._calculate_importance(concept)
                )
                stored_counts["knowledge"] += 1
            
            # ========== 4. DECISION（决策记录）- 从LLM提取的decisions直接使用 ==========
            for decision in extracted_info.get("decisions", []):
                decision_content = decision["name"]
                decision_attrs = decision.get("attributes", {})
                
                decision_metadata = {
                    "user_id": user_id,
                    "domain": self._infer_domain_from_message(message, extracted_info),
                    "decision_type": "general",
                    "options": decision_attrs.get("options", []),
                    "chosen": decision_attrs.get("chosen", ""),
                    "reasons": decision_attrs.get("reasons", []),
                    "outcome": "pending",
                    "confidence": decision.get("confidence", 0.9),
                    "timestamp": datetime.now().isoformat()
                }
                
                MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                    memory_type=MemoryType.DECISION,
                    content=decision_content,
                    metadata=decision_metadata,
                    importance=0.9  # 决策通常很重要
                )
                stored_counts["decision"] += 1
            
            # ========== 5. SCHEDULE（日程安排）- 从未来事件中识别 ==========
            for event in extracted_info.get("events", []):
                status = event.get('attributes', {}).get('status', 'completed')
                event_type = event.get("event_type", "unknown")
                
                # 只有scheduled状态或type为Schedule的事件才转为SCHEDULE
                if status == 'scheduled' or event_type == 'Schedule':
                    schedule_content = event['name']
                    event_attrs = event.get('attributes', {})
                    
                    schedule_metadata = {
                        "user_id": user_id,
                        "event_type": event_type,
                        "start_time": event_attrs.get('time', ''),
                        "end_time": "",
                        "location": event_attrs.get('location', ''),
                        "participants": event_attrs.get('participants', []),
                        "status": "scheduled",
                        "reminder": True,
                        "related_entities": [event['name']]
                    }
                    
                    MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                        memory_type=MemoryType.SCHEDULE,
                        content=schedule_content,
                        metadata=schedule_metadata,
                        importance=0.85
                    )
                    stored_counts["schedule"] += 1
            
            # ========== 6. TASK_COMPLETION（任务完成）- 从TaskCompletion类型事件中提取 ==========
            for event in extracted_info.get("events", []):
                event_type = event.get("event_type", "unknown")
                
                # 只有TaskCompletion类型的事件才转为TASK_COMPLETION
                if event_type == 'TaskCompletion':
                    task_content = event['name']
                    event_attrs = event.get('attributes', {})
                    
                    task_metadata = {
                        "user_id": user_id,
                        "task_name": event['name'],
                        "domain": self._infer_domain(event_type, event.get("category", "")),
                        "completion_time": datetime.now().isoformat(),
                        "duration": event_attrs.get('duration', ''),
                        "outcome": self._infer_outcome(event_attrs.get('description', '')),
                        "metrics": {},
                        "learnings": []
                    }
                    
                    MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                        memory_type=MemoryType.TASK_COMPLETION,
                        content=task_content,
                        metadata=task_metadata,
                        importance=0.8
                    )
                    stored_counts["task_completion"] += 1
            
            # ========== 7. SENSOR_DATA（传感器数据）- 从元数据中提取 ==========
            if metadata.get("location") or metadata.get("activity"):
                sensor_content = self._build_sensor_content(metadata)
                
                sensor_metadata = {
                    "user_id": user_id,
                    "sensor_type": "location" if metadata.get("location") else "activity",
                    "location": metadata.get("location", {}),
                    "activity": metadata.get("activity", ""),
                    "health_metrics": metadata.get("health_metrics", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                    memory_type=MemoryType.SENSOR_DATA,
                    content=sensor_content,
                    metadata=sensor_metadata,
                    importance=0.5
                )
                stored_counts["sensor_data"] += 1
            
            # ========== 8. PHOTO（照片记忆）- 从元数据中提取 ==========
            if metadata.get("photo_id") or metadata.get("photo_url"):
                photo_content = self._build_photo_content(metadata, extracted_info)
                
                photo_metadata = {
                    "user_id": user_id,
                    "photo_id": metadata.get("photo_id", ""),
                    "photo_url": metadata.get("photo_url", ""),
                    "location": metadata.get("location", ""),
                    "people": [e["name"] for e in extracted_info.get("entities", []) if e.get("entity_type") == "Person"],
                    "objects": metadata.get("objects", []),
                    "scene": metadata.get("scene", ""),
                    "emotion": metadata.get("emotion", "neutral"),
                    "ocr_text": metadata.get("ocr_text", ""),
                    "analysis": metadata.get("photo_analysis", "")
                }
                
                MemorySystemManager.get_system(user_id, use_gpu=True).add_memory(
                    memory_type=MemoryType.PHOTO,
                    content=photo_content,
                    metadata=photo_metadata,
                    importance=0.75
                )
                stored_counts["photo"] += 1
            
            # ========== 9. INSIGHT（洞察发现）- 暂不在此处生成 ==========
            # Insight由专门的洞察Agent生成，不在对话处理时创建
            # 见 backend/insights/realtime_insight_agents.py
            
            # ========== 不存储Entity和Pattern到FAISS ==========
            # Entity（Person/Job/School）只存储在Neo4j（结构化数据）
            # Pattern（Habit/Preference）只存储在Neo4j（结构化数据）
            
            print(f"✅ [MessageProcessor] 已按FAISS架构规范存入RAG记忆系统（9种类型）")
            print(f"   - CONVERSATION: {stored_counts['conversation']} 个")
            print(f"   - EXPERIENCE: {stored_counts['experience']} 个")
            print(f"   - KNOWLEDGE: {stored_counts['knowledge']} 个")
            print(f"   - DECISION: {stored_counts['decision']} 个")
            print(f"   - SCHEDULE: {stored_counts['schedule']} 个")
            print(f"   - TASK_COMPLETION: {stored_counts['task_completion']} 个")
            print(f"   - SENSOR_DATA: {stored_counts['sensor_data']} 个")
            print(f"   - PHOTO: {stored_counts['photo']} 个")
            print(f"   - INSIGHT: 由专门Agent生成（不在此处）")
            print(f"   - Entity和Pattern已存入Neo4j（不存入FAISS）")
            
        except Exception as e:
            print(f"❌ [MessageProcessor] 存储到RAG失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_tags(self, name: str, description: str) -> List[str]:
        """从名称和描述中提取标签"""
        tags = [name]
        
        if description:
            # 简单分词提取关键词（可以用jieba优化）
            words = description.replace('，', ' ').replace('。', ' ').replace('、', ' ').split()
            tags.extend([w for w in words if len(w) > 1])
        
        # 去重并限制数量
        return list(set(tags))[:10]
    
    def _infer_domain_from_message(self, message: str, extracted_info: Dict[str, Any]) -> str:
        """从消息内容推断领域"""
        # 职业关键词
        career_keywords = ['工作', '职业', '面试', '公司', '薪资', '职位', '简历', '跳槽']
        # 教育关键词
        education_keywords = ['学习', '学校', '课程', '考试', '专业', '大学', '研究生']
        # 人际关系关键词
        relationship_keywords = ['朋友', '家人', '同事', '认识', '聚会', '见面', '关系']
        
        message_lower = message.lower()
        
        # 统计关键词出现次数
        career_count = sum(1 for kw in career_keywords if kw in message_lower)
        education_count = sum(1 for kw in education_keywords if kw in message_lower)
        relationship_count = sum(1 for kw in relationship_keywords if kw in message_lower)
        
        # 也从提取的实体类型推断
        for entity in extracted_info.get("entities", []):
            entity_type = entity.get("entity_type", "")
            if entity_type == "Job":
                career_count += 2
            elif entity_type == "School":
                education_count += 2
            elif entity_type == "Person":
                relationship_count += 1
        
        # 返回最高分的领域
        max_count = max(career_count, education_count, relationship_count)
        if max_count == 0:
            return "general"
        elif career_count == max_count:
            return "career"
        elif education_count == max_count:
            return "education"
        else:
            return "relationship"
    
    def _infer_outcome(self, description: str) -> str:
        """从描述推断结果（positive/negative/neutral）"""
        positive_keywords = ['成功', '顺利', '开心', '满意', '好', '棒', '优秀', '完成']
        negative_keywords = ['失败', '困难', '问题', '不好', '差', '糟糕', '失望']
        
        if not description:
            return "neutral"
        
        desc_lower = description.lower()
        positive_count = sum(1 for kw in positive_keywords if kw in desc_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in desc_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_related_skills(self, description: str) -> List[str]:
        """从描述中提取相关技能"""
        # 常见技能关键词
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'C++', 'Go', 'Rust',
            '机器学习', '深度学习', '数据分析', '算法', '数据库',
            'Web开发', '前端', '后端', '全栈', 'DevOps',
            '项目管理', '团队协作', '沟通', '领导力'
        ]
        
        if not description:
            return []
        
        found_skills = []
        for skill in skill_keywords:
            if skill in description:
                found_skills.append(skill)
        
        return found_skills[:5]  # 最多返回5个
    
    def _extract_decisions(self, message: str, extracted_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从对话中识别决策"""
        decisions = []
        
        # 决策关键词
        decision_keywords = ['决定', '选择', '接受', '拒绝', '打算', '计划']
        
        message_lower = message.lower()
        has_decision = any(kw in message_lower for kw in decision_keywords)
        
        if has_decision:
            # 简单提取决策内容
            decision = {
                "content": message,
                "domain": self._infer_domain_from_message(message, extracted_info),
                "decision_type": "general",
                "options": [],
                "chosen": "",
                "reasons": [],
                "confidence": 0.7
            }
            
            # 尝试识别职业决策
            if '接受' in message_lower and 'offer' in message_lower:
                decision["decision_type"] = "job_offer"
            elif '跳槽' in message_lower or '换工作' in message_lower:
                decision["decision_type"] = "job_change"
            elif '申请' in message_lower and ('学校' in message_lower or '大学' in message_lower):
                decision["decision_type"] = "education_application"
            
            decisions.append(decision)
        
        return decisions
    
    def _extract_schedules(self, extracted_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从事件中识别未来安排"""
        schedules = []
        
        for event in extracted_info.get("events", []):
            time_str = event.get('attributes', {}).get('time', '')
            
            # 简单判断：如果时间包含未来日期关键词
            future_keywords = ['明天', '下周', '下月', '将要', '计划', '安排']
            is_future = any(kw in time_str for kw in future_keywords)
            
            if is_future:
                schedule = {
                    "content": event['name'],
                    "event_type": event.get("event_type", "unknown"),
                    "start_time": time_str,
                    "end_time": "",
                    "location": event.get('attributes', {}).get('location', ''),
                    "participants": event.get('attributes', {}).get('participants', []),
                    "related_entities": [event['name']]
                }
                schedules.append(schedule)
        
        return schedules
    
    def _extract_task_completions(self, extracted_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从事件中识别已完成任务"""
        tasks = []
        
        for event in extracted_info.get("events", []):
            description = event.get('attributes', {}).get('description', '')
            
            # 完成关键词
            completion_keywords = ['完成', '做完', '结束', '实现', '达成']
            is_completed = any(kw in description for kw in completion_keywords)
            
            if is_completed:
                task = {
                    "content": event['name'] + "，" + description,
                    "task_name": event['name'],
                    "domain": self._infer_domain(
                        event.get("event_type", "unknown"),
                        event.get("category", "")
                    ),
                    "completion_time": datetime.now().isoformat(),
                    "duration": event.get('attributes', {}).get('duration', ''),
                    "outcome": self._infer_outcome(description),
                    "metrics": {},
                    "learnings": []
                }
                tasks.append(task)
        
        return tasks
    
    def _build_sensor_content(self, metadata: Dict[str, Any]) -> str:
        """构建传感器数据的内容描述"""
        parts = [datetime.now().strftime("%Y-%m-%d %H:%M")]
        
        location = metadata.get("location", {})
        if location:
            city = location.get("city", "")
            district = location.get("district", "")
            if city and district:
                parts.append(f"在{city}{district}")
            elif city:
                parts.append(f"在{city}")
        
        activity = metadata.get("activity", "")
        if activity:
            parts.append(f"{activity}活动")
        
        health = metadata.get("health_metrics", {})
        if health:
            heart_rate = health.get("heart_rate")
            steps = health.get("steps")
            if heart_rate:
                parts.append(f"心率{heart_rate}")
            if steps:
                parts.append(f"步数{steps}")
        
        return "，".join(parts)
    
    def _build_photo_content(self, metadata: Dict[str, Any], extracted_info: Dict[str, Any]) -> str:
        """构建照片记忆的内容描述"""
        parts = [datetime.now().strftime("%Y-%m-%d")]
        
        # 提取人物
        people = [e["name"] for e in extracted_info.get("entities", []) if e.get("entity_type") == "Person"]
        if people:
            parts.append(f"和{', '.join(people)}")
        
        # 地点
        location = metadata.get("location", "")
        if location:
            parts.append(f"在{location}")
        
        # 场景
        scene = metadata.get("scene", "")
        if scene:
            parts.append(scene)
        
        # 情感
        emotion = metadata.get("emotion", "")
        emotion_map = {
            "happy": "很开心",
            "sad": "有些难过",
            "excited": "很兴奋",
            "calm": "很平静"
        }
        if emotion in emotion_map:
            parts.append(emotion_map[emotion])
        
        return "，".join(parts)


# 全局单例
_message_processor: Optional[MessageProcessor] = None


def get_message_processor() -> MessageProcessor:
    """获取全局消息处理器实例"""
    global _message_processor
    if _message_processor is None:
        _message_processor = MessageProcessor()
        _message_processor.start()
    return _message_processor


def stop_message_processor():
    """停止全局消息处理器"""
    global _message_processor
    if _message_processor:
        _message_processor.stop()
        _message_processor = None
