"""
动态画像更新系统
检测用户性格/习惯/价值观的变化，自动更新用户画像
"""
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.personality.personality_test import PersonalityTest
from backend.learning.production_rag_system import ProductionRAGSystem
from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph


@dataclass
class ProfileChange:
    """画像变化记录"""
    dimension: str  # 变化维度
    old_value: float  # 旧值
    new_value: float  # 新值
    change_rate: float  # 变化率
    confidence: float  # 置信度
    evidence: List[str]  # 证据


@dataclass
class UpdateResult:
    """更新结果"""
    user_id: str
    update_time: str
    has_changes: bool
    changes: List[ProfileChange]
    summary: str


class DynamicProfileUpdater:
    """动态画像更新器"""
    
    def __init__(self):
        self.personality_test = PersonalityTest()
        
        # 更新阈值
        self.thresholds = {
            "min_data_size": 50,  # 最少50条新数据
            "min_confidence": 0.6,  # 最低置信度
            "min_change_rate": 0.15  # 最小变化率15%
        }
    
    def check_update_trigger(self, user_id: str) -> bool:
        """
        检查是否需要更新画像
        
        触发条件:
        1. 距离上次更新超过7天
        2. 累积了足够的新数据
        3. 检测到显著变化
        """
        try:
            # 加载当前画像
            profile = self.personality_test.load_profile(user_id)
            
            if not profile:
                return False
            
            # 检查时间间隔
            if hasattr(profile, 'last_update'):
                last_update = datetime.fromisoformat(profile.last_update)
                days_since_update = (datetime.now() - last_update).days
                
                if days_since_update < 7:
                    print(f"距离上次更新仅{days_since_update}天，跳过")
                    return False
            
            # 检查新数据量
            rag = ProductionRAGSystem(user_id)
            memories = rag.get_all_memories()
            
            # 只统计最近7天的数据
            recent_memories = [
                m for m in memories
                if (datetime.now() - datetime.fromisoformat(m.timestamp)).days <= 7
            ]
            
            if len(recent_memories) < self.thresholds["min_data_size"]:
                print(f"新数据不足: {len(recent_memories)}/{self.thresholds['min_data_size']}")
                return False
            
            return True
            
        except Exception as e:
            print(f"检查更新触发失败: {e}")
            return False
    
    def update_profile(self, user_id: str) -> UpdateResult:
        """
        更新用户画像
        
        分析最近的数据，检测性格/习惯/价值观的变化
        """
        print(f"\n{'='*60}")
        print(f"开始更新用户画像: {user_id}")
        print(f"{'='*60}\n")
        
        # 加载当前画像
        current_profile = self.personality_test.load_profile(user_id)
        
        if not current_profile:
            return UpdateResult(
                user_id=user_id,
                update_time=datetime.now().isoformat(),
                has_changes=False,
                changes=[],
                summary="用户画像不存在"
            )
        
        # 分析最近数据
        changes = self._analyze_profile_changes(user_id, current_profile)
        
        # 应用变化
        if changes:
            self._apply_changes(user_id, current_profile, changes)
            has_changes = True
            summary = f"检测到{len(changes)}个维度的变化"
        else:
            has_changes = False
            summary = "未检测到显著变化"
        
        result = UpdateResult(
            user_id=user_id,
            update_time=datetime.now().isoformat(),
            has_changes=has_changes,
            changes=changes,
            summary=summary
        )
        
        # 保存更新记录
        self._save_update_record(result)
        
        print(f"\n{'='*60}")
        print(f"画像更新完成: {summary}")
        print(f"{'='*60}\n")
        
        return result
    
    def _analyze_profile_changes(self, user_id: str, current_profile: Any) -> List[ProfileChange]:
        """分析画像变化"""
        changes = []
        
        try:
            # 获取最近数据
            rag = ProductionRAGSystem(user_id)
            recent_memories = self._get_recent_memories(rag, days=7)
            
            if len(recent_memories) < self.thresholds["min_data_size"]:
                return changes
            
            # 分析各个维度的变化
            
            # 1. 分析决策风格变化
            decision_style_change = self._analyze_decision_style(recent_memories, current_profile)
            if decision_style_change:
                changes.append(decision_style_change)
            
            # 2. 分析风险偏好变化
            risk_preference_change = self._analyze_risk_preference(recent_memories, current_profile)
            if risk_preference_change:
                changes.append(risk_preference_change)
            
            # 3. 分析生活优先级变化
            priority_change = self._analyze_life_priority(recent_memories, current_profile)
            if priority_change:
                changes.append(priority_change)
            
            # 4. 分析情绪状态变化
            emotion_change = self._analyze_emotion_state(recent_memories, current_profile)
            if emotion_change:
                changes.append(emotion_change)
            
        except Exception as e:
            print(f"分析画像变化失败: {e}")
        
        return changes
    
    def _get_recent_memories(self, rag: ProductionRAGSystem, days: int = 7) -> List:
        """获取最近N天的记忆"""
        all_memories = rag.get_all_memories()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent = [
            m for m in all_memories
            if datetime.fromisoformat(m.timestamp) >= cutoff_date
        ]
        
        return recent
    
    def _analyze_decision_style(self, memories: List, current_profile: Any) -> Optional[ProfileChange]:
        """分析决策风格变化"""
        # 统计理性vs感性的关键词
        rational_keywords = ['分析', '数据', '逻辑', '理性', '计划', '评估']
        intuitive_keywords = ['感觉', '直觉', '冲动', '情感', '本能']
        
        rational_count = 0
        intuitive_count = 0
        evidence = []
        
        for memory in memories:
            content = memory.content.lower()
            
            for keyword in rational_keywords:
                if keyword in content:
                    rational_count += 1
            
            for keyword in intuitive_keywords:
                if keyword in content:
                    intuitive_count += 1
        
        total = rational_count + intuitive_count
        if total < 10:  # 数据太少
            return None
        
        # 计算理性倾向
        rational_ratio = rational_count / total
        
        # 当前风格
        current_style = current_profile.decision_style if hasattr(current_profile, 'decision_style') else "rational"
        current_value = 1.0 if current_style == "rational" else 0.0
        
        # 检测变化
        change_rate = abs(rational_ratio - current_value)
        
        if change_rate >= self.thresholds["min_change_rate"]:
            new_style = "rational" if rational_ratio > 0.6 else "intuitive"
            
            if new_style != current_style:
                evidence.append(f"理性关键词出现{rational_count}次")
                evidence.append(f"直觉关键词出现{intuitive_count}次")
                
                return ProfileChange(
                    dimension="decision_style",
                    old_value=current_value,
                    new_value=rational_ratio,
                    change_rate=change_rate,
                    confidence=min(0.9, total / 50),
                    evidence=evidence
                )
        
        return None
    
    def _analyze_risk_preference(self, memories: List, current_profile: Any) -> Optional[ProfileChange]:
        """分析风险偏好变化"""
        risk_seeking_keywords = ['冒险', '挑战', '尝试', '机会', '突破']
        risk_averse_keywords = ['稳定', '安全', '保守', '谨慎', '风险']
        
        seeking_count = 0
        averse_count = 0
        evidence = []
        
        for memory in memories:
            content = memory.content.lower()
            
            for keyword in risk_seeking_keywords:
                if keyword in content:
                    seeking_count += 1
            
            for keyword in risk_averse_keywords:
                if keyword in content:
                    averse_count += 1
        
        total = seeking_count + averse_count
        if total < 10:
            return None
        
        seeking_ratio = seeking_count / total
        
        # 当前偏好
        current_pref = current_profile.risk_preference if hasattr(current_profile, 'risk_preference') else "risk_neutral"
        current_value = 1.0 if current_pref == "risk_seeking" else (0.5 if current_pref == "risk_neutral" else 0.0)
        
        change_rate = abs(seeking_ratio - current_value)
        
        if change_rate >= self.thresholds["min_change_rate"]:
            if seeking_ratio > 0.6:
                new_pref = "risk_seeking"
            elif seeking_ratio < 0.4:
                new_pref = "risk_averse"
            else:
                new_pref = "risk_neutral"
            
            if new_pref != current_pref:
                evidence.append(f"风险追求关键词出现{seeking_count}次")
                evidence.append(f"风险规避关键词出现{averse_count}次")
                
                return ProfileChange(
                    dimension="risk_preference",
                    old_value=current_value,
                    new_value=seeking_ratio,
                    change_rate=change_rate,
                    confidence=min(0.9, total / 50),
                    evidence=evidence
                )
        
        return None
    
    def _analyze_life_priority(self, memories: List, current_profile: Any) -> Optional[ProfileChange]:
        """分析生活优先级变化"""
        priority_keywords = {
            "health_first": ['健康', '运动', '睡眠', '身体'],
            "career_first": ['工作', '事业', '职业', '晋升'],
            "wealth_first": ['赚钱', '财富', '收入', '投资'],
            "relationship_first": ['家人', '朋友', '爱情', '关系'],
            "freedom_first": ['自由', '独立', '旅行', '探索']
        }
        
        priority_counts = {key: 0 for key in priority_keywords.keys()}
        
        for memory in memories:
            content = memory.content.lower()
            
            for priority, keywords in priority_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        priority_counts[priority] += 1
        
        # 找出最高优先级
        if sum(priority_counts.values()) < 10:
            return None
        
        new_priority = max(priority_counts, key=priority_counts.get)
        current_priority = current_profile.life_priority if hasattr(current_profile, 'life_priority') else "health_first"
        
        if new_priority != current_priority and priority_counts[new_priority] >= 5:
            evidence = [f"{key}: {count}次" for key, count in priority_counts.items() if count > 0]
            
            return ProfileChange(
                dimension="life_priority",
                old_value=0.0,
                new_value=1.0,
                change_rate=1.0,
                confidence=0.7,
                evidence=evidence
            )
        
        return None
    
    def _analyze_emotion_state(self, memories: List, current_profile: Any) -> Optional[ProfileChange]:
        """分析情绪状态变化"""
        positive_keywords = ['开心', '快乐', '满意', '兴奋', '幸福']
        negative_keywords = ['焦虑', '压力', '疲惫', '沮丧', '担心']
        
        positive_count = 0
        negative_count = 0
        
        for memory in memories:
            content = memory.content.lower()
            
            for keyword in positive_keywords:
                if keyword in content:
                    positive_count += 1
            
            for keyword in negative_keywords:
                if keyword in content:
                    negative_count += 1
        
        total = positive_count + negative_count
        if total < 5:
            return None
        
        # 情绪得分 (0-1, 越高越积极)
        emotion_score = positive_count / total if total > 0 else 0.5
        
        # 如果情绪明显偏负面，记录变化
        if emotion_score < 0.3:
            evidence = [
                f"积极情绪关键词: {positive_count}次",
                f"消极情绪关键词: {negative_count}次",
                "建议关注心理健康"
            ]
            
            return ProfileChange(
                dimension="emotion_state",
                old_value=0.5,
                new_value=emotion_score,
                change_rate=abs(0.5 - emotion_score),
                confidence=0.6,
                evidence=evidence
            )
        
        return None
    
    def _apply_changes(self, user_id: str, current_profile: Any, changes: List[ProfileChange]):
        """应用画像变化"""
        for change in changes:
            if change.dimension == "decision_style":
                new_style = "rational" if change.new_value > 0.6 else "intuitive"
                current_profile.decision_style = new_style
                print(f"✅ 决策风格更新: {new_style}")
            
            elif change.dimension == "risk_preference":
                if change.new_value > 0.6:
                    new_pref = "risk_seeking"
                elif change.new_value < 0.4:
                    new_pref = "risk_averse"
                else:
                    new_pref = "risk_neutral"
                current_profile.risk_preference = new_pref
                print(f"✅ 风险偏好更新: {new_pref}")
            
            elif change.dimension == "life_priority":
                # 这里需要根据evidence推断新的优先级
                print(f"✅ 生活优先级可能发生变化")
        
        # 更新时间戳
        current_profile.last_update = datetime.now().isoformat()
        
        # 保存更新后的画像
        self.personality_test.save_profile(user_id, current_profile)
    
    def _save_update_record(self, result: UpdateResult):
        """保存更新记录"""
        record_dir = "./data/profile_updates"
        os.makedirs(record_dir, exist_ok=True)
        
        filename = f"{result.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(record_dir, filename)
        
        # 转换为可序列化格式
        record = {
            "user_id": result.user_id,
            "update_time": result.update_time,
            "has_changes": result.has_changes,
            "changes": [
                {
                    "dimension": c.dimension,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "change_rate": c.change_rate,
                    "confidence": c.confidence,
                    "evidence": c.evidence
                }
                for c in result.changes
            ],
            "summary": result.summary
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)


# 测试代码
if __name__ == "__main__":
    updater = DynamicProfileUpdater()
    
    user_id = "test_user_001"
    
    print("="*60)
    print("动态画像更新系统测试")
    print("="*60)
    print()
    
    # 检查是否需要更新
    print("1. 检查更新触发条件...")
    should_update = updater.check_update_trigger(user_id)
    
    if should_update:
        print("✅ 满足更新条件\n")
        
        # 执行更新
        print("2. 执行画像更新...")
        result = updater.update_profile(user_id)
        
        print(f"\n更新结果:")
        print(f"  有变化: {result.has_changes}")
        print(f"  变化数: {len(result.changes)}")
        print(f"  总结: {result.summary}")
        
        if result.changes:
            print(f"\n变化详情:")
            for change in result.changes:
                print(f"\n  维度: {change.dimension}")
                print(f"  变化率: {change.change_rate:.1%}")
                print(f"  置信度: {change.confidence:.1%}")
                print(f"  证据:")
                for evidence in change.evidence:
                    print(f"    - {evidence}")
    else:
        print("⏭️  不满足更新条件，跳过")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
