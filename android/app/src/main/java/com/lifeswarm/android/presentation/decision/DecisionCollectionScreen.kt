package com.lifeswarm.android.presentation.decision

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
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
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch

/**
 * 决策信息采集界面 - 对应 web/src/pages/DecisionWorkbenchPage.tsx (collecting阶段)
 * UI风格：白色背景 + 玻璃卡片 + 流式对话
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DecisionCollectionScreen(
    initialQuestion: String = "",
    decisionType: String = "general",
    onNavigateBack: () -> Unit,
    onComplete: (String) -> Unit,
    viewModel: DecisionCollectionViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()
    
    // 初始化：启动采集流程
    LaunchedEffect(Unit) {
        if (uiState.sessionId.isEmpty() && initialQuestion.isNotEmpty()) {
            viewModel.startCollection(initialQuestion, decisionType)
        }
    }
    
    // 自动滚动到底部
    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.size - 1)
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
        AnimatedCollectionBackground()
        
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = { 
                        Column {
                            Text("信息采集", color = Color(0xFF1A1A1A), fontWeight = FontWeight.Bold)
                            if (uiState.phase.isNotEmpty()) {
                                Text(
                                    uiState.phase,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Color(0xFF666666)
                                )
                            }
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
            val paddingValues = padding
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
        ) {
            // 进度指示器
            if (uiState.round > 0) {
                LinearProgressIndicator(
                    progress = (uiState.round / 5f).coerceIn(0f, 1f),
                    modifier = Modifier.fillMaxWidth()
                )
            }
            
            // 消息列表
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(uiState.messages) { message ->
                    CollectionMessageBubble(message)
                }
                
                // 加载状态
                if (uiState.isLoading) {
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Start
                        ) {
                            Surface(
                                shape = RoundedCornerShape(16.dp),
                                color = MaterialTheme.colorScheme.surfaceVariant,
                                modifier = Modifier.padding(8.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(12.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(16.dp),
                                        strokeWidth = 2.dp
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        "AI 正在思考...",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                            }
                        }
                    }
                }
            }
            
            // 错误提示
            if (uiState.error.isNotEmpty()) {
                Surface(
                    color = MaterialTheme.colorScheme.errorContainer,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp)
                ) {
                    Text(
                        text = uiState.error,
                        color = MaterialTheme.colorScheme.onErrorContainer,
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }
            
            // 完成提示
            if (uiState.isComplete) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.primary
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "信息采集完成",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        
                        if (uiState.summary.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                uiState.summary,
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        Button(
                            onClick = { onComplete(uiState.sessionId) },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("继续生成决策方案")
                        }
                    }
                }
            } else {
                Column {
                    // 生成选项的加载状态提示
                    if (uiState.isLoading && uiState.loadingMessage.isNotEmpty()) {
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 16.dp, vertical = 8.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.secondaryContainer
                            )
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(16.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(24.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                                Spacer(modifier = Modifier.width(12.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        uiState.loadingMessage,
                                        style = MaterialTheme.typography.bodyMedium,
                                        fontWeight = FontWeight.Medium,
                                        color = MaterialTheme.colorScheme.onSecondaryContainer
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        "这可能需要1-2分钟，请耐心等待...",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.7f)
                                    )
                                }
                            }
                        }
                    }
                    
                    // 手动结束采集按钮（当对话轮次 >= 3 时显示）
                    if (uiState.round >= 3) {
                        Button(
                            onClick = {
                                // 使用协程调用 suspend 函数
                                coroutineScope.launch {
                                    val options = viewModel.finishCollection()
                                    if (options != null && options.isNotEmpty()) {
                                        // 生成成功，触发完成回调
                                        android.util.Log.d("DecisionCollection", "[UI] 选项生成成功，准备导航")
                                        onComplete(uiState.sessionId)
                                    }
                                }
                            },
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 16.dp, vertical = 8.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.tertiaryContainer
                            ),
                            enabled = !uiState.isLoading
                        ) {
                            Icon(
                                Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onTertiaryContainer
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "信息已足够，结束采集",
                                color = MaterialTheme.colorScheme.onTertiaryContainer
                            )
                        }
                    }
                    
                    // 输入区域
                    CollectionInputArea(
                        input = uiState.input,
                        onInputChange = { viewModel.updateInput(it) },
                        onSend = { viewModel.sendResponse() },
                        isLoading = uiState.isLoading,
                        enabled = uiState.sessionId.isNotEmpty(),
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }
        }
    }
    }
}



@Composable
fun CollectionInputArea(
    input: String,
    onInputChange: (String) -> Unit,
    onSend: () -> Unit,
    isLoading: Boolean,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Bottom
    ) {
        OutlinedTextField(
            value = input,
            onValueChange = onInputChange,
            modifier = Modifier.weight(1f),
            placeholder = { Text("输入你的回答...") },
            minLines = 1,
            maxLines = 4,
            shape = RoundedCornerShape(24.dp),
            enabled = !isLoading && enabled
        )
        
        Spacer(modifier = Modifier.width(8.dp))
        
        FloatingActionButton(
            onClick = onSend,
            modifier = Modifier.size(56.dp),
            containerColor = if (enabled) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
            contentColor = if (enabled) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary,
                    strokeWidth = 2.dp
                )
            } else {
                Icon(Icons.Default.Send, "发送")
            }
        }
    }
}

// 数据类
data class CollectionMessage(
    val id: String,
    val role: String,
    val content: String
)


/**
 * 动态背景 - 色块动画（对应Web端）
 */
@Composable
fun AnimatedCollectionBackground() {
    val infiniteTransition = rememberInfiniteTransition(label = "collection_bg")
    
    val blob1X by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(10000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1X"
    )
    
    val blob2Y by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.7f,
        animationSpec = infiniteRepeatable(
            animation = tween(12000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob2Y"
    )
    
    Canvas(modifier = Modifier.fillMaxSize()) {
        // 蓝色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x400A59F7),
                    Color(0x000A59F7)
                )
            ),
            radius = size.minDimension * 0.4f,
            center = Offset(size.width * blob1X, size.height * 0.25f)
        )
        
        // 紫色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x406B48FF),
                    Color(0x006B48FF)
                )
            ),
            radius = size.minDimension * 0.35f,
            center = Offset(size.width * 0.7f, size.height * blob2Y)
        )
        
        // 青色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x4000D9FF),
                    Color(0x0000D9FF)
                )
            ),
            radius = size.minDimension * 0.3f,
            center = Offset(size.width * 0.3f, size.height * 0.75f)
        )
    }
}

/**
 * 消息气泡 - 对应Web端的消息样式
 */
@Composable
fun CollectionMessageBubble(message: CollectionMessage) {
    val isUser = message.role == "user"
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            shape = RoundedCornerShape(
                topStart = 16.dp,
                topEnd = 16.dp,
                bottomStart = if (isUser) 16.dp else 4.dp,
                bottomEnd = if (isUser) 4.dp else 16.dp
            ),
            color = if (isUser) {
                Color(0xFFF0F7FF) // 淡蓝色 - 用户消息
            } else {
                Color(0xFFF5F5F5) // 淡灰色 - AI消息
            },
            modifier = Modifier
                .widthIn(max = 280.dp)
                .padding(horizontal = 8.dp)
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                // 消息头部
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(bottom = 4.dp)
                ) {
                    // 头像
                    Box(
                        modifier = if (isUser) {
                            Modifier
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(Color(0xFF0A59F7))
                        } else {
                            Modifier
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(
                                    Brush.linearGradient(
                                        colors = listOf(
                                            Color(0xFF0A59F7),
                                            Color(0xFF6B48FF)
                                        )
                                    )
                                )
                        },
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            if (isUser) Icons.Default.Person else Icons.Default.SmartToy,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                    
                    Spacer(modifier = Modifier.width(8.dp))
                    
                    Text(
                        if (isUser) "你" else "AI 核心",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1A1A1A)
                    )
                }
                
                // 消息内容
                Text(
                    message.content,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF1A1A1A)
                )
            }
        }
    }
}
