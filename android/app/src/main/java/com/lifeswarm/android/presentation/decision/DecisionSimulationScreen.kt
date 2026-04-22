package com.lifeswarm.android.presentation.decision

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.lifeswarm.android.data.model.OptionInput

/**
 * 决策推演页面 - 对应 web/src/pages/DecisionSimulationPage.tsx
 * UI风格：白色背景 + 玻璃卡片 + Agent可视化
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DecisionSimulationScreen(
    sessionId: String,
    userId: String,
    question: String,
    options: List<OptionInput>,
    collectedInfo: Any? = null,
    decisionType: String = "general",
    onNavigateBack: () -> Unit,
    viewModel: DecisionSimulationViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    // 启动推演
    LaunchedEffect(sessionId) {
        if (uiState.phase == SimulationPhase.IDLE) {
            viewModel.startSimulation(
                sessionId = sessionId,
                userId = userId,
                question = question,
                options = options,
                collectedInfo = collectedInfo,
                decisionType = decisionType
            )
        }
    }
    
    Box(modifier = Modifier.fillMaxSize()) {
        // 白色背景
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.White)
        )
        
        // 动态色块背景
        AnimatedSimulationBackground()
        
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = {
                        Column {
                            Text(
                                "决策推演",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF1A1A1A)
                            )
                            Text(
                                question,
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFF666666)
                            )
                        }
                    },
                    navigationIcon = {
                        IconButton(onClick = onNavigateBack) {
                            Icon(Icons.Default.ArrowBack, "返回", tint = Color(0xFF1A1A1A))
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = Color.Transparent
                    )
                )
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
                when (uiState.phase) {
                    SimulationPhase.IDLE, SimulationPhase.CONNECTING -> {
                        ConnectingView(uiState.statusMessage)
                    }
                    
                    SimulationPhase.RUNNING -> {
                        if (uiState.agents.isNotEmpty()) {
                            PersonaInteractionView(
                                agents = uiState.agents,
                                totalScore = uiState.totalScore,
                                optionTitle = question,
                                isComplete = false
                            )
                        } else {
                            ConnectingView("等待 Agent 启动...")
                        }
                    }
                    
                    SimulationPhase.DONE -> {
                        PersonaInteractionView(
                            agents = uiState.agents,
                            totalScore = uiState.totalScore,
                            optionTitle = question,
                            isComplete = true
                        )
                    }
                    
                    SimulationPhase.ERROR -> {
                        ErrorView(uiState.error)
                    }
                }
            }
        }
    }
}

/**
 * 连接中视图
 */
@Composable
fun ConnectingView(statusMessage: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // 旋转的加载指示器
        val infiniteTransition = rememberInfiniteTransition(label = "loading")
        val rotation by infiniteTransition.animateFloat(
            initialValue = 0f,
            targetValue = 360f,
            animationSpec = infiniteRepeatable(
                animation = tween(1000, easing = LinearEasing),
                repeatMode = RepeatMode.Restart
            ),
            label = "rotation"
        )
        
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
 * Agents 视图
 */
@Composable
fun AgentsView(
    agents: List<AgentState>,
    totalScore: Double,
    statusMessage: String,
    isComplete: Boolean = false
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // 状态栏
        if (statusMessage.isNotEmpty() && !isComplete) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                )
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        statusMessage,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSecondaryContainer
                    )
                }
            }
        }
        
        // 总分显示
        if (totalScore > 0) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "综合评分",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        String.format("%.1f", totalScore),
                        style = MaterialTheme.typography.displayMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        "/ 100",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                    )
                }
            }
        }
        
        // Agents 列表
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(agents) { agent ->
                AgentCard(agent)
            }
        }
    }
}

/**
 * Agent 卡片
 */
@Composable
fun AgentCard(agent: AgentState) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // 头部：名称和状态
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // 状态指示器
                    Box(
                        modifier = Modifier
                            .size(12.dp)
                            .clip(CircleShape)
                            .background(
                                when (agent.status) {
                                    AgentStatus.WAITING -> Color.Gray
                                    AgentStatus.THINKING -> Color(0xFF2196F3)
                                    AgentStatus.COMPLETE -> Color(0xFF4CAF50)
                                    AgentStatus.ERROR -> Color(0xFFF44336)
                                }
                            )
                    )
                    
                    Text(
                        agent.name,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                
                // 分数
                if (agent.score != null) {
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = MaterialTheme.colorScheme.primaryContainer
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
            }
            
            // 立场
            if (agent.stance != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    agent.stance,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // 当前消息
            if (agent.currentMessage != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.secondaryContainer
                ) {
                    Text(
                        agent.currentMessage,
                        modifier = Modifier.padding(12.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                        lineHeight = 18.sp
                    )
                }
            }
        }
    }
}

/**
 * 错误视图
 */
@Composable
fun ErrorView(errorMessage: String) {
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
            color = MaterialTheme.colorScheme.error
        )
    }
}


/**
 * 动态背景 - 推演界面（对应Web端）
 */
@Composable
fun AnimatedSimulationBackground() {
    val infiniteTransition = rememberInfiniteTransition(label = "simulation_bg")
    
    val blob1X by infiniteTransition.animateFloat(
        initialValue = 0.15f,
        targetValue = 0.85f,
        animationSpec = infiniteRepeatable(
            animation = tween(15000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1X"
    )
    
    val blob2Y by infiniteTransition.animateFloat(
        initialValue = 0.25f,
        targetValue = 0.75f,
        animationSpec = infiniteRepeatable(
            animation = tween(18000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob2Y"
    )
    
    val blob3X by infiniteTransition.animateFloat(
        initialValue = 0.7f,
        targetValue = 0.3f,
        animationSpec = infiniteRepeatable(
            animation = tween(13000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob3X"
    )
    
    Canvas(modifier = Modifier.fillMaxSize()) {
        // 蓝色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x500A59F7),
                    Color(0x000A59F7)
                )
            ),
            radius = size.minDimension * 0.5f,
            center = Offset(size.width * blob1X, size.height * 0.3f)
        )
        
        // 紫色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x506B48FF),
                    Color(0x006B48FF)
                )
            ),
            radius = size.minDimension * 0.45f,
            center = Offset(size.width * 0.5f, size.height * blob2Y)
        )
        
        // 青色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x5000D9FF),
                    Color(0x0000D9FF)
                )
            ),
            radius = size.minDimension * 0.4f,
            center = Offset(size.width * blob3X, size.height * 0.7f)
        )
    }
}
