package com.lifeswarm.android.presentation.decision

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.lifecycle.viewmodel.compose.viewModel
import com.lifeswarm.android.data.model.CollectedInfo
import com.lifeswarm.android.data.model.OptionInput
import com.lifeswarm.android.data.model.PersonaAgent
import com.lifeswarm.android.data.model.PersonaStatus
import com.lifeswarm.android.data.model.ThinkingRecord
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.PI

/**
 * 增强版决策推演页面 - 圆形布局可视化
 * 对应 Web 端的 PersonaInteractionView
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EnhancedSimulationScreen(
    sessionId: String,
    userId: String,
    question: String,
    options: List<OptionInput>,
    collectedInfo: CollectedInfo? = null,
    decisionType: String = "general",
    onNavigateBack: () -> Unit
) {
    // 使用增强版 ViewModel
    val viewModel: EnhancedDecisionSimulationViewModel = viewModel(
        factory = EnhancedDecisionSimulationViewModelFactory(
            sessionId = sessionId,
            userId = userId,
            question = question,
            options = options,
            collectedInfo = collectedInfo,
            decisionType = decisionType
        )
    )
    
    val uiState by viewModel.uiState.collectAsState()
    
    // 缩放和平移状态
    var scale by remember { mutableStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    
    // 选中的 Agent（用于显示历史）
    var selectedAgent by remember { mutableStateOf<PersonaAgent?>(null) }
    
    // 获取当前活动选项的状态
    val activeOptionState = uiState.optionStates[uiState.activeOptionId]
    
    Scaffold(
        topBar = {
            Column {
                TopAppBar(
                    title = {
                        Column {
                            Text(
                                "决策图谱舞台",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                question,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1
                            )
                        }
                    },
                    navigationIcon = {
                        IconButton(onClick = onNavigateBack) {
                            Icon(Icons.Default.ArrowBack, "返回")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface
                    )
                )
                
                // 选项切换标签栏
                if (uiState.optionStates.isNotEmpty()) {
                    OptionTabsBar(
                        optionStates = uiState.optionStates,
                        activeOptionId = uiState.activeOptionId,
                        onSelectOption = { optionId ->
                            viewModel.switchToOption(optionId)
                        },
                        onPauseOption = { optionId ->
                            viewModel.pauseOption(optionId)
                        },
                        onResumeOption = { optionId ->
                            viewModel.resumeOption(optionId)
                        }
                    )
                }
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(
                            MaterialTheme.colorScheme.surface,
                            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
                        )
                    )
                )
        ) {
            // 显示当前活动选项的内容
            if (activeOptionState != null) {
                if (activeOptionState.agents.isNotEmpty()) {
                    CircularAgentsView(
                        agents = activeOptionState.agents,
                        totalScore = activeOptionState.totalScore,
                        optionTitle = activeOptionState.optionTitle,
                        currentMonth = activeOptionState.currentMonth,
                        isComplete = activeOptionState.isComplete,
                        scale = scale,
                        offset = offset,
                        onScaleChange = { scale = it },
                        onOffsetChange = { offset = it },
                        onAgentClick = { agent -> selectedAgent = agent }
                    )
                } else if (activeOptionState.isPaused) {
                    EnhancedConnectingView("推演已暂停")
                } else {
                    EnhancedConnectingView("等待 Agent 启动...")
                }
            } else if (uiState.error.isNotEmpty()) {
                EnhancedErrorView(uiState.error)
            } else {
                EnhancedConnectingView(uiState.currentStatus)
            }
            
            // 缩放控制按钮
            if (activeOptionState?.agents?.isNotEmpty() == true) {
                ZoomControls(
                    scale = scale,
                    onZoomIn = { scale = (scale * 1.2f).coerceAtMost(2f) },
                    onZoomOut = { scale = (scale * 0.8f).coerceAtLeast(0.5f) },
                    onReset = {
                        scale = 1f
                        offset = Offset.Zero
                    },
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(16.dp)
                )
            }
            
            // 完成标记
            if (activeOptionState?.isComplete == true) {
                Card(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 120.dp, end = 16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            "分析完成",
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
    
    // 思考历史弹窗
    if (selectedAgent != null) {
        PersonaThinkingHistoryDialog(
            agent = selectedAgent!!,
            onDismiss = { selectedAgent = null }
        )
    }
}

/**
 * 圆形 Agents 视图
 */
@Composable
fun CircularAgentsView(
    agents: List<PersonaAgent>,
    totalScore: Double,
    optionTitle: String,
    currentMonth: Int,
    isComplete: Boolean,
    scale: Float,
    offset: Offset,
    onScaleChange: (Float) -> Unit,
    onOffsetChange: (Offset) -> Unit,
    onAgentClick: (PersonaAgent) -> Unit
) {
    BoxWithConstraints(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectDragGestures { change, dragAmount ->
                    change.consume()
                    onOffsetChange(offset + dragAmount)
                }
            }
    ) {
        val containerWidth = constraints.maxWidth.toFloat()
        val containerHeight = constraints.maxHeight.toFloat()
        val centerX = containerWidth / 2
        val centerY = containerHeight / 2
        
        // 计算半径（基于容器大小）
        val radius = minOf(containerWidth, containerHeight) * 0.35f
        
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = scale,
                    scaleY = scale,
                    translationX = offset.x,
                    translationY = offset.y
                )
        ) {
            // 中心选项卡片
            Box(
                modifier = Modifier
                    .size(160.dp)
                    .align(Alignment.Center)
            ) {
                CenterOptionCard(
                    title = optionTitle,
                    totalScore = totalScore,
                    currentMonth = currentMonth
                )
            }
            
            // Agents 圆形排列
            agents.forEachIndexed { index, agent ->
                val angle = (index.toFloat() / agents.size) * 2 * PI.toFloat() - PI.toFloat() / 2
                val agentX = centerX + radius * cos(angle)
                val agentY = centerY + radius * sin(angle)
                
                Box(
                    modifier = Modifier
                        .offset {
                            IntOffset(
                                (agentX - 60.dp.toPx()).toInt(),
                                (agentY - 60.dp.toPx()).toInt()
                            )
                        }
                        .size(120.dp)
                ) {
                    AgentSphere(
                        agent = agent,
                        onClick = { onAgentClick(agent) }
                    )
                }
            }
        }
    }
}

/**
 * Agent 球体
 */
@Composable
fun AgentSphere(
    agent: PersonaAgent,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.fillMaxSize()
    ) {
        // 球体
        Box(
            modifier = Modifier
                .size(80.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            when (agent.status) {
                                PersonaStatus.WAITING -> Color(0xFF64B5F6)
                                PersonaStatus.THINKING -> Color(0xFFFFB74D)
                                PersonaStatus.COMPLETE -> Color(0xFF81C784)
                                PersonaStatus.ERROR -> Color(0xFFE57373)
                            },
                            when (agent.status) {
                                PersonaStatus.WAITING -> Color(0xFF1976D2)
                                PersonaStatus.THINKING -> Color(0xFFF57C00)
                                PersonaStatus.COMPLETE -> Color(0xFF388E3C)
                                PersonaStatus.ERROR -> Color(0xFFC62828)
                            }
                        )
                    )
                )
                .clickable(onClick = onClick),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Agent 名称
                Text(
                    agent.name,
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    textAlign = TextAlign.Center
                )
                
                // 评分
                if (agent.score != null) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "${agent.score.toInt()}",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
                
                // 状态指示器
                if (agent.status == PersonaStatus.THINKING) {
                    Spacer(modifier = Modifier.height(4.dp))
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = Color.White
                    )
                }
            }
        }
        
        // 立场标签
        if (agent.stance != null) {
            Spacer(modifier = Modifier.height(4.dp))
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.9f)
            ) {
                Text(
                    agent.stance ?: "",
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        // 消息气泡
        if (agent.currentMessage != null && agent.status == PersonaStatus.THINKING) {
            Spacer(modifier = Modifier.height(4.dp))
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f),
                shadowElevation = 4.dp
            ) {
                Text(
                    agent.currentMessage ?: "",
                    modifier = Modifier
                        .widthIn(max = 100.dp)
                        .padding(8.dp),
                    style = MaterialTheme.typography.bodySmall,
                    maxLines = 2,
                    overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                )
            }
        }
    }
}

/**
 * 中心选项卡片
 */
@Composable
fun CenterOptionCard(
    title: String,
    totalScore: Double,
    currentMonth: Int
) {
    Card(
        modifier = Modifier.fillMaxSize(),
        shape = CircleShape,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                maxLines = 2,
                modifier = Modifier.padding(horizontal = 16.dp)
            )
            
            if (currentMonth > 0) {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "第 $currentMonth 轮",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                )
            }
            
            if (totalScore > 0) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    String.format("%.1f", totalScore),
                    style = MaterialTheme.typography.displayMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    "综合评分",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                )
            }
        }
    }
}

/**
 * Agent 节点
 */
@Composable
fun BoxScope.AgentNode(
    agent: AgentState,
    position: Offset,
    onClick: () -> Unit
) {
    val statusColor = when (agent.status) {
        AgentStatus.WAITING -> Color.Gray
        AgentStatus.THINKING -> Color(0xFF2196F3)
        AgentStatus.COMPLETE -> Color(0xFF4CAF50)
        AgentStatus.ERROR -> Color(0xFFF44336)
    }
    
    // 思考中的脉冲动画
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .wrapContentSize(Alignment.TopStart)
            .offset(
                x = (position.x * 1000).dp,
                y = (position.y * 1000).dp
            )
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.offset(x = (-60).dp, y = (-60).dp)
        ) {
            // Agent 球体
            Box(
                modifier = Modifier
                    .size(120.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                Color.White.copy(alpha = 0.98f),
                                Color(0xFFE8F4FF),
                                Color(0xFFB8DCFF)
                            )
                        )
                    )
                    .pointerInput(Unit) {
                        detectTapGestures { onClick() }
                    },
                contentAlignment = Alignment.Center
            ) {
                // 状态指示器
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .align(Alignment.TopEnd)
                        .offset(x = (-8).dp, y = 8.dp)
                        .clip(CircleShape)
                        .background(statusColor.copy(alpha = if (agent.status == AgentStatus.THINKING) pulseAlpha else 1f))
                )
                
                // Agent 名称（球体内）
                Text(
                    agent.name,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.padding(8.dp)
                )
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // 评分
            if (agent.score != null) {
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.primaryContainer,
                    shadowElevation = 4.dp
                ) {
                    Text(
                        String.format("%.0f", agent.score),
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
            
            // 立场
            if (agent.stance != null) {
                Spacer(modifier = Modifier.height(4.dp))
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = when {
                        agent.stance.contains("支持") -> Color(0xFF4CAF50).copy(alpha = 0.2f)
                        agent.stance.contains("反对") -> Color(0xFFF44336).copy(alpha = 0.2f)
                        else -> Color.Gray.copy(alpha = 0.2f)
                    }
                ) {
                    Text(
                        agent.stance,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        fontSize = 10.sp
                    )
                }
            }
            
            // 当前消息气泡
            if (agent.currentMessage != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.secondaryContainer,
                    shadowElevation = 2.dp,
                    modifier = Modifier
                        .widthIn(max = 200.dp)
                        .pointerInput(Unit) {
                            detectTapGestures { onClick() }
                        }
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp)
                    ) {
                        Text(
                            agent.currentMessage.take(50) + if (agent.currentMessage.length > 50) "..." else "",
                            style = MaterialTheme.typography.bodySmall,
                            fontSize = 11.sp,
                            lineHeight = 14.sp
                        )
                        Text(
                            "详细 →",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.padding(top = 4.dp)
                        )
                    }
                }
            }
            
            // 查看历史按钮
            if (agent.thinkingHistory.isNotEmpty()) {
                Spacer(modifier = Modifier.height(4.dp))
                IconButton(
                    onClick = onClick,
                    modifier = Modifier.size(32.dp)
                ) {
                    Icon(
                        Icons.Default.History,
                        contentDescription = "查看历史",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}

/**
 * 分数影响动画
 */
@Composable
fun BoxScope.ScoreImpactAnimation(
    agentPosition: Offset,
    centerPosition: Offset
) {
    val infiniteTransition = rememberInfiniteTransition(label = "scoreImpact")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 0.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "alpha"
    )
    
    Canvas(
        modifier = Modifier.fillMaxSize()
    ) {
        val start = Offset(
            agentPosition.x * size.width,
            agentPosition.y * size.height
        )
        val end = Offset(
            centerPosition.x * size.width,
            centerPosition.y * size.height
        )
        
        drawLine(
            color = Color(0xFF2196F3).copy(alpha = alpha),
            start = start,
            end = end,
            strokeWidth = 3f,
            pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f))
        )
    }
}

/**
 * 缩放控制按钮
 */
@Composable
fun ZoomControls(
    scale: Float,
    onZoomIn: () -> Unit,
    onZoomOut: () -> Unit,
    onReset: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            IconButton(
                onClick = onZoomIn,
                modifier = Modifier.size(36.dp)
            ) {
                Icon(Icons.Default.Add, "放大")
            }
            
            IconButton(
                onClick = onZoomOut,
                modifier = Modifier.size(36.dp)
            ) {
                Icon(Icons.Default.Remove, "缩小")
            }
            
            IconButton(
                onClick = onReset,
                modifier = Modifier.size(36.dp)
            ) {
                Icon(Icons.Default.Refresh, "重置")
            }
            
            Text(
                "${(scale * 100).toInt()}%",
                style = MaterialTheme.typography.labelSmall,
                textAlign = TextAlign.Center,
                modifier = Modifier.width(36.dp)
            )
        }
    }
}

/**
 * 思考历史对话框
 */
@Composable
fun PersonaThinkingHistoryDialog(
    agent: PersonaAgent,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight(0.8f),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier.fillMaxSize()
            ) {
                // 标题栏
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.primaryContainer)
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "【${agent.name}】的思考历程",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, "关闭")
                    }
                }
                
                // 当前状态
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.secondaryContainer
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        if (agent.stance != null) {
                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = when {
                                    agent.stance.contains("支持") -> Color(0xFF4CAF50).copy(alpha = 0.2f)
                                    agent.stance.contains("反对") -> Color(0xFFF44336).copy(alpha = 0.2f)
                                    else -> Color.Gray.copy(alpha = 0.2f)
                                }
                            ) {
                                Text(
                                    agent.stance,
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                    style = MaterialTheme.typography.labelMedium,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                        
                        if (agent.score != null) {
                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = MaterialTheme.colorScheme.primaryContainer
                            ) {
                                Text(
                                    "${agent.score.toInt()}分",
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                    style = MaterialTheme.typography.labelMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                        }
                    }
                }
                
                // 历史记录列表
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    itemsIndexed(agent.thinkingHistory) { index, record ->
                        ThinkingRecordCard(record, index + 1)
                    }
                }
            }
        }
    }
}

/**
 * 思考记录卡片
 */
@Composable
fun ThinkingRecordCard(record: ThinkingRecord, roundNumber: Int) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(12.dp)
        ) {
            // 头部
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    "第 ${record.round} 轮",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (record.stance != null) {
                        Text(
                            record.stance,
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    if (record.score != null) {
                        Text(
                            "${record.score.toInt()}分",
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // 消息内容
            Text(
                record.message,
                style = MaterialTheme.typography.bodyMedium,
                lineHeight = 20.sp
            )
            
            // 关键论点
            if (record.keyPoints.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "关键论点:",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold
                )
                record.keyPoints.forEach { point ->
                    Text(
                        "• $point",
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(start = 8.dp, top = 2.dp)
                    )
                }
            }
            
            // 推理过程
            if (!record.reasoning.isNullOrEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "推理过程:",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    record.reasoning ?: "",
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(start = 8.dp, top = 2.dp)
                )
            }
            
            // 时间戳
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault())
                    .format(java.util.Date(record.timestamp)),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
            )
        }
    }
}


/**
 * 连接中视图 - 增强版专用
 */
@Composable
private fun EnhancedConnectingView(statusMessage: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(48.dp),
            strokeWidth = 4.dp
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            statusMessage.ifEmpty { "正在连接推演引擎..." },
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Medium
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            "等待推演引擎启动...",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * 错误视图 - 增强版专用
 */
@Composable
private fun EnhancedErrorView(errorMessage: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            Icons.Default.Error,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.error
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            "推演出错",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            errorMessage,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 32.dp)
        )
    }
}
