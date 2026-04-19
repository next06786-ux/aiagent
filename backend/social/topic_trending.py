"""
决策热度分析和推荐系统
混合方案：算法快速统计 + LLM 后台深度分析
分析用户决策数据，提取热门决策、痛点决策、成功决策
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import re


class DecisionTrendingService:
    """决策热度分析服务 - 混合方案"""
    
    def __init__(self):
        self.llm_service = None
        # 决策领域映射
        self.decision_domains = {
            'career': ['工作', '职业', '跳槽', '升职', '加薪', '创业', '面试', '辞职'],
            'education': ['学习', '考试', '升学', '考研', '留学', '培训', '技能'],
            'relationship': ['恋爱', '分手', '结婚', '离婚', '表白', '相亲', '感情'],
            'family': ['父母', '家庭', '亲情', '孩子', '教育', '养老'],
            'finance': ['理财', '投资', '买房', '贷款', '存钱', '消费', '债务'],
            'health': ['健康', '减肥', '运动', '体检', '医院', '养生', '睡眠'],
            'lifestyle': ['搬家', '旅行', '兴趣', '时间管理', '习惯', '目标'],
        }
        
    def _get_llm_service(self):
        """延迟加载 LLM 服务"""
        if self.llm_service is None:
            from backend.llm.llm_service import get_llm_service
            self.llm_service = get_llm_service()
        return self.llm_service
    
    def classify_decision_domain(self, text: str) -> str:
        """
        快速分类决策领域（算法方案）
        
        Args:
            text: 决策文本
            
        Returns:
            决策领域
        """
        text_lower = text.lower()
        domain_scores = defaultdict(int)
        
        for domain, keywords in self.decision_domains.items():
            for keyword in keywords:
                if keyword in text_lower:
                    domain_scores[domain] += 1
        
        if not domain_scores:
            return 'other'
        
        return max(domain_scores.items(), key=lambda x: x[1])[0]
    
    def extract_decisions_from_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从消息中提取决策（混合方案）
        
        Args:
            messages: 消息列表
            
        Returns:
            决策列表，包含决策类型、领域、情感等
        """
        if not messages:
            print(f"[DecisionTrending] 没有消息数据")
            return []
        
        # 合并消息内容
        message_texts = [msg.get('content', '') for msg in messages if msg.get('content')]
        if not message_texts:
            print(f"[DecisionTrending] 消息内容为空")
            return []
        
        print(f"[DecisionTrending] 准备分析 {len(message_texts)} 条消息")
        
        # 使用 LLM 提取决策
        llm = self._get_llm_service()
        if not llm or not llm.enabled:
            print(f"[DecisionTrending] LLM 服务不可用")
            return []
        
        try:
            prompt = f"""分析以下匿名决策消息，提取出主要的决策类型和痛点。

消息内容：
{chr(10).join(message_texts[:20])}  # 限制最多20条消息

请以 JSON 格式返回决策列表，每个决策包含：
- decision: 决策名称（简短，3-8个字）
- domain: 决策领域（career/education/relationship/family/finance/health/lifestyle）
- type: 决策类型（problem/success/question）
  - problem: 遇到困难的决策
  - success: 做得好的决策
  - question: 正在纠结的决策
- keywords: 相关关键词列表
- sentiment: 情感倾向（positive/neutral/negative）
- description: 决策描述（一句话）
- pain_point: 痛点描述（如果是problem类型）

示例格式：
[
  {{
    "decision": "要不要跳槽",
    "domain": "career",
    "type": "question",
    "keywords": ["跳槽", "工作", "选择"],
    "sentiment": "neutral",
    "description": "关于是否换工作的纠结",
    "pain_point": "不知道新工作是否更好"
  }},
  {{
    "decision": "成功转行",
    "domain": "career",
    "type": "success",
    "keywords": ["转行", "成功", "经验"],
    "sentiment": "positive",
    "description": "分享转行成功的经验"
  }}
]

只返回 JSON，不要其他内容。最多返回10个决策。"""

            print(f"[DecisionTrending] 调用 LLM...")
            response = llm.chat([{"role": "user", "content": prompt}], temperature=0.3)
            
            print(f"[DecisionTrending] LLM 响应长度: {len(response)} 字符")
            print(f"[DecisionTrending] LLM 响应前200字符: {response[:200]}")
            
            # 解析 JSON
            try:
                # 提取 JSON 部分
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    print(f"[DecisionTrending] 提取到 JSON: {json_str[:200]}...")
                    decisions = json.loads(json_str)
                    if decisions:  # 如果成功提取到决策
                        print(f"[DecisionTrending] ✅ LLM 成功提取 {len(decisions)} 个决策")
                        for i, d in enumerate(decisions[:3], 1):
                            print(f"  [{i}] {d.get('decision')} ({d.get('type')})")
                        return decisions[:10]  # 最多10个决策
                    else:
                        print(f"[DecisionTrending] ⚠️ JSON 数组为空")
                else:
                    print(f"[DecisionTrending] ❌ 未找到 JSON 数组")
                
                print(f"[DecisionTrending] LLM 未返回有效决策")
                return []
                
            except json.JSONDecodeError as e:
                print(f"[DecisionTrending] ❌ JSON 解析失败: {e}")
                print(f"[DecisionTrending] 完整响应: {response}")
                return []
                
        except Exception as e:
            print(f"[DecisionTrending] ❌ LLM 提取决策失败: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        return []
    
    def _extract_decisions_simple(self, message_texts: List[str]) -> List[Dict[str, Any]]:
        """算法快速提取决策（备用方案）"""
        # 常见决策关键词模式
        decision_patterns = {
            "要不要跳槽": {
                "keywords": ["跳槽", "换工作", "离职", "新工作"],
                "domain": "career",
                "type": "question"
            },
            "职业选择困惑": {
                "keywords": ["职业", "选择", "迷茫", "方向"],
                "domain": "career",
                "type": "problem"
            },
            "升职加薪": {
                "keywords": ["升职", "加薪", "晋升", "涨工资"],
                "domain": "career",
                "type": "question"
            },
            "考研还是工作": {
                "keywords": ["考研", "工作", "选择", "纠结"],
                "domain": "education",
                "type": "question"
            },
            "要不要表白": {
                "keywords": ["表白", "喜欢", "告白", "暗恋"],
                "domain": "relationship",
                "type": "question"
            },
            "分手还是继续": {
                "keywords": ["分手", "继续", "感情", "纠结"],
                "domain": "relationship",
                "type": "problem"
            },
            "买房决策": {
                "keywords": ["买房", "房子", "贷款", "首付"],
                "domain": "finance",
                "type": "question"
            },
            "理财投资": {
                "keywords": ["理财", "投资", "股票", "基金"],
                "domain": "finance",
                "type": "question"
            },
            "要不要辞职创业": {
                "keywords": ["辞职", "创业", "自己干"],
                "domain": "career",
                "type": "question"
            },
            "父母催婚": {
                "keywords": ["催婚", "父母", "结婚", "压力"],
                "domain": "family",
                "type": "problem"
            },
        }
        
        # 统计决策出现次数
        decision_counts = defaultdict(int)
        all_text = ' '.join(message_texts).lower()
        
        for decision, info in decision_patterns.items():
            for keyword in info['keywords']:
                if keyword in all_text:
                    decision_counts[decision] += all_text.count(keyword)
        
        # 转换为决策列表
        decisions = []
        for decision, count in sorted(decision_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                info = decision_patterns[decision]
                decisions.append({
                    'decision': decision,
                    'domain': info['domain'],
                    'type': info['type'],
                    'keywords': info['keywords'][:3],
                    'sentiment': 'negative' if info['type'] == 'problem' else 'neutral',
                    'description': f'关于{decision}的讨论',
                    'count': count
                })
        
        return decisions[:10]
    
    def calculate_decision_score(
        self, 
        message_count: int,
        like_count: int,
        comment_count: int,
        time_decay_hours: float,
        decision_type: str = 'question'
    ) -> float:
        """
        计算决策热度分数（算法方案）
        
        Args:
            message_count: 消息数量
            like_count: 点赞数
            comment_count: 评论数
            time_decay_hours: 距离现在的小时数
            decision_type: 决策类型（problem权重更高）
            
        Returns:
            热度分数
        """
        # 基础分数
        base_score = (
            message_count * 1.0 +
            like_count * 2.0 +
            comment_count * 1.5
        )
        
        # 决策类型权重
        type_weight = {
            'problem': 1.5,  # 痛点决策权重更高
            'question': 1.2,  # 纠结决策次之
            'success': 1.0,   # 成功经验正常权重
        }.get(decision_type, 1.0)
        
        # 时间衰减（24小时内的内容权重更高）
        time_factor = 1.0 / (1.0 + time_decay_hours / 24.0)
        
        # 最终分数
        score = base_score * type_weight * time_factor
        
        return round(score, 2)
    
    def get_trending_decisions(
        self,
        tree_holes: List[Dict[str, Any]],
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        获取热门决策排行榜（混合方案）
        
        Args:
            tree_holes: 树洞列表（包含消息数据）
            time_window_hours: 时间窗口（小时）
            
        Returns:
            热门决策列表，按热度排序
        """
        from datetime import timezone
        
        now = datetime.now(timezone.utc)  # 使用UTC时间
        trending_decisions = []
        
        print(f"[DecisionTrending] 开始分析 {len(tree_holes)} 个树洞")
        
        for hole in tree_holes:
            # 获取树洞的消息
            messages = hole.get('messages', [])
            if not messages:
                continue
            
            print(f"[DecisionTrending] 树洞 '{hole.get('title')}' 有 {len(messages)} 条消息")
            
            # 过滤时间窗口内的消息
            recent_messages = []
            for msg in messages:
                msg_time = msg.get('created_at')
                if isinstance(msg_time, str):
                    try:
                        # Neo4j返回的时间格式有9位纳秒，需要截断为6位微秒
                        # 例如: 2026-04-07T13:21:30.314000000+00:00 -> 2026-04-07T13:21:30.314000+00:00
                        if '.' in msg_time and '+' in msg_time:
                            parts = msg_time.split('.')
                            if len(parts) == 2:
                                microsec_and_tz = parts[1]
                                tz_start = microsec_and_tz.find('+')
                                if tz_start > 0:
                                    microsec = microsec_and_tz[:tz_start][:6]  # 只取前6位
                                    tz = microsec_and_tz[tz_start:]
                                    msg_time = f"{parts[0]}.{microsec}{tz}"
                        
                        # 解析ISO格式时间（带时区）
                        msg_time = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                    except Exception as e:
                        print(f"[DecisionTrending] 时间解析失败: {msg.get('created_at')}, 错误: {e}")
                        continue
                
                if isinstance(msg_time, datetime):
                    # 确保msg_time有时区信息
                    if msg_time.tzinfo is None:
                        msg_time = msg_time.replace(tzinfo=timezone.utc)
                    
                    hours_ago = (now - msg_time).total_seconds() / 3600
                    if hours_ago <= time_window_hours:
                        recent_messages.append(msg)
            
            print(f"[DecisionTrending] 时间窗口内的消息: {len(recent_messages)} 条")
            
            if not recent_messages:
                continue
            
            # 提取决策
            print(f"[DecisionTrending] 开始提取决策...")
            decisions = self.extract_decisions_from_messages(recent_messages)
            print(f"[DecisionTrending] 提取到 {len(decisions)} 个决策")
            
            # 计算热度
            for decision in decisions:
                message_count = len(recent_messages)
                like_count = sum(msg.get('likes', 0) for msg in recent_messages)
                comment_count = sum(msg.get('comments', 0) for msg in recent_messages)
                
                # 计算平均时间
                avg_hours_ago = sum(
                    (now - datetime.fromisoformat(msg['created_at'])).total_seconds() / 3600
                    for msg in recent_messages
                    if isinstance(msg.get('created_at'), str)
                ) / len(recent_messages) if recent_messages else 24
                
                score = self.calculate_decision_score(
                    message_count,
                    like_count,
                    comment_count,
                    avg_hours_ago,
                    decision.get('type', 'question')
                )
                
                trending_decisions.append({
                    'decision': decision['decision'],
                    'domain': decision.get('domain', 'other'),
                    'type': decision.get('type', 'question'),
                    'keywords': decision.get('keywords', []),
                    'sentiment': decision.get('sentiment', 'neutral'),
                    'description': decision.get('description', ''),
                    'pain_point': decision.get('pain_point', ''),
                    'score': score,
                    'message_count': message_count,
                    'tree_hole_id': hole.get('id'),
                    'tree_hole_title': hole.get('title'),
                })
        
        # 合并相同决策
        decision_map = {}
        for item in trending_decisions:
            decision_name = item['decision']
            if decision_name in decision_map:
                # 累加分数和消息数
                decision_map[decision_name]['score'] += item['score']
                decision_map[decision_name]['message_count'] += item['message_count']
                decision_map[decision_name]['tree_holes'].append({
                    'id': item['tree_hole_id'],
                    'title': item['tree_hole_title']
                })
            else:
                decision_map[decision_name] = {
                    'decision': decision_name,
                    'domain': item['domain'],
                    'type': item['type'],
                    'keywords': item['keywords'],
                    'sentiment': item['sentiment'],
                    'description': item['description'],
                    'pain_point': item.get('pain_point', ''),
                    'score': item['score'],
                    'message_count': item['message_count'],
                    'tree_holes': [{
                        'id': item['tree_hole_id'],
                        'title': item['tree_hole_title']
                    }]
                }
        
        # 排序并返回
        result = sorted(decision_map.values(), key=lambda x: x['score'], reverse=True)
        
        # 添加排名和趋势标记
        for i, decision in enumerate(result, 1):
            decision['rank'] = i
            # 痛点决策标记为热门，成功经验标记为上升
            if decision['type'] == 'problem':
                decision['trend'] = 'hot'
            elif decision['type'] == 'success':
                decision['trend'] = 'up'
            else:
                decision['trend'] = 'stable'
        
        return result[:20]  # 返回前20个热门决策
    
    def recommend_tree_holes(
        self,
        user_interests: List[str],
        tree_holes: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于用户兴趣推荐树洞
        
        Args:
            user_interests: 用户感兴趣的话题关键词
            tree_holes: 所有树洞列表
            limit: 返回数量
            
        Returns:
            推荐的树洞列表
        """
        if not user_interests:
            # 没有兴趣数据时，返回最热门的
            return sorted(
                tree_holes,
                key=lambda x: x.get('message_count', 0),
                reverse=True
            )[:limit]
        
        # 计算每个树洞的相关度
        scored_holes = []
        for hole in tree_holes:
            score = 0
            hole_text = f"{hole.get('title', '')} {hole.get('description', '')}".lower()
            
            # 计算关键词匹配度
            for interest in user_interests:
                if interest.lower() in hole_text:
                    score += 2
            
            # 加上热度因素
            score += hole.get('message_count', 0) * 0.1
            
            scored_holes.append({
                **hole,
                'recommendation_score': score
            })
        
        # 排序并返回
        return sorted(
            scored_holes,
            key=lambda x: x['recommendation_score'],
            reverse=True
        )[:limit]


# 全局单例
_trending_service = None

def get_trending_service() -> DecisionTrendingService:
    """获取决策热度服务单例"""
    global _trending_service
    if _trending_service is None:
        _trending_service = DecisionTrendingService()
    return _trending_service
