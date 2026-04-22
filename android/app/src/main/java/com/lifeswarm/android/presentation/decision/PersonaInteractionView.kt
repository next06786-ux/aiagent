package com.lifeswarm.android.presentation.decision

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.compose.ui.zIndex
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.PI

/**
 * 7个Agent球体交互视图 - 对应Web端PersonaInteractionView
 * 特点：圆形排列、玻璃质感、实时消息、分数动画
 */
@Composable
fun PersonaInteractionView(
    agents: List<AgentState>,
    totalScore: Double,
    optionTitle: String,
    isComplete: Boolean = false
) {
    // 缩放和平移状态
    var scale by remember { mutableStateOf(1f) }
    var offsetX by remember { mutableStateOf(0f) }
    var offsetY by remember { mutableStateOf(0f) }
    
    // 选中的Agent（用于显示历史记录）
    var selectedAgent by remember { mutableStateOf<AgentState?>(null) }
    
    // 分数影响动画状态
    val scoreAnimations = remember { mutableStateListOf<ScoreAnimation>() }
    
    // 监听agents的score变化，触发动画
    LaunchedEffect(agents) {
        agents.forEach { agent ->
            if (agent.score != null && agent.status == AgentStatus.COMPLETE) {
                val hasAnimation = scoreAnimations.any { it.agentId == agent.id }
                if (!hasAnimation) {
                    val animId = "${agent.id}_${System.currentTimeMillis()}"
                    scoreAnimations.add(ScoreAnimation(animId, agent.id, System.currentTimeMillis()))
                    
                    // 1.5秒后移除动画
                    kotlinx.coroutines.delay(1500)
                    scoreAnimations.removeAll { it.id == animId }
                }
            }
        }
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        Color(0x28B8DCFF),
                        Color(0x00B8DCFF)
                    )
                )
            )
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, _ ->
                    scale = (scale * zoom).coerceIn(0.5f, 2f)
                    offsetX += pan.x
                    offsetY += pan.y
                }
            }
    ) {
        // 缩放控制按钮
        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(20.dp)
                .zIndex(100f),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = Color.White.copy(alpha = 0.95f),
                shadowElevation = 4.dp
            ) {
                Column(
                    modifier = Modifier.padding(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    IconButton(
                        onClick = { scale = (scale * 1.2f).coerceAtMost(2f) },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Icon(Icons.Default.Add, "放大", tint = Color(0xFF0A59F7))
                    }
                    IconButton(
                        onClick = { scale = (scale * 0.8f).coerceAtLeast(0.5f) },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Icon(Icons.Default.Remove, "缩小", tint = Color(0xFF0A59F7))
                    }
                    IconButton(
                        onClick = {
                            scale = 1f
                            offsetX = 0f
                            offsetY = 0f
                        },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Icon(Icons.Default.Refresh, "重置", tint = Color(0xFF0A59F7))
                    }
                    Text(
                        "${(scale * 100).toInt()}%",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF64748B),
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
        
        // 完成标记
        if (isComplete) {
            Surface(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(top = 80.dp, end = 24.dp)
                    .zIndex(9999f),
                shape = RoundedCornerShape(12.dp),
                color = Color.White.copy(alpha = 0.98f),
                shadowElevation = 8.dp
            ) {
                Row(
                    modifier = Modifier.padding(12.dp, 24.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = Color(0xFF34C759),
                        modifier = Modifier.size(20.dp)
                    )
                    Text(
                        "分析完成",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF34C759)
                    )
                }
            }
        }
        
        // 可缩放的内容容器
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = scale,
                    scaleY = scale,
                    translationX = offsetX,
                    translationY = offsetY
                )
        ) {
            // 中心选项球体
            CenterOptionSphere(
                optionTitle = optionTitle,
                totalScore = totalScore
            )
            
            // 7个Agent球体
            agents.forEachIndexed { index, agent ->
                AgentSphere(
                    agent = agent,
                    index = index,
                    total = agents.size,
                    onAgentClick = { selectedAgent = agent }
                )
            }
            
            // 分数影响动画
            scoreAnimations.forEach { anim ->
                val agentIndex = agents.indexOfFirst { it.id == anim.agentId }
                if (agentIndex != -1) {
                    ScoreImpactAnimation(
                        agentIndex = agentIndex,
                        totalAgents = agents.size
                    )
                }
            }
        }
        
        // Agent历史记录弹窗
        if (selectedAgent != null) {
            AgentHistoryDialog(
                agent = selectedAgent!!,
                onDismiss = { selectedAgent = null }
            )
        }
    }
}

/**
 * 中心选项球体
 */
@Composable
fun BoxScope.CenterOptionSphere(
    optionTitle: String,
    totalScore: Double
) {
    Box(
        modifier = Modifier
            .align(Alignment.Center)
            .size(200.dp)
            .clip(CircleShape)
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        Color(0xFFFFFFF),
                        Color(0xFFF8FCFF),
                        Color(0xFFE8F4FF),
                        Color(0xFFC8E2FF)
                    ),
                    center = Offset(0.3f, 0.2f)
                )
            )
            .zIndex(5f),
        contentAlignment = Alignment.Center
    ) {
        // 高光效果
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        Color.White.copy(alpha = 0.55f),
                        Color.Transparent
                    ),
                    center = Offset(size.width * 0.34f, size.height * 0.26f),
                    radius = size.minDimension * 0.26f
                )
            )
        }
        
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                optionTitle,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A),
                textAlign = TextAlign.Center,
                maxLines = 2,
                modifier = Modifier.padding(horizontal = 16.dp)
            )
            
            Text(
                String.format("%.1f", totalScore),
                fontSize = 36.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            )
            
            Text(
                "综合评分",
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                color = Color(0x8C1A1A1A),
                letterSpacing = 0.5.sp
            )
        }
    }
}

/**
 * Agent球体
 */
@Composable
fun BoxScope.AgentSphere(
    agent: AgentState,
    index: Int,
    total: Int,
    onAgentClick: () -> Unit
) {
    val position = getAgentPosition(index, total)
    
    Box(
        modifier = Modifier
            .align(Alignment.Center)
            .offset(
                x = (position.x * 3.5).dp,
                y = (position.y * 3.5).dp
            )
            .size(120.dp)
            .zIndex(10f)
            .pointerInput(Unit) {
                detectTapGestures(onTap = { onAgentClick() })
            }
    ) {
        // Agent球体
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFFFFFFF),
                            Color(0xFFF8FCFF),
                            Color(0xFFE8F4FF),
                            Color(0xFFB8DCFF)
                        ),
                        center = Offset(0.3f, 0.2f)
                    )
                ),
            contentAlignment = Alignment.Center
        ) {
            // 高光效果
            Canvas(modifier = Modifier.fillMaxSize()) {
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            Color.White.copy(alpha = 0.55f),
                            Color.Transparent
                        ),
                        center = Offset(size.width * 0.34f, size.height * 0.26f),
                        radius = size.minDimension * 0.26f
                    )
                )
            }
            
            // Agent图标/名称
            Text(
                agent.name.take(2),
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            )
        }
        
        // Agent名称标签
        Text(
            agent.name,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xCC1A1A1A),
            textAlign = TextAlign.Center,
            modifier = Modifier
                .align(if (position.y < 0) Alignment.TopCenter else Alignment.BottomCenter)
                .offset(y = if (position.y < 0) (-28).dp else 28.dp)
                .background(
                    Color.White.copy(alpha = 0.95f),
                    RoundedCornerShape(12.dp)
                )
                .padding(horizontal = 14.dp, vertical = 5.dp)
        )
        
        // 状态指示器
        if (agent.status == AgentStatus.THINKING) {
            Text(
                "思考中...",
                fontSize = 9.sp,
                fontWeight = FontWeight.SemiBold,
                color = Color(0x801A1A1A),
                modifier = Modifier
                    .align(if (position.y < 0) Alignment.TopCenter else Alignment.BottomCenter)
                    .offset(y = if (position.y < 0) (-55).dp else 55.dp)
                    .background(
                        Color.White.copy(alpha = 0.95f),
                        RoundedCornerShape(10.dp)
                    )
                    .padding(horizontal = 10.dp, vertical = 3.dp)
            )
        }
        
        // 评分显示
        if (agent.score != null) {
            Surface(
                modifier = Modifier
                    .align(if (position.y < 0) Alignment.TopCenter else Alignment.BottomCenter)
                    .offset(y = if (position.y < 0) (-68).dp else 68.dp),
                shape = RoundedCornerShape(12.dp),
                color = Color.White,
                shadowElevation = 4.dp
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(2.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        agent.score.toString(),
                        fontSize = 16.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = Color(0xFF1A1A1A)
                    )
                    Text(
                        "分",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF999999)
                    )
                }
            }
        }
        
        // 立场标签
        if (agent.stance != null) {
            val stanceColor = when {
                agent.stance.contains("支持") -> Color(0xFF34C759)
                agent.stance.contains("反对") -> Color(0xFFFF3B30)
                else -> Color(0xFF8E8E93)
            }
            
            Surface(
                modifier = Modifier
                    .align(if (position.y < 0) Alignment.TopCenter else Alignment.BottomCenter)
                    .offset(y = if (position.y < 0) (-110).dp else 110.dp),
                shape = RoundedCornerShape(8.dp),
                color = stanceColor.copy(alpha = 0.1f)
            ) {
                Text(
                    agent.stance,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = stanceColor,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                )
            }
        }
        
        // 查看历史按钮
        if (agent.thinkingHistory?.isNotEmpty() == true) {
            IconButton(
                onClick = onAgentClick,
                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .offset(x = 50.dp)
                    .size(32.dp)
                    .background(Color.White, CircleShape)
            ) {
                Icon(
                    Icons.Default.Info,
                    contentDescription = "查看历史",
                    tint = Color(0xFF0A59F7),
                    modifier = Modifier.size(16.dp)
                )
            }
        }
        
        // 当前消息气泡
        if (agent.currentMessage != null) {
            Surface(
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(
                        x = (position.x * 0.5).dp,
                        y = (position.y * 0.5).dp
                    )
                    .width(160.dp)
                    .zIndex(5f),
                shape = RoundedCornerShape(12.dp),
                color = Color.White,
                shadowElevation = 8.dp
            ) {
                Column(
                    modifier = Modifier.padding(10.dp, 12.dp)
                ) {
                    Text(
                        agent.currentMessage.take(30) + if (agent.currentMessage.length > 30) "..." else "",
                        fontSize = 11.sp,
                        lineHeight = 16.sp,
                        color = Color(0xFF1A1A1A),
                        maxLines = 3
                    )
                    Text(
                        "详细 →",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF0A59F7),
                        modifier = Modifier
                            .align(Alignment.End)
                            .padding(top = 6.dp)
                    )
                }
            }
        }
    }
}

/**
 * 分数影响动画 - 从Agent到中心的连线
 */
@Composable
fun BoxScope.ScoreImpactAnimation(
    agentIndex: Int,
    totalAgents: Int
) {
    val agentPos = getAgentPosition(agentIndex, totalAgents)
    val infiniteTransition = rememberInfiniteTransition(label = "score_impact")
    
    val progress by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "progress"
    )
    
    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .zIndex(15f)
    ) {
        val centerX = size.width / 2
        val centerY = size.height / 2
        val agentX = centerX + agentPos.x * 3.5f * density
        val agentY = centerY + agentPos.y * 3.5f * density
        
        val currentX = agentX + (centerX - agentX) * progress
        val currentY = agentY + (centerY - agentY) * progress
        
        drawLine(
            brush = Brush.linearGradient(
                colors = listOf(
                    Color(0x00475569),
                    Color(0xFF475569),
                    Color(0x00475569)
                )
            ),
            start = Offset(agentX, agentY),
            end = Offset(centerX, centerY),
            strokeWidth = 3f,
            alpha = 1f - progress
        )
        
        drawCircle(
            color = Color(0xFF475569),
            radius = 4f,
            center = Offset(currentX, currentY),
            alpha = 1f - progress
        )
    }
}

/**
 * Agent历史记录弹窗
 */
@Composable
fun AgentHistoryDialog(
    agent: AgentState,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .fillMaxHeight(0.8f),
            shape = RoundedCornerShape(16.dp),
            color = Color.White
        ) {
            Column {
                // 标题栏
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp, 24.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "【${agent.name}】的思考历程",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1A1A1A)
                    )
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, "关闭")
                    }
                }
                
                Divider(color = Color(0xFFE2E8F0))
                
                // 内容
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // 当前状态
                    item {
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = Color(0x0D0A59F7)
                        ) {
                            Column(
                                modifier = Modifier.padding(16.dp)
                            ) {
                                Text(
                                    "当前状态",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = Color(0xFF999999),
                                    letterSpacing = 0.5.sp
                                )
                                
                                Spacer(modifier = Modifier.height(8.dp))
                                
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    if (agent.stance != null) {
                                        val stanceColor = when {
                                            agent.stance.contains("支持") -> Color(0xFF34C759)
                                            agent.stance.contains("反对") -> Color(0xFFFF3B30)
                                            else -> Color(0xFF8E8E93)
                                        }
                                        Surface(
                                            shape = RoundedCornerShape(6.dp),
                                            color = stanceColor.copy(alpha = 0.1f)
                                        ) {
                                            Text(
                                                agent.stance,
                                                fontSize = 13.sp,
                                                fontWeight = FontWeight.SemiBold,
                                                color = stanceColor,
                                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
                                            )
                                        }
                                    }
                                    
                                    if (agent.score != null) {
                                        Surface(
                                            shape = RoundedCornerShape(6.dp),
                                            color = Color(0x1A0A59F7)
                                        ) {
                                            Text(
                                                "${agent.score}分",
                                                fontSize = 13.sp,
                                                fontWeight = FontWeight.Bold,
                                                color = Color(0xFF0A59F7),
                                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
                                            )
                                        }
                                    }
                                }
                                
                                if (agent.currentMessage != null) {
                                    Spacer(modifier = Modifier.height(12.dp))
                                    Text(
                                        agent.currentMessage,
                                        fontSize = 14.sp,
                                        lineHeight = 20.sp,
                                        color = Color(0xFF1A1A1A)
                                    )
                                }
                            }
                        }
                    }
                    
                    // 历史记录
                    if (agent.thinkingHistory?.isNotEmpty() == true) {
                        item {
                            Text(
                                "思考历程",
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF1A1A1A),
                                modifier = Modifier.padding(top = 16.dp, bottom = 8.dp)
                            )
                        }
                        
                        items(agent.thinkingHistory) { record ->
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = Color.White,
                                shadowElevation = 2.dp
                            ) {
                                Column(
                                    modifier = Modifier.padding(16.dp)
                                ) {
                                    Row(
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Surface(
                                            shape = RoundedCornerShape(6.dp),
                                            color = Color(0x140A59F7)
                                        ) {
                                            Text(
                                                "第${record.round}轮",
                                                fontSize = 12.sp,
                                                fontWeight = FontWeight.Bold,
                                                color = Color(0xFF0A59F7),
                                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                                            )
                                        }
                                        
                                        if (record.score != null) {
                                            Text(
                                                "${record.score}分",
                                                fontSize = 12.sp,
                                                fontWeight = FontWeight.Bold,
                                                color = Color(0xFF666666)
                                            )
                                        }
                                    }
                                    
                                    Spacer(modifier = Modifier.height(12.dp))
                                    
                                    Text(
                                        record.message,
                                        fontSize = 14.sp,
                                        lineHeight = 20.sp,
                                        color = Color(0xFF1A1A1A)
                                    )
                                }
                            }
                        }
                    } else {
                        item {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(48.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Column(
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Text(
                                        "暂无历史思考记录",
                                        fontSize = 14.sp,
                                        color = Color(0xFF999999)
                                    )
                                    Text(
                                        "Agent的思考过程将在推演过程中记录",
                                        fontSize = 12.sp,
                                        color = Color(0xFFBBBBBB)
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * 计算Agent在圆形布局中的位置
 */
private fun getAgentPosition(index: Int, total: Int): Offset {
    val angle = (index.toFloat() / total) * 2 * PI.toFloat() - PI.toFloat() / 2
    val radius = 35f // 半径百分比
    return Offset(
        x = radius * cos(angle),
        y = radius * sin(angle)
    )
}

/**
 * 分数动画数据类
 */
private data class ScoreAnimation(
    val id: String,
    val agentId: String,
    val timestamp: Long
)
