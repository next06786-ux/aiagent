package com.lifeswarm.android.presentation.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import java.text.SimpleDateFormat
import java.util.*

/**
 * AI 聊天页面 - 对齐Web端UI风格
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: ChatViewModel,
    onNavigateBack: () -> Unit,
    onNavigateToKnowledgeGraph: (String) -> Unit,
    onNavigateToDecision: () -> Unit,
    onNavigateToParallelLife: () -> Unit,
    onNavigateToConversationList: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val listState = rememberLazyListState()
    
    // 自动滚动到底部
    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.size - 1)
        }
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)  // 白色背景
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            // 顶部栏 - 对齐Web端风格
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = Color.White,
                shadowElevation = 1.dp
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // AI图标
                    Surface(
                        modifier = Modifier.size(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        color = Color(0xFFF0F7FF)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text(
                                text = "AI",
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF0A59F7)
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.width(12.dp))
                    
                    // 标题
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "AI 核心",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF1a1a1a)
                        )
                        Text(
                            text = "Central Intelligence Engine",
                            fontSize = 12.sp,
                            color = Color(0xFF999999)
                        )
                    }
                    
                    // 右侧按钮
                    IconButton(onClick = onNavigateToConversationList) {
                        Icon(
                            Icons.Default.History,
                            contentDescription = "会话历史",
                            tint = Color(0xFF666666)
                        )
                    }
                    
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            Icons.Default.Close,
                            contentDescription = "关闭",
                            tint = Color(0xFF666666)
                        )
                    }
                }
            }
            
            // 快捷导航标签
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                QuickNavChip("决策推演", onClick = onNavigateToDecision)
                QuickNavChip("知识星图", onClick = { onNavigateToKnowledgeGraph("") })
                QuickNavChip("平行人生", onClick = onNavigateToParallelLife)
                QuickNavChip("洞察分析", onClick = {})
            }
            
            // 消息列表
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // 欢迎消息（如果是空会话）
                if (uiState.messages.isEmpty() || (uiState.messages.size == 1 && uiState.messages[0].role == "assistant")) {
                    item {
                        WelcomeMessage()
                    }
                }
                
                items(uiState.messages) { message ->
                    if (message.id != "welcome" && message.id != "welcome_new") {
                        ChatMessageBubbleWeb(message)
                    }
                }
                
                // 流式状态提示
                if (uiState.streamStatus.isNotEmpty()) {
                    item {
                        Text(
                            text = uiState.streamStatus,
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF0A59F7),
                            modifier = Modifier.padding(8.dp)
                        )
                    }
                }
            }
            
            // 路由建议卡片（在输入框上方）
            val routeSuggestion = uiState.routeSuggestion
            if (routeSuggestion != null) {
                RouteSuggestionCardWeb(
                    suggestion = routeSuggestion,
                    onNavigate = {
                        when (routeSuggestion.recommendedModule) {
                            "knowledge_graph" -> onNavigateToKnowledgeGraph(uiState.lastUserMessage)
                            "decision" -> onNavigateToDecision()
                            "parallel_life" -> onNavigateToParallelLife()
                        }
                    },
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                )
            }
            
            // 输入区域 - 对齐Web端风格
            ChatInputAreaWeb(
                input = uiState.input,
                onInputChange = { viewModel.updateInput(it) },
                onSend = { viewModel.sendMessage() },
                isSending = uiState.isSending,
                error = uiState.error,
                modifier = Modifier.padding(16.dp)
            )
        }
    }
}

@Composable
fun QuickNavChip(
    text: String,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(16.dp),
        color = Color(0xFFF5F5F5),
        modifier = Modifier.height(32.dp)
    ) {
        Box(
            modifier = Modifier.padding(horizontal = 12.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = text,
                fontSize = 13.sp,
                color = Color(0xFF666666)
            )
        }
    }
}

@Composable
fun WelcomeMessage() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // AI图标
        Surface(
            modifier = Modifier.size(80.dp),
            shape = RoundedCornerShape(20.dp),
            color = Color(0xFFF0F7FF)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = "AI",
                    fontSize = 36.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF0A59F7)
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "你好！我是 AI 核心",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF1a1a1a)
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "我可以帮你进行决策推演、查看知识星图、分析涌现模式，或者回答任何问题。",
            fontSize = 14.sp,
            color = Color(0xFF666666),
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 32.dp)
        )
    }
}

@Composable
fun ChatMessageBubbleWeb(message: ChatMessage) {
    val isUser = message.role == "user"
    
    Column(
        modifier = Modifier.fillMaxWidth()
    ) {
        // 消息头部
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start,
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (!isUser) {
                Surface(
                    modifier = Modifier.size(32.dp),
                    shape = RoundedCornerShape(8.dp),
                    color = Color(0xFFF0F7FF)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = "AI",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF0A59F7)
                        )
                    }
                }
                Spacer(modifier = Modifier.width(8.dp))
            }
            
            Text(
                text = if (isUser) "你" else "AI Core",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1a1a1a)
            )
            
            Spacer(modifier = Modifier.width(8.dp))
            
            Text(
                text = formatMessageTime(message.timestamp),
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF999999)
            )
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // 思考过程（可展开）
        if (message.thinking?.isNotEmpty() == true) {
            var expanded by remember { mutableStateOf(false) }
            
            Surface(
                onClick = { expanded = !expanded },
                shape = RoundedCornerShape(8.dp),
                color = Color(0xFFF5F5F5),
                modifier = Modifier.padding(bottom = 8.dp)
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = Color(0xFF666666)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        "查看推理过程",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color(0xFF666666)
                    )
                }
            }
            
            if (expanded) {
                Surface(
                    color = Color(0xFFF5F5F5),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.padding(bottom = 8.dp)
                ) {
                    Text(
                        text = message.thinking,
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF666666),
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }
        }
        
        // 消息内容
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = if (isUser) Color(0xFFF0F7FF) else Color(0xFFF5F5F5),
            modifier = Modifier.fillMaxWidth(if (isUser) 0.85f else 1f)
        ) {
            Text(
                text = message.content.ifEmpty { if (!isUser) "..." else "" },
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFF1a1a1a),
                modifier = Modifier.padding(16.dp)
            )
        }
    }
}

@Composable
fun RouteSuggestionCardWeb(
    suggestion: RouteSuggestion,
    onNavigate: () -> Unit,
    modifier: Modifier = Modifier
) {
    val moduleInfo = getModuleInfo(suggestion.recommendedModule)
    
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = Color(0xFFF0F7FF),
        onClick = onNavigate
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = moduleInfo.name,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1a1a1a)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = Color(0xFF0A59F7).copy(alpha = 0.1f)
                    ) {
                        Text(
                            text = "100% 匹配",
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                            fontSize = 11.sp,
                            color = Color(0xFF0A59F7),
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = suggestion.reason,
                    fontSize = 13.sp,
                    color = Color(0xFF666666),
                    lineHeight = 18.sp
                )
            }
            Icon(
                Icons.Default.ArrowForward,
                contentDescription = null,
                tint = Color(0xFF0A59F7)
            )
        }
    }
}

@Composable
fun ChatInputAreaWeb(
    input: String,
    onInputChange: (String) -> Unit,
    onSend: () -> Unit,
    isSending: Boolean,
    error: String,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        // 输入框
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = Color(0xFFF5F5F5),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column {
                OutlinedTextField(
                    value = input,
                    onValueChange = onInputChange,
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { 
                        Text(
                            "输入消息... (Enter 发送, Shift+Enter 换行)",
                            color = Color(0xFF999999),
                            fontSize = 14.sp
                        ) 
                    },
                    minLines = 1,
                    maxLines = 5,
                    enabled = !isSending,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = Color.Transparent,
                        unfocusedContainerColor = Color.Transparent,
                        disabledContainerColor = Color.Transparent,
                        focusedBorderColor = Color.Transparent,
                        unfocusedBorderColor = Color.Transparent,
                        disabledBorderColor = Color.Transparent
                    ),
                    textStyle = MaterialTheme.typography.bodyMedium.copy(
                        color = Color(0xFF1a1a1a)
                    )
                )
                
                // 发送按钮
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.End
                ) {
                    Button(
                        onClick = onSend,
                        enabled = input.isNotBlank() && !isSending,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF0A59F7),
                            disabledContainerColor = Color(0xFFE0E0E0)
                        ),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        if (isSending) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                        }
                        Text(
                            text = if (isSending) "发送中..." else "发送给 AI 核心",
                            color = if (input.isNotBlank() && !isSending) Color.White else Color(0xFF999999)
                        )
                    }
                }
            }
        }
        
        // 错误提示
        if (error.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))
            Surface(
                color = Color(0xFFFFEBEE),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text(
                    text = error,
                    color = Color(0xFFD32F2F),
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(12.dp)
                )
            }
        }
        
        // 提示文字
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "AI 核心可以帮你导航到任何功能模块，或回答你的问题",
            fontSize = 12.sp,
            color = Color(0xFF999999),
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )
    }
}

@Composable
fun ChatMessageBubble(message: ChatMessage) {
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
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surfaceVariant
            },
            modifier = Modifier.widthIn(max = 300.dp)
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                // 消息头部
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (isUser) "你" else "AI Core",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = if (isUser) {
                            MaterialTheme.colorScheme.onPrimaryContainer
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                    
                    Text(
                        text = formatMessageTime(message.timestamp),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                    )
                }
                
                Spacer(modifier = Modifier.height(4.dp))
                
                // 思考过程（可展开）
                if (message.thinking?.isNotEmpty() == true) {
                    var expanded by remember { mutableStateOf(false) }
                    
                    TextButton(
                        onClick = { expanded = !expanded },
                        modifier = Modifier.padding(vertical = 4.dp)
                    ) {
                        Icon(
                            imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("查看推理过程", style = MaterialTheme.typography.labelSmall)
                    }
                    
                    if (expanded) {
                        Surface(
                            color = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.padding(vertical = 4.dp)
                        ) {
                            Text(
                                text = message.thinking,
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.padding(8.dp)
                            )
                        }
                    }
                }
                
                // 消息内容
                Text(
                    text = message.content.ifEmpty { if (!isUser) "..." else "" },
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isUser) {
                        MaterialTheme.colorScheme.onPrimaryContainer
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    }
                )
            }
        }
    }
}

@Composable
fun RouteSuggestionCard(
    suggestion: RouteSuggestion,
    onNavigate: () -> Unit,
    onDismiss: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    println("[RouteSuggestionCard] 渲染卡片")
    println("[RouteSuggestionCard] - module: ${suggestion.recommendedModule}")
    println("[RouteSuggestionCard] - view: ${suggestion.recommendedView}")
    println("[RouteSuggestionCard] - reason: ${suggestion.reason}")
    
    // 获取模块信息
    val moduleInfo = getModuleInfo(suggestion.recommendedModule)
    
    Column(
        modifier = modifier
            .fillMaxWidth()
    ) {
        // 导航建议卡片（可点击跳转）
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            color = Color(0xFFE8EAF6), // 淡蓝紫色背景
            tonalElevation = 0.dp,
            onClick = {
                println("[RouteSuggestionCard] 导航卡片被点击")
                onNavigate()
            }
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                // 模块名称（加粗）
                Text(
                    text = moduleInfo.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // 描述文字（灰色）
                Text(
                    text = moduleInfo.description,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF666666),
                    lineHeight = 20.sp
                )
                
                Spacer(modifier = Modifier.height(12.dp))
                
                // 100% 匹配标签
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = Color(0xFF2196F3).copy(alpha = 0.1f)
                ) {
                    Text(
                        text = "100% 匹配",
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        color = Color(0xFF2196F3),
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // 不跳转按钮
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            color = Color(0xFFF5F5F5),
            onClick = {
                println("[RouteSuggestionCard] 不跳转按钮被点击")
                onDismiss()
            }
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.Close,
                    contentDescription = null,
                    tint = Color(0xFFE91E63),
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Column {
                    Text(
                        text = "不跳转",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Medium,
                        color = Color(0xFF1A1A1A)
                    )
                    Text(
                        text = "继续在这里对话",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF999999)
                    )
                }
            }
        }
    }
}

/**
 * 获取模块信息
 */
data class ModuleInfo(
    val name: String,
    val description: String
)

fun getModuleInfo(module: String): ModuleInfo {
    return when (module) {
        "knowledge_graph" -> ModuleInfo(
            name = "知识星图",
            description = "查看你的知识图谱，包括人际关系网络、教育升学规划、职业发展路径"
        )
        "decision" -> ModuleInfo(
            name = "决策图谱",
            description = "通过多维度分析和模拟，帮助你做出更明智的决策"
        )
        "parallel_life" -> ModuleInfo(
            name = "平行人生",
            description = "模拟不同选择带来的未来可能性，探索人生的多种路径"
        )
        else -> ModuleInfo(
            name = "AI 核心对话",
            description = "继续在这里补充信息，我会为你提供更准确的建议"
        )
    }
}

@Composable
fun ChatInputArea(
    input: String,
    onInputChange: (String) -> Unit,
    onSend: () -> Unit,
    isSending: Boolean,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        // 输入框和发送按钮在同一行
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.Bottom
        ) {
            OutlinedTextField(
                value = input,
                onValueChange = { newValue ->
                    println("[ChatInput] 输入变化: '$newValue'")
                    onInputChange(newValue)
                },
                modifier = Modifier.weight(1f),
                placeholder = { Text("例如：谁正在影响我该不该离开现在的环境？") },
                minLines = 1,
                maxLines = 5,
                shape = RoundedCornerShape(24.dp),
                enabled = !isSending,
                singleLine = false
            )
            
            // 发送按钮（圆形图标按钮）
            FloatingActionButton(
                onClick = {
                    println("[ChatScreen] 发送按钮被点击")
                    onSend()
                },
                modifier = Modifier.size(56.dp),
                containerColor = if (input.isNotBlank() && !isSending) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.surfaceVariant
                },
                elevation = FloatingActionButtonDefaults.elevation(
                    defaultElevation = 2.dp,
                    pressedElevation = 4.dp
                )
            ) {
                if (isSending) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                } else {
                    Icon(
                        Icons.Default.Send,
                        contentDescription = "发送",
                        tint = if (input.isNotBlank()) {
                            MaterialTheme.colorScheme.onPrimary
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                }
            }
        }
        
        // 导航建议现在通过 WebSocket 自动返回，不需要手动触发分析按钮
    }
}

private fun formatMessageTime(timestamp: String): String {
    return try {
        val date = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault()).parse(timestamp)
        date?.let {
            SimpleDateFormat("MM/dd HH:mm", Locale.getDefault()).format(it)
        } ?: timestamp
    } catch (e: Exception) {
        timestamp
    }
}

// 数据类
data class ChatMessage(
    val id: String = "",
    val role: String = "",
    val content: String = "",
    val thinking: String? = null,
    val timestamp: String = ""
)

data class RouteSuggestion(
    val recommendedModule: String,
    val recommendedView: String?,
    val reason: String
)
