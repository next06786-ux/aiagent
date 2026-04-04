"""
职业决策推演集成模块

将多Agent评估框架集成到现有的三条路径推演中

架构：
1. 用户选择3个职业决策选项
2. 每个选项生成一条推演路径（12个月时间线）
3. 每条路径使用5个Agent进行多维度评估
4. 生成综合对比和推荐
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime

from backend.decision.multi_agent_career_evaluator import (
    MultiAgentCareerEvaluator,
    AgentState,
    AgentInteraction,
    DecisionPoint
)

logger = logging.getLogger(__name__)


class CareerSimulationIntegration:
    """职业决策推演集成器"""
    
    def __init__(self):
        pass
    
    async def simulate_career_decision_with_agents(
        self,
        user_id: str,
        question: str,
        options: List[Dict[str, Any]],
        collected_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用多Agent框架模拟职业决策
        
        Args:
            user_id: 用户ID
            question: 决策问题
            options: 决策选项列表（通常3个）
            collected_info: 收集的用户信息
        
        Returns:
            {
                'question': 决策问题,
                'options_simulation': [
                    {
                        'option': 选项信息,
                        'timeline': 12个月时间线,
                        'agent_evaluation': 多Agent评估,
                        'summary': 总结
                    }
                ],
                'comparison': 选项对比,
                'recommendation': 推荐
            }
        """
        
        logger.info(f"[CareerSimulation] 开始职业决策推演 - 用户: {user_id}, 选项数: {len(options)}")
        
        options_simulation = []
        
        # 为每个选项运行多Agent模拟
        for i, option in enumerate(options):
            logger.info(f"[CareerSimulation] 模拟选项 {i+1}: {option.get('title')}")
            
            try:
                simulation_result = await self._simulate_single_option(
                    user_id=user_id,
                    question=question,
                    option=option,
                    collected_info=collected_info
                )
                
                options_simulation.append(simulation_result)
                
            except Exception as e:
                logger.error(f"[CareerSimulation] 选项 {i+1} 模拟失败: {e}", exc_info=True)
                # 添加错误占位
                options_simulation.append({
                    'option': option,
                    'error': str(e),
                    'timeline': [],
                    'agent_evaluation': None
                })
        
        # 生成对比和推荐
        comparison = self._compare_options(options_simulation)
        recommendation = self._generate_recommendation(options_simulation, comparison)
        
        return {
            'question': question,
            'user_id': user_id,
            'options_simulation': options_simulation,
            'comparison': comparison,
            'recommendation': recommendation,
            'generated_at': datetime.now().isoformat()
        }
    
    async def _simulate_single_option(
        self,
        user_id: str,
        question: str,
        option: Dict[str, Any],
        collected_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """模拟单个选项"""
        
        # 创建多Agent评估器
        evaluator = MultiAgentCareerEvaluator(user_id)
        
        # 构建上下文
        context = self._build_context(option, collected_info)
        
        # 运行12个月模拟
        simulation_result = await evaluator.simulate_full_timeline(
            context=context,
            months=12
        )
        
        # 格式化输出
        return {
            'option': {
                'title': option.get('title'),
                'description': option.get('description', '')
            },
            'timeline': self._format_timeline(simulation_result['timeline']),
            'agent_evaluation': {
                'summary': simulation_result['summary'],
                'interactions': [self._format_interaction(i) for i in simulation_result['all_interactions']],
                'decision_points': [self._format_decision_point(dp) for dp in simulation_result['all_decision_points']]
            },
            'ai_thinking': self._extract_ai_thinking(simulation_result['timeline']),  # 新增：5Agent思考过程
            'final_assessment': simulation_result['timeline'][-1]['overall_assessment'] if simulation_result['timeline'] else None
        }
    
    def _build_context(
        self,
        option: Dict[str, Any],
        collected_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建模拟上下文"""
        
        return {
            'target_role': option.get('title', ''),
            'current_role': collected_info.get('current_role', ''),
            'current_salary': collected_info.get('current_salary', 25000),
            'learning_hours_per_month': collected_info.get('learning_hours_per_month', 80),
            'learning_cost_per_month': collected_info.get('learning_cost_per_month', 2000),
            'networking_events_per_month': collected_info.get('networking_events_per_month', 2),
            'required_skills': option.get('required_skills', {}),
            'option_description': option.get('description', '')
        }
    
    def _format_timeline(self, timeline: List[Dict]) -> List[Dict]:
        """格式化时间线"""
        
        formatted = []
        
        for month_data in timeline:
            month = month_data['month']
            agents_state = month_data['agents_state']
            overall = month_data['overall_assessment']
            
            # 提取每个Agent的关键信息
            agents_summary = {}
            for agent_name, state in agents_state.items():
                agents_summary[agent_name] = {
                    'score': state.score,
                    'status': state.status,
                    'key_metrics': state.key_metrics,
                    'changes': state.changes[:2],  # 只取前2个变化
                    'top_risk': state.risks[0] if state.risks else None,
                    'top_opportunity': state.opportunities[0] if state.opportunities else None
                }
            
            formatted.append({
                'month': month,
                'overall_score': overall['overall_score'],
                'overall_status': overall['overall_status'],
                'status_text': overall['status_text'],
                'agents': agents_summary,
                'has_decision_point': len(month_data['decision_points']) > 0,
                'has_interaction': len(month_data['interactions']) > 0
            })
        
        return formatted
    
    def _format_interaction(self, interaction: AgentInteraction) -> Dict:
        """格式化交互"""
        return {
            'month': interaction.month,
            'agents': interaction.agents,
            'type': interaction.interaction_type,
            'description': interaction.description,
            'impact': interaction.impact
        }
    
    def _format_decision_point(self, dp: DecisionPoint) -> Dict:
        """格式化决策点"""
        return {
            'month': dp.month,
            'trigger': dp.trigger_agent,
            'description': dp.description,
            'options': dp.options,
            'recommendation': dp.recommendation,
            'agent_votes': dp.agent_votes
        }
    
    def _extract_ai_thinking(self, timeline: List[Dict]) -> List[Dict[str, Any]]:
        """
        提取5个Agent的思考过程，作为AI的思考内容展示
        
        Returns:
            [
                {
                    'month': 1,
                    'thinking_summary': '本月综合分析',
                    'agents_analysis': {
                        'skill_development': {...},
                        'career_network': {...},
                        'financial': {...},
                        'psychological': {...},
                        'market_environment': {...}
                    },
                    'key_insights': ['洞察1', '洞察2'],
                    'warnings': ['警告1', '警告2']
                }
            ]
        """
        
        ai_thinking = []
        
        for month_data in timeline:
            month = month_data['month']
            agents_state = month_data['agents_state']
            overall = month_data['overall_assessment']
            
            # 提取每个Agent的详细分析
            agents_analysis = {}
            all_insights = []
            all_warnings = []
            
            for agent_name, state in agents_state.items():
                agent_analysis = {
                    'agent_name': self._get_agent_display_name(agent_name),
                    'score': state.score,
                    'status': state.status,
                    'status_text': self._get_status_text(state.status),
                    'key_metrics': state.key_metrics,
                    'changes': state.changes,
                    'risks': state.risks,
                    'opportunities': state.opportunities,
                    'thinking': self._generate_agent_thinking_text(agent_name, state)
                }
                agents_analysis[agent_name] = agent_analysis
                
                # 收集关键洞察
                if state.opportunities:
                    all_insights.extend(state.opportunities[:2])
                
                # 收集警告
                if state.risks:
                    all_warnings.extend(state.risks[:2])
            
            # 生成本月综合分析
            thinking_summary = self._generate_monthly_thinking_summary(
                month, overall, agents_state
            )
            
            ai_thinking.append({
                'month': month,
                'thinking_summary': thinking_summary,
                'agents_analysis': agents_analysis,
                'key_insights': all_insights[:3],  # 最多3个洞察
                'warnings': all_warnings[:3],  # 最多3个警告
                'overall_score': overall['overall_score'],
                'overall_status': overall['overall_status'],
                'has_critical_issue': overall['overall_status'] == 'critical'
            })
        
        return ai_thinking
    
    def _get_agent_display_name(self, agent_name: str) -> str:
        """获取Agent的显示名称"""
        name_map = {
            'skill_development': '技能发展Agent',
            'career_network': '职业人脉Agent',
            'financial': '财务状况Agent',
            'psychological': '心理资本Agent',
            'market_environment': '市场环境Agent'
        }
        return name_map.get(agent_name, agent_name)
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'good': '良好',
            'warning': '需要关注',
            'critical': '存在风险'
        }
        return status_map.get(status, status)
    
    def _generate_agent_thinking_text(self, agent_name: str, state: AgentState) -> str:
        """生成Agent的思考文本"""
        
        thinking_parts = []
        
        # 状态评估
        if state.status == 'good':
            thinking_parts.append(f"当前状态良好（{state.score:.0f}分）")
        elif state.status == 'warning':
            thinking_parts.append(f"需要关注（{state.score:.0f}分）")
        else:
            thinking_parts.append(f"存在风险（{state.score:.0f}分）")
        
        # 主要变化
        if state.changes:
            thinking_parts.append(f"主要变化：{state.changes[0]}")
        
        # 最大风险
        if state.risks:
            thinking_parts.append(f"风险：{state.risks[0]}")
        
        # 最佳机会
        if state.opportunities:
            thinking_parts.append(f"机会：{state.opportunities[0]}")
        
        return "；".join(thinking_parts)
    
    def _generate_monthly_thinking_summary(
        self,
        month: int,
        overall: Dict[str, Any],
        agents_state: Dict[str, AgentState]
    ) -> str:
        """生成月度综合分析摘要"""
        
        summary_parts = []
        
        # 整体评估
        summary_parts.append(
            f"第{month}月综合评估：{overall['status_text']}（综合得分{overall['overall_score']:.0f}分）"
        )
        
        # 最强和最弱维度
        weakest = overall['weakest_dimension']
        strongest = overall['strongest_dimension']
        
        summary_parts.append(
            f"最强维度是{self._get_agent_display_name(strongest['name'])}（{strongest['score']:.0f}分），"
            f"最弱维度是{self._get_agent_display_name(weakest['name'])}（{weakest['score']:.0f}分）"
        )
        
        # 关键风险
        if overall['total_risks'] > 0:
            summary_parts.append(f"本月发现{overall['total_risks']}个风险点")
        
        # 关键机会
        if overall['total_opportunities'] > 0:
            summary_parts.append(f"本月有{overall['total_opportunities']}个机会点")
        
        return "。".join(summary_parts) + "。"
    
    def _compare_options(
        self,
        options_simulation: List[Dict]
    ) -> Dict[str, Any]:
        """对比多个选项"""
        
        if not options_simulation:
            return {}
        
        comparison = {
            'dimensions': {},
            'rankings': {}
        }
        
        # 按维度对比
        dimensions = [
            'skill_development',
            'career_network',
            'financial',
            'psychological',
            'market_environment'
        ]
        
        for dim in dimensions:
            dim_comparison = []
            
            for sim in options_simulation:
                if sim.get('error'):
                    continue
                
                timeline = sim.get('timeline', [])
                if not timeline:
                    continue
                
                # 取最后一个月的状态
                last_month = timeline[-1]
                agent_state = last_month['agents'].get(dim)
                
                if agent_state:
                    dim_comparison.append({
                        'option': sim['option']['title'],
                        'score': agent_state['score'],
                        'status': agent_state['status']
                    })
            
            # 排序
            dim_comparison.sort(key=lambda x: x['score'], reverse=True)
            comparison['dimensions'][dim] = dim_comparison
        
        # 综合排名
        overall_ranking = []
        for sim in options_simulation:
            if sim.get('error'):
                continue
            
            final_assessment = sim.get('final_assessment')
            if final_assessment:
                overall_ranking.append({
                    'option': sim['option']['title'],
                    'overall_score': final_assessment['overall_score'],
                    'success_probability': sim['agent_evaluation']['summary'].get('success_probability', 0.5)
                })
        
        overall_ranking.sort(key=lambda x: x['overall_score'], reverse=True)
        comparison['rankings']['overall'] = overall_ranking
        
        return comparison
    
    def _generate_recommendation(
        self,
        options_simulation: List[Dict],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成推荐"""
        
        if not comparison.get('rankings', {}).get('overall'):
            return {
                'recommended_option': None,
                'reason': '无法生成推荐',
                'considerations': []
            }
        
        # 取综合得分最高的
        top_option = comparison['rankings']['overall'][0]
        
        # 分析原因
        reasons = []
        considerations = []
        
        # 找到对应的模拟结果
        top_sim = None
        for sim in options_simulation:
            if sim['option']['title'] == top_option['option']:
                top_sim = sim
                break
        
        if top_sim:
            summary = top_sim['agent_evaluation']['summary']
            
            # 分析优势
            agent_trends = summary.get('agent_trends', {})
            for agent_name, trend_data in agent_trends.items():
                if trend_data['final_score'] >= 70:
                    reasons.append(f"{agent_name} 表现优秀 ({trend_data['final_score']:.0f}分)")
            
            # 分析风险
            decision_points = top_sim['agent_evaluation']['decision_points']
            if decision_points:
                considerations.append(f"需要注意 {len(decision_points)} 个关键决策点")
            
            # 成功概率
            success_prob = summary.get('success_probability', 0.5)
            if success_prob >= 0.7:
                reasons.append(f"成功概率较高 ({success_prob:.0%})")
            elif success_prob < 0.5:
                considerations.append(f"成功概率偏低 ({success_prob:.0%})，需要谨慎")
        
        return {
            'recommended_option': top_option['option'],
            'overall_score': top_option['overall_score'],
            'success_probability': top_option['success_probability'],
            'reasons': reasons,
            'considerations': considerations,
            'alternative': comparison['rankings']['overall'][1]['option'] if len(comparison['rankings']['overall']) > 1 else None
        }


# 使用示例
async def example_usage():
    """使用示例"""
    
    integration = CareerSimulationIntegration()
    
    result = await integration.simulate_career_decision_with_agents(
        user_id="test_user",
        question="我应该转行做产品经理还是继续深耕技术？",
        options=[
            {
                'title': '转行产品经理',
                'description': '从后端工程师转向产品经理',
                'required_skills': {
                    '需求分析': 8.0,
                    '原型设计': 7.0,
                    '项目管理': 7.5
                }
            },
            {
                'title': '深耕技术成为架构师',
                'description': '继续技术路线，目标架构师',
                'required_skills': {
                    '系统设计': 8.5,
                    '技术选型': 8.0,
                    '团队指导': 7.0
                }
            },
            {
                'title': '技术管理',
                'description': '转向技术管理岗位',
                'required_skills': {
                    '团队管理': 8.0,
                    '技术规划': 7.5,
                    '沟通协调': 8.0
                }
            }
        ],
        collected_info={
            'current_role': '后端工程师',
            'current_salary': 25000,
            'learning_hours_per_month': 80,
            'learning_cost_per_month': 2000,
            'networking_events_per_month': 2
        }
    )
    
    print("\n" + "="*80)
    print("职业决策多Agent推演结果")
    print("="*80)
    
    print(f"\n问题: {result['question']}")
    print(f"\n推荐选项: {result['recommendation']['recommended_option']}")
    print(f"综合得分: {result['recommendation']['overall_score']:.1f}")
    print(f"成功概率: {result['recommendation']['success_probability']:.0%}")
    
    print(f"\n推荐理由:")
    for reason in result['recommendation']['reasons']:
        print(f"  ✓ {reason}")
    
    print(f"\n需要考虑:")
    for consideration in result['recommendation']['considerations']:
        print(f"  ⚠ {consideration}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(example_usage())
