package com.lifeswarm.android.presentation.insight

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * 智慧洞察主界面 - 对应 web/src/pages/DecisionInsightsPage.tsx
 * UI风格：白色背景 + 粒子动画 + Agent卡片
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InsightsScreen(
    token: String,
    onNavigateBack: () -> Unit
) {
    val viewModel: InsightsViewModel = viewModel(
        factory = InsightsViewModelFactory(token)
    )
    
    val uiState by viewModel.uiState.collectAsState()
    
    Box(modifier = Modifier.fillMaxSize()) {
        // 白色背景
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.White)
        )
        
        // 动态色块背景
        AnimatedInsightsBackground()
        
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = { Text("智慧洞察", color = Color(0xFF1A1A1A)) },
                    navigationIcon = {
                        IconButton(onClick = onNavigateBack) {
                            Icon(Icons.Default.ArrowBack, "返回", tint = Color(0xFF1A1A1A))
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = Color.Transparent
                    )
                )
            },
        snackbarHost = {
            if (uiState.agentError.isNotEmpty() || uiState.crossDomainError.isNotEmpty()) {
                Snackbar(
                    modifier = Modifier.padding(16.dp),
                    action = {
                        TextButton(onClick = { viewModel.clearError() }) {
                            Text("关闭")
                        }
                    }
                ) {
                    Text(uiState.agentError.ifEmpty { uiState.crossDomainError })
                }
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(MaterialTheme.colorScheme.background)
        ) {
            // 标题卡片
            InsightsHeroCard()
            
            // 视图切换器
            ViewModeSwitcher(
                currentMode = uiState.viewMode,
                onModeChange = { viewModel.switchViewMode(it) }
            )
            
            // 内容区域
            when (uiState.viewMode) {
                ViewMode.AGENTS -> {
                    if (uiState.selectedAgent == null) {
                        // Agent 选择界面
                        AgentSelectionScreen(
                            onAgentSelected = { viewModel.generateAgentInsight(it) }
                        )
                    } else if (uiState.isAgentLoading) {
                        // 加载状态
                        AgentLoadingScreen(agentType = uiState.selectedAgent!!)
                    } else if (uiState.agentReport != null) {
                        // 报告展示
                        AgentReportScreen(
                            report = uiState.agentReport!!,
                            onBack = { viewModel.backToAgentSelection() }
                        )
                    }
                }
                ViewMode.CROSS_DOMAIN -> {
                    // 跨领域分析界面
                    CrossDomainAnalysisScreen(
                        query = uiState.crossDomainQuery,
                        result = uiState.crossDomainResult,
                        isLoading = uiState.isCrossDomainLoading,
                        onQueryChange = { viewModel.updateCrossDomainQuery(it) },
                        onAnalyze = { viewModel.generateCrossDomainAnalysis() }
                    )
                }
            }
        }
    }
    }
}

/**
 * 英雄卡片 - 玻璃质感（对应Web端）
 */
@Composable
fun InsightsHeroCard() {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        shape = RoundedCornerShape(24.dp),
        color = Color.White.copy(alpha = 0.7f),
        shadowElevation = 8.dp,
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            Color.White.copy(alpha = 0.3f)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp)
        ) {
            Text(
                "智慧洞察",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "三个专业Agent · 实时智能分析 · 多Agent协作",
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFF666666)
            )
        }
    }
}

/**
 * 视图模式切换器
 */
@Composable
fun ViewModeSwitcher(
    currentMode: ViewMode,
    onModeChange: (ViewMode) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // 单Agent分析按钮
        Button(
            onClick = { onModeChange(ViewMode.AGENTS) },
            modifier = Modifier.weight(1f),
            colors = ButtonDefaults.buttonColors(
                containerColor = if (currentMode == ViewMode.AGENTS) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.surfaceVariant
                },
                contentColor = if (currentMode == ViewMode.AGENTS) {
                    MaterialTheme.colorScheme.onPrimary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                }
            ),
            shape = RoundedCornerShape(16.dp)
        ) {
            Icon(
                Icons.Default.Person,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text("单Agent分析")
        }
        
        // 跨领域综合分析按钮
        Button(
            onClick = { onModeChange(ViewMode.CROSS_DOMAIN) },
            modifier = Modifier.weight(1f),
            colors = ButtonDefaults.buttonColors(
                containerColor = if (currentMode == ViewMode.CROSS_DOMAIN) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.surfaceVariant
                },
                contentColor = if (currentMode == ViewMode.CROSS_DOMAIN) {
                    MaterialTheme.colorScheme.onPrimary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                }
            ),
            shape = RoundedCornerShape(16.dp)
        ) {
            Icon(
                Icons.Default.Hub,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text("跨领域分析")
        }
    }
}

/**
 * 动态背景 - 粒子效果（对应Web端）
 */
@Composable
fun AnimatedInsightsBackground() {
    val infiniteTransition = rememberInfiniteTransition(label = "insights_bg")
    
    val blob1X by infiniteTransition.animateFloat(
        initialValue = 0.1f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(
            animation = tween(12000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1X"
    )
    
    val blob2Y by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(15000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob2Y"
    )
    
    val blob3X by infiniteTransition.animateFloat(
        initialValue = 0.7f,
        targetValue = 0.3f,
        animationSpec = infiniteRepeatable(
            animation = tween(10000, easing = LinearEasing),
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
