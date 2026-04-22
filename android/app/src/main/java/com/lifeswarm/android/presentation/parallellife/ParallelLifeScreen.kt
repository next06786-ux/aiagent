package com.lifeswarm.android.presentation.parallellife

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * 平行人生主界面 - 塔罗牌决策游戏
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ParallelLifeScreen(
    userId: String,
    onNavigateBack: () -> Unit
) {
    val viewModel: ParallelLifeViewModel = viewModel(
        factory = ParallelLifeViewModelFactory(userId)
    )
    
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("平行人生 · 塔罗占卜") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, "返回")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.Transparent
                )
            )
        },
        containerColor = Color(0xFF0A0E27)
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // 星空背景
            StarfieldBackground()
            
            // 渐变背景
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        Brush.verticalGradient(
                            colors = listOf(
                                Color(0xFF0A0E27),
                                Color(0xFF1A1F3A),
                                Color(0xFF0A0E27)
                            )
                        )
                    )
            )
            
            // 内容
            when (uiState.phase) {
                GamePhase.INTRO -> IntroPhase(
                    onStart = { viewModel.startGame() }
                )
                GamePhase.DRAWING -> DrawingPhase(
                    progress = uiState.progress,
                    isDrawing = uiState.isDrawing
                )
                GamePhase.CHOOSING -> ChoosingPhase(
                    card = uiState.currentCard,
                    progress = uiState.progress,
                    onChoice = { text, tendency ->
                        viewModel.submitChoice(text, tendency)
                    },
                    onFinishEarly = { viewModel.finishEarly() }
                )
                GamePhase.RESULT -> ResultPhase(
                    profile = uiState.profile,
                    onRestart = { viewModel.restart() },
                    onBack = onNavigateBack
                )
            }
            
            // 错误提示
            if (uiState.error.isNotEmpty()) {
                Snackbar(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(16.dp),
                    action = {
                        TextButton(onClick = { viewModel.restart() }) {
                            Text("重试")
                        }
                    }
                ) {
                    Text(uiState.error)
                }
            }
        }
    }
}

/**
 * 星空背景
 */
@Composable
fun StarfieldBackground() {
    val stars = remember {
        List(100) {
            Star(
                x = Random.nextFloat(),
                y = Random.nextFloat(),
                size = Random.nextFloat() * 2f + 1f,
                alpha = Random.nextFloat() * 0.5f + 0.5f
            )
        }
    }
    
    Canvas(modifier = Modifier.fillMaxSize()) {
        stars.forEach { star ->
            drawCircle(
                color = Color.White.copy(alpha = star.alpha),
                radius = star.size,
                center = Offset(
                    x = star.x * size.width,
                    y = star.y * size.height
                )
            )
        }
    }
}

private data class Star(
    val x: Float,
    val y: Float,
    val size: Float,
    val alpha: Float
)

/**
 * 介绍阶段
 */
@Composable
fun IntroPhase(onStart: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // 标题
        Text(
            "今日运势",
            style = MaterialTheme.typography.displayLarge,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            "AI星座塔罗占卜",
            style = MaterialTheme.typography.titleLarge,
            color = Color.White.copy(alpha = 0.7f),
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = Color.White.copy(alpha = 0.1f)
        ) {
            Text(
                "添加生日信息解读更准确",
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.8f)
            )
        }
        
        Spacer(modifier = Modifier.height(48.dp))
        
        // 塔罗牌预览
        TarotCardPreview()
        
        Spacer(modifier = Modifier.height(48.dp))
        
        // 开始按钮
        Button(
            onClick = onStart,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(28.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF6B48FF)
            )
        ) {
            Text(
                "点击占卜揭示今日运势！",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/**
 * 塔罗牌预览
 */
@Composable
fun TarotCardPreview() {
    val infiniteTransition = rememberInfiniteTransition(label = "cardGlow")
    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glowAlpha"
    )
    
    Box(
        modifier = Modifier
            .width(200.dp)
            .height(300.dp),
        contentAlignment = Alignment.Center
    ) {
        // 发光效果
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFF6B48FF).copy(alpha = glowAlpha),
                            Color.Transparent
                        )
                    )
                )
        )
        
        // 卡片背面
        Card(
            modifier = Modifier
                .width(180.dp)
                .height(280.dp),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFF1A1F3A)
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
        ) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                // 塔罗牌图案
                TarotPattern()
            }
        }
    }
}

/**
 * 塔罗牌图案
 */
@Composable
fun TarotPattern() {
    Canvas(
        modifier = Modifier
            .size(120.dp)
            .padding(16.dp)
    ) {
        val centerX = size.width / 2
        val centerY = size.height / 2
        val radius = size.minDimension / 3
        
        // 外圈
        drawCircle(
            color = Color(0xFF6B48FF).copy(alpha = 0.6f),
            radius = radius,
            center = Offset(centerX, centerY),
            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2f)
        )
        
        // 五角星
        val starPoints = 5
        val outerRadius = radius * 0.8f
        val innerRadius = radius * 0.4f
        
        for (i in 0 until starPoints * 2) {
            val angle = (i * Math.PI / starPoints - Math.PI / 2).toFloat()
            val r = if (i % 2 == 0) outerRadius else innerRadius
            val x = centerX + r * cos(angle)
            val y = centerY + r * sin(angle)
            
            if (i > 0) {
                val prevAngle = ((i - 1) * Math.PI / starPoints - Math.PI / 2).toFloat()
                val prevR = if ((i - 1) % 2 == 0) outerRadius else innerRadius
                val prevX = centerX + prevR * cos(prevAngle)
                val prevY = centerY + prevR * sin(prevAngle)
                
                drawLine(
                    color = Color(0xFF6B48FF),
                    start = Offset(prevX, prevY),
                    end = Offset(x, y),
                    strokeWidth = 2f
                )
            }
        }
        
        // 顶部和底部装饰点
        drawCircle(
            color = Color(0xFF6B48FF).copy(alpha = 0.8f),
            radius = 6f,
            center = Offset(centerX, 10f)
        )
        drawCircle(
            color = Color(0xFF6B48FF).copy(alpha = 0.8f),
            radius = 6f,
            center = Offset(centerX, size.height - 10f)
        )
    }
}

/**
 * 抽牌阶段
 */
@Composable
fun DrawingPhase(
    progress: Float,
    isDrawing: Boolean
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // 进度条
        ProgressBar(progress)
        
        Spacer(modifier = Modifier.height(64.dp))
        
        // 牌堆
        TarotDeck(isDrawing)
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(
            "正在抽取塔罗牌...",
            style = MaterialTheme.typography.titleLarge,
            color = Color.White.copy(alpha = 0.8f)
        )
    }
}

/**
 * 进度条
 */
@Composable
fun ProgressBar(progress: Float) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            "进度 ${progress.toInt()}/100",
            style = MaterialTheme.typography.bodyMedium,
            color = Color.White.copy(alpha = 0.7f)
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        LinearProgressIndicator(
            progress = progress / 100f,
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(RoundedCornerShape(4.dp)),
            color = Color(0xFF6B48FF),
            trackColor = Color.White.copy(alpha = 0.2f)
        )
    }
}

/**
 * 牌堆
 */
@Composable
fun TarotDeck(isDrawing: Boolean) {
    val rotation by rememberInfiniteTransition(label = "deckRotation").animateFloat(
        initialValue = 0f,
        targetValue = if (isDrawing) 360f else 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )
    
    Box(
        modifier = Modifier.size(200.dp),
        contentAlignment = Alignment.Center
    ) {
        // 多张卡片叠加效果
        repeat(7) { index ->
            Card(
                modifier = Modifier
                    .width(160.dp)
                    .height(240.dp)
                    .offset(
                        x = (-index * 2).dp,
                        y = (-index * 3).dp
                    )
                    .rotate(if (isDrawing && index == 6) rotation else -index * 1.5f),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF1A1F3A)
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = (7 - index).dp)
            ) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    TarotPattern()
                }
            }
        }
    }
}

// 继续在下一个文件...

/**
 * 选择阶段
 */
@Composable
fun ChoosingPhase(
    card: com.lifeswarm.android.data.model.TarotCard?,
    progress: Float,
    onChoice: (String, String) -> Unit,
    onFinishEarly: () -> Unit
) {
    if (card == null) return
    
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        item {
            // 进度条
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    "进度 ${progress.toInt()}/100 · ${card.dimension}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.7f)
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                LinearProgressIndicator(
                    progress = progress / 100f,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp)),
                    color = Color(0xFF6B48FF),
                    trackColor = Color.White.copy(alpha = 0.2f)
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // 揭示的卡片
            RevealedCard(card)
            
            Spacer(modifier = Modifier.height(24.dp))
        }
        
        // 场景描述（在卡片外面）
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF1A1F3A).copy(alpha = 0.6f)
                )
            ) {
                Text(
                    card.scenario,
                    modifier = Modifier.padding(20.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.White.copy(alpha = 0.9f),
                    textAlign = TextAlign.Center,
                    lineHeight = 24.sp
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
        }
        
        // 选项
        items(card.options) { option ->
            ChoiceButton(
                text = option.text,
                tendency = option.tendency,
                onClick = { onChoice(option.text, option.tendency) }
            )
            Spacer(modifier = Modifier.height(12.dp))
        }
        
        item {
            Spacer(modifier = Modifier.height(16.dp))
            
            // 提前结束按钮
            TextButton(
                onClick = onFinishEarly,
                colors = ButtonDefaults.textButtonColors(
                    contentColor = Color.White.copy(alpha = 0.6f)
                )
            ) {
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("我今天不想继续了")
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/**
 * 揭示的卡片
 */
@Composable
fun RevealedCard(card: com.lifeswarm.android.data.model.TarotCard) {
    Card(
        modifier = Modifier
            .width(280.dp)
            .height(180.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1A1F3A)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // 卡片图标
            Box(
                modifier = Modifier
                    .size(60.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            colors = listOf(
                                Color(0xFF0A59F7),
                                Color(0xFF6B48FF)
                            )
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.Star,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(32.dp)
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 卡片名称
            Text(
                card.card,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // 维度
            Text(
                card.dimension,
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFF6B48FF),
                textAlign = TextAlign.Center
            )
        }
    }
}

/**
 * 选择按钮
 */
@Composable
fun ChoiceButton(
    text: String,
    tendency: String,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(64.dp),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Color.White.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                if (tendency == "left") Icons.Default.KeyboardArrowLeft else Icons.Default.KeyboardArrowRight,
                contentDescription = null,
                tint = Color(0xFF6B48FF),
                modifier = Modifier.size(24.dp)
            )
            
            Text(
                text,
                style = MaterialTheme.typography.bodyLarge,
                color = Color.White,
                textAlign = TextAlign.Center,
                modifier = Modifier.weight(1f)
            )
            
            Icon(
                if (tendency == "left") Icons.Default.KeyboardArrowLeft else Icons.Default.KeyboardArrowRight,
                contentDescription = null,
                tint = Color(0xFF6B48FF),
                modifier = Modifier.size(24.dp)
            )
        }
    }
}

/**
 * 结果阶段
 */
@Composable
fun ResultPhase(
    profile: com.lifeswarm.android.data.model.DecisionProfile?,
    onRestart: () -> Unit,
    onBack: () -> Unit
) {
    if (profile == null) return
    
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        item {
            // 标题
            Text(
                "你的决策画像",
                style = MaterialTheme.typography.displayMedium,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                "Decision Profile",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White.copy(alpha = 0.7f),
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 统计信息
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = Color.White.copy(alpha = 0.1f)
            ) {
                Text(
                    "基于 ${profile.totalChoices} 次选择 · 置信度 ${(profile.confidence * 100).toInt()}%",
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.8f)
                )
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
        
        // 维度列表
        items(profile.dimensions.entries.toList()) { (name, data) ->
            DimensionCard(name, data)
            Spacer(modifier = Modifier.height(16.dp))
        }
        
        // 决策模式
        if (profile.patterns.isNotEmpty()) {
            item {
                Spacer(modifier = Modifier.height(16.dp))
                
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF1A1F3A)
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp)
                    ) {
                        Text(
                            "决策模式特征",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        profile.patterns.forEach { pattern ->
                            Row(
                                modifier = Modifier.padding(vertical = 4.dp),
                                verticalAlignment = Alignment.Top
                            ) {
                                Text(
                                    "•",
                                    color = Color(0xFF6B48FF),
                                    modifier = Modifier.padding(end = 8.dp)
                                )
                                Text(
                                    pattern,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = Color.White.copy(alpha = 0.8f)
                                )
                            }
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
        
        // 操作按钮
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Button(
                    onClick = onRestart,
                    modifier = Modifier
                        .weight(1f)
                        .height(56.dp),
                    shape = RoundedCornerShape(28.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF6B48FF)
                    )
                ) {
                    Text(
                        "重新开始",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                
                OutlinedButton(
                    onClick = onBack,
                    modifier = Modifier
                        .weight(1f)
                        .height(56.dp),
                    shape = RoundedCornerShape(28.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = Color.White
                    )
                ) {
                    Text(
                        "返回主页",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/**
 * 维度卡片
 */
@Composable
fun DimensionCard(
    name: String,
    data: com.lifeswarm.android.data.model.DimensionData
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1A1F3A)
        )
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            // 头部
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                
                Text(
                    "${(data.confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF6B48FF)
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // 进度条
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp))
                    .background(Color.White.copy(alpha = 0.2f))
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxHeight()
                        .fillMaxWidth(((data.value + 1) / 2).toFloat())
                        .background(
                            Brush.horizontalGradient(
                                colors = listOf(
                                    Color(0xFF0A59F7),
                                    Color(0xFF6B48FF)
                                )
                            )
                        )
                )
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // 倾向值
            Text(
                "倾向值: ${String.format("%.2f", data.value)}",
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.6f)
            )
        }
    }
}
