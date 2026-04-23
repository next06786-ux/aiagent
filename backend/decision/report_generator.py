"""
决策报告生成器
使用 LLM 生成决策分析报告
"""
import logging
from typing import Dict, List, Any
from backend.llm.llm_service import LLMService

logger = logging.getLogger(__name__)


class DecisionReportGenerator:
    """决策报告生成器"""
    
    def __init__(self, llm_service: LLMService):
        """
        初始化报告生成器
        
        Args:
            llm_service: LLM 服务实例
        """
        self.llm_service = llm_service
    
    async def generate_option_report(
        self,
        question: str,
        option_title: str,
        option_description: str,
        agents_data: List[Dict[str, Any]],
        total_score: float
    ) -> Dict[str, Any]:
        """
        生成选项的综合报告
        
        Args:
            question: 决策问题
            option_title: 选项标题
            option_description: 选项描述
            agents_data: 所有Agent的数据
            total_score: 总评分
        
        Returns:
            报告数据
        """
        try:
            # 构建提示词
            prompt = self._build_report_prompt(
                question,
                option_title,
                option_description,
                agents_data,
                total_score
            )
            
            # 调用 LLM 生成报告
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析响应
            report_text = response.get('content', '')
            
            # 提取关键信息
            report = self._parse_report(report_text, agents_data, total_score)
            
            return {
                'success': True,
                'report': report
            }
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            # 返回基础报告
            return {
                'success': False,
                'report': self._generate_fallback_report(
                    option_title,
                    agents_data,
                    total_score
                )
            }
    
    def _build_report_prompt(
        self,
        question: str,
        option_title: str,
        option_description: str,
        agents_data: List[Dict[str, Any]],
        total_score: float
    ) -> str:
        """构建报告生成提示词"""
        
        # 整理 Agent 观点
        agents_summary = []
        for agent in agents_data:
            agents_summary.append(
                f"- {agent['name']}: {agent.get('finalStance', '未知')} "
                f"(评分: {agent.get('finalScore', 0)}, "
                f"信心: {agent.get('finalConfidence', 0)*100:.0f}%)"
            )
        
        agents_text = "\n".join(agents_summary)
        
        prompt = f"""请为以下决策选项生成一份综合分析报告。

【决策问题】
{question}

【分析选项】
标题: {option_title}
描述: {option_description}

【Agent 评估结果】
{agents_text}

【综合评分】
{total_score:.1f} 分

请生成一份结构化的分析报告，包含以下部分：

1. 总体评价（2-3句话概括）
2. 关键洞察（3-5个要点）
3. 主要优势（3-5个要点）
4. 潜在风险（3-5个要点）
5. 综合建议（2-3句话）

要求：
- 语言简洁专业
- 观点基于 Agent 的分析结果
- 突出关键信息
- 避免重复

请按以下格式输出：

## 总体评价
[内容]

## 关键洞察
- [洞察1]
- [洞察2]
- [洞察3]

## 主要优势
- [优势1]
- [优势2]
- [优势3]

## 潜在风险
- [风险1]
- [风险2]
- [风险3]

## 综合建议
[内容]
"""
        
        return prompt
    
    def _parse_report(
        self,
        report_text: str,
        agents_data: List[Dict[str, Any]],
        total_score: float
    ) -> Dict[str, Any]:
        """解析报告文本"""
        
        sections = {
            'summary': '',
            'key_insights': [],
            'strengths': [],
            'risks': [],
            'recommendation': ''
        }
        
        # 简单的文本解析
        lines = report_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '总体评价' in line:
                current_section = 'summary'
            elif '关键洞察' in line:
                current_section = 'key_insights'
            elif '主要优势' in line:
                current_section = 'strengths'
            elif '潜在风险' in line:
                current_section = 'risks'
            elif '综合建议' in line:
                current_section = 'recommendation'
            elif line.startswith('- ') or line.startswith('• '):
                # 列表项
                item = line[2:].strip()
                if current_section in ['key_insights', 'strengths', 'risks']:
                    sections[current_section].append(item)
            elif line.startswith('#'):
                # 跳过标题行
                continue
            else:
                # 普通文本
                if current_section in ['summary', 'recommendation']:
                    sections[current_section] += line + ' '
        
        # 清理文本
        sections['summary'] = sections['summary'].strip()
        sections['recommendation'] = sections['recommendation'].strip()
        
        # 添加 Agent 数据
        sections['agents_summary'] = [
            {
                'name': agent['name'],
                'stance': agent.get('finalStance', '未知'),
                'score': agent.get('finalScore', 0),
                'confidence': agent.get('finalConfidence', 0)
            }
            for agent in agents_data
        ]
        
        sections['total_score'] = total_score
        sections['full_text'] = report_text
        
        return sections
    
    def _generate_fallback_report(
        self,
        option_title: str,
        agents_data: List[Dict[str, Any]],
        total_score: float
    ) -> Dict[str, Any]:
        """生成备用报告（当 LLM 失败时）"""
        
        # 统计立场
        stances = {}
        for agent in agents_data:
            stance = agent.get('finalStance', '未知')
            stances[stance] = stances.get(stance, 0) + 1
        
        # 找出主流立场
        dominant_stance = max(stances.items(), key=lambda x: x[1])[0] if stances else '未知'
        
        return {
            'summary': f'该选项"{option_title}"获得综合评分 {total_score:.1f} 分，'
                      f'多数 Agent 持"{dominant_stance}"立场。',
            'key_insights': [
                f'共有 {len(agents_data)} 个 Agent 参与评估',
                f'主流立场为"{dominant_stance}"',
                f'综合评分为 {total_score:.1f} 分'
            ],
            'strengths': ['详细分析需要查看各 Agent 的具体评估'],
            'risks': ['详细分析需要查看各 Agent 的具体评估'],
            'recommendation': '建议结合各 Agent 的详细分析进行综合判断。',
            'agents_summary': [
                {
                    'name': agent['name'],
                    'stance': agent.get('finalStance', '未知'),
                    'score': agent.get('finalScore', 0),
                    'confidence': agent.get('finalConfidence', 0)
                }
                for agent in agents_data
            ],
            'total_score': total_score,
            'full_text': ''
        }
