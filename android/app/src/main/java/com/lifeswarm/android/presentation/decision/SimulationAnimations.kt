package com.lifeswarm.android.presentation.decision

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.PersonaInteraction

/**
 * Agent 交互连线动画
 * 在两个 Agent 之间绘制虚线动画
 */
@Composable
fun InteractionLines(
    interactions: List<PersonaInteraction>,
    getAgentPosition: (String) -> Offset,
    modifier: Modifier = Modifier
) {
    // 虚线动画
    val infiniteTransition = rememberInfiniteTransition(label = "dash")
    val phase by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 20f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "dashPhase"
    )
    
    Canvas(modifier = modifier.fillMaxSize()) {
        interactions.forEach { interaction ->
            val fromPos = getAgentPosition(interaction.from)
            val toPos = getAgentPosition(interaction.to)
            
            // 绘制虚线
            drawLine(
                color = Color.White.copy(alpha = 0.4f),
                start = Offset(fromPos.x * size.width, fromPos.y * size.height),
                end = Offset(toPos.x * size.width, toPos.y * size.height),
                strokeWidth = 2.dp.toPx(),
                pathEffect = PathEffect.dashPathEffect(
                    intervals = floatArrayOf(10f, 10f),
                    phase = phase
                )
            )
            
            // 绘制箭头
            val arrowSize = 10.dp.toPx()
            val angle = kotlin.math.atan2(
                (toPos.y - fromPos.y) * size.height,
                (toPos.x - fromPos.x) * size.width
            )
            
            val arrowPath = Path().apply {
                moveTo(toPos.x * size.width, toPos.y * size.height)
                lineTo(
                    toPos.x * size.width - arrowSize * kotlin.math.cos(angle - kotlin.math.PI / 6).toFloat(),
                    toPos.y * size.height - arrowSize * kotlin.math.sin(angle - kotlin.math.PI / 6).toFloat()
                )
                moveTo(toPos.x * size.width, toPos.y * size.height)
                lineTo(
                    toPos.x * size.width - arrowSize * kotlin.math.cos(angle + kotlin.math.PI / 6).toFloat(),
                    toPos.y * size.height - arrowSize * kotlin.math.sin(angle + kotlin.math.PI / 6).toFloat()
                )
            }
            
            drawPath(
                path = arrowPath,
                color = Color.White.copy(alpha = 0.4f),
                style = Stroke(width = 2.dp.toPx())
            )
        }
    }
}

/**
 * 评分影响动画
 * 从 Agent 到中心的线条动画
 */
@Composable
fun ScoreImpactAnimation(
    agentPosition: Offset,
    centerPosition: Offset,
    modifier: Modifier = Modifier
) {
    var isVisible by remember { mutableStateOf(true) }
    
    // 淡出动画
    val alpha by animateFloatAsState(
        targetValue = if (isVisible) 1f else 0f,
        animationSpec = tween(durationMillis = 1000),
        finishedListener = { isVisible = false },
        label = "scoreAlpha"
    )
    
    // 线条延伸动画
    val progress by animateFloatAsState(
        targetValue = if (isVisible) 1f else 0f,
        animationSpec = tween(durationMillis = 500, easing = FastOutSlowInEasing),
        label = "scoreProgress"
    )
    
    LaunchedEffect(Unit) {
        isVisible = true
    }
    
    if (alpha > 0) {
        Canvas(modifier = modifier.fillMaxSize()) {
            val startX = agentPosition.x * size.width
            val startY = agentPosition.y * size.height
            val endX = centerPosition.x * size.width
            val endY = centerPosition.y * size.height
            
            val currentEndX = startX + (endX - startX) * progress
            val currentEndY = startY + (endY - startY) * progress
            
            // 绘制发光线条
            drawLine(
                color = Color(0xFFFFD700).copy(alpha = alpha * 0.8f),
                start = Offset(startX, startY),
                end = Offset(currentEndX, currentEndY),
                strokeWidth = 3.dp.toPx()
            )
            
            // 绘制外层发光效果
            drawLine(
                color = Color(0xFFFFD700).copy(alpha = alpha * 0.3f),
                start = Offset(startX, startY),
                end = Offset(currentEndX, currentEndY),
                strokeWidth = 8.dp.toPx()
            )
        }
    }
}

/**
 * 立场变化特效
 * 黄色警告动画
 */
@Composable
fun StanceChangeEffect(
    agentPosition: Offset,
    modifier: Modifier = Modifier
) {
    var isVisible by remember { mutableStateOf(true) }
    
    // 脉冲动画
    val infiniteTransition = rememberInfiniteTransition(label = "stance")
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.5f,
        animationSpec = infiniteRepeatable(
            animation = tween(500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "stanceScale"
    )
    
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 0.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "stanceAlpha"
    )
    
    // 3秒后自动消失
    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(3000)
        isVisible = false
    }
    
    if (isVisible) {
        Canvas(modifier = modifier.fillMaxSize()) {
            val centerX = agentPosition.x * size.width
            val centerY = agentPosition.y * size.height
            val radius = 40.dp.toPx() * scale
            
            // 绘制黄色警告圆圈
            drawCircle(
                color = Color(0xFFFFA726).copy(alpha = alpha),
                radius = radius,
                center = Offset(centerX, centerY),
                style = Stroke(width = 3.dp.toPx())
            )
            
            // 绘制内圈
            drawCircle(
                color = Color(0xFFFFA726).copy(alpha = alpha * 0.5f),
                radius = radius * 0.7f,
                center = Offset(centerX, centerY),
                style = Stroke(width = 2.dp.toPx())
            )
        }
    }
}

/**
 * 完成庆祝动画
 * 烟花效果
 */
@Composable
fun CompletionCelebration(
    centerPosition: Offset,
    modifier: Modifier = Modifier
) {
    var isVisible by remember { mutableStateOf(true) }
    
    val infiniteTransition = rememberInfiniteTransition(label = "celebration")
    val rotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "celebrationRotation"
    )
    
    val scale by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1.5f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "celebrationScale"
    )
    
    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(5000)
        isVisible = false
    }
    
    if (isVisible) {
        Canvas(modifier = modifier.fillMaxSize()) {
            val centerX = centerPosition.x * size.width
            val centerY = centerPosition.y * size.height
            
            // 绘制多个旋转的星星
            for (i in 0 until 8) {
                val angle = (rotation + i * 45f) * kotlin.math.PI / 180f
                val distance = 80.dp.toPx() * scale
                val x = centerX + distance * kotlin.math.cos(angle).toFloat()
                val y = centerY + distance * kotlin.math.sin(angle).toFloat()
                
                drawCircle(
                    color = Color(0xFFFFD700).copy(alpha = 0.8f),
                    radius = 5.dp.toPx(),
                    center = Offset(x, y)
                )
            }
        }
    }
}

/**
 * 思考波纹动画
 * Agent 思考时的波纹效果
 */
@Composable
fun ThinkingRipple(
    agentPosition: Offset,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "ripple")
    val scale by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rippleScale"
    )
    
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rippleAlpha"
    )
    
    Canvas(modifier = modifier.fillMaxSize()) {
        val centerX = agentPosition.x * size.width
        val centerY = agentPosition.y * size.height
        val radius = 50.dp.toPx() * scale
        
        drawCircle(
            color = Color(0xFF64B5F6).copy(alpha = alpha),
            radius = radius,
            center = Offset(centerX, centerY),
            style = Stroke(width = 2.dp.toPx())
        )
    }
}
