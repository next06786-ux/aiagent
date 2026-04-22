package com.lifeswarm.android.presentation.decision

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import kotlin.random.Random

/**
 * 决策副本页面 - 对应 web/src/pages/DecisionWorkbenchPage.tsx
 * UI风格：白色背景 + 动态色块 + 玻璃卡片
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DecisionScreen(
    onNavigateBack: () -> Unit,
    onNavigateToCollection: (String) -> Unit,
    onNavigateToHistory: () -> Unit
) {
    var showStartDialog by remember { mutableStateOf(false) }
    
    Box(modifier = Modifier.fillMaxSize()) {
        // 白色背景
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.White)
        )
        
        // 动态色块背景（对应Web端的blob）
        AnimatedColorBlobs()
        
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = { Text("决策副本", color = Color(0xFF1A1A1A)) },
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
        ) { padding: PaddingValues ->
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                item { Spacer(modifier = Modifier.height(8.dp)) }
                
                item {
                    // 英雄卡片 - 玻璃质感
                    GlassCard {
                        Column(
                            modifier = Modifier.padding(24.dp)
                        ) {
                            Text(
                                "发起决策分析",
                                style = MaterialTheme.typography.headlineMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF1A1A1A)
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "描述你正在面对的真实决策问题，AI 会通过几轮对话深入了解你的处境。",
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color(0xFF666666)
                            )
                            Spacer(modifier = Modifier.height(24.dp))
                            
                            // 开始按钮 - 圆形渐变按钮
                            Button(
                                onClick = { showStartDialog = true },
                                modifier = Modifier
                                    .size(80.dp),
                                shape = RoundedCornerShape(50),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color.Transparent
                                ),
                                contentPadding = PaddingValues(0.dp)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .background(
                                            Brush.linearGradient(
                                                colors = listOf(
                                                    Color(0xFF1e293b),
                                                    Color(0xFF0f172a)
                                                )
                                            ),
                                            shape = RoundedCornerShape(50)
                                        ),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        "开始\n采集",
                                        style = MaterialTheme.typography.labelMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White,
                                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                                    )
                                }
                            }
                        }
                    }
                }
                
                item {
                    Text(
                        "核心功能",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1A1A1A)
                    )
                }
                
                // 功能卡片 - 玻璃质感
                item {
                    GlassCard {
                        DecisionFeatureContent(
                            title = "信息采集",
                            description = "AI 通过对话深入了解你的处境",
                            icon = Icons.Default.Psychology,
                            onClick = { showStartDialog = true }
                        )
                    }
                }
                
                item {
                    GlassCard {
                        DecisionFeatureContent(
                            title = "多维评估",
                            description = "从多个维度分析决策的影响和风险",
                            icon = Icons.Default.Analytics,
                            onClick = { showStartDialog = true }
                        )
                    }
                }
                
                item {
                    GlassCard {
                        DecisionFeatureContent(
                            title = "方案对比",
                            description = "对比不同决策方案的优劣势",
                            icon = Icons.Default.Compare,
                            onClick = { showStartDialog = true }
                        )
                    }
                }
                
                item {
                    GlassCard {
                        DecisionFeatureContent(
                            title = "历史记录",
                            description = "查看历史决策记录，总结经验教训",
                            icon = Icons.Default.History,
                            onClick = onNavigateToHistory
                        )
                    }
                }
                
                item { Spacer(modifier = Modifier.height(16.dp)) }
            }
        }
    }
    
    // 开始决策对话框
    if (showStartDialog) {
        StartDecisionDialog(
            onDismiss = { showStartDialog = false },
            onConfirm = { question ->
                showStartDialog = false
                onNavigateToCollection(question)
            }
        )
    }
}

/**
 * 动态色块背景
 */
@Composable
fun AnimatedColorBlobs() {
    val infiniteTransition = rememberInfiniteTransition(label = "blobs")
    
    val blob1X by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(8000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1X"
    )
    
    val blob2Y by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.7f,
        animationSpec = infiniteRepeatable(
            animation = tween(10000, easing = LinearEasing),
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
            center = Offset(size.width * blob1X, size.height * 0.2f)
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
            center = Offset(size.width * 0.8f, size.height * blob2Y)
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
            center = Offset(size.width * 0.3f, size.height * 0.8f)
        )
    }
}

/**
 * 玻璃卡片组件
 */
@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = Color.White.copy(alpha = 0.7f),
        shadowElevation = 8.dp,
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            Color.White.copy(alpha = 0.3f)
        )
    ) {
        content()
    }
}

/**
 * 功能卡片内容
 */
@Composable
fun DecisionFeatureContent(
    title: String,
    description: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(20.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 图标
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = Color(0xFF0A59F7).copy(alpha = 0.1f),
            modifier = Modifier.size(48.dp)
        ) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.fillMaxSize()
            ) {
                Icon(
                    icon,
                    contentDescription = null,
                    tint = Color(0xFF0A59F7),
                    modifier = Modifier.size(24.dp)
                )
            }
        }
        
        // 文字
        Column(modifier = Modifier.weight(1f)) {
            Text(
                title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                description,
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF666666)
            )
        }
        
        // 箭头
        IconButton(onClick = onClick) {
            Icon(
                Icons.Default.ChevronRight,
                contentDescription = null,
                tint = Color(0xFF999999)
            )
        }
    }
}


@Composable
fun StartDecisionDialog(
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit
) {
    var question by remember { mutableStateOf("") }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { 
            Text(
                "开始新决策",
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            ) 
        },
        text = {
            Column {
                Text(
                    "请简要描述你要做的决策：",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF666666)
                )
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedTextField(
                    value = question,
                    onValueChange = { question = it },
                    placeholder = { Text("例如：我要不要在今年离开现在的工作？") },
                    minLines = 3,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Color(0xFF0A59F7),
                        unfocusedBorderColor = Color(0xFFE0E0E0)
                    )
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onConfirm(question) },
                enabled = question.isNotBlank(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF0A59F7)
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("开始")
            }
        },
        dismissButton = {
            TextButton(
                onClick = onDismiss,
                colors = ButtonDefaults.textButtonColors(
                    contentColor = Color(0xFF666666)
                )
            ) {
                Text("取消")
            }
        },
        shape = RoundedCornerShape(20.dp),
        containerColor = Color.White
    )
}
