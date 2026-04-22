package com.lifeswarm.android.presentation.knowledge

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.repository.KnowledgeGraphRepository
import com.lifeswarm.android.presentation.knowledge.opengl.Edge
import com.lifeswarm.android.presentation.knowledge.opengl.Node
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * 知识图谱 ViewModel
 * 对应 web/src/pages/KnowledgeGraphPage.tsx 的状态管理
 */
class KnowledgeGraphViewModel(
    private val repository: KnowledgeGraphRepository,
    private val userId: String
) : ViewModel() {
    
    // UI 状态
    private val _uiState = MutableStateFlow<KnowledgeGraphUiState>(KnowledgeGraphUiState.Loading)
    val uiState: StateFlow<KnowledgeGraphUiState> = _uiState.asStateFlow()
    
    // 当前视图模式
    private val _selectedView = MutableStateFlow("people")
    val selectedView: StateFlow<String> = _selectedView.asStateFlow()
    
    // 图谱数据
    private val _graphData = MutableStateFlow<KnowledgeGraphView?>(null)
    val graphData: StateFlow<KnowledgeGraphView?> = _graphData.asStateFlow()
    
    // OpenGL 渲染数据
    private val _nodes = MutableStateFlow<List<Node>>(emptyList())
    val nodes: StateFlow<List<Node>> = _nodes.asStateFlow()
    
    private val _edges = MutableStateFlow<List<Edge>>(emptyList())
    val edges: StateFlow<List<Edge>> = _edges.asStateFlow()
    
    /**
     * 切换视图
     */
    fun switchView(view: String) {
        if (_selectedView.value == view) return
        _selectedView.value = view
        loadGraphData()
    }
    
    /**
     * 加载图谱数据
     */
    fun loadGraphData() {
        viewModelScope.launch {
            _uiState.value = KnowledgeGraphUiState.Loading
            
            try {
                val graphView = when (_selectedView.value) {
                    "people" -> loadPeopleGraph()
                    "career" -> loadCareerGraph()
                    "education" -> loadEducationGraph()
                    else -> loadPeopleGraph()
                }
                
                // 调试：打印前3个节点的数据
                println("[KnowledgeGraph] ========== 后端返回数据 ==========")
                graphView.nodes.take(3).forEach { node ->
                    println("[KnowledgeGraph] 节点: id=${node.id}, name='${node.name}', type=${node.type}")
                    println("[KnowledgeGraph]   metadata=${node.metadata}")
                }
                println("[KnowledgeGraph] =====================================")
                
                _graphData.value = graphView
                
                // 转换为 OpenGL 渲染数据
                val (nodes, edges) = convertToRenderData(graphView)
                _nodes.value = nodes
                _edges.value = edges
                
                _uiState.value = KnowledgeGraphUiState.Success(graphView)
                
                println("[KnowledgeGraph] 加载成功: ${nodes.size} 个节点, ${edges.size} 条连线")
                
            } catch (e: Exception) {
                println("[KnowledgeGraph] 加载失败: ${e.message}")
                e.printStackTrace()
                _uiState.value = KnowledgeGraphUiState.Error(e.message ?: "加载失败")
            }
        }
    }
    
    /**
     * 加载人际关系图谱
     */
    private suspend fun loadPeopleGraph(): KnowledgeGraphView {
        val request = PeopleGraphRequest(
            userId = userId,
            question = "",
            sessionId = null
        )
        return repository.getPeopleGraph(request)
    }
    
    /**
     * 加载职业图谱
     */
    private suspend fun loadCareerGraph(): KnowledgeGraphView {
        val request = CareerGraphRequest(
            userId = userId,
            masteredSkills = emptyList(),
            partialSkills = emptyList(),
            missingSkills = emptyList(),
            targetDirection = ""
        )
        return repository.getCareerGraph(request)
    }
    
    /**
     * 加载升学规划图谱
     */
    private suspend fun loadEducationGraph(): KnowledgeGraphView {
        val request = EducationGraphRequest(
            userId = userId,
            gpa = 3.5,
            gpaMax = 4.0,
            rankingPercent = 10.0,
            satAct = 1400,
            researchExperience = 1.0,
            publications = 0,
            targetMajor = "Computer Science",
            targetLevel = "master",
            searchKeyword = "",
            location = ""
        )
        return repository.getEducationGraph(request)
    }
    
    /**
     * 将后端数据转换为 OpenGL 渲染数据
     */
    private fun convertToRenderData(graphView: KnowledgeGraphView): Pair<List<Node>, List<Edge>> {
        val nodes = mutableListOf<Node>()
        val edges = mutableListOf<Edge>()
        
        // 获取连线数据（兼容 links 和 edges 字段）
        val links = graphView.edges ?: graphView.links
        
        // 计算每个节点的连接数
        val connectionCounts = mutableMapOf<String, Int>()
        links.forEach { link ->
            connectionCounts[link.source] = (connectionCounts[link.source] ?: 0) + 1
            connectionCounts[link.target] = (connectionCounts[link.target] ?: 0) + 1
        }
        
        // 构建节点位置映射
        val nodePositions = mutableMapOf<String, Triple<Float, Float, Float>>()
        
        // 如果后端提供了位置信息，使用它
        val hasPositions = graphView.nodes.any { it.position != null }
        
        if (hasPositions) {
            // 使用后端提供的位置，并放大坐标以便在 3D 空间中更好地显示
            val scale = 5.0f // 放大倍数
            
            // 找到坐标范围以进行居中
            val minX = graphView.nodes.mapNotNull { it.position?.x }. minOrNull()?.toFloat() ?: 0f
            val maxX = graphView.nodes.mapNotNull { it.position?.x }.maxOrNull()?.toFloat() ?: 0f
            val minY = graphView.nodes.mapNotNull { it.position?.y }.minOrNull()?.toFloat() ?: 0f
            val maxY = graphView.nodes.mapNotNull { it.position?.y }.maxOrNull()?.toFloat() ?: 0f
            val minZ = graphView.nodes.mapNotNull { it.position?.z }.minOrNull()?.toFloat() ?: 0f
            val maxZ = graphView.nodes.mapNotNull { it.position?.z }.maxOrNull()?.toFloat() ?: 0f
            
            val centerX = (minX + maxX) / 2f
            val centerY = (minY + maxY) / 2f
            val centerZ = (minZ + maxZ) / 2f
            
            graphView.nodes.forEach { node ->
                val pos = node.position
                if (pos != null) {
                    // 居中并缩放
                    nodePositions[node.id] = Triple(
                        (pos.x.toFloat() - centerX) * scale,
                        (pos.y.toFloat() - centerY) * scale,
                        (pos.z.toFloat() - centerZ) * scale
                    )
                }
            }
        } else {
            // 使用力导向布局算法
            nodePositions.putAll(calculateForceDirectedLayout(graphView.nodes, links))
        }
        
        // 转换节点
        graphView.nodes.forEach { node ->
            val position = nodePositions[node.id] ?: Triple(0f, 0f, 0f)
            val color = getNodeColor(node)
            val radius = getNodeRadius(node)
            val connections = connectionCounts[node.id] ?: 0
            
            nodes.add(Node(
                id = node.id,
                x = position.first,
                y = position.second,
                z = position.third,
                radius = radius,
                color = color,
                label = node.label ?: node.name,
                connections = connections
            ))
        }
        
        // 转换连线
        links.forEach { link ->
            val color = getEdgeColor(link)
            edges.add(Edge(
                from = link.source,
                to = link.target,
                color = color
            ))
        }
        
        return Pair(nodes, edges)
    }
    
    /**
     * 计算力导向布局
     */
    private fun calculateForceDirectedLayout(
        nodes: List<KnowledgeGraphNode>,
        links: List<KnowledgeGraphLink>
    ): Map<String, Triple<Float, Float, Float>> {
        val positions = mutableMapOf<String, Triple<Float, Float, Float>>()
        
        // 找到中心节点（isSelf = true 或第一个节点）
        val centerNode = nodes.find { it.isSelf } ?: nodes.firstOrNull()
        
        if (centerNode == null) return positions
        
        // 中心节点放在原点
        positions[centerNode.id] = Triple(0f, 0f, 0f)
        
        // 构建连接关系
        val connections = mutableMapOf<String, MutableList<String>>()
        links.forEach { link ->
            connections.getOrPut(link.source) { mutableListOf() }.add(link.target)
            connections.getOrPut(link.target) { mutableListOf() }.add(link.source)
        }
        
        // 获取与中心节点直接连接的节点
        val directConnections = connections[centerNode.id] ?: emptyList()
        val otherNodes = nodes.filter { it.id != centerNode.id && it.id !in directConnections }
        
        // 第一层：直接连接的节点（圆形布局）
        val radius1 = 3f
        directConnections.forEachIndexed { index, nodeId ->
            val angle = (index * 2 * Math.PI / directConnections.size).toFloat()
            val x = radius1 * cos(angle)
            val z = radius1 * sin(angle)
            val y = (Math.random() * 1 - 0.5).toFloat()
            positions[nodeId] = Triple(x, y, z)
        }
        
        // 第二层：其他节点（更大的圆形布局）
        val radius2 = 5f
        otherNodes.forEachIndexed { index, node ->
            val angle = (index * 2 * Math.PI / otherNodes.size).toFloat()
            val x = radius2 * cos(angle)
            val z = radius2 * sin(angle)
            val y = (Math.random() * 2 - 1).toFloat()
            positions[node.id] = Triple(x, y, z)
        }
        
        return positions
    }
    
    /**
     * 获取节点颜色
     */
    private fun getNodeColor(node: KnowledgeGraphNode): FloatArray {
        return when {
            // 自己 - 蓝色
            node.isSelf -> floatArrayOf(0.2f, 0.6f, 1.0f, 1.0f)
            
            // 根据类型着色
            node.type == "person" -> when (node.category) {
                "family" -> floatArrayOf(1.0f, 0.4f, 0.4f, 1.0f) // 红色 - 家人
                "friend" -> floatArrayOf(0.4f, 1.0f, 0.4f, 1.0f) // 绿色 - 朋友
                "colleague" -> floatArrayOf(1.0f, 0.8f, 0.2f, 1.0f) // 黄色 - 同事
                else -> floatArrayOf(0.6f, 0.6f, 0.6f, 1.0f) // 灰色 - 其他
            }
            
            node.type == "skill" -> when (node.viewRole) {
                "mastered" -> floatArrayOf(0.2f, 0.8f, 0.2f, 1.0f) // 绿色 - 已掌握
                "partial" -> floatArrayOf(1.0f, 0.8f, 0.2f, 1.0f) // 黄色 - 部分掌握
                "missing" -> floatArrayOf(0.8f, 0.2f, 0.2f, 1.0f) // 红色 - 缺失
                else -> floatArrayOf(0.6f, 0.6f, 1.0f, 1.0f) // 蓝色 - 其他
            }
            
            node.type == "school" -> floatArrayOf(0.8f, 0.4f, 1.0f, 1.0f) // 紫色 - 学校
            node.type == "major" -> floatArrayOf(0.4f, 0.8f, 1.0f, 1.0f) // 青色 - 专业
            
            // 根据影响力着色
            node.influenceScore > 0.7 -> floatArrayOf(1.0f, 0.6f, 0.2f, 1.0f) // 橙色 - 高影响力
            node.influenceScore > 0.4 -> floatArrayOf(0.8f, 0.8f, 0.4f, 1.0f) // 黄色 - 中影响力
            
            else -> floatArrayOf(0.6f, 0.6f, 0.6f, 1.0f) // 灰色 - 默认
        }
    }
    
    /**
     * 获取节点半径
     */
    private fun getNodeRadius(node: KnowledgeGraphNode): Float {
        return when {
            node.isSelf -> 0.3f // 自己最大
            node.weight > 0 -> 0.15f + (node.weight * 0.15f).toFloat() // 根据权重
            node.influenceScore > 0 -> 0.15f + (node.influenceScore * 0.15f).toFloat() // 根据影响力
            node.connections > 5 -> 0.25f // 连接多的节点大一些
            node.connections > 2 -> 0.2f
            else -> 0.15f // 默认大小
        }
    }
    
    /**
     * 获取连线颜色
     */
    private fun getEdgeColor(link: KnowledgeGraphLink): FloatArray {
        val alpha = when {
            link.strength > 0.7 -> 0.8f // 强连接
            link.strength > 0.4 -> 0.5f // 中等连接
            else -> 0.3f // 弱连接
        }
        
        return when (link.type) {
            "family" -> floatArrayOf(1.0f, 0.4f, 0.4f, alpha) // 红色 - 家庭关系
            "friend" -> floatArrayOf(0.4f, 1.0f, 0.4f, alpha) // 绿色 - 朋友关系
            "work" -> floatArrayOf(1.0f, 0.8f, 0.2f, alpha) // 黄色 - 工作关系
            "prerequisite" -> floatArrayOf(0.4f, 0.6f, 1.0f, alpha) // 蓝色 - 前置关系
            "related" -> floatArrayOf(0.6f, 0.6f, 0.6f, alpha) // 灰色 - 相关关系
            else -> floatArrayOf(0.5f, 0.5f, 0.5f, alpha) // 默认灰色
        }
    }
}

/**
 * UI 状态
 */
sealed class KnowledgeGraphUiState {
    object Loading : KnowledgeGraphUiState()
    data class Success(val data: KnowledgeGraphView) : KnowledgeGraphUiState()
    data class Error(val message: String) : KnowledgeGraphUiState()
}
