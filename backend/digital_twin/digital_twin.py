"""
数字孪生系统
实时模拟用户状态和预测未来趋势
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import math
import random


class SimulationScenario(Enum):
    """模拟场景"""
    BASELINE = "baseline"  # 基线场景
    OPTIMISTIC = "optimistic"  # 乐观场景
    PESSIMISTIC = "pessimistic"  # 悲观场景
    INTERVENTION = "intervention"  # 干预场景


class DigitalTwin:
    """数字孪生"""
    
    def __init__(self, user_id: str, initial_state: Dict[str, float]):
        """
        初始化数字孪生
        
        Args:
            user_id: 用户ID
            initial_state: 初始状态
        """
        self.user_id = user_id
        self.current_state = initial_state.copy()
        self.state_history: List[Dict[str, Any]] = []
        
        # 状态转移模型
        self.state_transition_model = self._initialize_state_transition_model()
        
        # 模拟参数
        self.simulation_steps = 0
        self.simulation_history: List[Dict[str, Any]] = []
    
    def _initialize_state_transition_model(self) -> Dict[str, Any]:
        """初始化状态转移模型"""
        return {
            "sleep_hours": {
                "base_change": -0.1,  # 每天基础变化
                "factors": {
                    "stress_level": -0.05,  # 压力每增加1，睡眠减少0.05
                    "exercise_minutes": 0.02,  # 运动每增加1分钟，睡眠增加0.02
                    "mood": 0.03  # 心情每增加1，睡眠增加0.03
                },
                "bounds": (4, 10)  # 最小和最大值
            },
            "stress_level": {
                "base_change": 0.05,
                "factors": {
                    "sleep_hours": -0.1,
                    "exercise_minutes": -0.02,
                    "social_hours": -0.03,
                    "meditation": -0.05
                },
                "bounds": (0, 10)
            },
            "mood": {
                "base_change": 0.02,
                "factors": {
                    "sleep_hours": 0.1,
                    "exercise_minutes": 0.05,
                    "social_hours": 0.08,
                    "stress_level": -0.15
                },
                "bounds": (0, 10)
            },
            "health_score": {
                "base_change": 0.1,
                "factors": {
                    "sleep_hours": 0.5,
                    "exercise_minutes": 0.3,
                    "stress_level": -0.2,
                    "mood": 0.1
                },
                "bounds": (0, 100)
            },
            "exercise_minutes": {
                "base_change": -2,  # 每天基础减少
                "factors": {
                    "mood": 0.5,
                    "health_score": 0.1
                },
                "bounds": (0, 180)
            }
        }
    
    def simulate_step(self, scenario: SimulationScenario = SimulationScenario.BASELINE,
                     interventions: Dict[str, float] = None) -> Dict[str, float]:
        """
        模拟一步（一天）
        
        Args:
            scenario: 模拟场景
            interventions: 干预措施
        
        Returns:
            新的状态
        """
        new_state = self.current_state.copy()
        
        # 应用状态转移模型
        for metric, model in self.state_transition_model.items():
            if metric in new_state:
                # 计算基础变化
                change = model["base_change"]
                
                # 应用因子
                for factor, factor_weight in model["factors"].items():
                    if factor in self.current_state:
                        change += factor_weight * self.current_state[factor]
                
                # 根据场景调整
                if scenario == SimulationScenario.OPTIMISTIC:
                    change *= 1.5
                elif scenario == SimulationScenario.PESSIMISTIC:
                    change *= 0.5
                
                # 应用干预
                if interventions and metric in interventions:
                    change += interventions[metric]
                
                # 更新状态
                new_value = self.current_state[metric] + change
                
                # 应用边界
                min_val, max_val = model["bounds"]
                new_state[metric] = max(min_val, min(max_val, new_value))
        
        # 添加随机波动
        for metric in new_state:
            if metric not in self.state_transition_model:
                # 对于未定义的指标，添加小的随机波动
                new_state[metric] += random.gauss(0, 0.5)
        
        # 更新当前状态
        self.current_state = new_state
        self.simulation_steps += 1
        
        # 记录历史
        self.state_history.append({
            "step": self.simulation_steps,
            "state": new_state.copy(),
            "timestamp": datetime.now().isoformat()
        })
        
        return new_state
    
    def simulate_trajectory(self, days: int = 30, scenario: SimulationScenario = SimulationScenario.BASELINE,
                           interventions: Dict[str, float] = None) -> List[Dict[str, float]]:
        """
        模拟轨迹
        
        Args:
            days: 模拟天数
            scenario: 模拟场景
            interventions: 干预措施
        
        Returns:
            轨迹列表
        """
        trajectory = []
        
        for _ in range(days):
            state = self.simulate_step(scenario, interventions)
            trajectory.append(state.copy())
        
        return trajectory
    
    def predict_future_state(self, days: int = 7) -> Dict[str, Any]:
        """
        预测未来状态
        
        Args:
            days: 预测天数
        
        Returns:
            预测结果
        """
        # 保存当前状态
        saved_state = self.current_state.copy()
        saved_history = self.state_history.copy()
        saved_steps = self.simulation_steps
        
        # 运行三个场景的模拟
        scenarios = [
            SimulationScenario.PESSIMISTIC,
            SimulationScenario.BASELINE,
            SimulationScenario.OPTIMISTIC
        ]
        
        predictions = {}
        
        for scenario in scenarios:
            # 重置状态
            self.current_state = saved_state.copy()
            self.state_history = []
            self.simulation_steps = 0
            
            # 模拟
            trajectory = self.simulate_trajectory(days, scenario)
            
            # 计算统计
            predictions[scenario.value] = {
                "trajectory": trajectory,
                "final_state": trajectory[-1] if trajectory else {},
                "average_state": self._calculate_average_state(trajectory),
                "trend": self._calculate_trend(trajectory)
            }
        
        # 恢复状态
        self.current_state = saved_state
        self.state_history = saved_history
        self.simulation_steps = saved_steps
        
        return {
            "prediction_days": days,
            "scenarios": predictions,
            "recommended_scenario": self._recommend_scenario(predictions),
            "timestamp": datetime.now().isoformat()
        }
    
    def simulate_intervention(self, intervention: Dict[str, float], days: int = 7) -> Dict[str, Any]:
        """
        模拟干预效果
        
        Args:
            intervention: 干预措施
            days: 模拟天数
        
        Returns:
            干预效果
        """
        # 保存当前状态
        saved_state = self.current_state.copy()
        saved_history = self.state_history.copy()
        saved_steps = self.simulation_steps
        
        # 模拟无干预情况
        self.current_state = saved_state.copy()
        self.state_history = []
        self.simulation_steps = 0
        baseline_trajectory = self.simulate_trajectory(days, SimulationScenario.BASELINE)
        
        # 模拟有干预情况
        self.current_state = saved_state.copy()
        self.state_history = []
        self.simulation_steps = 0
        intervention_trajectory = self.simulate_trajectory(days, SimulationScenario.BASELINE, intervention)
        
        # 计算干预效果
        effect = {}
        for metric in baseline_trajectory[-1]:
            baseline_final = baseline_trajectory[-1][metric]
            intervention_final = intervention_trajectory[-1][metric]
            effect[metric] = intervention_final - baseline_final
        
        # 恢复状态
        self.current_state = saved_state
        self.state_history = saved_history
        self.simulation_steps = saved_steps
        
        return {
            "intervention": intervention,
            "days": days,
            "baseline_trajectory": baseline_trajectory,
            "intervention_trajectory": intervention_trajectory,
            "effect": effect,
            "total_impact": sum(abs(v) for v in effect.values()),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_average_state(self, trajectory: List[Dict[str, float]]) -> Dict[str, float]:
        """计算平均状态"""
        if not trajectory:
            return {}
        
        average = {}
        for metric in trajectory[0]:
            values = [state[metric] for state in trajectory]
            average[metric] = sum(values) / len(values)
        
        return average
    
    def _calculate_trend(self, trajectory: List[Dict[str, float]]) -> Dict[str, str]:
        """计算趋势"""
        if len(trajectory) < 2:
            return {}
        
        trend = {}
        for metric in trajectory[0]:
            first_value = trajectory[0][metric]
            last_value = trajectory[-1][metric]
            
            if last_value > first_value * 1.05:
                trend[metric] = "increasing"
            elif last_value < first_value * 0.95:
                trend[metric] = "decreasing"
            else:
                trend[metric] = "stable"
        
        return trend
    
    def _recommend_scenario(self, predictions: Dict[str, Any]) -> str:
        """推荐场景"""
        # 计算每个场景的健康分数
        scores = {}
        
        for scenario, data in predictions.items():
            final_state = data["final_state"]
            
            # 计算综合健康分数
            score = 0
            if "health_score" in final_state:
                score += final_state["health_score"]
            if "mood" in final_state:
                score += final_state["mood"] * 10
            if "stress_level" in final_state:
                score -= final_state["stress_level"] * 5
            
            scores[scenario] = score
        
        # 返回最高分的场景
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def export_twin_state(self) -> Dict[str, Any]:
        """导出孪生状态"""
        return {
            "user_id": self.user_id,
            "current_state": self.current_state,
            "simulation_steps": self.simulation_steps,
            "state_history": self.state_history[-30:],  # 最近30步
            "exported_at": datetime.now().isoformat()
        }


class DigitalTwinManager:
    """数字孪生管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.twins: Dict[str, DigitalTwin] = {}
    
    def create_twin(self, user_id: str, initial_state: Dict[str, float]) -> DigitalTwin:
        """创建数字孪生"""
        twin = DigitalTwin(user_id, initial_state)
        self.twins[user_id] = twin
        return twin
    
    def get_twin(self, user_id: str) -> Optional[DigitalTwin]:
        """获取数字孪生"""
        return self.twins.get(user_id)
    
    def get_or_create_twin(self, user_id: str, initial_state: Dict[str, float]) -> DigitalTwin:
        """获取或创建数字孪生"""
        if user_id not in self.twins:
            self.create_twin(user_id, initial_state)
        return self.twins[user_id]


# 全局管理器
_twin_manager = DigitalTwinManager()


def get_digital_twin(user_id: str, initial_state: Dict[str, float] = None) -> DigitalTwin:
    """获取或创建数字孪生"""
    if initial_state is None:
        initial_state = {
            "sleep_hours": 7,
            "stress_level": 5,
            "mood": 7,
            "health_score": 75,
            "exercise_minutes": 30
        }
    
    return _twin_manager.get_or_create_twin(user_id, initial_state)
