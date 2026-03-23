"""
LifeSwarm 后端服务 - FastAPI 应用主入口
"""
import os
import sys
import time
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

# 加载环境变量
load_dotenv()

# 设置 HuggingFace 离线模式(避免网络问题)
os.environ['HF_HUB_OFFLINE'] = '1'

# 创建FastAPI应用
app = FastAPI(
    title="LifeSwarm API",
    description="智能生活助手系统 - 多模态数据采集,AI分析,知识图谱",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 初始化系统====================

print("\n" + "="*60)
print("  LifeSwarm 后端服务启动")
print("="*60 + "\n")

# 延迟初始化所有系统(避免启动阻塞个llm_service = None
hybrid_systems = {}
fusion_system = None
rag_systems = {}
learners = {}
knowledge_graphs = {}
perception_layer = None
emergence_detector = None
report_generator = None
analysis_engine = None
enhanced_kg_systems = {}
optimized_learners = {}
optimized_detectors = {}
feedback_processors = {}

# 初始化数据库管理器(轻量级)
from backend.database.db_manager import db_manager

# 全局信息知识图谱系统字典
info_kg_systems = {}

def get_or_init_llm_service():
    """获取 LLM 服务"""
    from backend.startup_manager import get_llm_service
    return get_llm_service()

def get_or_init_fusion_system():
    """获取多模态融合系统"""
    from backend.startup_manager import get_fusion_system
    return get_fusion_system()

# 导入必要的类型(但不初始化)
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
from backend.learning.reinforcement_learner import ReinforcementLearner
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
from backend.learning.optimized_reinforcement_learner import OptimizedReinforcementLearner, LearningStrategy
from backend.prediction.optimized_emergence_detector import OptimizedEmergenceDetector
from backend.feedback.user_feedback_system import FeedbackProcessor, FeedbackType

def get_or_init_perception_layer():
    """获取感知层"""
    from backend.startup_manager import get_perception_layer
    return get_perception_layer()

def get_or_init_emergence_detector():
    """获取涌现检测系统"""
    from backend.startup_manager import get_emergence_detector
    return get_emergence_detector()

def get_or_init_report_generator():
    """获取报告生成器"""
    from backend.startup_manager import StartupManager
    return StartupManager.get_system('report_generator')

def get_or_init_analysis_engine():
    """获取分析引擎"""
    from backend.startup_manager import StartupManager
    return StartupManager.get_system('analysis_engine')

print("后端服务已启动(系统将按需加载)\n")


# ==================== 系统启动管理 ====================

from backend.startup_manager import StartupManager

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化所有系统"""
    await StartupManager.startup()
    
    # 启动 LoRA 训练调度器
    try:
        from backend.lora.lora_scheduler import get_scheduler
        scheduler = get_scheduler()
        # 启动调度器
        scheduler.start()
    except Exception as e:
        print(f"⚠️  LoRA 调度器启动失败: {e}")
    
    # 预初始化default_user的知识图谱，避免前端首次访问延迟
    try:
        from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
        global info_kg_systems
        print("🔧 预初始化 default_user 知识图谱...")
        info_kg_systems["default_user"] = InformationKnowledgeGraph("default_user")
        print("✅ default_user 知识图谱预加载完成")
    except Exception as e:
        print(f"⚠️ 知识图谱预初始化失败: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    try:
        from backend.lora.lora_scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.stop()
    except Exception as e:
        print(f"⚠️  LoRA 调度器停止失败: {e}")


# ==================== 工具函数 ====================

def get_or_create_user_system(user_id: str):
    """获取或创建用户的系统实例"""
    from backend.startup_manager import StartupManager
    
    # 所有用户都共享已初始化的默认系统
    # 这样避免了每个新用户都要重新初始化
    default_user_id = "default_user"
    
    return {
        'hybrid': None,  # 按需初始化
        'rag': StartupManager.get_user_system(default_user_id, 'rag'),
        'learner': StartupManager.get_user_system(default_user_id, 'learner'),
        'kg': StartupManager.get_user_system(default_user_id, 'kg'),
        'info_kg': StartupManager.get_user_system(default_user_id, 'info_kg')
    }


# ==================== 健康检查====================

@app.get("/health")
async def health_check():
    """健康检查"""
    from backend.startup_manager import get_init_status
    
    status = get_init_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": "✓ 就绪" if status['llm_service'] else "⚠️ 未就绪",
            "knowledge_graph": "✓ 就绪" if status['knowledge_graph'] else "⚠️ 未就绪",
            "rag": "✓ 就绪" if status['rag_system'] else "⚠️ 未就绪",
            "emergence_detector": "✓ 就绪" if status['emergence_detector'] else "⚠️ 未就绪",
            "database": "✓ 就绪"
        }
    }


# ==================== 数据采集API ====================

@app.post("/api/v4/multimodal/data")
async def upload_multimodal_data(request_data: Dict[str, Any]):
    """
    上传多模态数据
    
    请求体:
    {
        "user_id": "user_001",
        "timestamp": 1234567890,
        "sensor": {...},
        "health": {...},
        "context": {...},
        "image": {...},
        "text": "用户输入",
        "metadata": {...}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        timestamp = request_data.get("timestamp", int(datetime.now().timestamp() * 1000))
        
        # 获取用户系统
        systems = get_or_create_user_system(user_id)
        
        # 【新增】使用数据流协调器处理数据(自动构建知识图谱)
        try:
            from data_flow_orchestrator import DataFlowOrchestrator, PerceptionData
            
            # 创建数据流协调器
            orchestrator = DataFlowOrchestrator(
                perception_layer=get_or_init_perception_layer(),
                meta_agent=None,  # 简化版,不需要元智能体
                knowledge_graph=systems.get('kg'),
                reinforcement_learner=systems.get('learner'),
                multimodal_fusion=get_or_init_fusion_system(),
                rag_system=systems.get('rag'),
                info_kg_system=systems.get('info_kg')  # 信息知识图谱
            )
            
            # 构造感知数据
            perception_data = PerceptionData(
                user_id=user_id,
                text=request_data.get("text"),
                image=request_data.get("image"),
                sensors=request_data.get("sensor"),
                timestamp=datetime.fromtimestamp(timestamp / 1000)
            )
            
            # 处理数据(会自动提取信息并构建知识图谱)
            print(f"\n🔄 [自动化] 开始处理用个{user_id} 的数。.")
            orchestrator_result = orchestrator.process_perception_data_sync(perception_data)
            print(f"[自动化] 数据处理完成\n")
            
        except Exception as e:
            print(f"⚠️ 数据流协调器处理失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 1. 多模态融合(保留原有逻辑        modalities = []
        
        if "sensor" in request_data and request_data["sensor"]:
            modalities.append({
                "type": "sensor",
                "data": request_data["sensor"],
                "confidence": 0.9
            })
        
        if "health" in request_data and request_data["health"]:
            modalities.append({
                "type": "sensor",
                "data": request_data["health"],
                "confidence": 0.85
            })
        
        if "context" in request_data and request_data["context"]:
            modalities.append({
                "type": "sensor",
                "data": request_data["context"],
                "confidence": 0.8
            })
        
        if "text" in request_data and request_data["text"]:
            modalities.append({
                "type": "text",
                "data": request_data["text"],
                "confidence": 0.95
            })
        
        # 融合多模态数据
        fused_result = get_or_init_fusion_system().fuse_modalities(modalities)
        
        # 2. 感知层处理
        perception_result = get_or_init_perception_layer().perceive(
            user_id=user_id,
            data=request_data
        )
        
        # 3. 保存到数据库
        try:
            db_manager.save_health_record(
                user_id=user_id,
                data={
                    "sleep_hours": request_data.get("health", {}).get("sleepHours", 0),
                    "sleep_quality": request_data.get("health", {}).get("sleepQuality", 0),
                    "steps": request_data.get("sensor", {}).get("steps", 0),
                    "heart_rate": request_data.get("sensor", {}).get("heartRate", 0),
                    "exercise_minutes": request_data.get("health", {}).get("exerciseMinutes", 0),
                    "stress_level": request_data.get("health", {}).get("stressLevel", 0),
                    "health_score": 75.0
                }
            )
        except Exception as e:
            print(f"⚠️ 数据库保存失 {e}")
        
        # 4. 添加到RAG记忆
        try:
            # 【改进】根据数据类型分别存            
            # 如果有图片,存储图片记忆
            if "image" in request_data and request_data["image"]:
                image_description = perception_result.get("image_analysis", {}).get("description", "用户上传了一张图")
                
                systems['rag'].add_memory(
                    memory_type=MemoryType.PHOTO,
                    content=f"图片记忆: {image_description}",
                    metadata={
                        "timestamp": timestamp,
                        "image_data": request_data["image"][:100] if isinstance(request_data["image"], str) else "binary",
                        "scene": perception_result.get("image_analysis", {}).get("scene", {}),
                        "objects": perception_result.get("image_analysis", {}).get("objects", [])
                    },
                    importance=0.8
                )
                print(f"[自动记忆] 图片已存入RAG: {image_description[:50]}...")
            
            # 如果有文本,存储对话记忆
            if "text" in request_data and request_data["text"]:
                systems['rag'].add_memory(
                    memory_type=MemoryType.CONVERSATION,
                    content=f"用户输入: {request_data['text']}",
                    metadata={
                        "timestamp": timestamp,
                        "context": request_data.get("context", {})
                    },
                    importance=0.7
                )
                print(f"[自动记忆] 文本已存入RAG: {request_data['text'][:50]}...")
            
            # 存储传感器数            if "sensor" in request_data and request_data["sensor"]:
                sensor_summary = f"传感器数 步数{request_data['sensor'].get('steps', 0)}, 心率{request_data['sensor'].get('heartRate', 0)}"
                
                systems['rag'].add_memory(
                    memory_type=MemoryType.SENSOR_DATA,
                    content=sensor_summary,
                    metadata={
                        "timestamp": timestamp,
                        "sensor_data": request_data["sensor"]
                    },
                    importance=0.5
                )
                print(f"[自动记忆] 传感器数据已存入RAG")
                
        except Exception as e:
            print(f"⚠️ RAG保存失败: {e}")
        
        return {
            "code": 200,
            "message": "Data received successfully",
            "data": {
                "recordId": f"rec_{timestamp}",
                "timestamp": timestamp,
                "modalities_processed": [m["type"] for m in modalities],
                "fusion_confidence": fused_result.get("confidence", 0),
                "perception_quality": perception_result.get("perception_quality", 0)
            }
        }
    
    except Exception as e:
        print(f"数据上传失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 分析API ====================

@app.get("/api/v4/analysis/{user_id}")
async def get_analysis(user_id: str):
    """获取用户分析结果"""
    try:
        systems = get_or_create_user_system(user_id)
        
        # 获取最近的健康记录
        health_records = db_manager.get_health_records(user_id, limit=7)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 计算统计
        avg_sleep = sum(r.sleep_hours for r in health_records) / len(health_records) if health_records else 0
        avg_exercise = sum(r.exercise_minutes for r in health_records) / len(health_records) if health_records else 0
        avg_stress = sum(r.stress_level for r in health_records) / len(health_records) if health_records else 0
        
        return {
            "code": 200,
            "message": "Analysis retrieved successfully",
            "data": {
                "user_id": user_id,
                "period": "7_days",
                "health_metrics": {
                    "average_sleep": round(avg_sleep, 1),
                    "average_exercise": round(avg_exercise, 1),
                    "average_stress": round(avg_stress, 1),
                    "health_score": 75.0
                },
                "trends": {
                    "sleep_trend": "stable",
                    "exercise_trend": "improving",
                    "stress_trend": "stable"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"分析失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 6大领域综合分析API ====================

@app.get("/api/v4/life-analysis/{user_id}")
async def get_life_analysis(user_id: str):
    """
    获取综合生活分析
    
    分析6大领域:健康,时间,情绪,社交,财务,学习
    返回综合生活质量分数和关键洞察
    """
    try:
        # 获取用户的历史数据
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "health_score": getattr(record, 'health_score', 75),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000),
                "mood": getattr(record, 'mood', 7),
                "work_hours": getattr(record, 'work_hours', 8),
                "focus_time": getattr(record, 'focus_time', 6),
                "task_completion_rate": getattr(record, 'task_completion_rate', 0.7),
                "interruptions": getattr(record, 'interruptions', 3),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_hours": getattr(record, 'social_hours', 2),
                "social_interactions": getattr(record, 'social_interactions', 5),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "income": getattr(record, 'income', 0),
                "spending": getattr(record, 'spending', 0),
                "savings": getattr(record, 'savings', 0),
                "debt": getattr(record, 'debt', 0),
                "learning_hours": getattr(record, 'learning_hours', 1),
                "learning_quality": getattr(record, 'learning_quality', 7),
                "test_score": getattr(record, 'test_score', 75),
                "goal_progress": getattr(record, 'goal_progress', 0.5)
            })
        
        # 获取当前用户数据
        user_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 进行综合分析
        analysis = analysis_engine.analyze(user_id, user_data, history)
        
        # 获取领域总结
        domain_summary = analysis_engine.get_domain_summary(analysis)
        
        return {
            "code": 200,
            "message": "Life analysis completed",
            "data": {
                "user_id": user_id,
                "timestamp": analysis.timestamp,
                "overall_score": analysis.overall_score,
                "domains": domain_summary,
                "key_insights": analysis.key_insights,
                "priority_actions": analysis.priority_actions,
                "detailed_analysis": {
                    "health": analysis.health,
                    "time": analysis.time,
                    "emotion": analysis.emotion,
                    "social": analysis.social,
                    "finance": analysis.finance,
                    "learning": analysis.learning
                }
            }
        }
    
    except Exception as e:
        print(f"综合分析失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v4/domain-analysis/{user_id}/{domain}")
async def get_domain_analysis(user_id: str, domain: str):
    """
    获取特定领域的详细分析
    
    domain: health, time, emotion, social, finance, learning
    """
    try:
        # 获取用户的历史数据
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "health_score": getattr(record, 'health_score', 75),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000),
                "mood": getattr(record, 'mood', 7),
                "work_hours": getattr(record, 'work_hours', 8),
                "focus_time": getattr(record, 'focus_time', 6),
                "task_completion_rate": getattr(record, 'task_completion_rate', 0.7),
                "interruptions": getattr(record, 'interruptions', 3),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_hours": getattr(record, 'social_hours', 2),
                "social_interactions": getattr(record, 'social_interactions', 5),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "income": getattr(record, 'income', 0),
                "spending": getattr(record, 'spending', 0),
                "savings": getattr(record, 'savings', 0),
                "debt": getattr(record, 'debt', 0),
                "learning_hours": getattr(record, 'learning_hours', 1),
                "learning_quality": getattr(record, 'learning_quality', 7),
                "test_score": getattr(record, 'test_score', 75),
                "goal_progress": getattr(record, 'goal_progress', 0.5)
            })
        
        # 获取当前用户数据
        user_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 进行综合分析
        analysis = analysis_engine.analyze(user_id, user_data, history)
        
        # 返回特定领域的分析
        domain_map = {
            "health": analysis.health,
            "time": analysis.time,
            "emotion": analysis.emotion,
            "social": analysis.social,
            "finance": analysis.finance,
            "learning": analysis.learning
        }
        
        if domain not in domain_map:
            return {
                "code": 400,
                "message": f"Invalid domain: {domain}. Valid domains: health, time, emotion, social, finance, learning",
                "data": None
            }
        
        return {
            "code": 200,
            "message": f"{domain} analysis completed",
            "data": {
                "user_id": user_id,
                "domain": domain,
                "timestamp": analysis.timestamp,
                "analysis": domain_map[domain]
            }
        }
    
    except Exception as e:
        print(f"领域分析失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 用户认证API ====================

@app.post("/api/auth/register")
async def register(request_data: Dict[str, Any]):
    """
    用户注册
    
    请求个
    {
        "username": "user001",
        "email": "user@example.com",
        "password": "password123",
        "nickname": "昵称"
    }
    
    返回:
    {
        "code": 200,
        "message": "注册成功",
        "data": {
            "user_id": "xxx",
            "username": "user001",
            "email": "user@example.com",
            "nickname": "昵称",
            "token": "xxx"
        }
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        username = request_data.get("username", "").strip()
        email = request_data.get("email", "").strip()
        password = request_data.get("password", "")
        nickname = request_data.get("nickname", "").strip()
        
        # 验证必填字段
        if not username or not email or not password:
            return {
                "code": 400,
                "message": "用户名,邮箱和密码不能为空",
                "data": None
            }
        
        # 验证用户名格式(3-20个字符,字母数字下划线)
        import re
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return {
                "code": 400,
                "message": "用户名格式不正确个-20个字符,仅支持字母,数字,下划线",
                "data": None
            }
        
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {
                "code": 400,
                "message": "邮箱格式不正",
                "data": None
            }
        
        # 验证密码长度
        if len(password) < 6:
            return {
                "code": 400,
                "message": "密码长度不能少于6",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.register(username, email, password, nickname)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": result['data']
            }
        else:
            return {
                "code": 400,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"注册失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"注册失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/login")
async def login(request_data: Dict[str, Any]):
    """
    用户登录
    
    请求个
    {
        "username": "user001",  // 或邮        "password": "password123"
    }
    
    返回:
    {
        "code": 200,
        "message": "登录成功",
        "data": {
            "user_id": "xxx",
            "username": "user001",
            "email": "user@example.com",
            "nickname": "昵称",
            "avatar_url": "...",
            "token": "xxx"
        }
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        username_or_email = request_data.get("username", "").strip()
        password = request_data.get("password", "")
        
        if not username_or_email or not password:
            return {
                "code": 400,
                "message": "用户名和密码不能为空",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.login(username_or_email, password)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": result['data']
            }
        else:
            return {
                "code": 401,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"登录失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"登录失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/logout")
async def logout(request_data: Dict[str, Any]):
    """
    用户登出
    
    请求个
    {
        "token": "xxx"
    }
    
    返回:
    {
        "code": 200,
        "message": "登出成功",
        "data": null
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        token = request_data.get("token", "")
        
        if not token:
            return {
                "code": 400,
                "message": "Token不能为空",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.logout(token)
        
        return {
            "code": 200,
            "message": result['message'],
            "data": None
        }
        
    except Exception as e:
        print(f"登出失败: {e}")
        return {
            "code": 500,
            "message": f"登出失败: {str(e)}",
            "data": None
        }


@app.get("/api/auth/user/{user_id}")
async def get_user_info(user_id: str):
    """
    获取用户信息
    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "user_id": "xxx",
            "username": "user001",
            "email": "user@example.com",
            "nickname": "昵称",
            "avatar_url": "...",
            ...
        }
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        auth_service = get_auth_service()
        user_info = auth_service.get_user_info(user_id)
        
        if user_info:
            return {
                "code": 200,
                "message": "Success",
                "data": user_info
            }
        else:
            return {
                "code": 404,
                "message": "用户不存",
                "data": None
            }
            
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return {
            "code": 500,
            "message": f"获取用户信息失败: {str(e)}",
            "data": None
        }


@app.put("/api/auth/user/{user_id}")
async def update_user_info(user_id: str, request_data: Dict[str, Any]):
    """
    更新用户信息
    
    请求体:
    {
        "nickname": "新昵称",
        "avatar_url": "...",
        "phone": "13800138000"
    }
    
    返回:
    {
        "code": 200,
        "message": "更新成功",
        "data": {...}
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        auth_service = get_auth_service()
        result = auth_service.update_user_info(user_id, **request_data)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": result.get('data')
            }
        else:
            return {
                "code": 400,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"更新用户信息失败: {e}")
        return {
            "code": 500,
            "message": f"更新用户信息失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/change-password")
async def change_password(request_data: Dict[str, Any]):
    """
    修改密码
    
    请求个
    {
        "user_id": "xxx",
        "old_password": "old123",
        "new_password": "new123"
    }
    
    返回:
    {
        "code": 200,
        "message": "密码修改成功",
        "data": null
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        user_id = request_data.get("user_id", "")
        old_password = request_data.get("old_password", "")
        new_password = request_data.get("new_password", "")
        
        if not user_id or not old_password or not new_password:
            return {
                "code": 400,
                "message": "参数不完",
                "data": None
            }
        
        if len(new_password) < 6:
            return {
                "code": 400,
                "message": "新密码长度不能少",
                "data": None
            }
        
        auth_service = get_auth_service()
        result = auth_service.change_password(user_id, old_password, new_password)
        
        if result['success']:
            return {
                "code": 200,
                "message": result['message'],
                "data": None
            }
        else:
            return {
                "code": 400,
                "message": result['message'],
                "data": None
            }
            
    except Exception as e:
        print(f"修改密码失败: {e}")
        return {
            "code": 500,
            "message": f"修改密码失败: {str(e)}",
            "data": None
        }


@app.post("/api/auth/verify-token")
async def verify_token(request_data: Dict[str, Any]):
    """
    验证Token
    
    请求个
    {
        "token": "xxx"
    }
    
    返回:
    {
        "code": 200,
        "message": "Token有效",
        "data": {
            "user_id": "xxx",
            "valid": true
        }
    }
    """
    try:
        from auth.auth_service import get_auth_service
        
        token = request_data.get("token", "")
        
        if not token:
            return {
                "code": 400,
                "message": "Token不能为空",
                "data": None
            }
        
        auth_service = get_auth_service()
        user_id = auth_service.verify_token(token)
        
        if user_id:
            return {
                "code": 200,
                "message": "Token有效",
                "data": {
                    "user_id": user_id,
                    "valid": True
                }
            }
        else:
            return {
                "code": 401,
                "message": "Token无效或已过期",
                "data": {
                    "valid": False
                }
            }
            
    except Exception as e:
        print(f"验证Token失败: {e}")
        return {
            "code": 500,
            "message": f"验证Token失败: {str(e)}",
            "data": None
        }


# ==================== WebSocket 流式聊天API ====================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket 流式聊天接口 - HarmonyOS 真正的实时流式方案
    使用 WebSocket 替代 SSE,实现真正的实时双向通信
    
    消息格式:
    客户端发送: {"user_id": "xxx", "message": "你好"}
    服务端返回: {"type": "start", "session_id": "xxx"}
                {"type": "progress", "content": "..."}
                {"type": "thinking_chunk", "content": "..."}
                {"type": "answer_chunk", "content": "..."}
                {"type": "done"}
    """
    await websocket.accept()
    print(f"🔌 WebSocket 连接已建立")
    
    try:
        while True:
            # 接收客户端消息
            message_data = await websocket.receive_text()
            print(f"📨 收到 WebSocket 消息: {message_data[:100]}...")
            
            try:
                request_data = json.loads(message_data)
                user_id = request_data.get("user_id", "default_user")
                message = request_data.get("message", "")
                user_context = request_data.get("context", {})
                session_id = request_data.get("session_id")  # 前端可以传入session_id
                
                if not message:
                    await websocket.send_json({"type": "error", "content": "消息不能为空"})
                    continue
                
                # 生成或使用现有会话ID
                import uuid
                if not session_id:
                    session_id = f"session_{uuid.uuid4().hex[:16]}"
                
                # 保存用户消息到数据库
                from backend.conversation.conversation_storage import ConversationStorage
                ConversationStorage.save_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="user",
                    content=message
                )
                
                # 【实时洞察分析】从用户消息中提取情绪、话题、意图等数据
                try:
                    from backend.emergence.realtime_analyzer import analyze_message_realtime
                    insights = analyze_message_realtime(
                        user_id=user_id,
                        message=message,
                        message_id=f"{session_id}_{datetime.now().timestamp()}",
                        metadata=user_context  # 可包含图像描述、语音情感等
                    )
                    if insights:
                        print(f"🔍 [实时洞察] 提取了 {len(insights)} 条洞察数据")
                except Exception as e:
                    print(f"⚠️ [实时洞察] 分析失败: {e}")
                
                # 同时保存到内存（用于当前会话）
                global chat_history_storage
                if user_id not in chat_history_storage:
                    chat_history_storage[user_id] = {}
                if session_id not in chat_history_storage[user_id]:
                    chat_history_storage[user_id][session_id] = []
                
                user_message_data = {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }
                chat_history_storage[user_id][session_id].append(user_message_data)
                
                # 发送开始信息
                await websocket.send_json({"type": "start", "session_id": session_id})
                
                # 获取用户系统
                systems = get_or_create_user_system(user_id)
                
                # 使用LLM服务处理
                llm_service = get_or_init_llm_service()
                
                # 发送进度：分析中
                await websocket.send_json({"type": "progress", "content": "🔄 正在分析你的问题..."})
                await asyncio.sleep(0.3)
                
                # 第一步：生成思考过程
                thinking_prompt = f"""请分析这个问题并说明你的思考过程：

{message}

请用2-3句话简短说明你的思考过程。"""

                thinking_text = ""
                try:
                    messages = [{"role": "user", "content": thinking_prompt}]
                    thinking_text = llm_service.chat(messages, temperature=0.7)
                    print(f"💭 生成的思考过程: {thinking_text[:100]}...")
                except Exception as e:
                    print(f"思考过程生成失败: {e}")
                    thinking_text = "让我思考一下如何最好地回答这个问题..."
                
                # 推送思考过程(流式) - 逐字推送，模拟真实打字
                if thinking_text:
                    await websocket.send_json({"type": "progress", "content": "💭 思考中..."})
                    await asyncio.sleep(0.2)
                    
                    # 更小的chunk，更快的速度
                    chunk_size = 2  # 每次2个字符
                    for i in range(0, len(thinking_text), chunk_size):
                        chunk = thinking_text[i:i+chunk_size]
                        await websocket.send_json({"type": "thinking_chunk", "content": chunk})
                        await asyncio.sleep(0.03)  # 30ms延迟，更流畅
                    
                    await asyncio.sleep(0.3)
                
                # 第二步：生成正式回答
                await websocket.send_json({"type": "progress", "content": "✍️ 生成回答..."})
                await asyncio.sleep(0.2)
                
                try:
                    messages = [{"role": "user", "content": message}]
                    final_response = llm_service.chat(messages, temperature=0.7)
                    print(f"💬 生成的回答: {final_response[:100]}...")
                except Exception as e:
                    print(f"LLM调用失败: {e}")
                    final_response = f"抱歉，我现在无法回答。错误：{str(e)}"
                
                # 推送回复内容(流式) - 逐字推送，模拟真实打字
                if final_response:
                    print(f"📤 [WebSocket] 推送回复内容，长度: {len(final_response)}")
                    
                    # 更小的chunk，更快的速度
                    chunk_size = 3  # 每次3个字符
                    for i in range(0, len(final_response), chunk_size):
                        chunk = final_response[i:i+chunk_size]
                        await websocket.send_json({"type": "answer_chunk", "content": chunk})
                        await asyncio.sleep(0.025)  # 25ms延迟，更流畅
                
                # 推送完成信息
                await websocket.send_json({"type": "done"})
                print(f"✅ [WebSocket] 会话 {session_id} 完成")
                
                # 保存AI回复到数据库
                from backend.conversation.conversation_storage import ConversationStorage
                ConversationStorage.save_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="assistant",
                    content=final_response,
                    thinking=thinking_text
                )
                
                # 同时保存到RAG系统（用于LoRA训练）
                try:
                    from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
                    rag = ProductionRAGSystem(user_id)
                    conversation_content = f"用户: {message}\nAI: {final_response}"
                    rag.add_memory(
                        memory_type=MemoryType.CONVERSATION,
                        content=conversation_content,
                        metadata={
                            "session_id": session_id,
                            "thinking": thinking_text
                        }
                    )
                    print(f"✅ 对话已保存到RAG系统")
                except Exception as e:
                    print(f"⚠️ 保存到RAG系统失败: {e}")
                
                # 同时保存到内存（用于当前会话）
                ai_message_data = {
                    "role": "assistant",
                    "content": final_response,
                    "thinking": thinking_text,
                    "timestamp": datetime.now().isoformat()
                }
                chat_history_storage[user_id][session_id].append(ai_message_data)
                print(f"💾 已保存对话到数据库和内存，会话 {session_id}，共 {len(chat_history_storage[user_id][session_id])} 条消息")
                
                # 添加到RAG记忆
                try:
                    if systems.get('rag'):
                        systems['rag'].add_memory(
                            memory_type=MemoryType.CONVERSATION,
                            content=message,
                            metadata={"user_id": user_id, "response": final_response},
                            importance=0.7
                        )
                except Exception as e:
                    print(f"⚠️ 对话记忆保存失败: {e}")
                
                # 提取信息到知识图谱（增强版：添加关系推断和场景隔离）
                try:
                    from knowledge.information_extractor import InformationExtractor
                    from knowledge.information_knowledge_graph import InformationKnowledgeGraph
                    
                    # 使用信息提取器从对话中提取信息
                    extractor = InformationExtractor()
                    combined_text = f"用户: {message}\nAI: {final_response}"
                    extracted_info = extractor.extract_from_conversation(
                        combined_text, 
                        metadata={"user_id": user_id, "session_id": session_id}
                    )
                    
                    entities = extracted_info.get('entities', [])
                    events = extracted_info.get('events', [])
                    concepts = extracted_info.get('concepts', [])
                    
                    print(f"📊 提取结果: {len(entities)} 实体, {len(events)} 事件, {len(concepts)} 概念")
                    
                    # 获取或初始化知识图谱
                    if user_id not in info_kg_systems:
                        info_kg_systems[user_id] = InformationKnowledgeGraph(user_id)
                    
                    info_kg = info_kg_systems[user_id]
                    
                    # 添加提取的信息到知识图谱（带场景标识）
                    info_count = 0
                    node_names = []  # 记录本次添加的节点名称，用于关系推断
                    
                    for entity in entities:
                        node_id = info_kg.add_information(
                            name=entity['name'],
                            info_type='entity',
                            category=entity.get('category', 'general'),
                            confidence=entity.get('confidence', 0.8),
                            attributes={
                                **entity.get('attributes', {}),
                                'session_id': session_id,  # 场景标识
                                'timestamp': time.time()
                            }
                        )
                        node_names.append(entity['name'])
                        print(f"  ➕ 添加实体: {entity['name']} (会话: {session_id})")
                        info_count += 1
                    
                    for event in events:
                        node_id = info_kg.add_information(
                            name=event['name'],
                            info_type='event',
                            category=event.get('category', 'general'),
                            confidence=event.get('confidence', 0.8),
                            attributes={
                                **event.get('attributes', {}),
                                'session_id': session_id,
                                'timestamp': time.time()
                            }
                        )
                        node_names.append(event['name'])
                        print(f"  ➕ 添加事件: {event['name']} (会话: {session_id})")
                        info_count += 1
                    
                    for concept in concepts:
                        node_id = info_kg.add_information(
                            name=concept['name'],
                            info_type='concept',
                            category=concept.get('category', 'general'),
                            confidence=concept.get('confidence', 0.8),
                            attributes={
                                **concept.get('attributes', {}),
                                'session_id': session_id,
                                'timestamp': time.time()
                            }
                        )
                        node_names.append(concept['name'])
                        print(f"  ➕ 添加概念: {concept['name']} (会话: {session_id})")
                        info_count += 1
                    
                    # 使用Qwen3.5-plus推断节点之间的关系
                    if len(node_names) >= 2:
                        print(f"🔗 使用Qwen3.5-plus推断 {len(node_names)} 个节点之间的关系...")
                        try:
                            llm_service = get_or_init_llm_service()
                            
                            # 构造关系推断提示词
                            relation_prompt = f"""分析以下信息节点之间的关系，返回JSON格式的关系列表。

对话内容：
用户: {message}
AI: {final_response[:200]}

提取的节点：
{', '.join(node_names)}

请分析这些节点之间的关系，返回格式：
{{
  "relationships": [
    {{"source": "节点A", "target": "节点B", "type": "关系类型", "confidence": 0.9}},
    ...
  ]
}}

关系类型可以是：RELATED_TO(相关), PART_OF(属于), OCCURS_AT(发生在), INVOLVES(涉及), LEADS_TO(导致)等。
只返回JSON，不要其他文字。"""
                            
                            # 使用消息列表格式调用，并指定 JSON 响应格式
                            relation_response = llm_service.chat(
                                messages=[{"role": "user", "content": relation_prompt}],
                                temperature=0.3,
                                response_format="json_object"
                            )
                            
                            # 解析关系
                            import re
                            json_match = re.search(r'\{.*\}', relation_response, re.DOTALL)
                            if json_match:
                                relation_data = json.loads(json_match.group())
                                relationships = relation_data.get('relationships', [])
                                
                                # 添加关系到知识图谱
                                rel_count = 0
                                for rel in relationships:
                                    if rel['source'] in node_names and rel['target'] in node_names:
                                        info_kg.add_information_relationship(
                                            source_name=rel['source'],
                                            target_name=rel['target'],
                                            relation_type=rel['type'],
                                            properties={
                                                'confidence': rel.get('confidence', 0.8),
                                                'session_id': session_id,
                                                'inferred_by': 'qwen3.5-plus'
                                            }
                                        )
                                        print(f"  🔗 添加关系: {rel['source']} --[{rel['type']}]--> {rel['target']}")
                                        rel_count += 1
                                
                                print(f"✅ 已添加 {rel_count} 条关系")
                        except Exception as e:
                            print(f"⚠️ 关系推断失败: {e}")
                    
                    # 添加来源信息
                    source_id = f"chat_{session_id}_{int(time.time())}"
                    info_kg.add_source(
                        source_type="chat",
                        source_id=source_id,
                        timestamp=time.time(),
                        metadata={
                            "message": message[:100], 
                            "response": final_response[:100],
                            "session_id": session_id
                        }
                    )
                    
                    # 验证是否真的添加成功
                    stats = info_kg.get_statistics()
                    print(f"✅ 已提取 {info_count} 条信息到知识图谱，当前总计: {stats}")
                except Exception as e:
                    print(f"⚠️ 知识图谱提取失败: {e}")
                    import traceback
                    traceback.print_exc()
                
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "无效的JSON格式"})
            except Exception as e:
                print(f"[WebSocket] 处理失败: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({"type": "error", "content": str(e)})
                
    except WebSocketDisconnect:
        print("🔌 WebSocket 连接已断开")
    except Exception as e:
        print(f"[WebSocket] 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 会话管理API ====================

# 全局对话历史存储 {user_id: {session_id: [messages]}}
chat_history_storage = {}

@app.get("/api/chat/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """
    获取用户的所有会话列表
    
    返回格式:
    {
        "code": 200,
        "data": {
            "sessions": [
                {
                    "session_id": "xxx",
                    "title": "关于健康的对话",
                    "message_count": 10,
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T11:00:00"
                }
            ]
        }
    }
    """
    try:
        if user_id not in chat_history_storage:
            return {
                "code": 200,
                "message": "Success",
                "data": {"sessions": []}
            }
        
        user_sessions = chat_history_storage[user_id]
        sessions = []
        
        for session_id, messages in user_sessions.items():
            if not messages:
                continue
            
            # 生成会话标题（使用第一条用户消息）
            first_user_msg = next((m for m in messages if m.get('role') == 'user'), None)
            title = first_user_msg['content'][:30] + "..." if first_user_msg else "新对话"
            
            sessions.append({
                "session_id": session_id,
                "title": title,
                "message_count": len(messages),
                "created_at": messages[0].get('timestamp', datetime.now().isoformat()),
                "updated_at": messages[-1].get('timestamp', datetime.now().isoformat())
            })
        
        # 按更新时间倒序排列
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return {
            "code": 200,
            "message": "Success",
            "data": {"sessions": sessions}
        }
    
    except Exception as e:
        print(f"获取会话列表失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/chat/session/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    """
    获取指定会话的历史消息
    
    返回格式:
    {
        "code": 200,
        "data": {
            "session_id": "xxx",
            "messages": [
                {
                    "role": "user",
                    "content": "你好",
                    "timestamp": "2024-01-01T10:00:00"
                },
                {
                    "role": "assistant",
                    "content": "你好！有什么可以帮助你的吗？",
                    "thinking": "用户打招呼，我应该友好回应",
                    "timestamp": "2024-01-01T10:00:01"
                }
            ]
        }
    }
    """
    try:
        if user_id not in chat_history_storage:
            return {
                "code": 404,
                "message": "User not found",
                "data": None
            }
        
        if session_id not in chat_history_storage[user_id]:
            return {
                "code": 404,
                "message": "Session not found",
                "data": None
            }
        
        messages = chat_history_storage[user_id][session_id]
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "session_id": session_id,
                "messages": messages
            }
        }
    
    except Exception as e:
        print(f"获取会话历史失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/chat/session/new/{user_id}")
async def create_new_session(user_id: str):
    """
    创建新会话
    
    返回格式:
    {
        "code": 200,
        "data": {
            "session_id": "session_xxx"
        }
    }
    """
    try:
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        # 初始化用户存储
        if user_id not in chat_history_storage:
            chat_history_storage[user_id] = {}
        
        # 创建新会话
        chat_history_storage[user_id][session_id] = []
        
        return {
            "code": 200,
            "message": "Session created",
            "data": {"session_id": session_id}
        }
    
    except Exception as e:
        print(f"创建会话失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== V4 对话API（前端新版本使用）====================

@app.get("/api/v4/conversations/{user_id}/list")
async def get_conversations_v4(user_id: str):
    """
    V4: 获取用户的所有对话列表（从数据库读取）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "id": "session_xxx",
                "title": "关于健康的对话",
                "preview": "最近我感觉...",
                "message_count": 10,
                "last_message_time": "2024-01-01T11:00:00"
            }
        ]
    }
    """
    try:
        from backend.conversation.conversation_storage import ConversationStorage
        
        conversations = ConversationStorage.get_user_sessions(user_id)
        
        return {
            "success": True,
            "data": conversations  # 改为 data 字段，与前端接口一致
        }
    
    except Exception as e:
        print(f"获取对话列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "conversations": []
        }


@app.get("/api/v4/conversations/{user_id}/{session_id}/messages")
async def get_conversation_messages_v4(user_id: str, session_id: str):
    """
    V4: 获取指定对话的消息列表（从数据库读取）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "id": "123",
                "role": "user",
                "content": "你好",
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "id": "124",
                "role": "assistant",
                "content": "你好！",
                "thinking": "用户打招呼",
                "timestamp": "2024-01-01T10:00:01"
            }
        ]
    }
    """
    try:
        from backend.conversation.conversation_storage import ConversationStorage
        
        messages = ConversationStorage.get_session_messages(user_id, session_id)
        
        return {
            "success": True,
            "data": messages  # 改为 data 字段，与前端接口一致
        }
    
    except Exception as e:
        print(f"获取对话消息失败: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "messages": []
        }


@app.post("/api/v4/conversations/{user_id}/create")
async def create_conversation_v4(user_id: str):
    """
    V4: 创建新对话
    
    返回格式:
    {
        "success": true,
        "data": {
            "conversation_id": "session_xxx"
        }
    }
    """
    try:
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        # 初始化用户存储
        if user_id not in chat_history_storage:
            chat_history_storage[user_id] = {}
        
        # 创建新会话
        chat_history_storage[user_id][session_id] = []
        
        print(f"✅ 创建新对话: {session_id} for user {user_id}")
        
        return {
            "success": True,
            "data": {
                "conversation_id": session_id
            }
        }
    
    except Exception as e:
        print(f"创建对话失败: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "conversation_id": None
        }


# ==================== 反馈API ====================

@app.post("/api/hybrid/feedback")
async def submit_feedback(request_data: Dict[str, Any]):
    """
    提交用户反馈 - 使用真实的强化学习训    
    请求个
    {
        "user_id": "user_001",
        "rating": 5,
        "helpful": true,
        "action_taken": true,
        "action": "exercise",
        "state": {"health_score": 75, "mood": 7, "stress_level": 5},
        "strategy": "hybrid",
        "comments": "非常有帮助!"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        rating = request_data.get("rating", 3)
        helpful = request_data.get("helpful", False)
        action_taken = request_data.get("action_taken", False)
        action = request_data.get("action", "unknown")
        state = request_data.get("state", {})
        strategy = request_data.get("strategy", "hybrid")
        
        # 使用真实的强化学习训练器
        from backend.learning.rl_trainer import get_rl_trainer, FeedbackType
        rl_trainer = get_rl_trainer(user_id)
        
        # 确定反馈类型
        if action_taken:
            feedback_type = FeedbackType.ADOPTED
        elif helpful:
            feedback_type = FeedbackType.HELPFUL
        elif rating >= 4:
            feedback_type = FeedbackType.HELPFUL
        elif rating >= 3:
            feedback_type = FeedbackType.NEUTRAL
        elif rating >= 2:
            feedback_type = FeedbackType.UNHELPFUL
        else:
            feedback_type = FeedbackType.HARMFUL
        
        # 记录交互并训        training_result = rl_trainer.record_interaction(state, action, feedback_type, strategy)
        
        # 获取训练统计
        stats = rl_trainer.get_training_statistics()
        
        # 评估策略性能
        strategy_performance = rl_trainer.evaluate_strategy_performance()
        
        # 评估推荐性能
        recommendation_performance = rl_trainer.evaluate_recommendation_performance()
        
        return {
            "code": 200,
            "message": "Feedback recorded and model trained",
            "data": {
                "training_result": training_result,
                "evolution_metrics": {
                    "total_samples": stats['total_episodes'],
                    "confidence_score": stats['average_reward'],
                    "best_strategy": stats['best_strategy'],
                    "best_recommendation": stats['best_recommendation']
                },
                "strategy_performance": strategy_performance,
                "recommendation_performance": recommendation_performance
            }
        }
    
    except Exception as e:
        print(f"反馈提交失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 进化指标API ====================

@app.get("/api/chat/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """
    获取用户的所有会话列    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "sessions": [
                {
                    "session_id": "xxx",
                    "title": "对话标题",
                    "start_time": "2024-01-01T00:00:00",
                    "last_time": "2024-01-01T01:00:00",
                    "message_count": 10,
                    "is_current": true
                }
            ]
        }
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager(user_id)
        sessions = manager.get_all_sessions()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "sessions": sessions
            }
        }
    except Exception as e:
        print(f"获取会话列表失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/chat/session/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    """
    获取指定会话的历史记忆    
    返回:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "session_id": "xxx",
            "history": [
                {
                    "role": "user",
                    "content": "消息内容",
                    "timestamp": "2024-01-01T00:00:00"
                }
            ]
        }
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager(user_id, session_id=session_id)
        history = manager.get_conversation_history()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "session_id": session_id,
                "history": history
            }
        }
    except Exception as e:
        print(f"获取会话历史失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.delete("/api/chat/session/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """
    删除指定会话
    
    返回:
    {
        "code": 200,
        "message": "Session deleted",
        "data": null
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager(user_id)
        manager.delete_session(session_id)
        
        return {
            "code": 200,
            "message": "Session deleted",
            "data": None
        }
    except Exception as e:
        print(f"删除会话失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/chat/session/new/{user_id}")
async def create_new_session(user_id: str):
    """
    创建新会    
    返回:
    {
        "code": 200,
        "message": "New session created",
        "data": {
            "session_id": "xxx"
        }
    }
    """
    try:
        from llm.enhanced_conversation_manager import get_conversation_manager, clear_conversation_manager_cache
        
        # 清除缓存,强制创建新会话
        clear_conversation_manager_cache(user_id)
        
        manager = get_conversation_manager(user_id)
        
        return {
            "code": 200,
            "message": "New session created",
            "data": {
                "session_id": manager.session_id
            }
        }
    except Exception as e:
        print(f"创建新会话失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 进化指标API ====================

@app.get("/api/hybrid/strategy/{user_id}")
async def get_hybrid_strategy(user_id: str):
    """获取混合智能策略"""
    try:
        hybrid_system = get_or_create_hybrid_system(user_id)
        
        # 获取当前策略
        strategy = {
            "user_id": user_id,
            "current_strategy": "balanced",
            "ai_weight": 0.6,
            "human_weight": 0.4,
            "confidence": 0.75,
            "recommendations": [
                "继续当前策略",
                "增加AI辅助比重"
            ]
        }
        
        return {
            "code": 200,
            "message": "Success",
            "data": strategy
        }
    except Exception as e:
        print(f"获取策略失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/hybrid/evolution/{user_id}")
async def get_evolution_metrics(user_id: str):
    """获取进化指标"""
    try:
        systems = get_or_create_user_system(user_id)
        
        stats = systems['learner'].get_statistics()
        
        return {
            "code": 200,
            "data": {
                "totalSamples": stats['total_episodes'],
                "confidenceScore": stats['average_reward'],
                "accuracy": 0.75,
                "domainMetrics": {
                    "health": {"accuracy": 0.8, "samples": 100},
                    "time": {"accuracy": 0.75, "samples": 80},
                    "emotion": {"accuracy": 0.7, "samples": 60}
                },
                "recommendedStrategy": "hybrid",
                "lastUpdated": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取进化指标失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 涌现检测API ====================

@app.get("/api/emergence/patterns/{user_id}")
async def get_emergence_patterns(user_id: str):
    """
    获取用户的涌现模式    
    返回检测到的级联效应,反馈环,临界点和协同效    """
    try:
        # 获取用户的历史数        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "health_score": record.health_score if hasattr(record, 'health_score') else 75,
                "sleep_hours": record.sleep_hours if hasattr(record, 'sleep_hours') else 7,
                "exercise_minutes": record.exercise_minutes if hasattr(record, 'exercise_minutes') else 30,
                "stress_level": record.stress_level if hasattr(record, 'stress_level') else 5,
                "mood": getattr(record, 'mood', 7),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "efficiency_score": getattr(record, 'efficiency_score', 75),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_hours": getattr(record, 'social_hours', 2),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000)
            })
        
        # 获取当前用户数据
        user_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 检测涌现模式        patterns = emergence_detector.detect_all_patterns(user_data, history)
        
        # 获取模式总结
        summary = emergence_detector.get_pattern_summary(patterns)
        
        return {
            "code": 200,
            "message": "Emergence patterns detected",
            "data": {
                "user_id": user_id,
                "detection_time": datetime.now().isoformat(),
                "summary": summary,
                "patterns": summary["patterns"]
            }
        }
    
    except Exception as e:
        print(f"涌现检测失 {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/cascade/{user_id}")
async def get_cascade_patterns(user_id: str):
    """获取级联效应模式"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "health_score": getattr(r, 'health_score', 75),
                "time_pressure": getattr(r, 'time_pressure', 0.3),
                "mood": getattr(r, 'mood', 7),
                "sleep_hours": getattr(r, 'sleep_hours', 7),
                "efficiency_score": getattr(r, 'efficiency_score', 75)
            }
            for r in health_records
        ]
        
        cascades = emergence_detector.cascade_detector.detect_cascades({}, history)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "cascade_count": len(cascades),
                "cascades": [
                    {
                        "id": c.pattern_id,
                        "domains": c.domains,
                        "description": c.description,
                        "confidence": c.confidence,
                        "impact_score": c.impact_score,
                        "recommendations": c.recommendations
                    }
                    for c in cascades
                ]
            }
        }
    
    except Exception as e:
        print(f"级联检测失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/feedback-loops/{user_id}")
async def get_feedback_loops(user_id: str):
    """获取反馈环模式"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "stress_level": getattr(r, 'stress_level', 5),
                "sleep_hours": getattr(r, 'sleep_hours', 7),
                "exercise_minutes": getattr(r, 'exercise_minutes', 30),
                "mood": getattr(r, 'mood', 7),
                "loneliness": getattr(r, 'loneliness', 3),
                "social_hours": getattr(r, 'social_hours', 2)
            }
            for r in health_records
        ]
        
        loops = emergence_detector.feedback_detector.detect_feedback_loops({}, history)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "loop_count": len(loops),
                "feedback_loops": [
                    {
                        "id": l.pattern_id,
                        "domains": l.domains,
                        "description": l.description,
                        "confidence": l.confidence,
                        "impact_score": l.impact_score,
                        "recommendations": l.recommendations
                    }
                    for l in loops
                ]
            }
        }
    
    except Exception as e:
        print(f"反馈环检测失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/tipping-points/{user_id}")
async def get_tipping_points(user_id: str):
    """获取临界点模式"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "health_score": getattr(r, 'health_score', 75),
                "mood": getattr(r, 'mood', 7),
                "efficiency_score": getattr(r, 'efficiency_score', 75)
            }
            for r in health_records
        ]
        
        tipping_points = emergence_detector.tipping_detector.detect_tipping_points({}, history)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "tipping_point_count": len(tipping_points),
                "tipping_points": [
                    {
                        "id": tp.pattern_id,
                        "domains": tp.domains,
                        "description": tp.description,
                        "confidence": tp.confidence,
                        "impact_score": tp.impact_score,
                        "recommendations": tp.recommendations
                    }
                    for tp in tipping_points
                ]
            }
        }
    
    except Exception as e:
        print(f"临界点检测失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/synergies/{user_id}")
async def get_synergies(user_id: str):
    """获取协同效应模式"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "health_score": getattr(r, 'health_score', 75),
                "time_pressure": getattr(r, 'time_pressure', 0.3),
                "mood": getattr(r, 'mood', 7),
                "exercise_minutes": getattr(r, 'exercise_minutes', 30),
                "sleep_hours": getattr(r, 'sleep_hours', 7)
            }
            for r in health_records
        ]
        
        synergies = emergence_detector.synergy_detector.detect_synergies({}, history)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "synergy_count": len(synergies),
                "synergies": [
                    {
                        "id": s.pattern_id,
                        "domains": s.domains,
                        "description": s.description,
                        "confidence": s.confidence,
                        "impact_score": s.impact_score,
                        "recommendations": s.recommendations
                    }
                    for s in synergies
                ]
            }
        }
    
    except Exception as e:
        print(f"协同效应检测失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 报告生成API ====================

@app.get("/api/emergence/report/{user_id}")
async def get_emergence_report(user_id: str):
    """
    获取涌现模式综合分析报告
    
    返回详细的涌现模式分析,风险评估,行动计划等
    """
    try:
        # 获取用户的历史数        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "health_score": getattr(record, 'health_score', 75),
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "mood": getattr(record, 'mood', 7),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "efficiency_score": getattr(record, 'efficiency_score', 75),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_hours": getattr(record, 'social_hours', 2),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000)
            })
        
        # 获取当前用户数据
        user_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 检测涌现模式
        patterns = emergence_detector.detect_all_patterns(user_data, history)
        
        # 转换为字典格式
        patterns_dict = [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type.value,
                "domains": p.domains,
                "description": p.description,
                "confidence": p.confidence,
                "impact_score": p.impact_score,
                "recommendations": p.recommendations,
                "evidence": p.evidence,
                "affected_metrics": p.affected_metrics
            }
            for p in patterns
        ]
        
        # 生成综合报告
        report = report_generator.generate_comprehensive_report(
            user_id=user_id,
            patterns=patterns_dict,
            user_data=user_data,
            history=history
        )
        
        return {
            "code": 200,
            "message": "Report generated successfully",
            "data": report
        }
    
    except Exception as e:
        print(f"报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/report/{user_id}/executive-summary")
async def get_executive_summary(user_id: str):
    """获取执行摘要"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "health_score": getattr(r, 'health_score', 75),
                "mood": getattr(r, 'mood', 7),
                "stress_level": getattr(r, 'stress_level', 5),
                "time_pressure": getattr(r, 'time_pressure', 0.3),
                "social_satisfaction": getattr(r, 'social_satisfaction', 7),
                "efficiency_score": getattr(r, 'efficiency_score', 75),
                "loneliness": getattr(r, 'loneliness', 3),
                "social_hours": getattr(r, 'social_hours', 2),
                "sleep_hours": getattr(r, 'sleep_hours', 7),
                "exercise_minutes": getattr(r, 'exercise_minutes', 30)
            }
            for r in health_records
        ]
        
        user_data = {"user_id": user_id}
        patterns = emergence_detector.detect_all_patterns(user_data, history)
        
        patterns_dict = [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type.value,
                "domains": p.domains,
                "description": p.description,
                "confidence": p.confidence,
                "impact_score": p.impact_score,
                "recommendations": p.recommendations
            }
            for p in patterns
        ]
        
        summary = report_generator._generate_executive_summary(patterns_dict)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "summary": summary,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"执行摘要生成失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/report/{user_id}/action-plan")
async def get_action_plan(user_id: str):
    """获取行动计划"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "health_score": getattr(r, 'health_score', 75),
                "mood": getattr(r, 'mood', 7),
                "stress_level": getattr(r, 'stress_level', 5),
                "time_pressure": getattr(r, 'time_pressure', 0.3),
                "social_satisfaction": getattr(r, 'social_satisfaction', 7),
                "efficiency_score": getattr(r, 'efficiency_score', 75),
                "loneliness": getattr(r, 'loneliness', 3),
                "social_hours": getattr(r, 'social_hours', 2),
                "sleep_hours": getattr(r, 'sleep_hours', 7),
                "exercise_minutes": getattr(r, 'exercise_minutes', 30)
            }
            for r in health_records
        ]
        
        user_data = {"user_id": user_id}
        patterns = emergence_detector.detect_all_patterns(user_data, history)
        
        patterns_dict = [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type.value,
                "domains": p.domains,
                "description": p.description,
                "confidence": p.confidence,
                "impact_score": p.impact_score,
                "recommendations": p.recommendations
            }
            for p in patterns
        ]
        
        action_plan = report_generator._generate_action_plan(patterns_dict)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "action_plan": action_plan,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"行动计划生成失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/emergence/report/{user_id}/risk-assessment")
async def get_risk_assessment(user_id: str):
    """获取风险评估"""
    try:
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        history = [
            {
                "health_score": getattr(r, 'health_score', 75),
                "mood": getattr(r, 'mood', 7),
                "stress_level": getattr(r, 'stress_level', 5),
                "time_pressure": getattr(r, 'time_pressure', 0.3),
                "social_satisfaction": getattr(r, 'social_satisfaction', 7),
                "efficiency_score": getattr(r, 'efficiency_score', 75),
                "loneliness": getattr(r, 'loneliness', 3),
                "social_hours": getattr(r, 'social_hours', 2),
                "sleep_hours": getattr(r, 'sleep_hours', 7),
                "exercise_minutes": getattr(r, 'exercise_minutes', 30)
            }
            for r in health_records
        ]
        
        user_data = {"user_id": user_id}
        patterns = emergence_detector.detect_all_patterns(user_data, history)
        
        patterns_dict = [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type.value,
                "domains": p.domains,
                "description": p.description,
                "confidence": p.confidence,
                "impact_score": p.impact_score,
                "recommendations": p.recommendations
            }
            for p in patterns
        ]
        
        risk_assessment = report_generator._assess_risks(patterns_dict)
        
        return {
            "code": 200,
            "data": {
                "user_id": user_id,
                "risk_assessment": risk_assessment,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"风险评估生成失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== Phase 2: 涌现检测深化API ====================

# 初始化涌现检测系统
from backend.prediction.emergence_detection import get_emergence_detection_system
emergence_system = get_emergence_detection_system()

# 初始化流式分析模式
from backend.prediction.streaming_analysis import (
    get_streaming_engine,
    get_pattern_monitor,
    get_analysis_scheduler,
    get_batch_processor
)
streaming_engine = get_streaming_engine()
pattern_monitor = get_pattern_monitor()
analysis_scheduler = get_analysis_scheduler()
batch_processor = get_batch_processor()

@app.post("/api/v2/emergence/analyze")
async def analyze_emergence_deep(request_data: Dict[str, Any]):
    """
    Phase 2: 涌现检测深化分    
    执行完整的因果推理,多尺度模式检测,可视化,解释生    
    请求个
    {
        "user_id": "user_001",
        "days": 30
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        days = request_data.get("days", 30)
        
        # 获取历史数据
        health_records = db_manager.get_health_records(user_id, limit=days)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No historical data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "health_score": getattr(record, 'health_score', 75),
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "mood": getattr(record, 'mood', 7),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "efficiency_score": getattr(record, 'efficiency_score', 75),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_hours": getattr(record, 'social_hours', 2),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000)
            })
        
        # 执行涌现检测分        result = emergence_system.analyze(history)
        
        return {
            "code": 200,
            "message": "Emergence analysis completed",
            "data": result
        }
    
    except Exception as e:
        print(f"涌现检测分析失 {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v2/emergence/patterns/{user_id}")
async def get_emergence_patterns_deep(user_id: str):
    """
    获取涌现模式详细信息(Phase 2深化版本    
    返回因果图,模式网络,时间线等可视化数据
    """
    try:
        # 获取历史数据
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found",
                "data": None
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "health_score": getattr(record, 'health_score', 75),
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "mood": getattr(record, 'mood', 7),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "efficiency_score": getattr(record, 'efficiency_score', 75),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_hours": getattr(record, 'social_hours', 2),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000)
            })
        
        # 执行分析
        result = emergence_system.analyze(history)
        
        if result.get("status") == "success":
            return {
                "code": 200,
                "message": "Patterns retrieved",
                "data": {
                    "user_id": user_id,
                    "patterns": result.get("patterns", []),
                    "causal_graph": result.get("causal_graph", {}),
                    "dashboard": result.get("dashboard", {})
                }
            }
        else:
            return {
                "code": 500,
                "message": result.get("message", "Analysis failed"),
                "data": None
            }
    
    except Exception as e:
        print(f"获取模式失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v2/emergence/pattern/{pattern_id}")
async def get_pattern_details(pattern_id: str):
    """
    获取单个模式的详细信息    
    包括因果链,解释,可视化配置    """
    try:
        pattern_details = emergence_system.get_pattern_details(pattern_id)
        
        if pattern_details:
            return {
                "code": 200,
                "message": "Pattern details retrieved",
                "data": pattern_details
            }
        else:
            return {
                "code": 404,
                "message": "Pattern not found",
                "data": None
            }
    
    except Exception as e:
        print(f"获取模式详情失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v2/emergence/export")
async def export_emergence_analysis(request_data: Dict[str, Any]):
    """
    导出涌现检测分析结    
    请求个
    {
        "format": "json" | "html"
    }
    """
    try:
        format_type = request_data.get("format", "json")
        
        export_data = emergence_system.export_analysis(format_type)
        
        return {
            "code": 200,
            "message": f"Analysis exported as {format_type}",
            "data": {
                "format": format_type,
                "content": export_data
            }
        }
    
    except Exception as e:
        print(f"导出失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v2/emergence/history/{user_id}")
async def get_analysis_history(user_id: str):
    """
    获取用户的分析历    """
    try:
        history = emergence_system.get_analysis_history()
        
        return {
            "code": 200,
            "message": "Analysis history retrieved",
            "data": {
                "user_id": user_id,
                "history": history,
                "total_analyses": len(history)
            }
        }
    
    except Exception as e:
        print(f"获取历史失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== Phase 2.2: 实时流式分析API ====================

@app.get("/api/v2/emergence/stream/{user_id}")
async def stream_emergence_analysis(user_id: str):
    """
    流式分析端点(SSE    
    使用Server-Sent Events推送实时分析结    """
    try:
        # 获取历史数据
        health_records = db_manager.get_health_records(user_id, limit=30)
        
        if not health_records:
            return {
                "code": 404,
                "message": "No data found"
            }
        
        # 转换为字典列        history = []
        for record in health_records:
            history.append({
                "timestamp": record.timestamp,
                "health_score": getattr(record, 'health_score', 75),
                "sleep_hours": getattr(record, 'sleep_hours', 7),
                "exercise_minutes": getattr(record, 'exercise_minutes', 30),
                "stress_level": getattr(record, 'stress_level', 5),
                "mood": getattr(record, 'mood', 7),
                "time_pressure": getattr(record, 'time_pressure', 0.3),
                "social_satisfaction": getattr(record, 'social_satisfaction', 7),
                "efficiency_score": getattr(record, 'efficiency_score', 75),
                "loneliness": getattr(record, 'loneliness', 3),
                "social_hours": getattr(record, 'social_hours', 2),
                "sleep_quality": getattr(record, 'sleep_quality', 7),
                "heart_rate": getattr(record, 'heart_rate', 70),
                "steps": getattr(record, 'steps', 5000)
            })
        
        # 返回流式响应
        return StreamingResponse(
            streaming_engine.stream_analysis(user_id, history),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        print(f"流式分析失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.post("/api/v2/emergence/monitor")
async def monitor_pattern(request_data: Dict[str, Any]):
    """
    监控特定模式
    
    请求个
    {
        "pattern_id": "pattern_xxx",
        "threshold": 0.8
    }
    """
    try:
        pattern_id = request_data.get("pattern_id")
        threshold = request_data.get("threshold", 0.8)
        
        if not pattern_id:
            return {
                "code": 400,
                "message": "pattern_id is required"
            }
        
        # 获取模式详情
        pattern_details = emergence_system.get_pattern_details(pattern_id)
        
        if not pattern_details:
            return {
                "code": 404,
                "message": "Pattern not found"
            }
        
        # 开始监        pattern_monitor.monitor_pattern(pattern_id, pattern_details["pattern"], threshold)
        
        return {
            "code": 200,
            "message": "Pattern monitoring started",
            "data": {
                "pattern_id": pattern_id,
                "threshold": threshold
            }
        }
    
    except Exception as e:
        print(f"模式监控失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/v2/emergence/alerts")
async def get_pattern_alerts():
    """
    获取模式告警
    """
    try:
        alerts = pattern_monitor.get_alerts()
        
        return {
            "code": 200,
            "message": "Alerts retrieved",
            "data": {
                "alerts": alerts,
                "total": len(alerts)
            }
        }
    
    except Exception as e:
        print(f"获取告警失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.post("/api/v2/emergence/batch-analyze")
async def batch_analyze_emergence(request_data: Dict[str, Any]):
    """
    批量分析多个用户的涌现模式    
    请求个
    {
        "analyses": [
            {"user_id": "user_001", "history": [...]},
            {"user_id": "user_002", "history": [...]}
        ]
    }
    """
    try:
        analyses = request_data.get("analyses", [])
        
        if not analyses:
            return {
                "code": 400,
                "message": "analyses is required"
            }
        
        # 批量处理
        results = await batch_processor.process_batch(analyses)
        
        return {
            "code": 200,
            "message": "Batch analysis completed",
            "data": {
                "total": len(results),
                "successful": len([r for r in results if r["status"] == "success"]),
                "failed": len([r for r in results if r["status"] == "error"]),
                "results": results
            }
        }
    
    except Exception as e:
        print(f"批量分析失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/v2/emergence/schedule/{user_id}")
async def get_analysis_schedule(user_id: str):
    """
    获取用户的分析调度信息    """
    try:
        # 获取最近的分析历史
        history = emergence_system.get_analysis_history()
        
        if history:
            # 计算模式波动
            recent_patterns = history[-5:] if len(history) >= 5 else history
            volatility = analysis_scheduler.calculate_volatility(
                [{"strength": 0.5} for _ in recent_patterns]  # 简化示例
            )
            
            # 调整分析频率
            frequency = analysis_scheduler.adjust_frequency(volatility)
        else:
            volatility = 0.0
            frequency = analysis_scheduler.analysis_frequency
        
        return {
            "code": 200,
            "message": "Schedule retrieved",
            "data": {
                "user_id": user_id,
                "analysis_frequency": frequency,
                "frequency_minutes": frequency // 60,
                "pattern_volatility": volatility,
                "adaptive_enabled": analysis_scheduler.adaptive_enabled
            }
        }
    
    except Exception as e:
        print(f"获取调度信息失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


# ==================== Phase 2.3: 混合智能系统API ====================

# 初始化混合智能系统
try:
    from hybrid.hybrid_intelligence import HybridIntelligenceSystem
except ImportError:
    HybridIntelligenceSystem = None

hybrid_systems_v2 = {}

def get_or_create_hybrid_system(user_id: str):
    """获取或创建混合智能系统"""
    if user_id not in hybrid_systems_v2:
        if HybridIntelligenceSystem:
            hybrid_systems_v2[user_id] = HybridIntelligenceSystem(user_id)
        else:
            hybrid_systems_v2[user_id] = None
    return hybrid_systems_v2[user_id]


@app.post("/api/v2/hybrid/process-task")
async def process_hybrid_task(request_data: Dict[str, Any]):
    """
    处理混合智能任务
    
    请求个
    {
        "user_id": "user_001",
        "domain": "health",
        "task_type": "analysis",
        "context": {...},
        "llm_response": "..."
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        domain = request_data.get("domain")
        task_type = request_data.get("task_type")
        context = request_data.get("context", {})
        llm_response = request_data.get("llm_response")
        
        if not domain or not task_type:
            return {
                "code": 400,
                "message": "domain and task_type are required"
            }
        
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 处理任务
        result = system.process_task(domain, task_type, context, llm_response)
        
        return {
            "code": 200,
            "message": "Task processed",
            "data": result
        }
    
    except Exception as e:
        print(f"混合智能任务处理失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.post("/api/v2/hybrid/feedback")
async def add_hybrid_feedback(request_data: Dict[str, Any]):
    """
    添加用户反馈以训练器人模式    
    请求个
    {
        "user_id": "user_001",
        "domain": "health",
        "features": {...},
        "label": "good",
        "feedback": "correct"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        domain = request_data.get("domain")
        features = request_data.get("features", {})
        label = request_data.get("label")
        feedback = request_data.get("feedback")
        
        if not domain:
            return {
                "code": 400,
                "message": "domain is required"
            }
        
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 添加反馈
        system.add_feedback(domain, features, label, feedback)
        
        return {
            "code": 200,
            "message": "Feedback added",
            "data": {
                "user_id": user_id,
                "domain": domain,
                "feedback_recorded": True
            }
        }
    
    except Exception as e:
        print(f"反馈添加失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.post("/api/v2/hybrid/train")
async def train_hybrid_models(request_data: Dict[str, Any]):
    """
    训练器人模型
    
    请求个
    {
        "user_id": "user_001"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 训练模型
        results = system.train_models()
        
        return {
            "code": 200,
            "message": "Models trained",
            "data": {
                "user_id": user_id,
                "training_results": results
            }
        }
    
    except Exception as e:
        print(f"模型训练失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/v2/hybrid/status/{user_id}")
async def get_hybrid_system_status(user_id: str):
    """
    获取混合智能系统状态    """
    try:
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 更新指标
        system.update_metrics()
        
        # 获取系统状态        status = system.get_system_status()
        
        return {
            "code": 200,
            "message": "System status retrieved",
            "data": status
        }
    
    except Exception as e:
        print(f"获取系统状态失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/v2/hybrid/evolution/{user_id}")
async def get_evolution_report(user_id: str):
    """
    获取混合智能系统的进化报    """
    try:
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 获取进化报告
        report = system.metrics_tracker.get_evolution_report()
        
        return {
            "code": 200,
            "message": "Evolution report retrieved",
            "data": report
        }
    
    except Exception as e:
        print(f"获取进化报告失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/v2/hybrid/models/{user_id}")
async def get_personal_models(user_id: str):
    """
    获取用户的所有个人模式    """
    try:
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 获取所有模式        models = system.trainer.get_all_models()
        
        models_data = {
            domain: {
                "model_id": model.model_id,
                "domain": model.domain,
                "version": model.version,
                "accuracy": model.accuracy,
                "confidence": model.confidence,
                "training_samples": model.training_samples,
                "total_samples": model.total_samples,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            }
            for domain, model in models.items()
        }
        
        return {
            "code": 200,
            "message": "Personal models retrieved",
            "data": {
                "user_id": user_id,
                "models": models_data,
                "total_models": len(models_data)
            }
        }
    
    except Exception as e:
        print(f"获取个人模型失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/v2/hybrid/strategy-performance/{user_id}")
async def get_strategy_performance(user_id: str):
    """
    获取策略性能统计
    """
    try:
        # 获取混合智能系统
        system = get_or_create_hybrid_system(user_id)
        
        # 获取策略性能
        performance = system.selector.get_strategy_performance()
        
        return {
            "code": 200,
            "message": "Strategy performance retrieved",
            "data": {
                "user_id": user_id,
                "performance": performance
            }
        }
    
    except Exception as e:
        print(f"获取策略性能失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}"
        }


# ==================== Phase 2.4: 知识图谱推理API ====================

from backend.prediction.knowledge_graph_reasoning import (
    get_knowledge_graph_reasoner,
    get_recommendation_engine,
    get_semantic_query_engine,
    GraphNode,
    GraphRelation
)


@app.post("/api/v2/kg/add-node")
async def add_knowledge_node(request_data: Dict[str, Any]):
    """
    添加知识图谱节点
    
    请求个
    {
        "user_id": "user_001",
        "node_id": "health_sleep",
        "node_type": "concept",
        "properties": {"name": "睡眠", "domain": "health"},
        "labels": ["health", "important"]
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        node_id = request_data.get("node_id")
        node_type = request_data.get("node_type", "entity")
        properties = request_data.get("properties", {})
        labels = request_data.get("labels", [])
        
        if not node_id:
            return {"code": 400, "message": "node_id is required"}
        
        # 获取推理        reasoner = get_knowledge_graph_reasoner(user_id)
        
        # 创建节点
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties,
            labels=labels
        )
        
        # 添加节点
        reasoner.add_node(node)
        
        return {
            "code": 200,
            "message": "Node added",
            "data": {"node_id": node_id}
        }
    
    except Exception as e:
        print(f"添加节点失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/kg/add-relation")
async def add_knowledge_relation(request_data: Dict[str, Any]):
    """
    添加知识图谱关系
    
    请求个
    {
        "user_id": "user_001",
        "source_id": "health_sleep",
        "target_id": "health_score",
        "relation_type": "influences",
        "weight": 0.8,
        "confidence": 0.9
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        source_id = request_data.get("source_id")
        target_id = request_data.get("target_id")
        relation_type = request_data.get("relation_type", "relates_to")
        weight = request_data.get("weight", 1.0)
        confidence = request_data.get("confidence", 1.0)
        
        if not source_id or not target_id:
            return {"code": 400, "message": "source_id and target_id are required"}
        
        # 获取推理        reasoner = get_knowledge_graph_reasoner(user_id)
        
        # 创建关系
        relation = GraphRelation(
            relation_id=f"rel_{source_id}_{target_id}_{datetime.now().timestamp()}",
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence
        )
        
        # 添加关系
        reasoner.add_relation(relation)
        
        return {
            "code": 200,
            "message": "Relation added",
            "data": {"relation_id": relation.relation_id}
        }
    
    except Exception as e:
        print(f"添加关系失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.get("/api/v2/kg/path/{user_id}")
async def query_knowledge_path(user_id: str, start: str, end: str):
    """
    查询知识图谱中的路径
    
    参数:
    - start: 起始节点ID
    - end: 结束节点ID
    """
    try:
        # 获取推理        reasoner = get_knowledge_graph_reasoner(user_id)
        
        # 查找最短路径        path_result = reasoner.find_shortest_path(start, end)
        
        if path_result:
            path, relations, confidence = path_result
            return {
                "code": 200,
                "message": "Path found",
                "data": {
                    "path": path,
                    "relations": [r.relation_type for r in relations],
                    "confidence": confidence,
                    "length": len(path) - 1
                }
            }
        else:
            return {
                "code": 404,
                "message": "No path found",
                "data": None
            }
    
    except Exception as e:
        print(f"路径查询失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.get("/api/v2/kg/similarity/{user_id}")
async def query_node_similarity(user_id: str, node1: str, node2: str):
    """
    计算两个节点的相似度
    """
    try:
        # 获取推理        reasoner = get_knowledge_graph_reasoner(user_id)
        
        # 计算相似        similarity = reasoner.calculate_node_similarity(node1, node2)
        
        return {
            "code": 200,
            "message": "Similarity calculated",
            "data": {
                "node1": node1,
                "node2": node2,
                "similarity": similarity
            }
        }
    
    except Exception as e:
        print(f"相似度计算失 {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.get("/api/v2/kg/similar-nodes/{user_id}")
async def find_similar_nodes(user_id: str, node_id: str, top_k: int = 5):
    """
    查找相似节点
    """
    try:
        # 获取推理        reasoner = get_knowledge_graph_reasoner(user_id)
        
        # 查找相似节点
        similar = reasoner.find_similar_nodes(node_id, top_k=top_k)
        
        return {
            "code": 200,
            "message": "Similar nodes found",
            "data": {
                "node_id": node_id,
                "similar_nodes": [
                    {"node_id": n, "similarity": s}
                    for n, s in similar
                ]
            }
        }
    
    except Exception as e:
        print(f"查找相似节点失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/kg/infer-relations")
async def infer_missing_relations(request_data: Dict[str, Any]):
    """
    推理缺失的关    """
    try:
        user_id = request_data.get("user_id", "default_user")
        confidence_threshold = request_data.get("confidence_threshold", 0.6)
        
        # 获取推理        reasoner = get_knowledge_graph_reasoner(user_id)
        
        # 推理缺失关系
        inferred = reasoner.infer_missing_relations(confidence_threshold)
        
        return {
            "code": 200,
            "message": "Relations inferred",
            "data": {
                "inferred_count": len(inferred),
                "relations": [
                    {
                        "source": r.source_id,
                        "target": r.target_id,
                        "type": r.relation_type,
                        "confidence": r.confidence
                    }
                    for r in inferred[:10]
                ]
            }
        }
    
    except Exception as e:
        print(f"关系推理失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/kg/recommend")
async def get_recommendations(request_data: Dict[str, Any]):
    """
    获取推荐
    
    请求个
    {
        "user_id": "user_001",
        "type": "actions" | "similar" | "collaborative",
        "current_state": {...},
        "goal": "improve_health"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        rec_type = request_data.get("type", "similar")
        current_state = request_data.get("current_state", {})
        goal = request_data.get("goal", "")
        
        # 获取推荐引擎
        engine = get_recommendation_engine(user_id)
        
        if rec_type == "actions":
            recommendations = engine.recommend_actions(current_state, goal, top_k=5)
        elif rec_type == "similar":
            # 获取第一个节点作为参            reasoner = get_knowledge_graph_reasoner(user_id)
            node_ids = list(reasoner.nodes.keys())
            if node_ids:
                recommendations = engine.recommend_similar_items(node_ids[0], top_k=5)
            else:
                recommendations = []
        elif rec_type == "collaborative":
            preferences = current_state.get("preferences", [])
            recommendations = engine.recommend_by_collaborative_filtering(preferences, top_k=5)
        else:
            recommendations = []
        
        return {
            "code": 200,
            "message": "Recommendations generated",
            "data": {
                "type": rec_type,
                "recommendations": recommendations
            }
        }
    
    except Exception as e:
        print(f"推荐生成失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/kg/query")
async def semantic_query(request_data: Dict[str, Any]):
    """
    语义查询
    
    请求个
    {
        "user_id": "user_001",
        "query": "从睡眠到健康分数的路径
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        query_text = request_data.get("query", "")
        
        if not query_text:
            return {"code": 400, "message": "query is required"}
        
        # 获取查询引擎
        query_engine = get_semantic_query_engine(user_id)
        
        # 执行查询
        result = query_engine.query(query_text)
        
        return {
            "code": 200,
            "message": "Query executed",
            "data": {
                "query": result.query,
                "result_type": result.result_type,
                "results": result.results,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
        }
    
    except Exception as e:
        print(f"语义查询失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


# ==================== Phase 2.5: 数字孪生系统API ====================

from backend.prediction.digital_twin import get_digital_twin_system
digital_twin_systems = {}

def get_or_create_digital_twin(user_id: str):
    """获取或创建数字孪生系统"""
    if user_id not in digital_twin_systems:
        digital_twin_systems[user_id] = get_digital_twin_system(user_id)
    return digital_twin_systems[user_id]


@app.post("/api/v2/digital-twin/record-decision")
async def record_decision(request_data: Dict[str, Any]):
    """
    记录决策
    
    请求个
    {
        "user_id": "user_001",
        "decision_type": "health",
        "description": "决定早起运动",
        "context": {"time": "morning", "mood": "good"},
        "options": ["运动", "休息", "工作"],
        "chosen_option": "运动",
        "expected_impact": {"health_score": 0.1, "mood": 0.05}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        decision_type = request_data.get("decision_type", "health")
        description = request_data.get("description", "")
        context = request_data.get("context", {})
        options = request_data.get("options", [])
        chosen_option = request_data.get("chosen_option", "")
        expected_impact = request_data.get("expected_impact", {})
        
        if not description or not chosen_option:
            return {"code": 400, "message": "description and chosen_option are required"}
        
        # 获取数字孪生系统
        system = get_or_create_digital_twin(user_id)
        
        # 记录决策
        result = system.record_decision(
            decision_type, description, context, options, chosen_option, expected_impact
        )
        
        return {
            "code": 200,
            "message": "Decision recorded",
            "data": result
        }
    
    except Exception as e:
        print(f"决策记录失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/digital-twin/update-outcome")
async def update_decision_outcome(request_data: Dict[str, Any]):
    """
    更新决策结果
    
    请求个
    {
        "user_id": "user_001",
        "decision_id": "dec_xxx",
        "outcome": "positive",
        "actual_impact": {"health_score": 0.12, "mood": 0.08}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        decision_id = request_data.get("decision_id")
        outcome = request_data.get("outcome", "unknown")
        actual_impact = request_data.get("actual_impact", {})
        
        if not decision_id:
            return {"code": 400, "message": "decision_id is required"}
        
        # 获取数字孪生系统
        system = get_or_create_digital_twin(user_id)
        
        # 更新结果
        result = system.update_decision_outcome(decision_id, outcome, actual_impact)
        
        if result:
            return {
                "code": 200,
                "message": "Decision outcome updated",
                "data": result
            }
        else:
            return {
                "code": 404,
                "message": "Decision not found"
            }
    
    except Exception as e:
        print(f"决策结果更新失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/digital-twin/counterfactual")
async def analyze_counterfactual(request_data: Dict[str, Any]):
    """
    分析反事实场    
    请求个
    {
        "user_id": "user_001",
        "decision_id": "dec_xxx",
        "alternative_option": "休息"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        decision_id = request_data.get("decision_id")
        alternative_option = request_data.get("alternative_option")
        
        if not decision_id or not alternative_option:
            return {"code": 400, "message": "decision_id and alternative_option are required"}
        
        # 获取数字孪生系统
        system = get_or_create_digital_twin(user_id)
        
        # 分析反事件        result = system.analyze_counterfactual(decision_id, alternative_option)
        
        if result:
            return {
                "code": 200,
                "message": "Counterfactual analysis completed",
                "data": result
            }
        else:
            return {
                "code": 404,
                "message": "Decision not found"
            }
    
    except Exception as e:
        print(f"反事实分析失 {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/digital-twin/compare")
async def compare_decisions(request_data: Dict[str, Any]):
    """
    对比决策
    
    请求个
    {
        "user_id": "user_001",
        "decision1_id": "dec_xxx",
        "decision2_id": "dec_yyy"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        decision1_id = request_data.get("decision1_id")
        decision2_id = request_data.get("decision2_id")
        
        if not decision1_id or not decision2_id:
            return {"code": 400, "message": "decision1_id and decision2_id are required"}
        
        # 获取数字孪生系统
        system = get_or_create_digital_twin(user_id)
        
        # 对比决策
        result = system.compare_decisions(decision1_id, decision2_id)
        
        if result:
            return {
                "code": 200,
                "message": "Decision comparison completed",
                "data": result
            }
        else:
            return {
                "code": 404,
                "message": "One or both decisions not found"
            }
    
    except Exception as e:
        print(f"决策对比失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.get("/api/v2/digital-twin/status/{user_id}")
async def get_digital_twin_status(user_id: str):
    """
    获取数字孪生系统状态    """
    try:
        # 获取数字孪生系统
        system = get_or_create_digital_twin(user_id)
        
        # 获取系统状态        status = system.get_system_status()
        
        return {
            "code": 200,
            "message": "Digital twin status retrieved",
            "data": status
        }
    
    except Exception as e:
        print(f"获取数字孪生状态失 {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


# ==================== Phase 2.6: 强化学习优化API ====================

from backend.prediction.reinforcement_learning import (
    get_q_learning_agent,
    get_policy_gradient_agent,
    get_rl_evaluator,
    State,
    ActionType
)


@app.post("/api/v2/rl/train-q-learning")
async def train_q_learning(request_data: Dict[str, Any]):
    """
    训练Q-Learning代理
    
    请求个
    {
        "user_id": "user_001",
        "num_episodes": 10,
        "epsilon": 0.1,
        "initial_state": {
            "features": {
                "health_score": 75,
                "mood": 7,
                "efficiency": 70
            }
        }
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        num_episodes = request_data.get("num_episodes", 10)
        epsilon = request_data.get("epsilon", 0.1)
        initial_state_data = request_data.get("initial_state", {})
        
        # 获取Q-Learning代理
        agent = get_q_learning_agent(user_id)
        
        # 训练
        episodes = []
        for i in range(num_episodes):
            state = State(
                state_id=f"state_{i}",
                features=initial_state_data.get("features", {
                    "health_score": 75,
                    "mood": 7,
                    "efficiency": 70
                })
            )
            
            episode = agent.train_episode(state, epsilon=epsilon)
            episodes.append({
                "episode": episode["episode"],
                "steps": episode["steps"],
                "total_reward": episode["total_reward"]
            })
        
        return {
            "code": 200,
            "message": "Q-Learning training completed",
            "data": {
                "user_id": user_id,
                "episodes": episodes,
                "stats": agent.get_training_stats()
            }
        }
    
    except Exception as e:
        print(f"Q-Learning训练失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/rl/train-policy-gradient")
async def train_policy_gradient(request_data: Dict[str, Any]):
    """
    训练策略梯度代理
    
    请求个
    {
        "user_id": "user_001",
        "num_episodes": 10,
        "initial_state": {
            "features": {...}
        }
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        num_episodes = request_data.get("num_episodes", 10)
        initial_state_data = request_data.get("initial_state", {})
        
        # 获取策略梯度代理
        agent = get_policy_gradient_agent(user_id)
        
        # 训练
        episodes = []
        for i in range(num_episodes):
            state = State(
                state_id=f"state_{i}",
                features=initial_state_data.get("features", {
                    "health_score": 75,
                    "mood": 7,
                    "efficiency": 70
                })
            )
            
            episode = agent.train_episode(state)
            episodes.append({
                "episode": episode["episode"],
                "steps": episode["steps"],
                "total_reward": episode["total_reward"]
            })
        
        return {
            "code": 200,
            "message": "Policy gradient training completed",
            "data": {
                "user_id": user_id,
                "episodes": episodes,
                "stats": agent.get_training_stats()
            }
        }
    
    except Exception as e:
        print(f"策略梯度训练失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.get("/api/v2/rl/q-learning-policy/{user_id}")
async def get_q_learning_policy(user_id: str):
    """
    获取Q-Learning最优策    """
    try:
        # 获取Q-Learning代理
        agent = get_q_learning_agent(user_id)
        
        # 获取最优策        policy = agent.get_best_policy()
        
        return {
            "code": 200,
            "message": "Q-Learning policy retrieved",
            "data": {
                "user_id": user_id,
                "policy": {state_id: action.value for state_id, action in policy.items()},
                "policy_size": len(policy)
            }
        }
    
    except Exception as e:
        print(f"获取Q-Learning策略失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.get("/api/v2/rl/training-stats/{user_id}")
async def get_rl_training_stats(user_id: str, agent_type: str = "q_learning"):
    """
    获取强化学习训练统计
    
    参数:
    - agent_type: "q_learning"  "policy_gradient"
    """
    try:
        if agent_type == "q_learning":
            agent = get_q_learning_agent(user_id)
        else:
            agent = get_policy_gradient_agent(user_id)
        
        stats = agent.get_training_stats()
        
        return {
            "code": 200,
            "message": "Training stats retrieved",
            "data": {
                "user_id": user_id,
                "agent_type": agent_type,
                "stats": stats
            }
        }
    
    except Exception as e:
        print(f"获取训练统计失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/rl/evaluate")
async def evaluate_rl_agent(request_data: Dict[str, Any]):
    """
    评估强化学习代理
    
    请求个
    {
        "user_id": "user_001",
        "agent_type": "q_learning",
        "num_episodes": 10,
        "test_states": [...]
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        agent_type = request_data.get("agent_type", "q_learning")
        num_episodes = request_data.get("num_episodes", 10)
        test_states_data = request_data.get("test_states", [])
        
        # 获取代理
        if agent_type == "q_learning":
            agent = get_q_learning_agent(user_id)
        else:
            agent = get_policy_gradient_agent(user_id)
        
        # 创建测试状态        test_states = []
        for i, state_data in enumerate(test_states_data):
            state = State(
                state_id=f"test_state_{i}",
                features=state_data.get("features", {})
            )
            test_states.append(state)
        
        # 如果没有测试状态,创建默认        if not test_states:
            test_states = [State(
                state_id="default_test_state",
                features={
                    "health_score": 75,
                    "mood": 7,
                    "efficiency": 70,
                    "social_satisfaction": 6,
                    "learning_progress": 50
                }
            )]
        
        # 获取评估        evaluator = get_rl_evaluator()
        
        # 评估
        evaluation = evaluator.evaluate_agent(agent, test_states, num_episodes)
        
        return {
            "code": 200,
            "message": "Agent evaluation completed",
            "data": {
                "user_id": user_id,
                "agent_type": agent_type,
                "evaluation": evaluation
            }
        }
    
    except Exception as e:
        print(f"代理评估失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


@app.post("/api/v2/rl/compare-agents")
async def compare_rl_agents(request_data: Dict[str, Any]):
    """
    对比多个强化学习代理
    
    请求个
    {
        "user_id": "user_001",
        "num_episodes": 10
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        num_episodes = request_data.get("num_episodes", 10)
        
        # 获取两个代理
        q_agent = get_q_learning_agent(user_id)
        pg_agent = get_policy_gradient_agent(user_id)
        
        agents = {
            "q_learning": q_agent,
            "policy_gradient": pg_agent
        }
        
        # 创建测试状态
        test_states = [State(
            state_id="test_state",
            features={
                "health_score": 75,
                "mood": 7,
                "efficiency": 70,
                "social_satisfaction": 6,
                "learning_progress": 50
            }
        )]
        
        # 获取评估器
        evaluator = get_rl_evaluator()
        
        # 对比
        comparison = evaluator.compare_agents(agents, test_states, num_episodes)
        
        return {
            "code": 200,
            "message": "Agent comparison completed",
            "data": {
                "user_id": user_id,
                "comparison": comparison
            }
        }
    
    except Exception as e:
        print(f"代理对比失败: {e}")
        return {"code": 500, "message": f"Error: {str(e)}"}


# ==================== 知识图谱自动化构建API ====================

@app.post("/api/v3/kg/build-from-data")
async def build_kg_from_data(request_data: Dict[str, Any]):
    """
    从用户数据自动构建知识图    
    请求个
    {
        "user_id": "user_001",
        "user_data": {
            "sleep_hours": 7,
            "exercise_minutes": 30,
            "stress_level": 5,
            "mood": 7
        },
        "user_message": "我最近睡眠不足,应该怎么办?"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        user_data = request_data.get("user_data", {})
        user_message = request_data.get("user_message", "")
        
        # 获取自动化知识图谱构建器
        from backend.knowledge.automated_kg_builder import get_automated_kg_builder
        kg_builder = get_automated_kg_builder(user_id)
        
        # 从用户数据构建知识图        build_result = kg_builder.build_from_user_data(user_data, user_message)
        
        # 获取图谱统计
        graph_stats = kg_builder.get_graph_statistics()
        
        # 获取因果        causal_chains = []
        if build_result["extracted_entities"]:
            for entity_id in build_result["extracted_entities"][:3]:
                chains = kg_builder.get_causal_chains(entity_id, max_depth=2)
                for chain in chains:
                    entity_names = [kg_builder.entities[eid].name for eid in chain if eid in kg_builder.entities]
                    causal_chains.append("  ".join(entity_names))
        
        return {
            "code": 200,
            "message": "Knowledge graph built successfully",
            "data": {
                "user_id": user_id,
                "build_result": {
                    "extracted_entities": build_result["extracted_entities"],
                    "extracted_entity_count": len(build_result["extracted_entities"]),
                    "inferred_relations": build_result["inferred_relations"],
                    "inferred_relation_count": build_result["new_relations"]
                },
                "graph_statistics": graph_stats,
                "causal_chains": causal_chains[:5],
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"知识图谱构建失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/kg/statistics/{user_id}")
async def get_kg_statistics(user_id: str):
    """
    获取知识图谱统计信息
    """
    try:
        from backend.knowledge.automated_kg_builder import get_automated_kg_builder
        kg_builder = get_automated_kg_builder(user_id)
        
        # 获取统计信息
        stats = kg_builder.get_graph_statistics()
        
        # 导出图谱
        graph_data = kg_builder.export_graph()
        
        return {
            "code": 200,
            "message": "Knowledge graph statistics retrieved",
            "data": {
                "user_id": user_id,
                "statistics": stats,
                "graph_summary": {
                    "entity_count": graph_data["entity_count"],
                    "relation_count": graph_data["relation_count"]
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取知识图谱统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 信息知识图谱API (v4) ====================

@app.get("/api/v4/knowledge-graph/{user_id}/export")
async def export_information_knowledge_graph(user_id: str, session_id: str = None):
    """
    导出信息知识图谱(用于3D可视化)
    
    参数:
    - user_id: 用户ID
    - session_id: 可选，对话会话ID，如果提供则只返回该会话的节点
    
    返回格式:
    {
        "success": true,
        "data": {
            "information": [...],  // 信息节点
            "sources": [...],      // 来源节点
            "relationships": [...]  // 关系
        }
    }
    """
    try:
        # 【优化】直接使用预加载的系统,不做任何初始化
        global info_kg_systems
        
        # 如果用户系统不存在,尝试初始化(仅用于非默认用户)
        if user_id not in info_kg_systems:
            print(f"🔧 初始化信息知识图谱 for {user_id}")
            try:
                info_kg_systems[user_id] = InformationKnowledgeGraph(user_id)
            except Exception as e:
                print(f"信息知识图谱初始化失败: {e}")
                info_kg_systems[user_id] = None
        
        info_kg = info_kg_systems.get(user_id)
        
        if not info_kg:
            print(f"信息知识图谱未初始化 for {user_id}")
            return {
                "success": False,
                "message": "Neo4j 数据库连接失败,请检查后端服务配置",
                "error_code": "KG_NOT_INITIALIZED",
                "data": {
                    "information": [],
                    "sources": [],
                    "relationships": []
                }
            }
        
        # 导出图谱数据(快速操作,直接从Neo4j查询)
        try:
            graph_data = info_kg.export()
        except Exception as export_error:
            print(f"导出图谱数据失败: {export_error}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"导出失败: {str(export_error)}",
                "error_code": "EXPORT_FAILED",
                "data": {
                    "information": [],
                    "sources": [],
                    "relationships": []
                }
            }
        
        # 如果指定了session_id，筛选该会话的节点
        if session_id:
            print(f"🔍 筛选会话 {session_id} 的知识图谱节点")
            
            # 筛选属于该会话的信息节点
            filtered_info = [
                node for node in graph_data.get('information', [])
                if node.get('session_id') == session_id
            ]
            
            # 获取这些节点的ID
            node_ids = {node['id'] for node in filtered_info}
            
            # 筛选这些节点之间的关系
            filtered_rels = [
                rel for rel in graph_data.get('relationships', [])
                if rel['source'] in node_ids and rel['target'] in node_ids
            ]
            
            # 筛选该会话的来源
            filtered_sources = [
                src for src in graph_data.get('sources', [])
                if src.get('session_id') == session_id or 
                   (src.get('metadata') and src['metadata'].get('session_id') == session_id)
            ]
            
            graph_data = {
                'information': filtered_info,
                'sources': filtered_sources,
                'relationships': filtered_rels
            }
            
            print(f"✅ 会话 {session_id}: {len(filtered_info)} 节点, {len(filtered_rels)} 关系")
        
        # 检查是否有数据
        if not graph_data or not graph_data.get('information') or len(graph_data.get('information', [])) == 0:
            print(f"⚠️ 用户 {user_id} 的知识图谱为空")
            return {
                "success": False,
                "message": "知识图谱为空,请先进行对话以构建知识网络",
                "error_code": "KG_EMPTY",
                "data": {
                    "information": [],
                    "sources": [],
                    "relationships": []
                }
            }
        
        print(f"成功导出知识图谱 for {user_id}: {len(graph_data.get('information', []))} 节点")
        return {
            "success": True,
            "data": graph_data
        }
    
    except Exception as e:
        print(f"导出知识图谱失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"导出失败: {str(e)}",
            "error_code": "EXPORT_ERROR",
            "data": {
                "information": [],
                "sources": [],
                "relationships": []
            }
        }


@app.get("/api/v4/knowledge-graph/{user_id}/sessions")
async def get_kg_sessions(user_id: str):
    """
    获取用户所有有知识图谱的会话列表（与对话会话列表对应）
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "session_id": "session_xxx",
                "title": "关于健康的对话",
                "node_count": 5,
                "last_update": "2024-01-01T10:00:00"
            }
        ]
    }
    """
    try:
        global info_kg_systems, chat_history_storage
        
        if user_id not in info_kg_systems:
            info_kg_systems[user_id] = InformationKnowledgeGraph(user_id)
        
        info_kg = info_kg_systems.get(user_id)
        
        if not info_kg:
            return {
                "success": False,
                "message": "信息知识图谱未初始化",
                "data": []
            }
        
        # 导出所有数据
        graph_data = info_kg.export()
        
        # 按session_id分组统计
        session_stats = {}
        for node in graph_data.get('information', []):
            sid = node.get('session_id')
            if sid:
                if sid not in session_stats:
                    session_stats[sid] = {
                        'session_id': sid,
                        'node_count': 0,
                        'last_timestamp': 0
                    }
                
                session_stats[sid]['node_count'] += 1
                
                # 更新时间戳
                ts = node.get('timestamp', 0)
                if ts:
                    session_stats[sid]['last_timestamp'] = max(session_stats[sid]['last_timestamp'], ts)
        
        # 从对话历史中获取会话标题
        sessions = []
        for sid, stats in session_stats.items():
            # 获取对话标题
            title = "未命名对话"
            if user_id in chat_history_storage and sid in chat_history_storage[user_id]:
                messages = chat_history_storage[user_id][sid]
                if messages:
                    first_user_msg = next((m for m in messages if m.get('role') == 'user'), None)
                    if first_user_msg and first_user_msg.get('content'):
                        title = first_user_msg['content'][:30] + "..."
            
            sessions.append({
                'session_id': sid,
                'title': title,
                'node_count': stats['node_count'],
                'last_update': datetime.fromtimestamp(stats['last_timestamp']).isoformat() if stats['last_timestamp'] else datetime.now().isoformat()
            })
        
        # 按最后更新时间降序排列
        sessions.sort(key=lambda x: x['last_update'], reverse=True)
        
        return {
            "success": True,
            "data": sessions  # 改为 data 字段，与前端接口一致
        }
    
    except Exception as e:
        print(f"获取会话列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "sessions": []
        }


@app.get("/api/v4/information/{user_id}/{info_name}/sources")
async def get_information_sources(user_id: str, info_name: str):
    """
    获取信息节点的来源(溯源)
    
    返回格式:
    {
        "success": true,
        "sources": [
            {
                "source_id": "...",
                "type": "conversation",
                "timestamp": 123456,
                "confidence": 0.85
            }
        ]
    }
    """
    try:
        global info_kg_systems
        
        # 获取用户的信息知识图谱
        if user_id not in info_kg_systems:
            info_kg_systems[user_id] = InformationKnowledgeGraph(user_id)
        
        info_kg = info_kg_systems.get(user_id)
        
        if not info_kg:
            return {
                "success": False,
                "message": "信息知识图谱未初始化",
                "sources": []
            }
        
        # 获取信息来源
        sources = info_kg.get_information_sources(info_name)
        
        # 格式化返回数据
        formatted_sources = []
        for src in sources:
            source_data = src['source']
            formatted_sources.append({
                "source_id": source_data.get('source_id', ''),
                "type": source_data.get('type', 'unknown'),
                "timestamp": source_data.get('timestamp', 0),
                "confidence": src.get('confidence', 0.8),
                "description": f"{src['relation_type']} from {source_data.get('type', 'unknown')}"
            })
        
        return {
            "success": True,
            "sources": formatted_sources
        }
    
    except Exception as e:
        print(f"获取信息来源失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "sources": []
        }


@app.get("/api/v4/knowledge-graph/{user_id}/statistics")
async def get_kg_statistics(user_id: str):
    """获取知识图谱统计信息"""
    try:
        global info_kg_systems
        
        # 获取用户的信息知识图谱
        if user_id not in info_kg_systems:
            info_kg_systems[user_id] = InformationKnowledgeGraph(user_id)
        
        info_kg = info_kg_systems.get(user_id)
        
        if not info_kg:
            return {
                "success": False,
                "message": "信息知识图谱未初始化",
                "data": {}
            }
        
        stats = info_kg.get_statistics()
        
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        print(f"获取统计失败: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": {}
        }


# ==================== 强化学习训练API ====================

@app.get("/api/v3/rl/statistics/{user_id}")
async def get_rl_statistics(user_id: str):
    """
    获取强化学习训练统计
    """
    try:
        from backend.learning.rl_trainer import get_rl_trainer
        rl_trainer = get_rl_trainer(user_id)
        
        # 获取训练统计
        stats = rl_trainer.get_training_statistics()
        
        # 评估策略性能
        strategy_performance = rl_trainer.evaluate_strategy_performance()
        
        # 评估推荐性能
        recommendation_performance = rl_trainer.evaluate_recommendation_performance()
        
        return {
            "code": 200,
            "message": "RL training statistics retrieved",
            "data": {
                "user_id": user_id,
                "training_statistics": stats,
                "strategy_performance": strategy_performance,
                "recommendation_performance": recommendation_performance,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取强化学习统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/rl/predict-action-success")
async def predict_action_success(request_data: Dict[str, Any]):
    """
    预测行动的成功概    
    请求个
    {
        "user_id": "user_001",
        "state": {"health_score": 75, "mood": 7, "stress_level": 5},
        "action": "exercise"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        state = request_data.get("state", {})
        action = request_data.get("action", "")
        
        from backend.learning.rl_trainer import get_rl_trainer
        rl_trainer = get_rl_trainer(user_id)
        
        # 预测成功概率
        success_probability = rl_trainer.predict_action_success(state, action)
        
        return {
            "code": 200,
            "message": "Action success probability predicted",
            "data": {
                "user_id": user_id,
                "action": action,
                "state": state,
                "success_probability": success_probability,
                "recommendation": "highly_recommended" if success_probability > 0.7 else "recommended" if success_probability > 0.5 else "not_recommended",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"预测失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/decision/make-decision")
async def make_decision(request_data: Dict[str, Any]):
    """
    做出决策 - 基于真实数据的决策支    
    请求个
    {
        "user_id": "user_001",
        "user_data": {
            "sleep_hours": 5,
            "exercise_minutes": 20,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60
        },
        "knowledge_graph_data": {...},
        "rl_predictions": {"exercise": 0.8, "meditation": 0.7}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        user_data = request_data.get("user_data", {})
        kg_data = request_data.get("knowledge_graph_data", None)
        rl_predictions = request_data.get("rl_predictions", None)
        
        # 获取决策引擎
        from backend.decision.decision_engine import get_decision_engine
        decision_engine = get_decision_engine(user_id)
        
        # 做出决策
        decision = decision_engine.make_decision(user_data, kg_data, rl_predictions)
        
        # 获取决策统计
        stats = decision_engine.get_decision_statistics()
        
        return {
            "code": 200,
            "message": "Decision made successfully",
            "data": {
                "user_id": user_id,
                "decision": decision.to_dict(),
                "decision_statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"决策制定失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/decision/record-feedback")
async def record_decision_feedback(request_data: Dict[str, Any]):
    """
    记录决策反馈
    
    请求个
    {
        "user_id": "user_001",
        "decision_id": "dec_123456",
        "accepted": true,
        "feedback": "很有帮助",
        "actual_impact": {"mood": 0.2, "stress_level": -0.15}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        decision_id = request_data.get("decision_id", "")
        
        from backend.decision.decision_engine import get_decision_engine
        decision_engine = get_decision_engine(user_id)
        
        # 记录反馈
        decision_engine.record_decision_feedback(decision_id, request_data)
        
        # 获取更新后的统计
        stats = decision_engine.get_decision_statistics()
        
        return {
            "code": 200,
            "message": "Decision feedback recorded",
            "data": {
                "user_id": user_id,
                "decision_id": decision_id,
                "decision_statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"反馈记录失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/decision/statistics/{user_id}")
async def get_decision_statistics(user_id: str):
    """
    获取决策统计信息
    """
    try:
        from backend.decision.decision_engine import get_decision_engine
        decision_engine = get_decision_engine(user_id)
        
        # 获取统计信息
        stats = decision_engine.get_decision_statistics()
        
        # 获取最近的决策
        recent_decisions = decision_engine.get_recent_decisions(5)
        
        return {
            "code": 200,
            "message": "Decision statistics retrieved",
            "data": {
                "user_id": user_id,
                "statistics": stats,
                "recent_decisions": recent_decisions,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取决策统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/emergence/detect")
async def detect_emergence(request_data: Dict[str, Any]):
    """
    检测涌现现    
    请求个
    {
        "user_id": "user_001",
        "data_points": [
            {"sleep_hours": 7, "stress_level": 5, "mood": 7},
            {"sleep_hours": 6, "stress_level": 6, "mood": 6},
            {"sleep_hours": 5, "stress_level": 8, "mood": 4}
        ]
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        data_points = request_data.get("data_points", [])
        
        from backend.emergence.emergence_detector import get_emergence_detector
        detector = get_emergence_detector(user_id)
        
        # 添加数据点
        for data in data_points:
            detector.add_data_point(data)
        
        # 检测所有涌现现象
        emergence_events = detector.detect_all_emergences()
        
        # 获取统计信息
        stats = detector.get_emergence_statistics()
        
        return {
            "code": 200,
            "message": "Emergence detection completed",
            "data": {
                "user_id": user_id,
                "detected_events": [e.to_dict() for e in emergence_events],
                "event_count": len(emergence_events),
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"涌现检测失 {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/emergence/statistics/{user_id}")
async def get_emergence_statistics(user_id: str):
    """
    获取涌现检测统    """
    try:
        from backend.emergence.emergence_detector import get_emergence_detector
        detector = get_emergence_detector(user_id)
        
        # 获取统计信息
        stats = detector.get_emergence_statistics()
        
        # 获取最近的事件
        recent_events = detector.get_recent_events(5)
        
        return {
            "code": 200,
            "message": "Emergence statistics retrieved",
            "data": {
                "user_id": user_id,
                "statistics": stats,
                "recent_events": recent_events,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取涌现统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/hybrid/process")
async def process_hybrid_intelligence(request_data: Dict[str, Any]):
    """
    处理混合智能流程 - 完整个层架构处    
    请求个
    {
        "user_id": "user_001",
        "user_message": "我最近睡眠不足,应该怎么办?",
        "user_data": {
            "sleep_hours": 5,
            "exercise_minutes": 20,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60
        },
        "llm_response": "根据您的描述..."
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        user_message = request_data.get("user_message", "")
        user_data = request_data.get("user_data", {})
        llm_response = request_data.get("llm_response", None)
        
        from backend.hybrid.hybrid_intelligence import get_hybrid_intelligence_system
        hybrid_system = get_hybrid_intelligence_system(user_id)
        
        # 处理用户输入
        result = hybrid_system.process_user_input(user_message, user_data, llm_response)
        
        return {
            "code": 200,
            "message": "Hybrid intelligence processing completed",
            "data": result
        }
    
    except Exception as e:
        print(f"混合智能处理失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/hybrid/overview/{user_id}")
async def get_hybrid_system_overview(user_id: str):
    """
    获取混合智能系统概览
    """
    try:
        from backend.hybrid.hybrid_intelligence import get_hybrid_intelligence_system
        hybrid_system = get_hybrid_intelligence_system(user_id)
        
        # 获取系统概览
        overview = hybrid_system.get_system_overview()
        
        return {
            "code": 200,
            "message": "Hybrid system overview retrieved",
            "data": overview
        }
    
    except Exception as e:
        print(f"获取系统概览失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/hybrid/export/{user_id}")
async def export_hybrid_system_state(user_id: str):
    """
    导出混合智能系统状态    """
    try:
        from backend.hybrid.hybrid_intelligence import get_hybrid_intelligence_system
        hybrid_system = get_hybrid_intelligence_system(user_id)
        
        # 导出系统状态        state = hybrid_system.export_system_state()
        
        return {
            "code": 200,
            "message": "Hybrid system state exported",
            "data": state
        }
    
    except Exception as e:
        print(f"导出系统状态失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/digital-twin/predict")
async def predict_with_digital_twin(request_data: Dict[str, Any]):
    """
    使用数字孪生进行预测
    
    请求个
    {
        "user_id": "user_001",
        "current_state": {
            "sleep_hours": 5,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60,
            "exercise_minutes": 20
        },
        "prediction_days": 7
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        current_state = request_data.get("current_state", {})
        prediction_days = request_data.get("prediction_days", 7)
        
        from backend.digital_twin.digital_twin import get_digital_twin
        twin = get_digital_twin(user_id, current_state)
        
        # 预测未来状态        prediction = twin.predict_future_state(prediction_days)
        
        return {
            "code": 200,
            "message": "Digital twin prediction completed",
            "data": {
                "user_id": user_id,
                "prediction": prediction,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"数字孪生预测失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/digital-twin/simulate-intervention")
async def simulate_intervention(request_data: Dict[str, Any]):
    """
    模拟干预效果
    
    请求个
    {
        "user_id": "user_001",
        "current_state": {
            "sleep_hours": 5,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60,
            "exercise_minutes": 20
        },
        "intervention": {
            "sleep_hours": 1.5,
            "exercise_minutes": 20
        },
        "days": 7
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        current_state = request_data.get("current_state", {})
        intervention = request_data.get("intervention", {})
        days = request_data.get("days", 7)
        
        from backend.digital_twin.digital_twin import get_digital_twin
        twin = get_digital_twin(user_id, current_state)
        
        # 模拟干预效果
        result = twin.simulate_intervention(intervention, days)
        
        return {
            "code": 200,
            "message": "Intervention simulation completed",
            "data": {
                "user_id": user_id,
                "simulation": result,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"干预模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/digital-twin/state/{user_id}")
async def get_digital_twin_state(user_id: str):
    """
    获取数字孪生状态    """
    try:
        from backend.digital_twin.digital_twin import get_digital_twin
        twin = get_digital_twin(user_id)
        
        # 导出孪生状态        state = twin.export_twin_state()
        
        return {
            "code": 200,
            "message": "Digital twin state retrieved",
            "data": state
        }
    
    except Exception as e:
        print(f"获取孪生状态失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/counterfactual/what-if")
async def analyze_what_if(request_data: Dict[str, Any]):
    """
    反事实分析:如果...会怎样
    
    请求个
    {
        "user_id": "user_001",
        "original_decision": "work",
        "alternative_decision": "exercise",
        "current_state": {
            "sleep_hours": 5,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60
        },
        "decision_impact": {}
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        original_decision = request_data.get("original_decision", "")
        alternative_decision = request_data.get("alternative_decision", "")
        current_state = request_data.get("current_state", {})
        decision_impact = request_data.get("decision_impact", {})
        
        from backend.decision.counterfactual_analyzer import get_counterfactual_analyzer
        analyzer = get_counterfactual_analyzer(user_id)
        
        # 分析
        analysis = analyzer.analyze_what_if(
            original_decision, alternative_decision,
            current_state, decision_impact
        )
        
        return {
            "code": 200,
            "message": "What-if analysis completed",
            "data": {
                "user_id": user_id,
                "analysis": analysis.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"反事实分析失 {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/counterfactual/opportunity-cost")
async def analyze_opportunity_cost(request_data: Dict[str, Any]):
    """
    分析机会成本
    
    请求个
    {
        "user_id": "user_001",
        "chosen_action": "work",
        "foregone_action": "exercise",
        "current_state": {
            "sleep_hours": 5,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60
        }
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        chosen_action = request_data.get("chosen_action", "")
        foregone_action = request_data.get("foregone_action", "")
        current_state = request_data.get("current_state", {})
        
        from backend.decision.counterfactual_analyzer import get_counterfactual_analyzer
        analyzer = get_counterfactual_analyzer(user_id)
        
        # 分析
        analysis = analyzer.analyze_opportunity_cost(
            chosen_action, foregone_action, current_state
        )
        
        return {
            "code": 200,
            "message": "Opportunity cost analysis completed",
            "data": {
                "user_id": user_id,
                "analysis": analysis.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"机会成本分析失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 完整系统测试API ====================

@app.post("/api/v3/system/full-test")
async def full_system_test(request_data: Dict[str, Any]):
    """
    完整系统测试 - 演示所有组件的集成
    
    请求个
    {
        "user_id": "user_001",
        "user_message": "我最近睡眠不足,压力很大,应该怎么办?",
        "user_data": {
            "sleep_hours": 5,
            "exercise_minutes": 20,
            "stress_level": 8,
            "mood": 4,
            "health_score": 60
        }
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        user_message = request_data.get("user_message", "")
        user_data = request_data.get("user_data", {})
        
        print(f"\n{'='*60}")
        print(f"🚀 开始完整系统测个- 用户: {user_id}")
        print(f"{'='*60}\n")
        
        result = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # 1. 知识图谱构建
        print("📊  步:知识图谱自动构建...")
        from backend.knowledge.automated_kg_builder import get_automated_kg_builder
        kg_builder = get_automated_kg_builder(user_id)
        kg_result = kg_builder.build_from_user_data(user_data, user_message)
        kg_stats = kg_builder.get_graph_statistics()
        result["components"]["knowledge_graph"] = {
            "extracted_entities": kg_result["extracted_entities"],
            "inferred_relations": len(kg_result["inferred_relations"]),
            "total_entities": kg_stats["total_entities"],
            "total_relations": kg_stats["total_relations"]
        }
        print(f"    提取个{len(kg_result['extracted_entities'])}  实")
        print(f"    推理个{len(kg_result['inferred_relations'])}  关系\n")
        
        # 2. 涌现检查        print("🌟  步:涌现现象检查..")
        from backend.emergence.emergence_detector import get_emergence_detector
        detector = get_emergence_detector(user_id)
        detector.add_data_point(user_data)
        emergence_events = detector.detect_all_emergences()
        result["components"]["emergence_detection"] = {
            "detected_events": len(emergence_events),
            "event_types": [e.emergence_type.value for e in emergence_events]
        }
        print(f"    检测到 {len(emergence_events)}  涌现现象\n")
        
        # 3. 强化学习预测
        print("🧠  步:强化学习预测...")
        from backend.learning.rl_trainer import get_rl_trainer
        rl_trainer = get_rl_trainer(user_id)
        available_actions = ["exercise", "sleep", "meditation", "social"]
        selected_action, method = rl_trainer.select_action(user_data, available_actions)
        action_probs = {a: rl_trainer.predict_action_success(user_data, a) for a in available_actions}
        result["components"]["reinforcement_learning"] = {
            "selected_action": selected_action,
            "selection_method": method,
            "action_probabilities": action_probs
        }
        print(f"    推荐行动: {selected_action}")
        print(f"    成功概率: {action_probs[selected_action]:.2f}\n")
        
        # 4. 决策引擎
        print("🎯  步:决策制定...")
        from backend.decision.decision_engine import get_decision_engine
        decision_engine = get_decision_engine(user_id)
        decision = decision_engine.make_decision(user_data, None, action_probs)
        result["components"]["decision_engine"] = {
            "recommendation": decision.recommendation,
            "confidence": decision.confidence,
            "expected_impact": decision.expected_impact
        }
        print(f"    决策: {decision.recommendation}")
        print(f"    置信息 {decision.confidence:.2f}\n")
        
        # 5. 数字孪生预测
        print("🔮  步:数字孪生预测...")
        from backend.digital_twin.digital_twin import get_digital_twin
        twin = get_digital_twin(user_id, user_data)
        prediction = twin.predict_future_state(7)
        result["components"]["digital_twin"] = {
            "prediction_days": 7,
            "scenarios": list(prediction["scenarios"].keys()),
            "recommended_scenario": prediction["recommended_scenario"]
        }
        print(f"    预测了未来7天的状态")
        print(f"    推荐场景: {prediction['recommended_scenario']}\n")
        
        # 6. 反事实分析
        print("🔄  步骤6: 反事实决策分析...")
        from backend.decision.counterfactual_analyzer import get_counterfactual_analyzer
        cf_analyzer = get_counterfactual_analyzer(user_id)
        cf_analysis = cf_analyzer.analyze_what_if(
            "work", "exercise", user_data, {}
        )
        result["components"]["counterfactual_analysis"] = {
            "scenario_type": cf_analysis.scenario_type.value,
            "insights": cf_analysis.insights
        }
        print(f"    完成反事实分")
        print(f"    洞察数量: {len(cf_analysis.insights)}\n")
        
        # 7. 混合智能系统
        print("🤖  步:混合智能整合...")
        from backend.hybrid.hybrid_intelligence import get_hybrid_intelligence_system
        hybrid_system = get_hybrid_intelligence_system(user_id)
        hybrid_result = hybrid_system.process_user_input(user_message, user_data)
        result["components"]["hybrid_intelligence"] = {
            "mode": hybrid_result["components"]["mode_selection"]["selected_mode"],
            "system_health": hybrid_system.system_stats["system_health"]
        }
        print(f"    混合智能模式: {hybrid_result['components']['mode_selection']['selected_mode']}")
        print(f"    系统健康度: {hybrid_system.system_stats['system_health']:.2f}\n")
        
        # 最终建议
        result["final_recommendation"] = {
            "primary_action": decision.recommendation,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "expected_impact": decision.expected_impact,
            "alternative_actions": list(action_probs.keys()),
            "counterfactual_insights": cf_analysis.insights
        }
        
        print(f"{'='*60}")
        print(f"完整系统测试完成")
        print(f"{'='*60}\n")
        
        return {
            "code": 200,
            "message": "Full system test completed successfully",
            "data": result
        }
    
    except Exception as e:
        print(f"系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 真实数据集成API ====================

@app.post("/api/v3/real-data/receive-harmonyos-sensor")
async def receive_harmonyos_sensor_data(request_data: Dict[str, Any]):
    """
    接收来自HarmonyOS前端的真实传感器数据
    
    请求个
    {
        "user_id": "user_001",
        "heart_rate": 72,
        "steps": 1250,
        "accelerometer": {"x": 0.1, "y": 0.2, "z": 9.8},
        "gyroscope": {"x": 0.01, "y": 0.02, "z": 0.03},
        "light": 500,
        "pressure": 1013,
        "temperature": 36.8,
        "blood_oxygen": 97,
        "timestamp": "2026-03-15T10:30:00"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        
        from backend.data_collection.real_data_integration import get_real_data_integration_layer
        integration_layer = get_real_data_integration_layer(user_id)
        
        # 接收并处理传感器数据
        result = integration_layer.receive_harmonyos_sensor_data(request_data)
        
        return {
            "code": 200,
            "message": "Sensor data received successfully",
            "data": result
        }
    
    except Exception as e:
        print(f"传感器数据接收失 {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/real-data/latest-sensor/{user_id}")
async def get_latest_sensor_data(user_id: str):
    """
    获取最新的传感器数    """
    try:
        from backend.data_collection.real_data_integration import get_real_data_integration_layer
        integration_layer = get_real_data_integration_layer(user_id)
        
        latest_data = integration_layer.get_latest_sensor_data()
        
        return {
            "code": 200,
            "message": "Latest sensor data retrieved",
            "data": {
                "user_id": user_id,
                "latest_data": latest_data,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取传感器数据失 {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.post("/api/v3/real-data/daily-statistics")
async def get_daily_statistics(request_data: Dict[str, Any]):
    """
    获取每日统计
    
    请求个
    {
        "user_id": "user_001",
        "date": "2026-03-15"
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        date_str = request_data.get("date", datetime.now().isoformat()[:10])
        
        from datetime import datetime as dt
        date = dt.fromisoformat(date_str)
        
        from backend.data_collection.real_data_integration import get_real_data_integration_layer
        integration_layer = get_real_data_integration_layer(user_id)
        
        statistics = integration_layer.get_daily_statistics(date)
        
        return {
            "code": 200,
            "message": "Daily statistics retrieved",
            "data": statistics
        }
    
    except Exception as e:
        print(f"获取每日统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/v3/real-data/cache-stats/{user_id}")
async def get_cache_statistics(user_id: str):
    """
    获取缓存统计
    """
    try:
        from backend.data_collection.real_data_integration import get_real_data_integration_layer
        integration_layer = get_real_data_integration_layer(user_id)
        
        cache_stats = integration_layer.get_cache_stats()
        
        return {
            "code": 200,
            "message": "Cache statistics retrieved",
            "data": {
                "user_id": user_id,
                "cache_stats": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"获取缓存统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 测试数据生成API ====================

@app.post("/api/test/generate-data")
async def generate_test_data(request_data: Dict[str, Any]):
    """生成测试数据"""
    try:
        user_id = request_data.get("user_id", "test_user")
        days = request_data.get("days", 7)
        
        from backend.data_collection.sensor_data_generator import generate_test_dataset
        
        # 生成测试数据
        test_data = generate_test_dataset(user_id, days)
        
        # 上传测试数据
        for data_point in test_data:
            await upload_multimodal_data(data_point)
        
        return {
            "code": 200,
            "message": f"Generated {len(test_data)} test data points",
            "data": {
                "user_id": user_id,
                "data_points": len(test_data),
                "days": days
            }
        }
    
    except Exception as e:
        print(f"测试数据生成失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 启动事件 ====================
# 注意：启动事件已在文件开头定义，这里不再重复


# ==================== AI对话API - SSE流式输出 ====================

from backend.conversation.conversational_ai import ConversationalAI

# 全局对话系统实例
conversational_ai_system = None

def get_conversational_ai():
    """获取对话系统"""
    global conversational_ai_system
    if conversational_ai_system is None:
        from backend.startup_manager import StartupManager
        # 获取必要的系统组件
        meta_agent = StartupManager.get_system('meta_agent')
        kg = StartupManager.get_system('knowledge_graph')
        evolving_system = StartupManager.get_system('evolving_system')
        multimodal_fusion = StartupManager.get_system('multimodal_fusion')
        
        conversational_ai_system = ConversationalAI(
            meta_agent=meta_agent,
            knowledge_graph=kg,
            evolving_system=evolving_system,
            multimodal_fusion=multimodal_fusion
        )
    return conversational_ai_system


# ==================== LoRA 个性化训练 API ====================

# 全局 LoRA 管理器缓存
lora_trainers = {}
lora_manager = None

def get_lora_manager():
    """获取 LoRA 模型管理器(单例)"""
    global lora_manager
    if lora_manager is None:
        from backend.lora.lora_model_manager import LoRAModelManager
        lora_manager = LoRAModelManager()  # 直接实例化,__new__ 会处理单例
    return lora_manager

def get_lora_trainer(user_id: str):
    """获取用户的LoRA 训练器"""
    if user_id not in lora_trainers:
        from backend.lora.auto_lora_trainer import AutoLoRATrainer
        lora_trainers[user_id] = AutoLoRATrainer(user_id)
    return lora_trainers[user_id]



@app.post("/api/chat")
async def chat(request_data: Dict[str, Any]):
    """
    普通对话接口 - 一次性返回完整回复
    
    请求格式:
    {
        "user_id": "user_001",
        "message": "你好",
        "context": {...}  // 可选
    }
    """
    try:
        user_id = request_data.get("user_id", "default_user")
        message = request_data.get("message", "")
        context = request_data.get("context")
        
        if not message:
            return {
                "code": 400,
                "message": "Message is required",
                "data": None
            }
        
        # 获取对话系统
        chat_system = get_conversational_ai()
        
        # 执行对话
        response = await chat_system.chat(user_id, message, context)
        
        return {
            "code": 200,
            "message": "Chat completed",
            "data": {
                "user_id": user_id,
                "message": message,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        print(f"对话失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 流式聊天 API ====================

from backend.conversation.simple_streaming import router as streaming_router
app.include_router(streaming_router)

print("流式聊天 API 已加载")
print("   - POST /api/chat/stream - 流式聊天")
print("   - POST /api/chat/chat - 完整聊天")
print("   - GET /api/chat/health - 健康检查")


# ==================== 记忆查询 API ====================

@app.get("/api/memory/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """获取用户的记忆统计信息"""
    try:
        from llm.enhanced_memory_retriever import get_enhanced_memory_retriever
        
        retriever = get_enhanced_memory_retriever(user_id)
        stats = retriever.get_memory_statistics()
        
        return {
            "code": 200,
            "message": "Success",
            "data": stats
        }
    except Exception as e:
        print(f"获取记忆统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


@app.get("/api/memory/list/{user_id}")
async def list_memories(user_id: str, memory_type: Optional[str] = None, limit: int = 10):
    """列出用户的记忆"""
    try:
        from llm.enhanced_memory_retriever import get_enhanced_memory_retriever, MemoryType
        
        retriever = get_enhanced_memory_retriever(user_id)
        
        if memory_type:
            # 按类型检查            mem_type = MemoryType(memory_type)
            memories = retriever.retrieve_by_type(mem_type, top_k=limit)
            
            return {
                "code": 200,
                "message": "Success",
                "data": {
                    "memories": [
                        {
                            "id": m.memory_id,
                            "type": m.memory_type.value,
                            "content": m.content,
                            "importance": m.importance,
                            "timestamp": m.timestamp.isoformat(),
                            "access_count": m.access_count
                        }
                        for m in memories
                    ]
                }
            }
        else:
            # 返回所有记忆            all_memories = sorted(retriever.memories, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return {
                "code": 200,
                "message": "Success",
                "data": {
                    "memories": [
                        {
                            "id": m.memory_id,
                            "type": m.memory_type.value,
                            "content": m.content,
                            "importance": m.importance,
                            "timestamp": m.timestamp.isoformat(),
                            "access_count": m.access_count
                        }
                        for m in all_memories
                    ]
                }
            }
    except Exception as e:
        print(f"列出记忆失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== LoRA  性化训练 API ====================

# 全局 LoRA 管理器缓个lora_trainers = {}
lora_manager = None

def get_lora_manager():
    """获取 LoRA 模型管理器(单例)"""
    global lora_manager
    if lora_manager is None:
        from lora.lora_model_manager import LoRAModelManager
        lora_manager = LoRAModelManager()  # 直接实例化,__new__ 会处理单    return lora_manager

def get_lora_trainer(user_id: str):
    """获取用户的LoRA 训练器"""
    if user_id not in lora_trainers:
        from lora.auto_lora_trainer import AutoLoRATrainer
        lora_trainers[user_id] = AutoLoRATrainer(user_id)
    return lora_trainers[user_id]

@app.get("/api/lora/status/{user_id}")
async def get_lora_status(user_id: str):
    """获取用户的LoRA 训练状态"""
    try:
        trainer = get_lora_trainer(user_id)
        manager = get_lora_manager()
        
        # 获取训练状态        status = trainer.status
        
        # 获取模型信息
        has_model = manager.has_lora_model(user_id)
        model_path = manager.get_lora_path(user_id) if has_model else None
        
        # 获取对话数据        conversations = trainer.get_user_conversations()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "user_id": user_id,
                "has_model": has_model,
                "model_path": model_path,
                "model_version": f"v{status['model_version']}" if status['model_version'] > 0 else "未训",
                "last_train_time": status['last_train_time'].isoformat() if status['last_train_time'] else None,
                "total_trainings": status['total_trainings'],
                "current_data_size": len(conversations),
                "min_data_size": trainer.training_config['min_data_size'],
                "is_training": status['is_training'],
                "can_train": len(conversations) >= trainer.training_config['min_data_size'] and not status['is_training']
            }
        }
    except Exception as e:
        print(f"获取 LoRA 状态失 {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/lora/train/{user_id}")
async def trigger_lora_training(user_id: str, background_tasks: BackgroundTasks):
    """手动触发 LoRA 训练"""
    try:
        trainer = get_lora_trainer(user_id)
        
        # 检查是否可以训练
        if trainer.status['is_training']:
            return {
                "code": 400,
                "message": "训练任务已在进行",
                "data": None
            }
        
        conversations = trainer.get_user_conversations()
        if len(conversations) < trainer.training_config['min_data_size']:
            return {
                "code": 400,
                "message": f"数据不足,需要至个{trainer.training_config['min_data_size']} 条对",
                "data": {
                    "current": len(conversations),
                    "required": trainer.training_config['min_data_size']
                }
            }
        
        # 在后台执行训        background_tasks.add_task(trainer.auto_train_workflow)
        
        return {
            "code": 200,
            "message": "训练任务已启",
            "data": {
                "user_id": user_id,
                "data_size": len(conversations),
                "estimated_time": "3-5 分钟"
            }
        }
    except Exception as e:
        print(f"触发 LoRA 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/lora/models")
async def list_lora_models():
    """列出所有用户的 LoRA 模型"""
    try:
        import os
        models_dir = "./models/lora"
        
        if not os.path.exists(models_dir):
            return {
                "code": 200,
                "message": "Success",
                "data": {"models": []}
            }
        
        models = []
        for user_id in os.listdir(models_dir):
            user_dir = os.path.join(models_dir, user_id)
            if os.path.isdir(user_dir):
                # 查找最新版本
                versions = [d for d in os.listdir(user_dir) 
                           if d.startswith('v') and os.path.isdir(os.path.join(user_dir, d))]
                if versions:
                    latest_version = sorted(versions, key=lambda x: int(x[1:]))[-1]
                    final_path = os.path.join(user_dir, latest_version, "final")
                    
                    # 检查final 目录是否存在
                    if os.path.exists(final_path):
                        models.append({
                            "user_id": user_id,
                            "version": latest_version,
                            "path": final_path
                        })
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "models": models,
                "total": len(models)
            }
        }
    except Exception as e:
        print(f"列出 LoRA 模型失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 心理测评系统 API ====================

# 全局心理测评系统
personality_test = None

def get_personality_test():
    """获取心理测评系统(单例)"""
    global personality_test
    if personality_test is None:
        from personality.personality_test import PersonalityTest
        personality_test = PersonalityTest()
    return personality_test

@app.get("/api/personality/questions")
async def get_personality_questions():
    """获取心理测评题目"""
    try:
        test = get_personality_test()
        questions_data = test.get_questions()
        
        return {
            "code": 200,
            "message": "Success",
            "data": questions_data
        }
    except Exception as e:
        print(f"获取测评题目失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/personality/submit")
async def submit_personality_test(request_data: Dict[str, Any]):
    """
    提交心理测评答案
    
    请求个
    {
        "user_id": "user_001",
        "answers": {
            "1": 3,
            "2": 4,
            ...
        }
    }
    """
    try:
        user_id = request_data.get("user_id")
        answers = request_data.get("answers", {})
        
        if not user_id:
            return {
                "code": 400,
                "message": "user_id 不能为空",
                "data": None
            }
        
        if not answers:
            return {
                "code": 400,
                "message": "answers 不能为空",
                "data": None
            }
        
        # 转换答案格式(字符串key转整数)
        answers_int = {int(k): int(v) for k, v in answers.items()}
        
        # 计算性格画像
        test = get_personality_test()
        profile = test.calculate_profile(user_id, answers_int)
        
        # 保存画像
        test.save_profile(profile)
        
        # 返回结果
        return {
            "code": 200,
            "message": "测评完成",
            "data": {
                "profile": profile.to_dict(),
                "summary": profile.get_summary()
            }
        }
    except Exception as e:
        print(f"提交测评失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/personality/profile/{user_id}")
async def get_personality_profile(user_id: str):
    """获取用户的性格画像"""
    try:
        test = get_personality_test()
        profile = test.load_profile(user_id)
        
        if profile is None:
            return {
                "code": 404,
                "message": "未找到该用户的性格画像,请先完成测",
                "data": None
            }
        
        return {
            "code": 200,
            "message": "Success",
            "data": {
                "profile": profile.to_dict(),
                "summary": profile.get_summary()
            }
        }
    except Exception as e:
        print(f"获取性格画像失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 决策模拟系统 API ====================

# 注册增强决策 API（信息收集 + 决策模拟）
from backend.decision.enhanced_decision_api import router as enhanced_decision_router
app.include_router(enhanced_decision_router)

print("增强决策 API 已加载")

# ==================== 智能洞察 API ====================

# 注册智能洞察 API（涌现检测 + 对话分析）
from backend.emergence.insight_api import router as insight_router
app.include_router(insight_router)

print("智能洞察 API 已加载")
print("   - POST /api/v1/insights/process - 处理对话消息")
print("   - POST /api/v1/insights/generate - 生成智能洞察")
print("   - GET /api/v1/insights/dashboard/{user_id} - 获取仪表盘数据")
print("   - GET /api/v1/insights/list/{user_id} - 获取洞察列表")
print("   - GET /api/v1/insights/emotion-trend/{user_id} - 获取情绪趋势")
print("   - GET /api/v1/insights/topic-distribution/{user_id} - 获取话题分布")
print("   - POST /api/decision/enhanced/collect/start - 开始信息收集")
print("   - POST /api/decision/enhanced/collect/continue - 继续信息收集")
print("   - GET /api/decision/enhanced/collect/session/{session_id} - 获取收集会话")
print("   - POST /api/decision/enhanced/simulate/with-collection - 使用收集信息模拟")
print("   - POST /api/decision/enhanced/full-process - 完整决策流程（快速版）")

# 全局平行宇宙模拟器
parallel_simulator = None
# 全局副本存储
dungeons_storage: Dict[str, Dict[str, Any]] = {}

def get_parallel_simulator():
    """获取平行宇宙模拟器(单例)"""
    global parallel_simulator
    if parallel_simulator is None:
        from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator
        parallel_simulator = ParallelUniverseSimulator()
    return parallel_simulator

@app.post("/api/decision/simulate")
async def simulate_decision(request_data: Dict[str, Any]):
    """
    决策模拟 — 通过 SGLang (Qwen3.5-9B + 用户 LoRA) 推理
    
    请求体:
    {
        "user_id": "user_001",
        "question": "大三学生,毕业后应该选择什么?",
        "options": [
            {"title": "考研", "description": "继续深造"},
            {"title": "工作", "description": "直接就业"},
            {"title": "创业", "description": "自主创业"}
        ]
    }
    """
    try:
        user_id = request_data.get("user_id")
        question = request_data.get("question")
        options = request_data.get("options", [])
        
        if not user_id or not question or not options:
            return {
                "code": 400,
                "message": "user_id, question, options 不能为空",
                "data": None
            }
        
        if len(options) < 2:
            return {
                "code": 400,
                "message": "至少需要两个选项",
                "data": None
            }
        
        # 异步执行模拟（SGLang + LoRA）
        simulator = get_parallel_simulator()
        result = await simulator.simulate_decision(
            user_id=user_id,
            question=question,
            options=options,
        )
        
        # 转换为可序列化格式
        response_data = {
            "simulation_id": result.simulation_id,
            "question": result.question,
            "options": [
                {
                    "option_id": opt.option_id,
                    "title": opt.title,
                    "description": opt.description,
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "risk_assessment": opt.risk_assessment if hasattr(opt, 'risk_assessment') else None,
                    "timeline": [
                        {
                            "month": event.month,
                            "event": event.event,
                            "impact": event.impact,
                            "probability": event.probability
                        }
                        for event in opt.timeline
                    ]
                }
                for opt in result.options
            ],
            "recommendation": result.recommendation,
            "created_at": result.created_at
        }
        
        return {
            "code": 200,
            "message": "模拟完成",
            "data": response_data
        }
    except Exception as e:
        print(f"决策模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/decision/create-dungeon")
async def create_dungeon(request_data: Dict[str, Any]):
    """
    创建决策副本
    
    请求格式:
    {
        "user_id": "user_001",
        "title": "毕业后应该选择什么？",
        "description": "大三学生面临的选择",
        "context": "背景信息",
        "urgency": "medium",
        "options": ["考研", "工作", "创业"],
        "use_lora": true
    }
    """
    try:
        user_id = request_data.get("user_id")
        title = request_data.get("title")
        description = request_data.get("description")
        context = request_data.get("context", "")
        urgency = request_data.get("urgency", "medium")
        options = request_data.get("options", [])
        use_lora = request_data.get("use_lora", True)
        
        # 验证输入
        if not user_id or not title or not description:
            return {
                "code": 400,
                "message": "user_id, title, description 不能为空",
                "data": None
            }
        
        if len(options) < 2:
            return {
                "code": 400,
                "message": "至少需要2个选项",
                "data": None
            }
        
        # 生成副本ID
        import time
        dungeon_id = f"dungeon_{user_id}_{int(time.time())}"
        
        # 生成平行宇宙模拟
        option_inputs = [
            {"title": opt, "description": f"选择{opt}的发展路径"}
            for opt in options
        ]
        
        simulator = get_parallel_simulator()
        simulation_result = simulator.simulate_decision(
            user_id=user_id,
            question=title,
            options=option_inputs,
            use_lora=use_lora
        )
        
        # 构建副本数据
        dungeon_data = {
            "dungeon_id": dungeon_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "context": context,
            "urgency": urgency,
            "options": [
                {
                    "option_id": opt.option_id,
                    "title": opt.title,
                    "description": opt.description,
                    "timeline": [
                        {
                            "month": event.month,
                            "event": event.event,
                            "impact": event.impact,
                            "probability": event.probability
                        }
                        for event in opt.timeline
                    ],
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "risk_assessment": opt.risk_assessment if hasattr(opt, 'risk_assessment') else None
                }
                for opt in simulation_result.options
            ],
            "recommendation": simulation_result.recommendation,
            "created_at": datetime.now().isoformat(),
            "lora_trained": use_lora
        }
        
        # 保存副本数据
        dungeons_storage[dungeon_id] = dungeon_data
        
        return {
            "code": 200,
            "message": "副本创建成功",
            "data": {
                "dungeon_id": dungeon_id,
                "user_id": user_id,
                "title": title,
                "options_count": len(options),
                "created_at": dungeon_data["created_at"]
            }
        }
    except Exception as e:
        print(f"创建副本失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/decision/quick-analyze")
async def quick_analyze_decision(request_data: Dict[str, Any]):
    """
    快速分析用户输入，自动提取决策问题和选项
    
    请求格式:
    {
        "user_id": "user_001",
        "user_input": "我不知道毕业后应该考研还是工作"
    }
    """
    try:
        user_id = request_data.get("user_id")
        user_input = request_data.get("user_input", "")
        
        if not user_id or not user_input:
            return {
                "code": 400,
                "message": "user_id和user_input不能为空",
                "data": None
            }
        
        # 使用LLM分析用户输入
        llm_service = get_or_init_llm_service()
        
        analysis_prompt = f"""分析用户的困惑，提取决策问题和可能的选项。

用户输入：{user_input}

请以JSON格式返回：
{{
  "title": "决策问题（简短）",
  "description": "详细描述",
  "options": ["选项1", "选项2", "选项3"]
}}

注意：
1. 至少提供2个选项，最多5个
2. 选项要具体、可行
3. 如果用户没有明确选项，根据常识推荐"""

        messages = [{"role": "user", "content": analysis_prompt}]
        llm_response = llm_service.chat(messages, temperature=0.7)
        
        # 解析LLM响应
        import json
        import re
        
        # 提取JSON
        json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', llm_response, re.DOTALL)
        if json_match:
            analysis_data = json.loads(json_match.group())
        else:
            # 降级方案：使用简单规则
            analysis_data = {
                "title": user_input[:50],
                "description": user_input,
                "options": ["选项A", "选项B", "选项C"]
            }
        
        # 直接创建副本
        title = analysis_data.get("title", user_input[:50])
        description = analysis_data.get("description", user_input)
        options = analysis_data.get("options", ["选项A", "选项B"])
        
        # 生成副本
        import time
        dungeon_id = f"dungeon_{user_id}_{int(time.time())}"
        
        option_inputs = [
            {"title": opt, "description": f"选择{opt}的发展路径"}
            for opt in options
        ]
        
        simulator = get_parallel_simulator()
        simulation_result = simulator.simulate_decision(
            user_id=user_id,
            question=title,
            options=option_inputs,
            use_lora=True
        )
        
        # 构建副本数据
        dungeon_data = {
            "dungeon_id": dungeon_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "context": user_input,
            "urgency": "medium",
            "options": [
                {
                    "option_id": opt.option_id,
                    "title": opt.title,
                    "description": opt.description,
                    "timeline": [
                        {
                            "month": event.month,
                            "event": event.event,
                            "impact": event.impact,
                            "probability": event.probability
                        }
                        for event in opt.timeline
                    ],
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "risk_assessment": opt.risk_assessment if hasattr(opt, 'risk_assessment') else None
                }
                for opt in simulation_result.options
            ],
            "recommendation": simulation_result.recommendation,
            "created_at": datetime.now().isoformat(),
            "lora_trained": True
        }
        
        dungeons_storage[dungeon_id] = dungeon_data
        
        return {
            "code": 200,
            "message": "分析完成",
            "data": {
                "dungeon_id": dungeon_id,
                "title": title,
                "description": description,
                "options": options
            }
        }
        
    except Exception as e:
        print(f"快速分析失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/decision/dungeon/{dungeon_id}")
async def get_dungeon(dungeon_id: str):
    """获取副本详情"""
    try:
        if dungeon_id not in dungeons_storage:
            return {
                "code": 404,
                "message": "副本不存在",
                "data": None
            }
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": dungeons_storage[dungeon_id]
        }
    except Exception as e:
        print(f"获取副本失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/decision/dungeons/{user_id}")
async def list_user_dungeons(user_id: str):
    """获取用户的所有副本"""
    try:
        user_dungeons = [
            {
                "dungeon_id": dungeon_id,
                "title": data["title"],
                "description": data["description"],
                "options_count": len(data["options"]),
                "created_at": data["created_at"],
                "lora_trained": data.get("lora_trained", False)
            }
            for dungeon_id, data in dungeons_storage.items()
            if data["user_id"] == user_id
        ]
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "user_id": user_id,
                "dungeons": user_dungeons,
                "total": len(user_dungeons)
            }
        }
    except Exception as e:
        print(f"获取副本列表失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/decision/result/{simulation_id}")
async def get_simulation_result(simulation_id: str):
    """获取模拟结果"""
    try:
        simulator = get_parallel_simulator()
        result = simulator.load_simulation(simulation_id)
        
        if result is None:
            return {
                "code": 404,
                "message": "未找到该模拟结果",
                "data": None
            }
        
        # 转换为可序列化格式
        response_data = {
            "simulation_id": result.simulation_id,
            "question": result.question,
            "options": [
                {
                    "option_id": opt.option_id,
                    "title": opt.title,
                    "description": opt.description,
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "timeline": [
                        {
                            "month": event.month,
                            "event": event.event,
                            "impact": event.impact,
                            "probability": event.probability
                        }
                        for event in opt.timeline
                    ]
                }
                for opt in result.options
            ],
            "recommendation": result.recommendation,
            "created_at": result.created_at
        }
        
        return {
            "code": 200,
            "message": "Success",
            "data": response_data
        }
    except Exception as e:
        print(f"获取模拟结果失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }


# ==================== 决策反馈API ====================

# 全局决策反馈循环实例
decision_feedback_loop = None

def get_decision_feedback_loop():
    """获取决策反馈循环实例（单例）"""
    global decision_feedback_loop
    if decision_feedback_loop is None:
        from backend.decision.decision_feedback_loop import DecisionFeedbackLoop
        decision_feedback_loop = DecisionFeedbackLoop()
    return decision_feedback_loop

@app.post("/api/decision/record")
async def record_user_decision(request_data: Dict[str, Any]):
    """
    记录用户的决策选择
    
    请求体:
    {
        "user_id": "user_001",
        "simulation_id": "sim_xxx",
        "question": "毕业后应该选择什么？",
        "predicted_option": "直接工作",
        "predicted_score": 82.3,
        "actual_option": "直接工作"
    }
    """
    try:
        user_id = request_data.get("user_id")
        simulation_id = request_data.get("simulation_id")
        question = request_data.get("question")
        predicted_option = request_data.get("predicted_option")
        predicted_score = request_data.get("predicted_score", 0.0)
        actual_option = request_data.get("actual_option")
        
        if not all([user_id, simulation_id, question, predicted_option, actual_option]):
            return {
                "code": 400,
                "message": "缺少必要参数",
                "data": None
            }
        
        loop = get_decision_feedback_loop()
        feedback_id = loop.record_decision(
            user_id=user_id,
            simulation_id=simulation_id,
            question=question,
            predicted_option=predicted_option,
            predicted_score=predicted_score,
            actual_option=actual_option
        )
        
        return {
            "code": 200,
            "message": "决策已记录",
            "data": {"feedback_id": feedback_id}
        }
    except Exception as e:
        print(f"记录决策失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/decision/feedback")
async def submit_decision_feedback(request_data: Dict[str, Any]):
    """
    提交决策反馈（3个月后）
    
    请求体:
    {
        "feedback_id": "feedback_xxx",
        "actual_satisfaction": 8,
        "feedback_text": "工作很顺利，选择是对的"
    }
    """
    try:
        feedback_id = request_data.get("feedback_id")
        actual_satisfaction = request_data.get("actual_satisfaction")
        feedback_text = request_data.get("feedback_text")
        
        if not feedback_id or actual_satisfaction is None:
            return {
                "code": 400,
                "message": "缺少必要参数",
                "data": None
            }
        
        if not (1 <= actual_satisfaction <= 10):
            return {
                "code": 400,
                "message": "满意度必须在1-10之间",
                "data": None
            }
        
        loop = get_decision_feedback_loop()
        success = loop.submit_feedback(
            feedback_id=feedback_id,
            actual_satisfaction=actual_satisfaction,
            feedback_text=feedback_text
        )
        
        if success:
            return {
                "code": 200,
                "message": "反馈已提交",
                "data": None
            }
        else:
            return {
                "code": 404,
                "message": "反馈不存在",
                "data": None
            }
    except Exception as e:
        print(f"提交反馈失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/decision/pending-feedbacks/{user_id}")
async def get_pending_feedbacks(user_id: str, days: int = 90):
    """
    获取待反馈的决策列表
    
    参数:
    - user_id: 用户ID
    - days: 天数阈值（默认90天）
    """
    try:
        loop = get_decision_feedback_loop()
        pending = loop.get_pending_feedbacks(user_id, days_threshold=days)
        
        data = [
            {
                "feedback_id": f.feedback_id,
                "question": f.question,
                "predicted_option": f.predicted_option,
                "actual_option": f.actual_option,
                "feedback_time": f.feedback_time
            }
            for f in pending
        ]
        
        return {
            "code": 200,
            "message": "Success",
            "data": data
        }
    except Exception as e:
        print(f"获取待反馈列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/decision/accuracy/{user_id}")
async def get_decision_accuracy(user_id: str):
    """
    获取AI决策准确率统计
    
    参数:
    - user_id: 用户ID
    """
    try:
        loop = get_decision_feedback_loop()
        stats = loop.calculate_accuracy(user_id)
        
        return {
            "code": 200,
            "message": "Success",
            "data": stats
        }
    except Exception as e:
        print(f"获取准确率失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

# ==================== LoRA状态API ====================

# 全局LoRA调度器
lora_scheduler = None

def get_lora_scheduler():
    """获取LoRA调度器实例（单例）"""
    global lora_scheduler
    if lora_scheduler is None:
        from backend.lora.lora_scheduler import get_scheduler
        lora_scheduler = get_scheduler()
    return lora_scheduler

@app.get("/api/lora/status/{user_id}")
async def get_lora_status(user_id: str):
    """
    获取用户的LoRA模型状态
    
    参数:
    - user_id: 用户ID
    """
    try:
        from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
        
        analyzer = LoRADecisionAnalyzer()
        status = analyzer.get_lora_status(user_id)
        
        return {
            "code": 200,
            "message": "Success",
            "data": status
        }
    except Exception as e:
        print(f"获取LoRA状态失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/lora/train/{user_id}")
async def trigger_lora_training(user_id: str, priority: str = "normal"):
    """
    手动触发LoRA训练
    
    参数:
    - user_id: 用户ID
    - priority: 优先级 (normal/high)
    """
    try:
        scheduler = get_lora_scheduler()
        scheduler.add_training_task(user_id, priority)
        
        return {
            "code": 200,
            "message": "训练任务已添加到队列",
            "data": {"user_id": user_id, "priority": priority}
        }
    except Exception as e:
        print(f"触发训练失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/lora/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    try:
        scheduler = get_lora_scheduler()
        status = scheduler.get_status()
        
        return {
            "code": 200,
            "message": "Success",
            "data": status
        }
    except Exception as e:
        print(f"获取调度器状态失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/lora/scheduler/start")
async def start_scheduler():
    """启动调度器"""
    try:
        scheduler = get_lora_scheduler()
        scheduler.start()
        
        return {
            "code": 200,
            "message": "调度器已启动",
            "data": None
        }
    except Exception as e:
        print(f"启动调度器失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/lora/scheduler/stop")
async def stop_scheduler():
    """停止调度器"""
    try:
        scheduler = get_lora_scheduler()
        scheduler.stop()
        
        return {
            "code": 200,
            "message": "调度器已停止",
            "data": None
        }
    except Exception as e:
        print(f"停止调度器失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

# ==================== 系统管理API ====================

@app.get("/api/system/health")
async def system_health_check():
    """系统健康检查"""
    try:
        from backend.utils.health_checker import HealthChecker
        
        checker = HealthChecker()
        results = checker.check_all()
        
        return {
            "code": 200,
            "message": "Health check completed",
            "data": results
        }
    except Exception as e:
        print(f"健康检查失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/system/performance")
async def get_performance_stats():
    """获取性能统计"""
    try:
        from backend.utils.performance_monitor import get_monitor
        
        monitor = get_monitor()
        stats = monitor.get_statistics()
        
        return {
            "code": 200,
            "message": "Success",
            "data": stats
        }
    except Exception as e:
        print(f"获取性能统计失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.post("/api/system/backup")
async def create_system_backup():
    """创建系统备份"""
    try:
        from backend.utils.backup_manager import BackupManager
        
        manager = BackupManager()
        backup_path = manager.auto_backup()
        
        return {
            "code": 200,
            "message": "备份创建成功",
            "data": {"backup_path": backup_path}
        }
    except Exception as e:
        print(f"创建备份失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

@app.get("/api/system/backups")
async def list_system_backups():
    """列出所有备份"""
    try:
        from backend.utils.backup_manager import BackupManager
        
        manager = BackupManager()
        backups = manager.list_backups()
        
        return {
            "code": 200,
            "message": "Success",
            "data": {"backups": backups}
        }
    except Exception as e:
        print(f"列出备份失败: {e}")
        return {
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }

# ==================== 根路径====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "LifeSwarm API",
        "version": "1.0.0",
        "description": "智能生活助手系统",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )


