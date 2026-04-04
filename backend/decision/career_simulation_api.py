"""
职业决策推演API
整合：知识图谱 → 信息收集 → 决策算法 → 5Agent并行推演 → 实时图谱显示
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

from backend.decision_algorithm.career_decision_algorithm import (
    KnowledgeGraphCareerIntegration,
    CareerPath,
    PersonalCapital
)
from backend.decision.multi_agent_career_evaluator import (
    MultiAgentCareerEvaluator,
    AgentState
)
from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
from backend.decision.websocket_keepalive import EnhancedWebSocketManager

logger = logging.getLogger(__name__)


class CareerSimulationEngine:
    """
    职业决策推演引擎
    
    流程：
    1. 从知识图谱提取用户数据
    2. 结合信息收集阶段的用户输入
    3. 使用职业决策算法生成3个选项
    4. 每个选项启动5个Agent并行推演12个月
    5. 实时推送Agent状态到前端图谱
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.kg_integration = KnowledgeGraphCareerIntegration(user_id)
        
    async def simulate_career_decision(
        self,
        question: str,
        collected_info: Dict[str, Any],
        num_options: int = 3,
        simulation_months: int = 12
    ) -> Dict[str, Any]:
        """
        完整的职业决策推演
        
        Args:
            question: 决策问题
            collected_info: 信息收集阶段收集的数据
            num_options: 生成选项数量（默认3个）
            simulation_months: 推演月数（默认12个月）
        
        Returns:
            {
                'question': 决策问题,
                'personal_capital': 个人资本评估,
                'options': [
                    {
                        'option_id': 'opt1',
                        'title': '选项标题',
                        'description': '选项描述',
                        'timeline': [月度Agent状态],
                        'summary': 总结,
                        'success_probability': 成功概率
                    },
                    ...
                ],
                'recommendation': 推荐选项,
                'ai_thinking': 5个Agent的思考过程
            }
        """
        
        logger.info(f"[职业推演] 开始推演 - 用户: {self.user_id}, 问题: {question}")
        
        # 步骤1: 从知识图谱提取个人资本
        personal_capital = self.kg_integration.extract_personal_capital_from_kg()
        logger.info(f"[职业推演] 个人资本提取完成")
        
        # 步骤2: 构建职业网络图
        career_graph = self.kg_integration.build_career_graph_from_real_data()
        logger.info(f"[职业推演] 职业网络构建完成")
        
        # 步骤3: 生成决策选项（基于算法）
        options = self._generate_options(
            question,
            collected_info,
            personal_capital,
            num_options
        )
        logger.info(f"[职业推演] 生成{len(options)}个选项")
        
        # 步骤4: 并行推演所有选项
        simulation_tasks = []
        for option in options:
            task = self._simulate_single_option(
                option,
                personal_capital,
                simulation_months
            )
            simulation_tasks.append(task)
        
        # 并行执行
        simulation_results = await asyncio.gather(*simulation_tasks)
        
        # 步骤5: 整合结果
        for i, option in enumerate(options):
            option['timeline'] = simulation_results[i]['timeline']
            option['summary'] = simulation_results[i]['summary']
            option['success_probability'] = simulation_results[i]['success_probability']
            option['ai_thinking'] = simulation_results[i]['ai_thinking']
        
        # 步骤6: 排序和推荐
        options.sort(key=lambda x: x['success_probability'], reverse=True)
        
        return {
            'question': question,
            'personal_capital': {
                'human_capital': personal_capital.calculate_human_capital_score(),
                'social_capital': personal_capital.calculate_social_capital_score(),
                'psychological_capital': personal_capital.calculate_psychological_capital_score(),
                'economic_capital': personal_capital.calculate_economic_capital_score()
            },
            'options': options,
            'recommendation': options[0] if options else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_options(
        self,
        question: str,
        collected_info: Dict[str, Any],
        personal_capital: PersonalCapital,
        num_options: int
    ) -> List[Dict[str, Any]]:
        """
        基于决策算法生成选项
        
        这里使用职业决策算法的量化分析
        """
        
        # 从collected_info提取关键信息
        current_role = collected_info.get('current_position', '当前岗位')
        target_roles = collected_info.get('options_mentioned', [])
        
        # 如果用户没有明确提供选项，基于算法生成
        if not target_roles or len(target_roles) < num_options:
            target_roles = self._generate_target_roles(current_role, num_options)
        
        options = []
        for i, target_role in enumerate(target_roles[:num_options], 1):
            # 构建职业路径
            path = CareerPath(
                path_id=f"opt{i}",
                current_role=current_role,
                target_role=target_role,
                total_duration_months=12,
                success_probability=0.6,  # 基础概率，后续由Agent模拟调整
                expected_salary_increase=5000,
                market_volatility=0.3
            )
            
            # 使用算法模拟
            simulation_result = self.kg_integration.algorithm.simulate_career_path(
                path,
                personal_capital,
                num_simulations=1000
            )
            
            options.append({
                'option_id': f"opt{i}",
                'title': f"选项{i}: {target_role}",
                'description': f"从{current_role}转向{target_role}",
                'target_role': target_role,
                'path': path,
                'algorithm_simulation': simulation_result,
                'context': {
                    'current_role': current_role,
                    'target_role': target_role,
                    'required_skills': collected_info.get('required_skills', []),
                    'target_industry': collected_info.get('target_industry', ''),
                    'current_salary': collected_info.get('current_salary', 25000),
                    'learning_hours_per_month': 40,
                    'networking_hours_per_month': 10
                }
            })
        
        return options
    
    def _generate_target_roles(self, current_role: str, num: int) -> List[str]:
        """基于当前角色生成可能的目标角色"""
        # 简化实现，实际应该从职业图谱查询
        role_map = {
            '初级后端工程师': ['中级后端工程师', '全栈工程师', '技术支持'],
            '中级后端工程师': ['高级后端工程师', '架构师', '技术经理'],
            '产品经理': ['高级产品经理', '产品总监', '创业'],
            '默认': ['高级工程师', '技术专家', '管理岗位']
        }
        
        targets = role_map.get(current_role, role_map['默认'])
        return targets[:num]
    
    async def _simulate_single_option(
        self,
        option: Dict[str, Any],
        personal_capital: PersonalCapital,
        months: int
    ) -> Dict[str, Any]:
        """
        模拟单个选项的5Agent推演
        
        Returns:
            {
                'timeline': [月度数据],
                'summary': 总结,
                'success_probability': 成功概率,
                'ai_thinking': 5个Agent的思考过程
            }
        """
        
        # 创建多Agent评估器
        evaluator = MultiAgentCareerEvaluator(self.user_id)
        
        # 初始化所有Agent
        await evaluator.initialize_all_agents(option['context'])
        
        # 模拟完整时间线
        result = await evaluator.simulate_full_timeline(
            context=option['context'],
            months=months
        )
        
        # 提取AI思考过程（5个Agent的分析）
        ai_thinking = self._extract_ai_thinking(result['timeline'])
        
        return {
            'timeline': result['timeline'],
            'summary': result['summary'],
            'success_probability': result['summary']['success_probability'],
            'ai_thinking': ai_thinking
        }
    
    def _extract_ai_thinking(self, timeline: List[Dict]) -> List[Dict[str, Any]]:
        """
        提取5个Agent的思考过程，作为AI的思考内容
        
        Returns:
            [
                {
                    'month': 1,
                    'agents_thinking': {
                        'skill_development': '技能Agent的分析',
                        'career_network': '人脉Agent的分析',
                        'financial': '财务Agent的分析',
                        'psychological': '心理Agent的分析',
                        'market_environment': '市场Agent的分析'
                    },
                    'interactions': 'Agent间的交互',
                    'decision_points': '关键决策点'
                }
            ]
        """
        
        ai_thinking = []
        
        for month_data in timeline:
            month = month_data['month']
            agents_state = month_data['agents_state']
            
            # 提取每个Agent的思考
            agents_thinking = {}
            for agent_name, state in agents_state.items():
                thinking = {
                    'score': state.score,
                    'status': state.status,
                    'analysis': state.changes,
                    'risks': state.risks,
                    'opportunities': state.opportunities,
                    'metrics': state.key_metrics
                }
                agents_thinking[agent_name] = thinking
            
            # 提取交互和决策点
            interactions = [
                {
                    'type': inter.interaction_type,
                    'agents': inter.agents,
                    'description': inter.description,
                    'impact': inter.impact
                }
                for inter in month_data.get('interactions', [])
            ]
            
            decision_points = [
                {
                    'trigger': dp.trigger_agent,
                    'description': dp.description,
                    'options': dp.options,
                    'recommendation': dp.recommendation,
                    'votes': dp.agent_votes
                }
                for dp in month_data.get('decision_points', [])
            ]
            
            ai_thinking.append({
                'month': month,
                'agents_thinking': agents_thinking,
                'interactions': interactions,
                'decision_points': decision_points,
                'overall_assessment': month_data['overall_assessment']
            })
        
        return ai_thinking


class CareerSimulationWebSocket:
    """
    职业推演WebSocket服务
    实时推送Agent状态到前端图谱
    
    改进：
    1. 使用EnhancedWebSocketManager管理连接
    2. 自动keepalive防止超时
    3. 消息重试机制
    """
    
    def __init__(self):
        self.ws_manager = EnhancedWebSocketManager()
    
    async def connect(self, websocket, user_id: str):
        """建立WebSocket连接（自动启用keepalive）"""
        await self.ws_manager.connect(websocket, user_id, enable_keepalive=True)
        logger.info(f"[推演WS] 用户{user_id}连接成功，已启用keepalive")
    
    def disconnect(self, user_id: str):
        """断开连接"""
        asyncio.create_task(self.ws_manager.disconnect(user_id))
        logger.info(f"[推演WS] 用户{user_id}断开连接")
    
    async def send_agent_state(
        self,
        user_id: str,
        option_id: str,
        month: int,
        agents_state: Dict[str, AgentState]
    ):
        """
        推送Agent状态到前端
        
        前端接收后更新图谱显示
        """
        
        # 构建消息
        message = {
            'type': 'agent_state_update',
            'option_id': option_id,
            'month': month,
            'agents': {}
        }
        
        for agent_name, state in agents_state.items():
            message['agents'][agent_name] = {
                'score': state.score,
                'status': state.status,
                'metrics': state.key_metrics,
                'changes': state.changes,
                'risks': state.risks,
                'opportunities': state.opportunities
            }
        
        # 使用管理器发送（自动重试）
        success = await self.ws_manager.send_message(user_id, message, retry=3)
        
        if success:
            logger.debug(f"[推演WS] 推送第{month}月Agent状态到用户{user_id}")
        else:
            logger.error(f"[推演WS] 推送失败，用户{user_id}可能已断开")
    
    async def send_simulation_complete(
        self,
        user_id: str,
        option_id: str,
        summary: Dict[str, Any]
    ):
        """推送推演完成消息"""
        
        message = {
            'type': 'simulation_complete',
            'option_id': option_id,
            'summary': summary
        }
        
        await self.ws_manager.send_message(user_id, message, retry=3)
        logger.info(f"[推演WS] 推送推演完成到用户{user_id}")
    
    async def send_progress(
        self,
        user_id: str,
        progress: float,
        message: str
    ):
        """推送进度更新"""
        
        await self.ws_manager.send_message(user_id, {
            'type': 'progress',
            'progress': progress,
            'message': message
        })
    
    async def send_error(
        self,
        user_id: str,
        error_message: str
    ):
        """推送错误消息"""
        
        await self.ws_manager.send_message(user_id, {
            'type': 'error',
            'message': error_message
        })


# 全局实例
ws_manager = CareerSimulationWebSocket()
