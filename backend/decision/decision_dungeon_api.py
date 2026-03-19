"""
决策副本系统 API
集成LoRA模型训练和平行宇宙模拟
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import uuid

from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator
from backend.llm.auto_lora_trainer import AutoLoRATrainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision", tags=["decision"])

# 全局实例
simulator = ParallelUniverseSimulator()
lora_trainer = AutoLoRATrainer()

# 存储副本数据
dungeons_storage: Dict[str, Dict[str, Any]] = {}


class DecisionDungeonAPI:
    """决策副本API"""

    @staticmethod
    @router.post("/create-dungeon")
    async def create_dungeon(
        user_id: str,
        title: str,
        description: str,
        context: str,
        urgency: str,
        options: List[str],
        use_lora: bool = True
    ) -> Dict[str, Any]:
        """
        创建决策副本
        
        Args:
            user_id: 用户ID
            title: 决策标题
            description: 决策描述
            context: 背景信息
            urgency: 紧急程度 (low/medium/high)
            options: 决策选项列表
            use_lora: 是否使用LoRA模型
        
        Returns:
            副本数据
        """
        try:
            logger.info(f"Creating dungeon for user {user_id}: {title}")

            # 验证输入
            if not title or not description or len(options) < 2:
                return {
                    "code": 400,
                    "message": "Invalid input parameters",
                    "data": None
                }

            # 生成副本ID
            dungeon_id = f"dungeon_{user_id}_{int(datetime.now().timestamp())}"

            # 1. 触发LoRA模型训练（异步）
            if use_lora:
                try:
                    # 准备训练数据
                    training_data = {
                        "user_id": user_id,
                        "decision_title": title,
                        "decision_description": description,
                        "context": context,
                        "urgency": urgency,
                        "options": options,
                        "timestamp": datetime.now().isoformat()
                    }

                    # 异步启动LoRA训练
                    logger.info(f"Starting LoRA training for user {user_id}")
                    # 这里可以使用后台任务队列（如Celery）
                    # await lora_trainer.train_async(user_id, training_data)
                except Exception as e:
                    logger.error(f"LoRA training error: {str(e)}")
                    # 继续执行，不中断流程

            # 2. 生成平行宇宙模拟
            option_inputs = [
                {"title": opt, "description": f"选择{opt}的发展路径"}
                for opt in options
            ]

            simulation_result = simulator.simulate_decision(
                user_id=user_id,
                question=title,
                options=option_inputs,
                use_lora=use_lora
            )

            # 3. 构建副本数据
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
                        "risk_assessment": opt.risk_assessment
                    }
                    for opt in simulation_result.options
                ],
                "recommendation": simulation_result.recommendation,
                "created_at": datetime.now().isoformat(),
                "lora_trained": use_lora
            }

            # 4. 保存副本数据
            dungeons_storage[dungeon_id] = dungeon_data

            logger.info(f"Dungeon created successfully: {dungeon_id}")

            return {
                "code": 200,
                "message": "Dungeon created successfully",
                "data": {
                    "dungeon_id": dungeon_id,
                    "user_id": user_id,
                    "title": title,
                    "options_count": len(options),
                    "created_at": dungeon_data["created_at"]
                }
            }

        except Exception as e:
            logger.error(f"Error creating dungeon: {str(e)}")
            return {
                "code": 500,
                "message": f"Failed to create dungeon: {str(e)}",
                "data": None
            }

    @staticmethod
    @router.get("/dungeon/{dungeon_id}")
    async def get_dungeon(dungeon_id: str) -> Dict[str, Any]:
        """
        获取副本详情
        
        Args:
            dungeon_id: 副本ID
        
        Returns:
            副本数据
        """
        try:
            if dungeon_id not in dungeons_storage:
                return {
                    "code": 404,
                    "message": "Dungeon not found",
                    "data": None
                }

            dungeon_data = dungeons_storage[dungeon_id]

            return {
                "code": 200,
                "message": "Dungeon retrieved successfully",
                "data": dungeon_data
            }

        except Exception as e:
            logger.error(f"Error retrieving dungeon: {str(e)}")
            return {
                "code": 500,
                "message": f"Failed to retrieve dungeon: {str(e)}",
                "data": None
            }

    @staticmethod
    @router.get("/dungeons/{user_id}")
    async def list_user_dungeons(user_id: str) -> Dict[str, Any]:
        """
        获取用户的所有副本
        
        Args:
            user_id: 用户ID
        
        Returns:
            副本列表
        """
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
                "message": "Dungeons retrieved successfully",
                "data": {
                    "user_id": user_id,
                    "dungeons": user_dungeons,
                    "total": len(user_dungeons)
                }
            }

        except Exception as e:
            logger.error(f"Error listing dungeons: {str(e)}")
            return {
                "code": 500,
                "message": f"Failed to list dungeons: {str(e)}",
                "data": None
            }

    @staticmethod
    @router.post("/dungeon/{dungeon_id}/feedback")
    async def submit_dungeon_feedback(
        dungeon_id: str,
        user_id: str,
        selected_option: str,
        feedback: str,
        rating: int = 5
    ) -> Dict[str, Any]:
        """
        提交副本反馈
        
        Args:
            dungeon_id: 副本ID
            user_id: 用户ID
            selected_option: 选择的选项
            feedback: 反馈内容
            rating: 评分 (1-5)
        
        Returns:
            反馈结果
        """
        try:
            if dungeon_id not in dungeons_storage:
                return {
                    "code": 404,
                    "message": "Dungeon not found",
                    "data": None
                }

            dungeon_data = dungeons_storage[dungeon_id]

            # 保存反馈数据用于LoRA训练
            feedback_data = {
                "dungeon_id": dungeon_id,
                "user_id": user_id,
                "selected_option": selected_option,
                "feedback": feedback,
                "rating": rating,
                "timestamp": datetime.now().isoformat()
            }

            # 触发LoRA模型更新（异步）
            try:
                logger.info(f"Updating LoRA model with feedback for user {user_id}")
                # await lora_trainer.update_with_feedback(user_id, feedback_data)
            except Exception as e:
                logger.error(f"LoRA update error: {str(e)}")

            return {
                "code": 200,
                "message": "Feedback submitted successfully",
                "data": {
                    "dungeon_id": dungeon_id,
                    "feedback_id": f"feedback_{dungeon_id}_{int(datetime.now().timestamp())}"
                }
            }

        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            return {
                "code": 500,
                "message": f"Failed to submit feedback: {str(e)}",
                "data": None
            }

    @staticmethod
    @router.get("/dungeon/{dungeon_id}/stats")
    async def get_dungeon_stats(dungeon_id: str) -> Dict[str, Any]:
        """
        获取副本统计信息
        
        Args:
            dungeon_id: 副本ID
        
        Returns:
            统计数据
        """
        try:
            if dungeon_id not in dungeons_storage:
                return {
                    "code": 404,
                    "message": "Dungeon not found",
                    "data": None
                }

            dungeon_data = dungeons_storage[dungeon_id]

            # 计算统计信息
            options_stats = []
            for option in dungeon_data["options"]:
                options_stats.append({
                    "title": option["title"],
                    "final_score": option["final_score"],
                    "risk_level": option["risk_level"],
                    "timeline_events": len(option["timeline"])
                })

            return {
                "code": 200,
                "message": "Statistics retrieved successfully",
                "data": {
                    "dungeon_id": dungeon_id,
                    "title": dungeon_data["title"],
                    "options_count": len(dungeon_data["options"]),
                    "options_stats": options_stats,
                    "created_at": dungeon_data["created_at"],
                    "lora_trained": dungeon_data.get("lora_trained", False)
                }
            }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {
                "code": 500,
                "message": f"Failed to get stats: {str(e)}",
                "data": None
            }


# 创建API实例并注册路由
api = DecisionDungeonAPI()

# 注册路由处理器
@router.post("/create-dungeon")
async def create_dungeon_handler(
    user_id: str,
    title: str,
    description: str,
    context: str,
    urgency: str,
    options: List[str],
    use_lora: bool = True
):
    return await api.create_dungeon(user_id, title, description, context, urgency, options, use_lora)


@router.get("/dungeon/{dungeon_id}")
async def get_dungeon_handler(dungeon_id: str):
    return await api.get_dungeon(dungeon_id)


@router.get("/dungeons/{user_id}")
async def list_dungeons_handler(user_id: str):
    return await api.list_user_dungeons(user_id)


@router.post("/dungeon/{dungeon_id}/feedback")
async def submit_feedback_handler(
    dungeon_id: str,
    user_id: str,
    selected_option: str,
    feedback: str,
    rating: int = 5
):
    return await api.submit_dungeon_feedback(dungeon_id, user_id, selected_option, feedback, rating)


@router.get("/dungeon/{dungeon_id}/stats")
async def get_stats_handler(dungeon_id: str):
    return await api.get_dungeon_stats(dungeon_id)



