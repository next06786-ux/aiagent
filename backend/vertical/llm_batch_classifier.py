"""
统一的LLM批量分类服务
支持异步批量处理、三级缓存、自动识别垂直领域和节点类型
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
import os
import json
import time
import hashlib
from dotenv import load_dotenv

load_dotenv()


@dataclass
class NodeClassificationRequest:
    """节点分类请求"""
    node_id: str
    node_data: Dict[str, Any]
    user_context: Optional[Dict[str, Any]] = None


@dataclass
class NodeClassificationResult:
    """节点分类结果"""
    node_id: str
    vertical_domain: Literal["education", "career", "relationship", "unknown"]  # 垂直领域
    node_type: str  # 节点类型
    category: str  # 分类标签
    score: float  # 匹配分数 0-1
    reasons: List[str]  # 分类原因
    metadata: Dict[str, Any]  # 额外元数据


class LLMBatchClassifier:
    """统一的LLM批量分类器（支持三级缓存）"""
    
    def __init__(self):
        print("[LLMBatchClassifier] 初始化统一LLM批量分类器")
        
        # L1: 内存缓存
        self._classification_cache = {}  # {cache_key: List[NodeClassificationResult]}
        self._cache_timestamps = {}
        self.cache_ttl = 3600  # 1小时
        
        # 批量处理配置
        self.batch_size = 10  # 进一步减小批量大小
    
    def _get_cache_key(self, nodes_hash: str, context_hash: str) -> str:
        """生成缓存key"""
        return f"llm_classify:{nodes_hash}:{context_hash}"
    
    def _get_nodes_hash(self, nodes: List[Dict]) -> str:
        """计算节点列表的哈希值（按ID排序，确保稳定）"""
        # 按节点ID排序，确保相同节点集合生成相同哈希
        nodes_str = "_".join(sorted([
            f"{n.get('id', '')}_{n.get('name', '')}_{n.get('type', '')}"
            for n in nodes
        ]))
        return hashlib.md5(nodes_str.encode()).hexdigest()[:12]
    
    def _get_context_hash(self, context: Optional[Dict]) -> str:
        """计算上下文的哈希值"""
        if not context:
            return "no_context"
        context_str = json.dumps(context, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(context_str.encode()).hexdigest()[:8]
    
    def _get_cached_results(self, cache_key: str) -> Optional[List[NodeClassificationResult]]:
        """从缓存获取分类结果（L1 -> L2）"""
        # L1: 内存缓存
        if cache_key in self._classification_cache:
            if time.time() - self._cache_timestamps.get(cache_key, 0) < self.cache_ttl:
                print(f"[L1 Hit] 从内存加载分类结果")
                return self._classification_cache[cache_key]
            else:
                del self._classification_cache[cache_key]
                del self._cache_timestamps[cache_key]
        
        # L2: Redis缓存
        try:
            import redis
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True
            )
            
            cached_str = redis_client.get(cache_key)
            if cached_str:
                print(f"[L2 Hit] 从Redis加载分类结果")
                cached_data = json.loads(cached_str)
                results = [
                    NodeClassificationResult(**item)
                    for item in cached_data
                ]
                # 回填到L1
                self._classification_cache[cache_key] = results
                self._cache_timestamps[cache_key] = time.time()
                return results
        except Exception as e:
            print(f"[L2 Miss] Redis读取失败: {e}")
        
        return None
    
    def _cache_results(self, cache_key: str, results: List[NodeClassificationResult]):
        """缓存分类结果（L1 + L2）"""
        # L1: 内存缓存
        self._classification_cache[cache_key] = results
        self._cache_timestamps[cache_key] = time.time()
        
        # L2: Redis缓存
        try:
            import redis
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True
            )
            
            # 转换为可序列化的字典
            serializable_data = [
                {
                    "node_id": r.node_id,
                    "vertical_domain": r.vertical_domain,
                    "node_type": r.node_type,
                    "category": r.category,
                    "score": r.score,
                    "reasons": r.reasons,
                    "metadata": r.metadata
                }
                for r in results
            ]
            
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(serializable_data, ensure_ascii=False)
            )
            print(f"[Cache Write] 分类结果已缓存到L1+L2")
        except Exception as e:
            print(f"[Cache Write Failed] Redis写入失败: {e}")
    
    def classify_nodes_batch_incremental(
        self,
        nodes: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[NodeClassificationResult]:
        """
        增量批量分类节点（只对新节点使用LLM）
        
        Args:
            nodes: 节点列表
            user_context: 用户上下文
            
        Returns:
            分类结果列表
        """
        if not nodes:
            return []
        
        print(f"[增量分类] 检查 {len(nodes)} 个节点的缓存状态...")
        
        # 为每个节点生成单独的缓存key
        cached_results = []
        uncached_nodes = []
        uncached_indices = []
        
        for i, node in enumerate(nodes):
            # 为单个节点生成缓存key
            node_id = node.get('id', f'node_{i}')
            node_hash = hashlib.md5(f"{node_id}_{node.get('name', '')}_{node.get('type', '')}".encode()).hexdigest()[:12]
            context_hash = self._get_context_hash(user_context)
            cache_key = f"llm_classify_single:{node_hash}:{context_hash}"
            
            # 尝试从缓存获取
            cached = self._get_cached_results(cache_key)
            if cached and len(cached) > 0:
                cached_results.append((i, cached[0]))
            else:
                uncached_nodes.append(node)
                uncached_indices.append(i)
        
        print(f"[增量分类] 缓存命中: {len(cached_results)}/{len(nodes)}，需要LLM分类: {len(uncached_nodes)}")
        
        # 对未缓存的节点进行LLM分类
        new_results = []
        if uncached_nodes:
            print(f"[增量分类] 开始LLM分类 {len(uncached_nodes)} 个新节点...")
            
            # 分批处理
            for i in range(0, len(uncached_nodes), self.batch_size):
                batch = uncached_nodes[i:i+self.batch_size]
                batch_indices = uncached_indices[i:i+self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(uncached_nodes) + self.batch_size - 1) // self.batch_size
                
                print(f"[增量分类] 处理第 {batch_num}/{total_batches} 批，包含 {len(batch)} 个节点")
                
                try:
                    batch_results = self._classify_batch_with_llm(batch, user_context)
                    
                    # 缓存每个节点的结果
                    for j, result in enumerate(batch_results):
                        node = batch[j]
                        node_id = node.get('id', f'node_{batch_indices[j]}')
                        node_hash = hashlib.md5(f"{node_id}_{node.get('name', '')}_{node.get('type', '')}".encode()).hexdigest()[:12]
                        context_hash = self._get_context_hash(user_context)
                        cache_key = f"llm_classify_single:{node_hash}:{context_hash}"
                        
                        # 缓存单个节点结果
                        self._cache_results(cache_key, [result])
                        new_results.append((batch_indices[j], result))
                    
                except Exception as e:
                    print(f"[增量分类] 批次 {batch_num} 失败: {e}")
                    # LLM失败，使用默认分类
                    for j, node in enumerate(batch):
                        result = self._classify_node_default(node, user_context)
                        new_results.append((batch_indices[j], result))
        
        # 合并缓存结果和新结果，按原始顺序排列
        all_results_dict = {}
        for idx, result in cached_results:
            all_results_dict[idx] = result
        for idx, result in new_results:
            all_results_dict[idx] = result
        
        # 按索引排序
        final_results = [all_results_dict[i] for i in range(len(nodes))]
        
        print(f"[增量分类] 分类完成，共 {len(final_results)} 个节点（{len(cached_results)} 来自缓存，{len(new_results)} 新分类）")
        return final_results
    
    def classify_nodes_batch(
        self,
        nodes: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
        use_llm: bool = False  # 默认不使用LLM，避免阻塞
    ) -> List[NodeClassificationResult]:
        """
        批量分类节点（支持三级缓存）
        
        Args:
            nodes: 节点列表，每个节点包含 id, name, type 等字段
            user_context: 用户上下文（用于个性化分类）
            use_llm: 是否使用LLM分类（默认False，使用快速默认分类）
            
        Returns:
            分类结果列表
        """
        if not nodes:
            return []
        
        # 生成缓存key
        nodes_hash = self._get_nodes_hash(nodes)
        context_hash = self._get_context_hash(user_context)
        cache_key = self._get_cache_key(nodes_hash, context_hash)
        
        # 尝试从缓存获取
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            print(f"[Cache Hit ✓] 使用缓存的分类结果，共 {len(cached_results)} 个节点，跳过LLM调用")
            return cached_results
        
        # 缓存未命中
        print(f"[Cache Miss ✗] 缓存key: {cache_key}")
        
        if use_llm:
            # 使用LLM分类（慢，但准确）
            print(f"[LLMBatchClassifier] 开始LLM批量分类，共 {len(nodes)} 个节点")
            all_results = []
            
            # 分批处理
            for i in range(0, len(nodes), self.batch_size):
                batch = nodes[i:i+self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(nodes) + self.batch_size - 1) // self.batch_size
                
                print(f"[LLMBatchClassifier] 处理第 {batch_num}/{total_batches} 批，包含 {len(batch)} 个节点")
                
                try:
                    batch_results = self._classify_batch_with_llm(batch, user_context)
                    all_results.extend(batch_results)
                except Exception as e:
                    print(f"[LLMBatchClassifier] 批次 {batch_num} 失败，使用默认分类: {e}")
                    # LLM失败，使用默认分类
                    batch_results = [self._classify_node_default(node, user_context) for node in batch]
                    all_results.extend(batch_results)
        else:
            # 使用快速默认分类（快，基于节点属性）
            print(f"[LLMBatchClassifier] 使用快速默认分类，共 {len(nodes)} 个节点")
            all_results = [self._classify_node_default(node, user_context) for node in nodes]
        
        # 缓存结果
        self._cache_results(cache_key, all_results)
        
        print(f"[LLMBatchClassifier] 分类完成，共 {len(all_results)} 个节点")
        return all_results
    
    def _classify_batch_with_llm(
        self,
        nodes: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]]
    ) -> List[NodeClassificationResult]:
        """使用LLM批量分类一批节点"""
        try:
            from backend.llm.llm_service import get_llm_service
            llm = get_llm_service()
            
            if not llm or not llm.enabled:
                raise Exception("LLM服务不可用")
            
            # 构建用户上下文描述
            context_desc = ""
            if user_context:
                context_desc = f"""用户背景：
- 目标方向: {user_context.get('target_direction', '未知')}
- 技能水平: {user_context.get('skill_level', '未知')}
- 学业背景: {user_context.get('academic_background', '未知')}
- 意向地区: {user_context.get('preferred_locations', [])}
"""
            
            # 构建节点列表描述（简化，减少token数量）
            nodes_desc = []
            for i, node in enumerate(nodes):
                node_info = f"""节点{i+1}: {node.get('name', '未命名')} (类型: {node.get('type', 'unknown')})"""
                nodes_desc.append(node_info)
            
            nodes_text = "\n".join(nodes_desc)
            
            # 构建极简的分类prompt（减少token）
            prompt = f"""批量分类节点。

节点：
{nodes_text}

对每个节点返回：
1. vertical_domain: education/career/relationship
2. category: education用reach/match/safety，career用target/potential/backup，relationship用close/normal/distant
3. score: 0-1分数

JSON格式：
{{
    "classifications": [
        {{"node_index": 1, "vertical_domain": "education", "category": "match", "score": 0.75}}
    ]
}}"""

            print(f"[LLMBatchClassifier] 调用LLM分析 {len(nodes)} 个节点...")
            
            # 增加超时时间到60秒
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    llm.chat,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                try:
                    response = future.result(timeout=60)  # 60秒超时
                except concurrent.futures.TimeoutError:
                    print(f"[LLMBatchClassifier] LLM调用超时（60秒），抛出异常")
                    raise TimeoutError("LLM调用超时")
            
            # 解析LLM响应
            if not response or not response.strip():
                print(f"[LLMBatchClassifier] LLM返回空响应")
                raise ValueError("LLM返回空响应")
            
            # 清理响应内容（移除可能的markdown代码块标记）
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"[LLMBatchClassifier] JSON解析失败，响应内容: {response[:500]}")
                raise ValueError(f"JSON解析失败: {e}")
            
            classifications = result.get('classifications', [])
            
            # 构建返回结果
            results = []
            for i, node in enumerate(nodes):
                # 查找对应的分类结果
                classification = None
                for c in classifications:
                    if c.get('node_index') == i + 1:
                        classification = c
                        break
                
                if classification:
                    results.append(NodeClassificationResult(
                        node_id=node.get('id', f'node_{i}'),
                        vertical_domain=classification.get('vertical_domain', 'unknown'),
                        node_type=classification.get('node_type', 'unknown'),
                        category=classification.get('category', 'unknown'),
                        score=max(0.0, min(1.0, float(classification.get('score', 0.5)))),
                        reasons=classification.get('reasons', ['LLM分类'])[:2],
                        metadata=classification.get('metadata', {})
                    ))
                else:
                    # LLM未返回该节点结果，使用默认值
                    results.append(NodeClassificationResult(
                        node_id=node.get('id', f'node_{i}'),
                        vertical_domain='unknown',
                        node_type='unknown',
                        category='unknown',
                        score=0.5,
                        reasons=['LLM未返回分类结果'],
                        metadata={}
                    ))
            
            print(f"[LLMBatchClassifier] LLM分类完成，成功分析 {len(results)} 个节点")
            return results
            
        except Exception as e:
            print(f"[LLMBatchClassifier] LLM分类失败: {e}")
            import traceback
            traceback.print_exc()
            raise  # 抛出异常
    
    def _classify_node_default(self, node: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> NodeClassificationResult:
        """快速默认分类（基于节点属性，不使用LLM）"""
        node_id = node.get('id', 'unknown')
        node_name = node.get('name', '').lower()
        node_type = node.get('type', '').lower()
        properties = node.get('properties', {})
        
        # 根据节点类型快速判断垂直领域
        if node_type in ['school', 'university', 'college', 'major', 'course', 'degree']:
            vertical_domain = "education"
            node_type_result = node_type
            # 根据属性判断分类
            if properties.get('is_985') or properties.get('gpa_requirement', 0) > 3.7:
                category = "reach"
                score = 0.4
            elif properties.get('is_211') or properties.get('gpa_requirement', 0) > 3.3:
                category = "match"
                score = 0.6
            else:
                category = "safety"
                score = 0.8
            reasons = [f"基于{node_type}类型的默认分类"]
            
        elif node_type in ['company', 'job', 'position', 'skill', 'industry']:
            vertical_domain = "career"
            node_type_result = node_type
            # 根据薪资判断分类
            salary = properties.get('salary', 0)
            if salary > 30000:
                category = "target"
                score = 0.8
            elif salary > 20000:
                category = "potential"
                score = 0.6
            else:
                category = "backup"
                score = 0.4
            reasons = [f"基于{node_type}类型的默认分类"]
            
        elif node_type in ['person', 'friend', 'colleague', 'family', 'people']:
            vertical_domain = "relationship"
            node_type_result = node_type
            # 根据影响力判断分类
            influence = properties.get('influence_score', 0.5)
            if influence > 0.7:
                category = "close"
                score = 0.8
            elif influence > 0.4:
                category = "normal"
                score = 0.6
            else:
                category = "distant"
                score = 0.4
            reasons = [f"基于{node_type}类型的默认分类"]
            
        else:
            # 无法识别，返回unknown
            vertical_domain = "unknown"
            node_type_result = "unknown"
            category = "unknown"
            score = 0.5
            reasons = ["无法识别的节点类型"]
        
        return NodeClassificationResult(
            node_id=node_id,
            vertical_domain=vertical_domain,
            node_type=node_type_result,
            category=category,
            score=score,
            reasons=reasons,
            metadata={"classification_method": "default"}
        )


# 全局单例
_llm_batch_classifier = None

def get_llm_batch_classifier() -> LLMBatchClassifier:
    """获取LLM批量分类器单例"""
    global _llm_batch_classifier
    if _llm_batch_classifier is None:
        _llm_batch_classifier = LLMBatchClassifier()
    return _llm_batch_classifier
