"""
平行人生API - 塔罗牌决策游戏
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.parallel_life.tarot_game import TarotGameEngine
from backend.parallel_life.decision_logic_analyzer import DecisionLogicAnalyzer


router = APIRouter(prefix="/api/v5/parallel-life", tags=["parallel-life"])


class DrawCardRequest(BaseModel):
    """抽牌请求"""
    user_id: str
    drawn_cards: Optional[List[str]] = None


class SubmitChoiceRequest(BaseModel):
    """提交选择请求"""
    user_id: str
    card: str
    card_key: str
    dimension: str
    dimension_key: str
    scenario: str
    choice: str
    tendency: str


# 全局游戏引擎
game_engine = TarotGameEngine()


@router.post("/draw-card")
async def draw_card(request: DrawCardRequest):
    """
    抽取塔罗牌
    
    Returns:
        {
            'success': true,
            'data': {
                'card': 牌名,
                'dimension': 决策维度,
                'scenario': 情景描述,
                'options': 选项列表
            }
        }
    """
    try:
        card_data = game_engine.draw_card(
            user_id=request.user_id,
            drawn_cards=request.drawn_cards
        )
        
        return {
            'success': True,
            'data': card_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-choice")
async def submit_choice(request: SubmitChoiceRequest):
    """
    提交用户选择
    
    Returns:
        {
            'success': true,
            'data': {
                'recorded': true,
                'analysis': 分析结果
            }
        }
    """
    try:
        # 分析选择
        analysis = game_engine.analyze_choice(
            card_key=request.card_key,
            dimension_key=request.dimension_key,
            choice=request.choice,
            tendency=request.tendency
        )
        
        # 记录到RAG和数据库
        analyzer = DecisionLogicAnalyzer(request.user_id)
        analyzer.record_choice(
            card=request.card,
            dimension=request.dimension,
            scenario=request.scenario,
            choice=request.choice,
            tendency_value=analysis['tendency_value']
        )
        
        return {
            'success': True,
            'data': {
                'recorded': True,
                'analysis': analysis
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision-profile/{user_id}")
async def get_decision_profile(user_id: str):
    """
    获取用户的决策画像
    
    Returns:
        {
            'success': true,
            'data': {
                'dimensions': 各维度倾向,
                'patterns': 决策模式,
                'confidence': 置信度
            }
        }
    """
    try:
        analyzer = DecisionLogicAnalyzer(user_id)
        profile = analyzer.get_decision_profile()
        
        return {
            'success': True,
            'data': profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game-stats/{user_id}")
async def get_game_stats(user_id: str):
    """
    获取游戏统计
    
    Returns:
        {
            'success': true,
            'data': {
                'total_cards_drawn': 抽牌总数,
                'choices_made': 选择总数,
                'profile_confidence': 画像置信度
            }
        }
    """
    try:
        analyzer = DecisionLogicAnalyzer(user_id)
        profile = analyzer.get_decision_profile()
        
        return {
            'success': True,
            'data': {
                'total_cards_drawn': profile['total_choices'],
                'choices_made': profile['total_choices'],
                'profile_confidence': profile['confidence'],
                'dimensions_analyzed': len(profile['dimensions'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
