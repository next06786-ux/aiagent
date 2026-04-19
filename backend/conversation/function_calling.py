"""
Function Calling 系统
让 AI 能够调用系统功能
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import asyncio


@dataclass
class FunctionDefinition:
    """函数定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class FunctionRegistry:
    """函数注册表"""
    
    def __init__(self):
        self.functions: Dict[str, FunctionDefinition] = {}
    
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """注册函数"""
        self.functions[name] = FunctionDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        print(f"[Function Calling] 注册函数: {name}")
    
    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """获取所有函数的 schema（用于 LLM）"""
        schemas = []
        for func in self.functions.values():
            schemas.append({
                "name": func.name,
                "description": func.description,
                "parameters": func.parameters
            })
        return schemas
    
    async def call_function(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用函数"""
        if name not in self.functions:
            return {
                "success": False,
                "error": f"函数 {name} 不存在"
            }
        
        func = self.functions[name]
        
        try:
            print(f"[Function Calling] 调用函数: {name}")
            print(f"[Function Calling] 参数: {arguments}")
            
            # 调用处理函数
            if asyncio.iscoroutinefunction(func.handler):
                result = await func.handler(**arguments)
            else:
                result = func.handler(**arguments)
            
            print(f"[Function Calling] 函数 {name} 执行成功")
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[Function Calling] 函数 {name} 执行失败: {error_msg}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局函数注册表
function_registry = FunctionRegistry()


# ==================== 注册系统函数 ====================

def register_schedule_functions():
    """注册日程相关函数"""
    
    async def generate_schedule(user_id: str, date: Optional[str] = None, tasks: Optional[List[Dict]] = None):
        """生成日程"""
        from backend.schedule.schedule_task_manager import task_manager, TaskType
        from datetime import datetime
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 如果没有提供任务，使用默认任务
        if not tasks:
            tasks = [
                {
                    "task_id": f"task_{datetime.now().timestamp()}",
                    "title": "工作任务",
                    "task_type": "work",
                    "duration_minutes": 120,
                    "priority": "high",
                    "flexibility": 0.3,
                    "energy_required": 0.7,
                    "focus_required": 0.8
                },
                {
                    "task_id": f"task_{datetime.now().timestamp() + 1}",
                    "title": "学习时间",
                    "task_type": "study",
                    "duration_minutes": 90,
                    "priority": "medium",
                    "flexibility": 0.5,
                    "energy_required": 0.6,
                    "focus_required": 0.7
                }
            ]
        
        # 创建任务
        task_id = task_manager.create_task(
            user_id=user_id,
            task_type=TaskType.SCHEDULE_GENERATION,
            params={
                "tasks": tasks,
                "date": date
            }
        )
        
        # 在后台执行
        async def execute():
            await task_manager.execute_schedule_generation(
                task_id,
                user_id,
                {"tasks": tasks, "date": date}
            )
        
        # 启动后台任务
        asyncio.create_task(execute())
        
        return {
            "task_id": task_id,
            "date": date,
            "message": f"正在为你生成 {date} 的日程安排，请稍候在智能日程页面查看..."
        }
    
    function_registry.register(
        name="generate_schedule",
        description="为用户生成智能日程安排。当用户要求安排日程、规划时间、生成日程时调用此函数。",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "date": {
                    "type": "string",
                    "description": "日期，格式 YYYY-MM-DD，如果用户说今天则使用当天日期"
                },
                "tasks": {
                    "type": "array",
                    "description": "任务列表（可选），如果用户没有明确说明任务，可以不提供",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "任务标题"},
                            "task_type": {"type": "string", "enum": ["work", "study", "exercise", "social", "rest"]},
                            "duration_minutes": {"type": "integer", "description": "预计时长（分钟）"},
                            "priority": {"type": "string", "enum": ["high", "medium", "low"]}
                        }
                    }
                }
            },
            "required": ["user_id"]
        },
        handler=generate_schedule
    )
    
    async def query_schedule(user_id: str, query: str):
        """查询日程"""
        from backend.schedule.schedule_rag_integration import ScheduleRAGIntegration
        
        rag = ScheduleRAGIntegration(user_id)
        schedules = rag.query_schedule_history(query, limit=5)
        
        return {
            "schedules": schedules,
            "count": len(schedules)
        }
    
    function_registry.register(
        name="query_schedule",
        description="查询用户的历史日程记录。当用户询问过去的日程、查看历史安排时调用。",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "query": {
                    "type": "string",
                    "description": "查询内容，如'上周的日程'、'最近的工作安排'"
                }
            },
            "required": ["user_id", "query"]
        },
        handler=query_schedule
    )


def register_knowledge_graph_functions():
    """注册知识图谱相关函数"""
    
    def query_relationships(user_id: str, person_name: Optional[str] = None):
        """查询人际关系"""
        from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
        
        kg = InformationKnowledgeGraph(user_id)
        
        if person_name:
            # 查询特定人的关系
            relationships = kg.get_person_relationships(user_id, person_name)
        else:
            # 查询所有关系
            relationships = kg.get_relationships(user_id, limit=20)
        
        kg.close()
        
        return {
            "relationships": [
                {
                    "person": r.get("person_name", ""),
                    "type": r.get("relationship_type", ""),
                    "description": r.get("description", "")
                }
                for r in relationships
            ]
        }
    
    function_registry.register(
        name="query_relationships",
        description="查询用户的人际关系网络。当用户询问关于人际关系、朋友、家人时调用。",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "person_name": {
                    "type": "string",
                    "description": "特定人名（可选）"
                }
            },
            "required": ["user_id"]
        },
        handler=query_relationships
    )


# 初始化时注册所有函数
def initialize_functions():
    """初始化所有函数"""
    register_schedule_functions()
    register_knowledge_graph_functions()
    print(f"[Function Calling] 已注册 {len(function_registry.functions)} 个函数")


# 自动初始化
initialize_functions()
