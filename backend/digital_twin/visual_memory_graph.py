"""
视觉记忆图谱
Visual Memory Graph - LifeSwarm核心模块
"""
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import pickle
from pathlib import Path


class MemoryNode:
    """视觉记忆节点"""
    def __init__(
        self,
        node_id: str,
        features: np.ndarray,
        scene: str,
        objects: List[str],
        activities: List[str],
        timestamp: int,
        location: Dict[str, float],
        embedding: np.ndarray
    ):
        self.id = node_id
        self.features = features
        self.scene = scene
        self.objects = objects
        self.activities = activities
        self.timestamp = timestamp
        self.location = location
        self.embedding = embedding
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'scene': self.scene,
            'objects': self.objects,
            'activities': self.activities,
            'timestamp': self.timestamp,
            'location': self.location
        }


class VisualMemoryGraph:
    """
    视觉记忆图谱
    核心创新：图结构存储跨时空视觉记忆
    """
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.graph = nx.MultiDiGraph()
        self.nodes_data = {}  # 存储完整节点数据
        self.node_counter = 0
        
    def add_memory(
        self,
        features: np.ndarray,
        scene: str,
        objects: List[str],
        activities: List[str],
        timestamp: int,
        location: Dict[str, float]
    ) -> str:
        """
        添加视觉记忆
        
        Args:
            features: 视觉特征向量
            scene: 场景类型
            objects: 检测到的物体列表
            activities: 识别到的活动列表
            timestamp: 时间戳
            location: 位置信息 {'lat': float, 'lng': float}
        
        Returns:
            node_id: 新创建的节点ID
        """
        # 生成节点ID
        node_id = f"{self.user_id}_mem_{self.node_counter}"
        self.node_counter += 1
        
        # 计算embedding（简化版，实际应使用预训练模型）
        embedding = self._compute_embedding(features)
        
        # 创建节点
        node = MemoryNode(
            node_id=node_id,
            features=features,
            scene=scene,
            objects=objects,
            activities=activities,
            timestamp=timestamp,
            location=location,
            embedding=embedding
        )
        
        # 添加到图
        self.graph.add_node(
            node_id,
            scene=scene,
            objects=objects,
            activities=activities,
            timestamp=timestamp,
            location=location
        )
        
        # 存储完整数据
        self.nodes_data[node_id] = node
        
        # 建立关联
        self._link_temporal(node_id, timestamp)
        self._link_spatial(node_id, location)
        self._link_semantic(node_id, embedding, scene)
        
        return node_id
    
    def _compute_embedding(self, features: np.ndarray) -> np.ndarray:
        """
        计算embedding向量
        实际应使用预训练的视觉编码器（如CLIP、ViT）
        这里使用特征的降维表示
        """
        if len(features.shape) > 1:
            # 如果是多维特征，使用均值池化
            embedding = features.mean(axis=0)
        else:
            embedding = features
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _link_temporal(self, node_id: str, timestamp: int):
        """
        建立时间关联
        设计思想：连接时间上相近的记忆节点，形成时间线
        """
        # 找到时间上最近的k个节点
        k = 5
        recent_nodes = []
        
        for nid in self.graph.nodes():
            if nid != node_id:
                node_time = self.graph.nodes[nid]['timestamp']
                time_diff = abs(timestamp - node_time)
                recent_nodes.append((nid, time_diff))
        
        # 排序并取前k个
        recent_nodes.sort(key=lambda x: x[1])
        
        for nid, time_diff in recent_nodes[:k]:
            # 计算时间衰减权重：时间越近权重越大
            # 使用指数衰减：w = exp(-time_diff / tau)
            tau = 3600  # 时间常数：1小时
            weight = np.exp(-time_diff / tau)
            
            self.graph.add_edge(
                nid,
                node_id,
                type='temporal',
                time_delta=time_diff,
                weight=weight
            )
    
    def _link_spatial(self, node_id: str, location: Dict[str, float]):
        """
        建立空间关联
        设计思想：连接地理位置相近的记忆节点，形成空间网络
        """
        # 空间阈值：100米
        spatial_threshold = 100.0
        nearby_nodes = []
        
        for nid in self.graph.nodes():
            if nid != node_id:
                node_loc = self.graph.nodes[nid]['location']
                distance = self._calculate_distance(location, node_loc)
                
                if distance <= spatial_threshold:
                    nearby_nodes.append((nid, distance))
        
        # 添加空间边
        for nid, distance in nearby_nodes:
            # 计算空间衰减权重：距离越近权重越大
            # 使用高斯核：w = exp(-(distance^2) / (2 * sigma^2))
            sigma = 50.0  # 空间尺度：50米
            weight = np.exp(-(distance ** 2) / (2 * sigma ** 2))
            
            self.graph.add_edge(
                nid,
                node_id,
                type='spatial',
                distance=distance,
                weight=weight
            )
    
    def _link_semantic(self, node_id: str, embedding: np.ndarray, scene: str):
        """
        建立语义关联
        设计思想：连接语义相似的记忆节点，形成概念网络
        """
        # 语义相似度阈值
        similarity_threshold = 0.7
        k = 10  # 最多连接k个相似节点
        
        similar_nodes = []
        
        for nid in self.graph.nodes():
            if nid != node_id and nid in self.nodes_data:
                node_emb = self.nodes_data[nid].embedding
                node_scene = self.graph.nodes[nid]['scene']
                
                # 计算语义相似度
                similarity = self._cosine_similarity(embedding, node_emb)
                
                # 场景匹配加成
                if node_scene == scene:
                    similarity = similarity * 1.2  # 相同场景提升20%
                
                if similarity > similarity_threshold:
                    similar_nodes.append((nid, similarity))
        
        # 排序并取前k个
        similar_nodes.sort(key=lambda x: x[1], reverse=True)
        
        for nid, similarity in similar_nodes[:k]:
            self.graph.add_edge(
                nid,
                node_id,
                type='semantic',
                similarity=min(similarity, 1.0),  # 限制在[0,1]
                weight=min(similarity, 1.0)
            )
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """计算两点距离（米）"""
        # 简化实现：使用欧氏距离
        # 实际应使用Haversine公式
        lat_diff = loc1.get('lat', 0) - loc2.get('lat', 0)
        lng_diff = loc1.get('lng', 0) - loc2.get('lng', 0)
        return np.sqrt(lat_diff**2 + lng_diff**2) * 111000  # 粗略转换为米
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def query_temporal(self, start_time: int, end_time: int) -> List[Dict]:
        """
        时间查询："我上周做了什么？"
        """
        results = []
        for node_id in self.graph.nodes():
            node_time = self.graph.nodes[node_id]['timestamp']
            if start_time <= node_time <= end_time:
                results.append(self.graph.nodes[node_id])
        
        # 按时间排序
        results.sort(key=lambda x: x['timestamp'])
        return results
    
    def query_spatial(self, location: Dict[str, float], radius: float = 100) -> List[Dict]:
        """
        空间查询："我在这个地方做过什么？"
        """
        results = []
        for node_id in self.graph.nodes():
            node_loc = self.graph.nodes[node_id]['location']
            distance = self._calculate_distance(location, node_loc)
            if distance <= radius:
                result = self.graph.nodes[node_id].copy()
                result['distance'] = distance
                results.append(result)
        
        # 按距离排序
        results.sort(key=lambda x: x['distance'])
        return results
    
    def query_semantic(self, query_scene: str, query_objects: List[str]) -> List[Dict]:
        """
        语义查询："我上次见到XX是什么时候？"
        """
        results = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            
            # 计算语义相似度
            scene_match = 1.0 if node_data['scene'] == query_scene else 0.0
            object_match = len(set(query_objects) & set(node_data['objects'])) / max(len(query_objects), 1)
            
            similarity = 0.5 * scene_match + 0.5 * object_match
            
            if similarity > 0.3:
                result = node_data.copy()
                result['similarity'] = similarity
                results.append(result)
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def query_reasoning(self, query: str, context: Dict) -> Dict:
        """
        推理查询："我的钥匙可能在哪？"
        设计思想：基于图结构的多跳推理
        """
        target_object = context.get('target_object', '钥匙')
        
        # 1. 找到包含目标物体的所有记忆
        relevant_memories = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if target_object in node_data['objects']:
                relevant_memories.append({
                    'node_id': node_id,
                    **node_data
                })
        
        if not relevant_memories:
            return {
                'found': False,
                'message': f'没有找到关于{target_object}的记忆',
                'confidence': 0.0
            }
        
        # 2. 找到最后一次看到（时间最近）
        last_seen = max(relevant_memories, key=lambda x: x['timestamp'])
        
        # 3. 基于图结构进行多跳推理
        # 从最后看到的位置出发，沿着时间边和空间边推理
        reasoning_path = self._multi_hop_reasoning(
            start_node=last_seen['node_id'],
            max_hops=5
        )
        
        # 4. 推理可能的位置
        possible_locations = []
        location_scores = {}
        
        for node_id in reasoning_path:
            node_data = self.graph.nodes[node_id]
            loc_key = f"{node_data['location']['lat']:.4f},{node_data['location']['lng']:.4f}"
            
            if loc_key not in location_scores:
                location_scores[loc_key] = {
                    'location': node_data['location'],
                    'scene': node_data['scene'],
                    'score': 0.0,
                    'visits': 0
                }
            
            location_scores[loc_key]['score'] += 1.0
            location_scores[loc_key]['visits'] += 1
        
        # 排序并归一化分数
        for loc_data in location_scores.values():
            possible_locations.append(loc_data)
        
        possible_locations.sort(key=lambda x: x['score'], reverse=True)
        
        # 计算置信度
        confidence = min(len(relevant_memories) / 10.0, 1.0)  # 记忆越多越可信
        
        return {
            'found': True,
            'target_object': target_object,
            'last_seen': {
                'location': last_seen['location'],
                'scene': last_seen['scene'],
                'timestamp': last_seen['timestamp'],
                'time_ago_hours': (int(datetime.now().timestamp()) - last_seen['timestamp']) / 3600
            },
            'possible_locations': possible_locations[:5],  # 返回前5个最可能的位置
            'reasoning_path_length': len(reasoning_path),
            'confidence': confidence,
            'recommendation': self._generate_recommendation(last_seen, possible_locations)
        }
    
    def _multi_hop_reasoning(self, start_node: str, max_hops: int = 5) -> List[str]:
        """
        多跳推理：从起始节点出发，沿着图边进行推理
        """
        visited = set()
        current_nodes = [start_node]
        all_nodes = [start_node]
        
        for hop in range(max_hops):
            next_nodes = []
            
            for node in current_nodes:
                if node in visited:
                    continue
                
                visited.add(node)
                
                # 获取邻居节点（优先时间边和空间边）
                for neighbor in self.graph.neighbors(node):
                    edge_data = self.graph.get_edge_data(node, neighbor)
                    
                    # 选择权重较高的边
                    for key, data in edge_data.items():
                        if data.get('weight', 0) > 0.3:  # 权重阈值
                            if neighbor not in visited:
                                next_nodes.append(neighbor)
                                all_nodes.append(neighbor)
            
            current_nodes = next_nodes
            
            if not current_nodes:
                break
        
        return all_nodes
    
    def _generate_recommendation(self, last_seen: Dict, possible_locations: List[Dict]) -> str:
        """生成推荐建议"""
        if not possible_locations:
            return f"建议回到最后看到的地方：{last_seen['scene']}"
        
        top_location = possible_locations[0]
        return f"最可能在：{top_location['scene']}（访问次数：{top_location['visits']}）"
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'temporal_edges': sum(1 for _, _, d in self.graph.edges(data=True) if d.get('type') == 'temporal'),
            'spatial_edges': sum(1 for _, _, d in self.graph.edges(data=True) if d.get('type') == 'spatial'),
            'semantic_edges': sum(1 for _, _, d in self.graph.edges(data=True) if d.get('type') == 'semantic')
        }
    
    def save(self, filepath: str):
        """保存图谱到文件"""
        data = {
            'user_id': self.user_id,
            'node_counter': self.node_counter,
            'graph': nx.node_link_data(self.graph),
            'nodes_data': {
                nid: {
                    'features': node.features.tolist(),
                    'embedding': node.embedding.tolist(),
                    **node.to_dict()
                }
                for nid, node in self.nodes_data.items()
            }
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'VisualMemoryGraph':
        """从文件加载图谱"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        graph = cls(data['user_id'])
        graph.node_counter = data['node_counter']
        graph.graph = nx.node_link_graph(data['graph'])
        
        # 恢复节点数据
        for nid, node_data in data['nodes_data'].items():
            node = MemoryNode(
                node_id=nid,
                features=np.array(node_data['features']),
                scene=node_data['scene'],
                objects=node_data['objects'],
                activities=node_data['activities'],
                timestamp=node_data['timestamp'],
                location=node_data['location'],
                embedding=np.array(node_data['embedding'])
            )
            graph.nodes_data[nid] = node
        
        return graph
