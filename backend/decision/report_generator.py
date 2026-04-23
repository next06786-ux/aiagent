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
            
            # 调用 LLM 生成报告 - 使用 qwen-plus 模型获得更好的报告质量
            messages = [
                {
                    "role": "system",
                    "content": "你是一位资深的人生决策顾问，拥有丰富的咨询经验。你擅长从多个维度深入分析重大人生选择，并给出切实可行、有洞察力的建议。你的建议总是基于事实和数据，语言真诚接地气，能真正帮助人们做出明智的决策。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.llm_service.chat_async(
                messages=messages,
                temperature=0.7,
                model="qwen-plus"  # 使用 qwen-plus 模型生成高质量报告
            )
            
            # 解析响应 - chat_async 直接返回字符串
            report_text = response if isinstance(response, str) else response.get('content', '')
            
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
        
        # 整理 Agent 观点和推理过程
        agents_analysis = []
        for agent in agents_data:
            name = agent.get('name', '未知')
            stance = agent.get('stance', '未知')
            score = agent.get('score', 0)
            reasoning = agent.get('reasoning', '')
            
            # 提取推理的关键点（前200字）
            key_reasoning = reasoning[:200] + '...' if len(reasoning) > 200 else reasoning
            
            agents_analysis.append(
                f"【{name}】{stance} (评分: {score})\n"
                f"核心观点: {key_reasoning if key_reasoning else '暂无详细分析'}"
            )
        
        agents_text = "\n\n".join(agents_analysis)
        
        prompt = f"""你是一位资深的人生决策顾问，擅长从多个维度分析重大人生选择，并给出切实可行的建议。

【用户面临的决策】
{question}

【当前分析的选项】
{option_title}
{option_description if option_description else ''}

【7位专业顾问的深度分析】
{agents_text}

【综合评分】{total_score:.1f}/100

请基于以上7位顾问的专业分析，生成一份**真正有价值、可落地执行**的决策报告。

## 报告要求

1. **总体评价**（100-150字）
   - 用通俗易懂的语言概括这个选项的核心特点
   - 明确指出这个选项最适合什么样的人
   - 给出一个清晰的总体判断

2. **关键洞察**（3-5个要点）
   - 提炼出最重要的、容易被忽视的关键信息
   - 每个洞察要具体、可验证
   - 避免空洞的套话

3. **主要优势**（3-5个要点）
   - 列出这个选项的实际好处
   - 每个优势要具体说明如何实现
   - 关注长期价值和短期收益

4. **潜在风险**（3-5个要点）
   - 指出可能遇到的实际困难和挑战
   - 每个风险要说明发生概率和影响程度
   - 提供应对建议

5. **行动建议**（150-200字）
   - 如果选择这个方案，具体应该怎么做
   - 给出3-5个可执行的行动步骤
   - 说明需要准备什么、注意什么

## 写作风格要求
- 语言真诚、接地气，像朋友聊天一样
- 避免官话套话，要说人话
- 数据和事实优先，少用形容词
- 每个建议都要具体可行，不要泛泛而谈
- 站在用户角度思考，真正帮助他们做决策

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

## 行动建议
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
            elif '行动建议' in line or '综合建议' in line:
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
                'name': agent.get('name', '未知'),
                'stance': agent.get('stance', '未知'),
                'score': agent.get('score', 0),
                'confidence': agent.get('confidence', 0.8)  # 默认信心度
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
            stance = agent.get('stance', '未知')
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
                    'name': agent.get('name', '未知'),
                    'stance': agent.get('stance', '未知'),
                    'score': agent.get('score', 0),
                    'confidence': agent.get('confidence', 0.8)
                }
                for agent in agents_data
            ],
            'total_score': total_score,
            'full_text': ''
        }
