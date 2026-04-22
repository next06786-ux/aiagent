package com.lifeswarm.android.presentation.knowledge

import android.opengl.GLSurfaceView
import android.view.MotionEvent
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import com.lifeswarm.android.LifeSwarmApp
import com.lifeswarm.android.presentation.knowledge.opengl.EnhancedKnowledgeGraphRenderer
import kotlin.math.sqrt

/**
 * 知识星图页面 - OpenGL ES 3.0 增强版实现
 * 对应 web/src/pages/KnowledgeGraphPage.tsx
 * 
 * 特性：
 * - 多层发光节点
 * - 贝塞尔曲线连线
 * - 流光粒子系统
 * - 3D 球形背景星空
 * - 平滑缓动动画
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun KnowledgeGraphScreen(
    token: String,
    userId: String,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val app = context.applicationContext as LifeSwarmApp
    
    // 创建 ViewModel
    val viewModel: KnowledgeGraphViewModel = viewModel(
        factory = KnowledgeGraphViewModelFactory(
            repository = app.knowledgeGraphRepository,
            userId = userId
        )
    )
    
    // 收集状态
    val uiState by viewModel.uiState.collectAsState()
    val selectedView by viewModel.selectedView.collectAsState()
    val nodes by viewModel.nodes.collectAsState()
    val edges by viewModel.edges.collectAsState()
    
    // OpenGL 渲染器 - 使用增强版
    val renderer = remember { EnhancedKnowledgeGraphRenderer() }
    
    // 选中的节点 - OpenGL渲染用
    var selectedRenderNode by remember { mutableStateOf<com.lifeswarm.android.presentation.knowledge.opengl.Node?>(null) }
    
    // 选中的节点 - 数据模型用（用于侧边栏）
    var selectedGraphNode by remember { mutableStateOf<com.lifeswarm.android.data.model.KnowledgeGraphNode?>(null) }
    
    // 当数据更新时，更新渲染器
    LaunchedEffect(nodes, edges) {
        println("[KnowledgeGraphScreen] 数据更新: nodes=${nodes.size}, edges=${edges.size}")
        if (nodes.isNotEmpty()) {
            println("[KnowledgeGraphScreen] 开始更新渲染器...")
            renderer.updateGraph(nodes, edges)
            println("[KnowledgeGraphScreen] 渲染器更新完成")
        }
    }
    
    // 初始加载数据
    LaunchedEffect(Unit) {
        println("=".repeat(60))
        println("[KnowledgeGraphScreen] ========== 知识星图页面已加载 ==========")
        println("[KnowledgeGraphScreen] 版本: 2026-04-21-16:45 (真机调试版本)")
        println("[KnowledgeGraphScreen] userId: $userId")
        println("=".repeat(60))
        viewModel.loadGraphData()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("知识星图") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadGraphData() }) {
                        Icon(Icons.Default.Refresh, "刷新")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // 视图切换按钮
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterChip(
                    selected = selectedView == "people",
                    onClick = { viewModel.switchView("people") },
                    label = { Text("人际关系") },
                    leadingIcon = if (selectedView == "people") {
                        { Icon(Icons.Default.Check, null, Modifier.size(18.dp)) }
                    } else null,
                    modifier = Modifier.weight(1f)
                )
                FilterChip(
                    selected = selectedView == "career",
                    onClick = { viewModel.switchView("career") },
                    label = { Text("职业发展") },
                    leadingIcon = if (selectedView == "career") {
                        { Icon(Icons.Default.Check, null, Modifier.size(18.dp)) }
                    } else null,
                    modifier = Modifier.weight(1f)
                )
                FilterChip(
                    selected = selectedView == "education",
                    onClick = { viewModel.switchView("education") },
                    label = { Text("升学规划") },
                    leadingIcon = if (selectedView == "education") {
                        { Icon(Icons.Default.Check, null, Modifier.size(18.dp)) }
                    } else null,
                    modifier = Modifier.weight(1f)
                )
            }
            
            // 内容区域
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                when (uiState) {
                    is KnowledgeGraphUiState.Loading -> {
                        // 加载中
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(16.dp)
                            ) {
                                CircularProgressIndicator()
                                Text(
                                    "正在加载知识图谱...",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                    
                    is KnowledgeGraphUiState.Error -> {
                        // 错误状态
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(16.dp),
                                modifier = Modifier.padding(32.dp)
                            ) {
                                Icon(
                                    Icons.Default.Warning,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.error,
                                    modifier = Modifier.size(48.dp)
                                )
                                Text(
                                    "加载失败",
                                    style = MaterialTheme.typography.titleMedium,
                                    color = MaterialTheme.colorScheme.error
                                )
                                Text(
                                    (uiState as KnowledgeGraphUiState.Error).message,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Button(onClick = { viewModel.loadGraphData() }) {
                                    Icon(Icons.Default.Refresh, null)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("重试")
                                }
                            }
                        }
                    }
                    
                    is KnowledgeGraphUiState.Success -> {
                        Box(modifier = Modifier.fillMaxSize()) {
                            // 视图尺寸状态
                            var viewWidth by remember { mutableStateOf(0) }
                            var viewHeight by remember { mutableStateOf(0) }
                            var currentMVPMatrix by remember { mutableStateOf(FloatArray(16)) }
                            
                            // OpenGL ES 3.0 增强版 3D 视图
                            AndroidView(
                                factory = { ctx ->
                                    GLSurfaceView(ctx).apply {
                                        // 使用 OpenGL ES 3.0
                                        setEGLContextClientVersion(3)
                                        setRenderer(renderer)
                                        renderMode = GLSurfaceView.RENDERMODE_CONTINUOUSLY
                                        
                                        // 保存视图尺寸
                                        post {
                                            viewWidth = width
                                            viewHeight = height
                                        }
                                        
                                        // 定期更新 MVP 矩阵（用于文字标签投影）
                                        val updateRunnable = object : Runnable {
                                            override fun run() {
                                                currentMVPMatrix = renderer.getMVPMatrix()
                                                postDelayed(this, 16) // 60 FPS
                                            }
                                        }
                                        post(updateRunnable)
                                        
                                        // 触摸手势处理
                                        var lastX = 0f
                                        var lastY = 0f
                                        var lastDistance = 0f
                                        var isSingleTap = false
                                        var tapStartTime = 0L
                                        
                                        setOnTouchListener { view, event ->
                                            when (event.actionMasked) {
                                                MotionEvent.ACTION_DOWN -> {
                                                    lastX = event.x
                                                    lastY = event.y
                                                    isSingleTap = true
                                                    tapStartTime = System.currentTimeMillis()
                                                }
                                                MotionEvent.ACTION_MOVE -> {
                                                    if (event.pointerCount == 1) {
                                                        // 单指拖动
                                                        val deltaX = event.x - lastX
                                                        val deltaY = event.y - lastY
                                                        
                                                        // 如果移动距离超过阈值，不算点击
                                                        if (kotlin.math.abs(deltaX) > 10 || kotlin.math.abs(deltaY) > 10) {
                                                            isSingleTap = false
                                                            renderer.rotateCamera(deltaX, deltaY)
                                                        }
                                                        
                                                        lastX = event.x
                                                        lastY = event.y
                                                    } else if (event.pointerCount == 2) {
                                                        // 双指缩放
                                                        isSingleTap = false
                                                        val dx = event.getX(0) - event.getX(1)
                                                        val dy = event.getY(0) - event.getY(1)
                                                        val distance = sqrt(dx * dx + dy * dy)
                                                        
                                                        if (lastDistance > 0) {
                                                            val scale = distance / lastDistance
                                                            // 修复：使用当前相机距离而不是固定值
                                                            val currentDistance = renderer.getCameraDistance()
                                                            val newDistance = currentDistance / scale
                                                            renderer.setCameraDistance(newDistance)
                                                            println("[KnowledgeGraph] 缩放: scale=$scale, distance=$newDistance")
                                                        }
                                                        lastDistance = distance
                                                    }
                                                }
                                                MotionEvent.ACTION_UP -> {
                                                    // 检测单击
                                                    if (isSingleTap && System.currentTimeMillis() - tapStartTime < 300) {
                                                        // 检测点击的节点
                                                        val clickedNode = renderer.detectNodeClick(
                                                            event.x,
                                                            event.y,
                                                            view.width,
                                                            view.height
                                                        )
                                                        
                                                        if (clickedNode != null) {
                                                            // 查找对应的KnowledgeGraphNode
                                                            val currentGraphData = (uiState as? KnowledgeGraphUiState.Success)?.data
                                                            val graphNode = currentGraphData?.nodes?.find { it.id == clickedNode.id }
                                                            if (graphNode != null) {
                                                                selectedRenderNode = clickedNode
                                                                selectedGraphNode = graphNode
                                                                renderer.focusOnNode(clickedNode.id)
                                                                println("[KnowledgeGraph] 点击节点: ${clickedNode.label}")
                                                            }
                                                        } else {
                                                            // 点击空白处，重置相机
                                                            selectedRenderNode = null
                                                            selectedGraphNode = null
                                                            renderer.resetCamera()
                                                        }
                                                    }
                                                    lastDistance = 0f
                                                }
                                                MotionEvent.ACTION_POINTER_UP -> {
                                                    lastDistance = 0f
                                                }
                                            }
                                            true
                                        }
                                    }
                                },
                                modifier = Modifier.fillMaxSize()
                            )
                            
                            // 节点标签文字层（叠加在 OpenGL 视图上方）
                            if (viewWidth > 0 && viewHeight > 0) {
                                NodeLabelsOverlay(
                                    nodes = nodes,
                                    mvpMatrix = currentMVPMatrix,
                                    viewWidth = viewWidth,
                                    viewHeight = viewHeight,
                                    selectedNodeId = selectedGraphNode?.id,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }
                            
                            // 节点详情侧边栏 - 对应 Web 端实现
                            NodeDetailPanel(
                                selectedNode = selectedGraphNode,
                                graph = (uiState as? KnowledgeGraphUiState.Success)?.data,
                                viewMode = selectedView,
                                onClose = {
                                    selectedRenderNode = null
                                    selectedGraphNode = null
                                    renderer.resetCamera()
                                },
                                onDelete = { node ->
                                    // TODO: 实现删除节点功能
                                    println("[KnowledgeGraph] 删除节点: ${node.name}")
                                },
                                onNavigateToNode = { node ->
                                    // 导航到指定节点
                                    selectedGraphNode = node
                                    renderer.focusOnNode(node.id)
                                    println("[KnowledgeGraph] 导航到节点: ${node.name}")
                                },
                                modifier = Modifier.align(Alignment.CenterEnd)
                            )
                            
                            // 操作提示（仅在未选中节点时显示）
                            if (selectedGraphNode == null) {
                                Card(
                                    modifier = Modifier
                                        .align(Alignment.BottomStart)
                                        .padding(16.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.9f)
                                    )
                                ) {
                                    Column(
                                        modifier = Modifier.padding(12.dp)
                                    ) {
                                        Text(
                                            "操作提示",
                                            style = MaterialTheme.typography.labelMedium,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            "• 单击节点：查看详情",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        Text(
                                            "• 单指拖动：旋转视角",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        Text(
                                            "• 双指缩放：调整距离",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        Text(
                                            "• 点击空白：重置视角",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }
                            }
                            
                            // 节点统计信息
                            Card(
                                modifier = Modifier
                                    .align(Alignment.TopEnd)
                                    .padding(16.dp),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.9f)
                                )
                            ) {
                                Column(
                                    modifier = Modifier.padding(12.dp)
                                ) {
                                    Text(
                                        "节点: ${nodes.size}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onPrimaryContainer
                                    )
                                    Text(
                                        "连线: ${edges.size}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onPrimaryContainer
                                    )
                                }
                            }
                        }
                    }
                }
            }
            
            // 底部信息
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                )
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.secondary,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        when (selectedView) {
                            "people" -> "人际关系图谱 - 展示您的社交网络"
                            "career" -> "职业发展图谱 - 展示您的职业路径"
                            "education" -> "升学规划图谱 - 展示您的学习路径"
                            else -> ""
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSecondaryContainer
                    )
                }
            }
        }
    }
}

