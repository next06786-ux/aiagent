"""
协作式智慧洞察Agent - 完整实现
三层混合AI架构 + 多Agent协作

每个Agent都具备：
1. 三层混合AI架构（规则引擎 + 机器学习 + LLM）
2. 多Agent协作能力（共享记忆、任务链传递、状态广播）
3. 独立的领域专业知识

作者: AI System
版本: 2.0
日期: 2026-04-18
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time

from backend.insights.multi_agent_system import CollaborativeAgent, AgentStatus
from backend.llm.llm_service import LLMService


# ==================== 人际关系Agent ====================

class RelationshipInsightAgent(CollaborativeAgent):
    """
    人际关系洞察Agent
    
    专注领域：
    - 关系网络分析
    - 社交模式识别
    - 关系质量评估
    - 人脉资源优化
    """
    
    def __init__(self, user_id: str):
        super().__init__(name="relationship", agent_type="人际关系")
        self.user_id = user_id
        self.llm_service = None
        
        try:
            self.llm_service = LLMService()
        except Exception as e:
            print(f"  ⚠️ LLM服务初始化失败: {e}")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行人际关系分析"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始执行任务")
        print(f"{'='*60}\n")
        
        query = input_data.get("query", "分析我的人际关系网络")
        hybrid_data = input_data.get("hybrid_data", {})
        
        self.status = AgentStatus.WORKING
        if self.gateway:
            self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.WORKING)
        
        start_time = datetime.now()
        layer_timing = {}
        
        try:
            # 分离数据
            rag_data, neo4j_data = self._split_hybrid_data(hybrid_data)
            
            # 第1层：规则引擎
            print("📊 第1层：规则引擎分析...")
            layer1_start = datetime.now()
            key_findings = self._layer1_rule_engine(rag_data, neo4j_data)
            layer_timing["layer1_ms"] = (datetime.now() - layer1_start).total_seconds() * 1000
            print(f"  ✓ 完成，发现 {len(key_findings)} 个关键点，耗时 {layer_timing['layer1_ms']:.2f}ms")
            
            # 第2层：机器学习评估
            print("🤖 第2层：机器学习评估...")
            layer2_start = datetime.now()
            ml_evaluation = self._layer2_ml_evaluation(rag_data, neo4j_data, key_findings)
            layer_timing["layer2_ms"] = (datetime.now() - layer2_start).total_seconds() * 1000
            print(f"  ✓ 完成，风险等级: {ml_evaluation['risk_level']}，耗时 {layer_timing['layer2_ms']:.2f}ms")
            
            # 第3层：LLM深度解读
            print("🧠 第3层：LLM深度解读...")
            layer3_start = datetime.now()
            llm_output = self._layer3_llm_deep_insight(query, rag_data, neo4j_data, key_findings, ml_evaluation)
            layer_timing["layer3_ms"] = (datetime.now() - layer3_start).total_seconds() * 1000
            print(f"  ✓ 完成，生成 {len(llm_output.get('recommendations', []))} 条建议，耗时 {layer_timing['layer3_ms']:.2f}ms")
            
            # 构建输出
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": llm_output.get("summary", ""),
                "key_findings": key_findings,
                "ml_evaluation": ml_evaluation,
                "recommendations": llm_output.get("recommendations", []),
                "confidence_score": self._calculate_confidence(rag_data, neo4j_data),
                "data_sources": {
                    "rag_nodes": len(rag_data.get('nodes', [])),
                    "neo4j_nodes": len(neo4j_data.get('nodes', []))
                },
                "layer_timing": layer_timing
            }
            
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            print(f"\n✅ [{self.name}] 任务完成，总耗时: {sum(layer_timing.values()):.2f}ms\n")
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 任务失败: {e}")
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            raise
    
    def _split_hybrid_data(self, hybrid_data: Dict) -> tuple:
        """分离混合数据 - 支持直接 Neo4j/FAISS 格式"""
        # 优先使用直接查询格式（nodes/relationships）
        if hybrid_data.get('nodes'):
            all_nodes = hybrid_data.get('nodes', [])
            relationships = hybrid_data.get('relationships', [])
            
            rag_data = {
                "nodes": [n for n in all_nodes if n.get("source") in ["faiss", "vector", "hybrid"]],
                "relationships": [],
                "influence_summary": hybrid_data.get("influence_summary", {})
            }
            neo4j_data = {
                "nodes": [n for n in all_nodes if n.get("source") in ["neo4j", "graph", "hybrid"]],
                "relationships": relationships
            }
            return rag_data, neo4j_data
        
        # 兼容旧的 retrieval_context 格式
        results = hybrid_data.get('results', [])
        nodes = []
        for result in results:
            nodes.append({
                "id": result.get("id", ""),
                "name": result.get("content", ""),
                "type": result.get("node_type", "unknown"),
                "category": result.get("category", "unknown"),
                "confidence": result.get("confidence", 0.5),
                "source": result.get("source", "unknown"),
                "metadata": result.get("metadata", {})
            })
        
        rag_data = {
            "nodes": [n for n in nodes if n.get("source") in ["vector", "hybrid"]],
            "relationships": [],
            "influence_summary": {}
        }
        neo4j_data = {
            "nodes": [n for n in nodes if n.get("source") in ["graph", "hybrid"]],
            "relationships": []
        }
        return rag_data, neo4j_data
    
    def _layer1_rule_engine(self, rag_data: Dict, neo4j_data: Dict) -> List[Dict]:
        """第1层：规则引擎 - 人际关系分析"""
        findings = []
        
        # 人物统计
        person_nodes = [n for n in neo4j_data.get("nodes", []) if n.get("type") == "Person"]
        total_people = len(person_nodes)
        person_names = [n.get('name', '') for n in person_nodes if n.get('name')]
        
        if total_people >= 20:
            findings.append({
                "type": "network_size",
                "title": f"关系网络规模: {total_people} 人（丰富）",
                "description": f"你的人际网络包含{total_people}位重要人物，网络规模较为丰富",
                "importance": "high",
                "count": total_people,
                "people_sample": person_names[:5]
            })
        elif total_people >= 10:
            findings.append({
                "type": "network_size",
                "title": f"关系网络规模: {total_people} 人（适中）",
                "description": f"你的人际网络包含{total_people}位重要人物，可以考虑进一步拓展",
                "importance": "medium",
                "count": total_people,
                "people_sample": person_names[:5]
            })
        else:
            findings.append({
                "type": "network_size",
                "title": f"关系网络规模: {total_people} 人（较小）",
                "description": f"建议主动拓展人际关系，增加社交机会",
                "importance": "high",
                "count": total_people,
                "people_sample": person_names
            })
        
        return findings
    
    def _layer2_ml_evaluation(self, rag_data: Dict, neo4j_data: Dict, key_findings: List) -> Dict:
        """第2层：机器学习评估"""
        node_count = len(neo4j_data.get('nodes', []))
        
        risk_level = "low" if node_count >= 15 else ("medium" if node_count >= 10 else "high")
        trend = "rising" if node_count > 30 else ("stable" if node_count >= 10 else "declining")
        match_score = min(node_count * 3, 100)
        
        return {
            "risk_level": risk_level,
            "trend": trend,
            "match_score": match_score,
            "model_version": "relationship_v1.0"
        }
    
    def _layer3_llm_deep_insight(self, query: str, rag_data: Dict, neo4j_data: Dict, 
                                  key_findings: List, ml_evaluation: Dict) -> Dict:
        """第3层：LLM深度解读"""
        if not self.llm_service:
            return self._generate_fallback_output(key_findings, ml_evaluation)
        
        prompt = self._build_prompt(query, key_findings, ml_evaluation, "人际关系", neo4j_data)
        
        try:
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            # 检查是否是错误响应
            if response.startswith("大模型调用失败") or response.startswith("大模型未配置"):
                print(f"  ⚠️ LLM返回错误: {response[:100]}")
                return self._generate_fallback_output(key_findings, ml_evaluation)
            result = self._parse_llm_response(response)
            print(f"  [调试] 解析结果 recommendations数量: {len(result.get('recommendations', []))}")
            return result
        except Exception as e:
            import traceback
            print(f"  ⚠️ LLM调用失败: {e}")
            traceback.print_exc()
            return self._generate_fallback_output(key_findings, ml_evaluation)
    
    def _build_prompt(self, query: str, key_findings: List, ml_evaluation: Dict, domain: str, neo4j_data: Dict = None) -> str:
        """构建LLM prompt"""
        findings_text = "\n".join([f"- {f['title']}: {f['description']}" for f in key_findings])
        
        # 提取人物信息
        people_info = ""
        if neo4j_data:
            person_nodes = [n for n in neo4j_data.get("nodes", []) if n.get("type") == "Person"]
            if person_nodes:
                categories = {}
                for node in person_nodes:
                    cat = node.get('category', 'unknown')
                    if cat not in categories:
                        categories[cat] = []
                    name = node.get('name', '')
                    if name:
                        categories[cat].append(name)
                
                cat_display = {
                    'friends': '朋友', 'colleagues': '同事', 'family': '家人',
                    'mentors': '导师', 'classmates': '同学', 'close_friends': '密友', 'unknown': '其他'
                }
                people_info = f"\n【人际关系详情】\n总人数: {len(person_nodes)} 人\n"
                for cat, names in categories.items():
                    display = cat_display.get(cat, cat)
                    people_info += f"{display}({len(names)}人): {', '.join(names[:8])}\n"
        
        return f"""你是专业的{domain}分析师。基于以下数据生成深度洞察。

【用户查询】{query}

【关键发现】
{findings_text}

【ML评估】
风险等级: {ml_evaluation['risk_level']}
发展趋势: {ml_evaluation['trend']}
匹配度: {ml_evaluation['match_score']}/100
{people_info}
请以JSON格式返回：
{{
    "summary": "200-300字的深度摘要（必须基于实际数据，如人数、分类等）",
    "recommendations": [
        {{
            "priority": "high/medium/low",
            "category": "类别",
            "action": "具体行动",
            "expected_impact": "预期影响",
            "timeline": "时间线",
            "reasoning": "推理依据"
        }}
    ]
}}
"""
    
    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应"""
        import re
        import json as json_module

        # 先尝试直接解析
        try:
            return json_module.loads(response.strip())
        except:
            pass

        # 提取 markdown 代码块中的 JSON
        try:
            code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_match:
                return json_module.loads(code_match.group(1))
        except:
            pass

        # 找最外层的 JSON 对象
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                result = json_module.loads(response[start:end+1])
                if isinstance(result, dict):
                    return result
        except:
            pass

        print(f"  LLM响应解析失败，原始响应前200字: {response[:200]}")
        return {"summary": response[:500], "recommendations": []}

    
    def _generate_fallback_output(self, key_findings: List, ml_evaluation: Dict) -> Dict:
        """生成降级输出"""
        return {
            "summary": f"基于数据分析，识别到{len(key_findings)}个关键发现。风险等级{ml_evaluation['risk_level']}。",
            "recommendations": [
                {
                    "priority": "high",
                    "category": "改进建议",
                    "action": "根据关键发现采取相应行动",
                    "expected_impact": "改善整体状况",
                    "timeline": "1-3个月",
                    "reasoning": "基于规则引擎分析"
                }
            ]
        }
    
    def _calculate_confidence(self, rag_data: Dict, neo4j_data: Dict) -> float:
        """计算置信度"""
        rag_score = min(len(rag_data.get('nodes', [])) / 10, 1.0) * 0.5
        neo4j_score = min(len(neo4j_data.get('nodes', [])) / 20, 1.0) * 0.5
        return rag_score + neo4j_score


# ==================== 教育升学Agent ====================

class EducationInsightAgent(CollaborativeAgent):
    """教育升学洞察Agent - 三层混合AI架构"""
    
    def __init__(self, user_id: str):
        super().__init__(name="education", agent_type="教育升学")
        self.user_id = user_id
        self.llm_service = None
        
        try:
            self.llm_service = LLMService()
        except Exception as e:
            print(f"  ⚠️ LLM服务初始化失败: {e}")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行教育升学分析 - 三层混合AI架构"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始执行任务")
        print(f"{'='*60}")
        
        query = input_data.get("query", "分析我的升学路径")
        layer_timing = {}
        
        try:
            # 获取共享记忆空间的数据
            if self.gateway and self.gateway.shared_memory:
                hybrid_data = self.gateway.shared_memory.get_shared_context()
            else:
                hybrid_data = {"results": []}
            
            rag_data, neo4j_data = self._split_hybrid_data(hybrid_data)
            
            # 第1层：规则引擎
            print(f"\n📊 第1层：规则引擎分析...")
            start = time.time()
            key_findings = self._layer1_rule_engine(rag_data, neo4j_data)
            layer_timing['layer1_ms'] = (time.time() - start) * 1000
            print(f"✓ 完成，发现 {len(key_findings)} 个关键点，耗时 {layer_timing['layer1_ms']:.2f}ms")
            
            # 第2层：机器学习
            print(f"\n🤖 第2层：机器学习评估...")
            start = time.time()
            ml_evaluation = self._layer2_ml_evaluation(rag_data, neo4j_data, key_findings)
            layer_timing['layer2_ms'] = (time.time() - start) * 1000
            print(f"✓ 完成，风险等级: {ml_evaluation['risk_level']}，耗时 {layer_timing['layer2_ms']:.2f}ms")
            
            # 第3层：LLM深度解读
            print(f"\n🧠 第3层：LLM深度解读...")
            start = time.time()
            llm_output = self._layer3_llm_deep_insight(query, rag_data, neo4j_data, key_findings, ml_evaluation)
            layer_timing['layer3_ms'] = (time.time() - start) * 1000
            print(f"✓ 完成，生成 {len(llm_output.get('recommendations', []))} 条建议，耗时 {layer_timing['layer3_ms']:.2f}ms")
            
            # 组装输出
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": llm_output.get("summary", "教育升学分析完成"),
                "key_findings": key_findings,
                "ml_evaluation": ml_evaluation,
                "recommendations": llm_output.get("recommendations", []),
                "confidence_score": self._calculate_confidence(rag_data, neo4j_data),
                "data_sources": {
                    "rag_nodes": len(rag_data.get('nodes', [])),
                    "neo4j_nodes": len(neo4j_data.get('nodes', []))
                },
                "layer_timing": layer_timing
            }
            
            # 更新状态
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            print(f"\n✅ [{self.name}] 任务完成，总耗时: {sum(layer_timing.values()):.2f}ms\n")
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 任务失败: {e}")
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            raise
    
    def _split_hybrid_data(self, hybrid_data: Dict) -> tuple:
        """分离混合数据"""
        results = hybrid_data.get('results', [])
        nodes = []
        for result in results:
            nodes.append({
                "id": result.get("id", ""),
                "name": result.get("content", ""),
                "type": result.get("node_type", "unknown"),
                "category": result.get("category", "unknown"),
                "confidence": result.get("confidence", 0.5),
                "source": result.get("source", "unknown"),
                "metadata": result.get("metadata", {})
            })
        
        rag_data = {
            "nodes": [n for n in nodes if n.get("source") in ["vector", "hybrid"]],
            "relationships": [],
            "influence_summary": {}
        }
        neo4j_data = {
            "nodes": [n for n in nodes if n.get("source") in ["graph", "hybrid"]],
            "relationships": []
        }
        return rag_data, neo4j_data
    
    def _layer1_rule_engine(self, rag_data: Dict, neo4j_data: Dict) -> List[Dict]:
        """第1层：规则引擎 - 教育升学分析"""
        findings = []
        
        # 院校统计
        school_nodes = [n for n in neo4j_data.get("nodes", []) if n.get("type") == "School"]
        total_schools = len(school_nodes)
        
        if total_schools >= 10:
            findings.append({
                "type": "school_knowledge",
                "title": f"院校了解: {total_schools} 所（丰富）",
                "description": f"你对{total_schools}所院校有了解，知识储备丰富",
                "importance": "high"
            })
        elif total_schools >= 5:
            findings.append({
                "type": "school_knowledge",
                "title": f"院校了解: {total_schools} 所（适中）",
                "description": f"你对{total_schools}所院校有了解，可以进一步拓展",
                "importance": "medium"
            })
        else:
            findings.append({
                "type": "school_knowledge",
                "title": f"院校了解: {total_schools} 所（较少）",
                "description": f"建议多了解目标院校，增加选择机会",
                "importance": "high"
            })
        
        return findings
    
    def _layer2_ml_evaluation(self, rag_data: Dict, neo4j_data: Dict, key_findings: List) -> Dict:
        """第2层：机器学习评估"""
        node_count = len(neo4j_data.get('nodes', []))
        
        risk_level = "low" if node_count >= 10 else ("medium" if node_count >= 5 else "high")
        trend = "rising" if node_count > 15 else ("stable" if node_count >= 5 else "declining")
        match_score = min(node_count * 5, 100)
        
        return {
            "risk_level": risk_level,
            "trend": trend,
            "match_score": match_score,
            "model_version": "education_v1.0"
        }
    
    def _layer3_llm_deep_insight(self, query: str, rag_data: Dict, neo4j_data: Dict, 
                                  key_findings: List, ml_evaluation: Dict) -> Dict:
        """第3层：LLM深度解读"""
        if not self.llm_service:
            return self._generate_fallback_output(key_findings, ml_evaluation)
        
        prompt = self._build_prompt(query, key_findings, ml_evaluation, "教育升学")
        
        try:
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"  ⚠️ LLM调用失败: {e}")
            return self._generate_fallback_output(key_findings, ml_evaluation)
    
    def _build_prompt(self, query: str, key_findings: List, ml_evaluation: Dict, domain: str) -> str:
        """构建LLM prompt"""
        findings_text = "\n".join([f"- {f['title']}: {f['description']}" for f in key_findings])
        
        return f"""你是专业的{domain}分析师。基于以下数据生成深度洞察。

【用户查询】{query}

【关键发现】
{findings_text}

【ML评估】
风险等级: {ml_evaluation['risk_level']}
发展趋势: {ml_evaluation['trend']}
匹配度: {ml_evaluation['match_score']}/100

请以JSON格式返回：
{{
    "summary": "200-300字的深度摘要",
    "recommendations": [
        {{
            "priority": "high/medium/low",
            "category": "类别",
            "action": "具体行动",
            "expected_impact": "预期影响",
            "timeline": "时间线",
            "reasoning": "推理依据"
        }}
    ]
}}
"""
    
    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"summary": response[:500], "recommendations": []}
    
    def _generate_fallback_output(self, key_findings: List, ml_evaluation: Dict) -> Dict:
        """生成降级输出"""
        return {
            "summary": f"基于数据分析，识别到{len(key_findings)}个关键发现。风险等级{ml_evaluation['risk_level']}。",
            "recommendations": [
                {
                    "priority": "high",
                    "category": "改进建议",
                    "action": "根据关键发现采取相应行动",
                    "expected_impact": "改善整体状况",
                    "timeline": "1-3个月",
                    "reasoning": "基于规则引擎分析"
                }
            ]
        }
    
    def _calculate_confidence(self, rag_data: Dict, neo4j_data: Dict) -> float:
        """计算置信度"""
        rag_score = min(len(rag_data.get('nodes', [])) / 10, 1.0) * 0.5
        neo4j_score = min(len(neo4j_data.get('nodes', [])) / 20, 1.0) * 0.5
        return rag_score + neo4j_score


# ==================== 职业规划Agent ====================

class CareerInsightAgent(CollaborativeAgent):
    """职业规划洞察Agent - 三层混合AI架构"""
    
    def __init__(self, user_id: str):
        super().__init__(name="career", agent_type="职业规划")
        self.user_id = user_id
        self.llm_service = None
        
        try:
            self.llm_service = LLMService()
        except Exception as e:
            print(f"  ⚠️ LLM服务初始化失败: {e}")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行职业规划分析 - 三层混合AI架构"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始执行任务")
        print(f"{'='*60}")
        
        query = input_data.get("query", "分析我的职业发展路径")
        layer_timing = {}
        
        try:
            # 获取共享记忆空间的数据
            if self.gateway and self.gateway.shared_memory:
                hybrid_data = self.gateway.shared_memory.get_shared_context()
            else:
                hybrid_data = {"results": []}
            
            rag_data, neo4j_data = self._split_hybrid_data(hybrid_data)
            
            # 第1层：规则引擎
            print(f"\n📊 第1层：规则引擎分析...")
            start = time.time()
            key_findings = self._layer1_rule_engine(rag_data, neo4j_data)
            layer_timing['layer1_ms'] = (time.time() - start) * 1000
            print(f"✓ 完成，发现 {len(key_findings)} 个关键点，耗时 {layer_timing['layer1_ms']:.2f}ms")
            
            # 第2层：机器学习
            print(f"\n🤖 第2层：机器学习评估...")
            start = time.time()
            ml_evaluation = self._layer2_ml_evaluation(rag_data, neo4j_data, key_findings)
            layer_timing['layer2_ms'] = (time.time() - start) * 1000
            print(f"✓ 完成，风险等级: {ml_evaluation['risk_level']}，耗时 {layer_timing['layer2_ms']:.2f}ms")
            
            # 第3层：LLM深度解读
            print(f"\n🧠 第3层：LLM深度解读...")
            start = time.time()
            llm_output = self._layer3_llm_deep_insight(query, rag_data, neo4j_data, key_findings, ml_evaluation)
            layer_timing['layer3_ms'] = (time.time() - start) * 1000
            print(f"✓ 完成，生成 {len(llm_output.get('recommendations', []))} 条建议，耗时 {layer_timing['layer3_ms']:.2f}ms")
            
            # 组装输出
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": llm_output.get("summary", "职业规划分析完成"),
                "key_findings": key_findings,
                "ml_evaluation": ml_evaluation,
                "recommendations": llm_output.get("recommendations", []),
                "confidence_score": self._calculate_confidence(rag_data, neo4j_data),
                "data_sources": {
                    "rag_nodes": len(rag_data.get('nodes', [])),
                    "neo4j_nodes": len(neo4j_data.get('nodes', []))
                },
                "layer_timing": layer_timing
            }
            
            # 更新状态
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            print(f"\n✅ [{self.name}] 任务完成，总耗时: {sum(layer_timing.values()):.2f}ms\n")
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 任务失败: {e}")
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            raise
    
    def _split_hybrid_data(self, hybrid_data: Dict) -> tuple:
        """分离混合数据"""
        results = hybrid_data.get('results', [])
        nodes = []
        for result in results:
            nodes.append({
                "id": result.get("id", ""),
                "name": result.get("content", ""),
                "type": result.get("node_type", "unknown"),
                "category": result.get("category", "unknown"),
                "confidence": result.get("confidence", 0.5),
                "source": result.get("source", "unknown"),
                "metadata": result.get("metadata", {})
            })
        
        rag_data = {
            "nodes": [n for n in nodes if n.get("source") in ["vector", "hybrid"]],
            "relationships": [],
            "influence_summary": {}
        }
        neo4j_data = {
            "nodes": [n for n in nodes if n.get("source") in ["graph", "hybrid"]],
            "relationships": []
        }
        return rag_data, neo4j_data
    
    def _layer1_rule_engine(self, rag_data: Dict, neo4j_data: Dict) -> List[Dict]:
        """第1层：规则引擎 - 职业规划分析"""
        findings = []
        
        # 岗位和公司统计
        job_nodes = [n for n in neo4j_data.get("nodes", []) if n.get("type") == "Job"]
        company_nodes = [n for n in neo4j_data.get("nodes", []) if n.get("type") == "Organization"]
        total_jobs = len(job_nodes)
        total_companies = len(company_nodes)
        
        if total_jobs >= 10:
            findings.append({
                "type": "job_knowledge",
                "title": f"岗位了解: {total_jobs} 个（丰富）",
                "description": f"你对{total_jobs}个岗位有了解，职业视野开阔",
                "importance": "high"
            })
        elif total_jobs >= 5:
            findings.append({
                "type": "job_knowledge",
                "title": f"岗位了解: {total_jobs} 个（适中）",
                "description": f"你对{total_jobs}个岗位有了解，可以进一步探索",
                "importance": "medium"
            })
        else:
            findings.append({
                "type": "job_knowledge",
                "title": f"岗位了解: {total_jobs} 个（较少）",
                "description": f"建议多了解不同岗位，拓宽职业选择",
                "importance": "high"
            })
        
        if total_companies > 0:
            findings.append({
                "type": "company_knowledge",
                "title": f"公司了解: {total_companies} 家",
                "description": f"你对{total_companies}家公司有了解",
                "importance": "medium"
            })
        
        return findings
    
    def _layer2_ml_evaluation(self, rag_data: Dict, neo4j_data: Dict, key_findings: List) -> Dict:
        """第2层：机器学习评估"""
        node_count = len(neo4j_data.get('nodes', []))
        
        risk_level = "low" if node_count >= 15 else ("medium" if node_count >= 8 else "high")
        trend = "rising" if node_count > 20 else ("stable" if node_count >= 8 else "declining")
        match_score = min(node_count * 4, 100)
        
        return {
            "risk_level": risk_level,
            "trend": trend,
            "match_score": match_score,
            "model_version": "career_v1.0"
        }
    
    def _layer3_llm_deep_insight(self, query: str, rag_data: Dict, neo4j_data: Dict, 
                                  key_findings: List, ml_evaluation: Dict) -> Dict:
        """第3层：LLM深度解读"""
        if not self.llm_service:
            return self._generate_fallback_output(key_findings, ml_evaluation)
        
        prompt = self._build_prompt(query, key_findings, ml_evaluation, "职业规划")
        
        try:
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"  ⚠️ LLM调用失败: {e}")
            return self._generate_fallback_output(key_findings, ml_evaluation)
    
    def _build_prompt(self, query: str, key_findings: List, ml_evaluation: Dict, domain: str) -> str:
        """构建LLM prompt"""
        findings_text = "\n".join([f"- {f['title']}: {f['description']}" for f in key_findings])
        
        return f"""你是专业的{domain}分析师。基于以下数据生成深度洞察。

【用户查询】{query}

【关键发现】
{findings_text}

【ML评估】
风险等级: {ml_evaluation['risk_level']}
发展趋势: {ml_evaluation['trend']}
匹配度: {ml_evaluation['match_score']}/100

请以JSON格式返回：
{{
    "summary": "200-300字的深度摘要",
    "recommendations": [
        {{
            "priority": "high/medium/low",
            "category": "类别",
            "action": "具体行动",
            "expected_impact": "预期影响",
            "timeline": "时间线",
            "reasoning": "推理依据"
        }}
    ]
}}
"""
    
    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"summary": response[:500], "recommendations": []}
    
    def _generate_fallback_output(self, key_findings: List, ml_evaluation: Dict) -> Dict:
        """生成降级输出"""
        return {
            "summary": f"基于数据分析，识别到{len(key_findings)}个关键发现。风险等级{ml_evaluation['risk_level']}。",
            "recommendations": [
                {
                    "priority": "high",
                    "category": "改进建议",
                    "action": "根据关键发现采取相应行动",
                    "expected_impact": "改善整体状况",
                    "timeline": "1-3个月",
                    "reasoning": "基于规则引擎分析"
                }
            ]
        }
    
    def _calculate_confidence(self, rag_data: Dict, neo4j_data: Dict) -> float:
        """计算置信度"""
        rag_score = min(len(rag_data.get('nodes', [])) / 10, 1.0) * 0.5
        neo4j_score = min(len(neo4j_data.get('nodes', [])) / 20, 1.0) * 0.5
        return rag_score + neo4j_score


# ==================== 跨领域综合分析Agent ====================

class CrossDomainAnalysisAgent(CollaborativeAgent):
    """
    跨领域综合分析Agent
    
    核心功能：
    1. 整合三个领域Agent的输出
    2. 发现跨领域的关联和模式
    3. 生成综合性的战略建议
    4. 识别领域间的协同效应和冲突
    
    示例场景：
    - "我的人际关系如何影响职业发展？"
    - "教育背景和人脉资源如何协同提升职业竞争力？"
    - "如何平衡学业、人际关系和职业规划？"
    """
    
    def __init__(self, user_id: str):
        super().__init__(name="cross_domain", agent_type="跨领域综合分析")
        self.user_id = user_id
        self.llm_service = None
        
        try:
            self.llm_service = LLMService()
        except Exception as e:
            print(f"  ⚠️ LLM服务初始化失败: {e}")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行跨领域综合分析
        
        Args:
            input_data: {
                "query": 用户查询,
                "hybrid_data": 共享的混合检索数据,
                "prev_agent_output": 上一个Agent的输出,
                "context": 任务链上下文（包含所有Agent的输出）
            }
        """
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始跨领域综合分析")
        print(f"{'='*60}\n")
        
        query = input_data.get("query", "综合分析我的发展情况")
        context = input_data.get("context", {})
        
        self.status = AgentStatus.WORKING
        if self.gateway:
            self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.WORKING)
        
        start_time = datetime.now()
        
        try:
            # 1. 收集所有领域的分析结果
            print("📦 步骤1: 收集领域分析结果...")
            relationship_insights = context.get("relationship_insights", [])
            education_insights = context.get("education_insights", [])
            career_insights = context.get("career_insights", [])
            
            print(f"  - 人际关系: {len(relationship_insights)} 个洞察")
            print(f"  - 教育升学: {len(education_insights)} 个洞察")
            print(f"  - 职业规划: {len(career_insights)} 个洞察")
            
            # 2. 识别跨领域关联
            print("\n🔗 步骤2: 识别跨领域关联...")
            cross_domain_patterns = self._identify_cross_domain_patterns(
                relationship_insights,
                education_insights,
                career_insights
            )
            print(f"  ✓ 发现 {len(cross_domain_patterns)} 个跨领域模式")
            
            # 3. 分析协同效应和冲突
            print("\n⚖️ 步骤3: 分析协同效应和冲突...")
            synergies = self._analyze_synergies(cross_domain_patterns)
            conflicts = self._analyze_conflicts(cross_domain_patterns)
            print(f"  ✓ 协同效应: {len(synergies)} 个")
            print(f"  ✓ 潜在冲突: {len(conflicts)} 个")
            
            # 4. 生成综合战略建议
            print("\n🎯 步骤4: 生成综合战略建议...")
            strategic_recommendations = self._generate_strategic_recommendations(
                query,
                cross_domain_patterns,
                synergies,
                conflicts
            )
            print(f"  ✓ 生成 {len(strategic_recommendations)} 条战略建议")
            
            # 5. LLM深度综合分析
            print("\n🧠 步骤5: LLM深度综合分析...")
            comprehensive_analysis = self._llm_comprehensive_analysis(
                query,
                relationship_insights,
                education_insights,
                career_insights,
                cross_domain_patterns,
                synergies,
                conflicts
            )
            
            # 构建输出
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": comprehensive_analysis.get("summary", ""),
                "cross_domain_patterns": cross_domain_patterns,
                "synergies": synergies,
                "conflicts": conflicts,
                "strategic_recommendations": strategic_recommendations,
                "integrated_insights": comprehensive_analysis.get("integrated_insights", []),
                "action_plan": comprehensive_analysis.get("action_plan", {}),
                "confidence_score": 0.85,
                "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
            
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            print(f"\n✅ [{self.name}] 跨领域综合分析完成")
            print(f"  - 跨领域模式: {len(cross_domain_patterns)} 个")
            print(f"  - 战略建议: {len(strategic_recommendations)} 条")
            print(f"  - 总耗时: {output['execution_time_ms']:.2f}ms\n")
            
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 任务失败: {e}")
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            raise
    
    def _identify_cross_domain_patterns(
        self,
        relationship_insights: List,
        education_insights: List,
        career_insights: List
    ) -> List[Dict]:
        """识别跨领域模式"""
        patterns = []
        
        # 模式1: 人脉 × 职业
        if relationship_insights and career_insights:
            patterns.append({
                "pattern_type": "relationship_career_synergy",
                "title": "人脉资源对职业发展的影响",
                "description": "你的人际网络中可能存在对职业发展有帮助的关键人物",
                "domains": ["relationship", "career"],
                "strength": "high"
            })
        
        # 模式2: 教育 × 职业
        if education_insights and career_insights:
            patterns.append({
                "pattern_type": "education_career_alignment",
                "title": "教育背景与职业目标的匹配度",
                "description": "你的教育背景和职业目标之间存在一定的关联",
                "domains": ["education", "career"],
                "strength": "medium"
            })
        
        # 模式3: 人脉 × 教育
        if relationship_insights and education_insights:
            patterns.append({
                "pattern_type": "relationship_education_support",
                "title": "人际关系对教育发展的支持",
                "description": "你的人际网络可能为教育发展提供资源和机会",
                "domains": ["relationship", "education"],
                "strength": "medium"
            })
        
        # 模式4: 三领域协同
        if relationship_insights and education_insights and career_insights:
            patterns.append({
                "pattern_type": "three_domain_integration",
                "title": "三领域协同发展机会",
                "description": "人际关系、教育背景和职业规划可以形成协同效应",
                "domains": ["relationship", "education", "career"],
                "strength": "high"
            })
        
        return patterns
    
    def _analyze_synergies(self, patterns: List[Dict]) -> List[Dict]:
        """分析协同效应"""
        synergies = []
        
        for pattern in patterns:
            if pattern["strength"] in ["high", "medium"]:
                synergies.append({
                    "synergy_type": pattern["pattern_type"],
                    "title": f"协同机会: {pattern['title']}",
                    "description": "可以通过整合多个领域的资源来提升整体效果",
                    "involved_domains": pattern["domains"],
                    "potential_benefit": "提升整体发展效率和成功率"
                })
        
        return synergies
    
    def _analyze_conflicts(self, patterns: List[Dict]) -> List[Dict]:
        """分析潜在冲突"""
        conflicts = []
        
        # 示例：时间和精力的冲突
        conflicts.append({
            "conflict_type": "resource_allocation",
            "title": "时间和精力分配冲突",
            "description": "在人际关系维护、学业提升和职业发展之间可能存在时间分配冲突",
            "involved_domains": ["relationship", "education", "career"],
            "severity": "medium",
            "resolution_suggestion": "建立优先级体系，在不同阶段侧重不同领域"
        })
        
        return conflicts
    
    def _generate_strategic_recommendations(
        self,
        query: str,
        patterns: List[Dict],
        synergies: List[Dict],
        conflicts: List[Dict]
    ) -> List[Dict]:
        """生成综合战略建议"""
        recommendations = []
        
        # 基于协同效应的建议
        for synergy in synergies:
            recommendations.append({
                "priority": "high",
                "category": "协同发展",
                "action": f"利用{synergy['title']}，整合多领域资源",
                "expected_impact": synergy["potential_benefit"],
                "timeline": "3-6个月",
                "involved_domains": synergy["involved_domains"]
            })
        
        # 基于冲突的建议
        for conflict in conflicts:
            recommendations.append({
                "priority": "medium",
                "category": "冲突化解",
                "action": conflict["resolution_suggestion"],
                "expected_impact": "减少资源浪费，提高效率",
                "timeline": "立即执行",
                "involved_domains": conflict["involved_domains"]
            })
        
        return recommendations[:5]  # 最多5条
    
    def _llm_comprehensive_analysis(
        self,
        query: str,
        relationship_insights: List,
        education_insights: List,
        career_insights: List,
        patterns: List[Dict],
        synergies: List[Dict],
        conflicts: List[Dict]
    ) -> Dict:
        """LLM深度综合分析"""
        if not self.llm_service:
            return self._generate_fallback_analysis()
        
        prompt = f"""你是一个跨领域综合分析专家。请基于以下三个领域的分析结果，生成深度综合洞察。

【用户查询】
{query}

【人际关系领域】
- 关键洞察数: {len(relationship_insights)}

【教育升学领域】
- 关键洞察数: {len(education_insights)}

【职业规划领域】
- 关键洞察数: {len(career_insights)}

【跨领域模式】
{json.dumps([p['title'] for p in patterns], ensure_ascii=False)}

【协同效应】
{json.dumps([s['title'] for s in synergies], ensure_ascii=False)}

【潜在冲突】
{json.dumps([c['title'] for c in conflicts], ensure_ascii=False)}

请生成：
1. 综合摘要（300-400字）：整合三个领域的洞察，给出整体评估
2. 整合洞察（3-5个）：跨领域的深层次发现
3. 行动计划：分阶段的具体行动建议

以JSON格式返回：
{{
    "summary": "综合摘要",
    "integrated_insights": [
        {{
            "title": "洞察标题",
            "description": "详细描述",
            "domains": ["涉及的领域"],
            "importance": "high/medium/low"
        }}
    ],
    "action_plan": {{
        "short_term": ["1-3个月内的行动"],
        "medium_term": ["3-6个月内的行动"],
        "long_term": ["6-12个月内的行动"]
    }}
}}
"""
        
        try:
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"  ⚠️ LLM调用失败: {e}")
            return self._generate_fallback_analysis()
    
    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return self._generate_fallback_analysis()
    
    def _generate_fallback_analysis(self) -> Dict:
        """生成降级分析"""
        return {
            "summary": "基于三个领域的分析，建议关注跨领域的协同效应，平衡各领域的发展。",
            "integrated_insights": [
                {
                    "title": "整合发展机会",
                    "description": "人际关系、教育背景和职业规划可以相互促进",
                    "domains": ["relationship", "education", "career"],
                    "importance": "high"
                }
            ],
            "action_plan": {
                "short_term": ["评估当前各领域状况"],
                "medium_term": ["制定整合发展计划"],
                "long_term": ["持续优化跨领域协同"]
            }
        }


# ==================== 工厂函数 ====================

def create_collaborative_agents(user_id: str) -> Dict[str, CollaborativeAgent]:
    """创建所有协作Agent - 使用 realtime_insight_agents 里已验证的实现"""
    from backend.insights.realtime_insight_agents import (
        get_relationship_agent,
        get_education_agent,
        get_career_agent
    )
    
    return {
        "relationship": get_relationship_agent(user_id),
        "education": get_education_agent(user_id),
        "career": get_career_agent(user_id),
        "cross_domain": CrossDomainAnalysisAgent(user_id)  # 跨领域分析仍用本地实现
    }
