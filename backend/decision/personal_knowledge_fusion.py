# -*- coding: utf-8 -*-
"""
PKF-DS: Personal Knowledge Fusion for Decision Simulation

四阶段推演流水线：
1. 多源个人知识抽取与融合（Personal Fact Extraction）
2. 因果推理图构建（Causal Reasoning Graph）
3. 个性化条件生成（Personalized Conditional Generation）
4. 反事实校验与纠错（Counterfactual Verification）
"""
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 1：个人事实三元组抽取
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PersonalFact:
    """个人事实三元组 (subject, relation, object)"""
    subject: str
    relation: str
    obj: str
    confidence: float = 0.8
    source: str = ""  # "chat" | "collect" | "game" | "kg"
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "relation": self.relation,
            "object": self.obj,
            "confidence": self.confidence,
            "source": self.source
        }

    def to_text(self) -> str:
        return f"{self.subject} {self.relation} {self.obj}"


class PersonalFactExtractor:
    """从多源数据中抽取个人事实三元组"""

    # LLM 抽取 prompt
    EXTRACT_PROMPT = """从以下用户对话中提取个人事实，每条事实用 (主语, 关系, 宾语) 三元组表示。
只提取关于用户本人的客观事实，不要推测。

对话内容：
{text}

请以 JSON 数组格式输出，每个元素包含 subject, relation, object 三个字段。
示例：[{{"subject":"用户","relation":"月薪","object":"18k"}},{{"subject":"用户","relation":"工作","object":"后端开发"}}]
只输出 JSON，不要解释。"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.facts: List[PersonalFact] = []

    def extract_all(self) -> List[PersonalFact]:
        """从所有数据源抽取事实"""
        self.facts = []
        self._extract_from_kg()
        self._extract_from_conversations()
        self._extract_from_game()
        self._deduplicate()
        print(f"[PKF] 用户 {self.user_id} 共抽取 {len(self.facts)} 条个人事实")
        return self.facts

    def _extract_from_kg(self):
        """从知识图谱抽取人物关系事实"""
        try:
            from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
            with Neo4jKnowledgeGraph(self.user_id) as kg:
                central = kg.get_central_nodes(limit=10)
                for node in central:
                    name = node.get("name", "")
                    if not name:
                        continue
                    rels = kg.get_entity_relationships(name)
                    for r in rels[:5]:
                        self.facts.append(PersonalFact(
                            subject="用户",
                            relation=f"认识({r.get('type', '关系')})",
                            obj=name,
                            confidence=0.9,
                            source="kg"
                        ))
        except Exception as e:
            print(f"[PKF] 知识图谱抽取失败: {e}")

    def _extract_from_conversations(self):
        """从对话历史中用 LLM 抽取事实"""
        try:
            from backend.database.connection import db_connection
            from backend.database.models import ConversationHistory
            from sqlalchemy import and_

            db = db_connection.get_session()
            rows = db.query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == self.user_id,
                    ConversationHistory.role == "user"
                )
            ).order_by(ConversationHistory.timestamp.desc()).limit(30).all()
            db.close()

            if not rows:
                return

            # 合并最近的对话文本
            texts = [r.content for r in rows if r.content and len(r.content) > 10]
            if not texts:
                return

            combined = "\n".join(texts[:15])  # 最多取 15 条，避免 prompt 过长

            # 用 LLM 抽取
            facts = self._llm_extract(combined, "chat")
            self.facts.extend(facts)

            # 额外处理收集对话
            collect_rows = db_connection.get_session().query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == self.user_id,
                    ConversationHistory.session_id.like("collect_%"),
                    ConversationHistory.role == "user"
                )
            ).order_by(ConversationHistory.timestamp.desc()).limit(10).all()
            db_connection.get_session().close()

            if collect_rows:
                collect_text = "\n".join([r.content for r in collect_rows if r.content])
                collect_facts = self._llm_extract(collect_text, "collect")
                self.facts.extend(collect_facts)

        except Exception as e:
            print(f"[PKF] 对话抽取失败: {e}")

    def _extract_from_game(self):
        """从游戏数据中抽取决策偏好事实"""
        try:
            from backend.database.connection import db_connection
            from backend.database.models import ConversationHistory
            from sqlalchemy import and_

            db = db_connection.get_session()
            rows = db.query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == self.user_id,
                    ConversationHistory.session_id.like("game_%"),
                    ConversationHistory.role == "assistant"
                )
            ).order_by(ConversationHistory.timestamp.desc()).limit(5).all()
            db.close()

            for r in rows:
                if not r.content:
                    continue
                if "冒险探索" in r.content:
                    self.facts.append(PersonalFact("用户", "决策风格", "偏冒险", 0.7, "game"))
                elif "稳健保守" in r.content:
                    self.facts.append(PersonalFact("用户", "决策风格", "偏保守", 0.7, "game"))
                if "情绪健康" in r.content:
                    self.facts.append(PersonalFact("用户", "最看重", "情绪健康", 0.7, "game"))
                elif "财务安全" in r.content:
                    self.facts.append(PersonalFact("用户", "最看重", "财务安全", 0.7, "game"))
                elif "社交关系" in r.content:
                    self.facts.append(PersonalFact("用户", "最看重", "社交关系", 0.7, "game"))

        except Exception as e:
            print(f"[PKF] 游戏数据抽取失败: {e}")

    def _llm_extract(self, text: str, source: str) -> List[PersonalFact]:
        """用 LLM 从文本中抽取事实三元组"""
        try:
            from backend.llm.llm_service import get_llm_service
            llm = get_llm_service()
            if not llm or not llm.enabled:
                return self._rule_extract(text, source)

            prompt = self.EXTRACT_PROMPT.format(text=text[:2000])
            response = llm.chat([
                {"role": "system", "content": "你是一个信息抽取助手，只输出 JSON。"},
                {"role": "user", "content": prompt}
            ], temperature=0.1)

            if not response:
                return self._rule_extract(text, source)

            # 解析 JSON
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            data = json.loads(response.strip())

            facts = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "subject" in item and "relation" in item and "object" in item:
                        facts.append(PersonalFact(
                            subject=str(item["subject"]),
                            relation=str(item["relation"]),
                            obj=str(item["object"]),
                            confidence=0.75,
                            source=source
                        ))
            return facts

        except Exception as e:
            print(f"[PKF] LLM 抽取失败: {e}")
            return self._rule_extract(text, source)

    def _rule_extract(self, text: str, source: str) -> List[PersonalFact]:
        """规则兜底抽取"""
        facts = []
        # 薪资
        m = re.search(r"(\d+)[kK万]", text)
        if m:
            facts.append(PersonalFact("用户", "薪资相关", m.group(0), 0.6, source))
        # 职业关键词
        for kw in ["考研", "工作", "创业", "跳槽", "辞职", "读研", "考公"]:
            if kw in text:
                facts.append(PersonalFact("用户", "考虑中", kw, 0.5, source))
        return facts

    def _deduplicate(self):
        """去重：相同 (relation, obj) 只保留置信度最高的"""
        seen: Dict[str, PersonalFact] = {}
        for f in self.facts:
            key = f"{f.relation}_{f.obj}"
            if key not in seen or f.confidence > seen[key].confidence:
                seen[key] = f
        self.facts = list(seen.values())


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 2：因果推理图构建
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CausalEdge:
    """因果边"""
    cause: str
    effect: str
    strength: float = 0.5   # 因果强度 0-1
    polarity: str = "+"     # "+" 正向 / "-" 负向
    personal: bool = False  # 是否基于个人事实

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause": self.cause,
            "effect": self.effect,
            "strength": self.strength,
            "polarity": self.polarity,
            "personal": self.personal
        }


class CausalReasoningGraph:
    """因果推理图：基于个人事实约束的因果链自动构建"""

    BUILD_PROMPT = """你是一个因果推理专家。根据以下决策问题和用户的个人事实，构建因果推理链。

决策问题：{question}
决策选项：{option}

用户个人事实：
{facts}

请生成 8-12 条因果关系，格式为 JSON 数组：
[{{"cause":"辞职","effect":"收入中断","strength":0.9,"polarity":"-"}},
 {{"cause":"收入中断","effect":"房贷压力增大","strength":0.8,"polarity":"-"}}]

要求：
1. 因果链必须基于用户的真实个人事实，不要编造用户没有的情况
2. 包含正面和负面两个方向的因果链
3. strength 表示因果关系的强度（0-1）
4. polarity 为 "+" 表示正向影响，"-" 表示负向影响
只输出 JSON。"""

    def __init__(self, question: str, option: str, facts: List[PersonalFact]):
        self.question = question
        self.option = option
        self.facts = facts
        self.edges: List[CausalEdge] = []

    def build(self) -> List[CausalEdge]:
        """构建因果推理图"""
        self.edges = []
        llm_edges = self._llm_build()
        self.edges.extend(llm_edges)
        self._filter_by_facts()
        self._enrich_with_facts()
        print(f"[PKF-因果图] 构建了 {len(self.edges)} 条因果边")
        return self.edges

    def _llm_build(self) -> List[CausalEdge]:
        """用 LLM 生成因果关系候选"""
        try:
            from backend.llm.llm_service import get_llm_service
            llm = get_llm_service()
            if not llm or not llm.enabled:
                return self._fallback_build()

            facts_text = "\n".join([f"- {f.to_text()}" for f in self.facts[:15]])
            prompt = self.BUILD_PROMPT.format(
                question=self.question,
                option=self.option,
                facts=facts_text
            )

            response = llm.chat([
                {"role": "system", "content": "你是因果推理专家，只输出 JSON。"},
                {"role": "user", "content": prompt}
            ], temperature=0.2)

            if not response:
                return self._fallback_build()

            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            data = json.loads(response.strip())

            edges = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "cause" in item and "effect" in item:
                        edges.append(CausalEdge(
                            cause=str(item["cause"]),
                            effect=str(item["effect"]),
                            strength=float(item.get("strength", 0.5)),
                            polarity=str(item.get("polarity", "+")),
                            personal=False
                        ))
            return edges

        except Exception as e:
            print(f"[PKF-因果图] LLM 构建失败: {e}")
            return self._fallback_build()

    def _filter_by_facts(self):
        """用个人事实过滤不相关的因果边"""
        fact_keywords = set()
        for f in self.facts:
            fact_keywords.add(f.obj)
            fact_keywords.add(f.relation)

        # 不做硬过滤，而是降低不相关边的 strength
        for edge in self.edges:
            has_personal_anchor = any(
                kw in edge.cause or kw in edge.effect
                for kw in fact_keywords if len(kw) > 1
            )
            if has_personal_anchor:
                edge.personal = True
                edge.strength = min(1.0, edge.strength * 1.2)
            else:
                edge.strength *= 0.7

    def _enrich_with_facts(self):
        """用个人事实扩展因果图"""
        for f in self.facts:
            if f.relation.startswith("认识"):
                # 人脉关系 → 信息渠道
                self.edges.append(CausalEdge(
                    cause=f"联系{f.obj}",
                    effect="获取内部信息",
                    strength=0.7,
                    polarity="+",
                    personal=True
                ))
            elif f.relation == "顾虑" or f.relation == "担心":
                self.edges.append(CausalEdge(
                    cause=self.option,
                    effect=f"加剧{f.obj}",
                    strength=0.6,
                    polarity="-",
                    personal=True
                ))

    def _fallback_build(self) -> List[CausalEdge]:
        """规则兜底"""
        return [
            CausalEdge(self.option, "环境变化", 0.8, "+"),
            CausalEdge("环境变化", "需要适应期", 0.7, "-"),
            CausalEdge("适应期", "能力提升", 0.6, "+"),
            CausalEdge(self.option, "机会成本", 0.7, "-"),
        ]

    def get_chains(self, max_depth: int = 4) -> List[List[CausalEdge]]:
        """提取因果链（从根节点到叶节点的路径）"""
        # 找根节点（只作为 cause 出现，不作为 effect）
        effects = {e.effect for e in self.edges}
        causes = {e.cause for e in self.edges}
        roots = causes - effects

        chains: List[List[CausalEdge]] = []
        for root in roots:
            self._dfs(root, [], chains, max_depth)

        # 按 strength 排序
        chains.sort(key=lambda c: sum(e.strength for e in c) / max(len(c), 1), reverse=True)
        return chains[:8]

    def _dfs(self, node: str, path: List[CausalEdge],
             chains: List[List[CausalEdge]], max_depth: int):
        if len(path) >= max_depth:
            if path:
                chains.append(list(path))
            return

        next_edges = [e for e in self.edges if e.cause == node]
        if not next_edges:
            if path:
                chains.append(list(path))
            return

        for edge in next_edges:
            path.append(edge)
            self._dfs(edge.effect, path, chains, max_depth)
            path.pop()


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 3：个性化条件生成
# ═══════════════════════════════════════════════════════════════════════════

class PersonalizedTimelineGenerator:
    """沿因果链条件生成时间线，每个事件锚定在具体的因果关系和个人事实上"""

    EVENT_PROMPT = """你是用户的个人决策推演引擎。请根据以下因果链和个人事实，生成第 {month} 个月的具体事件。

决策问题：{question}
决策选项：{option}

本月需要体现的因果链：
{causal_chain}

用户个人事实（请在事件中引用具体信息）：
{facts}

之前已发生的事件：
{previous_events}

要求：
1. 事件必须具体，引用用户的真实人名、数字、情况
2. 事件必须沿着因果链的逻辑推进
3. 输出 JSON：{{"month":{month},"event":"具体事件描述","impact":{{"健康":0.0,"财务":0.0,"社交":0.0,"情绪":0.0,"学习":0.0,"时间":0.0}},"probability":0.8,"causal_basis":"基于哪条因果链"}}
只输出 JSON，不要解释。"""

    def __init__(self, user_id: str, question: str, option: str,
                 facts: List[PersonalFact], causal_graph: CausalReasoningGraph):
        self.user_id = user_id
        self.question = question
        self.option = option
        self.facts = facts
        self.causal_graph = causal_graph
        self.generated_events: List[Dict[str, Any]] = []

    async def generate_timeline(self, num_months: int = 12) -> List[Dict[str, Any]]:
        """逐月生成时间线，每月沿不同因果链推进"""
        chains = self.causal_graph.get_chains()
        if not chains:
            return []

        self.generated_events = []
        facts_text = "\n".join([f"- {f.to_text()}" for f in self.facts[:10]])

        for month in range(1, num_months + 1):
            # 选择本月的因果链（轮流使用不同链）
            chain_idx = (month - 1) % len(chains)
            chain = chains[chain_idx]
            chain_text = " -> ".join([
                f"{e.cause}({e.polarity}{e.strength:.1f}){e.effect}"
                for e in chain
            ])

            prev_text = "\n".join([
                f"- 第{e['month']}月：{e['event']}"
                for e in self.generated_events[-3:]
            ]) if self.generated_events else "（尚无）"

            event = await self._generate_single_event(
                month, chain_text, facts_text, prev_text
            )
            if event:
                self.generated_events.append(event)

        return self.generated_events

    async def _generate_single_event(self, month: int, chain_text: str,
                                      facts_text: str, prev_text: str) -> Optional[Dict]:
        """生成单个月的事件"""
        import asyncio
        try:
            from backend.lora.lora_model_manager import lora_manager
            prompt = self.EVENT_PROMPT.format(
                month=month, question=self.question, option=self.option,
                causal_chain=chain_text, facts=facts_text, previous_events=prev_text
            )
            # 优先用 LoRA 模型
            if lora_manager.has_lora_model(self.user_id):
                response = await asyncio.to_thread(
                    lora_manager.generate, self.user_id, prompt, 200, 0.3
                )
            else:
                from backend.llm.llm_service import get_llm_service
                llm = get_llm_service()
                if llm and llm.enabled:
                    response = llm.chat([
                        {"role": "system", "content": "你是决策推演引擎，只输出 JSON。"},
                        {"role": "user", "content": prompt}
                    ], temperature=0.3)
                else:
                    return self._fallback_event(month)

            if not response:
                return self._fallback_event(month)

            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            m = re.search(r'\{.*?\}', response, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                if "month" in data and "event" in data:
                    data["month"] = month
                    return data

            return self._fallback_event(month)

        except Exception as e:
            print(f"[PKF-生成] 第{month}月生成失败: {e}")
            return self._fallback_event(month)

    def _fallback_event(self, month: int) -> Dict:
        return {
            "month": month,
            "event": f"第{month}个月，{self.option}的推进进入新阶段",
            "impact": {"健康": 0.0, "财务": 0.0, "社交": 0.0, "情绪": 0.0, "学习": 0.0, "时间": 0.0},
            "probability": 0.7,
            "causal_basis": "fallback"
        }


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 4：反事实校验
# ═══════════════════════════════════════════════════════════════════════════

class CounterfactualVerifier:
    """反事实校验：识别关键转折点，标记重要节点"""

    CF_PROMPT = """如果第 {month} 个月的事件"{event}"没有发生，后续最可能的替代走向是什么？
请用一句话描述替代走向，并评估与原走向的差异程度（0-1，1=完全不同）。
输出 JSON：{{"alternative":"替代走向描述","divergence":0.7}}
只输出 JSON。"""

    @staticmethod
    async def verify(user_id: str, timeline: List[Dict]) -> List[Dict]:
        """对时间线中的关键节点做反事实校验，标记重要程度"""
        import asyncio
        if not timeline or len(timeline) < 3:
            return timeline

        # 只校验前 4 个节点（节省推理时间）
        for event in timeline[:4]:
            try:
                from backend.llm.llm_service import get_llm_service
                llm = get_llm_service()
                if not llm or not llm.enabled:
                    event["importance"] = 0.5
                    continue

                prompt = CounterfactualVerifier.CF_PROMPT.format(
                    month=event["month"], event=event["event"]
                )
                response = llm.chat([
                    {"role": "system", "content": "只输出 JSON。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.2)

                if response:
                    response = re.sub(r"```json\s*", "", response)
                    response = re.sub(r"```\s*", "", response)
                    m = re.search(r'\{.*?\}', response, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        event["importance"] = float(data.get("divergence", 0.5))
                        event["counterfactual"] = data.get("alternative", "")
                    else:
                        event["importance"] = 0.5
                else:
                    event["importance"] = 0.5

            except Exception:
                event["importance"] = 0.5

        # 未校验的节点给默认值
        for event in timeline[4:]:
            event["importance"] = 0.4

        return timeline


# ═══════════════════════════════════════════════════════════════════════════
# 统一入口：PKF-DS 完整推演流水线
# ═══════════════════════════════════════════════════════════════════════════

async def pkf_decision_simulate(
    user_id: str,
    question: str,
    option_title: str,
    option_desc: str = "",
    num_months: int = 12,
    enable_counterfactual: bool = True
) -> Dict[str, Any]:
    """
    PKF-DS 完整推演流水线

    Args:
        user_id: 用户 ID
        question: 决策问题
        option_title: 选项标题
        option_desc: 选项描述
        num_months: 推演月数
        enable_counterfactual: 是否启用反事实校验

    Returns:
        {
            "facts": [...],           # 抽取的个人事实
            "causal_edges": [...],    # 因果推理图
            "causal_chains": [...],   # 因果链
            "timeline": [...],        # 时间线事件
            "key_turning_points": [...] # 关键转折点
        }
    """
    print(f"\n{'='*60}")
    print(f"[PKF-DS] 开始个性化决策推演")
    print(f"  用户: {user_id}")
    print(f"  问题: {question}")
    print(f"  选项: {option_title}")
    print(f"{'='*60}")

    # 阶段 1：抽取个人事实
    print("\n[阶段1] 多源个人知识抽取...")
    extractor = PersonalFactExtractor(user_id)
    facts = extractor.extract_all()
    print(f"  抽取了 {len(facts)} 条个人事实")

    # 阶段 2：构建因果推理图
    print("\n[阶段2] 因果推理图构建...")
    causal_graph = CausalReasoningGraph(question, option_title, facts)
    edges = causal_graph.build()
    chains = causal_graph.get_chains()
    print(f"  构建了 {len(edges)} 条因果边，{len(chains)} 条因果链")

    # 阶段 3：个性化条件生成
    print(f"\n[阶段3] 个性化条件生成（{num_months}个月）...")
    generator = PersonalizedTimelineGenerator(
        user_id, question, option_title, facts, causal_graph
    )
    timeline = await generator.generate_timeline(num_months)
    print(f"  生成了 {len(timeline)} 个时间线事件")

    # 阶段 4：反事实校验
    key_points = []
    if enable_counterfactual and timeline:
        print("\n[阶段4] 反事实校验...")
        timeline = await CounterfactualVerifier.verify(user_id, timeline)
        key_points = [e for e in timeline if e.get("importance", 0) > 0.6]
        print(f"  识别了 {len(key_points)} 个关键转折点")

    print(f"\n[PKF-DS] 推演完成")
    print(f"{'='*60}\n")

    return {
        "facts": [f.to_dict() for f in facts],
        "causal_edges": [e.to_dict() for e in edges],
        "causal_chains": [
            [e.to_dict() for e in chain] for chain in chains
        ],
        "timeline": timeline,
        "key_turning_points": key_points
    }
