"""
平行人生 - 塔罗牌决策游戏
通过游戏化方式收集用户的决策逻辑和价值观
"""
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class TarotCard(Enum):
    """塔罗牌类型"""
    THE_FOOL = "愚者"  # 冒险 vs 稳妥
    THE_MAGICIAN = "魔术师"  # 主动 vs 被动
    THE_EMPRESS = "皇后"  # 感性 vs 理性
    THE_EMPEROR = "皇帝"  # 权威 vs 自由
    THE_HIEROPHANT = "教皇"  # 传统 vs 创新
    THE_LOVERS = "恋人"  # 关系 vs 独立
    THE_CHARIOT = "战车"  # 进取 vs 保守
    STRENGTH = "力量"  # 坚持 vs 妥协
    THE_HERMIT = "隐者"  # 内省 vs 外向
    WHEEL_OF_FORTUNE = "命运之轮"  # 机遇 vs 计划
    JUSTICE = "正义"  # 公平 vs 效率
    THE_HANGED_MAN = "倒吊人"  # 牺牲 vs 自我
    DEATH = "死神"  # 变革 vs 维持
    TEMPERANCE = "节制"  # 平衡 vs 极致
    THE_DEVIL = "恶魔"  # 欲望 vs 克制
    THE_TOWER = "高塔"  # 破坏 vs 建设
    THE_STAR = "星星"  # 理想 vs 现实
    THE_MOON = "月亮"  # 直觉 vs 逻辑
    THE_SUN = "太阳"  # 乐观 vs 谨慎
    JUDGEMENT = "审判"  # 反思 vs 前进
    THE_WORLD = "世界"  # 完成 vs 探索


class DecisionDimension(Enum):
    """决策维度"""
    RISK_TOLERANCE = "风险偏好"  # 冒险 vs 稳妥
    INITIATIVE = "主动性"  # 主动 vs 被动
    THINKING_STYLE = "思维方式"  # 感性 vs 理性
    AUTHORITY = "权威态度"  # 服从 vs 独立
    INNOVATION = "创新倾向"  # 传统 vs 创新
    RELATIONSHIP = "关系导向"  # 关系 vs 目标
    AMBITION = "进取心"  # 进取 vs 保守
    PERSISTENCE = "坚持度"  # 坚持 vs 灵活
    SOCIAL = "社交倾向"  # 内向 vs 外向
    PLANNING = "计划性"  # 计划 vs 随机
    FAIRNESS = "公平观"  # 公平 vs 效率
    SACRIFICE = "牺牲精神"  # 利他 vs 利己
    CHANGE = "变革态度"  # 变革 vs 稳定
    BALANCE = "平衡观"  # 平衡 vs 专注
    DESIRE = "欲望控制"  # 克制 vs 放纵
    DESTRUCTION = "破坏性"  # 破坏 vs 建设
    IDEALISM = "理想主义"  # 理想 vs 现实
    INTUITION = "直觉依赖"  # 直觉 vs 逻辑
    OPTIMISM = "乐观度"  # 乐观 vs 悲观
    REFLECTION = "反思性"  # 反思 vs 行动
    COMPLETION = "完成导向"  # 完成 vs 探索


class TarotGameEngine:
    """塔罗牌游戏引擎"""
    
    # 塔罗牌与决策维度的映射
    CARD_DIMENSION_MAP = {
        TarotCard.THE_FOOL: DecisionDimension.RISK_TOLERANCE,
        TarotCard.THE_MAGICIAN: DecisionDimension.INITIATIVE,
        TarotCard.THE_EMPRESS: DecisionDimension.THINKING_STYLE,
        TarotCard.THE_EMPEROR: DecisionDimension.AUTHORITY,
        TarotCard.THE_HIEROPHANT: DecisionDimension.INNOVATION,
        TarotCard.THE_LOVERS: DecisionDimension.RELATIONSHIP,
        TarotCard.THE_CHARIOT: DecisionDimension.AMBITION,
        TarotCard.STRENGTH: DecisionDimension.PERSISTENCE,
        TarotCard.THE_HERMIT: DecisionDimension.SOCIAL,
        TarotCard.WHEEL_OF_FORTUNE: DecisionDimension.PLANNING,
        TarotCard.JUSTICE: DecisionDimension.FAIRNESS,
        TarotCard.THE_HANGED_MAN: DecisionDimension.SACRIFICE,
        TarotCard.DEATH: DecisionDimension.CHANGE,
        TarotCard.TEMPERANCE: DecisionDimension.BALANCE,
        TarotCard.THE_DEVIL: DecisionDimension.DESIRE,
        TarotCard.THE_TOWER: DecisionDimension.DESTRUCTION,
        TarotCard.THE_STAR: DecisionDimension.IDEALISM,
        TarotCard.THE_MOON: DecisionDimension.INTUITION,
        TarotCard.THE_SUN: DecisionDimension.OPTIMISM,
        TarotCard.JUDGEMENT: DecisionDimension.REFLECTION,
        TarotCard.THE_WORLD: DecisionDimension.COMPLETION,
    }
    
    def __init__(self):
        self.llm_service = None
        try:
            from backend.llm.llm_service import get_llm_service
            self.llm_service = get_llm_service()
            if self.llm_service:
                print(f"[塔罗牌] LLM服务初始化成功，启用状态: {self.llm_service.enabled}")
            else:
                print("[塔罗牌] LLM服务未初始化")
        except Exception as e:
            print(f"[塔罗牌] LLM服务初始化失败: {e}")
    
    def draw_card(self, user_id: str, drawn_cards: List[str] = None) -> Dict[str, Any]:
        """
        抽取一张塔罗牌
        
        Args:
            user_id: 用户ID
            drawn_cards: 已抽取的牌（避免重复）
        
        Returns:
            {
                'card': 牌名,
                'dimension': 决策维度,
                'scenario': AI生成的情景,
                'options': 选项列表
            }
        """
        # 过滤已抽取的牌
        available_cards = [card for card in TarotCard if card.value not in (drawn_cards or [])]
        
        if not available_cards:
            # 所有牌都抽完了，重新开始
            available_cards = list(TarotCard)
        
        # 随机抽取
        card = random.choice(available_cards)
        dimension = self.CARD_DIMENSION_MAP[card]
        
        # 生成情景和选项
        scenario = self._generate_scenario(card, dimension)
        
        return {
            'card': card.value,
            'card_key': card.name,
            'dimension': dimension.value,
            'dimension_key': dimension.name,
            'scenario': scenario['scenario'],
            'options': scenario['options'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_scenario(self, card: TarotCard, dimension: DecisionDimension) -> Dict[str, Any]:
        """
        使用LLM生成情景和选项
        
        Returns:
            {
                'scenario': 情景描述,
                'options': [
                    {'id': 'A', 'text': '选项A', 'tendency': 'left'},
                    {'id': 'B', 'text': '选项B', 'tendency': 'right'}
                ]
            }
        """
        if not self.llm_service or not self.llm_service.enabled:
            return self._get_fallback_scenario(card, dimension)
        
        try:
            import json
            
            prompt = f"""你是一个塔罗牌决策游戏的情景设计师。

塔罗牌：{card.value}
决策维度：{dimension.value}

请生成一个真实的人生决策情景，包含两个选项。这个情景应该：
1. 贴近真实生活
2. 能够反映用户在"{dimension.value}"维度上的倾向
3. 两个选项没有明显的对错，都有合理性
4. 情景描述简洁（50-100字）
5. 选项描述清晰（20-30字）

返回JSON格式：
{{
  "scenario": "情景描述",
  "options": [
    {{"id": "A", "text": "选项A描述", "tendency": "left"}},
    {{"id": "B", "text": "选项B描述", "tendency": "right"}}
  ]
}}

只返回JSON，不要其他内容。"""
            
            response = self.llm_service.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format="json_object"
            )
            
            result = json.loads(response)
            return result
            
        except Exception as e:
            print(f"[塔罗牌] 生成情景失败: {e}")
            return self._get_fallback_scenario(card, dimension)
    
    def _get_fallback_scenario(self, card: TarotCard, dimension: DecisionDimension) -> Dict[str, Any]:
        """备用情景（当LLM不可用时）"""
        scenarios = {
            TarotCard.THE_FOOL: {
                'scenario': '你收到一个海外工作机会，薪资是现在的两倍，但需要放弃国内稳定的工作和熟悉的环境。',
                'options': [
                    {'id': 'A', 'text': '接受挑战，去海外发展', 'tendency': 'left'},
                    {'id': 'B', 'text': '保持现状，继续稳定工作', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_MAGICIAN: {
                'scenario': '公司有一个重要项目缺少负责人，你有能力但经验不足，领导在观望。',
                'options': [
                    {'id': 'A', 'text': '主动请缨，争取机会', 'tendency': 'left'},
                    {'id': 'B', 'text': '等待安排，积累经验', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_EMPRESS: {
                'scenario': '朋友向你借钱创业，他很有激情但计划不够完善，你手头有些积蓄。',
                'options': [
                    {'id': 'A', 'text': '相信朋友，支持他的梦想', 'tendency': 'left'},
                    {'id': 'B', 'text': '理性分析，建议他完善计划', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_EMPEROR: {
                'scenario': '上级要求你执行一个你认为不合理的决策，但这是公司的统一安排。',
                'options': [
                    {'id': 'A', 'text': '服从安排，执行决策', 'tendency': 'left'},
                    {'id': 'B', 'text': '提出异议，坚持己见', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_HIEROPHANT: {
                'scenario': '你所在的行业有一个新兴技术方向，但大多数人还在使用传统方法。',
                'options': [
                    {'id': 'A', 'text': '跟随主流，使用成熟方案', 'tendency': 'left'},
                    {'id': 'B', 'text': '尝试新技术，探索创新', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_LOVERS: {
                'scenario': '你的好友和你的职业导师发生矛盾，双方都希望你站在他们一边。',
                'options': [
                    {'id': 'A', 'text': '维护友情，支持朋友', 'tendency': 'left'},
                    {'id': 'B', 'text': '保持中立，独立判断', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_CHARIOT: {
                'scenario': '你有机会竞争一个高级职位，但需要投入大量时间精力，可能影响生活质量。',
                'options': [
                    {'id': 'A', 'text': '全力以赴，争取晋升', 'tendency': 'left'},
                    {'id': 'B', 'text': '保持平衡，稳步发展', 'tendency': 'right'}
                ]
            },
            TarotCard.STRENGTH: {
                'scenario': '你的创业项目遇到困难，团队士气低落，有人建议转型或放弃。',
                'options': [
                    {'id': 'A', 'text': '坚持初心，继续努力', 'tendency': 'left'},
                    {'id': 'B', 'text': '灵活调整，及时转型', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_HERMIT: {
                'scenario': '周末有一个行业社交活动，可以认识很多人，但你更想独处充电。',
                'options': [
                    {'id': 'A', 'text': '独处休息，恢复精力', 'tendency': 'left'},
                    {'id': 'B', 'text': '参加活动，拓展人脉', 'tendency': 'right'}
                ]
            },
            TarotCard.WHEEL_OF_FORTUNE: {
                'scenario': '有一个投资机会收益很高但风险未知，你可以选择投资或按计划储蓄。',
                'options': [
                    {'id': 'A', 'text': '按计划储蓄，稳健理财', 'tendency': 'left'},
                    {'id': 'B', 'text': '抓住机会，尝试投资', 'tendency': 'right'}
                ]
            },
            TarotCard.JUSTICE: {
                'scenario': '团队分配奖金，你可以选择平均分配或按贡献分配（你贡献最大）。',
                'options': [
                    {'id': 'A', 'text': '公平分配，人人平等', 'tendency': 'left'},
                    {'id': 'B', 'text': '按贡献分配，提高效率', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_HANGED_MAN: {
                'scenario': '家人需要你回家照顾，但这会影响你的职业发展和个人规划。',
                'options': [
                    {'id': 'A', 'text': '回家照顾，承担责任', 'tendency': 'left'},
                    {'id': 'B', 'text': '继续发展，寻找其他方案', 'tendency': 'right'}
                ]
            },
            TarotCard.DEATH: {
                'scenario': '你的行业正在衰退，需要转行学习新技能，但现在的工作还算稳定。',
                'options': [
                    {'id': 'A', 'text': '维持现状，观望形势', 'tendency': 'left'},
                    {'id': 'B', 'text': '主动转型，学习新技能', 'tendency': 'right'}
                ]
            },
            TarotCard.TEMPERANCE: {
                'scenario': '你可以选择专注一个领域成为专家，或者发展多个技能成为通才。',
                'options': [
                    {'id': 'A', 'text': '平衡发展，成为通才', 'tendency': 'left'},
                    {'id': 'B', 'text': '专注深耕，成为专家', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_DEVIL: {
                'scenario': '你很想买一个昂贵的奢侈品，但这会花掉你几个月的积蓄。',
                'options': [
                    {'id': 'A', 'text': '克制欲望，理性消费', 'tendency': 'left'},
                    {'id': 'B', 'text': '满足自己，享受生活', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_TOWER: {
                'scenario': '你发现公司的管理制度有严重问题，可以选择推动改革或适应现状。',
                'options': [
                    {'id': 'A', 'text': '推动改革，打破现状', 'tendency': 'left'},
                    {'id': 'B', 'text': '适应环境，稳步建设', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_STAR: {
                'scenario': '你有一个理想的职业目标，但实现它需要放弃现在的高薪工作。',
                'options': [
                    {'id': 'A', 'text': '追求理想，勇敢尝试', 'tendency': 'left'},
                    {'id': 'B', 'text': '面对现实，保持稳定', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_MOON: {
                'scenario': '面对一个重要决策，你的直觉告诉你选A，但数据分析显示选B更好。',
                'options': [
                    {'id': 'A', 'text': '相信直觉，跟随感觉', 'tendency': 'left'},
                    {'id': 'B', 'text': '依据逻辑，分析数据', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_SUN: {
                'scenario': '你的项目遇到困难，团队情绪低落，你需要决定如何应对。',
                'options': [
                    {'id': 'A', 'text': '保持乐观，鼓舞士气', 'tendency': 'left'},
                    {'id': 'B', 'text': '谨慎评估，做好准备', 'tendency': 'right'}
                ]
            },
            TarotCard.JUDGEMENT: {
                'scenario': '年底了，你可以选择总结反思过去一年，或者直接规划新一年的目标。',
                'options': [
                    {'id': 'A', 'text': '反思总结，吸取经验', 'tendency': 'left'},
                    {'id': 'B', 'text': '向前看，制定新计划', 'tendency': 'right'}
                ]
            },
            TarotCard.THE_WORLD: {
                'scenario': '你完成了一个大项目，可以选择庆祝成果或立即开始新的挑战。',
                'options': [
                    {'id': 'A', 'text': '享受成果，好好休息', 'tendency': 'left'},
                    {'id': 'B', 'text': '继续探索，开启新篇章', 'tendency': 'right'}
                ]
            },
        }
        
        return scenarios.get(card, {
            'scenario': f'关于{dimension.value}的决策情景',
            'options': [
                {'id': 'A', 'text': '选项A', 'tendency': 'left'},
                {'id': 'B', 'text': '选项B', 'tendency': 'right'}
            ]
        })
    
    def analyze_choice(
        self,
        card_key: str,
        dimension_key: str,
        choice: str,
        tendency: str
    ) -> Dict[str, Any]:
        """
        分析用户的选择
        
        Args:
            card_key: 塔罗牌key
            dimension_key: 决策维度key
            choice: 用户选择的选项ID
            tendency: 选项倾向（left/right）
        
        Returns:
            分析结果
        """
        # 计算倾向值（-1到1，-1表示极左，1表示极右）
        tendency_value = -1.0 if tendency == 'left' else 1.0
        
        return {
            'dimension': dimension_key,
            'tendency_value': tendency_value,
            'choice': choice,
            'timestamp': datetime.now().isoformat()
        }
