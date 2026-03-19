"""
自主决策引擎
Autonomous Decision Engine
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import json


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 5  # 紧急且重要
    HIGH = 4      # 重要
    MEDIUM = 3    # 一般
    LOW = 2       # 不重要
    IDLE = 1      # 空闲时执行


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SceneContext:
    """场景上下文"""
    scene_type: str  # 场景类型
    objects: List[str]  # 检测到的物体
    actions: List[str]  # 识别到的行为
    intent: str  # 推断的意图
    timestamp: datetime
    location: Optional[str] = None
    confidence: float = 0.0


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    urgency: float  # 紧急度 [0, 1]
    importance: float  # 重要性 [0, 1]
    user_preference: float  # 用户偏好 [0, 1]
    estimated_duration: int  # 预计耗时(秒)
    deadline: Optional[datetime] = None
    dependencies: List[str] = None  # 依赖的任务ID
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []
    
    def compute_score(self) -> float:
        """计算任务优先级分数"""
        # 基础分数
        base_score = (
            self.urgency * 0.4 +
            self.importance * 0.3 +
            self.user_preference * 0.3
        )
        
        # 优先级加成
        priority_bonus = self.priority.value * 0.1
        
        # 截止时间惩罚
        deadline_penalty = 0.0
        if self.deadline:
            time_left = (self.deadline - datetime.now()).total_seconds()
            if time_left < 3600:  # 1小时内
                deadline_penalty = 0.3
            elif time_left < 86400:  # 24小时内
                deadline_penalty = 0.1
        
        return base_score + priority_bonus + deadline_penalty


class SceneAnalyzer:
    """场景分析器"""
    
    def __init__(self):
        self.scene_rules = self._load_scene_rules()
    
    def _load_scene_rules(self) -> Dict:
        """加载场景规则"""
        return {
            '厨房': {
                'typical_objects': ['食物', '餐具', '厨具', '冰箱'],
                'typical_actions': ['烹饪', '进餐', '洗碗'],
                'typical_intents': ['准备早餐', '准备午餐', '准备晚餐']
            },
            '卧室': {
                'typical_objects': ['床', '衣柜', '台灯'],
                'typical_actions': ['睡觉', '穿衣', '休息'],
                'typical_intents': ['睡前准备', '起床准备', '休息放松']
            },
            '办公室': {
                'typical_objects': ['电脑', '文件', '桌椅'],
                'typical_actions': ['工作', '打字', '开会'],
                'typical_intents': ['工作准备', '会议准备', '完成任务']
            }
        }
    
    async def analyze(self, multimodal_input: Dict) -> SceneContext:
        """
        分析场景
        
        Args:
            multimodal_input: 多模态输入
                - tags: 层次化标签
                - timestamp: 时间戳
                - location: 位置(可选)
        """
        tags = multimodal_input.get('tags', {})
        
        # 提取场景信息
        scene_type = self._extract_top_prediction(tags.get('scene', {}))
        objects = self._extract_multi_predictions(tags.get('objects', {}), top_k=5)
        actions = self._extract_multi_predictions(tags.get('actions', {}), top_k=3)
        intent = self._extract_top_prediction(tags.get('intents', {}))
        
        # 计算置信度
        confidence = self._compute_confidence(tags)
        
        return SceneContext(
            scene_type=scene_type,
            objects=objects,
            actions=actions,
            intent=intent,
            timestamp=multimodal_input.get('timestamp', datetime.now()),
            location=multimodal_input.get('location'),
            confidence=confidence
        )
    
    def _extract_top_prediction(self, pred_dict: Dict) -> str:
        """提取最高概率的预测"""
        if not pred_dict or 'probs' not in pred_dict:
            return 'unknown'
        probs = pred_dict['probs']
        if len(probs) == 0:
            return 'unknown'
        return str(probs.argmax().item())
    
    def _extract_multi_predictions(self, pred_dict: Dict, top_k: int = 5) -> List[str]:
        """提取多个高概率预测"""
        if not pred_dict or 'probs' not in pred_dict:
            return []
        probs = pred_dict['probs']
        if len(probs) == 0:
            return []
        top_indices = probs.topk(min(top_k, len(probs))).indices
        return [str(idx.item()) for idx in top_indices]
    
    def _compute_confidence(self, tags: Dict) -> float:
        """计算整体置信度"""
        confidences = []
        for level in ['scene', 'objects', 'actions', 'intents']:
            if level in tags and 'probs' in tags[level]:
                max_prob = tags[level]['probs'].max().item()
                confidences.append(max_prob)
        return sum(confidences) / len(confidences) if confidences else 0.0


class TaskPlanner:
    """任务规划器"""
    
    def __init__(self):
        self.task_templates = self._load_task_templates()
        
        # 接入大模型
        try:
            from llm.llm_service import get_llm_service
            self.llm = get_llm_service()
            self.llm_enabled = self.llm is not None
            if self.llm_enabled:
                print("✓ 任务规划器已接入大模型")
        except Exception as e:
            self.llm = None
            self.llm_enabled = False
            print(f"⚠️ 任务规划器未接入大模型: {e}")
    
    def _load_task_templates(self) -> Dict:
        """加载任务模板"""
        return {
            '准备早餐': [
                {
                    'type': 'reminder',
                    'description': '提醒用户吃早餐',
                    'priority': TaskPriority.HIGH,
                    'urgency': 0.8,
                    'importance': 0.7
                },
                {
                    'type': 'nutrition_check',
                    'description': '检查营养均衡',
                    'priority': TaskPriority.MEDIUM,
                    'urgency': 0.5,
                    'importance': 0.6
                }
            ],
            '睡前准备': [
                {
                    'type': 'reminder',
                    'description': '提醒关闭电器',
                    'priority': TaskPriority.HIGH,
                    'urgency': 0.7,
                    'importance': 0.8
                },
                {
                    'type': 'environment_check',
                    'description': '检查门窗安全',
                    'priority': TaskPriority.HIGH,
                    'urgency': 0.8,
                    'importance': 0.9
                },
                {
                    'type': 'health_reminder',
                    'description': '提醒按时休息',
                    'priority': TaskPriority.MEDIUM,
                    'urgency': 0.6,
                    'importance': 0.7
                }
            ],
            '工作准备': [
                {
                    'type': 'schedule_check',
                    'description': '查看今日日程',
                    'priority': TaskPriority.HIGH,
                    'urgency': 0.8,
                    'importance': 0.8
                },
                {
                    'type': 'reminder',
                    'description': '提醒重要会议',
                    'priority': TaskPriority.CRITICAL,
                    'urgency': 0.9,
                    'importance': 0.9
                }
            ]
        }
    
    async def plan(
        self,
        scene: SceneContext,
        user_history: List[Dict],
        current_time: datetime
    ) -> List[Task]:
        """
        规划任务
        
        Args:
            scene: 场景上下文
            user_history: 用户历史行为
            current_time: 当前时间
        """
        tasks = []
        
        # 如果有大模型，用它来智能规划任务
        if self.llm_enabled and scene.confidence > 0.5:
            try:
                llm_tasks = await self._llm_plan_tasks(scene, user_history, current_time)
                if llm_tasks:
                    tasks.extend(llm_tasks)
                    print(f"  ✓ 大模型生成了 {len(llm_tasks)} 个任务")
            except Exception as e:
                print(f"  ⚠️ 大模型规划失败，使用规则方法: {e}")
        
        # 基于意图生成任务（规则方法）
        if scene.intent in self.task_templates:
            templates = self.task_templates[scene.intent]
            for i, template in enumerate(templates):
                task = Task(
                    task_id=f"{scene.intent}_{i}_{current_time.timestamp()}",
                    task_type=template['type'],
                    description=template['description'],
                    priority=template['priority'],
                    urgency=template['urgency'],
                    importance=template['importance'],
                    user_preference=self._get_user_preference(
                        template['type'], user_history
                    ),
                    estimated_duration=60
                )
                tasks.append(task)
        
        # 基于场景生成额外任务
        scene_tasks = await self._generate_scene_tasks(scene, current_time)
        tasks.extend(scene_tasks)
        
        # 基于时间生成定时任务
        time_tasks = await self._generate_time_tasks(current_time, user_history)
        tasks.extend(time_tasks)
        
        return tasks
    
    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """任务优先级排序"""
        if not tasks:
            return []
        
        # 规则方法排序
        scored_tasks = [(task.compute_score(), task) for task in tasks]
        sorted_tasks = sorted(scored_tasks, key=lambda x: x[0], reverse=True)
        return [task for _, task in sorted_tasks]
    
    async def _llm_plan_tasks(
        self,
        scene: SceneContext,
        user_history: List[Dict],
        current_time: datetime
    ) -> List[Task]:
        """使用大模型智能规划任务"""
        prompt = f"""
你是一个智能任务规划助手。基于当前场景，规划合适的任务。

场景信息：
- 场景类型: {scene.scene_type}
- 检测到的物体: {', '.join(scene.objects[:5])}
- 识别到的行为: {', '.join(scene.actions)}
- 推断的意图: {scene.intent}
- 当前时间: {current_time.strftime('%Y-%m-%d %H:%M')}
- 置信度: {scene.confidence:.2f}

请生成2-4个任务，以JSON格式返回：
[
    {{
        "type": "reminder/safety_alert/health_reminder/schedule_check",
        "description": "任务描述",
        "priority": "CRITICAL/HIGH/MEDIUM/LOW",
        "urgency": 0.0-1.0,
        "importance": 0.0-1.0,
        "reasoning": "为什么需要这个任务"
    }}
]

要求：
1. 任务要具体、可执行
2. 考虑用户当前状态和需求
3. 优先级要合理
"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "你是智能任务规划专家，擅长根据场景生成合理的任务。"},
                {"role": "user", "content": prompt}
            ], temperature=0.7)
            
            # 解析大模型响应
            import json
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                llm_tasks_data = json.loads(json_match.group())
                tasks = []
                
                for i, task_data in enumerate(llm_tasks_data):
                    # 转换优先级
                    priority_map = {
                        'CRITICAL': TaskPriority.CRITICAL,
                        'HIGH': TaskPriority.HIGH,
                        'MEDIUM': TaskPriority.MEDIUM,
                        'LOW': TaskPriority.LOW
                    }
                    priority = priority_map.get(task_data.get('priority', 'MEDIUM'), TaskPriority.MEDIUM)
                    
                    task = Task(
                        task_id=f"llm_{scene.intent}_{i}_{current_time.timestamp()}",
                        task_type=task_data.get('type', 'reminder'),
                        description=task_data.get('description', ''),
                        priority=priority,
                        urgency=task_data.get('urgency', 0.5),
                        importance=task_data.get('importance', 0.5),
                        user_preference=0.7,  # 大模型生成的任务默认较高偏好
                        estimated_duration=60
                    )
                    tasks.append(task)
                
                return tasks
        except Exception as e:
            print(f"大模型任务规划失败: {e}")
        
        return []
    
    def _get_user_preference(self, task_type: str, user_history: List[Dict]) -> float:
        """获取用户对任务类型的偏好"""
        # 简化实现：基于历史完成率
        completed = sum(1 for h in user_history if h.get('type') == task_type and h.get('completed'))
        total = sum(1 for h in user_history if h.get('type') == task_type)
        return completed / total if total > 0 else 0.5
    
    async def _generate_scene_tasks(self, scene: SceneContext, current_time: datetime) -> List[Task]:
        """基于场景生成任务"""
        tasks = []
        
        # 示例：厨房场景检测到燃气
        if scene.scene_type == '厨房' and '燃气' in scene.objects:
            if '烹饪' not in scene.actions:
                # 可能忘记关燃气
                tasks.append(Task(
                    task_id=f"safety_check_{current_time.timestamp()}",
                    task_type='safety_alert',
                    description='检测到燃气开启但无烹饪行为，请确认安全',
                    priority=TaskPriority.CRITICAL,
                    urgency=1.0,
                    importance=1.0,
                    user_preference=0.9,
                    estimated_duration=10
                ))
        
        return tasks
    
    async def _generate_time_tasks(self, current_time: datetime, user_history: List[Dict]) -> List[Task]:
        """基于时间生成任务"""
        tasks = []
        hour = current_time.hour
        
        # 早晨提醒
        if 7 <= hour < 9:
            tasks.append(Task(
                task_id=f"morning_reminder_{current_time.timestamp()}",
                task_type='reminder',
                description='早安！新的一天开始了',
                priority=TaskPriority.MEDIUM,
                urgency=0.6,
                importance=0.5,
                user_preference=0.7,
                estimated_duration=5
            ))
        
        # 喝水提醒(每2小时)
        if hour % 2 == 0:
            tasks.append(Task(
                task_id=f"water_reminder_{current_time.timestamp()}",
                task_type='health_reminder',
                description='该喝水了，保持水分充足',
                priority=TaskPriority.LOW,
                urgency=0.4,
                importance=0.6,
                user_preference=0.6,
                estimated_duration=5
            ))
        
        return tasks


class ActionExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.execution_history = []
    
    async def execute(self, task: Task) -> bool:
        """
        执行任务
        
        Returns:
            是否执行成功
        """
        try:
            task.status = TaskStatus.RUNNING
            
            # 根据任务类型执行不同操作
            if task.task_type == 'reminder':
                await self._send_notification(task)
            elif task.task_type == 'safety_alert':
                await self._send_alert(task)
            elif task.task_type == 'health_reminder':
                await self._send_health_tip(task)
            elif task.task_type == 'schedule_check':
                await self._check_schedule(task)
            else:
                await self._default_action(task)
            
            task.status = TaskStatus.COMPLETED
            self.execution_history.append({
                'task_id': task.task_id,
                'type': task.task_type,
                'completed': True,
                'timestamp': datetime.now()
            })
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            print(f"Task execution failed: {e}")
            return False
    
    async def _send_notification(self, task: Task):
        """发送通知"""
        print(f"[通知] {task.description}")
        await asyncio.sleep(0.1)  # 模拟异步操作
    
    async def _send_alert(self, task: Task):
        """发送警告"""
        print(f"[警告] {task.description}")
        await asyncio.sleep(0.1)
    
    async def _send_health_tip(self, task: Task):
        """发送健康提示"""
        print(f"[健康] {task.description}")
        await asyncio.sleep(0.1)
    
    async def _check_schedule(self, task: Task):
        """检查日程"""
        print(f"[日程] {task.description}")
        await asyncio.sleep(0.1)
    
    async def _default_action(self, task: Task):
        """默认操作"""
        print(f"[任务] {task.description}")
        await asyncio.sleep(0.1)
    
    def get_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.execution_history


class AgentMemory:
    """Agent记忆系统"""
    
    def __init__(self, max_size: int = 1000):
        self.short_term_memory = []  # 短期记忆
        self.long_term_memory = []  # 长期记忆
        self.max_size = max_size
    
    def store(self, scene: SceneContext, tasks: List[Task]):
        """存储记忆"""
        memory_item = {
            'scene': scene,
            'tasks': tasks,
            'timestamp': datetime.now()
        }
        self.short_term_memory.append(memory_item)
        
        # 短期记忆满了转移到长期记忆
        if len(self.short_term_memory) > 100:
            self._consolidate_memory()
    
    def retrieve(self, scene: SceneContext, top_k: int = 5) -> List[Dict]:
        """检索相关记忆"""
        # 简化实现：返回最近的记忆
        all_memory = self.short_term_memory + self.long_term_memory
        return all_memory[-top_k:]
    
    def _consolidate_memory(self):
        """整合记忆"""
        # 将旧的短期记忆转为长期记忆
        old_memories = self.short_term_memory[:50]
        self.long_term_memory.extend(old_memories)
        self.short_term_memory = self.short_term_memory[50:]
        
        # 限制长期记忆大小
        if len(self.long_term_memory) > self.max_size:
            self.long_term_memory = self.long_term_memory[-self.max_size:]


class AutonomousDecisionEngine:
    """自主决策引擎"""
    
    def __init__(self):
        self.scene_analyzer = SceneAnalyzer()
        self.task_planner = TaskPlanner()
        self.action_executor = ActionExecutor()
        self.memory = AgentMemory()
        
        # 接入大模型用于决策推理
        try:
            from llm.llm_service import get_llm_service
            self.llm = get_llm_service()
            self.llm_enabled = self.llm is not None
            if self.llm_enabled:
                print("✓ 决策引擎已接入大模型")
        except Exception as e:
            self.llm = None
            self.llm_enabled = False
            print(f"⚠️ 决策引擎未接入大模型: {e}")
    
    async def analyze_and_decide(self, multimodal_input: Dict) -> Dict[str, Any]:
        """
        分析场景并做出决策
        
        Args:
            multimodal_input: 多模态输入
                - tags: 层次化标签
                - timestamp: 时间戳
                - location: 位置
        
        Returns:
            决策结果
        """
        # 1. 场景理解
        scene = await self.scene_analyzer.analyze(multimodal_input)
        print(f"\n[场景分析] {scene.scene_type} - {scene.intent}")
        print(f"  物体: {', '.join(scene.objects[:3])}")
        print(f"  行为: {', '.join(scene.actions)}")
        print(f"  置信度: {scene.confidence:.2f}")
        
        # 2. 检索相关记忆
        relevant_memory = self.memory.retrieve(scene)
        
        # 3. 任务规划
        tasks = await self.task_planner.plan(
            scene=scene,
            user_history=self.action_executor.get_history(),
            current_time=datetime.now()
        )
        print(f"\n[任务规划] 生成 {len(tasks)} 个任务")
        
        # 4. 优先级排序
        prioritized_tasks = self.task_planner.prioritize_tasks(tasks)
        
        # 5. 大模型决策推理（如果启用）
        decision_reasoning = None
        if self.llm_enabled and len(prioritized_tasks) > 0:
            decision_reasoning = await self._llm_decision_reasoning(
                scene, prioritized_tasks[:3], relevant_memory
            )
        
        # 6. 执行决策
        print(f"\n[任务执行]")
        executed_tasks = []
        for task in prioritized_tasks[:3]:  # 执行前3个高优先级任务
            success = await self.action_executor.execute(task)
            if success:
                executed_tasks.append(task)
        
        # 7. 存储记忆
        self.memory.store(scene, executed_tasks)
        
        return {
            'scene': {
                'type': scene.scene_type,
                'objects': scene.objects,
                'actions': scene.actions,
                'intent': scene.intent,
                'confidence': scene.confidence
            },
            'tasks': [
                {
                    'id': t.task_id,
                    'type': t.task_type,
                    'description': t.description,
                    'priority': t.priority.name,
                    'score': t.compute_score(),
                    'status': t.status.value
                }
                for t in executed_tasks
            ],
            'decision_reasoning': decision_reasoning,
            'actions_taken': len(executed_tasks)
        }
    
    async def _llm_decision_reasoning(
        self,
        scene: SceneContext,
        top_tasks: List[Task],
        memory: List[Dict]
    ) -> str:
        """使用大模型进行决策推理"""
        try:
            tasks_desc = "\n".join([
                f"{i+1}. [{t.priority.name}] {t.description} (紧急度:{t.urgency:.2f}, 重要性:{t.importance:.2f})"
                for i, t in enumerate(top_tasks)
            ])
            
            prompt = f"""
你是一个智能决策助手。请分析当前情况并解释决策理由。

场景信息：
- 场景: {scene.scene_type}
- 意图: {scene.intent}
- 物体: {', '.join(scene.objects[:5])}
- 行为: {', '.join(scene.actions)}

计划执行的任务：
{tasks_desc}

请提供：
1. 对当前情况的分析（2-3句话）
2. 为什么选择这些任务（简要说明）
3. 执行建议（1-2条）

要求简洁、实用。
"""
            
            response = self.llm.chat([
                {"role": "system", "content": "你是智能决策助手，擅长分析情况并给出合理建议。"},
                {"role": "user", "content": prompt}
            ], temperature=0.7)
            
            return response
        except Exception as e:
            print(f"大模型决策推理失败: {e}")
            return None
    
    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """任务优先级排序"""
        # 如果有大模型且任务较多，用它来智能排序
        if self.llm_enabled and len(tasks) > 3:
            try:
                llm_sorted = self._llm_prioritize_tasks(tasks)
                if llm_sorted:
                    return llm_sorted
            except Exception as e:
                print(f"大模型排序失败，使用规则方法: {e}")
        
        # 规则方法排序
        scored_tasks = [(task.compute_score(), task) for task in tasks]
        sorted_tasks = sorted(scored_tasks, key=lambda x: x[0], reverse=True)
        return [task for _, task in sorted_tasks]
    
    def _llm_prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """使用大模型智能排序任务"""
        tasks_info = []
        for i, task in enumerate(tasks):
            tasks_info.append({
                'index': i,
                'type': task.task_type,
                'description': task.description,
                'priority': task.priority.name,
                'urgency': task.urgency,
                'importance': task.importance,
                'score': task.compute_score()
            })
        
        prompt = f"""
你是任务优先级专家。请根据以下任务信息，给出最优的执行顺序。

任务列表：
{json.dumps(tasks_info, ensure_ascii=False, indent=2)}

请考虑：
1. 紧急程度（urgency）
2. 重要性（importance）
3. 任务类型（安全类优先）
4. 任务之间的依赖关系

返回任务索引的排序列表（JSON数组），例如：[2, 0, 1, 3]
只返回数组，不要其他内容。
"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "你是任务优先级专家。"},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # 解析排序结果
            import json
            import re
            json_match = re.search(r'\[[\d,\s]+\]', response)
            if json_match:
                order = json.loads(json_match.group())
                sorted_tasks = [tasks[i] for i in order if i < len(tasks)]
                return sorted_tasks
        except Exception as e:
            print(f"大模型排序解析失败: {e}")
        
        return None
