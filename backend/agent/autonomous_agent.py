"""
自主AI代理
Autonomous AI Agent - 实现心跳机制和主动服务
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AutonomousAgent:
    """
    自主AI代理
    类似OpenClaw的Agent Runtime + Heartbeat
    """
    
    def __init__(self, digital_twin, prediction_engine, decision_engine):
        self.twin = digital_twin
        self.predictor = prediction_engine
        self.decider = decision_engine
        
        # 运行状态
        self.is_running = False
        self.heartbeat_interval = 1800  # 30分钟（秒）
        self.last_heartbeat = None
        
        # 事件队列
        self.event_queue = asyncio.Queue()
        
        # 统计信息
        self.stats = {
            'heartbeats': 0,
            'predictions': 0,
            'actions': 0,
            'alerts': 0
        }
    
    async def start(self):
        """启动自主运行"""
        if self.is_running:
            logger.warning("Agent already running")
            return
        
        self.is_running = True
        logger.info(f"[Agent] 启动自主运行 - 心跳间隔: {self.heartbeat_interval}秒")
        
        # 启动心跳循环
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 启动事件监听
        event_task = asyncio.create_task(self._event_listener())
        
        # 等待任务完成（或被取消）
        try:
            await asyncio.gather(heartbeat_task, event_task)
        except asyncio.CancelledError:
            logger.info("[Agent] 任务被取消")
    
    async def stop(self):
        """停止自主运行"""
        self.is_running = False
        logger.info("[Agent] 停止自主运行")
    
    async def _heartbeat_loop(self):
        """
        心跳循环（类似OpenClaw的Heartbeat）
        定期主动检查和预测
        """
        while self.is_running:
            try:
                logger.info(f"\n[心跳] 第 {self.stats['heartbeats'] + 1} 次心跳")
                self.last_heartbeat = datetime.now()
                
                # 1. 收集最新数据（实际应该从传感器获取）
                # 这里简化为使用当前状态
                
                # 2. 运行预测
                predictions = await self._run_prediction()
                self.stats['predictions'] += 1
                
                # 3. 决策
                actions = await self._decide_actions(predictions)
                
                # 4. 执行
                for action in actions:
                    await self._execute_action(action)
                    self.stats['actions'] += 1
                
                self.stats['heartbeats'] += 1
                
                # 5. 等待下一个心跳
                logger.info(f"[心跳] 完成，等待 {self.heartbeat_interval} 秒")
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"[心跳] 错误: {e}")
                await asyncio.sleep(60)  # 错误后等待1分钟
    
    async def _event_listener(self):
        """
        事件监听器
        实时响应重要事件
        """
        while self.is_running:
            try:
                # 等待事件（带超时）
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(), 
                        timeout=10.0
                    )
                    await self._handle_event(event)
                except asyncio.TimeoutError:
                    # 超时，继续等待
                    continue
                    
            except Exception as e:
                logger.error(f"[事件监听] 错误: {e}")
                await asyncio.sleep(1)
    
    async def _run_prediction(self) -> Dict:
        """运行预测"""
        try:
            predictions = self.predictor.predict_future(
                time_horizon='1_day'
            )
            return predictions
        except Exception as e:
            logger.error(f"[预测] 失败: {e}")
            return {'predictions': {}, 'emergent_patterns': []}
    
    async def _decide_actions(self, predictions: Dict) -> List[Dict]:
        """基于预测决策行动"""
        actions = []
        
        # 健康预测
        for pred in predictions.get('predictions', {}).get('health', []):
            if pred.get('confidence', 0) > 0.7:
                actions.append({
                    'type': 'health_alert',
                    'priority': 'high',
                    'message': pred['description'],
                    'data': pred
                })
        
        # 时间管理预测
        for pred in predictions.get('predictions', {}).get('time', []):
            if pred.get('confidence', 0) > 0.7:
                actions.append({
                    'type': 'time_alert',
                    'priority': 'medium',
                    'message': pred['description'],
                    'data': pred
                })
        
        # 异常检测
        for pred in predictions.get('predictions', {}).get('anomalies', []):
            actions.append({
                'type': 'anomaly_alert',
                'priority': 'high',
                'message': pred['description'],
                'data': pred
            })
            self.stats['alerts'] += 1
        
        return actions
    
    async def _execute_action(self, action: Dict):
        """执行行动"""
        action_type = action.get('type')
        priority = action.get('priority', 'low')
        message = action.get('message', '')
        
        logger.info(f"[执行] [{priority.upper()}] {action_type}: {message}")
        
        # 实际应该发送通知、更新UI等
        # 这里简化为日志输出
        
        # 模拟异步操作
        await asyncio.sleep(0.1)
    
    async def _handle_event(self, event: Dict):
        """处理事件"""
        event_type = event.get('type')
        logger.info(f"[事件] 处理事件: {event_type}")
        
        if event_type == 'anomaly':
            # 异常事件：立即处理
            await self._handle_anomaly(event)
        
        elif event_type == 'user_query':
            # 用户查询：响应
            await self._respond_to_query(event)
        
        elif event_type == 'data_update':
            # 数据更新：可能触发预测
            if event.get('trigger_prediction', False):
                predictions = await self._run_prediction()
                actions = await self._decide_actions(predictions)
                for action in actions:
                    await self._execute_action(action)
    
    async def _handle_anomaly(self, event: Dict):
        """处理异常"""
        logger.warning(f"[异常] {event.get('description', 'Unknown anomaly')}")
        # 实际应该发送紧急通知
    
    async def _respond_to_query(self, event: Dict):
        """响应用户查询"""
        query = event.get('query', '')
        logger.info(f"[查询] 用户查询: {query}")
        # 实际应该调用决策引擎生成响应
    
    def trigger_event(self, event: Dict):
        """触发事件（同步方法）"""
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("[事件] 队列已满，丢弃事件")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'uptime_seconds': (datetime.now() - self.last_heartbeat).total_seconds() if self.last_heartbeat else 0
        }


# 示例使用
async def main():
    """测试自主Agent"""
    from digital_twin.digital_twin import DigitalTwin
    from prediction.swarm_prediction import SwarmPredictionEngine
    from agent.decision_engine import AutonomousDecisionEngine
    
    # 创建组件
    twin = DigitalTwin(user_id="test_user")
    predictor = SwarmPredictionEngine(twin)
    decider = AutonomousDecisionEngine()
    
    # 创建自主Agent
    agent = AutonomousAgent(twin, predictor, decider)
    
    # 启动（运行30秒后停止）
    agent_task = asyncio.create_task(agent.start())
    
    # 模拟一些事件
    await asyncio.sleep(5)
    agent.trigger_event({'type': 'data_update', 'trigger_prediction': True})
    
    await asyncio.sleep(10)
    agent.trigger_event({'type': 'user_query', 'query': '我今天健康状况如何？'})
    
    # 等待一段时间后停止
    await asyncio.sleep(15)
    await agent.stop()
    
    # 等待任务完成
    try:
        await asyncio.wait_for(agent_task, timeout=5.0)
    except asyncio.TimeoutError:
        agent_task.cancel()
    
    # 打印统计
    print("\n统计信息:")
    stats = agent.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
