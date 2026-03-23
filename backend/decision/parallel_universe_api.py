"""
平行宇宙模拟 API
提供决策模拟的 REST 接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import json

from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision", tags=["decision"])

# 全局模拟器实例
simulator = ParallelUniverseSimulator()


class DecisionOptionInput:
    """决策选项输入"""
    def __init__(self, title: str, description: str):
        self.title = title
        self.description = description


@router.post("/simulate")
async def simulate_decision(
    user_id: str,
    question: str,
    options: List[Dict[str, str]],
    use_lora: bool = True
) -> Dict[str, Any]:
    """
    模拟决策的平行宇宙
    
    Args:
        user_id: 用户ID
        question: 决策问题
        options: 选项列表 [{"title": "选项A", "description": "描述"}]
        use_lora: 是否使用LoRA模型增强
    
    Returns:
        模拟结果
    """
    try:
        logger.info(f"Starting simulation for user {user_id}: {question}")
        
        # 验证输入
        if not user_id or not question or not options:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        if len(options) < 2:
            raise HTTPException(status_code=400, detail="At least 2 options required")
        
        if len(options) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 options allowed")
        
        # 执行模拟
        result = simulator.simulate_decision(
            user_id=user_id,
            question=question,
            options=options,
            use_lora=use_lora
        )
        
        # 转换为可序列化格式
        response_data = {
            "code": 200,
            "message": "Simulation completed successfully",
            "data": {
                "simulation_id": result.simulation_id,
                "user_id": result.user_id,
                "question": result.question,
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
                    for opt in result.options
                ],
                "recommendation": result.recommendation,
                "created_at": result.created_at
            }
        }
        
        logger.info(f"Simulation completed for user {user_id}")
        return response_data
        
    except HTTPException as e:
        logger.error(f"HTTP error in simulation: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/simulate/{simulation_id}")
async def get_simulation_result(simulation_id: str) -> Dict[str, Any]:
    """
    获取已保存的模拟结果
    
    Args:
        simulation_id: 模拟ID
    
    Returns:
        模拟结果
    """
    try:
        result = simulator.load_simulation(simulation_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        response_data = {
            "code": 200,
            "message": "Simulation retrieved successfully",
            "data": {
                "simulation_id": result.simulation_id,
                "user_id": result.user_id,
                "question": result.question,
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
                        "risk_level": opt.risk_level
                    }
                    for opt in result.options
                ],
                "recommendation": result.recommendation,
                "created_at": result.created_at
            }
        }
        
        return response_data
        
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error retrieving simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation: {str(e)}")




