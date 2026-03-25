"""
智能体工具集
将现有系统能力封装为可调用的工具
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.agent.react_agent import Tool, ToolRegistry


def create_tool_registry(
    user_id: str,
    rag_system=None,
    knowledge_graph=None,
    db_manager=None,
    llm_service=None
) -> ToolRegistry:
    """
    创建工具注册表
    将现有系统能力封装为工具
    """
    registry = ToolRegistry()
    
    # ==================== 记忆工具 ====================
    
    def search_memory(query: str, memory_type: str = "all", limit: int = 5) -> str:
        """搜索用户记忆"""
        if not rag_system:
            return "记忆系统未初始化"
        
        try:
            from backend.learning.production_rag_system import MemoryType
            
            type_map = {
                "all": None,
                "conversation": [MemoryType.CONVERSATION],
                "knowledge": [MemoryType.KNOWLEDGE],
                "experience": [MemoryType.EXPERIENCE],
                "decision": [MemoryType.DECISION]
            }
            
            memories = rag_system.search(
                query=query,
                memory_types=type_map.get(memory_type),
                top_k=limit
            )
            
            if not memories:
                return "未找到相关记忆"
            
            results = []
            for mem in memories:
                results.append({
                    "type": mem.memory_type.value,
                    "content": mem.content[:200],
                    "importance": mem.importance,
                    "time": mem.timestamp.strftime("%Y-%m-%d %H:%M")
                })
            
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"搜索失败: {str(e)}"
    
    registry.register(Tool(
        name="search_memory",
        description="搜索用户的历史记忆，包括对话、知识、经验等",
        parameters={
            "query": "搜索关键词",
            "memory_type": "记忆类型: all/conversation/knowledge/experience/decision",
            "limit": "返回数量，默认5"
        },
        func=search_memory
    ))
    
    # ==================== 知识图谱工具 ====================
    
    def query_knowledge_graph(query: str, max_depth: int = 2) -> str:
        """查询知识图谱"""
        if not knowledge_graph:
            return "知识图谱未初始化"
        
        try:
            # 搜索相关信息
            results = knowledge_graph.search_information(
                keyword=query,
                limit=10
            )
            
            if not results:
                return "知识图谱中未找到相关信息"
            
            # 获取关联信息
            output = []
            for info in results[:5]:
                related = knowledge_graph.get_related_information(
                    info_name=info.get("name", ""),
                    max_depth=max_depth
                )
                output.append({
                    "name": info.get("name"),
                    "type": info.get("type"),
                    "category": info.get("category"),
                    "confidence": info.get("confidence"),
                    "related_count": len(related)
                })
            
            return json.dumps(output, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"查询失败: {str(e)}"
    
    registry.register(Tool(
        name="query_knowledge_graph",
        description="查询用户的个人知识图谱，获取实体、概念及其关系",
        parameters={
            "query": "查询关键词",
            "max_depth": "关系深度，默认2"
        },
        func=query_knowledge_graph
    ))
    
    # ==================== 健康数据工具 ====================
    
    def get_health_data(days: int = 7) -> str:
        """获取健康数据"""
        if not db_manager:
            return "数据库未初始化"
        
        try:
            records = db_manager.get_health_records(user_id, limit=days)
            
            if not records:
                return "暂无健康数据"
            
            data = []
            for r in records:
                data.append({
                    "date": r.timestamp.strftime("%Y-%m-%d") if hasattr(r, 'timestamp') else "未知",
                    "sleep_hours": getattr(r, 'sleep_hours', 0),
                    "exercise_minutes": getattr(r, 'exercise_minutes', 0),
                    "stress_level": getattr(r, 'stress_level', 0),
                    "health_score": getattr(r, 'health_score', 0)
                })
            
            # 计算统计
            if data:
                avg_sleep = sum(d['sleep_hours'] for d in data) / len(data)
                avg_exercise = sum(d['exercise_minutes'] for d in data) / len(data)
                avg_stress = sum(d['stress_level'] for d in data) / len(data)
                
                return json.dumps({
                    "records": data,
                    "summary": {
                        "avg_sleep_hours": round(avg_sleep, 1),
                        "avg_exercise_minutes": round(avg_exercise, 1),
                        "avg_stress_level": round(avg_stress, 1),
                        "days_analyzed": len(data)
                    }
                }, ensure_ascii=False, indent=2)
            
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"获取失败: {str(e)}"
    
    registry.register(Tool(
        name="get_health_data",
        description="获取用户最近的健康数据，包括睡眠、运动、压力等",
        parameters={
            "days": "获取最近几天的数据，默认7天"
        },
        func=get_health_data
    ))
    
    # ==================== 分析工具 ====================
    
    def analyze_health_trend(aspect: str = "all") -> str:
        """分析健康趋势"""
        if not db_manager:
            return "数据库未初始化"
        
        try:
            records = db_manager.get_health_records(user_id, limit=30)
            
            if len(records) < 3:
                return "数据不足，无法分析趋势"
            
            # 简单趋势分析
            recent = records[:7]
            older = records[7:14] if len(records) > 7 else records[7:]
            
            def avg(items, attr):
                vals = [getattr(r, attr, 0) for r in items]
                return sum(vals) / len(vals) if vals else 0
            
            trends = {}
            
            if aspect in ["all", "sleep"]:
                recent_sleep = avg(recent, 'sleep_hours')
                older_sleep = avg(older, 'sleep_hours') if older else recent_sleep
                trends["sleep"] = {
                    "current": round(recent_sleep, 1),
                    "previous": round(older_sleep, 1),
                    "trend": "improving" if recent_sleep > older_sleep else "declining" if recent_sleep < older_sleep else "stable"
                }
            
            if aspect in ["all", "exercise"]:
                recent_ex = avg(recent, 'exercise_minutes')
                older_ex = avg(older, 'exercise_minutes') if older else recent_ex
                trends["exercise"] = {
                    "current": round(recent_ex, 1),
                    "previous": round(older_ex, 1),
                    "trend": "improving" if recent_ex > older_ex else "declining" if recent_ex < older_ex else "stable"
                }
            
            if aspect in ["all", "stress"]:
                recent_stress = avg(recent, 'stress_level')
                older_stress = avg(older, 'stress_level') if older else recent_stress
                trends["stress"] = {
                    "current": round(recent_stress, 1),
                    "previous": round(older_stress, 1),
                    "trend": "improving" if recent_stress < older_stress else "worsening" if recent_stress > older_stress else "stable"
                }
            
            return json.dumps(trends, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"分析失败: {str(e)}"
    
    registry.register(Tool(
        name="analyze_health_trend",
        description="分析用户健康数据的趋势变化",
        parameters={
            "aspect": "分析方面: all/sleep/exercise/stress"
        },
        func=analyze_health_trend
    ))
    
    # ==================== 决策工具 ====================
    
    def simulate_decision(question: str, options: List[str]) -> str:
        return "该功能已下线，请使用决策副本入口进行决策推演。"
    
    registry.register(Tool(
        name="simulate_decision",
        description="模拟不同决策选项的可能结果，帮助用户做出选择",
        parameters={
            "question": "决策问题",
            "options": "选项列表，如 ['选项A', '选项B']"
        },
        func=simulate_decision
    ))
    
    # ==================== 日程工具 ====================
    
    def get_current_time() -> str:
        """获取当前时间"""
        now = datetime.now()
        return json.dumps({
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
            "hour": now.hour
        }, ensure_ascii=False)
    
    registry.register(Tool(
        name="get_current_time",
        description="获取当前日期和时间",
        parameters={},
        func=get_current_time
    ))
    
    # ==================== 计算工具 ====================
    
    def calculate(expression: str) -> str:
        """安全计算数学表达式"""
        try:
            # 只允许基本数学运算
            allowed = set('0123456789+-*/.() ')
            if not all(c in allowed for c in expression):
                return "不支持的表达式"
            
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    registry.register(Tool(
        name="calculate",
        description="计算数学表达式",
        parameters={
            "expression": "数学表达式，如 '(100 + 50) * 2'"
        },
        func=calculate
    ))
    
    # ==================== 建议生成工具 ====================
    
    def generate_advice(topic: str, context: str = "") -> str:
        """生成个性化建议"""
        if not llm_service:
            return "LLM 服务未初始化"
        
        try:
            prompt = f"""基于以下信息，为用户生成3条具体、可执行的建议：

主题: {topic}
上下文: {context}

要求：
1. 建议要具体、可操作
2. 考虑用户的实际情况
3. 每条建议不超过50字

请以JSON数组格式返回，如：
["建议1", "建议2", "建议3"]
"""
            
            response = llm_service.chat([
                {"role": "system", "content": "你是健康生活顾问，擅长给出实用建议。"},
                {"role": "user", "content": prompt}
            ], temperature=0.7)
            
            return response
        except Exception as e:
            return f"生成失败: {str(e)}"
    
    registry.register(Tool(
        name="generate_advice",
        description="基于特定主题生成个性化建议",
        parameters={
            "topic": "建议主题，如'改善睡眠'、'减压方法'",
            "context": "额外上下文信息"
        },
        func=generate_advice
    ))
    
    return registry


# ==================== 工具工厂 ====================

class ToolFactory:
    """工具工厂 - 便捷创建工具集"""
    
    @staticmethod
    def create_for_user(
        user_id: str,
        include_memory: bool = True,
        include_kg: bool = True,
        include_health: bool = True,
        include_decision: bool = True
    ) -> ToolRegistry:
        """为用户创建工具集"""
        from backend.startup_manager import (
            get_rag_system,
            get_info_kg,
            get_llm_service
        )
        from backend.database.db_manager import db_manager
        
        return create_tool_registry(
            user_id=user_id,
            rag_system=get_rag_system(user_id) if include_memory else None,
            knowledge_graph=get_info_kg(user_id) if include_kg else None,
            db_manager=db_manager if include_health else None,
            llm_service=get_llm_service()
        )
